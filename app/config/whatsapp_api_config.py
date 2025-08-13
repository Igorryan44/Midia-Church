"""
Configurações para API não oficial do WhatsApp
Suporte para múltiplas implementações: whatsapp-web.js, pywhatkit, baileys
"""

import os
from typing import Dict, List, Optional

# Configurações gerais da API
API_CONFIG = {
    'primary_method': 'whatsapp_web_js',  # 'whatsapp_web_js', 'pywhatkit', 'baileys'
    'fallback_method': 'pywhatkit',
    'session_path': './whatsapp_sessions',
    'auto_reconnect': True,
    'max_reconnect_attempts': 5,
    'reconnect_delay': 30,  # segundos
    'message_delay': 2,  # segundos entre mensagens
    'max_messages_per_minute': 20,
    'timeout': 60,
    'headless': False,
    'debug': True
}

# Configurações do whatsapp-web.js (Node.js)
WHATSAPP_WEB_JS_CONFIG = {
    'port': 3001,
    'webhook_url': 'http://localhost:8000/webhook/whatsapp',
    'qr_timeout': 60,
    'auth_timeout': 60,
    'puppeteer_args': [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--single-process',
        '--disable-gpu'
    ],
    'session_file': 'whatsapp_session.json'
}

# Configurações do PyWhatKit (fallback)
PYWHATKIT_CONFIG = {
    'wait_time': 15,  # segundos para aguardar antes de enviar
    'tab_close': True,
    'close_time': 3,  # segundos para fechar aba
    'chrome_path': None,  # None para usar padrão
    'user_data_dir': './chrome_user_data'
}

# Configurações do Baileys (alternativa)
BAILEYS_CONFIG = {
    'auth_folder': './baileys_auth',
    'browser': ['Ubuntu', 'Chrome', '20.0.04'],
    'print_qr_in_terminal': True,
    'default_query_timeout': 60,
    'connect_timeout': 60
}

# Tipos de mensagem suportados
MESSAGE_TYPES = {
    'text': 'text',
    'image': 'image', 
    'video': 'video',
    'audio': 'audio',
    'document': 'document',
    'location': 'location',
    'contact': 'contact',
    'sticker': 'sticker'
}

# Status de mensagem
MESSAGE_STATUS = {
    'pending': 'pending',
    'sent': 'sent',
    'delivered': 'delivered',
    'read': 'read',
    'failed': 'failed',
    'error': 'error'
}

# Configurações de rate limiting
RATE_LIMITS = {
    'messages_per_second': 1,
    'messages_per_minute': 20,
    'messages_per_hour': 1000,
    'bulk_message_delay': 3,  # segundos entre mensagens em massa
    'group_message_delay': 5   # segundos entre mensagens para grupos
}

# Configurações de webhook
WEBHOOK_CONFIG = {
    'enabled': True,
    'url': '/webhook/whatsapp',
    'secret': os.getenv('WHATSAPP_WEBHOOK_SECRET', 'your-secret-key'),
    'events': [
        'message',
        'message_ack',
        'qr',
        'ready',
        'authenticated',
        'auth_failure',
        'disconnected'
    ]
}

# Templates de mensagem para igreja
CHURCH_TEMPLATES = {
    'welcome': {
        'name': 'boas_vindas',
        'content': '🙏 Olá {nome}! Bem-vindo(a) à nossa igreja. Que Deus abençoe sua jornada conosco!',
        'variables': ['nome'],
        'category': 'welcome'
    },
    'event_reminder': {
        'name': 'lembrete_evento',
        'content': '📅 Lembrete: {evento} será em {data} às {horario}. Não perca! 🙏',
        'variables': ['evento', 'data', 'horario'],
        'category': 'reminder'
    },
    'birthday': {
        'name': 'aniversario',
        'content': '🎉 Feliz aniversário, {nome}! 🎂 Que Deus abençoe este novo ano de vida!',
        'variables': ['nome'],
        'category': 'birthday'
    },
    'prayer_request': {
        'name': 'pedido_oracao',
        'content': '🙏 Recebemos seu pedido de oração por {motivo}. Nossa equipe estará orando. Deus te abençoe!',
        'variables': ['motivo'],
        'category': 'prayer'
    },
    'donation_thanks': {
        'name': 'agradecimento_doacao',
        'content': '💝 Obrigado pela sua doação de R$ {valor}! Sua generosidade faz a diferença no Reino de Deus.',
        'variables': ['valor'],
        'category': 'donation'
    }
}

