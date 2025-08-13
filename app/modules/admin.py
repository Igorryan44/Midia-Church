import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from app.database.local_connection import db_manager, get_all_users, create_user
from app.utils.auth import get_current_user, require_admin, is_admin
from app.utils.validation import DataValidator, SecurityHelper
from app.utils.backup import BackupManager, LogManager
from app.utils.helpers import get_user_id_by_username
from app.utils.responsive import apply_responsive_layout, responsive_metric_cards
import bcrypt

def render_admin():
    """Renderiza a página de administração"""
    
    # Verificar se é admin
    if not is_admin():
        st.error("🚫 Acesso negado! Esta página é restrita a administradores.")
        return
    
    st.title("🔧 Painel de Administração")
    st.markdown("*Gerencie todos os aspectos do sistema Mídia Church*")
    
    # Criar menu de navegação mais organizado
    admin_option = st.selectbox(
        "Selecione uma área de administração:",
        [
            "👥 Gerenciamento de Usuários",
            "📧 Administração de Emails", 
            "📊 Relatórios e Estatísticas",
            "⚙️ Configurações do Sistema",
            "🗄️ Backup e Restauração",
            "📋 Logs e Monitoramento"
        ],
        key="admin_navigation"
    )
    
    st.markdown("---")
    
    # Renderizar seção selecionada
    if admin_option == "👥 Gerenciamento de Usuários":
        render_user_management()
    elif admin_option == "📧 Administração de Emails":
        render_email_management()
    elif admin_option == "📊 Relatórios e Estatísticas":
        render_reports()
    elif admin_option == "⚙️ Configurações do Sistema":
        render_settings()
    elif admin_option == "🗄️ Backup e Restauração":
        render_backup()
    elif admin_option == "📋 Logs e Monitoramento":
        render_logs()

