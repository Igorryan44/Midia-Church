"""
Sistema de Cache Otimizado para Mídia Church
Melhora performance através de cache inteligente
"""

import streamlit as st
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
import pandas as pd
from functools import wraps
import threading
import weakref
from app.utils.memory_optimizer import memory_optimizer

class CacheManager:
    """Gerenciador de cache inteligente para otimizar performance"""
    
    def __init__(self):
        if 'cache_storage' not in st.session_state:
            st.session_state.cache_storage = {}
        if 'cache_timestamps' not in st.session_state:
            st.session_state.cache_timestamps = {}
        if 'cache_access_count' not in st.session_state:
            st.session_state.cache_access_count = {}
        if 'cache_size_limit' not in st.session_state:
            st.session_state.cache_size_limit = 50  # MB
        
        self.cache_refs = weakref.WeakValueDictionary()
        self._lock = threading.Lock()
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Gera chave única para cache"""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str, max_age_minutes: int = 5) -> Optional[Any]:
        """Recupera item do cache se ainda válido"""
        with self._lock:
            if key not in st.session_state.cache_storage:
                return None
            
            timestamp = st.session_state.cache_timestamps.get(key)
            if not timestamp:
                return None
            
            age = datetime.now() - timestamp
            if age > timedelta(minutes=max_age_minutes):
                # Cache expirado
                del st.session_state.cache_storage[key]
                del st.session_state.cache_timestamps[key]
                return None
            
            # Incrementar contador de acesso
            st.session_state.cache_access_count[key] = st.session_state.cache_access_count.get(key, 0) + 1
            
            return st.session_state.cache_storage[key]
    
    def set_cached_item(self, key: str, value: Any) -> None:
        """Armazena item no cache"""
        with self._lock:
            # Verificar limite de tamanho antes de adicionar
            self._check_cache_size()
            
            # Otimizar DataFrame se aplicável
            if isinstance(value, pd.DataFrame):
                value = memory_optimizer.optimize_dataframe(value)
                memory_optimizer.register_large_object(value)
            
            st.session_state.cache_storage[key] = value
            st.session_state.cache_timestamps[key] = datetime.now()
            st.session_state.cache_access_count[key] = 0
    
    def clear(self, pattern: Optional[str] = None) -> None:
        """Limpa cache (opcionalmente por padrão)"""
        with self._lock:
            if pattern:
                keys_to_remove = [k for k in st.session_state.cache_storage.keys() if pattern in k]
                for key in keys_to_remove:
                    self._remove_cache_item(key)
            else:
                st.session_state.cache_storage.clear()
                st.session_state.cache_timestamps.clear()
                st.session_state.cache_access_count.clear()
                self.cache_refs.clear()
    
    def _check_cache_size(self):
        """Verifica e limita o tamanho do cache"""
        # Implementação simplificada - em produção seria mais sofisticada
        if len(st.session_state.cache_storage) > 100:  # Limite de itens
            self._cleanup_least_used()
    
    def _cleanup_least_used(self):
        """Remove itens menos usados do cache"""
        if not st.session_state.cache_access_count:
            return
        
        # Ordenar por menor uso
        sorted_items = sorted(
            st.session_state.cache_access_count.items(),
            key=lambda x: x[1]
        )
        
        # Remover 25% dos itens menos usados
        items_to_remove = len(sorted_items) // 4
        for key, _ in sorted_items[:items_to_remove]:
            self._remove_cache_item(key)
    
    def _remove_cache_item(self, key: str):
        """Remove item específico do cache"""
        st.session_state.cache_storage.pop(key, None)
        st.session_state.cache_timestamps.pop(key, None)
        st.session_state.cache_access_count.pop(key, None)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        return {
            'total_items': len(st.session_state.cache_storage),
            'total_accesses': sum(st.session_state.cache_access_count.values()),
            'most_accessed': max(st.session_state.cache_access_count.items(), 
                               key=lambda x: x[1]) if st.session_state.cache_access_count else None,
            'cache_size_limit': st.session_state.cache_size_limit
        }

# Instância global do cache
cache_manager = CacheManager()

def smart_cache(max_age_minutes: int = 5, key_prefix: str = ""):
    """Decorator para cache inteligente"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave do cache
            cache_key = cache_manager._generate_key(
                f"{key_prefix}{func.__name__}", args, kwargs
            )
            
            # Tentar recuperar do cache
            cached_result = cache_manager.get(cache_key, max_age_minutes)
            if cached_result is not None:
                return cached_result
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            cache_manager.set_cached_item(cache_key, result)
            return result
        
        return wrapper
    return decorator

