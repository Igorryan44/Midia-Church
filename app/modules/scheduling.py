import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from app.database.local_connection import db_manager, get_events, create_event, get_all_users
from app.utils.auth import get_current_user

def render_scheduling():
    """Renderiza o módulo de agendamento e rotinas"""
    
    st.title("⏰ Agendamento e Rotinas")
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3 = st.tabs(["📋 Rotinas", "➕ Nova Rotina", "🔔 Notificações"])
    
    with tab1:
        render_routines_list()
    
    with tab2:
        render_new_routine_form()
    
    with tab3:
        render_notifications_settings()

def render_routines_list():
    """Renderiza a lista de rotinas"""
    
    st.subheader("📋 Lista de Rotinas")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_frequency = st.selectbox(
            "Frequência",
            options=["Todas", "Diária", "Semanal", "Mensal", "Anual"]
        )
    
    with col2:
        filter_status = st.selectbox(
            "Status",
            options=["Todas", "Pendentes", "Concluídas"]
        )
    
    with col3:
        show_assigned = st.checkbox("Apenas minhas tarefas")
    
    # Buscar rotinas
    routines = get_filtered_routines(filter_frequency, filter_status, show_assigned)
    
    if routines:
        for routine in routines:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    status_icon = "✅" if routine['completed'] else "⏳"
                    st.markdown(f"{status_icon} **{routine['title']}**")
                    st.caption(f"{routine['description'] or 'Sem descrição'}")
                
                with col2:
                    frequency_emoji = get_frequency_emoji(routine['frequency'])
                    st.markdown(f"{frequency_emoji} {routine['frequency']}")
                
                with col3:
                    if routine['due_date']:
                        due_date = datetime.fromisoformat(routine['due_date']).date()
                        st.markdown(f"📅 {due_date.strftime('%d/%m/%Y')}")
                    else:
                        st.markdown("📅 Sem prazo")
                
                with col4:
                    if not routine['completed']:
                        if st.button("✅ Concluir", key=f"complete_{routine['id']}"):
                            complete_routine(routine['id'])
                            st.success("Rotina concluída!")
                            st.rerun()
                    else:
                        if st.button("🔄 Reabrir", key=f"reopen_{routine['id']}"):
                            reopen_routine(routine['id'])
                            st.success("Rotina reaberta!")
                            st.rerun()
                
                st.divider()
    else:
        st.info("Nenhuma rotina encontrada com os filtros selecionados.")

def render_new_routine_form():
    """Renderiza o formulário para criar nova rotina"""
    
    st.subheader("➕ Criar Nova Rotina")
    
    with st.form("new_routine_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Título da Rotina *", placeholder="Ex: Preparar material do culto")
            frequency = st.selectbox(
                "Frequência *",
                options=["Diária", "Semanal", "Mensal", "Anual"]
            )
            due_date = st.date_input("Data de Vencimento", value=None)
        
        with col2:
            # Buscar usuários para atribuição
            users = get_all_users()
            user_options = {user['full_name']: user['id'] for user in users}
            
            assigned_to_name = st.selectbox(
                "Atribuir para",
                options=["Ninguém"] + list(user_options.keys())
            )
            
            priority = st.selectbox(
                "Prioridade",
                options=["Baixa", "Média", "Alta"]
            )
        
        description = st.text_area("Descrição", placeholder="Descreva a rotina...")
        
        submitted = st.form_submit_button("🎯 Criar Rotina", use_container_width=True)
        
        if submitted:
            if title and frequency:
                # Obter ID do usuário atribuído
                assigned_to = user_options.get(assigned_to_name) if assigned_to_name != "Ninguém" else None
                
                # Obter ID do usuário atual
                user_info = get_current_user()
                created_by = get_user_id(user_info['username'])
                
                success = create_routine(
                    title=title,
                    description=description,
                    frequency=frequency,
                    assigned_to=assigned_to,
                    due_date=due_date,
                    created_by=created_by
                )
                
                if success:
                    st.success("✅ Rotina criada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao criar rotina. Tente novamente.")
            else:
                st.error("⚠️ Preencha todos os campos obrigatórios!")

