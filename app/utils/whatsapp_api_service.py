"""
Serviço WhatsApp API Não Oficial
Implementação robusta com múltiplas APIs: whatsapp-web.js, pywhatkit, baileys
"""

import asyncio
import json
import logging
import os
import subprocess
import time
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import phonenumbers
from phonenumbers import NumberParseException

# Imports locais
from app.config.whatsapp_api_config import (
    API_CONFIG, WHATSAPP_WEB_JS_CONFIG, PYWHATKIT_CONFIG,
    MESSAGE_TYPES, MESSAGE_STATUS, ERROR_MESSAGES, SUCCESS_MESSAGES,
    RATE_LIMITS, SECURITY_CONFIG, validate_phone_number, format_phone_number
)
from app.database.local_connection import db_manager

logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    QR_REQUIRED = "qr_required"
    ERROR = "error"

class MessagePriority(Enum):
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0

@dataclass
class WhatsAppMessage:
    """Estrutura de mensagem WhatsApp"""
    id: str
    phone: str
    message: str
    message_type: str = MESSAGE_TYPES['text']
    priority: MessagePriority = MessagePriority.NORMAL
    scheduled_at: Optional[datetime] = None
    status: str = MESSAGE_STATUS['pending']
    error_message: Optional[str] = None
    media_path: Optional[str] = None
    caption: Optional[str] = None
    created_at: datetime = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class WhatsAppContact:
    """Estrutura de contato WhatsApp"""
    phone: str
    name: str
    is_registered: bool = False
    profile_pic_url: Optional[str] = None
    status: Optional[str] = None
    last_seen: Optional[datetime] = None
    is_business: bool = False
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

