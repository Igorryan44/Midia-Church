"""
Conexão com banco de dados usando SQLAlchemy e Supabase
"""

import os
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Date, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import bcrypt
from dotenv import load_dotenv
from supabase import create_client, Client
import psycopg2
import sqlite3

from app.database.models import Base, User, Event, Attendance, MediaContent, Post, Comment, Routine, AIConversation, SecurityLog, SystemSetting, Message

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gerenciador de conexão com o banco de dados"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.supabase_client = None
        self.logger = logging.getLogger(__name__)
        self.database_type = "sqlite"  # Default
        self._setup_database()
    
    def _setup_database(self):
        """Configura a conexão com o banco de dados"""
        load_dotenv()  # Load environment variables
        
        # Check if Supabase should be used
        use_supabase = os.getenv('USE_SUPABASE', 'false').lower() == 'true'
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        database_url = os.getenv('DATABASE_URL')
        
        # Verificar se é uma configuração válida do Supabase
        if (use_supabase and supabase_url and supabase_key and database_url and 
            database_url.startswith('postgresql://') and 
            'supabase.co' in database_url and
            not '[YOUR-PROJECT-REF]' in database_url):
            
            try:
                logger.info("Tentando conectar ao Supabase PostgreSQL...")
                
                # Test Supabase connection
                if self._test_supabase_connection(supabase_url, supabase_key):
                    # Create Supabase client
                    self.supabase_client = create_client(supabase_url, supabase_key)
                    
                    self.engine = create_engine(
                        database_url,
                        pool_pre_ping=True,
                        pool_recycle=300,
                        echo=os.getenv('DEBUG', 'False').lower() == 'true'
                    )
                    
                    # Testar conexão
                    with self.engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    
                    self.database_type = "supabase"
                    logger.info("✅ Conectado ao Supabase PostgreSQL com sucesso!")
                else:
                    logger.warning("⚠️ Teste de conexão Supabase falhou")
                    logger.info("🔄 Usando SQLite como fallback...")
                    self._setup_sqlite_fallback()
                
            except Exception as e:
                logger.warning(f"⚠️ Falha ao conectar ao Supabase: {e}")
                logger.info("🔄 Usando SQLite como fallback...")
                self._setup_sqlite_fallback()
        else:
            logger.info("🔄 Configuração do Supabase não encontrada, usando SQLite...")
            self._setup_sqlite_fallback()
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def _setup_sqlite_fallback(self):
        """Configura SQLite como fallback"""
        # Criar diretório data se não existir
        os.makedirs('data', exist_ok=True)
        
        sqlite_url = "sqlite:///data/church_media.db"
        self.engine = create_engine(
            sqlite_url,
            connect_args={"check_same_thread": False},
            echo=os.getenv('DEBUG', 'False').lower() == 'true'
        )
        self.database_type = "sqlite"
        logger.info("✅ Usando SQLite como banco de dados")
    
    def _test_supabase_connection(self, supabase_url: str, supabase_key: str) -> bool:
        """Test Supabase connection"""
        try:
            test_client = create_client(supabase_url, supabase_key)
            # Try a simple operation to test connection
            test_client.table('users').select('*').limit(1).execute()
            return True
        except Exception as e:
            self.logger.warning(f"Supabase connection test failed: {e}")
            return False
    
    @contextmanager
    def get_db_session(self) -> Session:
        """Context manager para sessões do banco"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erro na sessão do banco: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Cria todas as tabelas no banco"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Tabelas criadas/verificadas com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")
            raise
    
    def get_session(self) -> Session:
        """Retorna uma nova sessão do banco de dados"""
        return self.SessionLocal()
    
    def get_engine(self):
        """Retorna o engine do banco"""
        return self.engine
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None, fetch: bool = False) -> Any:
        """
        Executa uma query SQL usando SQLAlchemy
        
        Args:
            query: Query SQL para executar
            params: Parâmetros para a query
            fetch: Se True, retorna os resultados; se False, executa e retorna lastrowid
        
        Returns:
            Resultados da query ou lastrowid
        """
        try:
            with self.get_db_session() as session:
                if fetch:
                    result = session.execute(text(query), params or {})
                    return [dict(row._mapping) for row in result.fetchall()]
                else:
                    result = session.execute(text(query), params or {})
                    return result.lastrowid
                    
        except Exception as e:
            print(f"❌ Erro ao executar query: {e}")
            raise e
    
    def get_database_type(self) -> str:
        """Get current database type"""
        return self.database_type
    
    def execute_raw_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        """Execute raw SQL query"""
        try:
            with self.get_db_session() as session:
                result = session.execute(text(query), params or {})
                session.commit()
                return result
        except Exception as e:
            self.logger.error(f"Raw query execution failed: {e}")
            raise
    
    def get_table_count(self, table_name: str) -> int:
        """Get count of records in a table"""
        try:
            if self.database_type == "supabase" and self.supabase_client:
                result = self.supabase_client.table(table_name).select('*', count='exact').execute()
                return result.count
            else:
                with self.get_db_session() as session:
                    result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    return result.scalar()
        except Exception as e:
            self.logger.error(f"Failed to get table count for {table_name}: {e}")
            return 0
    
    def upsert_data(self, table_name: str, data: Dict[str, Any]) -> bool:
        """Upsert data using Supabase client or SQLAlchemy"""
        try:
            if self.database_type == "supabase" and self.supabase_client:
                result = self.supabase_client.table(table_name).upsert(data).execute()
                return True
            else:
                # For SQLite, implement upsert logic with SQLAlchemy
                # This would need to be customized based on your models
                return False
        except Exception as e:
            self.logger.error(f"Upsert failed for table {table_name}: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get database health status"""
        try:
            status = {
                "database_type": self.database_type,
                "connected": False,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.database_type == "supabase" and self.supabase_client:
                # Test Supabase connection
                self.supabase_client.table('users').select('id').limit(1).execute()
                status["connected"] = True
                status["supabase_client"] = True
            else:
                # Test SQLAlchemy connection
                with self.get_db_session() as session:
                    session.execute(text("SELECT 1"))
                status["connected"] = True
                status["supabase_client"] = False
            
            return status
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "database_type": self.database_type,
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Instância global do gerenciador
db_manager = DatabaseManager()

def init_database():
    """Inicializa o banco de dados com as tabelas e dados iniciais"""
    try:
        # Criar todas as tabelas
        db_manager.create_tables()
        
        # Criar usuário admin padrão se não existir
        with db_manager.get_db_session() as session:
            admin_user = session.query(User).filter(User.username == 'admin').first()
            
            if not admin_user:
                password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                admin_user = User(
                    username='admin',
                    email='admin@igreja.com',
                    password_hash=password_hash,
                    full_name='Administrador',
                    role='admin'
                )
                session.add(admin_user)
                session.commit()
                print("✅ Usuário admin criado com sucesso")
        
        print("✅ Banco de dados inicializado com sucesso")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        raise e

def execute_query(query: str, params: Optional[Dict[str, Any]] = None, fetch: bool = False) -> Any:
    """
    Executa uma query SQL usando SQLAlchemy
    
    Args:
        query: Query SQL para executar
        params: Parâmetros para a query
        fetch: Se True, retorna os resultados; se False, executa e retorna lastrowid
    
    Returns:
        Resultados da query ou lastrowid
    """
    try:
        with db_manager.get_db_session() as session:
            if fetch:
                result = session.execute(text(query), params or {})
                return [dict(row._mapping) for row in result.fetchall()]
            else:
                result = session.execute(text(query), params or {})
                session.commit()
                return result.lastrowid
                
    except Exception as e:
        print(f"❌ Erro ao executar query: {e}")
        raise e

# Funções de conveniência para operações comuns

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Busca usuário por username"""
    try:
        with db_manager.get_db_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'password_hash': user.password_hash,
                    'full_name': user.full_name,
                    'phone': user.phone,
                    'role': user.role,
                    'created_at': user.created_at,
                    'is_active': user.is_active
                }
            return None
    except Exception as e:
        print(f"❌ Erro ao buscar usuário: {e}")
        return None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Busca usuário por email"""
    try:
        with db_manager.get_db_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'password_hash': user.password_hash,
                    'full_name': user.full_name,
                    'phone': user.phone,
                    'role': user.role,
                    'created_at': user.created_at,
                    'is_active': user.is_active
                }
            return None
    except Exception as e:
        print(f"❌ Erro ao buscar usuário por email: {e}")
        return None