def render_notifications_settings():
    """Renderiza as configurações de notificações"""
    
    st.subheader("🔔 Configurações de Notificações")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📧 Notificações por Email")
        
        email_events = st.checkbox("Novos eventos", value=True)
        email_routines = st.checkbox("Rotinas vencendo", value=True)
        email_announcements = st.checkbox("Anúncios importantes", value=True)
        
        email_frequency = st.selectbox(
            "Frequência de resumo",
            options=["Imediato", "Diário", "Semanal"]
        )
    
    with col2:
        st.markdown("### 🔔 Notificações no Sistema")
        
        system_events = st.checkbox("Eventos próximos", value=True)
        system_routines = st.checkbox("Tarefas pendentes", value=True)
        system_messages = st.checkbox("Novas mensagens", value=True)
        
        reminder_time = st.selectbox(
            "Lembrete de eventos",
            options=["15 minutos antes", "30 minutos antes", "1 hora antes", "1 dia antes"]
        )
    
    if st.button("💾 Salvar Configurações", use_container_width=True):
        # Aqui você salvaria as configurações no banco de dados
        st.success("✅ Configurações salvas com sucesso!")
    
    st.divider()
    
    # Próximas notificações
    st.subheader("📬 Próximas Notificações")
    
    upcoming_notifications = get_upcoming_notifications()
    
    if upcoming_notifications:
        for notification in upcoming_notifications:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    notification_icon = get_notification_icon(notification['type'])
                    st.markdown(f"{notification_icon} **{notification['title']}**")
                    st.caption(notification['description'])
                
                with col2:
                    st.markdown(f"📅 {notification['date']}")
                
                with col3:
                    st.markdown(f"⏰ {notification['time']}")
                
                st.divider()
    else:
        st.info("Nenhuma notificação programada.")

def get_frequency_emoji(frequency):
    """Retorna emoji para a frequência"""
    emojis = {
        "Diária": "📅",
        "Semanal": "📆",
        "Mensal": "🗓️",
        "Anual": "📋"
    }
    return emojis.get(frequency, "📋")

def get_notification_icon(notification_type):
    """Retorna ícone para o tipo de notificação"""
    icons = {
        "event": "📅",
        "routine": "⏰",
        "announcement": "📢",
        "message": "💬"
    }
    return icons.get(notification_type, "🔔")

def get_filtered_routines(filter_frequency, filter_status, show_assigned):
    """Busca rotinas com filtros aplicados"""
    try:
        query = "SELECT r.*, u.full_name as assigned_name FROM routines r LEFT JOIN users u ON r.assigned_to = u.id WHERE r.is_active = 1"
        params = []
        
        # Filtro por frequência
        if filter_frequency != "Todas":
            query += " AND r.frequency = ?"
            params.append(filter_frequency)
        
        # Filtro por status
        if filter_status == "Pendentes":
            query += " AND r.completed = 0"
        elif filter_status == "Concluídas":
            query += " AND r.completed = 1"
        
        # Filtro por usuário atual
        if show_assigned:
            user_info = get_current_user()
            user_id = get_user_id(user_info['username'])
            query += " AND r.assigned_to = ?"
            params.append(user_id)
        
        query += " ORDER BY r.due_date ASC, r.created_at DESC"
        
        return db_manager.fetch_all(query, params)
    except:
        return []

def get_all_users():
    """Busca todos os usuários ativos"""
    try:
        query = "SELECT id, full_name FROM users WHERE is_active = 1 ORDER BY full_name"
        return db_manager.fetch_all(query)
    except:
        return []

def create_routine(title, description, frequency, assigned_to, due_date, created_by):
    """Cria uma nova rotina"""
    try:
        query = """
        INSERT INTO routines (title, description, frequency, assigned_to, due_date, created_by)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (title, description, frequency, assigned_to, due_date, created_by)
        db_manager.execute_query(query, params)
        return True
    except Exception as e:
        st.error(f"Erro ao criar rotina: {e}")
        return False

def complete_routine(routine_id):
    """Marca uma rotina como concluída"""
    try:
        query = "UPDATE routines SET completed = 1 WHERE id = ?"
        db_manager.execute_query(query, (routine_id,))
        return True
    except:
        return False

def reopen_routine(routine_id):
    """Reabre uma rotina concluída"""
    try:
        query = "UPDATE routines SET completed = 0 WHERE id = ?"
        db_manager.execute_query(query, (routine_id,))
        return True
    except:
        return False

def get_user_id(username):
    """Busca o ID do usuário pelo username"""
    try:
        query = "SELECT id FROM users WHERE username = ?"
        result = db_manager.fetch_all(query, (username,))
        return result[0]['id'] if result else None
    except:
        return None

def get_upcoming_notifications():
    """Retorna próximas notificações"""
    # Simulação de notificações
    notifications = [
        {
            'type': 'event',
            'title': 'Culto de Domingo',
            'description': 'Lembrete: Culto começa em 1 hora',
            'date': '15/12/2024',
            'time': '09:00'
        },
        {
            'type': 'routine',
            'title': 'Preparar material',
            'description': 'Tarefa vence hoje',
            'date': '15/12/2024',
            'time': '18:00'
        }
    ]
    return notifications