class WhatsAppAPIService:
    """Serviço principal da API não oficial do WhatsApp"""
    
    def __init__(self):
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.current_method = API_CONFIG['primary_method']
        self.fallback_method = API_CONFIG['fallback_method']
        self.session_data = {}
        self.qr_code = None
        self.node_process = None
        self.webhook_server = None
        self.message_queue = []
        self.contacts = {}
        self.groups = {}
        self.stats = {
            'messages_sent': 0,
            'messages_failed': 0,
            'uptime_start': datetime.now(),
            'last_activity': None
        }
        self._init_database()
        self._setup_directories()
    
    def _init_database(self):
        """Inicializa tabelas do banco de dados"""
        try:
            from sqlalchemy import text
            with db_manager.get_db_session() as session:
                # Tabela de configurações da API
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS whatsapp_api_config (
                        id INTEGER PRIMARY KEY,
                        method TEXT DEFAULT 'whatsapp_web_js',
                        session_data TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        last_connection TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Tabela de mensagens da API
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS whatsapp_api_messages (
                        id TEXT PRIMARY KEY,
                        phone TEXT NOT NULL,
                        message TEXT NOT NULL,
                        message_type TEXT DEFAULT 'text',
                        status TEXT DEFAULT 'pending',
                        priority INTEGER DEFAULT 2,
                        scheduled_at TIMESTAMP,
                        sent_at TIMESTAMP,
                        delivered_at TIMESTAMP,
                        read_at TIMESTAMP,
                        error_message TEXT,
                        media_path TEXT,
                        caption TEXT,
                        method_used TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Tabela de contatos da API
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS whatsapp_api_contacts (
                        phone TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        is_registered BOOLEAN DEFAULT 0,
                        profile_pic_url TEXT,
                        status TEXT,
                        last_seen TIMESTAMP,
                        is_business BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Tabela de grupos da API
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS whatsapp_api_groups (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        participants TEXT,
                        admin_phones TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Tabela de estatísticas
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS whatsapp_api_stats (
                        id INTEGER PRIMARY KEY,
                        date DATE UNIQUE,
                        messages_sent INTEGER DEFAULT 0,
                        messages_failed INTEGER DEFAULT 0,
                        connection_time INTEGER DEFAULT 0,
                        method_used TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                session.commit()
                logger.info("✅ Banco de dados da API WhatsApp inicializado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco: {e}")
    
    def _setup_directories(self):
        """Cria diretórios necessários"""
        directories = [
            API_CONFIG['session_path'],
            './whatsapp_media',
            './whatsapp_backups',
            './logs'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    async def connect(self, method: Optional[str] = None) -> Tuple[bool, str]:
        """Conecta usando o método especificado ou padrão"""
        try:
            if method:
                self.current_method = method
            
            logger.info(f"🔄 Conectando usando método: {self.current_method}")
            
            if self.current_method == 'whatsapp_web_js':
                return await self._connect_whatsapp_web_js()
            elif self.current_method == 'pywhatkit':
                return await self._connect_pywhatkit()
            elif self.current_method == 'baileys':
                return await self._connect_baileys()
            else:
                return False, f"Método não suportado: {self.current_method}"
                
        except Exception as e:
            logger.error(f"❌ Erro na conexão: {e}")
            return False, f"Erro na conexão: {str(e)}"
    
    async def _connect_whatsapp_web_js(self) -> Tuple[bool, str]:
        """Conecta usando whatsapp-web.js (Node.js)"""
        try:
            # Verificar se Node.js está instalado
            try:
                subprocess.run(['node', '--version'], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("Node.js não encontrado, usando fallback")
                return await self._connect_fallback()
            
            # Criar script Node.js se não existir
            await self._create_node_script()
            
            # Iniciar processo Node.js
            self.connection_status = ConnectionStatus.CONNECTING
            
            cmd = [
                'node', 
                './whatsapp_node_service.js',
                '--port', str(WHATSAPP_WEB_JS_CONFIG['port'])
            ]
            
            self.node_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )
            
            # Aguardar inicialização
            await asyncio.sleep(3)
            
            # Verificar se o processo está rodando
            if self.node_process.poll() is None:
                # Verificar status via API
                status = await self._check_node_status()
                if status.get('ready'):
                    self.connection_status = ConnectionStatus.CONNECTED
                    return True, "✅ Conectado via whatsapp-web.js"
                elif status.get('qr_required'):
                    self.connection_status = ConnectionStatus.QR_REQUIRED
                    self.qr_code = status.get('qr_code')
                    return False, "📱 QR Code necessário. Escaneie para conectar."
                else:
                    return False, "⏳ Aguardando autenticação..."
            else:
                error = self.node_process.stderr.read() if self.node_process.stderr else "Processo falhou"
                logger.error(f"Processo Node.js falhou: {error}")
                return await self._connect_fallback()
                
        except Exception as e:
            logger.error(f"❌ Erro no whatsapp-web.js: {e}")
            return await self._connect_fallback()
    
    async def _connect_pywhatkit(self) -> Tuple[bool, str]:
        """Conecta usando pywhatkit (fallback)"""
        try:
            import pywhatkit as pwk
            
            # pywhatkit não mantém conexão persistente
            # Apenas verifica se está funcionando
            self.connection_status = ConnectionStatus.CONNECTED
            self.current_method = 'pywhatkit'
            
            logger.info("✅ PyWhatKit configurado como fallback")
            return True, "✅ Conectado via PyWhatKit (requer WhatsApp Web aberto)"
            
        except ImportError:
            logger.error("PyWhatKit não instalado")
            return False, "❌ PyWhatKit não está instalado"
        except Exception as e:
            logger.error(f"❌ Erro no PyWhatKit: {e}")
            return False, f"❌ Erro no PyWhatKit: {str(e)}"
    
    async def _connect_baileys(self) -> Tuple[bool, str]:
        """Conecta usando Baileys (alternativa)"""
        # Implementação futura do Baileys
        logger.warning("Baileys ainda não implementado, usando fallback")
        return await self._connect_fallback()
    
    async def _connect_fallback(self) -> Tuple[bool, str]:
        """Conecta usando método de fallback"""
        if self.fallback_method != self.current_method:
            logger.info(f"🔄 Tentando fallback: {self.fallback_method}")
            return await self.connect(self.fallback_method)
        else:
            return False, "❌ Todos os métodos de conexão falharam"
    
    async def _create_node_script(self):
        """Cria script Node.js para whatsapp-web.js"""
        script_content = '''
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const express = require('express');
const qrcode = require('qrcode');
const fs = require('fs');

const app = express();
app.use(express.json());

let client;
let qrCodeData = null;
let isReady = false;
let isAuthenticated = false;

// Configurar cliente WhatsApp
client = new Client({
    authStrategy: new LocalAuth({
        dataPath: './whatsapp_sessions'
    }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-gpu'
        ]
    }
});

// Event listeners
client.on('qr', async (qr) => {
    console.log('QR Code recebido');
    qrCodeData = await qrcode.toDataURL(qr);
});

client.on('ready', () => {
    console.log('Cliente WhatsApp pronto!');
    isReady = true;
    isAuthenticated = true;
});

client.on('authenticated', () => {
    console.log('Cliente autenticado');
    isAuthenticated = true;
});

client.on('auth_failure', (msg) => {
    console.error('Falha na autenticação:', msg);
    isAuthenticated = false;
});

client.on('disconnected', (reason) => {
    console.log('Cliente desconectado:', reason);
    isReady = false;
    isAuthenticated = false;
});

// API Routes
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
        const { phone, message, type = 'text' } = req.body;
        
        if (!isReady) {
            return res.status(400).json({ error: 'Cliente não está pronto' });
        }
        
        const chatId = phone.includes('@') ? phone : `${phone}@c.us`;
        
        if (type === 'text') {
            await client.sendMessage(chatId, message);
        }
        
        res.json({ success: true, message: 'Mensagem enviada' });
    } catch (error) {
        console.error('Erro ao enviar mensagem:', error);
        res.status(500).json({ error: error.message });
    }
});

app.get('/contacts', async (req, res) => {
    try {
        if (!isReady) {
            return res.status(400).json({ error: 'Cliente não está pronto' });
        }
        
        const contacts = await client.getContacts();
        res.json(contacts.map(contact => ({
            id: contact.id._serialized,
            name: contact.name || contact.pushname,
            phone: contact.number,
            isMyContact: contact.isMyContact
        })));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/disconnect', async (req, res) => {
    try {
        await client.destroy();
        res.json({ success: true });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Iniciar servidor
const PORT = process.argv.includes('--port') ? 
    process.argv[process.argv.indexOf('--port') + 1] : 3001;

app.listen(PORT, () => {
    console.log(`Servidor WhatsApp rodando na porta ${PORT}`);
});

// Inicializar cliente
client.initialize();

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('Desconectando cliente...');
    await client.destroy();
    process.exit(0);
});
'''
        
        # Salvar script
        with open('./whatsapp_node_service.js', 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Criar package.json se não existir
        package_json = {
            "name": "whatsapp-api-service",
            "version": "1.0.0",
            "description": "WhatsApp API Service for Igreja",
            "main": "whatsapp_node_service.js",
            "dependencies": {
                "whatsapp-web.js": "^1.23.0",
                "express": "^4.18.2",
                "qrcode": "^1.5.3"
            }
        }
        
        if not os.path.exists('./package.json'):
            with open('./package.json', 'w') as f:
                json.dump(package_json, f, indent=2)
            
            # Instalar dependências
            try:
                subprocess.run(['npm', 'install'], check=True, capture_output=True)
                logger.info("✅ Dependências Node.js instaladas")
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠️ Erro ao instalar dependências: {e}")
    
    async def _check_node_status(self) -> Dict:
        """Verifica status do serviço Node.js"""
        try:
            url = f"http://localhost:{WHATSAPP_WEB_JS_CONFIG['port']}/status"
            response = requests.get(url, timeout=5)
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao verificar status Node.js: {e}")
            return {}
    
    async def send_message(
        self, 
        phone: str, 
        message: str, 
        message_type: str = 'text',
        media_path: Optional[str] = None,
        caption: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Tuple[bool, str]:
        """Envia mensagem usando o método ativo"""
        try:
            # Validar número
            formatted_phone = format_phone_number(phone)
            if not formatted_phone:
                return False, ERROR_MESSAGES['invalid_phone']
            
            # Criar objeto mensagem
            msg_id = f"msg_{int(time.time() * 1000)}"
            whatsapp_msg = WhatsAppMessage(
                id=msg_id,
                phone=formatted_phone,
                message=message,
                message_type=message_type,
                priority=priority,
                media_path=media_path,
                caption=caption
            )
            
            # Salvar no banco
            await self._save_message(whatsapp_msg)
            
            # Enviar usando método ativo
            if self.current_method == 'whatsapp_web_js':
                success, result = await self._send_via_node(whatsapp_msg)
            elif self.current_method == 'pywhatkit':
                success, result = await self._send_via_pywhatkit(whatsapp_msg)
            else:
                success, result = False, "Método não suportado"
            
            # Atualizar status
            if success:
                whatsapp_msg.status = MESSAGE_STATUS['sent']
                whatsapp_msg.sent_at = datetime.now()
                self.stats['messages_sent'] += 1
            else:
                whatsapp_msg.status = MESSAGE_STATUS['failed']
                whatsapp_msg.error_message = result
                self.stats['messages_failed'] += 1
            
            await self._update_message(whatsapp_msg)
            return success, result
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return False, f"Erro interno: {str(e)}"
    
    async def _send_via_node(self, message: WhatsAppMessage) -> Tuple[bool, str]:
        """Envia mensagem via Node.js service"""
        try:
            url = f"http://localhost:{WHATSAPP_WEB_JS_CONFIG['port']}/send-message"
            
            # Remover + do número para o formato do WhatsApp Web
            phone_clean = message.phone.replace('+', '')
            
            payload = {
                'phone': phone_clean,
                'message': message.message,
                'type': message.message_type
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                return True, SUCCESS_MESSAGES['message_sent']
            else:
                error_data = response.json()
                return False, error_data.get('error', 'Erro desconhecido')
                
        except Exception as e:
            logger.error(f"❌ Erro no envio via Node.js: {e}")
            return False, f"Erro na API Node.js: {str(e)}"
    
    async def _send_via_pywhatkit(self, message: WhatsAppMessage) -> Tuple[bool, str]:
        """Envia mensagem via PyWhatKit"""
        try:
            import pywhatkit as pwk
            
            # PyWhatKit requer horário futuro
            now = datetime.now()
            send_time = now + timedelta(minutes=1)
            
            # Enviar mensagem
            pwk.sendwhatmsg(
                message.phone,
                message.message,
                send_time.hour,
                send_time.minute,
                wait_time=PYWHATKIT_CONFIG['wait_time'],
                tab_close=PYWHATKIT_CONFIG['tab_close'],
                close_time=PYWHATKIT_CONFIG['close_time']
            )
            
            return True, SUCCESS_MESSAGES['message_sent']
            
        except Exception as e:
            logger.error(f"❌ Erro no PyWhatKit: {e}")
            return False, f"Erro no PyWhatKit: {str(e)}"
    
    async def _save_message(self, message: WhatsAppMessage):
        """Salva mensagem no banco de dados"""
        try:
            from sqlalchemy import text
            with db_manager.get_db_session() as session:
                session.execute(text("""
                    INSERT INTO whatsapp_api_messages 
                    (id, phone, message, message_type, status, priority, 
                     media_path, caption, method_used, created_at)
                    VALUES (:id, :phone, :message, :message_type, :status, 
                            :priority, :media_path, :caption, :method_used, :created_at)
                """), {
                    'id': message.id,
                    'phone': message.phone,
                    'message': message.message,
                    'message_type': message.message_type,
                    'status': message.status,
                    'priority': message.priority.value,
                    'media_path': message.media_path,
                    'caption': message.caption,
                    'method_used': self.current_method,
                    'created_at': message.created_at
                })
                session.commit()
        except Exception as e:
            logger.error(f"❌ Erro ao salvar mensagem: {e}")
    
    async def _update_message(self, message: WhatsAppMessage):
        """Atualiza status da mensagem no banco"""
        try:
            from sqlalchemy import text
            with db_manager.get_db_session() as session:
                session.execute(text("""
                    UPDATE whatsapp_api_messages 
                    SET status = :status, sent_at = :sent_at, 
                        error_message = :error_message
                    WHERE id = :id
                """), {
                    'status': message.status,
                    'sent_at': message.sent_at,
                    'error_message': message.error_message,
                    'id': message.id
                })
                session.commit()
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar mensagem: {e}")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Retorna status da conexão"""
        return {
            'status': self.connection_status.value,
            'method': self.current_method,
            'connected': self.connection_status in [ConnectionStatus.CONNECTED, ConnectionStatus.AUTHENTICATED],
            'qr_required': self.connection_status == ConnectionStatus.QR_REQUIRED,
            'qr_code': self.qr_code,
            'uptime': (datetime.now() - self.stats['uptime_start']).total_seconds(),
            'stats': self.stats
        }
    
    def get_qr_code(self) -> Optional[str]:
        """Retorna QR code se disponível"""
        return self.qr_code
    
    async def disconnect(self) -> bool:
        """Desconecta do WhatsApp"""
        try:
            if self.node_process:
                # Tentar desconectar graciosamente via API
                try:
                    url = f"http://localhost:{WHATSAPP_WEB_JS_CONFIG['port']}/disconnect"
                    requests.post(url, timeout=5)
                except:
                    pass
                
                # Terminar processo
                self.node_process.terminate()
                self.node_process.wait(timeout=10)
                self.node_process = None
            
            self.connection_status = ConnectionStatus.DISCONNECTED
            self.qr_code = None
            
            logger.info("✅ Desconectado do WhatsApp")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao desconectar: {e}")
            return False
    
    def __del__(self):
        """Cleanup ao destruir objeto"""
        try:
            if self.node_process:
                self.node_process.terminate()
        except:
            pass

# Instância global do serviço
whatsapp_api_service = WhatsAppAPIService()