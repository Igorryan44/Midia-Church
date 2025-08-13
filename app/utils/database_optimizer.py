"""
Otimizador de Banco de Dados para Mídia Church
Otimizações específicas para consultas e performance do banco
"""

import sqlite3
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from functools import wraps
import pandas as pd

from app.database.local_connection import db_manager, get_db_connection

class DatabaseOptimizer:
    """Otimizador de banco de dados"""
    
    def __init__(self):
        self.query_cache = {}
        self.slow_queries = []
        self.query_stats = {}
    
    def optimize_database(self):
        """Executa otimizações gerais no banco"""
        optimizations = []
        
        try:
            # VACUUM - reorganiza e compacta o banco
            db_manager.execute_query("VACUUM")
            optimizations.append("✅ VACUUM executado")
            
            # ANALYZE - atualiza estatísticas do otimizador
            db_manager.execute_query("ANALYZE")
            optimizations.append("✅ ANALYZE executado")
            
            # Reindexar tabelas principais
            self.reindex_tables()
            optimizations.append("✅ Índices recriados")
            
            # Limpar logs antigos
            self.cleanup_old_logs()
            optimizations.append("✅ Logs antigos limpos")
            
        except Exception as e:
            optimizations.append(f"❌ Erro: {e}")
        
        return optimizations
    
    def reindex_tables(self):
        """Recria índices das tabelas principais"""
        indexes = [
            # Usuários
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
            
            # Eventos
            "CREATE INDEX IF NOT EXISTS idx_events_date ON events(start_datetime)",
            "CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_events_active ON events(is_active)",
            
            # Sessões de usuário
            "CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at)",
            
            # Performance logs
            "CREATE INDEX IF NOT EXISTS idx_perf_function ON performance_logs(function_name)",
            "CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON performance_logs(timestamp)",
            
            # Notificações
            "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_date ON notifications(created_at)",
        ]
        
        for index_sql in indexes:
            try:
                db_manager.execute_query(index_sql)
            except Exception as e:
                print(f"Erro ao criar índice: {e}")
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Remove logs antigos para liberar espaço"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        cleanup_queries = [
            f"DELETE FROM performance_logs WHERE timestamp < '{cutoff_date}'",
            f"DELETE FROM security_logs WHERE created_at < '{cutoff_date}'",
            f"DELETE FROM user_sessions WHERE expires_at < '{cutoff_date}' AND is_active = 0",
        ]
        
        for query in cleanup_queries:
            try:
                db_manager.execute_query(query)
            except Exception as e:
                print(f"Erro na limpeza: {e}")
    
    def analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """Analisa consultas lentas"""
        try:
            # Buscar consultas de performance
            slow_queries = db_manager.fetch_all("""
                SELECT function_name, AVG(execution_time) as avg_time, 
                       COUNT(*) as call_count, MAX(execution_time) as max_time
                FROM performance_logs 
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY function_name
                HAVING avg_time > 1.0
                ORDER BY avg_time DESC
                LIMIT 10
            """)
            
            return slow_queries or []
            
        except Exception as e:
            print(f"Erro ao analisar consultas lentas: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco de dados"""
        stats = {}
        
        try:
            # Tamanho do banco
            db_size = db_manager.fetch_all("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            stats['database_size_mb'] = (db_size[0]['size'] / 1024 / 1024) if db_size else 0
            
            # Contagem de tabelas
            table_counts = {}
            tables = ['users', 'events', 'user_sessions', 'notifications', 'performance_logs']
            
            for table in tables:
                try:
                    count = db_manager.fetch_all(f"SELECT COUNT(*) as count FROM {table}")
                    table_counts[table] = count[0]['count'] if count else 0
                except:
                    table_counts[table] = 0
            
            stats['table_counts'] = table_counts
            
            # Estatísticas de performance
            perf_stats = db_manager.fetch_all("""
                SELECT 
                    COUNT(*) as total_queries,
                    AVG(execution_time) as avg_execution_time,
                    MAX(execution_time) as max_execution_time
                FROM performance_logs 
                WHERE timestamp > datetime('now', '-24 hours')
            """)
            
            if perf_stats:
                stats['performance'] = perf_stats[0]
            else:
                stats['performance'] = {
                    'total_queries': 0,
                    'avg_execution_time': 0,
                    'max_execution_time': 0
                }
            
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
        
        return stats
    
    def optimize_query(self, query: str) -> str:
        """Otimiza uma consulta SQL"""
        # Otimizações básicas
        optimized = query.strip()
        
        # Adicionar LIMIT se não existir em SELECT sem WHERE específico
        if optimized.upper().startswith('SELECT') and 'LIMIT' not in optimized.upper():
            if 'WHERE' not in optimized.upper() or 'COUNT(' in optimized.upper():
                optimized += ' LIMIT 1000'
        
        # Sugerir índices para WHERE clauses
        if 'WHERE' in optimized.upper():
            # Análise básica de WHERE clauses
            pass
        
        return optimized
    
    def monitor_query_performance(self, func):
        """Decorator para monitorar performance de consultas"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Registrar estatísticas
                func_name = func.__name__
                if func_name not in self.query_stats:
                    self.query_stats[func_name] = {
                        'total_calls': 0,
                        'total_time': 0,
                        'avg_time': 0,
                        'max_time': 0
                    }
                
                stats = self.query_stats[func_name]
                stats['total_calls'] += 1
                stats['total_time'] += execution_time
                stats['avg_time'] = stats['total_time'] / stats['total_calls']
                stats['max_time'] = max(stats['max_time'], execution_time)
                
                # Se for muito lenta, adicionar à lista
                if execution_time > 2.0:
                    self.slow_queries.append({
                        'function': func_name,
                        'execution_time': execution_time,
                        'timestamp': datetime.now(),
                        'args': str(args)[:100]
                    })
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"Erro na consulta {func.__name__}: {e} (tempo: {execution_time:.3f}s)")
                raise
        
        return wrapper
    
    def batch_insert(self, table: str, data: List[Dict[str, Any]], batch_size: int = 100):
        """Inserção em lote otimizada"""
        if not data:
            return
        
        # Dividir em lotes
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            
            # Construir query de inserção em lote
            if batch:
                columns = list(batch[0].keys())
                placeholders = ', '.join(['?' * len(columns)])
                column_names = ', '.join(columns)
                
                query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
                
                # Preparar valores
                values = []
                for row in batch:
                    values.append(tuple(row[col] for col in columns))
                
                # Executar em lote
                try:
                    with get_db_connection() as conn:
                        conn.executemany(query, values)
                        conn.commit()
                except Exception as e:
                    print(f"Erro na inserção em lote: {e}")
    
    def create_materialized_view(self, view_name: str, query: str):
        """Cria uma 'view materializada' usando tabela temporária"""
        try:
            # Remover view existente
            db_manager.execute_query(f"DROP TABLE IF EXISTS {view_name}")
            
            # Criar nova tabela com dados da query
            create_query = f"CREATE TABLE {view_name} AS {query}"
            db_manager.execute_query(create_query)
            
            # Criar índice na view
            db_manager.execute_query(f"CREATE INDEX IF NOT EXISTS idx_{view_name}_id ON {view_name}(rowid)")
            
        except Exception as e:
            print(f"Erro ao criar view materializada: {e}")
    
    def refresh_materialized_view(self, view_name: str, query: str):
        """Atualiza view materializada"""
        try:
            # Recriar a view
            self.create_materialized_view(view_name, query)
        except Exception as e:
            print(f"Erro ao atualizar view materializada: {e}")

# Instância global
db_optimizer = DatabaseOptimizer()

# Decorators úteis
def monitor_db_performance(func):
    """Decorator para monitorar performance de funções de banco"""
    return db_optimizer.monitor_query_performance(func)

def optimized_query(func):
    """Decorator para otimizar consultas automaticamente"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Se o primeiro argumento for uma query string, otimizar
        if args and isinstance(args[0], str):
            optimized_sql = db_optimizer.optimize_query(args[0])
            args = (optimized_sql,) + args[1:]
        
        return func(*args, **kwargs)
    
    return wrapper

# Funções utilitárias
def optimize_database():
    """Executa otimização completa do banco"""
    return db_optimizer.optimize_database()

def get_database_stats():
    """Retorna estatísticas do banco"""
    return db_optimizer.get_database_stats()

def analyze_slow_queries():
    """Analisa consultas lentas"""
    return db_optimizer.analyze_slow_queries()

def cleanup_old_data(days: int = 30):
    """Limpa dados antigos"""
    db_optimizer.cleanup_old_logs(days)

# Views materializadas úteis
def create_dashboard_views():
    """Cria views materializadas para o dashboard"""
    views = {
        'dashboard_stats': """
            SELECT 
                (SELECT COUNT(*) FROM users WHERE is_active = 1) as active_users,
                (SELECT COUNT(*) FROM events WHERE is_active = 1) as total_events,
                (SELECT COUNT(*) FROM events WHERE start_datetime > datetime('now')) as upcoming_events,
                (SELECT COUNT(*) FROM notifications WHERE is_read = 0) as unread_notifications
        """,
        'recent_activities': """
            SELECT 'user' as type, username as title, created_at as timestamp
            FROM users 
            WHERE created_at > datetime('now', '-7 days')
            UNION ALL
            SELECT 'event' as type, title, created_at
            FROM events 
            WHERE created_at > datetime('now', '-7 days')
            ORDER BY timestamp DESC
            LIMIT 50
        """
    }
    
    for view_name, query in views.items():
        db_optimizer.create_materialized_view(view_name, query)

def refresh_dashboard_views():
    """Atualiza views do dashboard"""
    views = {
        'dashboard_stats': """
            SELECT 
                (SELECT COUNT(*) FROM users WHERE is_active = 1) as active_users,
                (SELECT COUNT(*) FROM events WHERE is_active = 1) as total_events,
                (SELECT COUNT(*) FROM events WHERE start_datetime > datetime('now')) as upcoming_events,
                (SELECT COUNT(*) FROM notifications WHERE is_read = 0) as unread_notifications
        """,
        'recent_activities': """
            SELECT 'user' as type, username as title, created_at as timestamp
            FROM users 
            WHERE created_at > datetime('now', '-7 days')
            UNION ALL
            SELECT 'event' as type, title, created_at
            FROM events 
            WHERE created_at > datetime('now', '-7 days')
            ORDER BY timestamp DESC
            LIMIT 50
        """
    }
    
    for view_name, query in views.items():
        db_optimizer.refresh_materialized_view(view_name, query)