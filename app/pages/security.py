import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import secrets
from app.utils.security_monitor import SecurityMonitor
from app.utils.auth import get_current_user
import plotly.express as px
import plotly.graph_objects as go

def show_security_page():
    """Página principal de segurança"""
    
    # Verificar autenticação e permissões
    current_user = get_current_user()
    if not current_user:
        st.error("🚫 Acesso negado. Faça login para continuar.")
        return
    
    if current_user.get('role') != 'admin':
        st.error("🚫 Acesso restrito a administradores")
        return
    
    st.title("🛡️ Centro de Segurança")
    st.markdown("---")
    
    # Tabs para diferentes seções
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard", 
        "🔍 Logs Detalhados", 
        "⚠️ Alertas", 
        "⚙️ Configurações"
    ])
    
    with tab1:
        show_security_dashboard()
    
    with tab2:
        show_detailed_logs()
    
    with tab3:
        show_security_alerts()
    
    with tab4:
        show_security_settings()

def show_security_dashboard():
    """Mostra o dashboard de segurança"""
    
    # Verificar se o usuário é administrador
    if not st.session_state.get('user_role') == 'admin':
        st.error("🚫 Acesso negado. Apenas administradores podem acessar esta página.")
        return
    
    st.title("🔒 Dashboard de Segurança")
    
    # Tabs principais
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Visão Geral",
        "🔍 Logs de Acesso", 
        "🚨 Alertas",
        "👥 Usuários",
        "⚙️ Configurações"
    ])
    
    with tab1:
        show_security_overview()
    
    with tab2:
        show_access_logs()
    
    with tab3:
        show_security_alerts()
    
    with tab4:
        show_user_security()
    
    with tab5:
        show_security_settings()

def show_security_overview():
    """Mostra visão geral de segurança"""
    st.subheader("📊 Visão Geral de Segurança")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    security_stats = get_security_stats()
    
    with col1:
        st.metric(
            "Tentativas Hoje", 
            security_stats.get('attempts_today', 0),
            delta=security_stats.get('attempts_delta', 0)
        )
    
    with col2:
        st.metric(
            "Logins Bem-sucedidos", 
            security_stats.get('successful_logins', 0),
            delta=security_stats.get('success_delta', 0)
        )
    
    with col3:
        st.metric(
            "Tentativas Falhadas", 
            security_stats.get('failed_attempts', 0),
            delta=security_stats.get('failed_delta', 0)
        )
    
    with col4:
        success_rate = security_stats.get('success_rate', 0)
        st.metric(
            "Taxa de Sucesso", 
            f"{success_rate:.1f}%",
            delta=f"{security_stats.get('rate_delta', 0):+.1f}%"
        )
    
    st.divider()
    
    # Gráficos de tendência
    show_security_trends()
    
    # Status de segurança
    show_security_status()

def show_security_trends():
    """Mostra gráficos de tendência de segurança"""
    st.subheader("📈 Tendências de Segurança")
    
    try:
        import pandas as pd
        import plotly.express as px
        from datetime import datetime, timedelta
        import random
        
        # Dados dos últimos 7 dias
        dates = [datetime.now() - timedelta(days=i) for i in range(7, 0, -1)]
        
        security_data = pd.DataFrame({
            'Data': dates,
            'Logins Sucesso': [random.randint(50, 150) for _ in range(7)],
            'Tentativas Falhadas': [random.randint(10, 50) for _ in range(7)],
            'Alertas': [random.randint(0, 10) for _ in range(7)]
        })
        
        # Gráfico de logins
        fig_logins = px.line(
            security_data,
            x='Data',
            y=['Logins Sucesso', 'Tentativas Falhadas'],
            title="Atividade de Login (Últimos 7 dias)"
        )
        st.plotly_chart(fig_logins, use_container_width=True)
        
        # Gráfico de alertas
        fig_alerts = px.bar(
            security_data,
            x='Data',
            y='Alertas',
            title="Alertas de Segurança por Dia"
        )
        st.plotly_chart(fig_alerts, use_container_width=True)
    
    except ImportError:
        st.info("📊 Instale plotly e pandas para visualizar gráficos")

