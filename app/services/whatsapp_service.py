"""
Serviço WhatsApp refatorado usando interface unificada
Remove duplicações e melhora arquitetura
"""

import asyncio
import json
import time
import os
import subprocess
import requests
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
from app.config.whatsapp_api_config import (
    API_CONFIG, WHATSAPP_WEB_JS_CONFIG, PYWHATKIT_CONFIG,
    ERROR_MESSAGES, SUCCESS_MESSAGES, RATE_LIMITS
)

logger = logging.getLogger(__name__)

class WhatsAppConnectionStatus:
    """Status de conexão do WhatsApp"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    QR_REQUIRED = "qr_required"
    CONNECTED = "connected"
    ERROR = "error"

class WhatsAppService(BaseMessageService):
    """Serviço WhatsApp implementando interface unificada"""
    
    def __init__(self):
        super().__init__("WhatsApp")
        self.connection_status = WhatsAppConnectionStatus.DISCONNECTED
        self.current_method = API_CONFIG.get('primary_method', 'whatsapp_web_js')
        self.fallback_method = API_CONFIG.get('fallback_method', 'pywhatkit')
        self.node_process = None
        self.qr_code = None
        self.last_message_time = 0
        self.message_count = 0
        self.session_data = {}
        
        # Inicializar banco de dados
        self._init_database()
    
    def _init_database(self):
        """Inicializa tabelas do banco de dados"""
        try:
            with db_manager.get_db_session() as session:
                # Tabela de mensagens WhatsApp
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS whatsapp_messages (
                        id TEXT PRIMARY KEY,
                        phone TEXT NOT NULL,
                        message TEXT NOT NULL,
                        message_type TEXT DEFAULT 'text',
                        status TEXT DEFAULT 'pending',
                        method_used TEXT,
                        sent_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT
                    )
                """))
                
                # Tabela de contatos WhatsApp
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS whatsapp_contacts (
                        phone TEXT PRIMARY KEY,
                        name TEXT,
                        is_registered BOOLEAN DEFAULT 0,
                        last_seen TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Tabela de estatísticas
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS whatsapp_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE DEFAULT CURRENT_DATE,
                        messages_sent INTEGER DEFAULT 0,
                        messages_failed INTEGER DEFAULT 0,
                        connections INTEGER DEFAULT 0,
                        method_used TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                session.commit()
                logger.info("✅ Banco de dados WhatsApp inicializado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco: {e}")
    
    async def connect(self) -> Tuple[bool, str]:
        """Conecta ao WhatsApp usando método configurado"""
        try:
            logger.info(f"🔄 Conectando ao WhatsApp via {self.current_method}")
            self.connection_status = WhatsAppConnectionStatus.CONNECTING
            
            if self.current_method == 'whatsapp_web_js':
                success, message = await self._connect_whatsapp_web_js()
            elif self.current_method == 'pywhatkit':
                success, message = await self._connect_pywhatkit()
            else:
                success, message = False, f"Método não suportado: {self.current_method}"
            
            if success:
                self.is_connected_flag = True
                self.connection_status = WhatsAppConnectionStatus.CONNECTED
                await self._log_connection_stats()
            else:
                self.connection_status = WhatsAppConnectionStatus.ERROR
                # Tentar fallback se disponível
                if self.current_method != self.fallback_method:
                    logger.info(f"🔄 Tentando fallback: {self.fallback_method}")
                    return await self._connect_fallback()
            
            return success, message
            
        except Exception as e:
            logger.error(f"❌ Erro na conexão: {e}")
            self.connection_status = WhatsAppConnectionStatus.ERROR
            return False, f"Erro na conexão: {str(e)}"
    
    async def _connect_whatsapp_web_js(self) -> Tuple[bool, str]:
        """Conecta usando whatsapp-web.js"""
        try:
            # Verificar Node.js
            try:
                result = subprocess.run(['node', '--version'], 
                                      capture_output=True, text=True, check=True)
                logger.info(f"Node.js encontrado: {result.stdout.strip()}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("Node.js não encontrado")
                return False, "Node.js não está instalado"
            
            # Criar script Node.js se necessário
            await self._ensure_node_script()
            
            # Iniciar processo Node.js
            cmd = ['node', 'whatsapp_node_service.js']
            self.node_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )
            
            # Aguardar inicialização
            await asyncio.sleep(3)
            
            # Verificar status
            if self.node_process.poll() is None:
                status = await self._check_node_status()
                if status.get('ready'):
                    return True, "✅ Conectado via whatsapp-web.js"
                elif status.get('qr_required'):
                    self.connection_status = WhatsAppConnectionStatus.QR_REQUIRED
                    self.qr_code = status.get('qr_code')
                    return False, "📱 QR Code necessário"
                else:
                    return False, "⏳ Aguardando autenticação"
            else:
                error = self.node_process.stderr.read() if self.node_process.stderr else "Processo falhou"
                logger.error(f"Processo Node.js falhou: {error}")
                return False, f"Falha no processo: {error}"
                
        except Exception as e:
            logger.error(f"❌ Erro no whatsapp-web.js: {e}")
            return False, str(e)
    
    async def _connect_pywhatkit(self) -> Tuple[bool, str]:
        """Conecta usando pywhatkit (fallback)"""
        try:
            import pywhatkit as pwk
            logger.info("✅ PyWhatKit configurado")
            return True, "✅ Conectado via PyWhatKit"
        except ImportError:
            return False, "PyWhatKit não está instalado"
        except Exception as e:
            return False, f"Erro no PyWhatKit: {str(e)}"
    
    async def _connect_fallback(self) -> Tuple[bool, str]:
        """Conecta usando método de fallback"""
        if self.fallback_method != self.current_method:
            old_method = self.current_method
            self.current_method = self.fallback_method
            success, message = await self.connect()
            if not success:
                self.current_method = old_method
            return success, message
        return False, "Todos os métodos falharam"
    
    async def disconnect(self) -> bool:
        """Desconecta do WhatsApp"""
        try:
            if self.node_process:
                self.node_process.terminate()
                self.node_process = None
            
            self.is_connected_flag = False
            self.connection_status = WhatsAppConnectionStatus.DISCONNECTED
            self.qr_code = None
            
            logger.info("✅ Desconectado do WhatsApp")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao desconectar: {e}")
            return False
    
    async def send_message(self, message: Message) -> MessageResult:
        """Envia mensagem via WhatsApp"""
        try:
            # Validar mensagem
            is_valid, error_msg = self._validate_message(message)
            if not is_valid:
                return MessageResult(success=False, error_message=error_msg)
            
            # Verificar conexão
            if not await self.is_connected():
                return MessageResult(
                    success=False, 
                    error_message="WhatsApp não está conectado"
                )
            
            # Rate limiting
            if not await self._check_rate_limit():
                return MessageResult(
                    success=False,
                    error_message="Limite de mensagens excedido"
                )
            
            # Log da tentativa
            self._log_message_attempt(message, self.current_method)
            
            # Enviar mensagem
            if self.current_method == 'whatsapp_web_js':
                success, msg_id, error = await self._send_via_node(message)
            elif self.current_method == 'pywhatkit':
                success, msg_id, error = await self._send_via_pywhatkit(message)
            else:
                success, msg_id, error = False, None, "Método não suportado"
            
            # Salvar no banco
            await self._save_message_to_db(message, success, msg_id, error)
            
            # Criar resultado
            result = MessageResult(
                success=success,
                message_id=msg_id,
                error_message=error if not success else None,
                status=MessageStatus.SENT if success else MessageStatus.FAILED
            )
            
            # Log do resultado
            self._log_message_result(result, self.current_method)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return MessageResult(
                success=False,
                error_message=str(e),
                status=MessageStatus.ERROR
            )
    
    async def _send_via_node(self, message: Message) -> Tuple[bool, Optional[str], Optional[str]]:
        """Envia mensagem via Node.js"""
        try:
            import requests
            
            # Preparar dados
            recipient = message.recipients[0]  # WhatsApp é 1:1
            phone = MessageValidator.format_phone(recipient.phone)
            
            if not phone:
                return False, None, "Número de telefone inválido"
            
            data = {
                'phone': phone,
                'message': message.content.text,
                'type': message.message_type.value
            }
            
            # Enviar via API Node.js
            response = requests.post(
                f"http://localhost:{WHATSAPP_WEB_JS_CONFIG['port']}/send-message",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return True, result.get('message_id'), None
            else:
                error = response.json().get('error', 'Erro desconhecido')
                return False, None, error
                
        except Exception as e:
            return False, None, str(e)
    
    async def _send_via_pywhatkit(self, message: Message) -> Tuple[bool, Optional[str], Optional[str]]:
        """Envia mensagem via PyWhatKit"""
        try:
            import pywhatkit as pwk
            
            recipient = message.recipients[0]
            phone = MessageValidator.format_phone(recipient.phone)
            
            if not phone:
                return False, None, "Número de telefone inválido"
            
            # Remover + do número para pywhatkit
            clean_phone = phone.replace('+', '')
            
            # Enviar mensagem
            pwk.sendwhatmsg_instantly(
                clean_phone,
                message.content.text,
                wait_time=PYWHATKIT_CONFIG.get('wait_time', 15),
                tab_close=PYWHATKIT_CONFIG.get('tab_close', True),
                close_time=PYWHATKIT_CONFIG.get('close_time', 3)
            )
            
            # PyWhatKit não retorna ID, gerar um
            msg_id = f"pwk_{int(time.time())}"
            return True, msg_id, None
            
        except Exception as e:
            return False, None, str(e)
    
    async def get_message_status(self, message_id: str) -> MessageStatus:
        """Obtém status de uma mensagem"""
        try:
            with db_manager.get_db_session() as session:
                result = session.execute(
                    "SELECT status FROM whatsapp_messages WHERE id = ?",
                    (message_id,)
                ).fetchone()
                
                if result:
                    return MessageStatus(result[0])
                return MessageStatus.ERROR
                
        except Exception as e:
            logger.error(f"Erro ao obter status: {e}")
            return MessageStatus.ERROR
    
    async def validate_recipient(self, recipient: MessageRecipient) -> bool:
        """Valida destinatário WhatsApp"""
        if not recipient.phone:
            return False
        
        return MessageValidator.validate_phone(recipient.phone)
    
    def get_supported_types(self) -> List[MessageType]:
        """Tipos suportados pelo WhatsApp"""
        return [
            MessageType.TEXT,
            MessageType.IMAGE,
            MessageType.VIDEO,
            MessageType.AUDIO,
            MessageType.DOCUMENT
        ]
    
    async def _check_rate_limit(self) -> bool:
        """Verifica limite de mensagens"""
        current_time = time.time()
        
        # Reset contador se passou 1 minuto
        if current_time - self.last_message_time > 60:
            self.message_count = 0
        
        # Verificar limite
        max_per_minute = RATE_LIMITS.get('messages_per_minute', 20)
        if self.message_count >= max_per_minute:
            return False
        
        self.message_count += 1
        self.last_message_time = current_time
        return True
    
    async def _save_message_to_db(self, message: Message, success: bool, msg_id: Optional[str], error: Optional[str]):
        """Salva mensagem no banco de dados"""
        try:
            with db_manager.get_db_session() as session:
                recipient = message.recipients[0] if message.recipients else None
                phone = recipient.phone if recipient else None
                
                session.execute(text("""
                    INSERT INTO whatsapp_messages 
                    (id, phone, message, message_type, status, method_used, sent_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """), (
                    msg_id or f"msg_{int(time.time())}",
                    phone,
                    message.content.text,
                    message.message_type.value,
                    'sent' if success else 'failed',
                    self.current_method,
                    datetime.now() if success else None,
                    json.dumps({
                        'error': error,
                        'priority': message.priority.value,
                        'subject': message.subject
                    })
                ))
                session.commit()
                
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem: {e}")
    
    async def _log_connection_stats(self):
        """Log de estatísticas de conexão"""
        try:
            with db_manager.get_db_session() as session:
                session.execute(text("""
                    INSERT INTO whatsapp_stats (date, connections, method_used)
                    VALUES (CURRENT_DATE, 1, ?)
                    ON CONFLICT(date, method_used) DO UPDATE SET
                    connections = connections + 1
                """), (self.current_method,))
                session.commit()
                
        except Exception as e:
            logger.error(f"Erro ao salvar stats: {e}")
    
    async def _ensure_node_script(self):
        """Garante que o script Node.js existe"""
        script_path = "whatsapp_node_service.js"
        if not os.path.exists(script_path):
            await self._create_node_script()
    
    async def _create_node_script(self):
        """Cria script Node.js otimizado"""
        script_content = '''
const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');
const qrcode = require('qrcode');

const app = express();
app.use(express.json());

let client;
let qrCodeData = null;
let isReady = false;
let isAuthenticated = false;

// Configurar cliente
client = new Client({
    authStrategy: new LocalAuth({
        dataPath: './whatsapp_sessions'
    }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage'
        ]
    }
});

// Events
client.on('qr', async (qr) => {
    qrCodeData = await qrcode.toDataURL(qr);
});

client.on('ready', () => {
    isReady = true;
    isAuthenticated = true;
});

client.on('authenticated', () => {
    isAuthenticated = true;
});

client.on('auth_failure', () => {
    isAuthenticated = false;
});

client.on('disconnected', () => {
    isReady = false;
    isAuthenticated = false;
});

// Routes
app.get('/status', (req, res) => {
    res.json({
        ready: isReady,
        authenticated: isAuthenticated,
        qr_required: !isAuthenticated && qrCodeData !== null,
        qr_code: qrCodeData
    });
});

app.post('/send-message', async (req, res) => {
    try {
        const { phone, message } = req.body;
        
        if (!isReady) {
            return res.status(400).json({ error: 'Cliente não está pronto' });
        }
        
        const chatId = phone.includes('@') ? phone : `${phone}@c.us`;
        const result = await client.sendMessage(chatId, message);
        
        res.json({ 
            success: true, 
            message_id: result.id.id 
        });
        
    } catch (error) {
        res.status(500).json({ 
            error: error.message 
        });
    }
});

// Inicializar
client.initialize();

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
    console.log(`WhatsApp service running on port ${PORT}`);
});
'''
        
        with open("whatsapp_node_service.js", "w", encoding="utf-8") as f:
            f.write(script_content)
        
        logger.info("✅ Script Node.js criado")
    
    async def _check_node_status(self) -> Dict:
        """Verifica status do serviço Node.js"""
        try:
            import requests
            response = requests.get(
                f"http://localhost:{WHATSAPP_WEB_JS_CONFIG['port']}/status",
                timeout=5
            )
            return response.json()
        except:
            return {}
    
    def get_qr_code(self) -> Optional[str]:
        """Retorna QR code se disponível"""
        return self.qr_code
    
    def get_connection_status(self) -> str:
        """Retorna status da conexão"""
        return self.connection_status

# Registrar serviço na factory
MessageServiceFactory.register_service('whatsapp', WhatsAppService)