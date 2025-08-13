"""
Sistema de Carregamento Lazy (Preguiçoso) para Mídia Church
Implementa carregamento sob demanda para melhorar performance inicial
"""

import streamlit as st
import time
import threading
from typing import Any, Callable, Dict, Optional, List
from functools import wraps
import pandas as pd
from datetime import datetime, timedelta

class LazyLoader:
    """Gerenciador de carregamento lazy"""
    
    def __init__(self):
        self.loading_states = {}
        self.loaded_data = {}
        self.loading_threads = {}
    
    def lazy_component(self, 
                      loader_func: Callable, 
                      placeholder_text: str = "Carregando...",
                      cache_key: Optional[str] = None,
                      auto_refresh_minutes: int = 0):
        """
        Decorator para componentes com carregamento lazy
        
        Args:
            loader_func: Função que carrega os dados
            placeholder_text: Texto exibido durante carregamento
            cache_key: Chave para cache (opcional)
            auto_refresh_minutes: Minutos para refresh automático (0 = sem refresh)
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                component_key = cache_key or f"{func.__name__}_{id(func)}"
                
                # Verificar se já está carregado e ainda válido
                if self._is_data_valid(component_key, auto_refresh_minutes):
                    return func(self.loaded_data[component_key], *args, **kwargs)
                
                # Verificar se está carregando
                if component_key in self.loading_states and self.loading_states[component_key]:
                    st.info(f"⏳ {placeholder_text}")
                    return None
                
                # Iniciar carregamento
                self._start_loading(component_key, loader_func, placeholder_text)
                st.info(f"⏳ {placeholder_text}")
                
                # Botão para forçar carregamento síncrono
                if st.button(f"🔄 Carregar agora", key=f"force_load_{component_key}"):
                    with st.spinner("Carregando..."):
                        data = loader_func()
                        self.loaded_data[component_key] = {
                            'data': data,
                            'loaded_at': datetime.now()
                        }
                        self.loading_states[component_key] = False
                        st.rerun()
                
                return None
            
            return wrapper
        return decorator
    
    def _is_data_valid(self, key: str, auto_refresh_minutes: int) -> bool:
        """Verifica se os dados ainda são válidos"""
        if key not in self.loaded_data:
            return False
        
        if auto_refresh_minutes <= 0:
            return True
        
        loaded_at = self.loaded_data[key].get('loaded_at')
        if not loaded_at:
            return False
        
        age = datetime.now() - loaded_at
        return age < timedelta(minutes=auto_refresh_minutes)
    
    def _start_loading(self, key: str, loader_func: Callable, placeholder_text: str):
        """Inicia carregamento em thread separada"""
        if key in self.loading_threads and self.loading_threads[key].is_alive():
            return
        
        self.loading_states[key] = True
        
        def load_data():
            try:
                data = loader_func()
                self.loaded_data[key] = {
                    'data': data,
                    'loaded_at': datetime.now()
                }
            except Exception as e:
                st.error(f"Erro ao carregar dados: {e}")
                self.loaded_data[key] = {
                    'data': None,
                    'error': str(e),
                    'loaded_at': datetime.now()
                }
            finally:
                self.loading_states[key] = False
        
        thread = threading.Thread(target=load_data)
        thread.daemon = True
        thread.start()
        self.loading_threads[key] = thread
    
    def get_loading_status(self, key: str) -> Dict[str, Any]:
        """Retorna status de carregamento"""
        return {
            'is_loading': self.loading_states.get(key, False),
            'is_loaded': key in self.loaded_data,
            'data': self.loaded_data.get(key, {}).get('data'),
            'error': self.loaded_data.get(key, {}).get('error'),
            'loaded_at': self.loaded_data.get(key, {}).get('loaded_at')
        }
    
    def clear_cache(self, key: Optional[str] = None):
        """Limpa cache de dados"""
        if key:
            self.loaded_data.pop(key, None)
            self.loading_states.pop(key, None)
        else:
            self.loaded_data.clear()
            self.loading_states.clear()

# Instância global
lazy_loader = LazyLoader()

class ProgressiveLoader:
    """Carregador progressivo para grandes datasets"""
    
    @staticmethod
    def load_dataframe_progressive(query: str, 
                                 chunk_size: int = 1000,
                                 max_rows: int = 10000) -> pd.DataFrame:
        """Carrega DataFrame de forma progressiva"""
        from app.database.local_connection import db_manager
        
        # Primeiro, contar total de registros
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
        total_result = db_manager.fetch_all(count_query)
        total_rows = total_result[0]['total'] if total_result else 0
        
        if total_rows == 0:
            return pd.DataFrame()
        
        # Limitar ao máximo especificado
        actual_rows = min(total_rows, max_rows)
        
        # Criar placeholder para progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        chunks = []
        offset = 0
        
        while offset < actual_rows:
            current_chunk_size = min(chunk_size, actual_rows - offset)
            
            # Query com LIMIT e OFFSET
            chunk_query = f"{query} LIMIT {current_chunk_size} OFFSET {offset}"
            from app.database.local_connection import db_manager
            chunk_data = db_manager.fetch_all(chunk_query)
            
            if chunk_data:
                chunks.append(pd.DataFrame(chunk_data))
            
            offset += current_chunk_size
            progress = offset / actual_rows
            
            progress_bar.progress(progress)
            status_text.text(f"Carregando... {offset}/{actual_rows} registros")
            
            # Pequena pausa para não travar a interface
            time.sleep(0.01)
        
        # Limpar indicadores de progresso
        progress_bar.empty()
        status_text.empty()
        
        # Combinar todos os chunks
        if chunks:
            return pd.concat(chunks, ignore_index=True)
        else:
            return pd.DataFrame()

class VirtualizedTable:
    """Tabela virtualizada para grandes datasets"""
    
    def __init__(self, data: pd.DataFrame, page_size: int = 50):
        self.data = data
        self.page_size = page_size
        self.total_rows = len(data)
        self.total_pages = (self.total_rows - 1) // page_size + 1 if self.total_rows > 0 else 0
    
    def render(self, key: str = "virtualized_table"):
        """Renderiza tabela virtualizada"""
        if self.total_rows == 0:
            st.info("Nenhum dado disponível")
            return
        
        # Controles de navegação
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
        
        with col1:
            current_page = st.number_input(
                "Página",
                min_value=1,
                max_value=self.total_pages,
                value=st.session_state.get(f"{key}_page", 1),
                key=f"{key}_page_input"
            )
        
        with col2:
            st.metric("Total de Registros", self.total_rows)
        
        with col3:
            st.metric("Total de Páginas", self.total_pages)
        
        with col4:
            page_size = st.selectbox(
                "Por página",
                [25, 50, 100, 200],
                index=1,
                key=f"{key}_page_size"
            )
        
        # Atualizar page_size se mudou
        if page_size != self.page_size:
            self.page_size = page_size
            self.total_pages = (self.total_rows - 1) // page_size + 1
            current_page = 1
        
        # Calcular índices da página atual
        start_idx = (current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, self.total_rows)
        
        # Exibir dados da página atual
        page_data = self.data.iloc[start_idx:end_idx]
        st.dataframe(page_data, use_container_width=True)
        
        # Controles de navegação inferior
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("⏮️ Primeira", disabled=current_page == 1, key=f"{key}_first"):
                st.session_state[f"{key}_page"] = 1
                st.rerun()
        
        with col2:
            if st.button("⬅️ Anterior", disabled=current_page == 1, key=f"{key}_prev"):
                st.session_state[f"{key}_page"] = current_page - 1
                st.rerun()
        
        with col3:
            st.markdown(f"<div style='text-align: center; padding: 8px;'>"
                       f"Mostrando {start_idx + 1}-{end_idx} de {self.total_rows}"
                       f"</div>", unsafe_allow_html=True)
        
        with col4:
            if st.button("➡️ Próxima", disabled=current_page == self.total_pages, key=f"{key}_next"):
                st.session_state[f"{key}_page"] = current_page + 1
                st.rerun()
        
        with col5:
            if st.button("⏭️ Última", disabled=current_page == self.total_pages, key=f"{key}_last"):
                st.session_state[f"{key}_page"] = self.total_pages
                st.rerun()
        
        # Salvar página atual no session_state
        st.session_state[f"{key}_page"] = current_page

# Funções utilitárias para carregamento lazy
def lazy_load_users():
    """Carrega usuários de forma lazy"""
    from app.database.local_connection import db_manager
    
    query = """
        SELECT id, username, full_name, email, role, is_active, created_at
        FROM users 
        ORDER BY created_at DESC
    """
    return db_manager.fetch_all(query)

def lazy_load_events():
    """Carrega eventos de forma lazy"""
    from app.database.local_connection import db_manager
    
    query = """
        SELECT id, title, event_type, start_datetime, end_datetime, 
               location, description, is_active
        FROM events 
        ORDER BY start_datetime DESC
    """
    return db_manager.fetch_all(query)

def lazy_load_dashboard_stats():
    """Carrega estatísticas do dashboard de forma lazy"""
    from app.database.local_connection import db_manager
    
    stats = {}
    
    # Carregar estatísticas básicas
    queries = {
        'total_users': "SELECT COUNT(*) as count FROM users WHERE is_active = 1",
        'total_events': "SELECT COUNT(*) as count FROM events WHERE is_active = 1",
        'upcoming_events': "SELECT COUNT(*) as count FROM events WHERE start_datetime > datetime('now')",
        'this_month_events': """
            SELECT COUNT(*) as count FROM events 
            WHERE strftime('%Y-%m', start_datetime) = strftime('%Y-%m', 'now')
        """
    }
    
    for key, query in queries.items():
        try:
            result = db_manager.fetch_all(query)
            stats[key] = result[0]['count'] if result else 0
        except:
            stats[key] = 0
    
    return stats

# Decorators para carregamento lazy
def lazy_component(loader_func: Callable, 
                  placeholder: str = "Carregando...",
                  cache_minutes: int = 5):
    """Decorator para componentes lazy"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return lazy_loader.lazy_component(
                loader_func, 
                placeholder, 
                func.__name__,
                cache_minutes
            )(func)(*args, **kwargs)
        return wrapper
    return decorator

def progressive_dataframe(chunk_size: int = 1000, max_rows: int = 10000):
    """Decorator para DataFrames progressivos"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            query = func(*args, **kwargs)
            return ProgressiveLoader.load_dataframe_progressive(
                query, chunk_size, max_rows
            )
        return wrapper
    return decorator