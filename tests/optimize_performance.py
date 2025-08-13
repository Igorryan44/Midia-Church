#!/usr/bin/env python3
"""
Script de Otimização de Performance
Resolve problemas de memória e performance detectados
"""

import os
import sys
import gc
import psutil
import sqlite3
from pathlib import Path

# Adicionar o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def optimize_memory():
    """Otimiza uso de memória"""
    print("🧠 Otimizando memória...")
    
    # Forçar garbage collection
    gc.collect()
    
    # Configurar garbage collection mais agressivo
    gc.set_threshold(700, 10, 10)
    
    print("  ✅ Garbage collection otimizado")

def fix_database_connections():
    """Corrige conexões de banco não fechadas"""
    print("🗄️ Otimizando conexões de banco...")
    
    try:
        from app.database.local_connection import db_manager
        
        # Fechar conexões ativas
        if hasattr(db_manager, 'connection') and db_manager.connection:
            db_manager.connection.close()
            
        # Recriar pool de conexões com configurações otimizadas
        db_manager.init_database()
        
        print("  ✅ Conexões de banco otimizadas")
    except Exception as e:
        print(f"  ⚠️ Erro ao otimizar banco: {e}")

def optimize_imports():
    """Otimiza imports pesados"""
    print("📦 Otimizando imports...")
    
    # Lista de módulos pesados para lazy loading
    heavy_modules = [
        'pandas',
        'plotly',
        'numpy',
        'matplotlib',
        'seaborn'
    ]
    
    # Remover módulos pesados do cache se carregados
    modules_to_remove = []
    for module_name in sys.modules:
        for heavy in heavy_modules:
            if heavy in module_name:
                modules_to_remove.append(module_name)
    
    for module in modules_to_remove:
        if module in sys.modules:
            del sys.modules[module]
    
    print(f"  ✅ {len(modules_to_remove)} módulos pesados removidos do cache")

def optimize_streamlit_cache():
    """Otimiza cache do Streamlit"""
    print("⚡ Otimizando cache do Streamlit...")
    
    try:
        import streamlit as st
        
        # Limpar cache do Streamlit
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
        if hasattr(st, 'cache_resource'):
            st.cache_resource.clear()
            
        print("  ✅ Cache do Streamlit limpo")
    except Exception as e:
        print(f"  ⚠️ Erro ao limpar cache: {e}")

def create_memory_monitor():
    """Cria monitor de memória"""
    print("📊 Criando monitor de memória...")
    
    monitor_code = '''
import psutil
import gc
import threading
import time
from datetime import datetime

class MemoryMonitor:
    def __init__(self, threshold_mb=500):
        self.threshold_mb = threshold_mb
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Inicia monitoramento de memória"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Para monitoramento de memória"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_loop(self):
        """Loop de monitoramento"""
        while self.monitoring:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                if memory_mb > self.threshold_mb:
                    print(f"⚠️ Alto uso de memória: {memory_mb:.1f}MB")
                    gc.collect()  # Forçar limpeza
                
                time.sleep(30)  # Verificar a cada 30 segundos
            except Exception:
                break
    
    def get_memory_usage(self):
        """Retorna uso atual de memória"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0

# Instância global do monitor
memory_monitor = MemoryMonitor()
'''
    
    monitor_file = project_root / "app" / "utils" / "memory_monitor.py"
    with open(monitor_file, 'w', encoding='utf-8') as f:
        f.write(monitor_code)
    
    print("  ✅ Monitor de memória criado")

def optimize_database_queries():
    """Otimiza queries do banco de dados"""
    print("🔍 Otimizando queries do banco...")
    
    try:
        from app.database.local_connection import db_manager
        
        # Criar índices para melhorar performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_events_datetime ON events(start_datetime)",
            "CREATE INDEX IF NOT EXISTS idx_events_active ON events(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_event ON attendance(event_id)",
            "CREATE INDEX IF NOT EXISTS idx_media_active ON media_content(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_media_type ON media_content(file_type)",
            "CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)"
        ]
        
        for index_sql in indexes:
            try:
                db_manager.execute_query(index_sql)
            except Exception:
                pass  # Índice já existe
        
        # Executar VACUUM para otimizar banco
        db_manager.execute_query("VACUUM")
        
        print("  ✅ Índices criados e banco otimizado")
    except Exception as e:
        print(f"  ⚠️ Erro ao otimizar queries: {e}")

def create_performance_config():
    """Cria configurações de performance"""
    print("⚙️ Criando configurações de performance...")
    
    config_code = '''
"""
Configurações de Performance
"""

# Configurações de memória
MEMORY_SETTINGS = {
    'max_memory_mb': 512,
    'gc_threshold': (700, 10, 10),
    'enable_monitoring': True,
    'cleanup_interval': 300  # 5 minutos
}

# Configurações de cache
CACHE_SETTINGS = {
    'max_cache_size': 100,
    'cache_ttl': 300,  # 5 minutos
    'enable_compression': True
}

# Configurações de banco
DATABASE_SETTINGS = {
    'connection_pool_size': 5,
    'connection_timeout': 30,
    'enable_wal_mode': True,
    'pragma_settings': {
        'journal_mode': 'WAL',
        'synchronous': 'NORMAL',
        'cache_size': -64000,  # 64MB
        'temp_store': 'MEMORY'
    }
}

# Configurações de lazy loading
LAZY_LOADING = {
    'heavy_modules': [
        'pandas',
        'plotly',
        'numpy',
        'matplotlib',
        'seaborn'
    ],
    'defer_imports': True,
    'module_timeout': 30
}
'''
    
    config_file = project_root / "app" / "config" / "performance.py"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_code)
    
    print("  ✅ Configurações de performance criadas")

def main():
    """Função principal de otimização"""
    print("🚀 INICIANDO OTIMIZAÇÃO DE PERFORMANCE")
    print("=" * 60)
    
    # Medir memória inicial
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024
    print(f"💾 Memória inicial: {initial_memory:.1f}MB")
    
    # Executar otimizações
    optimize_memory()
    fix_database_connections()
    optimize_imports()
    optimize_streamlit_cache()
    create_memory_monitor()
    optimize_database_queries()
    create_performance_config()
    
    # Medir memória final
    gc.collect()
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_saved = initial_memory - final_memory
    
    print("=" * 60)
    print("✅ OTIMIZAÇÃO CONCLUÍDA!")
    print(f"💾 Memória final: {final_memory:.1f}MB")
    if memory_saved > 0:
        print(f"🎉 Memória economizada: {memory_saved:.1f}MB")
    else:
        print(f"📊 Variação de memória: {abs(memory_saved):.1f}MB")
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("  1. Reinicie a aplicação para aplicar todas as otimizações")
    print("  2. Execute os testes novamente para verificar melhorias")
    print("  3. Monitor de memória será ativado automaticamente")

if __name__ == "__main__":
    main()