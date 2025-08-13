import re
import html
import streamlit as st
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Union
import bleach

class DataValidator:
    """Classe para validação e sanitização de dados"""
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 255) -> str:
        """Sanitiza uma string removendo caracteres perigosos"""
        if not isinstance(text, str):
            return ""
        
        # Remove caracteres de controle e espaços extras
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        text = text.strip()
        
        # Limita o tamanho
        if len(text) > max_length:
            text = text[:max_length]
        
        # Escapa HTML
        text = html.escape(text)
        
        return text
    
    @staticmethod
    def sanitize_html(html_content: str, allowed_tags: List[str] = None) -> str:
        """Sanitiza conteúdo HTML permitindo apenas tags seguras"""
        if not isinstance(html_content, str):
            return ""
        
        if allowed_tags is None:
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        
        # Remove scripts e outros elementos perigosos
        clean_html = bleach.clean(
            html_content,
            tags=allowed_tags,
            attributes={},
            strip=True
        )
        
        return clean_html
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida formato de email"""
        if not isinstance(email, str):
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_username(username: str) -> Dict[str, Any]:
        """Valida nome de usuário"""
        result = {"valid": True, "errors": []}
        
        if not isinstance(username, str):
            result["valid"] = False
            result["errors"].append("Nome de usuário deve ser uma string")
            return result
        
        username = username.strip()
        
        if len(username) < 3:
            result["valid"] = False
            result["errors"].append("Nome de usuário deve ter pelo menos 3 caracteres")
        
        if len(username) > 30:
            result["valid"] = False
            result["errors"].append("Nome de usuário deve ter no máximo 30 caracteres")
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            result["valid"] = False
            result["errors"].append("Nome de usuário deve conter apenas letras, números e underscore")
        
        if username.startswith('_') or username.endswith('_'):
            result["valid"] = False
            result["errors"].append("Nome de usuário não pode começar ou terminar com underscore")
        
        return result
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Valida força da senha"""
        result = {"valid": True, "errors": [], "strength": "weak"}
        
        if not isinstance(password, str):
            result["valid"] = False
            result["errors"].append("Senha deve ser uma string")
            return result
        
        if len(password) < 8:
            result["valid"] = False
            result["errors"].append("Senha deve ter pelo menos 8 caracteres")
        
        if len(password) > 128:
            result["valid"] = False
            result["errors"].append("Senha deve ter no máximo 128 caracteres")
        
        # Verificar complexidade
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        strength_score = sum([has_upper, has_lower, has_digit, has_special])
        
        if strength_score < 2:
            result["strength"] = "weak"
            result["errors"].append("Senha muito fraca. Use letras maiúsculas, minúsculas, números e símbolos")
        elif strength_score < 3:
            result["strength"] = "medium"
        else:
            result["strength"] = "strong"
        
        return result
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valida número de telefone"""
        if not isinstance(phone, str):
            return False
        
        # Remove caracteres não numéricos
        phone_clean = re.sub(r'[^\d]', '', phone)
        
        # Verifica se tem entre 10 e 15 dígitos
        return 10 <= len(phone_clean) <= 15
    
    @staticmethod
    def validate_date(date_value: Union[str, date, datetime]) -> bool:
        """Valida data"""
        if isinstance(date_value, (date, datetime)):
            return True
        
        if isinstance(date_value, str):
            try:
                datetime.strptime(date_value, '%Y-%m-%d')
                return True
            except ValueError:
                return False
        
        return False
    
    @staticmethod
    def validate_event_data(event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados de evento"""
        result = {"valid": True, "errors": []}
        
        # Validar título
        if not event_data.get('title'):
            result["valid"] = False
            result["errors"].append("Título é obrigatório")
        elif len(event_data['title']) > 200:
            result["valid"] = False
            result["errors"].append("Título deve ter no máximo 200 caracteres")
        
        # Validar descrição
        if event_data.get('description') and len(event_data['description']) > 1000:
            result["valid"] = False
            result["errors"].append("Descrição deve ter no máximo 1000 caracteres")
        
        # Validar data - suporta tanto date/time quanto start_datetime/end_datetime
        if event_data.get('date'):
            # Formato antigo: date + time separados
            if not DataValidator.validate_date(event_data.get('date')):
                result["valid"] = False
                result["errors"].append("Data inválida")
            
            # Validar horário
            time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
            if event_data.get('time') and not re.match(time_pattern, event_data['time']):
                result["valid"] = False
                result["errors"].append("Horário inválido (formato: HH:MM)")
        
        elif event_data.get('start_datetime') or event_data.get('end_datetime'):
            # Formato novo: start_datetime e end_datetime
            start_dt = event_data.get('start_datetime')
            end_dt = event_data.get('end_datetime')
            
            if not start_dt:
                result["valid"] = False
                result["errors"].append("Data/hora de início é obrigatória")
            elif not isinstance(start_dt, datetime):
                result["valid"] = False
                result["errors"].append("Data/hora de início deve ser um objeto datetime")
            
            if not end_dt:
                result["valid"] = False
                result["errors"].append("Data/hora de fim é obrigatória")
            elif not isinstance(end_dt, datetime):
                result["valid"] = False
                result["errors"].append("Data/hora de fim deve ser um objeto datetime")
            
            # Verificar se a data de fim é posterior à de início
            if start_dt and end_dt and isinstance(start_dt, datetime) and isinstance(end_dt, datetime):
                if end_dt <= start_dt:
                    result["valid"] = False
                    result["errors"].append("Data/hora de fim deve ser posterior à de início")
        
        else:
            result["valid"] = False
            result["errors"].append("Data é obrigatória")
        
        # Validar capacidade máxima
        if event_data.get('max_attendees'):
            try:
                max_attendees = int(event_data['max_attendees'])
                if max_attendees < 1 or max_attendees > 10000:
                    result["valid"] = False
                    result["errors"].append("Capacidade máxima deve estar entre 1 e 10.000")
            except (ValueError, TypeError):
                result["valid"] = False
                result["errors"].append("Capacidade máxima deve ser um número")
        
        return result

