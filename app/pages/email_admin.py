import streamlit as st
import json
from app.utils.email_service import EmailService, send_notification_email
from app.utils.auth import require_admin
from app.database.local_connection import db_manager, get_all_users

def show_email_admin():
    """Interface de administração de emails"""
    
    require_admin()
    
    st.title("📧 Administração de Emails")
    
    email_service = EmailService()
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚙️ Configurações", 
        "📝 Templates", 
        "📤 Enviar Email", 
        "📊 Estatísticas",
        "📋 Logs"
    ])
    
    with tab1:
        show_email_config(email_service)
    
    with tab2:
        show_email_templates(email_service)
    
    with tab3:
        show_send_email(email_service)
    
    with tab4:
        show_email_stats(email_service)
    
    with tab5:
        show_email_logs()

def show_email_config(email_service):
    """Mostra configurações de email"""
    
    st.header("Configurações do Servidor de Email")
    
    config = email_service.config
    
    with st.form("email_config_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Servidor SMTP")
            smtp_server = st.text_input("Servidor SMTP", value=config.get('smtp_server', ''))
            smtp_port = st.number_input("Porta SMTP", min_value=1, max_value=65535, value=config.get('smtp_port', 587))
            use_tls = st.checkbox("Usar TLS/SSL", value=config.get('use_tls', True))
            
            st.subheader("Autenticação")
            username = st.text_input("Usuário/Email", value=config.get('username', ''))
            password = st.text_input("Senha", type="password", value=config.get('password', ''))
        
        with col2:
            st.subheader("Remetente")
            from_name = st.text_input("Nome do Remetente", value=config.get('from_name', 'Mídia Church'))
            from_email = st.text_input("Email do Remetente", value=config.get('from_email', ''))
            
            st.subheader("Limites")
            max_daily_emails = st.number_input("Máximo de emails por dia", min_value=1, max_value=1000, value=config.get('max_daily_emails', 100))
            enabled = st.checkbox("Habilitar serviço de email", value=config.get('enabled', False))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("💾 Salvar Configurações", use_container_width=True):
                new_config = {
                    'smtp_server': smtp_server,
                    'smtp_port': smtp_port,
                    'use_tls': use_tls,
                    'username': username,
                    'password': password,
                    'from_name': from_name,
                    'from_email': from_email,
                    'max_daily_emails': max_daily_emails,
                    'enabled': enabled,
                    'templates': config.get('templates', {})
                }
                
                if email_service.save_email_config(new_config):
                    st.success("✅ Configurações salvas com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar configurações!")
        
        with col2:
            if st.form_submit_button("🔍 Testar Conexão", use_container_width=True):
                if enabled:
                    test_config = {
                        'smtp_server': smtp_server,
                        'smtp_port': smtp_port,
                        'use_tls': use_tls,
                        'username': username,
                        'password': password,
                        'enabled': True
                    }
                    
                    # Criar instância temporária para teste
                    temp_service = EmailService()
                    temp_service.config = test_config
                    
                    result = temp_service.test_connection()
                    
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                    else:
                        st.error(f"❌ {result['message']}")
                else:
                    st.warning("⚠️ Habilite o serviço de email primeiro!")

