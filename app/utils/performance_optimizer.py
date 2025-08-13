"""
Sistema de Otimização de Performance para Mídia Church
Implementa melhorias de performance, cache avançado e otimizações
"""

import streamlit as st
import time
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from functools import wraps, lru_cache
import pandas as pd
import gc
import psutil
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import text

from app.database.local_connection import db_manager
from app.utils.cache_manager import cache_manager, smart_cache

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Otimizador de performance da aplicação"""
    
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.optimization_cache = {}
        self.performance_metrics = {}
        self._init_optimization_tables()
    
    def _init_optimization_tables(self):
        """Inicializa tabelas de otimização"""
        try:
            with db_manager.get_db_session() as session:
                # Tabela de métricas de performance
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        metric_type TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT,
                        user_id INTEGER
                    )
                """))
                
                # Tabela de cache de consultas
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS query_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_hash TEXT UNIQUE NOT NULL,
                        query_result TEXT NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Índices para performance
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp)"))
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_cache_expires ON query_cache(expires_at)"))
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Erro ao inicializar tabelas de otimização: {e}")
    
    def measure_performance(self, func_name: str = None):
        """Decorator para medir performance de funções"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                    memory_used = end_memory - start_memory
                    
                    # Registrar métricas
                    self._record_metric(
                        func_name or func.__name__,
                        execution_time,
                        "execution_time"
                    )
                    
                    self._record_metric(
                        f"{func_name or func.__name__}_memory",
                        memory_used,
                        "memory_usage"
                    )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    self._record_metric(
                        f"{func_name or func.__name__}_error",
                        execution_time,
                        "error_time"
                    )
                    raise
            
            return wrapper
        return decorator
    
    def _record_metric(self, name: str, value: float, metric_type: str):
        """Registra métrica de performance"""
        try:
            session_id = st.session_state.get('session_id', 'unknown')
            user_id = st.session_state.get('user_id', None)
            
            db_manager.execute_query(
                """INSERT INTO performance_metrics 
                   (metric_name, metric_value, metric_type, session_id, user_id)
                   VALUES (?, ?, ?, ?, ?)""",
                (name, value, metric_type, session_id, user_id)
            )
        except Exception as e:
            logger.error(f"Erro ao registrar métrica: {e}")
    
    def optimize_dataframe_operations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Otimiza operações em DataFrames"""
        if df.empty:
            return df
        
        # Otimizar tipos de dados
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    # Tentar converter para categoria se há repetições
                    if df[col].nunique() / len(df) < 0.5:
                        df[col] = df[col].astype('category')
                except:
                    pass
            elif df[col].dtype == 'int64':
                # Usar int32 se possível
                if df[col].min() >= -2147483648 and df[col].max() <= 2147483647:
                    df[col] = df[col].astype('int32')
        
        return df
    
    def batch_database_operations(self, operations: List[Dict[str, Any]]) -> List[Any]:
        """Executa operações de banco em lote para melhor performance"""
        results = []
        
        try:
            with db_manager.get_db_session() as session:
                for operation in operations:
                    query = operation.get('query')
                    params = operation.get('params')
                    fetch = operation.get('fetch', False)
                    
                    if fetch:
                        result = session.execute(query, params or {})
                        results.append(result.fetchall())
                    else:
                        session.execute(query, params or {})
                        results.append(True)
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Erro em operações em lote: {e}")
            results.append(False)
        
        return results
    
    def async_data_loader(self, data_sources: List[Callable]) -> Dict[str, Any]:
        """Carrega dados de múltiplas fontes de forma assíncrona"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=len(data_sources)) as executor:
            future_to_source = {
                executor.submit(source): f"source_{i}" 
                for i, source in enumerate(data_sources)
            }
            
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    results[source_name] = future.result()
                except Exception as e:
                    logger.error(f"Erro ao carregar {source_name}: {e}")
                    results[source_name] = None
        
        return results
    
    def cleanup_memory(self):
        """Limpa memória desnecessária"""
        try:
            # Limpar cache antigo
            cache_manager.clear()
            
            # Forçar garbage collection
            gc.collect()
            
            # Limpar session_state desnecessário
            keys_to_remove = []
            for key in st.session_state.keys():
                if key.startswith('temp_') or key.startswith('cache_'):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del st.session_state[key]
            
            logger.info("Limpeza de memória realizada")
            
        except Exception as e:
            logger.error(f"Erro na limpeza de memória: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Gera relatório de performance"""
        try:
            # Métricas dos últimos 30 minutos
            query = text("""
                SELECT 
                    metric_name,
                    AVG(metric_value) as avg_value,
                    MIN(metric_value) as min_value,
                    MAX(metric_value) as max_value,
                    COUNT(*) as count
                FROM performance_metrics 
                WHERE timestamp >= datetime('now', '-30 minutes')
                GROUP BY metric_name
                ORDER BY avg_value DESC
            """)
            
            metrics = db_manager.fetch_all(query)
            
            # Informações do sistema
            process = psutil.Process()
            system_info = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_used_mb': process.memory_info().rss / 1024 / 1024,
                'open_files': len(process.open_files()),
                'threads': process.num_threads()
            }
            
            return {
                'metrics': metrics,
                'system_info': system_info,
                'cache_size': len(st.session_state.get('cache_store', {})),
                'session_size': len(st.session_state.keys())
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            return {}

# Instância global do otimizador
performance_optimizer = PerformanceOptimizer()

# Decorators otimizados
def optimized_cache(max_age_minutes: int = 10, key_prefix: str = "opt_"):
    """Cache otimizado com limpeza automática"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Usar cache inteligente
            cached_func = smart_cache(max_age_minutes, key_prefix)(func)
            return cached_func(*args, **kwargs)
        return wrapper
    return decorator

def lazy_load(threshold_seconds: float = 0.1):
    """Carregamento lazy para operações custosas"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Verificar se já está em cache
            cache_key = f"lazy_{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            if cache_key in st.session_state:
                return st.session_state[cache_key]
            
            # Executar com medição de tempo
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Cachear se demorou mais que o threshold
            if execution_time > threshold_seconds:
                st.session_state[cache_key] = result
            
            return result
        return wrapper
    return decorator

def database_optimized(batch_size: int = 100):
    """Otimização para operações de banco de dados"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Adicionar medição de performance
            measured_func = performance_optimizer.measure_performance()(func)
            return measured_func(*args, **kwargs)
        return wrapper
    return decorator

# Funções de otimização específicas
@optimized_cache(max_age_minutes=15, key_prefix="users_")
def get_optimized_users():
    """Versão otimizada para buscar usuários"""
    query = text("""
        SELECT id, username, full_name, email, role, is_active
        FROM users 
        WHERE is_active = 1
        ORDER BY full_name
    """)
    return db_manager.fetch_all(query)

@optimized_cache(max_age_minutes=10, key_prefix="events_")
def get_optimized_events():
    """Versão otimizada para buscar eventos"""
    query = text("""
        SELECT id, title, event_type, start_datetime, end_datetime, location
        FROM events 
        WHERE is_active = 1 AND start_datetime >= date('now')
        ORDER BY start_datetime
        LIMIT 50
    """)
    return db_manager.fetch_all(query)

@optimized_cache(max_age_minutes=5, key_prefix="stats_")
def get_optimized_dashboard_stats():
    """Versão otimizada para estatísticas do dashboard"""
    # Usar operações em lote
    operations = [
        {
            'query': text("SELECT COUNT(*) as count FROM users WHERE is_active = 1"),
            'fetch': True
        },
        {
            'query': text("SELECT COUNT(*) as count FROM events WHERE start_datetime > datetime('now')"),
            'fetch': True
        },
        {
            'query': text("""
                SELECT COUNT(*) as count FROM events 
                WHERE start_datetime >= date('now', 'weekday 0', '-6 days') 
                AND start_datetime < date('now', 'weekday 0', '+1 day')
            """),
            'fetch': True
        }
    ]
    
    results = performance_optimizer.batch_database_operations(operations)
    
    return {
        'active_users': results[0][0]['count'] if results[0] else 0,
        'upcoming_events': results[1][0]['count'] if results[1] else 0,
        'week_events': results[2][0]['count'] if results[2] else 0
    }

def optimize_streamlit_config():
    """Otimiza configurações do Streamlit"""
    try:
        # Configurações de performance
        st.set_page_config(
            page_title="Mídia Church",
            page_icon="🎵",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # CSS para melhor performance
        st.markdown("""
        <style>
        /* Otimizações de CSS */
        .stDataFrame {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .stPlotlyChart {
            height: 400px !important;
        }
        
        /* Reduzir animações para melhor performance */
        * {
            transition: none !important;
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
        }
        
        /* Otimizar renderização de tabelas */
        .dataframe {
            font-size: 0.9rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        logger.error(f"Erro ao otimizar configurações: {e}")

def cleanup_old_data():
    """Limpa dados antigos para manter performance"""
    try:
        # Limpar métricas antigas (mais de 7 dias)
        db_manager.execute_query("""
            DELETE FROM performance_metrics 
            WHERE timestamp < datetime('now', '-7 days')
        """)
        
        # Limpar cache expirado
        db_manager.execute_query("""
            DELETE FROM query_cache 
            WHERE expires_at < datetime('now')
        """)
        
        # Limpar logs de segurança antigos (mais de 30 dias)
        db_manager.execute_query("""
            DELETE FROM security_logs 
            WHERE timestamp < datetime('now', '-30 days')
        """)
        
        logger.info("Limpeza de dados antigos realizada")
        
    except Exception as e:
        logger.error(f"Erro na limpeza de dados: {e}")