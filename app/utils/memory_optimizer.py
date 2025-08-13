"""
Otimizador de Memória para Mídia Church
Gerencia uso de memória e limpeza automática
"""

import gc
import psutil
import streamlit as st
import pandas as pd
import threading
import time
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import wraps
import weakref

class MemoryOptimizer:
    """Gerenciador de otimização de memória"""
    
    def __init__(self):
        self.memory_threshold = 80  # Porcentagem de uso de memória para limpeza
        self.cleanup_interval = 300  # 5 minutos
        self.last_cleanup = datetime.now()
        self.memory_stats = {}
        self.large_objects = weakref.WeakSet()
        self._monitoring = False
        
    def start_monitoring(self):
        """Inicia monitoramento automático de memória"""
        if self._monitoring:
            return
            
        self._monitoring = True
        
        def monitor_loop():
            while self._monitoring:
                try:
                    self._check_memory_usage()
                    time.sleep(60)  # Verificar a cada minuto
                except Exception as e:
                    print(f"Erro no monitoramento de memória: {e}")
                    
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
    
    def stop_monitoring(self):
        """Para monitoramento de memória"""
        self._monitoring = False
    
    def _check_memory_usage(self):
        """Verifica uso de memória e executa limpeza se necessário"""
        memory_percent = psutil.virtual_memory().percent
        
        if memory_percent > self.memory_threshold:
            self.cleanup_memory()
            
        # Atualizar estatísticas
        self.memory_stats = {
            'memory_percent': memory_percent,
            'memory_available': psutil.virtual_memory().available,
            'memory_used': psutil.virtual_memory().used,
            'last_check': datetime.now()
        }
    
    def cleanup_memory(self, force: bool = False):
        """Executa limpeza de memória"""
        now = datetime.now()
        
        # Verificar se já passou tempo suficiente desde última limpeza
        if not force and (now - self.last_cleanup).seconds < self.cleanup_interval:
            return
        
        # Limpar cache do Streamlit
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
        if hasattr(st, 'cache_resource'):
            st.cache_resource.clear()
        
        # Limpar session_state de itens antigos
        self._cleanup_session_state()
        
        # Forçar garbage collection
        collected = gc.collect()
        
        self.last_cleanup = now
        
        print(f"Limpeza de memória executada. Objetos coletados: {collected}")
    
    def _cleanup_session_state(self):
        """Limpa itens antigos do session_state"""
        if not hasattr(st, 'session_state'):
            return
            
        # Remover itens temporários antigos
        keys_to_remove = []
        for key in st.session_state.keys():
            if key.startswith('temp_') or key.startswith('cache_'):
                # Verificar se é muito antigo (mais de 1 hora)
                if hasattr(st.session_state[key], 'timestamp'):
                    timestamp = getattr(st.session_state[key], 'timestamp', datetime.now())
                    if (datetime.now() - timestamp).seconds > 3600:
                        keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state[key]
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de memória"""
        memory = psutil.virtual_memory()
        
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent,
            'free': memory.free,
            'last_cleanup': self.last_cleanup,
            'cleanup_interval': self.cleanup_interval,
            'threshold': self.memory_threshold
        }
    
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Otimiza DataFrame para usar menos memória"""
        if df.empty:
            return df
        
        # Criar cópia para não modificar original
        optimized_df = df.copy()
        
        # Otimizar tipos de dados
        for col in optimized_df.columns:
            col_type = optimized_df[col].dtype
            
            # Otimizar inteiros
            if col_type == 'int64':
                if optimized_df[col].min() >= 0:
                    if optimized_df[col].max() < 255:
                        optimized_df[col] = optimized_df[col].astype('uint8')
                    elif optimized_df[col].max() < 65535:
                        optimized_df[col] = optimized_df[col].astype('uint16')
                    elif optimized_df[col].max() < 4294967295:
                        optimized_df[col] = optimized_df[col].astype('uint32')
                else:
                    if optimized_df[col].min() > -128 and optimized_df[col].max() < 127:
                        optimized_df[col] = optimized_df[col].astype('int8')
                    elif optimized_df[col].min() > -32768 and optimized_df[col].max() < 32767:
                        optimized_df[col] = optimized_df[col].astype('int16')
                    elif optimized_df[col].min() > -2147483648 and optimized_df[col].max() < 2147483647:
                        optimized_df[col] = optimized_df[col].astype('int32')
            
            # Otimizar floats
            elif col_type == 'float64':
                optimized_df[col] = optimized_df[col].astype('float32')
            
            # Otimizar strings para categorias se houver repetição
            elif col_type == 'object':
                unique_ratio = len(optimized_df[col].unique()) / len(optimized_df[col])
                if unique_ratio < 0.5:  # Se menos de 50% são únicos
                    optimized_df[col] = optimized_df[col].astype('category')
        
        return optimized_df
    
    def register_large_object(self, obj):
        """Registra objeto grande para monitoramento"""
        self.large_objects.add(obj)
    
    def memory_efficient_decorator(self, cleanup_after: bool = True):
        """Decorator para funções que usam muita memória"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Verificar memória antes
                memory_before = psutil.virtual_memory().percent
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Otimizar resultado se for DataFrame
                    if isinstance(result, pd.DataFrame):
                        result = self.optimize_dataframe(result)
                        self.register_large_object(result)
                    
                    return result
                    
                finally:
                    if cleanup_after:
                        # Verificar memória depois
                        memory_after = psutil.virtual_memory().percent
                        
                        # Se uso de memória aumentou muito, fazer limpeza
                        if memory_after - memory_before > 10:
                            gc.collect()
                
            return wrapper
        return decorator

class DataFrameOptimizer:
    """Otimizador específico para DataFrames"""
    
    @staticmethod
    def reduce_memory_usage(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
        """Reduz uso de memória de DataFrame"""
        start_mem = df.memory_usage(deep=True).sum() / 1024**2
        
        for col in df.columns:
            col_type = df[col].dtype
            
            if col_type != object:
                c_min = df[col].min()
                c_max = df[col].max()
                
                if str(col_type)[:3] == 'int':
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        df[col] = df[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        df[col] = df[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        df[col] = df[col].astype(np.int32)
                    elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                        df[col] = df[col].astype(np.int64)
                else:
                    if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                        df[col] = df[col].astype(np.float16)
                    elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                        df[col] = df[col].astype(np.float32)
                    else:
                        df[col] = df[col].astype(np.float64)
            else:
                df[col] = df[col].astype('category')
        
        end_mem = df.memory_usage(deep=True).sum() / 1024**2
        
        if verbose:
            print(f'Uso de memória reduzido de {start_mem:.2f} MB para {end_mem:.2f} MB '
                  f'({100 * (start_mem - end_mem) / start_mem:.1f}% de redução)')
        
        return df
    
    @staticmethod
    def chunk_dataframe(df: pd.DataFrame, chunk_size: int = 1000):
        """Divide DataFrame em chunks menores"""
        for i in range(0, len(df), chunk_size):
            yield df.iloc[i:i + chunk_size]

class CacheOptimizer:
    """Otimizador de cache"""
    
    def __init__(self, max_cache_size_mb: int = 100):
        self.max_cache_size_mb = max_cache_size_mb
        self.cache_stats = {}
    
    def smart_cache_clear(self):
        """Limpeza inteligente de cache baseada em uso"""
        if hasattr(st, 'cache_data'):
            # Limpar cache se muito grande
            cache_size = self._estimate_cache_size()
            if cache_size > self.max_cache_size_mb:
                st.cache_data.clear()
                print(f"Cache limpo - tamanho estimado: {cache_size:.2f} MB")
    
    def _estimate_cache_size(self) -> float:
        """Estima tamanho do cache em MB"""
        # Implementação simplificada
        # Em produção, seria necessário uma implementação mais sofisticada
        return 50.0  # Placeholder

# Instância global
memory_optimizer = MemoryOptimizer()

# Decorators úteis
def memory_efficient(cleanup_after: bool = True):
    """Decorator para funções que usam muita memória"""
    return memory_optimizer.memory_efficient_decorator(cleanup_after)

def optimize_dataframe(func):
    """Decorator para otimizar DataFrames retornados"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, pd.DataFrame):
            return memory_optimizer.optimize_dataframe(result)
        return result
    return wrapper