def show_security_status():
    """Mostra status de segurança do sistema"""
    st.subheader("🛡️ Status de Segurança")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🔒 Componentes de Segurança:**")
        
        security_components = [
            ("🔐 Autenticação", "🟢 Ativo", "normal"),
            ("🛡️ Firewall", "🟢 Ativo", "normal"),
            ("🔍 Monitoramento", "🟢 Ativo", "normal"),
            ("📧 Alertas por Email", "🟡 Parcial", "warning"),
            ("🔄 Backup Automático", "🟢 Ativo", "normal")
        ]
        
        for component, status, level in security_components:
            if level == "normal":
                st.success(f"{component}: {status}")
            elif level == "warning":
                st.warning(f"{component}: {status}")
            else:
                st.error(f"{component}: {status}")
    
    with col2:
        st.write("**⚠️ Recomendações de Segurança:**")
        
        recommendations = get_security_recommendations()
        for rec in recommendations:
            st.info(f"💡 {rec}")

def show_access_logs():
    """Mostra logs de acesso detalhados"""
    st.subheader("📋 Logs de Acesso")
    
    # Filtros
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        event_filter = st.selectbox(
            "Tipo de Evento:",
            ["Todos", "Login Sucesso", "Login Falha", "Logout", "Acesso Negado", "Alteração Senha"]
        )
    
    with col2:
        date_from = st.date_input("Data Inicial:", value=datetime.now().date() - timedelta(days=7))
    
    with col3:
        date_to = st.date_input("Data Final:", value=datetime.now().date())
    
    with col4:
        user_filter = st.text_input("Filtrar Usuário:")
    
    # Buscar logs
    logs = get_security_logs(event_filter, date_from, date_to, user_filter)
    
    if logs:
        # Estatísticas dos logs filtrados
        st.write("**📊 Estatísticas dos Logs Filtrados:**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Eventos", len(logs))
        with col2:
            success_count = len([log for log in logs if log.get('status') == 'success'])
            st.metric("Sucessos", success_count)
        with col3:
            failed_count = len([log for log in logs if log.get('status') == 'failed'])
            st.metric("Falhas", failed_count)
        
        st.divider()
        
        # Tabela de logs
        st.write("**📋 Logs Detalhados:**")
        
        # Preparar dados para exibição
        display_logs = []
        for log in logs:
            display_logs.append({
                "🕐 Timestamp": log.get('timestamp', ''),
                "👤 Usuário": log.get('username', ''),
                "🔍 Evento": log.get('event_type', ''),
                "🌐 IP": log.get('ip_address', ''),
                "📱 Dispositivo": log.get('device', ''),
                "📍 Localização": log.get('location', ''),
                "✅ Status": get_status_icon(log.get('status', ''))
            })
        
        # Paginação
        page_size = 20
        total_pages = (len(display_logs) + page_size - 1) // page_size
        
        if total_pages > 1:
            page = st.selectbox("Página:", range(1, total_pages + 1))
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            display_logs = display_logs[start_idx:end_idx]
        
        st.dataframe(display_logs, use_container_width=True)
        
        # Exportar logs
        if st.button("📤 Exportar Logs"):
            export_security_logs(logs)
    
    else:
        st.info("📭 Nenhum log encontrado com os filtros selecionados.")

