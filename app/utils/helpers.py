"""
Funções auxiliares para o sistema
"""
from app.database.local_connection import db_manager

def get_user_id_by_username(username):
    """Busca o ID do usuário pelo username"""
    try:
        query = "SELECT id FROM users WHERE username = ?"
        result = db_manager.fetch_all(query, (username,))
        return result[0]["id"] if result else None
    except Exception:
        return None

def get_username_by_id(user_id):
    """Busca o username pelo ID do usuário"""
    try:
        query = "SELECT username FROM users WHERE id = ?"
        result = db_manager.fetch_all(query, (user_id,))
        return result[0]["username"] if result else None
    except Exception:
        return None

def format_file_size(size_bytes):
    """Formata o tamanho do arquivo em formato legível"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def sanitize_filename(filename):
    """Sanitiza nome de arquivo removendo caracteres perigosos"""
    import re
    # Remove caracteres perigosos
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove espaços duplos
    filename = re.sub(r'\s+', ' ', filename)
    # Remove espaços no início e fim
    filename = filename.strip()
    return filename

def validate_email_format(email):
    """Valida formato de email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_secure_token(length=32):
    """Gera token seguro"""
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_password(password):
    """Gera hash da senha"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    """Verifica senha contra hash"""
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed)