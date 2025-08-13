"""
Serviço de Email refatorado usando interface unificada
Remove duplicações e melhora arquitetura
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging
from sqlalchemy import text

from app.interfaces.message_service import (
    IMessageService, BaseMessageService, Message, MessageResult, 
    MessageType, MessageStatus, MessagePriority, MessageRecipient,
    MessageValidator, MessageServiceFactory
)
from app.database.local_connection import db_manager
from app.config.settings import load_config

logger = logging.getLogger(__name__)

class EmailService(BaseMessageService):
    """Serviço de Email implementando interface unificada"""
    
    def __init__(self):
        super().__init__("Email")
        self.config = load_config()
        self.smtp_server = None
        self.smtp_port = None
        self.email_user = None
        self.email_password = None
        self.email_from_name = None
        self._load_email_config()
        self._init_database()
    
    def _load_email_config(self):
        """Carrega configurações de email"""
        self.smtp_server = self.config.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(self.config.get('SMTP_PORT', 587))
        self.email_user = self.config.get('EMAIL_USER')
        self.email_password = self.config.get('EMAIL_PASSWORD')
        self.email_from_name = self.config.get('EMAIL_FROM_NAME', 'Igreja')
        
        if not all([self.email_user, self.email_password]):
            logger.warning("⚠️ Configurações de email incompletas")
    
    def _init_database(self):
        """Inicializa tabelas do banco de dados"""
        try:
            with db_manager.get_db_session() as session:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS email_messages (
                        id TEXT PRIMARY KEY,
                        to_email TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        message TEXT NOT NULL,
                        message_type TEXT DEFAULT 'text',
                        status TEXT DEFAULT 'pending',
                        sent_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT
                    )
                """))
                
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS email_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE DEFAULT CURRENT_DATE,
                        emails_sent INTEGER DEFAULT 0,
                        emails_failed INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                session.commit()
                logger.info("✅ Banco de dados Email inicializado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco: {e}")
    
    async def connect(self) -> Tuple[bool, str]:
        """Testa conexão SMTP"""
        try:
            if not all([self.email_user, self.email_password]):
                return False, "Configurações de email não encontradas"
            
            # Testar conexão SMTP
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_user, self.email_password)
            
            self.is_connected_flag = True
            logger.info("✅ Conexão SMTP estabelecida")
            return True, "✅ Conectado ao servidor de email"
            
        except Exception as e:
            logger.error(f"❌ Erro na conexão SMTP: {e}")
            return False, f"Erro na conexão: {str(e)}"
    
    async def disconnect(self) -> bool:
        """Desconecta do serviço (SMTP não mantém conexão persistente)"""
        self.is_connected_flag = False
        return True
    
    async def send_message(self, message: Message) -> MessageResult:
        """Envia email"""
        try:
            # Validar mensagem
            is_valid, error_msg = self._validate_message(message)
            if not is_valid:
                return MessageResult(success=False, error_message=error_msg)
            
            # Validar configurações
            if not all([self.email_user, self.email_password]):
                return MessageResult(
                    success=False,
                    error_message="Configurações de email não encontradas"
                )
            
            # Log da tentativa
            self._log_message_attempt(message, "SMTP")
            
            # Enviar para cada destinatário
            results = []
            for recipient in message.recipients:
                if not MessageValidator.validate_email(recipient.email):
                    results.append(MessageResult(
                        success=False,
                        error_message=f"Email inválido: {recipient.email}"
                    ))
                    continue
                
                success, msg_id, error = await self._send_single_email(message, recipient)
                
                # Salvar no banco
                await self._save_message_to_db(message, recipient, success, msg_id, error)
                
                results.append(MessageResult(
                    success=success,
                    message_id=msg_id,
                    error_message=error if not success else None,
                    status=MessageStatus.SENT if success else MessageStatus.FAILED
                ))
            
            # Resultado consolidado
            success_count = sum(1 for r in results if r.success)
            total_count = len(results)
            
            if success_count == total_count:
                result = MessageResult(
                    success=True,
                    message_id=f"batch_{int(datetime.now().timestamp())}",
                    status=MessageStatus.SENT,
                    metadata={'sent': success_count, 'total': total_count}
                )
            elif success_count > 0:
                result = MessageResult(
                    success=True,
                    message_id=f"partial_{int(datetime.now().timestamp())}",
                    status=MessageStatus.SENT,
                    error_message=f"Enviado para {success_count}/{total_count} destinatários",
                    metadata={'sent': success_count, 'total': total_count}
                )
            else:
                result = MessageResult(
                    success=False,
                    error_message="Falha ao enviar para todos os destinatários",
                    status=MessageStatus.FAILED,
                    metadata={'sent': success_count, 'total': total_count}
                )
            
            # Log do resultado
            self._log_message_result(result, "SMTP")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email: {e}")
            return MessageResult(
                success=False,
                error_message=str(e),
                status=MessageStatus.ERROR
            )
    
    async def _send_single_email(self, message: Message, recipient: MessageRecipient) -> Tuple[bool, Optional[str], Optional[str]]:
        """Envia email para um destinatário"""
        try:
            # Criar mensagem MIME
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email_from_name} <{self.email_user}>"
            msg['To'] = recipient.email
            msg['Subject'] = message.subject or "Mensagem da Igreja"
            
            # Conteúdo da mensagem
            if message.message_type == MessageType.TEXT:
                # Texto simples
                text_part = MIMEText(message.content.text, 'plain', 'utf-8')
                msg.attach(text_part)
                
                # HTML se disponível
                if message.content.metadata and message.content.metadata.get('html'):
                    html_part = MIMEText(message.content.metadata['html'], 'html', 'utf-8')
                    msg.attach(html_part)
            
            # Anexos se houver
            if message.content.file_path and os.path.exists(message.content.file_path):
                with open(message.content.file_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                filename = os.path.basename(message.content.file_path)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                msg.attach(part)
            
            # Enviar email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            # Gerar ID da mensagem
            msg_id = f"email_{int(datetime.now().timestamp())}_{hash(recipient.email)}"
            
            return True, msg_id, None
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email para {recipient.email}: {e}")
            return False, None, str(e)
    
    async def get_message_status(self, message_id: str) -> MessageStatus:
        """Obtém status de um email"""
        try:
            with db_manager.get_db_session() as session:
                result = session.execute(
                    "SELECT status FROM email_messages WHERE id = ?",
                    (message_id,)
                ).fetchone()
                
                if result:
                    return MessageStatus(result[0])
                return MessageStatus.ERROR
                
        except Exception as e:
            logger.error(f"Erro ao obter status: {e}")
            return MessageStatus.ERROR
    
    async def validate_recipient(self, recipient: MessageRecipient) -> bool:
        """Valida destinatário de email"""
        if not recipient.email:
            return False
        
        return MessageValidator.validate_email(recipient.email)
    
    def get_supported_types(self) -> List[MessageType]:
        """Tipos suportados pelo Email"""
        return [
            MessageType.TEXT,
            MessageType.DOCUMENT  # Via anexo
        ]
    
    async def _save_message_to_db(self, message: Message, recipient: MessageRecipient, 
                                success: bool, msg_id: Optional[str], error: Optional[str]):
        """Salva email no banco de dados"""
        try:
            with db_manager.get_db_session() as session:
                import json
                
                session.execute(text("""
                    INSERT INTO email_messages 
                    (id, to_email, subject, message, message_type, status, sent_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """), (
                    msg_id or f"email_{int(datetime.now().timestamp())}",
                    recipient.email,
                    message.subject,
                    message.content.text,
                    message.message_type.value,
                    'sent' if success else 'failed',
                    datetime.now() if success else None,
                    json.dumps({
                        'error': error,
                        'priority': message.priority.value,
                        'recipient_name': recipient.name
                    })
                ))
                session.commit()
                
        except Exception as e:
            logger.error(f"Erro ao salvar email: {e}")
    
    def _validate_message(self, message: Message) -> Tuple[bool, str]:
        """Validação específica para email"""
        # Validação base
        is_valid, error_msg = super()._validate_message(message)
        if not is_valid:
            return is_valid, error_msg
        
        # Validar assunto
        if not message.subject or len(message.subject.strip()) == 0:
            return False, "Assunto é obrigatório para emails"
        
        # Validar destinatários
        for recipient in message.recipients:
            if not recipient.email:
                return False, f"Email não informado para destinatário: {recipient.name or 'Desconhecido'}"
            
            if not MessageValidator.validate_email(recipient.email):
                return False, f"Email inválido: {recipient.email}"
        
        return True, ""

# Registrar serviço na factory
MessageServiceFactory.register_service('email', EmailService)