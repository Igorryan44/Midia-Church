import streamlit as st
import bcrypt
import re
import hashlib
import time
import os
import json
import platform
from sqlalchemy import text
from app.database.local_connection import db_manager, get_user_by_username, get_user_by_email, create_user
from app.utils.styles import get_login_css
from app.utils.validation import DataValidator, SecurityHelper
from app.utils.security_monitor import SecurityMonitor
from datetime import datetime, timedelta

def get_device_fingerprint():
    """Gera um fingerprint único do dispositivo baseado em características do navegador e sistema"""
    try:
        # Obter informações do navegador via JavaScript
        user_agent = st.context.headers.get("user-agent", "unknown")
        
        # Obter informações adicionais se disponíveis
        accept_language = st.context.headers.get("accept-language", "unknown")
        accept_encoding = st.context.headers.get("accept-encoding", "unknown")
        
        # Informações do sistema (lado servidor)
        system_info = {
            "platform": platform.system(),
            "python_version": platform.python_version(),
        }
        
        # Criar fingerprint combinando informações
        fingerprint_data = {
            "user_agent": user_agent,
            "accept_language": accept_language,
            "accept_encoding": accept_encoding,
            "system_info": system_info,
            "timestamp": int(time.time() // 86400)  # Dia atual para permitir mudanças diárias
        }
        
        # Gerar hash único
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        device_fingerprint = hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]
        
        return device_fingerprint, user_agent
        
    except Exception as e:
        # Fallback para um fingerprint baseado apenas no user-agent
        user_agent = "unknown"
        try:
            user_agent = st.context.headers.get("user-agent", "unknown")
        except:
            pass
        
        fallback_data = f"fallback_{user_agent}_{int(time.time() // 86400)}"
        device_fingerprint = hashlib.sha256(fallback_data.encode()).hexdigest()[:32]
        
        return device_fingerprint, user_agent

def get_client_ip():
    """Obtém o IP do cliente"""
    try:
        # Tentar obter IP real através de headers
        forwarded_for = st.context.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = st.context.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback
        return st.context.headers.get("host", "unknown")
        
    except Exception:
        return "unknown"

def is_trusted_device(user_id, device_fingerprint):
    """Verifica se o dispositivo é confiável para o usuário"""
    try:
        with db_manager.get_db_session() as session:
            result = session.execute(
                text("""
                SELECT COUNT(*) as count FROM user_sessions 
                WHERE user_id = :user_id 
                AND device_fingerprint = :device_fingerprint 
                AND is_trusted = 1
                AND created_at > datetime('now', '-90 days')
                """),
                {
                    "user_id": user_id,
                    "device_fingerprint": device_fingerprint
                }
            ).fetchone()
            
            return result.count > 0 if result else False
            
    except Exception as e:
        # Em caso de erro, considerar dispositivo não confiável
        return False

def check_device_matches_session(user_id, device_fingerprint):
    """Verifica se o dispositivo atual corresponde à sessão ativa do usuário"""
    try:
        session_token = st.session_state.get('session_token')
        if not session_token:
            return False
            
        with db_manager.get_db_session() as session:
            result = session.execute(
                text("""
                SELECT COUNT(*) as count FROM user_sessions 
                WHERE user_id = :user_id 
                AND session_token = :session_token
                AND device_fingerprint = :device_fingerprint 
                AND is_active = 1
                AND expires_at > datetime('now')
                """),
                {
                    "user_id": user_id,
                    "session_token": session_token,
                    "device_fingerprint": device_fingerprint
                }
            ).fetchone()
            
            return result.count > 0 if result else False
            
    except Exception as e:
        # Em caso de erro, considerar dispositivo não correspondente
        return False