def create_user(username: str, email: str, password_hash: str, full_name: str, 
                phone: str = None, role: str = 'member') -> Optional[int]:
    """Cria um novo usuário"""
    try:
        with db_manager.get_db_session() as session:
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                phone=phone,
                role=role
            )
            session.add(user)
            session.commit()
            return user.id
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        return None

def get_all_users() -> List[Dict[str, Any]]:
    """Retorna todos os usuários"""
    try:
        with db_manager.get_db_session() as session:
            users = session.query(User).filter(User.is_active == True).all()
            return [{
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'phone': user.phone,
                'role': user.role,
                'created_at': user.created_at,
                'is_active': user.is_active
            } for user in users]
    except Exception as e:
        print(f"❌ Erro ao buscar usuários: {e}")
        return []

def get_events() -> List[Dict[str, Any]]:
    """Retorna todos os eventos ativos"""
    try:
        with db_manager.get_db_session() as session:
            events = session.query(Event).filter(Event.is_active == True).all()
            return [{
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'event_type': event.event_type,
                'start_datetime': event.start_datetime,
                'end_datetime': event.end_datetime,
                'location': event.location,
                'created_by': event.created_by,
                'created_at': event.created_at,
                'is_active': event.is_active
            } for event in events]
    except Exception as e:
        print(f"❌ Erro ao buscar eventos: {e}")
        return []

def create_event(title: str, description: str, event_type: str, start_datetime, 
                end_datetime, location: str = None, created_by: int = None) -> Optional[int]:
    """Cria um novo evento"""
    try:
        with db_manager.get_db_session() as session:
            event = Event(
                title=title,
                description=description,
                event_type=event_type,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                location=location,
                created_by=created_by
            )
            session.add(event)
            session.commit()
            return event.id
    except Exception as e:
        print(f"❌ Erro ao criar evento: {e}")
        return None

def log_security_event(event_type: str, description: str, user_id: str = None, ip_address: str = None):
    """Registra um evento de segurança"""
    try:
        with db_manager.get_db_session() as session:
            log = SecurityLog(
                event_type=event_type,
                description=description,
                user_id=user_id,
                ip_address=ip_address
            )
            session.add(log)
            session.commit()
    except Exception as e:
        print(f"❌ Erro ao registrar log de segurança: {e}")

# Funções de compatibilidade com o código existente
def get_connection():
    """Função de compatibilidade - retorna uma sessão SQLAlchemy"""
    return db_manager.get_session()

def get_db_path():
    """Função de compatibilidade - não aplicável para PostgreSQL"""
    return "postgresql://supabase"