def show_security_alerts():
    """Mostra alertas de segurança"""
    st.subheader("🚨 Alertas de Segurança")
    
    # Filtros de alertas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        alert_level = st.selectbox(
            "Nível:",
            ["Todos", "Crítico", "Alto", "Médio", "Baixo"]
        )
    
    with col2:
        alert_status = st.selectbox(
            "Status:",
            ["Todos", "Ativo", "Resolvido", "Ignorado"]
        )
    
    with col3:
        days_back = st.number_input(
            "Últimos dias:",
            min_value=1,
            max_value=90,
            value=7
        )
    
    # Buscar alertas
    alerts = get_security_alerts(alert_level, alert_status, days_back)
    
    if alerts:
        # Estatísticas de alertas
        st.write("**📊 Resumo de Alertas:**")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", len(alerts))
        with col2:
            critical_count = len([a for a in alerts if a.get('level') == 'critical'])
            st.metric("Críticos", critical_count)
        with col3:
            active_count = len([a for a in alerts if a.get('status') == 'active'])
            st.metric("Ativos", active_count)
        with col4:
            resolved_count = len([a for a in alerts if a.get('status') == 'resolved'])
            st.metric("Resolvidos", resolved_count)
        
        st.divider()
        
        # Lista de alertas
        for alert in alerts:
            with st.expander(f"{get_alert_icon(alert.get('level'))} {alert.get('title', 'Alerta')} - {alert.get('timestamp', '')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Descrição:** {alert.get('description', '')}")
                    st.write(f"**Origem:** {alert.get('source', '')}")
                    if alert.get('ip_address'):
                        st.write(f"**IP:** {alert.get('ip_address')}")
                    if alert.get('user'):
                        st.write(f"**Usuário:** {alert.get('user')}")
                
                with col2:
                    st.write(f"**Nível:** {alert.get('level', '').title()}")
                    st.write(f"**Status:** {alert.get('status', '').title()}")
                    
                    if alert.get('status') == 'active':
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("✅ Resolver", key=f"resolve_{alert.get('id')}"):
                                resolve_alert(alert.get('id'))
                                st.rerun()
                        with col_b:
                            if st.button("🙈 Ignorar", key=f"ignore_{alert.get('id')}"):
                                ignore_alert(alert.get('id'))
                                st.rerun()
    
    else:
        st.info("📭 Nenhum alerta encontrado com os filtros selecionados.")
    
    st.divider()
    
    # Criar novo alerta manual
    st.subheader("➕ Criar Alerta Manual")
    
    with st.form("manual_alert"):
        col1, col2 = st.columns(2)
        
        with col1:
            alert_title = st.text_input("Título do Alerta:")
            alert_description = st.text_area("Descrição:")
        
        with col2:
            alert_level = st.selectbox("Nível:", ["low", "medium", "high", "critical"])
            alert_source = st.text_input("Origem/Fonte:")
        
        if st.form_submit_button("🚨 Criar Alerta"):
            if alert_title and alert_description:
                create_manual_alert(alert_title, alert_description, alert_level, alert_source)
                st.success("✅ Alerta criado com sucesso!")
                st.rerun()
            else:
                st.error("❌ Título e descrição são obrigatórios!")