def check_authentication():
    """Verifica se o usuário está autenticado e se o dispositivo é confiável"""
    
    try:
        # Inicializar variáveis de sessão se não existirem
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        
        if 'username' not in st.session_state:
            st.session_state.username = None
        
        if 'device_verified' not in st.session_state:
            st.session_state.device_verified = False
        
        # Obter fingerprint do dispositivo atual
        device_fingerprint, user_agent = get_device_fingerprint()
        st.session_state.device_fingerprint = device_fingerprint
        st.session_state.user_agent = user_agent
        
        # REGRA PRINCIPAL: Se o usuário já está autenticado na sessão atual, permitir acesso
        # Isso evita re-autenticação desnecessária ao atualizar a página
        if ('authenticated' in st.session_state and st.session_state.authenticated) and \
           ('user_info' in st.session_state and st.session_state.user_info):
            
            # Se já está autenticado, verificar dispositivo apenas uma vez por sessão
            if not st.session_state.device_verified:
                user_id = st.session_state.user_info.get('id')
                if user_id:
                    # Verificar se é um dispositivo confiável ou se corresponde à sessão atual
                    if (is_trusted_device(user_id, device_fingerprint) or 
                        check_device_matches_session(user_id, device_fingerprint)):
                        st.session_state.device_verified = True
                    else:
                        # Marcar como verificado mesmo para dispositivos não confiáveis
                        # se o usuário já estava logado (evita logout em refresh)
                        st.session_state.device_verified = True
            
            return True
        
        # Se não está na sessão atual, verificar persistência de sessão
        if check_persistent_session():
            # Verificar dispositivo após restaurar sessão
            user_id = st.session_state.user_info.get('id') if 'user_info' in st.session_state else None
            if user_id:
                # Para sessões restauradas, verificar se o dispositivo é o mesmo da sessão
                if check_device_matches_session(user_id, device_fingerprint):
                    st.session_state.device_verified = True
                    return True
                elif is_trusted_device(user_id, device_fingerprint):
                    st.session_state.device_verified = True
                    return True
                else:
                    # Dispositivo não confiável - invalidar sessão restaurada APENAS
                    # se for realmente um novo dispositivo (não um refresh)
                    st.session_state.authenticated = False
                    st.session_state.device_verified = False
                    if 'session_token' in st.session_state:
                        del st.session_state.session_token
                    st.warning("🔒 Insira suas credenciais.")
        
        # Se nenhuma verificação passou, exibir formulário de login/registro
        show_auth_form()
        
        return False
    except Exception as e:
        st.error(f"⚠️ Erro no sistema de autenticação: {e}")
        return False

def check_persistent_session():
    """Verifica se existe uma sessão persistente válida"""
    try:
        # Verificar se existe token de sessão no session_state
        session_token = st.session_state.get('session_token')
        
        # Se não há token no session_state, tentar encontrar uma sessão ativa mais recente
        if not session_token:
            # Buscar a sessão mais recente que ainda está ativa
            with db_manager.get_db_session() as session:
                result = session.execute(
                    text("""
                    SELECT us.session_token, u.username, u.full_name, u.role, us.expires_at, u.id
                    FROM users u 
                    JOIN user_sessions us ON u.id = us.user_id 
                    WHERE us.expires_at > datetime('now') AND us.is_active = 1
                    ORDER BY us.last_accessed DESC
                    LIMIT 1
                    """)
                ).fetchone()
                
                if result:
                    session_token = result.session_token
                    # Restaurar sessão completa
                    st.session_state.authenticated = True
                    st.session_state.username = result.username
                    st.session_state.user_info = {
                        'id': result.id,
                        'username': result.username,
                        'full_name': result.full_name,
                        'role': result.role
                    }
                    st.session_state.session_token = session_token
                    
                    # Atualizar último acesso
                    session.execute(
                        text("UPDATE user_sessions SET last_accessed = datetime('now') WHERE session_token = :token"),
                        {"token": session_token}
                    )
                    session.commit()
                    
                    return True
        
        elif session_token:
            # Verificar se o token é válido no banco de dados
            with db_manager.get_db_session() as session:
                result = session.execute(
                    text("""
                    SELECT u.username, u.full_name, u.role, us.expires_at, u.id
                    FROM users u 
                    JOIN user_sessions us ON u.id = us.user_id 
                    WHERE us.session_token = :token AND us.expires_at > datetime('now') AND us.is_active = 1
                    """),
                    {"token": session_token}
                ).fetchone()
                
                if result:
                    # Restaurar sessão
                    st.session_state.authenticated = True
                    st.session_state.username = result.username
                    st.session_state.user_info = {
                        'id': result.id,
                        'username': result.username,
                        'full_name': result.full_name,
                        'role': result.role
                    }
                    st.session_state.session_token = session_token
                    
                    # Atualizar último acesso
                    session.execute(
                        text("UPDATE user_sessions SET last_accessed = datetime('now') WHERE session_token = :token"),
                        {"token": session_token}
                    )
                    session.commit()
                    
                    return True
                else:
                    # Token inválido, remover do session_state
                    if 'session_token' in st.session_state:
                        del st.session_state['session_token']
        
        return False
    except Exception as e:
        # Em caso de erro, não bloquear o login mas registrar
        if 'debug_mode' in st.session_state and st.session_state.debug_mode:
            st.warning(f"⚠️ Erro na verificação de sessão: {e}")
        return False

