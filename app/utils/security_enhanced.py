"""
Sistema de Segurança Avançado para Mídia Church
Inclui rate limiting, validações e proteções CSRF
"""

import streamlit as st
import hashlib
import hmac
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import bleach
import secrets
from functools import wraps

class RateLimiter:
    """Sistema de rate limiting para prevenir ataques"""
    
    def __init__(self):
        if 'rate_limit_store' not in st.session_state:
            st.session_state.rate_limit_store = {}
    
    def is_allowed(self, key: str, max_requests: int = 5, window_minutes: int = 1) -> bool:
        """Verifica se a requisição é permitida"""
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Limpar registros antigos
        if key in st.session_state.rate_limit_store:
            st.session_state.rate_limit_store[key] = [
                timestamp for timestamp in st.session_state.rate_limit_store[key]
                if timestamp > window_start
            ]
        else:
            st.session_state.rate_limit_store[key] = []
        
        # Verificar limite
        if len(st.session_state.rate_limit_store[key]) >= max_requests:
            return False
        
        # Registrar nova requisição
        st.session_state.rate_limit_store[key].append(now)
        return True
    
    def get_remaining_time(self, key: str, window_minutes: int = 1) -> int:
        """Retorna tempo restante para próxima tentativa (em segundos)"""
        if key not in st.session_state.rate_limit_store:
            return 0
        
        if not st.session_state.rate_limit_store[key]:
            return 0
        
        oldest_request = min(st.session_state.rate_limit_store[key])
        window_end = oldest_request + timedelta(minutes=window_minutes)
        
        if datetime.now() >= window_end:
            return 0
        
        return int((window_end - datetime.now()).total_seconds())

class InputValidator:
    """Validador avançado de inputs"""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove tags HTML perigosas"""
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
        return bleach.clean(text, tags=allowed_tags, strip=True)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valida formato de telefone brasileiro"""
        # Remove caracteres não numéricos
        phone_clean = re.sub(r'\D', '', phone)
        # Verifica se tem 10 ou 11 dígitos
        return len(phone_clean) in [10, 11] and phone_clean.isdigit()
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Valida força da senha"""
        result = {
            'valid': True,
            'score': 0,
            'issues': []
        }
        
        if len(password) < 8:
            result['issues'].append("Senha deve ter pelo menos 8 caracteres")
            result['valid'] = False
        else:
            result['score'] += 1
        
        if not re.search(r'[A-Z]', password):
            result['issues'].append("Senha deve conter pelo menos uma letra maiúscula")
            result['valid'] = False
        else:
            result['score'] += 1
        
        if not re.search(r'[a-z]', password):
            result['issues'].append("Senha deve conter pelo menos uma letra minúscula")
            result['valid'] = False
        else:
            result['score'] += 1
        
        if not re.search(r'\d', password):
            result['issues'].append("Senha deve conter pelo menos um número")
            result['valid'] = False
        else:
            result['score'] += 1
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result['issues'].append("Senha deve conter pelo menos um caractere especial")
        else:
            result['score'] += 1
        
        return result
    
    @staticmethod
    def validate_sql_injection(text: str) -> bool:
        """Detecta tentativas de SQL injection"""
        dangerous_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(--|#|/\*|\*/)',
            r'(\bOR\b.*=.*\bOR\b)',
            r'(\bAND\b.*=.*\bAND\b)',
            r"('[^']*'|\"[^\"]*\")",
        ]
        
        text_upper = text.upper()
        for pattern in dangerous_patterns:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return False
        return True

class CSRFProtection:
    """Proteção contra ataques CSRF"""
    
    @staticmethod
    def generate_token() -> str:
        """Gera token CSRF"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_or_create_token() -> str:
        """Obtém ou cria token CSRF para a sessão"""
        if 'csrf_token' not in st.session_state:
            st.session_state.csrf_token = CSRFProtection.generate_token()
        return st.session_state.csrf_token
    
    @staticmethod
    def validate_token(provided_token: str) -> bool:
        """Valida token CSRF"""
        session_token = st.session_state.get('csrf_token')
        if not session_token or not provided_token:
            return False
        return hmac.compare_digest(session_token, provided_token)

