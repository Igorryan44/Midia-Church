#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Correção de Problemas Detectados
Corrige automaticamente os problemas identificados nos testes intensivos
"""

import sys
import os
import shutil
from pathlib import Path

# Adicionar o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def fix_sqlalchemy_deprecation():
    """Corrige warnings de deprecação do SQLAlchemy"""
    print("🔧 Corrigindo warnings de deprecação do SQLAlchemy...")
    
    files_to_fix = [
        project_root / "app" / "database" / "models.py",
        project_root / "app" / "modules" / "ai_assistant.py",
        project_root / "app" / "services" / "message_manager.py"
    ]
    
    for file_path in files_to_fix:
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Substituir imports deprecados
                old_imports = [
                    "from sqlalchemy.ext.declarative import declarative_base",
                    "from sqlalchemy.ext.declarative import DeclarativeMeta"
                ]
                
                new_imports = [
                    "from sqlalchemy.orm import declarative_base",
                    "from sqlalchemy.orm import DeclarativeMeta"
                ]
                
                modified = False
                for old_import, new_import in zip(old_imports, new_imports):
                    if old_import in content:
                        content = content.replace(old_import, new_import)
                        modified = True
                        print(f"  ✅ {file_path.name}: Corrigido import deprecado")
                
                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
            except Exception as e:
                print(f"  ❌ Erro ao corrigir {file_path.name}: {str(e)}")
        else:
            print(f"  ⚠️ Arquivo não encontrado: {file_path}")

def fix_configuration_types():
    """Corrige tipos incorretos nas configurações"""
    print("\n🔧 Corrigindo tipos de configuração...")
    
    config_file = project_root / "app" / "config" / "settings.py"
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Garantir que UPLOAD_DIR seja string
            if "UPLOAD_DIR" in content and "Path(" in content:
                # Procurar por padrões como Path(...) e converter para str(Path(...))
                import re
                pattern = r"'UPLOAD_DIR':\s*Path\([^)]+\)"
                matches = re.findall(pattern, content)
                
                for match in matches:
                    new_match = match.replace("Path(", "str(Path(").replace(")", "))")
                    content = content.replace(match, new_match)
                    print("  ✅ UPLOAD_DIR: Convertido para string")
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            
        except Exception as e:
            print(f"  ❌ Erro ao corrigir configurações: {str(e)}")
    else:
        print("  ⚠️ Arquivo de configuração não encontrado")

def create_missing_directories():
    """Cria diretórios ausentes"""
    print("\n🔧 Criando diretórios ausentes...")
    
    directories_to_create = [
        project_root / "static",
        project_root / "static" / "css",
        project_root / "static" / "js",
        project_root / "static" / "images",
        project_root / "logs",
        project_root / "temp",
        project_root / "downloads"
    ]
    
    for directory in directories_to_create:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Diretório criado: {directory.name}")
        except Exception as e:
            print(f"  ❌ Erro ao criar {directory}: {str(e)}")

def fix_database_connections():
    """Corrige problemas de conexão com banco de dados"""
    print("\n🔧 Corrigindo conexões de banco de dados...")
    
    connection_file = project_root / "app" / "database" / "connection.py"
    
    if connection_file.exists():
        try:
            with open(connection_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Adicionar context manager para conexões
            if "def get_connection():" in content and "with sqlite3.connect" not in content:
                # Procurar pela função get_connection e modificar
                lines = content.split('\n')
                new_lines = []
                in_get_connection = False
                
                for line in lines:
                    if "def get_connection():" in line:
                        in_get_connection = True
                        new_lines.append(line)
                        new_lines.append('    """Retorna conexão com o banco usando context manager"""')
                    elif in_get_connection and line.strip().startswith("return sqlite3.connect"):
                        # Substituir por context manager
                        db_path_line = line.strip()
                        new_lines.append(f"    conn = {db_path_line}")
                        new_lines.append("    conn.row_factory = sqlite3.Row")
                        new_lines.append("    return conn")
                        in_get_connection = False
                    else:
                        new_lines.append(line)
                
                modified_content = '\n'.join(new_lines)
                
                with open(connection_file, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                print("  ✅ Conexões de banco otimizadas")
            
        except Exception as e:
            print(f"  ❌ Erro ao corrigir conexões: {str(e)}")

def optimize_imports():
    """Otimiza imports para melhorar performance"""
    print("\n🔧 Otimizando imports para performance...")
    
    # Arquivos que podem ter imports pesados
    files_to_optimize = [
        project_root / "app" / "modules" / "dashboard.py",
        project_root / "app" / "modules" / "content_management.py",
        project_root / "app" / "modules" / "ai_assistant.py"
    ]
    
    for file_path in files_to_optimize:
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Mover imports pesados para dentro de funções (lazy loading)
                heavy_imports = [
                    "import pandas as pd",
                    "import plotly",
                    "import numpy as np"
                ]
                
                modified = False
                for heavy_import in heavy_imports:
                    if heavy_import in content and "def " in content:
                        # Se o import está no topo e há funções, sugerir lazy loading
                        lines = content.split('\n')
                        if any(line.strip() == heavy_import for line in lines[:20]):
                            print(f"  ⚠️ {file_path.name}: Import pesado detectado - {heavy_import}")
                            print(f"    💡 Considere mover para lazy loading dentro das funções")
                
            except Exception as e:
                print(f"  ❌ Erro ao analisar {file_path.name}: {str(e)}")

def add_memory_optimization():
    """Adiciona otimizações de memória"""
    print("\n🔧 Adicionando otimizações de memória...")
    
    # Criar arquivo de otimização de memória
    memory_optimizer_file = project_root / "app" / "utils" / "memory_optimizer_enhanced.py"
    
    memory_optimizer_content = '''#!/usr/bin/env python3
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
'''
    
    try:
        with open(memory_optimizer_file, 'w', encoding='utf-8') as f:
            f.write(memory_optimizer_content)
        print("  ✅ Otimizador de memória aprimorado criado")
    except Exception as e:
        print(f"  ❌ Erro ao criar otimizador: {str(e)}")

def create_error_handler():
    """Cria sistema robusto de tratamento de erros"""
    print("\n🔧 Criando sistema de tratamento de erros...")
    
    error_handler_file = project_root / "app" / "utils" / "error_handler.py"
    
    error_handler_content = '''#!/usr/bin/env python3
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
'''
    
    try:
        with open(error_handler_file, 'w', encoding='utf-8') as f:
            f.write(error_handler_content)
        print("  ✅ Sistema de tratamento de erros criado")
    except Exception as e:
        print(f"  ❌ Erro ao criar error handler: {str(e)}")

def main():
    """Executa todas as correções"""
    print("🔧 INICIANDO CORREÇÃO DE PROBLEMAS DETECTADOS")
    print("=" * 60)
    
    corrections = [
        ("SQLAlchemy Deprecation", fix_sqlalchemy_deprecation),
        ("Tipos de Configuração", fix_configuration_types),
        ("Diretórios Ausentes", create_missing_directories),
        ("Conexões de Banco", fix_database_connections),
        ("Otimização de Imports", optimize_imports),
        ("Otimização de Memória", add_memory_optimization),
        ("Tratamento de Erros", create_error_handler)
    ]
    
    for correction_name, correction_func in corrections:
        try:
            correction_func()
        except Exception as e:
            print(f"❌ Erro ao executar {correction_name}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ CORREÇÕES CONCLUÍDAS!")
    print("💡 Execute os testes novamente para verificar melhorias.")
    print("🚀 Reinicie a aplicação para aplicar todas as mudanças.")

if __name__ == "__main__":
    main()