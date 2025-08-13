#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Robusto de Tratamento de Erros
Captura, registra e trata erros de forma elegante
"""

import logging
import traceback
import streamlit as st
from functools import wraps
from typing import Any, Callable, Optional
from pathlib import Path

# Configurar logging
log_dir = Path(__file__).parent.parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "app_errors.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Gerenciador centralizado de erros"""
    
    @staticmethod
    def handle_database_error(error: Exception, context: str = "") -> None:
        """Trata erros de banco de dados"""
        logger.error(f"Erro de banco de dados {context}: {str(error)}")
        st.error("❌ Erro de conexão com banco de dados. Tente novamente.")
    
    @staticmethod
    def handle_file_error(error: Exception, context: str = "") -> None:
        """Trata erros de arquivo"""
        logger.error(f"Erro de arquivo {context}: {str(error)}")
        st.error("❌ Erro ao processar arquivo. Verifique o formato.")
    
    @staticmethod
    def handle_api_error(error: Exception, context: str = "") -> None:
        """Trata erros de API"""
        logger.error(f"Erro de API {context}: {str(error)}")
        st.error("❌ Erro de comunicação. Verifique sua conexão.")
    
    @staticmethod
    def handle_validation_error(error: Exception, context: str = "") -> None:
        """Trata erros de validação"""
        logger.warning(f"Erro de validação {context}: {str(error)}")
        st.warning("⚠️ Dados inválidos. Verifique as informações inseridas.")
    
    @staticmethod
    def handle_generic_error(error: Exception, context: str = "") -> None:
        """Trata erros genéricos"""
        logger.error(f"Erro genérico {context}: {str(error)}")
        logger.error(traceback.format_exc())
        st.error("❌ Ocorreu um erro inesperado. Tente novamente.")

def safe_execute(func: Callable) -> Callable:
    """Decorator para execução segura com tratamento de erros"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            ErrorHandler.handle_file_error(e, f"em {func.__name__}")
            return None
        except ConnectionError as e:
            ErrorHandler.handle_api_error(e, f"em {func.__name__}")
            return None
        except ValueError as e:
            ErrorHandler.handle_validation_error(e, f"em {func.__name__}")
            return None
        except Exception as e:
            ErrorHandler.handle_generic_error(e, f"em {func.__name__}")
            return None
    
    return wrapper

def with_error_boundary(title: str = "Erro"):
    """Context manager para captura de erros em blocos de código"""
    class ErrorBoundary:
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                logger.error(f"Erro em {title}: {exc_val}")
                st.error(f"❌ {title}: {str(exc_val)}")
                return True  # Suprimir exceção
            return False
    
    return ErrorBoundary()