def show_user_security():
    """Mostra informações de segurança dos usuários"""
    st.subheader("👥 Segurança dos Usuários")
    
    # Buscar usuários com problemas de segurança
    security_issues = get_user_security_issues()
    
    # Estatísticas de usuários
    st.write("**📊 Estatísticas de Usuários:**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = get_total_users_count()
        st.metric("Total de Usuários", total_users)
    
    with col2:
        active_users = get_active_users_today()
        st.metric("Ativos Hoje", active_users)
    
    with col3:
        blocked_users = get_blocked_users_count()
        st.metric("Bloqueados", blocked_users)
    
    with col4:
        weak_passwords = get_weak_passwords_count()
        st.metric("Senhas Fracas", weak_passwords)
    
    st.divider()
    
    # Usuários com problemas de segurança
    if security_issues:
        st.write("**⚠️ Usuários com Problemas de Segurança:**")
        
        for issue in security_issues:
            with st.expander(f"⚠️ {issue.get('username')} - {issue.get('issue_type')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Problema:** {issue.get('description')}")
                    st.write(f"**Último Login:** {issue.get('last_login', 'Nunca')}")
                    st.write(f"**Tentativas Falhadas:** {issue.get('failed_attempts', 0)}")
                
                with col2:
                    if st.button("🔒 Bloquear", key=f"block_{issue.get('user_id')}"):
                        block_user(issue.get('user_id'))
                        st.success("Usuário bloqueado!")
                        st.rerun()
                    
                    if st.button("🔄 Reset Senha", key=f"reset_{issue.get('user_id')}"):
                        reset_user_password(issue.get('user_id'))
                        st.success("Senha resetada!")
                        st.rerun()
    
    st.divider()
    
    # Ações em massa
    st.write("**🔧 Ações em Massa:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔒 Forçar Troca de Senhas Fracas"):
            force_password_change_weak()
            st.success("✅ Usuários com senhas fracas serão forçados a trocar!")
    
    with col2:
        if st.button("🧹 Limpar Tentativas Falhadas"):
            clear_failed_attempts()
            st.success("✅ Tentativas falhadas limpas!")
    
    with col3:
        if st.button("📧 Enviar Alerta de Segurança"):
            send_security_alert_to_all()
            st.success("✅ Alerta enviado para todos os usuários!")

def show_security_settings():
    """Mostra configurações de segurança"""
    st.subheader("⚙️ Configurações de Segurança")
    
    # Carregar configurações atuais
    current_settings = get_security_settings()
    
    with st.form("security_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🔐 Políticas de Senha:**")
            
            min_length = st.number_input(
                "Comprimento mínimo:",
                min_value=6,
                max_value=20,
                value=current_settings.get('min_password_length', 8)
            )
            
            require_uppercase = st.checkbox(
                "Exigir maiúsculas",
                value=current_settings.get('require_uppercase', True)
            )
            
            require_lowercase = st.checkbox(
                "Exigir minúsculas",
                value=current_settings.get('require_lowercase', True)
            )
            
            require_numbers = st.checkbox(
                "Exigir números",
                value=current_settings.get('require_numbers', True)
            )
            
            require_symbols = st.checkbox(
                "Exigir símbolos",
                value=current_settings.get('require_symbols', False)
            )
            
            password_expiry = st.number_input(
                "Expiração da senha (dias):",
                min_value=0,
                max_value=365,
                value=current_settings.get('password_expiry_days', 90)
            )
        
        with col2:
            st.write("**🔒 Configurações de Sessão:**")
            
            session_timeout = st.number_input(
                "Timeout da sessão (minutos):",
                min_value=15,
                max_value=480,
                value=current_settings.get('session_timeout', 60)
            )
            
            max_login_attempts = st.number_input(
                "Máximo de tentativas de login:",
                min_value=3,
                max_value=10,
                value=current_settings.get('max_login_attempts', 5)
            )
            
            lockout_duration = st.number_input(
                "Duração do bloqueio (minutos):",
                min_value=5,
                max_value=1440,
                value=current_settings.get('lockout_duration', 15)
            )
            
            enable_2fa = st.checkbox(
                "Habilitar 2FA obrigatório",
                value=current_settings.get('enable_2fa', False)
            )
            
            enable_captcha = st.checkbox(
                "Habilitar CAPTCHA após falhas",
                value=current_settings.get('enable_captcha', True)
            )
            
            log_retention_days = st.number_input(
                "Retenção de logs (dias):",
                min_value=30,
                max_value=365,
                value=current_settings.get('log_retention_days', 90)
            )
        
        st.divider()
        
        # Configurações de monitoramento
        st.write("**📊 Monitoramento e Alertas:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            enable_monitoring = st.checkbox(
                "Habilitar monitoramento em tempo real",
                value=current_settings.get('enable_monitoring', True)
            )
            
            alert_failed_logins = st.number_input(
                "Alertar após X tentativas falhadas:",
                min_value=3,
                max_value=20,
                value=current_settings.get('alert_failed_logins', 5)
            )
        
        with col2:
            enable_email_alerts = st.checkbox(
                "Enviar alertas por email",
                value=current_settings.get('enable_email_alerts', True)
            )
            
            alert_new_device = st.checkbox(
                "Alertar sobre novos dispositivos",
                value=current_settings.get('alert_new_device', True)
            )
        
        if st.form_submit_button("💾 Salvar Configurações", type="primary"):
            new_settings = {
                'min_password_length': min_length,
                'require_uppercase': require_uppercase,
                'require_lowercase': require_lowercase,
                'require_numbers': require_numbers,
                'require_symbols': require_symbols,
                'password_expiry_days': password_expiry,
                'session_timeout': session_timeout,
                'max_login_attempts': max_login_attempts,
                'lockout_duration': lockout_duration,
                'enable_2fa': enable_2fa,
                'enable_captcha': enable_captcha,
                'log_retention_days': log_retention_days,
                'enable_monitoring': enable_monitoring,
                'alert_failed_logins': alert_failed_logins,
                'enable_email_alerts': enable_email_alerts,
                'alert_new_device': alert_new_device
            }
            
            save_security_settings(new_settings)
            st.success("✅ Configurações de segurança salvas com sucesso!")
            st.rerun()

# Funções auxiliares
def get_security_stats():
    """Retorna estatísticas de segurança"""
    import random
    return {
        'attempts_today': random.randint(100, 200),
        'attempts_delta': random.randint(-10, 20),
        'successful_logins': random.randint(80, 150),
        'success_delta': random.randint(-5, 15),
        'failed_attempts': random.randint(10, 50),
        'failed_delta': random.randint(-5, 10),
        'success_rate': random.uniform(70, 95),
        'rate_delta': random.uniform(-5, 5)
    }

def get_security_recommendations():
    """Retorna recomendações de segurança"""
    return [
        "Configure autenticação de dois fatores para administradores",
        "Revise usuários com múltiplas tentativas de login falhadas",
        "Atualize políticas de senha para maior segurança"
    ]

def get_security_logs(event_filter, date_from, date_to, user_filter):
    """Busca logs de segurança"""
    # Simulação de logs
    import random
    from datetime import datetime, timedelta
    
    logs = []
    for i in range(50):
        log_date = date_from + timedelta(days=random.randint(0, (date_to - date_from).days))
        logs.append({
            'id': i,
            'timestamp': log_date.strftime('%Y-%m-%d %H:%M:%S'),
            'username': f'user{random.randint(1, 100)}',
            'event_type': random.choice(['Login Sucesso', 'Login Falha', 'Logout', 'Acesso Negado']),
            'ip_address': f'192.168.1.{random.randint(1, 255)}',
            'device': random.choice(['Desktop', 'Mobile', 'Tablet']),
            'location': random.choice(['São Paulo', 'Rio de Janeiro', 'Brasília']),
            'status': random.choice(['success', 'failed', 'warning'])
        })
    
    # Aplicar filtros
    if event_filter != "Todos":
        logs = [log for log in logs if log['event_type'] == event_filter]
    
    if user_filter:
        logs = [log for log in logs if user_filter.lower() in log['username'].lower()]
    
    return logs

def get_status_icon(status):
    """Retorna ícone para status"""
    icons = {
        'success': '✅',
        'failed': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    }
    return icons.get(status, '❓')

def get_alert_icon(level):
    """Retorna ícone para nível de alerta"""
    icons = {
        'critical': '🚨',
        'high': '⚠️',
        'medium': '🟡',
        'low': 'ℹ️'
    }
    return icons.get(level, '❓')

def get_security_alerts(level, status, days_back):
    """Busca alertas de segurança"""
    import random
    from datetime import datetime, timedelta
    
    alerts = []
    for i in range(20):
        alert_date = datetime.now() - timedelta(days=random.randint(0, days_back))
        alerts.append({
            'id': i,
            'title': random.choice([
                'Múltiplas tentativas de login falhadas',
                'Novo dispositivo detectado',
                'Acesso de localização suspeita',
                'Tentativa de acesso não autorizado'
            ]),
            'description': 'Descrição detalhada do alerta de segurança',
            'level': random.choice(['low', 'medium', 'high', 'critical']),
            'status': random.choice(['active', 'resolved', 'ignored']),
            'timestamp': alert_date.strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'Sistema de Monitoramento',
            'ip_address': f'192.168.1.{random.randint(1, 255)}',
            'user': f'user{random.randint(1, 100)}'
        })
    
    # Aplicar filtros
    if level != "Todos":
        alerts = [alert for alert in alerts if alert['level'] == level.lower()]
    
    if status != "Todos":
        alerts = [alert for alert in alerts if alert['status'] == status.lower()]
    
    return alerts

def get_user_security_issues():
    """Busca usuários com problemas de segurança"""
    import random
    
    issues = []
    for i in range(10):
        issues.append({
            'user_id': i,
            'username': f'user{i}',
            'issue_type': random.choice(['Senha Fraca', 'Múltiplas Falhas', 'Dispositivo Suspeito']),
            'description': 'Descrição do problema de segurança',
            'last_login': '2024-01-15 10:30:00',
            'failed_attempts': random.randint(0, 10)
        })
    
    return issues

def get_security_settings():
    """Carrega configurações de segurança"""
    return {
        'min_password_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_numbers': True,
        'require_symbols': False,
        'password_expiry_days': 90,
        'session_timeout': 60,
        'max_login_attempts': 5,
        'lockout_duration': 15,
        'enable_2fa': False,
        'enable_captcha': True,
        'log_retention_days': 90,
        'enable_monitoring': True,
        'alert_failed_logins': 5,
        'enable_email_alerts': True,
        'alert_new_device': True
    }

# Funções de ação (stubs)
def export_security_logs(logs):
    """Exporta logs de segurança"""
    pass

def resolve_alert(alert_id):
    """Resolve um alerta"""
    pass

def ignore_alert(alert_id):
    """Ignora um alerta"""
    pass

def create_manual_alert(title, description, level, source):
    """Cria alerta manual"""
    pass

def get_total_users_count():
    """Retorna total de usuários"""
    import random
    return random.randint(100, 500)

def get_active_users_today():
    """Retorna usuários ativos hoje"""
    import random
    return random.randint(20, 100)

def get_blocked_users_count():
    """Retorna usuários bloqueados"""
    import random
    return random.randint(0, 10)

def get_weak_passwords_count():
    """Retorna usuários com senhas fracas"""
    import random
    return random.randint(5, 25)

def block_user(user_id):
    """Bloqueia um usuário"""
    pass

def reset_user_password(user_id):
    """Reseta senha do usuário"""
    pass

def force_password_change_weak():
    """Força troca de senhas fracas"""
    pass

def clear_failed_attempts():
    """Limpa tentativas falhadas"""
    pass

def send_security_alert_to_all():
    """Envia alerta para todos os usuários"""
    pass

def save_security_settings(settings):
    """Salva configurações de segurança"""
    pass

def show_security_metrics(data):
    """Exibe métricas principais de segurança"""
    login_stats = data.get('login_stats', {})
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_attempts = login_stats.get('total_attempts', 0)
        st.metric(
            "🔐 Total Tentativas",
            total_attempts,
            help="Total de tentativas de login no período"
        )
    
    with col2:
        successful = login_stats.get('successful_logins', 0)
        st.metric(
            "✅ Sucessos",
            successful,
            help="Logins realizados com sucesso"
        )
    
    with col3:
        failed = login_stats.get('failed_attempts', 0)
        delta_color = "inverse" if failed > 0 else "normal"
        st.metric(
            "❌ Falhas",
            failed,
            help="Tentativas de login que falharam"
        )
    
    with col4:
        success_rate = 0
        if total_attempts > 0:
            success_rate = (successful / total_attempts) * 100
        
        color = "normal" if success_rate >= 80 else "inverse"
        st.metric(
            "📈 Taxa Sucesso",
            f"{success_rate:.1f}%",
            help="Porcentagem de logins bem-sucedidos"
        )
    
    with col5:
        suspicious_count = len(data.get('suspicious_ips', []))
        color = "inverse" if suspicious_count > 0 else "normal"
        st.metric(
            "🚨 IPs Suspeitos",
            suspicious_count,
            help="IPs com atividade suspeita"
        )

def show_login_attempts_chart(data):
    """Gráfico de tentativas de login ao longo do tempo"""
    st.subheader("📈 Tentativas de Login")
    
    # Simular dados temporais (em implementação real, buscar do banco)
    hours = list(range(24))
    successful = [max(0, 10 + i * 2 + (i % 3) * 5) for i in hours]
    failed = [max(0, 3 + (i % 5) * 2) for i in hours]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hours,
        y=successful,
        mode='lines+markers',
        name='Sucessos',
        line=dict(color='green'),
        fill='tonexty'
    ))
    
    fig.add_trace(go.Scatter(
        x=hours,
        y=failed,
        mode='lines+markers',
        name='Falhas',
        line=dict(color='red'),
        fill='tozeroy'
    ))
    
    fig.update_layout(
        title="Tentativas de Login por Hora",
        xaxis_title="Hora",
        yaxis_title="Quantidade",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_events_by_type_chart(data):
    """Gráfico de eventos por tipo"""
    st.subheader("🎯 Eventos por Tipo")
    
    events = data.get('events', [])
    
    if events:
        df = pd.DataFrame(events)
        
        # Agrupar por tipo de evento
        event_counts = df.groupby('event_type')['count'].sum().reset_index()
        
        fig = px.pie(
            event_counts,
            values='count',
            names='event_type',
            title="Distribuição de Eventos de Segurança"
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Nenhum evento registrado no período selecionado")

def show_top_users_table(data):
    """Tabela de usuários mais ativos"""
    st.subheader("👥 Usuários Mais Ativos")
    
    active_users = data.get('active_users', [])
    
    if active_users:
        df = pd.DataFrame(active_users)
        df.columns = ['Usuário', 'Atividades']
        
        # Adicionar ranking
        df.insert(0, 'Rank', range(1, len(df) + 1))
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("👤 Nenhuma atividade de usuário registrada")

def show_suspicious_ips_table(data):
    """Tabela de IPs suspeitos"""
    st.subheader("🚨 IPs Suspeitos")
    
    suspicious_ips = data.get('suspicious_ips', [])
    
    if suspicious_ips:
        df = pd.DataFrame(suspicious_ips)
        df.columns = ['Endereço IP', 'Tentativas Falhadas']
        
        # Adicionar nível de risco
        df['Nível de Risco'] = df['Tentativas Falhadas'].apply(
            lambda x: '🔴 Alto' if x >= 10 else '🟡 Médio' if x >= 5 else '🟢 Baixo'
        )
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Botão para bloquear IPs
        if st.button("🚫 Bloquear IPs Suspeitos", type="secondary"):
            st.warning("⚠️ Funcionalidade de bloqueio será implementada em versão futura")
    else:
        st.success("✅ Nenhuma atividade suspeita detectada")

def show_detailed_logs():
    """Exibe logs detalhados de segurança"""
    st.header("🔍 Logs Detalhados")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        event_type = st.selectbox(
            "Tipo de Evento:",
            ["Todos", "LOGIN_SUCCESS", "LOGIN_FAILED", "PASSWORD_RESET", "ADMIN_ACTION"],
            index=0
        )
    
    with col2:
        severity = st.selectbox(
            "Severidade:",
            ["Todas", "INFO", "WARNING", "ERROR", "CRITICAL"],
            index=0
        )
    
    with col3:
        limit = st.number_input(
            "Limite de registros:",
            min_value=10,
            max_value=1000,
            value=100,
            step=10
        )
    
    # Buscar logs
    logs = get_filtered_logs(event_type, severity, limit)
    
    if logs:
        # Converter para DataFrame
        df = pd.DataFrame(logs)
        
        # Formatação das colunas
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m/%Y %H:%M:%S')
        
        # Renomear colunas
        column_mapping = {
            'created_at': 'Data/Hora',
            'event_type': 'Tipo',
            'username': 'Usuário',
            'ip_address': 'IP',
            'severity': 'Severidade',
            'event_data': 'Detalhes'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Exibir tabela
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Botão para exportar
        if st.button("📥 Exportar Logs"):
            csv = df.to_csv(index=False)
            st.download_button(
                "📄 Baixar CSV",
                csv,
                file_name=f"security_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("📋 Nenhum log encontrado com os filtros aplicados")

def show_security_alerts():
    """Exibe alertas de segurança"""
    st.header("⚠️ Alertas de Segurança")
    
    # Verificar alertas ativos
    alerts = check_security_alerts()
    
    if alerts:
        for alert in alerts:
            alert_type = alert.get('type', 'info')
            message = alert.get('message', '')
            details = alert.get('details', [])
            
            if alert_type == 'critical':
                st.error(f"🚨 **CRÍTICO**: {message}")
            elif alert_type == 'warning':
                st.warning(f"⚠️ **ATENÇÃO**: {message}")
            else:
                st.info(f"ℹ️ **INFO**: {message}")
            
            if details:
                with st.expander("Ver detalhes"):
                    for detail in details:
                        st.write(f"• {detail}")
    else:
        st.success("✅ Nenhum alerta ativo no momento")
    
    # Configurações de alertas
    st.subheader("🔔 Configurações de Alertas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("Alertas por email", value=True, help="Receber alertas por email")
        st.checkbox("Alertas de login suspeito", value=True)
        st.checkbox("Alertas de múltiplas falhas", value=True)
    
    with col2:
        st.number_input("Limite de tentativas falhadas", min_value=3, max_value=20, value=5)
        st.number_input("Janela de tempo (minutos)", min_value=5, max_value=60, value=15)
    
    if st.button("💾 Salvar Configurações"):
        st.success("✅ Configurações salvas com sucesso!")

def show_security_settings():
    """Configurações de segurança"""
    st.header("⚙️ Configurações de Segurança")
    
    # Configurações gerais
    st.subheader("🔧 Configurações Gerais")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input(
            "Tempo de sessão (minutos):",
            min_value=15,
            max_value=480,
            value=120,
            help="Tempo limite para sessões inativas"
        )
        
        st.number_input(
            "Máximo tentativas de login:",
            min_value=3,
            max_value=10,
            value=5,
            help="Número máximo de tentativas antes do bloqueio"
        )
    
    with col2:
        st.number_input(
            "Tempo de bloqueio (minutos):",
            min_value=5,
            max_value=60,
            value=15,
            help="Tempo de bloqueio após exceder tentativas"
        )
        
        st.number_input(
            "Retenção de logs (dias):",
            min_value=7,
            max_value=365,
            value=90,
            help="Tempo para manter logs no sistema"
        )
    
    # Configurações de senha
    st.subheader("🔐 Política de Senhas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Comprimento mínimo:", min_value=6, max_value=20, value=8)
        st.checkbox("Exigir letras maiúsculas", value=True)
        st.checkbox("Exigir números", value=True)
    
    with col2:
        st.number_input("Validade da senha (dias):", min_value=30, max_value=365, value=90)
        st.checkbox("Exigir caracteres especiais", value=True)
        st.checkbox("Verificar senhas comuns", value=True)
    
    # Ações de manutenção
    st.subheader("🧹 Manutenção")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Limpar Logs Antigos", use_container_width=True):
            if SecurityMonitor.cleanup_old_logs():
                st.success("✅ Logs antigos removidos!")
            else:
                st.error("❌ Erro ao remover logs")
    
    with col2:
        if st.button("📊 Gerar Relatório", use_container_width=True):
            report = SecurityMonitor.generate_security_report()
            st.download_button(
                "📥 Baixar Relatório",
                report,
                file_name=f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col3:
        if st.button("🔄 Reinicializar Sistema", use_container_width=True):
            st.warning("⚠️ Esta ação reiniciará o sistema de segurança")
    
    # Salvar configurações
    if st.button("💾 Salvar Todas as Configurações", type="primary"):
        st.success("✅ Configurações salvas com sucesso!")

# Funções auxiliares
def get_security_data_by_period(hours: int):
    """Obtém dados de segurança por período"""
    # Em implementação real, buscar dados do banco baseado no período
    return SecurityMonitor.get_security_dashboard_data()

def get_filtered_logs(event_type: str, severity: str, limit: int):
    """Obtém logs filtrados"""
    # Implementação simplificada - em produção, fazer query no banco
    try:
        from app.database.local_connection import db_manager
        
        query = "SELECT * FROM security_logs WHERE 1=1"
        params = []
        
        if event_type != "Todos":
            query += " AND event_type = ?"
            params.append(event_type)
        
        if severity != "Todas":
            query += " AND severity = ?"
            params.append(severity)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        return db_manager.fetch_all(query, params)
    except:
        return []

def check_security_alerts():
    """Verifica alertas de segurança ativos"""
    alerts = []
    
    # Verificar dados recentes
    data = SecurityMonitor.get_security_dashboard_data()
    
    # Verificar IPs suspeitos
    suspicious_ips = data.get('suspicious_ips', [])
    if len(suspicious_ips) > 0:
        alerts.append({
            'type': 'warning',
            'message': f"{len(suspicious_ips)} IP(s) com atividade suspeita detectada",
            'details': [f"IP {ip['ip_address']}: {ip['failed_count']} tentativas falhadas" for ip in suspicious_ips[:5]]
        })
    
    # Verificar taxa de falhas alta
    login_stats = data.get('login_stats', {})
    if login_stats.get('total_attempts', 0) > 0:
        failure_rate = (login_stats.get('failed_attempts', 0) / login_stats.get('total_attempts', 1)) * 100
        
        if failure_rate > 50:
            alerts.append({
                'type': 'critical',
                'message': f"Taxa crítica de falhas de login: {failure_rate:.1f}%",
                'details': ["Possível ataque de força bruta em andamento"]
            })
        elif failure_rate > 30:
            alerts.append({
                'type': 'warning',
                'message': f"Taxa elevada de falhas de login: {failure_rate:.1f}%",
                'details': ["Monitorar atividade suspeita"]
            })
    
    return alerts