# Configurações de segurança
SECURITY_CONFIG = {
    'max_failed_attempts': 5,
    'lockout_duration': 1800,  # 30 minutos
    'allowed_file_types': [
        'jpg', 'jpeg', 'png', 'gif', 'webp',  # imagens
        'mp4', 'avi', 'mov', 'webm',          # vídeos
        'mp3', 'wav', 'ogg', 'aac',           # áudios
        'pdf', 'doc', 'docx', 'txt',          # documentos
        'xls', 'xlsx', 'ppt', 'pptx'
    ],
    'max_file_size': 16 * 1024 * 1024,  # 16MB
    'encrypt_sessions': True,
    'log_all_messages': True
}

# Configurações de monitoramento
MONITORING_CONFIG = {
    'health_check_interval': 30,  # segundos
    'metrics_retention_days': 30,
    'alert_on_failure': True,
    'alert_email': os.getenv('ALERT_EMAIL'),
    'performance_tracking': True,
    'error_reporting': True
}

# Configurações de backup
BACKUP_CONFIG = {
    'auto_backup': True,
    'backup_interval_hours': 24,
    'backup_retention_days': 30,
    'backup_location': './backups/whatsapp',
    'include_media': False,  # Por questões de espaço
    'compress_backups': True
}

# Mensagens de erro em português
ERROR_MESSAGES = {
    'connection_failed': 'Falha na conexão com WhatsApp. Tente novamente.',
    'invalid_phone': 'Número de telefone inválido. Use o formato: +5511999999999',
    'message_too_long': 'Mensagem muito longa. Máximo de 4096 caracteres.',
    'rate_limit_exceeded': 'Limite de mensagens excedido. Aguarde alguns minutos.',
    'file_too_large': 'Arquivo muito grande. Máximo de 16MB.',
    'file_type_not_allowed': 'Tipo de arquivo não permitido.',
    'session_expired': 'Sessão expirada. Faça login novamente.',
    'phone_not_registered': 'Número não registrado no WhatsApp.',
    'group_not_found': 'Grupo não encontrado.',
    'contact_not_found': 'Contato não encontrado.',
    'api_error': 'Erro na API. Tente novamente mais tarde.',
    'network_error': 'Erro de rede. Verifique sua conexão.',
    'permission_denied': 'Permissão negada para esta ação.',
    'service_unavailable': 'Serviço temporariamente indisponível.'
}

# Mensagens de sucesso
SUCCESS_MESSAGES = {
    'message_sent': 'Mensagem enviada com sucesso!',
    'file_sent': 'Arquivo enviado com sucesso!',
    'contact_added': 'Contato adicionado com sucesso!',
    'group_created': 'Grupo criado com sucesso!',
    'template_saved': 'Template salvo com sucesso!',
    'connection_established': 'Conexão estabelecida com sucesso!',
    'session_restored': 'Sessão restaurada com sucesso!',
    'backup_created': 'Backup criado com sucesso!',
    'settings_saved': 'Configurações salvas com sucesso!'
}

# Configurações de interface
UI_CONFIG = {
    'refresh_interval': 5,  # segundos
    'max_messages_display': 100,
    'enable_emoji_picker': True,
    'enable_file_preview': True,
    'enable_message_search': True,
    'enable_export': True,
    'theme': 'light',  # 'light' ou 'dark'
    'language': 'pt_BR'
}

def get_api_config() -> Dict:
    """Retorna configuração principal da API"""
    return API_CONFIG

def get_config(config_name: str) -> Dict:
    """Retorna configuração específica"""
    configs = {
        'api': API_CONFIG,
        'whatsapp_web_js': WHATSAPP_WEB_JS_CONFIG,
        'pywhatkit': PYWHATKIT_CONFIG,
        'baileys': BAILEYS_CONFIG,
        'security': SECURITY_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'backup': BACKUP_CONFIG,
        'ui': UI_CONFIG,
        'webhook': WEBHOOK_CONFIG,
        'rate_limits': RATE_LIMITS
    }
    return configs.get(config_name, {})

def validate_phone_number(phone: str) -> bool:
    """Valida formato do número de telefone"""
    import re
    # Formato brasileiro: +5511999999999
    pattern = r'^\+55\d{10,11}$'
    return bool(re.match(pattern, phone))

def format_phone_number(phone: str) -> Optional[str]:
    """Formata número de telefone para padrão brasileiro"""
    import re
    
    # Remove caracteres não numéricos
    clean_phone = re.sub(r'\D', '', phone)
    
    # Se tem 11 dígitos (celular) ou 10 dígitos (fixo)
    if len(clean_phone) == 11:
        return f"+55{clean_phone}"
    elif len(clean_phone) == 10:
        return f"+55{clean_phone}"
    elif len(clean_phone) == 13 and clean_phone.startswith('55'):
        return f"+{clean_phone}"
    
    return None