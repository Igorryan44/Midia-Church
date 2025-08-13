"""
Gerenciador unificado de mensagens
Coordena todos os serviços de mensagem e remove duplicações
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging
from sqlalchemy import text

from app.interfaces.message_service import (
    IMessageService, Message, MessageResult, MessageType, 
    MessageStatus, MessagePriority, MessageRecipient,
    MessageServiceFactory, MessageValidator
)
from app.services.whatsapp_service import WhatsAppService
from app.services.email_service import EmailService
from app.database.local_connection import db_manager

logger = logging.getLogger(__name__)

class MessageManager:
    """Gerenciador central de mensagens"""
    
    def __init__(self):
        self.services: Dict[str, IMessageService] = {}
        self.default_service = 'whatsapp'
        self._init_services()
    
    def _init_services(self):
        """Inicializa todos os serviços disponíveis"""
        try:
            # Registrar serviços
            self.services['whatsapp'] = MessageServiceFactory.create_service('whatsapp')
            self.services['email'] = MessageServiceFactory.create_service('email')
            
            logger.info(f"✅ Serviços inicializados: {list(self.services.keys())}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar serviços: {e}")
    
    async def connect_all_services(self) -> Dict[str, Tuple[bool, str]]:
        """Conecta todos os serviços"""
        results = {}
        
        for service_name, service in self.services.items():
            try:
                success, message = await service.connect()
                results[service_name] = (success, message)
                logger.info(f"Serviço {service_name}: {message}")
            except Exception as e:
                results[service_name] = (False, str(e))
                logger.error(f"Erro ao conectar {service_name}: {e}")
        
        return results
    
    async def disconnect_all_services(self) -> Dict[str, bool]:
        """Desconecta todos os serviços"""
        results = {}
        
        for service_name, service in self.services.items():
            try:
                success = await service.disconnect()
                results[service_name] = success
            except Exception as e:
                results[service_name] = False
                logger.error(f"Erro ao desconectar {service_name}: {e}")
        
        return results
    
    async def send_message(self, message: Message, service_type: Optional[str] = None) -> MessageResult:
        """Envia mensagem usando serviço especificado ou padrão"""
        try:
            # Determinar serviço
            if service_type and service_type in self.services:
                service = self.services[service_type]
            else:
                service = self._determine_best_service(message)
            
            if not service:
                return MessageResult(
                    success=False,
                    error_message="Nenhum serviço disponível"
                )
            
            # Verificar se serviço está conectado
            if not await service.is_connected():
                success, msg = await service.connect()
                if not success:
                    return MessageResult(
                        success=False,
                        error_message=f"Falha na conexão: {msg}"
                    )
            
            # Enviar mensagem
            result = await service.send_message(message)
            
            # Log do resultado
            logger.info(
                f"Mensagem enviada via {service.get_service_name()}: "
                f"Sucesso={result.success}, ID={result.message_id}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return MessageResult(
                success=False,
                error_message=str(e),
                status=MessageStatus.ERROR
            )
    
    async def send_bulk_messages(self, messages: List[Message], 
                               service_type: Optional[str] = None) -> List[MessageResult]:
        """Envia múltiplas mensagens"""
        results = []
        
        # Agrupar mensagens por serviço se não especificado
        if service_type:
            service = self.services.get(service_type)
            if service:
                return await service.send_bulk_messages(messages)
            else:
                return [MessageResult(
                    success=False,
                    error_message=f"Serviço não encontrado: {service_type}"
                ) for _ in messages]
        
        # Agrupar por tipo de destinatário
        grouped_messages = self._group_messages_by_service(messages)
        
        # Enviar por grupo
        for svc_type, msg_list in grouped_messages.items():
            service = self.services.get(svc_type)
            if service:
                batch_results = await service.send_bulk_messages(msg_list)
                results.extend(batch_results)
            else:
                # Serviço não disponível
                failed_results = [MessageResult(
                    success=False,
                    error_message=f"Serviço não disponível: {svc_type}"
                ) for _ in msg_list]
                results.extend(failed_results)
        
        return results
    
    async def send_notification(self, title: str, content: str, 
                              recipients: List[MessageRecipient],
                              priority: MessagePriority = MessagePriority.NORMAL,
                              preferred_service: Optional[str] = None) -> List[MessageResult]:
        """Envia notificação para múltiplos destinatários"""
        
        # Agrupar destinatários por tipo de contato
        whatsapp_recipients = []
        email_recipients = []
        
        for recipient in recipients:
            if recipient.phone and MessageValidator.validate_phone(recipient.phone):
                whatsapp_recipients.append(recipient)
            elif recipient.email and MessageValidator.validate_email(recipient.email):
                email_recipients.append(recipient)
        
        results = []
        
        # Enviar via WhatsApp
        if whatsapp_recipients and (not preferred_service or preferred_service == 'whatsapp'):
            whatsapp_message = Message(
                subject=title,
                content=MessageContent(text=content),
                recipients=whatsapp_recipients,
                message_type=MessageType.TEXT,
                priority=priority
            )
            
            result = await self.send_message(whatsapp_message, 'whatsapp')
            results.append(result)
        
        # Enviar via Email
        if email_recipients and (not preferred_service or preferred_service == 'email'):
            from app.interfaces.message_service import MessageContent
            
            email_message = Message(
                subject=title,
                content=MessageContent(text=content),
                recipients=email_recipients,
                message_type=MessageType.TEXT,
                priority=priority
            )
            
            result = await self.send_message(email_message, 'email')
            results.append(result)
        
        return results
    
    def _determine_best_service(self, message: Message) -> Optional[IMessageService]:
        """Determina o melhor serviço baseado nos destinatários"""
        if not message.recipients:
            return None
        
        # Verificar se todos têm WhatsApp
        all_have_whatsapp = all(
            recipient.phone and MessageValidator.validate_phone(recipient.phone)
            for recipient in message.recipients
        )
        
        if all_have_whatsapp and 'whatsapp' in self.services:
            return self.services['whatsapp']
        
        # Verificar se todos têm email
        all_have_email = all(
            recipient.email and MessageValidator.validate_email(recipient.email)
            for recipient in message.recipients
        )
        
        if all_have_email and 'email' in self.services:
            return self.services['email']
        
        # Retornar serviço padrão
        return self.services.get(self.default_service)
    
    def _group_messages_by_service(self, messages: List[Message]) -> Dict[str, List[Message]]:
        """Agrupa mensagens por serviço apropriado"""
        grouped = {'whatsapp': [], 'email': []}
        
        for message in messages:
            service = self._determine_best_service(message)
            if service:
                service_name = service.get_service_name().lower()
                if service_name in grouped:
                    grouped[service_name].append(message)
        
        # Remover grupos vazios
        return {k: v for k, v in grouped.items() if v}
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtém status de todos os serviços"""
        status = {}
        
        for service_name, service in self.services.items():
            try:
                # Verificar se o serviço tem is_connected_flag como atributo
                if hasattr(service, 'is_connected_flag'):
                    is_connected = service.is_connected_flag
                else:
                    is_connected = False
                    
                supported_types = service.get_supported_types()
                
                status[service_name] = {
                    'connected': is_connected,
                    'supported_types': [t.value for t in supported_types],
                    'service_name': service.get_service_name()
                }
                
                # Informações específicas do WhatsApp
                if service_name == 'whatsapp' and hasattr(service, 'get_connection_status'):
                    status[service_name]['connection_status'] = service.get_connection_status()
                    status[service_name]['qr_code'] = service.get_qr_code()
                
            except Exception as e:
                status[service_name] = {
                    'connected': False,
                    'error': str(e)
                }
        
        return status
    
    async def get_message_history(self, service_type: Optional[str] = None, 
                                limit: int = 100) -> List[Dict[str, Any]]:
        """Obtém histórico de mensagens"""
        try:
            with db_manager.get_db_session() as session:
                if service_type == 'whatsapp':
                    query = text("""
                        SELECT id, contact_id as recipient, content as message, status, 
                               sent_at,
                               sent_at as created_at
                        FROM whatsapp_messages
                        ORDER BY sent_at DESC
                        LIMIT :limit
                    """)
                elif service_type == 'email':
                    query = text("""
                        SELECT id, to_email as recipient, subject, message, status, 
                               COALESCE(sent_at, created_at) as sent_at,
                               created_at
                        FROM email_messages
                        ORDER BY COALESCE(created_at, sent_at) DESC
                        LIMIT :limit
                    """)
                else:
                    # Consulta simplificada - buscar apenas WhatsApp por enquanto
                    query = text("""
                        SELECT id, contact_id as recipient, content as message, status, 
                               sent_at,
                               sent_at as created_at,
                               'whatsapp' as service
                        FROM whatsapp_messages
                        ORDER BY sent_at DESC
                        LIMIT :limit
                    """)
                
                results = session.execute(query, {"limit": limit}).fetchall()
                
                return [dict(row._mapping) for row in results]
                
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Obtém estatísticas de mensagens"""
        try:
            with db_manager.get_db_session() as session:
                # WhatsApp stats
                whatsapp_query = """
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                    FROM whatsapp_messages
                    WHERE DATE(sent_at) = DATE('now')
                """
                
                try:
                    whatsapp_stats = session.execute(text(whatsapp_query)).fetchone()
                except Exception as e:
                    logger.warning(f"Erro nas estatísticas WhatsApp: {e}")
                    whatsapp_stats = None
                
                # Email stats
                email_query = """
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                    FROM email_messages
                    WHERE DATE(COALESCE(created_at, sent_at)) = DATE('now')
                """
                
                try:
                    email_stats = session.execute(text(email_query)).fetchone()
                except Exception as e:
                    logger.warning(f"Erro nas estatísticas Email: {e}")
                    email_stats = None
                
                # Obter status dos serviços de forma síncrona
                services_status = self.get_service_status()
                
                return {
                    'today': {
                        'whatsapp': dict(whatsapp_stats._mapping) if whatsapp_stats else {'total': 0, 'sent': 0, 'failed': 0},
                        'email': dict(email_stats._mapping) if email_stats else {'total': 0, 'sent': 0, 'failed': 0}
                    },
                    'services': services_status
                }
                
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {'today': {'whatsapp': {'total': 0, 'sent': 0, 'failed': 0}, 'email': {'total': 0, 'sent': 0, 'failed': 0}}, 'services': {}}

    def _get_message_count_sync(self, service_type: str) -> int:
        """Obter contagem de mensagens para um serviço (versão síncrona)"""
        try:
            from app.database.db_manager import DatabaseManager
            from sqlalchemy import text
            db_manager = DatabaseManager()
            
            with db_manager.get_db_session() as session:
                result = session.execute(
                    text("SELECT COUNT(*) FROM whatsapp_messages WHERE service_type = :service_type"),
                    {"service_type": service_type}
                ).fetchone()
                return result[0] if result else 0
        except Exception:
            return 0
    
    async def _get_message_count(self, service_type: str) -> int:
        """Obter contagem de mensagens para um serviço"""
        return self._get_message_count_sync(service_type)

# Instância global do gerenciador
message_manager = MessageManager()