# Funções utilitárias
def get_memory_usage() -> Dict[str, Any]:
    """Retorna informações de uso de memória"""
    return memory_optimizer.get_memory_stats()

def force_cleanup():
    """Força limpeza de memória"""
    memory_optimizer.cleanup_memory(force=True)

def start_memory_monitoring():
    """Inicia monitoramento automático"""
    memory_optimizer.start_monitoring()

def render_memory_widget():
    """Renderiza widget de monitoramento de memória"""
    stats = get_memory_usage()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Uso de Memória",
            f"{stats['percent']:.1f}%",
            delta=f"{stats['used'] / 1024**3:.1f} GB"
        )
    
    with col2:
        st.metric(
            "Memória Disponível",
            f"{stats['available'] / 1024**3:.1f} GB"
        )
    
    with col3:
        if st.button("🧹 Limpar Memória"):
            force_cleanup()
            st.success("Limpeza executada!")
            st.rerun()
    
    # Barra de progresso visual
    progress_color = "red" if stats['percent'] > 80 else "orange" if stats['percent'] > 60 else "green"
    st.markdown(f"""
        <div style="background-color: #f0f0f0; border-radius: 10px; padding: 10px; margin: 10px 0;">
            <div style="background-color: {progress_color}; height: 20px; width: {stats['percent']}%; 
                        border-radius: 10px; transition: width 0.3s ease;"></div>
        </div>
    """, unsafe_allow_html=True)