def create_session_token(username, remember_me=True, trust_device=True):
    """Cria um token de sessão persistente com informações do dispositivo"""
    try:
        # Gerar token único
        timestamp = str(time.time())
        random_data = os.urandom(32).hex()
        token_data = f"{username}:{timestamp}:{random_data}"
        session_token = hashlib.sha256(token_data.encode()).hexdigest()
        
        # Definir expiração (30 dias)
        expires_at = datetime.now() + timedelta(days=30)
        
        # Buscar ID do usuário
        user = get_user_by_username(username)
        
        if user:
            user_id = user['id']
            
            # Obter informações do dispositivo e sessão
            device_fingerprint, user_agent = get_device_fingerprint()
            ip_address = get_client_ip()
            
            with db_manager.get_db_session() as session:
                # Invalidar sessões antigas do usuário
                session.execute(
                    text("UPDATE user_sessions SET is_active = 0 WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                
                # Criar nova sessão
                session.execute(
                    text("""
                    INSERT INTO user_sessions (user_id, session_token, expires_at, created_at, last_accessed, is_active, 
                                             user_agent, ip_address, device_fingerprint, is_trusted)
                    VALUES (:user_id, :token, :expires_at, datetime('now'), datetime('now'), 1, 
                            :user_agent, :ip_address, :device_fingerprint, :is_trusted)
                    """),
                    {
                        "user_id": user_id,
                        "token": session_token,
                        "expires_at": expires_at.isoformat(),
                        "user_agent": user_agent,
                        "ip_address": ip_address,
                        "device_fingerprint": device_fingerprint,
                        "is_trusted": 1 if trust_device else 0
                    }
                )
                session.commit()
            
            # Armazenar informações na sessão
            st.session_state.device_fingerprint = device_fingerprint
            st.session_state.device_verified = True
            
            return session_token
        
        return None
    except Exception as e:
        st.error(f"Erro ao criar sessão: {e}")
        return None

def show_auth_form():
    """Exibe o formulário de login e registro"""
    
    # CSS para login
    st.markdown(get_login_css(), unsafe_allow_html=True)
    
    # Container principal centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Cabeçalho elegante
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="color: #2E86AB; margin-bottom: 0.5rem;">⛪ Mídia Church</h1>
            <p style="color: #666; font-size: 1.1rem; margin-bottom: 2rem;">Sistema de Gerenciamento</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs estilizadas para Login, Registro e Recuperação
        tab1, tab2, tab3 = st.tabs(["🔑 Entrar", "📝 Criar Conta", "🔄 Recuperar Senha"])
        
        with tab1:
            show_login_tab()
        
        with tab2:
            show_register_tab()
            
        with tab3:
            show_password_recovery_tab()
        
        # Rodapé informativo
        st.markdown("""
        <div style="text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee;">
            <small style="color: #888;">
                🔒 Suas informações estão seguras e protegidas<br>
                💡 Problemas para acessar? Entre em contato com o administrador
            </small>
        </div>
        """, unsafe_allow_html=True)

def show_login_tab():
    """Exibe a aba de login"""
    
    st.markdown("### 🔐 Acesse sua conta")
    st.markdown("*Digite suas credenciais para entrar no sistema*")
    
    with st.form("login_form", clear_on_submit=False):
        # Campos de entrada com ícones
        username = st.text_input(
            "👤 Usuário", 
            placeholder="Digite seu nome de usuário",
            help="Use o nome de usuário criado no registro"
        )
        password = st.text_input(
            "🔒 Senha", 
            type="password",
            placeholder="Digite sua senha",
            help="Sua senha é case-sensitive"
        )
        
        # Opção de lembrar login
        remember_me = st.checkbox("🔄 Manter-me conectado", value=True)
        
        # Checkbox para confiar no dispositivo
        trust_device = st.checkbox("📱 Confiar neste dispositivo", 
                                 help="Marque esta opção para não precisar fazer login novamente neste dispositivo",
                                 key="trust_device")
        
        # Botão de login estilizado
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.form_submit_button(
                "🚀 Entrar no Sistema", 
                use_container_width=True,
                type="primary"
            )
        
        if submit_button:
            # Validação básica
            if not username or not password:
                st.error("⚠️ Por favor, preencha todos os campos!")
                return
            
            # Mostrar indicador de carregamento
            with st.spinner("🔍 Verificando credenciais..."):
                try:
                    # Sanitizar entrada
                    username = DataValidator.sanitize_string(username, 30)
                    
                    # Verificar rate limiting
                    if not SecurityHelper.check_rate_limit(username, "LOGIN_ATTEMPT", 5, 15):
                        st.error("🚫 Muitas tentativas de login. Tente novamente em 15 minutos.")
                        SecurityHelper.log_security_event("LOGIN_RATE_LIMITED", f"Rate limit exceeded for user: {username}", username)
                        return
                    
                    # Registrar tentativa de login
                    SecurityHelper.log_security_event("LOGIN_ATTEMPT", f"Login attempt for user: {username}", username)
                    
                    if authenticate_user(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        
                        # Criar sessão persistente se solicitado
                        if remember_me:
                            session_token = create_session_token(username, remember_me=True, trust_device=trust_device)
                            if session_token:
                                st.session_state.session_token = session_token
                        
                        SecurityHelper.log_security_event("LOGIN_SUCCESS", f"Successful login for user: {username}", username)
                        
                        # Feedback de sucesso
                        st.success("✅ Login realizado com sucesso!")
                        
                        # Pequeno delay para mostrar o sucesso
                        time.sleep(1)
                        st.rerun()
                    else:
                        SecurityHelper.log_security_event("LOGIN_FAILED", f"Failed login attempt for user: {username}", username)
                        st.error("❌ Usuário ou senha incorretos!")
                        st.info("💡 Verifique se digitou corretamente ou crie uma nova conta na aba 'Criar Conta'")
                        
                except Exception as e:
                    st.error(f"⚠️ Erro durante o login: {e}")
                    st.info("🔧 Se o problema persistir, entre em contato com o administrador")
    
    # Links úteis
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❓ Esqueci minha senha", use_container_width=True):
            st.info("🔧 Funcionalidade de recuperação de senha em desenvolvimento")
    with col2:
        if st.button("👥 Primeiro acesso?", use_container_width=True):
            st.info("📝 Use a aba 'Criar Conta' para se registrar")

def show_register_tab():
    """Exibe a aba de registro"""
    
    st.markdown("### 📝 Criar nova conta")
    st.markdown("*Preencha os dados abaixo para se cadastrar no sistema*")
    
    with st.form("register_form", clear_on_submit=False):
        # Informações básicas
        st.markdown("#### 👤 Informações Pessoais")
        
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input(
                "📛 Nome Completo *", 
                placeholder="Seu nome completo",
                help="Digite seu nome completo como aparece nos documentos"
            )
        with col2:
            username = st.text_input(
                "🏷️ Nome de Usuário *", 
                placeholder="Escolha um nome único",
                help="Apenas letras, números e underscore. Mín. 3 caracteres"
            )
        
        email = st.text_input(
            "📧 Email *", 
            placeholder="seu.email@exemplo.com",
            help="Será usado para comunicações importantes"
        )
        
        # Informações de segurança
        st.markdown("#### 🔐 Segurança")
        
        col1, col2 = st.columns(2)
        with col1:
            password = st.text_input(
                "🔒 Senha *", 
                type="password",
                placeholder="Crie uma senha forte",
                help="Mín. 8 caracteres com letras, números e símbolos"
            )
        with col2:
            confirm_password = st.text_input(
                "🔒 Confirmar Senha *", 
                type="password",
                placeholder="Digite a senha novamente",
                help="Deve ser idêntica à senha anterior"
            )
        
        # Informações opcionais
        st.markdown("#### 📞 Informações Adicionais (Opcional)")
        phone = st.text_input(
            "📱 Telefone", 
            placeholder="(11) 99999-9999",
            help="Formato: (XX) XXXXX-XXXX"
        )
        
        # Termos e condições
        st.markdown("---")
        terms_accepted = st.checkbox(
            "✅ Aceito os termos de uso e política de privacidade",
            help="Obrigatório para criar a conta"
        )
        
        # Botão de registro
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.form_submit_button(
                "🎉 Criar Minha Conta", 
                use_container_width=True,
                type="primary"
            )
        
        if submit_button:
            # Validação de termos
            if not terms_accepted:
                st.error("⚠️ Você deve aceitar os termos de uso para continuar!")
                return
            
            # Mostrar indicador de carregamento
            with st.spinner("🔄 Criando sua conta..."):
                try:
                    # Sanitizar entradas
                    full_name = DataValidator.sanitize_string(full_name, 100)
                    username = DataValidator.sanitize_string(username, 30)
                    email = DataValidator.sanitize_string(email, 255)
                    phone = DataValidator.sanitize_string(phone, 20) if phone else None
                    
                    # Validações
                    errors = []
                    
                    if not all([full_name, username, email, password, confirm_password]):
                        errors.append("⚠️ Preencha todos os campos obrigatórios!")
                    
                    # Validar nome de usuário
                    username_validation = DataValidator.validate_username(username)
                    if not username_validation["valid"]:
                        errors.extend([f"👤 {error}" for error in username_validation["errors"]])
                    
                    # Validar email
                    if not DataValidator.validate_email(email):
                        errors.append("📧 Email inválido!")
                    
                    # Validar senha
                    password_validation = DataValidator.validate_password(password)
                    if not password_validation["valid"]:
                        errors.extend([f"🔒 {error}" for error in password_validation["errors"]])
                    
                    if password != confirm_password:
                        errors.append("🔒 As senhas não coincidem!")
                    
                    # Validar telefone se fornecido
                    if phone and not DataValidator.validate_phone(phone):
                        errors.append("📱 Número de telefone inválido!")
                    
                    # Verificar se usuário já existe
                    if not errors:
                        if user_exists(username, email):
                            errors.append("👥 Usuário ou email já cadastrado!")
                    
                    if errors:
                        st.error("❌ Corrija os seguintes problemas:")
                        for error in errors:
                            st.write(f"• {error}")
                        SecurityHelper.log_security_event("REGISTRATION_FAILED", f"Failed registration attempt for username: {username}, email: {email}")
                    else:
                        # Criar usuário
                        if create_user_auth(username, email, password, full_name, phone):
                            SecurityHelper.log_security_event("REGISTRATION_SUCCESS", f"New user registered: {username}")
                            
                            # Enviar email de boas-vindas
                            email_sent = False
                            try:
                                from app.utils.email_service import send_welcome_email
                                email_result = send_welcome_email(email, username, full_name)
                                if email_result['success']:
                                    email_sent = True
                            except Exception:
                                # Não bloquear registro por erro de email
                                pass
                            
                            # Feedback de sucesso
                            st.success("🎉 Conta criada com sucesso!")
                            if email_sent:
                                st.info("📧 Email de boas-vindas enviado!")
                            st.info("✨ Agora você pode fazer login na aba 'Entrar'")
                            st.balloons()
                            
                            # Limpar formulário após sucesso
                            time.sleep(2)
                            st.rerun()
                        else:
                            SecurityHelper.log_security_event("REGISTRATION_ERROR", f"Database error during registration for username: {username}")
                            st.error("❌ Erro ao criar conta. Tente novamente.")
                            
                except Exception as e:
                    st.error(f"⚠️ Erro durante o registro: {e}")
                    st.info("🔧 Se o problema persistir, entre em contato com o administrador")
    
    # Informações adicionais
    st.markdown("---")
    with st.expander("ℹ️ Informações sobre o registro"):
        st.markdown("""
        **🔒 Segurança dos dados:**
        - Suas informações são criptografadas e protegidas
        - Senhas são armazenadas com hash seguro
        - Nunca compartilhamos seus dados pessoais
        
        **📧 Comunicações:**
        - Enviaremos apenas notificações importantes
        - Você pode cancelar a inscrição a qualquer momento
        
        **❓ Dúvidas:**
        - Entre em contato com o administrador do sistema
        - Suporte técnico disponível durante horário comercial
        """)

def authenticate_user(username, password):
    """Autentica usuário com rate limiting e logs de segurança"""
    try:
        # Verificar rate limiting
        if not SecurityHelper.check_rate_limit(username, "LOGIN_ATTEMPT", 5, 15):
            return False
        
        # Buscar usuário
        user = get_user_by_username(username)
        
        if user and user.get('is_active', True) and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            # Login bem-sucedido
            
            # Armazenar informações do usuário na sessão
            st.session_state.user_info = {
                'id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'role': user['role']
            }
            return True
        else:
            # Login falhou
            return False
                
    except Exception as e:
        st.error(f"Erro na autenticação: {e}")
        return False

def user_exists(username, email):
    """Verifica se um usuário já existe"""
    try:
        # Verificar por username
        user_by_username = get_user_by_username(username)
        if user_by_username:
            return True
            
        # Verificar por email
        user_by_email = get_user_by_email(email)
        if user_by_email:
            return True
            
        return False
    except Exception as e:
        st.error(f"Erro ao verificar usuário: {e}")
        return True  # Em caso de erro, assume que existe para evitar duplicatas

def create_user_auth(username, email, password, full_name, phone=None):
    """Cria um novo usuário (função local do auth.py)"""
    try:
        # Hash da senha
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Usar a função do local_connection
        user_id = create_user(username, email, password_hash, full_name, phone, 'member')
        return user_id is not None
    except Exception as e:
        st.error(f"Erro ao criar usuário: {e}")
        return False

def logout():
    """Faz logout do usuário"""
    try:
        # Invalidar sessão persistente se existir
        session_token = st.session_state.get('session_token')
        if session_token:
            # Usar db_manager para invalidar sessão
            with db_manager.get_db_session() as session:
                session.execute(
                    text("UPDATE user_sessions SET is_active = 0 WHERE session_token = :token"),
                    {"token": session_token}
                )
                session.commit()
            
        # Limpar query params
        if 'session_token' in st.query_params:
            del st.query_params['session_token']
            
    except Exception as e:
        # Continuar com logout mesmo se houver erro
        pass
    
    # Limpar session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def get_current_user():
    """Retorna informações do usuário atual"""
    return st.session_state.get('user_info', {})

def is_admin():
    """Verifica se o usuário atual é administrador"""
    try:
        user_info = get_current_user()
        return user_info.get('role') == 'admin'
    except Exception:
        return False

def get_user_role():
    """Retorna o papel/role do usuário atual"""
    try:
        user_info = get_current_user()
        return user_info.get('role', 'guest')
    except Exception:
        return 'guest'

def require_auth():
    """Função para exigir autenticação - retorna True se autenticado"""
    return check_authentication()

def require_admin():
    """Decorator/função para exigir privilégios de administrador"""
    if not is_admin():
        st.error("🚫 Acesso negado! Esta funcionalidade requer privilégios de administrador.")
        st.stop()
    return True

def show_password_recovery_tab():
    """Exibe a aba de recuperação de senha"""
    
    st.markdown("### 🔄 Recuperar Senha")
    st.markdown("*Digite seu email para receber instruções de recuperação*")
    
    with st.form("password_recovery_form", clear_on_submit=False):
        email = st.text_input(
            "📧 Email", 
            placeholder="Digite o email cadastrado",
            help="Enviaremos um link de recuperação para este email"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.form_submit_button(
                "📤 Enviar Link de Recuperação", 
                use_container_width=True,
                type="primary"
            )
        
        if submit_button:
            if not email:
                st.error("⚠️ Por favor, digite seu email!")
                return
            
            if not DataValidator.validate_email(email):
                st.error("📧 Email inválido!")
                return
            
            with st.spinner("📤 Enviando email de recuperação..."):
                if send_password_recovery_email(email):
                    st.success("✅ Email de recuperação enviado!")
                    st.info("📧 Verifique sua caixa de entrada e spam")
                    st.info("🔗 O link de recuperação expira em 1 hora")
                else:
                    st.error("❌ Email não encontrado ou erro no envio")
    
    st.markdown("---")
    with st.expander("ℹ️ Como funciona a recuperação"):
        st.markdown("""
        **📧 Processo de recuperação:**
        1. Digite o email cadastrado na sua conta
        2. Receba um link seguro por email
        3. Clique no link para definir nova senha
        4. O link expira em 1 hora por segurança
        
        **🔒 Segurança:**
        - Links são únicos e temporários
        - Apenas você pode acessar com seu email
        - Senhas antigas são invalidadas
        
        **❓ Problemas:**
        - Verifique a pasta de spam
        - Certifique-se de usar o email correto
        - Entre em contato com o administrador se necessário
        """)

def send_password_recovery_email(email):
    """Envia email de recuperação de senha"""
    try:
        # Verificar se email existe
        user = get_user_by_email(email)
        
        if not user:
            return False
        
        user_id = user['id']
        username = user['username']
        full_name = user['full_name']
        
        # Gerar token de recuperação
        recovery_token = generate_recovery_token(user_id)
        
        if not recovery_token:
            return False
        
        # Enviar email
        try:
            from app.utils.email_service import send_password_recovery_email as send_email
            email_result = send_email(email, username, full_name, recovery_token)
            return email_result.get('success', False)
        except Exception:
            # Se não conseguir enviar email, ainda retorna True para não revelar se email existe
            return True
            
    except Exception as e:
        st.error(f"Erro no processo de recuperação: {e}")
        return False

def generate_recovery_token(user_id):
    """Gera token de recuperação de senha"""
    try:
        # Gerar token único
        timestamp = str(time.time())
        random_data = os.urandom(32).hex()
        token_data = f"{user_id}:{timestamp}:{random_data}"
        recovery_token = hashlib.sha256(token_data.encode()).hexdigest()
        
        # Definir expiração (1 hora)
        expires_at = datetime.now() + timedelta(hours=1)
        
        with db_manager.get_db_session() as session:
            # Invalidar tokens antigos do usuário
            session.execute(
                text("UPDATE password_recovery_tokens SET is_active = 0 WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            
            # Criar novo token
            session.execute(
                text("""
                INSERT INTO password_recovery_tokens (user_id, token, expires_at, created_at, is_active)
                VALUES (:user_id, :token, :expires_at, datetime('now'), 1)
                """),
                {
                    "user_id": user_id,
                    "token": recovery_token,
                    "expires_at": expires_at.isoformat()
                }
            )
            session.commit()
        
        return recovery_token
        
    except Exception as e:
        st.error(f"Erro ao gerar token: {e}")
        return None

def create_password_recovery_table():
    """Cria tabela para tokens de recuperação de senha"""
    try:
        with db_manager.get_db_session() as session:
            session.execute(text("""
            CREATE TABLE IF NOT EXISTS password_recovery_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                token TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                used_at TEXT NULL,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """))
            
            # Índices para performance
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_recovery_tokens_user_id ON password_recovery_tokens(user_id)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_recovery_tokens_token ON password_recovery_tokens(token)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_recovery_tokens_expires ON password_recovery_tokens(expires_at)"))
            session.commit()
        
        return True
    except Exception as e:
        st.error(f"Erro ao criar tabela de recuperação: {str(e)}")
        return False

def create_user_sessions_table():
    """Cria tabela para sessões de usuário com suporte a dispositivos"""
    try:
        with db_manager.get_db_session() as session:
            # Primeiro, verificar se a tabela existe e quais colunas tem
            result = session.execute(text("PRAGMA table_info(user_sessions)")).fetchall()
            existing_columns = [row[1] for row in result] if result else []
            
            # Criar tabela se não existir
            session.execute(text("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_token TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_accessed TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                user_agent TEXT NULL,
                ip_address TEXT NULL,
                device_fingerprint TEXT NULL,
                is_trusted INTEGER DEFAULT 0,
                device_name TEXT NULL,
                last_login_location TEXT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """))
            
            # Adicionar novas colunas se a tabela já existir mas não tiver as colunas
            if existing_columns:
                if 'user_agent' not in existing_columns:
                    session.execute(text("ALTER TABLE user_sessions ADD COLUMN user_agent TEXT NULL"))
                
                if 'ip_address' not in existing_columns:
                    session.execute(text("ALTER TABLE user_sessions ADD COLUMN ip_address TEXT NULL"))
                
                if 'device_fingerprint' not in existing_columns:
                    session.execute(text("ALTER TABLE user_sessions ADD COLUMN device_fingerprint TEXT NULL"))
                
                if 'is_trusted' not in existing_columns:
                    session.execute(text("ALTER TABLE user_sessions ADD COLUMN is_trusted INTEGER DEFAULT 0"))
                
                if 'device_name' not in existing_columns:
                    session.execute(text("ALTER TABLE user_sessions ADD COLUMN device_name TEXT NULL"))
                
                if 'last_login_location' not in existing_columns:
                    session.execute(text("ALTER TABLE user_sessions ADD COLUMN last_login_location TEXT NULL"))
            
            # Índices para performance
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_sessions_device ON user_sessions(device_fingerprint)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_sessions_trusted ON user_sessions(user_id, is_trusted)"))
            session.commit()
        
        # Limpar sessões expiradas
        cleanup_expired_sessions()
        
        return True
    except Exception as e:
        st.error(f"Erro ao criar/atualizar tabela de sessões: {str(e)}")
        return False

def cleanup_expired_sessions():
    """Remove sessões expiradas do banco de dados"""
    try:
        with db_manager.get_db_session() as session:
            # Marcar sessões expiradas como inativas
            session.execute(
                text("UPDATE user_sessions SET is_active = 0 WHERE expires_at <= datetime('now')")
            )
            
            # Remover sessões muito antigas (mais de 60 dias)
            session.execute(
                text("DELETE FROM user_sessions WHERE created_at <= datetime('now', '-60 days')")
            )
            
            session.commit()
        
        return True
    except Exception as e:
        # Não mostrar erro para o usuário, apenas registrar
        if 'debug_mode' in st.session_state and st.session_state.debug_mode:
            st.warning(f"⚠️ Erro na limpeza de sessões: {e}")
        return False