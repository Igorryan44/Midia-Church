
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
