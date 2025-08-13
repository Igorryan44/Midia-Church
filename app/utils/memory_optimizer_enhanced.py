#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Otimizador de Memória Aprimorado
Gerencia uso de memória e previne vazamentos
"""

import gc
import sys
import weakref
from functools import wraps
from typing import Any, Callable

class MemoryManager:
    """Gerenciador de memória para a aplicação"""
    
    def __init__(self):
        self._tracked_objects = weakref.WeakSet()
        self._memory_threshold = 100 * 1024 * 1024  # 100MB
    
    def track_object(self, obj: Any) -> Any:
        """Rastreia objeto para limpeza automática"""
        self._tracked_objects.add(obj)
        return obj
    
    def cleanup(self) -> int:
        """Força limpeza de memória"""
        collected = gc.collect()
        return collected
    
    def get_memory_usage(self) -> int:
        """Retorna uso atual de memória em bytes"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            return sys.getsizeof(gc.get_objects())
    
    def check_memory_threshold(self) -> bool:
        """Verifica se uso de memória excede limite"""
        return self.get_memory_usage() > self._memory_threshold

# Instância global do gerenciador
memory_manager = MemoryManager()

def memory_optimized(func: Callable) -> Callable:
    """Decorator para otimização automática de memória"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # Verificar uso de memória após execução
            if memory_manager.check_memory_threshold():
                collected = memory_manager.cleanup()
                print(f"🧹 Limpeza de memória: {collected} objetos coletados")
            
            return result
        except Exception as e:
            # Limpar memória em caso de erro
            memory_manager.cleanup()
            raise e
    
    return wrapper

def optimize_dataframe(df):
    """Otimiza DataFrame para uso eficiente de memória"""
    try:
        import pandas as pd
        
        if isinstance(df, pd.DataFrame):
            # Otimizar tipos de dados
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].nunique() / len(df) < 0.5:  # Se menos de 50% valores únicos
                    df[col] = df[col].astype('category')
            
            # Otimizar tipos numéricos
            for col in df.select_dtypes(include=['int64']).columns:
                if df[col].min() >= 0 and df[col].max() <= 255:
                    df[col] = df[col].astype('uint8')
                elif df[col].min() >= -128 and df[col].max() <= 127:
                    df[col] = df[col].astype('int8')
        
        return df
    except ImportError:
        return df

def clear_cache():
    """Limpa caches da aplicação"""
    try:
        import streamlit as st
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
        if hasattr(st, 'cache_resource'):
            st.cache_resource.clear()
    except:
        pass
    
    # Limpeza manual de garbage collection
    for i in range(3):
        gc.collect()
