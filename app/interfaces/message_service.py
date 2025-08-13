"""
Interface unificada para serviços de mensagem
Resolve duplicação de código e padroniza implementações
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Tipos de mensagem suportados"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"

class MessageStatus(Enum):
    """Status de mensagem"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    ERROR = "error"

class MessagePriority(Enum):
    """Prioridade da mensagem"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class MessageRecipient:
    """Destinatário da mensagem"""
    id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    type: str = "individual"  # individual, group

@dataclass
class MessageContent:
    """Conteúdo da mensagem"""
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    file_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Message:
    """Estrutura unificada de mensagem"""
    id: Optional[str] = None
    sender_id: Optional[str] = None
    recipients: List[MessageRecipient] = None
    subject: Optional[str] = None
    content: MessageContent = None
    message_type: MessageType = MessageType.TEXT
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.PENDING
    created_at: Optional[str] = None
    sent_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.recipients is None:
            self.recipients = []
        if self.content is None:
            self.content = MessageContent()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class MessageResult:
    """Resultado do envio de mensagem"""
    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    status: MessageStatus = MessageStatus.PENDING
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class IMessageService(ABC):
    """Interface para serviços de mensagem"""
    
    @abstractmethod
    async def connect(self) -> Tuple[bool, str]:
        """Conecta ao serviço de mensagem"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Desconecta do serviço"""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Verifica se está conectado"""
        pass
    
    @abstractmethod
    async def send_message(self, message: Message) -> MessageResult:
        """Envia uma mensagem"""
        pass
    
    @abstractmethod
    async def send_bulk_messages(self, messages: List[Message]) -> List[MessageResult]:
        """Envia múltiplas mensagens"""
        pass
    
    @abstractmethod
    async def get_message_status(self, message_id: str) -> MessageStatus:
        """Obtém status de uma mensagem"""
        pass
    
    @abstractmethod
    async def validate_recipient(self, recipient: MessageRecipient) -> bool:
        """Valida um destinatário"""
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """Retorna nome do serviço"""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[MessageType]:
        """Retorna tipos de mensagem suportados"""
        pass

class BaseMessageService(IMessageService):
    """Implementação base com funcionalidades comuns"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.is_connected_flag = False
        self.logger = logging.getLogger(f"{__name__}.{service_name}")
    
    def get_service_name(self) -> str:
        return self.service_name
    
    async def is_connected(self) -> bool:
        return self.is_connected_flag
    
    async def send_bulk_messages(self, messages: List[Message]) -> List[MessageResult]:
        """Implementação padrão de envio em lote"""
        results = []
        
        for message in messages:
            try:
                result = await self.send_message(message)
                results.append(result)
                
                # Delay entre mensagens para evitar rate limiting
                import asyncio
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Erro ao enviar mensagem {message.id}: {e}")
                results.append(MessageResult(
                    success=False,
                    error_message=str(e),
                    status=MessageStatus.FAILED
                ))
        
        return results
    
    def _validate_message(self, message: Message) -> Tuple[bool, str]:
        """Validação básica de mensagem"""
        if not message.recipients:
            return False, "Nenhum destinatário especificado"
        
        if not message.content or not message.content.text:
            return False, "Conteúdo da mensagem é obrigatório"
        
        if len(message.content.text) > 4096:
            return False, "Mensagem muito longa (máximo 4096 caracteres)"
        
        return True, ""
    
    def _log_message_attempt(self, message: Message, service: str):
        """Log de tentativa de envio"""
        self.logger.info(
            f"Tentando enviar mensagem via {service}: "
            f"ID={message.id}, Destinatários={len(message.recipients)}, "
            f"Tipo={message.message_type.value}"
        )
    
    def _log_message_result(self, result: MessageResult, service: str):
        """Log de resultado do envio"""
        if result.success:
            self.logger.info(f"Mensagem enviada com sucesso via {service}: ID={result.message_id}")
        else:
            self.logger.error(f"Falha ao enviar mensagem via {service}: {result.error_message}")

class MessageServiceFactory:
    """Factory para criar serviços de mensagem"""
    
    _services = {}
    
    @classmethod
    def register_service(cls, service_type: str, service_class):
        """Registra um serviço"""
        cls._services[service_type] = service_class
    
    @classmethod
    def create_service(cls, service_type: str, **kwargs) -> IMessageService:
        """Cria uma instância do serviço"""
        if service_type not in cls._services:
            raise ValueError(f"Serviço não registrado: {service_type}")
        
        return cls._services[service_type](**kwargs)
    
    @classmethod
    def get_available_services(cls) -> List[str]:
        """Retorna serviços disponíveis"""
        return list(cls._services.keys())

# Utilitários de validação
class MessageValidator:
    """Validador unificado de mensagens"""
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valida formato de telefone brasileiro"""
        import re
        if not phone:
            return False
        
        # Remove caracteres não numéricos
        clean_phone = re.sub(r'\D', '', phone)
        
        # Formato brasileiro: 11 dígitos (celular) ou 10 dígitos (fixo)
        return len(clean_phone) in [10, 11] or (len(clean_phone) == 13 and clean_phone.startswith('55'))
    
    @staticmethod
    def format_phone(phone: str) -> Optional[str]:
        """Formata telefone para padrão internacional"""
        import re
        if not phone:
            return None
        
        # Remove caracteres não numéricos
        clean_phone = re.sub(r'\D', '', phone)
        
        # Adiciona código do país se necessário
        if len(clean_phone) == 11:  # Celular
            return f"+55{clean_phone}"
        elif len(clean_phone) == 10:  # Fixo
            return f"+55{clean_phone}"
        elif len(clean_phone) == 13 and clean_phone.startswith('55'):
            return f"+{clean_phone}"
        
        return None
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida formato de email"""
        import re
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 4096) -> str:
        """Sanitiza texto da mensagem"""
        if not text:
            return ""
        
        # Remove caracteres perigosos
        import html
        sanitized = html.escape(text.strip())
        
        # Limita tamanho
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length-3] + "..."
        
        return sanitized