class SecurityHelper:
    """Classe para funções de segurança"""
    
    @staticmethod
    def log_security_event(event_type: str, details: str, user_id: Optional[str] = None):
        """Registra evento de segurança"""
        try:
            from app.database.local_connection import db_manager
            import json
            
            # Criar dados do evento no formato JSON
            event_data = {
                'description': details,
                'timestamp': datetime.now().isoformat()
            }
            
            query = """
            INSERT INTO security_logs (event_type, event_data, user_id, created_at)
            VALUES (?, ?, ?, ?)
            """
            
            db_manager.execute_query(query, (event_type, json.dumps(event_data), user_id, datetime.now().isoformat()))
        
        except Exception as e:
            # Não mostrar erro para não interromper o fluxo
            pass
    
    @staticmethod
    def check_rate_limit(user_id: str, action: str, limit: int = 5, window_minutes: int = 15) -> bool:
        """Verifica limite de taxa para ações"""
        try:
            from app.database.local_connection import db_manager
            
            # Verificar tentativas recentes
            window_start = (datetime.now() - timedelta(minutes=window_minutes)).isoformat()
            
            query = """
            SELECT COUNT(*) as count FROM security_logs 
            WHERE user_id = ? AND event_type = ? AND created_at >= ?
            """
            
            result = db_manager.fetch_all(query, (user_id, action, window_start))
            
            if result and result[0]['count'] >= limit:
                SecurityHelper.log_security_event(
                    "RATE_LIMIT_EXCEEDED",
                    f"User {user_id} exceeded rate limit for {action}",
                    user_id
                )
                return False
            
            return True
        
        except Exception:
            # Em caso de erro, permitir a ação mas registrar
            SecurityHelper.log_security_event(
                "RATE_LIMIT_ERROR",
                f"Error checking rate limit for user {user_id}",
                user_id
            )
            return True
    
    @staticmethod
    def validate_file_upload(uploaded_file) -> Dict[str, Any]:
        """Valida arquivo enviado"""
        result = {"valid": True, "errors": []}
        
        if not uploaded_file:
            result["valid"] = False
            result["errors"].append("Nenhum arquivo selecionado")
            return result
        
        # Verificar tamanho (máximo 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            result["valid"] = False
            result["errors"].append("Arquivo muito grande (máximo 10MB)")
        
        # Verificar extensão
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt']
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        if f'.{file_extension}' not in allowed_extensions:
            result["valid"] = False
            result["errors"].append("Tipo de arquivo não permitido")
        
        return result

# As tabelas de segurança são criadas pelo SecurityMonitor