class PaginationHelper:
    """Helper para paginação de dados"""
    
    @staticmethod
    def paginate_dataframe(df: pd.DataFrame, page_size: int = 10, page_key: str = "page") -> tuple:
        """Pagina um DataFrame"""
        if df.empty:
            return df, 0, 0, 0
        
        total_items = len(df)
        total_pages = (total_items - 1) // page_size + 1
        
        # Controle de página
        if f"{page_key}_current" not in st.session_state:
            st.session_state[f"{page_key}_current"] = 1
        
        current_page = st.session_state[f"{page_key}_current"]
        
        # Garantir que a página está dentro dos limites
        if current_page > total_pages:
            current_page = total_pages
            st.session_state[f"{page_key}_current"] = current_page
        elif current_page < 1:
            current_page = 1
            st.session_state[f"{page_key}_current"] = current_page
        
        # Calcular índices
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_items)
        
        # Retornar dados paginados
        paginated_df = df.iloc[start_idx:end_idx]
        
        return paginated_df, current_page, total_pages, total_items
    
    @staticmethod
    def render_pagination_controls(current_page: int, total_pages: int, page_key: str = "page"):
        """Renderiza controles de paginação"""
        if total_pages <= 1:
            return
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ Primeira", disabled=current_page == 1, key=f"{page_key}_first"):
                st.session_state[f"{page_key}_current"] = 1
                st.rerun()
        
        with col2:
            if st.button("⬅️ Anterior", disabled=current_page == 1, key=f"{page_key}_prev"):
                st.session_state[f"{page_key}_current"] = current_page - 1
                st.rerun()
        
        with col3:
            st.markdown(f"<div style='text-align: center; padding: 8px;'>Página {current_page} de {total_pages}</div>", 
                       unsafe_allow_html=True)
        
        with col4:
            if st.button("➡️ Próxima", disabled=current_page == total_pages, key=f"{page_key}_next"):
                st.session_state[f"{page_key}_current"] = current_page + 1
                st.rerun()
        
        with col5:
            if st.button("⏭️ Última", disabled=current_page == total_pages, key=f"{page_key}_last"):
                st.session_state[f"{page_key}_current"] = total_pages
                st.rerun()

def clear_cache_on_data_change(table_name: str):
    """Limpa cache quando dados são modificados"""
    cache_manager.clear(table_name)

# Funções de cache específicas para dados comuns
@smart_cache(max_age_minutes=10, key_prefix="events_")
def get_cached_events():
    """Cache para eventos"""
    from app.database.local_connection import get_events
    return get_events()

@smart_cache(max_age_minutes=15, key_prefix="users_")
def get_cached_users():
    """Cache para usuários"""
    from app.database.local_connection import get_all_users
    return get_all_users()

@smart_cache(max_age_minutes=5, key_prefix="stats_")
def get_cached_dashboard_stats():
    """Cache para estatísticas do dashboard"""
    from app.database.local_connection import db_manager
    
    stats = {}
    
    # Total de eventos
    events_result = db_manager.fetch_all("SELECT COUNT(*) as total FROM events WHERE start_datetime >= date('now')")
    stats['upcoming_events'] = events_result[0]['total'] if events_result else 0
    
    # Total de usuários ativos
    users_result = db_manager.fetch_all("SELECT COUNT(*) as total FROM users WHERE is_active = 1")
    stats['active_users'] = users_result[0]['total'] if users_result else 0
    
    # Eventos desta semana
    week_events = db_manager.fetch_all("""
        SELECT COUNT(*) as total FROM events 
        WHERE start_datetime >= date('now', 'weekday 0', '-6 days') 
        AND start_datetime < date('now', 'weekday 0', '+1 day')
    """)
    stats['week_events'] = week_events[0]['total'] if week_events else 0
    
    return stats