def show_email_templates(email_service):
    """Mostra gerenciamento de templates"""
    
    st.header("Templates de Email")
    
    templates = email_service.get_email_templates()
    
    # Criar novo template
    with st.expander("➕ Criar Novo Template"):
        with st.form("new_template_form"):
            template_name = st.text_input("Nome do Template")
            template_subject = st.text_input("Assunto")
            template_body = st.text_area("Corpo do Email (Texto)", height=100)
            template_html = st.text_area("Corpo do Email (HTML)", height=150)
            
            st.info("💡 Use {variavel} para inserir variáveis dinâmicas (ex: {username}, {full_name})")
            
            if st.form_submit_button("💾 Salvar Template"):
                if template_name and template_subject:
                    template_data = {
                        'subject': template_subject,
                        'body': template_body,
                        'html_body': template_html
                    }
                    
                    if email_service.save_email_template(template_name, template_data):
                        st.success(f"✅ Template '{template_name}' salvo com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar template!")
                else:
                    st.error("❌ Nome e assunto são obrigatórios!")
    
    # Listar templates existentes
    if templates:
        st.subheader("Templates Existentes")
        
        for name, template in templates.items():
            with st.expander(f"📄 {name}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Assunto:** {template.get('subject', 'N/A')}")
                    st.write(f"**Corpo:** {template.get('body', 'N/A')[:100]}...")
                    if template.get('html_body'):
                        st.write("**HTML:** Sim")
                
                with col2:
                    if st.button(f"🗑️ Excluir", key=f"delete_{name}"):
                        if email_service.delete_email_template(name):
                            st.success(f"✅ Template '{name}' removido!")
                            st.rerun()
                        else:
                            st.error("❌ Erro ao remover template!")
    else:
        st.info("📝 Nenhum template criado ainda.")

def show_send_email(email_service):
    """Interface para envio de emails"""
    
    st.header("Enviar Email")
    
    if not email_service.config.get('enabled', False):
        st.warning("⚠️ Serviço de email não está habilitado. Configure primeiro na aba 'Configurações'.")
        return
    
    # Buscar usuários para seleção
    try:
        users_query = "SELECT username, email, full_name FROM users WHERE is_active = 1 AND email IS NOT NULL AND email != ''"
        users_result = db_manager.fetch_all(users_query)
        users = {f"{user['full_name']} ({user['username']})": user['email'] for user in users_result}
    except:
        users = {}
    
    with st.form("send_email_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Destinatários")
            
            # Opções de destinatários
            recipient_type = st.radio(
                "Tipo de destinatário:",
                ["Usuários específicos", "Todos os usuários", "Emails personalizados"]
            )
            
            recipients = []
            if recipient_type == "Usuários específicos":
                if users:
                    selected_users = st.multiselect("Selecionar usuários:", list(users.keys()))
                    recipients = [users[user] for user in selected_users]
                else:
                    st.warning("Nenhum usuário com email encontrado")
            
            elif recipient_type == "Todos os usuários":
                recipients = list(users.values()) if users else []
                st.info(f"📧 {len(recipients)} usuários serão incluídos")
            
            elif recipient_type == "Emails personalizados":
                custom_emails = st.text_area(
                    "Emails (um por linha):",
                    placeholder="email1@exemplo.com\nemail2@exemplo.com"
                )
                if custom_emails:
                    recipients = [email.strip() for email in custom_emails.split('\n') if email.strip()]
        
        with col2:
            st.subheader("Conteúdo")
            
            # Usar template ou criar novo
            use_template = st.checkbox("Usar template existente")
            
            if use_template:
                templates = email_service.get_email_templates()
                if templates:
                    selected_template = st.selectbox("Selecionar template:", list(templates.keys()))
                    if selected_template:
                        template = templates[selected_template]
                        subject = st.text_input("Assunto:", value=template.get('subject', ''))
                        body = st.text_area("Corpo do email:", value=template.get('body', ''), height=150)
                        html_body = st.text_area("HTML (opcional):", value=template.get('html_body', ''), height=100)
                    else:
                        subject = body = html_body = ""
                else:
                    st.warning("Nenhum template disponível")
                    subject = body = html_body = ""
            else:
                subject = st.text_input("Assunto:")
                body = st.text_area("Corpo do email:", height=150)
                html_body = st.text_area("HTML (opcional):", height=100)
            
            # Variáveis disponíveis
            st.info("💡 Variáveis: {username}, {full_name}, {email}")
        
        # Botões de ação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            send_email = st.form_submit_button("📤 Enviar Email", use_container_width=True)
        
        with col2:
            preview_email = st.form_submit_button("👁️ Visualizar", use_container_width=True)
        
        with col3:
            save_draft = st.form_submit_button("💾 Salvar Rascunho", use_container_width=True)
        
        if send_email:
            if not recipients:
                st.error("❌ Selecione pelo menos um destinatário!")
            elif not subject or not body:
                st.error("❌ Assunto e corpo são obrigatórios!")
            else:
                # Enviar emails
                success_count = 0
                error_count = 0
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, recipient in enumerate(recipients):
                    try:
                        # Substituir variáveis se for usuário do sistema
                        email_subject = subject
                        email_body = body
                        email_html = html_body
                        
                        # Buscar dados do usuário se for email do sistema
                        user_data = None
                        if recipient in users.values():
                            for user_name, user_email in users.items():
                                if user_email == recipient:
                                    # Extrair dados do usuário
                                    username = user_name.split('(')[1].split(')')[0] if '(' in user_name else user_name
                                    full_name = user_name.split('(')[0].strip() if '(' in user_name else user_name
                                    user_data = {
                                        'username': username,
                                        'full_name': full_name,
                                        'email': recipient
                                    }
                                    break
                        
                        if user_data:
                            email_subject = email_subject.format(**user_data)
                            email_body = email_body.format(**user_data)
                            if email_html:
                                email_html = email_html.format(**user_data)
                        
                        # Enviar email
                        result = email_service.send_email(
                            to_email=recipient,
                            subject=email_subject,
                            body=email_body,
                            html_body=email_html if email_html else None
                        )
                        
                        if result['success']:
                            success_count += 1
                        else:
                            error_count += 1
                            st.error(f"Erro ao enviar para {recipient}: {result['message']}")
                    
                    except Exception as e:
                        error_count += 1
                        st.error(f"Erro ao enviar para {recipient}: {str(e)}")
                    
                    # Atualizar progresso
                    progress = (i + 1) / len(recipients)
                    progress_bar.progress(progress)
                    status_text.text(f"Enviando... {i + 1}/{len(recipients)}")
                
                # Resultado final
                if success_count > 0:
                    st.success(f"✅ {success_count} emails enviados com sucesso!")
                if error_count > 0:
                    st.error(f"❌ {error_count} emails falharam!")
        
        elif preview_email:
            if subject and body:
                st.subheader("👁️ Visualização do Email")
                st.write(f"**Assunto:** {subject}")
                st.write(f"**Destinatários:** {len(recipients)} emails")
                st.write("**Corpo:**")
                st.write(body)
                if html_body:
                    st.write("**HTML:**")
                    st.code(html_body, language='html')
        
        elif save_draft:
            st.info("💾 Funcionalidade de rascunho será implementada em breve")