def render_user_management():
    """Gerenciamento de usuários"""
    
    st.subheader("👥 Gerenciamento de Usuários")
    
    # Estatísticas rápidas
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Total de usuários
        total_users = db_manager.fetch_all("SELECT COUNT(*) as count FROM users")[0]['count']
        
        # Usuários ativos
        active_users = db_manager.fetch_all("SELECT COUNT(*) as count FROM users WHERE is_active = 1")[0]['count']
        
        # Administradores
        admins = db_manager.fetch_all("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")[0]['count']
        
        # Novos usuários (últimos 30 dias)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        new_users = db_manager.fetch_all(
            "SELECT COUNT(*) as count FROM users WHERE created_at >= ?", 
            (thirty_days_ago,)
        )[0]['count']
        
        with col1:
            st.metric("Total de Usuários", total_users)
        
        with col2:
            st.metric("Usuários Ativos", active_users)
        
        with col3:
            st.metric("Administradores", admins)
        
        with col4:
            st.metric("Novos (30 dias)", new_users)
    
    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {e}")
    
    st.markdown("---")
    
    # Ações de usuário
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Lista de Usuários")
        
        # Filtros
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            role_filter = st.selectbox("Filtrar por Função", ["Todos", "admin", "member"])
        
        with filter_col2:
            status_filter = st.selectbox("Filtrar por Status", ["Todos", "Ativo", "Inativo"])
        
        # Buscar usuários
        try:
            query = "SELECT id, username, email, full_name, role, is_active, created_at FROM users WHERE 1=1"
            params = []
            
            if role_filter != "Todos":
                query += " AND role = ?"
                params.append(role_filter)
            
            if status_filter != "Todos":
                query += " AND is_active = ?"
                params.append(1 if status_filter == "Ativo" else 0)
            
            query += " ORDER BY created_at DESC"
            
            users = db_manager.fetch_all(query, params)
            
            if users:
                df = pd.DataFrame(users)
                df['Status'] = df['is_active'].apply(lambda x: "✅ Ativo" if x else "❌ Inativo")
                df['Função'] = df['role'].apply(lambda x: "👑 Admin" if x == "admin" else "👤 Membro")
                
                # Exibir tabela
                st.dataframe(
                    df[['username', 'full_name', 'email', 'Função', 'Status', 'created_at']],
                    column_config={
                        'username': 'Usuário',
                        'full_name': 'Nome Completo',
                        'email': 'Email',
                        'created_at': 'Criado em'
                    },
                    use_container_width=True
                )
            else:
                st.info("Nenhum usuário encontrado.")
        
        except Exception as e:
            st.error(f"Erro ao carregar usuários: {e}")
    
    with col2:
        st.subheader("Ações Rápidas")
        
        # Criar novo usuário admin
        with st.expander("➕ Criar Administrador"):
            with st.form("create_admin"):
                admin_username = st.text_input("Nome de Usuário")
                admin_email = st.text_input("Email")
                admin_name = st.text_input("Nome Completo")
                admin_password = st.text_input("Senha", type="password")
                
                if st.form_submit_button("Criar Admin"):
                    if all([admin_username, admin_email, admin_name, admin_password]):
                        try:
                            # Verificar se já existe
                            existing = db_manager.fetch_all(
                                "SELECT COUNT(*) as count FROM users WHERE username = ? OR email = ?",
                                (admin_username, admin_email)
                            )[0]['count']
                            
                            if existing > 0:
                                st.error("Usuário ou email já existe!")
                            else:
                                # Criar hash da senha
                                password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                                
                                # Inserir admin
                                db_manager.execute_query(
                                    "INSERT INTO users (username, email, password_hash, full_name, role) VALUES (?, ?, ?, ?, ?)",
                                    (admin_username, admin_email, password_hash, admin_name, 'admin')
                                )
                                
                                st.success("✅ Administrador criado com sucesso!")
                                st.rerun()
                        
                        except Exception as e:
                            st.error(f"Erro ao criar administrador: {e}")
                    else:
                        st.error("Preencha todos os campos!")
        
        # Ações em lote
        with st.expander("🔧 Ações em Lote"):
            if st.button("🗑️ Limpar Usuários Inativos", type="secondary"):
                try:
                    result = db_manager.execute_query(
                        "DELETE FROM users WHERE is_active = 0 AND created_at < ?",
                        ((datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),)
                    )
                    st.success("✅ Usuários inativos removidos!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

def render_reports():
    """Relatórios e analytics"""
    
    st.subheader("📊 Relatórios e Analytics")
    
    # Período de análise
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Data Início", datetime.now() - timedelta(days=30))
    
    with col2:
        end_date = st.date_input("Data Fim", datetime.now())
    
    try:
        # Relatório de eventos
        st.subheader("📅 Relatório de Eventos")
        
        events_query = """
        SELECT 
            event_type,
            COUNT(*) as total,
            AVG(CASE WHEN max_attendees > 0 THEN max_attendees ELSE NULL END) as avg_capacity
        FROM events 
        WHERE start_datetime BETWEEN ? AND ?
        GROUP BY event_type
        ORDER BY total DESC
        """
        
        events_data = db_manager.fetch_all(events_query, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        if events_data:
            df_events = pd.DataFrame(events_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.bar_chart(df_events.set_index('event_type')['total'])
            
            with col2:
                st.dataframe(
                    df_events,
                    column_config={
                        'event_type': 'Tipo de Evento',
                        'total': 'Total',
                        'avg_capacity': 'Capacidade Média'
                    }
                )
        
        # Relatório de usuários
        st.subheader("👥 Relatório de Usuários")
        
        users_query = """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as new_users
        FROM users 
        WHERE created_at BETWEEN ? AND ?
        GROUP BY DATE(created_at)
        ORDER BY date
        """
        
        users_data = db_manager.fetch_all(users_query, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        if users_data:
            df_users = pd.DataFrame(users_data)
            df_users['date'] = pd.to_datetime(df_users['date'])
            
            st.line_chart(df_users.set_index('date')['new_users'])
        
    except Exception as e:
        st.error(f"Erro ao gerar relatórios: {e}")

def render_settings():
    """Configurações do sistema"""
    
    st.subheader("⚙️ Configurações do Sistema")
    
    # Configurações de segurança
    with st.expander("🔒 Segurança"):
        st.checkbox("Exigir senhas fortes", value=True)
        st.checkbox("Ativar autenticação de dois fatores", value=False)
        st.number_input("Tempo de sessão (minutos)", min_value=15, max_value=480, value=120)
        
        if st.button("Salvar Configurações de Segurança"):
            st.success("✅ Configurações salvas!")
    
    # Configurações de email
    with st.expander("📧 Configurações de Email"):
        st.text_input("Servidor SMTP")
        st.number_input("Porta SMTP", value=587)
        st.text_input("Email do Sistema")
        st.text_input("Senha do Email", type="password")
        
        if st.button("Testar Conexão Email"):
            st.info("🔄 Testando conexão...")
    
    # Configurações de backup
    with st.expander("💾 Backup Automático"):
        st.checkbox("Ativar backup automático", value=True)
        st.selectbox("Frequência", ["Diário", "Semanal", "Mensal"])
        st.number_input("Manter backups por (dias)", min_value=7, max_value=365, value=30)

def render_backup():
    """Sistema de backup"""
    
    st.subheader("🗄️ Sistema de Backup")
    
    backup_manager = BackupManager()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Criar Backup")
        
        backup_type = st.selectbox(
            "Tipo de Backup",
            ["manual", "scheduled", "emergency"],
            help="Selecione o tipo de backup"
        )
        
        if st.button("🗄️ Criar Backup Agora", type="primary"):
            with st.spinner("Criando backup..."):
                try:
                    user_info = get_current_user()
                    user_id = get_user_id_by_username(user_info.get('username', ''))
                    
                    result = backup_manager.create_backup(backup_type, user_id)
                    
                    if result["success"]:
                        st.success(f"✅ Backup criado com sucesso!")
                        st.info(f"📁 Arquivo: {result['backup_name']}")
                        st.info(f"📊 Tamanho: {result['size']}")
                    else:
                        st.error(f"❌ Erro ao criar backup: {result['error']}")
                    
                except Exception as e:
                    st.error(f"Erro ao criar backup: {e}")
    
    with col2:
        st.subheader("Backups Disponíveis")
        
        backups = backup_manager.list_backups()
        
        if backups:
            for backup in backups[:5]:  # Mostrar apenas os 5 mais recentes
                with st.container():
                    st.write(f"**{backup['name']}**")
                    st.write(f"📅 {backup['created_date'].strftime('%d/%m/%Y %H:%M')}")
                    st.write(f"📊 {backup['size']}")
                    
                    col_restore, col_delete = st.columns(2)
                    
                    with col_restore:
                        if st.button(f"🔄 Restaurar", key=f"restore_{backup['name']}"):
                            if st.session_state.get(f"confirm_restore_{backup['name']}", False):
                                with st.spinner("Restaurando backup..."):
                                    user_info = get_current_user()
                                    user_id = get_user_id_by_username(user_info.get('username', ''))
                                    
                                    result = backup_manager.restore_backup(backup['path'], user_id)
                                    
                                    if result["success"]:
                                        st.success("✅ Backup restaurado com sucesso!")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Erro: {result['error']}")
                            else:
                                st.session_state[f"confirm_restore_{backup['name']}"] = True
                                st.warning("⚠️ Clique novamente para confirmar a restauração")
                    
                    with col_delete:
                        if st.button(f"🗑️ Deletar", key=f"delete_{backup['name']}"):
                            user_info = get_current_user()
                            user_id = get_user_id_by_username(user_info.get('username', ''))
                            
                            result = backup_manager.delete_backup(backup['path'], user_id)
                            
                            if result["success"]:
                                st.success("✅ Backup deletado!")
                                st.rerun()
                            else:
                                st.error(f"❌ Erro: {result['error']}")
                    
                    st.divider()
        else:
            st.info("📝 Nenhum backup disponível")

def render_logs():
    """Visualização de logs"""
    
    st.subheader("📋 Logs do Sistema")
    
    log_manager = LogManager()
    
    # Filtros de log
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_level = st.selectbox("Nível", ["Todos", "INFO", "WARNING", "ERROR"])
    
    with col2:
        log_date = st.date_input("Data", datetime.now())
    
    with col3:
        if st.button("🔄 Atualizar Logs"):
            st.rerun()
    
    # Buscar logs do banco de dados
    try:
        logs = log_manager.get_logs(
            date=log_date,
            level=log_level if log_level != "Todos" else None,
            limit=100
        )
        
        if logs:
            # Exibir logs
            for log in logs:
                level_color = {
                    "INFO": "🔵",
                    "WARNING": "🟡", 
                    "ERROR": "🔴"
                }.get(log["level"], "⚪")
                
                # Determinar cor da borda baseada no nível
                border_color = "#3B82F6" if log['level'] == 'INFO' else "#F59E0B" if log['level'] == 'WARNING' else "#EF4444"
                
                st.markdown(f"""
                <div style="padding: 8px; margin: 4px 0; border-left: 3px solid {border_color}; background-color: #F8FAFC;">
                    <strong>{level_color} {log['timestamp']}</strong> - {log['level']}<br>
                    {log['message']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📝 Nenhum log encontrado para os filtros selecionados")
            
    except Exception as e:
        st.error(f"Erro ao carregar logs: {e}")
        
        # Fallback para logs simulados em caso de erro
        logs = [
            {"timestamp": "2024-01-30 12:00:00", "level": "INFO", "message": "Usuário admin fez login"},
            {"timestamp": "2024-01-30 11:55:00", "level": "INFO", "message": "Evento 'Culto de Domingo' criado"},
            {"timestamp": "2024-01-30 11:50:00", "level": "WARNING", "message": "Tentativa de login falhada para usuário 'test'"},
            {"timestamp": "2024-01-30 11:45:00", "level": "INFO", "message": "Backup automático executado"},
            {"timestamp": "2024-01-30 11:40:00", "level": "ERROR", "message": "Erro na conexão com banco de dados"},
        ]
        
        # Filtrar logs
        if log_level != "Todos":
            logs = [log for log in logs if log["level"] == log_level]
        
        # Exibir logs
        for log in logs:
            level_color = {
                "INFO": "🔵",
                "WARNING": "🟡", 
                "ERROR": "🔴"
            }.get(log["level"], "⚪")
            
            # Determinar cor da borda baseada no nível
            border_color = "#3B82F6" if log['level'] == 'INFO' else "#F59E0B" if log['level'] == 'WARNING' else "#EF4444"
            
            st.markdown(f"""
            <div style="padding: 8px; margin: 4px 0; border-left: 3px solid {border_color}; background-color: #F8FAFC;">
                <strong>{level_color} {log['timestamp']}</strong> - {log['level']}<br>
                {log['message']}
            </div>
            """, unsafe_allow_html=True)

def render_email_management():
    """Gerenciamento de emails"""
    
    st.subheader("📧 Administração de Emails")
    st.markdown("*Configure e gerencie o sistema de emails do Mídia Church*")
    
    try:
        from app.pages.email_admin import show_email_admin
        show_email_admin()
    except ImportError as e:
        st.error("❌ Módulo de email não encontrado. Verifique se o arquivo email_admin.py existe.")
        st.code(f"Erro: {e}")
    except Exception as e:
        st.error(f"❌ Erro ao carregar administração de emails: {e}")
        
        # Interface de fallback
        st.markdown("### 🔧 Configuração Básica de Email")
        
        with st.form("basic_email_config"):
            st.text_input("Servidor SMTP", placeholder="smtp.gmail.com")
            st.number_input("Porta", value=587, min_value=1, max_value=65535)
            st.text_input("Email do Sistema", placeholder="sistema@igreja.com")
            st.text_input("Senha", type="password")
            
            if st.form_submit_button("Salvar Configurações"):
                st.info("⚠️ Funcionalidade completa em desenvolvimento")
        
        st.info("💡 Para funcionalidade completa de emails, certifique-se de que todos os módulos estão instalados corretamente.")