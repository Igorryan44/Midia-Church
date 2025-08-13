import os
from dotenv import load_dotenv
from pathlib import Path

def load_config():
    """Carrega as configurações da aplicação"""
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Diretório raiz do projeto
    ROOT_DIR = Path(__file__).parent.parent.parent
    
    config = {
        # Configurações gerais
        'ROOT_DIR': ROOT_DIR,
        'DEBUG': os.getenv('DEBUG', 'False').lower() == 'true',
        'SECRET_KEY': os.getenv('SECRET_KEY', 'default-secret-key-change-in-production'),
        
        # Banco de dados
        'DATABASE_URL': os.getenv('DATABASE_URL', f'sqlite:///{ROOT_DIR}/data/church_media.db'),
        
        # API do Groq
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY', ''),
        
        # Configurações de email
        'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'SMTP_PORT': int(os.getenv('SMTP_PORT', '587')),
        'EMAIL_USER': os.getenv('EMAIL_USER', ''),
        'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD', ''),
        
        # Configurações de upload
        'MAX_UPLOAD_SIZE': os.getenv('MAX_UPLOAD_SIZE', '50MB'),
        'ALLOWED_EXTENSIONS': os.getenv('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,gif,mp4,avi,mov,pdf,doc,docx').split(','),
        'UPLOAD_DIR': str(ROOT_DIR / 'data' / 'uploads'),
        
        # Diretórios
        'DATA_DIR': str(ROOT_DIR / 'data'),
        'STATIC_DIR': str(ROOT_DIR / 'static'),
    }
    
    # Criar diretórios se não existirem
    Path(config['DATA_DIR']).mkdir(exist_ok=True)
    Path(config['UPLOAD_DIR']).mkdir(exist_ok=True)
    
    return config

# Configurações globais
CONFIG = load_config()