def show_email_stats(email_service):
    """Mostra estatísticas de email"""
    
    st.header("📊 Estatísticas de Email")
    
    try:
        # Buscar estatísticas do banco de dados
        
        # Estatísticas básicas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            try:
                total_sent = db_manager.fetch_all(
                    "SELECT COUNT(*) as count FROM email_logs WHERE status = 'sent'"
                )[0]['count']
            except:
                total_sent = 0
            st.metric("📤 Total Enviados", total_sent)
        
        with col2:
            try:
                total_failed = db_manager.fetch_all(
                    "SELECT COUNT(*) as count FROM email_logs WHERE status = 'failed'"
                )[0]['count']
            except:
                total_failed = 0
            st.metric("❌ Falharam", total_failed)
        
        with col3:
            try:
                today_sent = db_manager.fetch_all(
                    "SELECT COUNT(*) as count FROM email_logs WHERE status = 'sent' AND DATE(created_at) = DATE('now')"
                )[0]['count']
            except:
                today_sent = 0
            st.metric("📅 Hoje", today_sent)
        
        with col4:
            success_rate = (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0
            st.metric("📈 Taxa de Sucesso", f"{success_rate:.1f}%")
        
        # Gráfico de emails por dia (últimos 30 dias)
        try:
            daily_stats = db_manager.fetch_all("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM email_logs 
                WHERE created_at >= DATE('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            
            if daily_stats:
                import pandas as pd
                import plotly.express as px
                
                df = pd.DataFrame(daily_stats)
                
                fig = px.line(df, x='date', y=['sent', 'failed'], 
                             title="Emails por Dia (Últimos 30 dias)",
                             labels={'value': 'Quantidade', 'date': 'Data'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 Sem dados suficientes para gráficos")
        
        except Exception as e:
            st.warning(f"⚠️ Erro ao carregar gráficos: {str(e)}")
        
        # Top destinatários
        try:
            top_recipients = db_manager.fetch_all("""
                SELECT 
                    to_email,
                    COUNT(*) as count,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent
                FROM email_logs 
                GROUP BY to_email
                ORDER BY count DESC
                LIMIT 10
            """)
            
            if top_recipients:
                st.subheader("🏆 Top Destinatários")
                for recipient in top_recipients:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(recipient['to_email'])
                    with col2:
                        st.write(f"Total: {recipient['count']}")
                    with col3:
                        st.write(f"Enviados: {recipient['sent']}")
        
        except Exception as e:
            st.warning(f"⚠️ Erro ao carregar top destinatários: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar estatísticas: {str(e)}")

def show_email_logs():
    """Mostra logs de email"""
    
    st.header("📋 Logs de Email")
    
    try:
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Status:",
                ["Todos", "sent", "failed", "pending"]
            )
        
        with col2:
            days_filter = st.selectbox(
                "Período:",
                ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Todos"]
            )
        
        with col3:
            limit = st.number_input("Limite de registros:", min_value=10, max_value=1000, value=100)
        
        # Construir query
        where_conditions = []
        
        if status_filter != "Todos":
            where_conditions.append(f"status = '{status_filter}'")
        
        if days_filter != "Todos":
            days = {"Últimos 7 dias": 7, "Últimos 30 dias": 30, "Últimos 90 dias": 90}[days_filter]
            where_conditions.append(f"created_at >= DATE('now', '-{days} days')")
        
        where_clause = " AND ".join(where_conditions)
        if where_clause:
            where_clause = "WHERE " + where_clause
        
        # Buscar logs
        logs_query = f"""
            SELECT 
                id,
                to_email,
                subject,
                status,
                error_message,
                created_at
            FROM email_logs 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit}
        """
        
        logs = db_manager.fetch_all(logs_query)
        
        if logs:
            # Exibir logs em tabela
            import pandas as pd
            
            df = pd.DataFrame(logs)
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m/%Y %H:%M')
            
            # Configurar cores por status
            def color_status(val):
                if val == 'sent':
                    return 'background-color: #d4edda'
                elif val == 'failed':
                    return 'background-color: #f8d7da'
                elif val == 'pending':
                    return 'background-color: #fff3cd'
                return ''
            
            styled_df = df.style.applymap(color_status, subset=['status'])
            st.dataframe(styled_df, use_container_width=True)
            
            # Detalhes do log selecionado
            if st.checkbox("Mostrar detalhes"):
                selected_id = st.selectbox("Selecionar log:", df['id'].tolist())
                if selected_id:
                    selected_log = next(log for log in logs if log['id'] == selected_id)
                    
                    st.subheader("Detalhes do Log")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**ID:** {selected_log['id']}")
                        st.write(f"**Para:** {selected_log['to_email']}")
                        st.write(f"**Status:** {selected_log['status']}")
                    
                    with col2:
                        st.write(f"**Assunto:** {selected_log['subject']}")
                        st.write(f"**Data:** {selected_log['created_at']}")
                        if selected_log['error_message']:
                            st.write(f"**Erro:** {selected_log['error_message']}")
        else:
            st.info("📭 Nenhum log encontrado com os filtros selecionados")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar logs: {str(e)}")

if __name__ == "__main__":
    show_email_admin()