class SecurityLogger:
    """Logger de eventos de segurança"""
    
    @staticmethod
    def log_security_event(event_type: str, details: Dict[str, Any], user_id: Optional[str] = None):
        """Registra evento de segurança"""
        try:
            from app.database.local_connection import db_manager
            
            db_manager.execute_query("""
                INSERT INTO security_logs (event_type, details, user_id, timestamp, ip_address)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event_type,
                str(details),
                user_id,
                datetime.now().isoformat(),
                st.session_state.get('client_ip', 'unknown')
            ))
        except Exception as e:
            # Log em arquivo se banco falhar
            with open('security.log', 'a') as f:
                f.write(f"{datetime.now()}: {event_type} - {details} - Error: {e}\n")

# Instâncias globais
rate_limiter = RateLimiter()
validator = InputValidator()

def rate_limit(max_requests: int = 5, window_minutes: int = 1, key_func=None):
    """Decorator para rate limiting"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave para rate limiting
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__name__}_{st.session_state.get('user_id', 'anonymous')}"
            
            if not rate_limiter.is_allowed(key, max_requests, window_minutes):
                remaining_time = rate_limiter.get_remaining_time(key, window_minutes)
                st.error(f"🚫 Muitas tentativas. Tente novamente em {remaining_time} segundos.")
                
                # Log evento de segurança
                SecurityLogger.log_security_event(
                    'RATE_LIMIT_EXCEEDED',
                    {'function': func.__name__, 'key': key},
                    st.session_state.get('user_id')
                )
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_input(validation_rules: Dict[str, Any]):
    """Decorator para validação de inputs"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validar argumentos baseado nas regras
            for arg_name, rules in validation_rules.items():
                if arg_name in kwargs:
                    value = kwargs[arg_name]
                    
                    # Validação de SQL injection
                    if rules.get('sql_safe', True) and not validator.validate_sql_injection(str(value)):
                        st.error("🚫 Input contém caracteres não permitidos")
                        SecurityLogger.log_security_event(
                            'SQL_INJECTION_ATTEMPT',
                            {'function': func.__name__, 'input': str(value)[:100]},
                            st.session_state.get('user_id')
                        )
                        return None
                    
                    # Sanitização HTML
                    if rules.get('sanitize_html', False):
                        kwargs[arg_name] = validator.sanitize_html(str(value))
                    
                    # Validação de email
                    if rules.get('email', False) and not validator.validate_email(str(value)):
                        st.error("🚫 Formato de email inválido")
                        return None
                    
                    # Validação de telefone
                    if rules.get('phone', False) and not validator.validate_phone(str(value)):
                        st.error("🚫 Formato de telefone inválido")
                        return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_csrf_token(func):
    """Decorator que exige token CSRF válido"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Verificar se token CSRF foi fornecido
        provided_token = kwargs.pop('csrf_token', None)
        if not CSRFProtection.validate_token(provided_token):
            st.error("🚫 Token de segurança inválido. Recarregue a página.")
            SecurityLogger.log_security_event(
                'CSRF_TOKEN_INVALID',
                {'function': func.__name__},
                st.session_state.get('user_id')
            )
            return None
        
        return func(*args, **kwargs)
    return wrapper

def create_security_tables():
    """Cria tabelas de segurança se não existirem"""
    from app.database.local_connection import db_manager
    
    try:
        db_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                details TEXT,
                user_id TEXT,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db_manager.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_security_logs_timestamp 
            ON security_logs(timestamp)
        """)
        
        db_manager.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_security_logs_event_type 
            ON security_logs(event_type)
        """)
        
    except Exception as e:
        st.error(f"Erro ao criar tabelas de segurança: {e}")

# Função para renderizar campo com CSRF
def render_secure_form(form_key: str):
    """Renderiza formulário com proteção CSRF"""
    csrf_token = CSRFProtection.get_or_create_token()
    
    # Campo oculto com token CSRF
    st.markdown(f"""
        <input type="hidden" id="csrf_token_{form_key}" value="{csrf_token}">
    """, unsafe_allow_html=True)
    
    return csrf_token