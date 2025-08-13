import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional, Dict, Any
import streamlit as st
from app.database.local_connection import db_manager, get_user_by_email
import json
from datetime import datetime

class EmailService:
    """Serviço de envio de emails configurável"""
    
    def __init__(self):
        self.config = self.load_email_config()
    
    def load_email_config(self) -> Dict[str, Any]:
        """Carrega configurações de email do banco de dados"""
        try:
            query = "SELECT setting_key, setting_value FROM system_settings WHERE setting_key LIKE 'email_%'"
            result = db_manager.fetch_all(query)
            
            config = {}
            for row in result:
                key = row['setting_key'].replace('email_', '')
                value = row['setting_value']
                
                # Tentar converter JSON se aplicável
                try:
                    config[key] = json.loads(value)
                except:
                    config[key] = value
            
            # Configurações padrão se não existirem
            default_config = {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True,
                'username': '',
                'password': '',
                'from_name': 'Mídia Church',
                'from_email': '',
                'enabled': False,
                'max_daily_emails': 100,
                'templates': {}
            }
            
            # Mesclar com configurações padrão
            for key, default_value in default_config.items():
                if key not in config:
                    config[key] = default_value
            
            return config
            
        except Exception as e:
            st.error(f"Erro ao carregar configurações de email: {e}")
            return {}
    
    def save_email_config(self, config: Dict[str, Any]) -> bool:
        """Salva configurações de email no banco de dados"""
        try:
            for key, value in config.items():
                setting_key = f"email_{key}"
                
                # Converter para JSON se necessário
                if isinstance(value, (dict, list)):
                    setting_value = json.dumps(value)
                else:
                    setting_value = str(value)
                
                # Inserir ou atualizar configuração
                query = """
                INSERT OR REPLACE INTO system_settings (setting_key, setting_value, updated_at)
                VALUES (?, ?, datetime('now'))
                """
                db_manager.execute_query(query, (setting_key, setting_value))
            
            self.config = config
            return True
            
        except Exception as e:
            st.error(f"Erro ao salvar configurações de email: {e}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Testa a conexão com o servidor de email"""
        try:
            if not self.config.get('enabled', False):
                return {'success': False, 'message': 'Serviço de email não está habilitado'}
            
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            
            if self.config.get('use_tls', True):
                context = ssl.create_default_context()
                server.starttls(context=context)
            
            server.login(self.config['username'], self.config['password'])
            server.quit()
            
            return {'success': True, 'message': 'Conexão estabelecida com sucesso'}
            
        except Exception as e:
            return {'success': False, 'message': f'Erro na conexão: {str(e)}'}
    
    def send_email(self, 
                   to_emails: List[str], 
                   subject: str, 
                   body: str, 
                   html_body: Optional[str] = None,
                   attachments: Optional[List[str]] = None,
                   template_name: Optional[str] = None,
                   template_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Envia um email"""
        
        try:
            if not self.config.get('enabled', False):
                return {'success': False, 'message': 'Serviço de email não está habilitado'}
            
            # Verificar limite diário
            if not self._check_daily_limit():
                return {'success': False, 'message': 'Limite diário de emails excedido'}
            
            # Usar template se especificado
            if template_name and template_name in self.config.get('templates', {}):
                template = self.config['templates'][template_name]
                subject = self._apply_template_vars(template.get('subject', subject), template_vars or {})
                body = self._apply_template_vars(template.get('body', body), template_vars or {})
                if 'html_body' in template:
                    html_body = self._apply_template_vars(template['html_body'], template_vars or {})
            
            # Criar mensagem
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.config['from_name']} <{self.config['from_email']}>"
            message['To'] = ', '.join(to_emails)
            
            # Adicionar corpo do email
            if body:
                text_part = MIMEText(body, 'plain', 'utf-8')
                message.attach(text_part)
            
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                message.attach(html_part)
            
            # Adicionar anexos
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        message.attach(part)
            
            # Enviar email
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            
            if self.config.get('use_tls', True):
                context = ssl.create_default_context()
                server.starttls(context=context)
            
            server.login(self.config['username'], self.config['password'])
            
            failed_emails = []
            for email in to_emails:
                try:
                    server.sendmail(self.config['from_email'], email, message.as_string())
                except Exception as e:
                    failed_emails.append(f"{email}: {str(e)}")
            
            server.quit()
            
            # Registrar envio
            self._log_email_sent(to_emails, subject, len(failed_emails) == 0)
            
            if failed_emails:
                return {
                    'success': False, 
                    'message': f'Falha ao enviar para alguns destinatários: {"; ".join(failed_emails)}'
                }
            else:
                return {'success': True, 'message': f'Email enviado com sucesso para {len(to_emails)} destinatário(s)'}
                
        except Exception as e:
            return {'success': False, 'message': f'Erro ao enviar email: {str(e)}'}
    
    def _apply_template_vars(self, text: str, variables: Dict[str, str]) -> str:
        """Aplica variáveis ao template"""
        for key, value in variables.items():
            text = text.replace(f"{{{key}}}", str(value))
        return text
    
    def _check_daily_limit(self) -> bool:
        """Verifica se o limite diário de emails foi excedido"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            query = """
            SELECT COUNT(*) as count FROM email_logs 
            WHERE DATE(sent_at) = ? AND status = 'sent'
            """
            result = db_manager.fetch_all(query, (today,))
            
            if result:
                daily_count = result[0]['count']
                max_daily = self.config.get('max_daily_emails', 100)
                return daily_count < max_daily
            
            return True
            
        except Exception:
            return True  # Em caso de erro, permitir envio
    
    def _log_email_sent(self, to_emails: List[str], subject: str, success: bool):
        """Registra o envio de email no log"""
        try:
            status = 'sent' if success else 'failed'
            recipients = ', '.join(to_emails)
            
            query = """
            INSERT INTO email_logs (recipients, subject, status, sent_at)
            VALUES (?, ?, ?, datetime('now'))
            """
            db_manager.execute_query(query, (recipients, subject, status))
            
        except Exception:
            pass  # Não bloquear envio por erro de log
    
    def get_email_templates(self) -> Dict[str, Dict[str, str]]:
        """Retorna templates de email disponíveis"""
        return self.config.get('templates', {})
    
    def save_email_template(self, name: str, template: Dict[str, str]) -> bool:
        """Salva um template de email"""
        try:
            templates = self.config.get('templates', {})
            templates[name] = template
            
            config = self.config.copy()
            config['templates'] = templates
            
            return self.save_email_config(config)
            
        except Exception as e:
            st.error(f"Erro ao salvar template: {e}")
            return False
    
    def delete_email_template(self, name: str) -> bool:
        """Remove um template de email"""
        try:
            templates = self.config.get('templates', {})
            if name in templates:
                del templates[name]
                
                config = self.config.copy()
                config['templates'] = templates
                
                return self.save_email_config(config)
            
            return True
            
        except Exception as e:
            st.error(f"Erro ao remover template: {e}")
            return False
    
    def get_email_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de email"""
        try:
            # Emails enviados hoje
            today = datetime.now().strftime('%Y-%m-%d')
            today_query = """
            SELECT COUNT(*) as count FROM email_logs 
            WHERE DATE(sent_at) = ? AND status = 'sent'
            """
            today_result = db_manager.fetch_all(today_query, (today,))
            today_count = today_result[0]['count'] if today_result else 0
            
            # Total de emails enviados
            total_query = "SELECT COUNT(*) as count FROM email_logs WHERE status = 'sent'"
            total_result = db_manager.fetch_all(total_query)
            total_count = total_result[0]['count'] if total_result else 0
            
            # Emails falharam
            failed_query = "SELECT COUNT(*) as count FROM email_logs WHERE status = 'failed'"
            failed_result = db_manager.fetch_all(failed_query)
            failed_count = failed_result[0]['count'] if failed_result else 0
            
            return {
                'today_sent': today_count,
                'total_sent': total_count,
                'total_failed': failed_count,
                'daily_limit': self.config.get('max_daily_emails', 100),
                'remaining_today': max(0, self.config.get('max_daily_emails', 100) - today_count)
            }
            
        except Exception as e:
            return {
                'today_sent': 0,
                'total_sent': 0,
                'total_failed': 0,
                'daily_limit': 100,
                'remaining_today': 100
            }

# Funções de conveniência
def send_notification_email(to_emails: List[str], title: str, message: str) -> Dict[str, Any]:
    """Envia email de notificação usando template padrão"""
    email_service = EmailService()
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                <h2 style="color: #333; text-align: center;">⛪ Mídia Church</h2>
                <h3 style="color: #007bff;">{title}</h3>
                <div style="background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p style="color: #333; line-height: 1.6;">{message}</p>
                </div>
                <p style="color: #666; font-size: 12px; text-align: center;">
                    Esta é uma mensagem automática do sistema Mídia Church.
                </p>
            </div>
        </body>
    </html>
    """
    
    return email_service.send_email(
        to_emails=to_emails,
        subject=f"Mídia Church - {title}",
        body=f"{title}\n\n{message}",
        html_body=html_body
    )

def send_welcome_email(to_email: str, username: str, full_name: str) -> Dict[str, Any]:
    """Envia email de boas-vindas para novos usuários"""
    email_service = EmailService()
    
    template_vars = {
        'username': username,
        'full_name': full_name,
        'system_name': 'Mídia Church'
    }
    
    return email_service.send_email(
        to_emails=[to_email],
        subject="Bem-vindo ao Mídia Church!",
        body="",
        template_name="welcome",
        template_vars=template_vars
    )