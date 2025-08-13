import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from streamlit_calendar import calendar
from app.database.local_connection import db_manager, get_events, get_all_users
from app.utils.auth import get_current_user
from app.utils.validation import DataValidator, SecurityHelper
from app.utils.responsive import apply_responsive_layout, responsive_metric_cards
from app.modules.meeting_reports import render_meeting_reports

def render_planner():
    """Renderiza o módulo de planejamento com calendário"""
    
    st.title("📅 Planner - Calendário de Eventos")
    
    # Verificar se deve navegar para aba específica
    if 'active_tab' in st.session_state:
        active_tab_index = st.session_state.active_tab
        del st.session_state.active_tab
    else:
        active_tab_index = 0
    
    # Verificar se há evento selecionado para relatório
    if 'selected_event_for_report' in st.session_state:
        active_tab_index = 3  # Aba de relatórios
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Calendário Visual", 
        "➕ Novo Evento", 
        "📋 Lista de Eventos",
        "📝 Relatórios"
    ])
    
    # Renderizar todas as abas sempre (Streamlit gerencia a navegação automaticamente)
    with tab1:
        render_visual_calendar()
    
    with tab2:
        render_new_event_form()
    
    with tab3:
        render_events_list()
    
    with tab4:
        try:
            render_meeting_reports()
        except Exception as e:
            st.error(f"Erro ao carregar relatórios: {e}")
            st.info("Módulo de relatórios temporariamente indisponível.")

def render_visual_calendar():
    """Renderiza o calendário visual interativo"""
    
    st.subheader("📅 Calendário Interativo")
    
    try:
        # Buscar todos os eventos
        events = get_events()
        
        # Converter eventos para formato do calendário
        calendar_events = []
        for event in events:
            try:
                # Tratar diferentes tipos de dados para datetime
                start_datetime = event['start_datetime']
                end_datetime = event['end_datetime']
                
                if isinstance(start_datetime, str):
                    start_dt = datetime.fromisoformat(start_datetime.replace('Z', ''))
                elif isinstance(start_datetime, datetime):
                    start_dt = start_datetime
                else:
                    continue
                
                if isinstance(end_datetime, str):
                    end_dt = datetime.fromisoformat(end_datetime.replace('Z', ''))
                elif isinstance(end_datetime, datetime):
                    end_dt = end_datetime
                else:
                    continue
                
                # Definir cor baseada no tipo de evento
                color = get_event_color(event['event_type'])
                
                calendar_event = {
                    "title": event['title'],
                    "start": start_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                    "end": end_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                    "backgroundColor": color,
                    "borderColor": color,
                    "textColor": "#ffffff",
                    "extendedProps": {
                        "description": event['description'] or '',
                        "location": event['location'] or '',
                        "event_type": event['event_type'],
                        "id": event['id']
                    }
                }
                calendar_events.append(calendar_event)
            except Exception as e:
                st.error(f"Erro ao processar evento {event.get('title', 'Desconhecido')}: {e}")
                continue
        
        # Configurações do calendário
        calendar_options = {
            "editable": "true",
            "navLinks": "true",
            "selectable": "true",
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay"
            },
            "initialView": "dayGridMonth",
            "height": 650,
            "locale": "pt-br",
            "buttonText": {
                "today": "Hoje",
                "month": "Mês",
                "week": "Semana",
                "day": "Dia"
            },
            "slotMinTime": "06:00:00",
            "slotMaxTime": "23:00:00",
            "allDaySlot": False
        }
        
        # Renderizar calendário
        calendar_result = calendar(
            events=calendar_events,
            options=calendar_options,
            custom_css="""
            .fc-event-past {
                opacity: 0.8;
            }
            .fc-event-time {
                font-weight: bold;
            }
            .fc-event-title {
                font-weight: bold;
            }
            """,
            key="church_calendar"
        )
        
        # Processar interações do calendário
        if calendar_result.get("eventClick"):
            event_clicked = calendar_result["eventClick"]["event"]
            show_event_details(event_clicked)
        
        if calendar_result.get("dateClick"):
            date_clicked = calendar_result["dateClick"]["date"]
            st.session_state.new_event_date = datetime.fromisoformat(date_clicked.replace('Z', '')).date()
            st.info(f"📅 Data selecionada: {st.session_state.new_event_date.strftime('%d/%m/%Y')}. Vá para a aba 'Novo Evento' para criar um evento nesta data.")
    
    except Exception as e:
        st.error(f"Erro ao carregar calendário: {e}")
        st.info("Tente recarregar a página ou verifique se há eventos cadastrados.")

def show_event_details(event):
    """Exibe detalhes do evento em um modal"""
    
    with st.expander(f"📋 Detalhes: {event['title']}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Tratar conversão de datetime de forma segura
            try:
                start_str = event['start']
                end_str = event['end']
                if isinstance(start_str, str):
                    start_dt = datetime.fromisoformat(start_str.replace('Z', ''))
                    end_dt = datetime.fromisoformat(end_str.replace('Z', ''))
                else:
                    start_dt = start_str
                    end_dt = end_str
                
                st.markdown(f"**📅 Data:** {start_dt.strftime('%d/%m/%Y')}")
                st.markdown(f"**⏰ Horário:** {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}")
            except Exception as e:
                st.markdown(f"**📅 Data:** Erro ao carregar data")
                st.markdown(f"**⏰ Horário:** Erro ao carregar horário")
            
            st.markdown(f"**🏷️ Tipo:** {event['extendedProps']['event_type']}")
        
        with col2:
            if event['extendedProps']['location']:
                st.markdown(f"**📍 Local:** {event['extendedProps']['location']}")
            if event['extendedProps']['description']:
                st.markdown(f"**📝 Descrição:** {event['extendedProps']['description']}")
        
        # Botões de ação
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✏️ Editar", key=f"edit_modal_{event['extendedProps']['id']}"):
                st.session_state.editing_event = event['extendedProps']['id']
                st.rerun()
        
        with col2:
            if st.button("🗑️ Excluir", key=f"delete_modal_{event['extendedProps']['id']}"):
                if delete_event(event['extendedProps']['id']):
                    st.success("Evento excluído!")
                    st.rerun()
        
        with col3:
            if st.button("📝 Relatório", key=f"report_modal_{event['extendedProps']['id']}"):
                st.session_state.selected_event_for_report = event['extendedProps']['id']
                st.session_state.active_tab = 3  # Aba de relatórios
                st.rerun()
        
        with col4:
            if st.button("📋 Ver Lista", key=f"list_modal_{event['extendedProps']['id']}"):
                st.session_state.current_tab = 2

def render_new_event_form():
    """Renderiza o formulário para criar novo evento"""
    
    st.subheader("➕ Criar Novo Evento")
    
    # Verificar se há data selecionada do calendário
    default_date = st.session_state.get('new_event_date', datetime.now().date())
    if 'new_event_date' in st.session_state:
        st.info(f"📅 Criando evento para: {default_date.strftime('%d/%m/%Y')}")
    
    # Verificar se está editando um evento
    editing_event_id = st.session_state.get('editing_event')
    editing_event = None
    
    if editing_event_id:
        editing_event = get_event_by_id(editing_event_id)
        if editing_event:
            st.info(f"✏️ Editando evento: {editing_event['title']}")
            if st.button("❌ Cancelar Edição", key="cancel_edit_btn"):
                del st.session_state.editing_event
                st.rerun()
        else:
            st.error("Evento não encontrado!")
            del st.session_state.editing_event
            st.rerun()
            return
    
    # Pré-carregar dados se editando
    if editing_event:
        default_title = editing_event['title']
        default_type = editing_event['event_type']
        default_location = editing_event.get('location', '')
        default_description = editing_event.get('description', '')
        
        # Tratar conversão de datetime de forma segura
        try:
            start_datetime = editing_event['start_datetime']
            end_datetime = editing_event['end_datetime']
            
            if isinstance(start_datetime, str):
                start_dt = datetime.fromisoformat(start_datetime.replace('Z', ''))
            else:
                start_dt = start_datetime
                
            if isinstance(end_datetime, str):
                end_dt = datetime.fromisoformat(end_datetime.replace('Z', ''))
            else:
                end_dt = end_datetime
        except Exception as e:
            st.error(f"Erro ao carregar dados do evento: {e}")
            start_dt = datetime.now()
            end_dt = datetime.now() + timedelta(hours=2)
        
        default_date = start_dt.date()
        default_start_time = start_dt.time()
        default_end_time = end_dt.time()
        form_key = f"event_form_edit_{editing_event_id}"
    else:
        default_title = ""
        default_type = "Culto"
        default_location = ""
        default_description = ""
        default_start_time = datetime.now().replace(minute=0, second=0, microsecond=0).time()
        default_end_time = (datetime.now() + timedelta(hours=2)).replace(minute=0, second=0, microsecond=0).time()
        form_key = "event_form_new"
    
    with st.form(form_key, clear_on_submit=not editing_event):
        # Informações básicas
        st.markdown("### 📋 Informações Básicas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input(
                "Título do Evento *", 
                value=default_title,
                placeholder="Ex: Culto de Domingo",
                max_chars=200,
                key=f"title_{form_key}"
            )
            
            event_type = st.selectbox(
                "Tipo de Evento *",
                options=["Culto", "Reunião", "Celebração", "Estudo Bíblico", "Evento Especial", "Conferência", "Retiro", "Outro"],
                index=["Culto", "Reunião", "Celebração", "Estudo Bíblico", "Evento Especial", "Conferência", "Retiro", "Outro"].index(default_type) if default_type in ["Culto", "Reunião", "Celebração", "Estudo Bíblico", "Evento Especial", "Conferência", "Retiro", "Outro"] else 0,
                key=f"type_{form_key}"
            )
            
            location = st.text_input(
                "Local", 
                value=default_location,
                placeholder="Ex: Santuário Principal, Sala 1, Online",
                max_chars=255,
                key=f"location_{form_key}"
            )
        
        with col2:
            start_date = st.date_input(
                "Data de Início *", 
                value=default_date,
                key=f"start_date_{form_key}"
            )
            
            start_time = st.time_input(
                "Hora de Início *", 
                value=default_start_time,
                key=f"start_time_{form_key}"
            )
            
            end_time = st.time_input(
                "Hora de Término *", 
                value=default_end_time,
                key=f"end_time_{form_key}"
            )
        
        # Descrição
        description = st.text_area(
            "Descrição", 
            value=default_description,
            placeholder="Descreva o evento, objetivos, programação, etc...",
            max_chars=1000,
            height=100,
            key=f"description_{form_key}"
        )
        
        # Botões de ação
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button(
                "💾 Salvar Evento" if editing_event else "🎯 Criar Evento", 
                use_container_width=True
            )
        
        with col2:
            if editing_event:
                delete_clicked = st.form_submit_button("🗑️ Excluir Evento", use_container_width=True)
        
        # Processar ações do formulário
        if submitted:
            # Validação básica
            if not title or len(title.strip()) < 3:
                st.error("⚠️ Título deve ter pelo menos 3 caracteres")
            elif start_date and start_time and end_time:
                start_datetime = datetime.combine(start_date, start_time)
                end_datetime = datetime.combine(start_date, end_time)
                
                if end_datetime <= start_datetime:
                    st.error("⚠️ Hora de término deve ser posterior à hora de início")
                else:
                    # Processar envio do formulário
                    success = process_event_submission(
                        title=title,
                        description=description,
                        event_type=event_type,
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                        location=location,
                        editing_event_id=editing_event_id
                    )
                    
                    if success:
                        if editing_event:
                            st.success("✅ Evento atualizado com sucesso!")
                            del st.session_state.editing_event
                        else:
                            st.success("✅ Evento criado com sucesso!")
                            if 'new_event_date' in st.session_state:
                                del st.session_state.new_event_date
                        
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao processar evento. Tente novamente.")
        
        # Processar exclusão
        if editing_event and 'delete_clicked' in locals() and delete_clicked:
            if delete_event(editing_event_id):
                st.success("Evento excluído com sucesso!")
                del st.session_state.editing_event
                st.rerun()
            else:
                st.error("Erro ao excluir evento!")

def render_events_list():
    """Renderiza a lista de eventos"""
    
    st.subheader("📋 Lista de Eventos")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_type = st.selectbox(
            "Filtrar por Tipo",
            options=["Todos", "Culto", "Reunião", "Celebração", "Estudo Bíblico", "Evento Especial", "Outro"]
        )
    
    with col2:
        filter_period = st.selectbox(
            "Período",
            options=["Próximos 30 dias", "Este mês", "Próximo mês", "Todos"]
        )
    
    with col3:
        search_term = st.text_input("🔍 Buscar eventos", placeholder="Digite para buscar...")
    
    # Buscar eventos
    events = get_filtered_events(filter_type, filter_period, search_term)
    
    if not events:
        st.info("📅 Nenhum evento encontrado para os filtros selecionados.")
        return
    
    # Exibir eventos
    for event in events:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"### {get_event_type_emoji(event['event_type'])} {event['title']}")
                
                # Tratar conversão de datetime de forma segura
                try:
                    start_datetime = event['start_datetime']
                    end_datetime = event['end_datetime']
                    
                    if isinstance(start_datetime, str):
                        start_dt = datetime.fromisoformat(start_datetime.replace('Z', ''))
                    else:
                        start_dt = start_datetime
                        
                    if isinstance(end_datetime, str):
                        end_dt = datetime.fromisoformat(end_datetime.replace('Z', ''))
                    else:
                        end_dt = end_datetime
                    
                    st.markdown(f"📅 {start_dt.strftime('%d/%m/%Y %H:%M')} - {end_dt.strftime('%H:%M')}")
                except Exception as e:
                    st.markdown(f"📅 Erro ao carregar data/hora")
                
                if event['location']:
                    st.markdown(f"📍 {event['location']}")
                if event['description']:
                    st.markdown(f"📝 {event['description'][:100]}{'...' if len(event['description']) > 100 else ''}")
            
            with col2:
                if st.button("✏️ Editar", key=f"edit_list_{event['id']}"):
                    st.session_state.editing_event = event['id']
                    st.session_state.active_tab = 1  # Aba de novo evento
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Excluir", key=f"delete_list_{event['id']}"):
                    if delete_event(event['id']):
                        st.success("Evento excluído!")
                        st.rerun()
            
            st.divider()

# Funções auxiliares
def get_event_type_emoji(event_type):
    """Retorna emoji baseado no tipo de evento"""
    emojis = {
        "Culto": "⛪",
        "Reunião": "👥",
        "Celebração": "🎉",
        "Estudo Bíblico": "📖",
        "Evento Especial": "✨",
        "Conferência": "🎤",
        "Retiro": "🏕️",
        "Outro": "📅"
    }
    return emojis.get(event_type, "📅")

def get_event_color(event_type):
    """Retorna cor baseada no tipo de evento"""
    colors = {
        "Culto": "#4CAF50",
        "Reunião": "#2196F3",
        "Celebração": "#FF9800",
        "Estudo Bíblico": "#9C27B0",
        "Evento Especial": "#E91E63",
        "Conferência": "#607D8B",
        "Retiro": "#795548",
        "Outro": "#757575"
    }
    return colors.get(event_type, "#757575")

def get_filtered_events(filter_type, filter_period, search_term):
    """Busca eventos com filtros aplicados"""
    try:
        events = get_events()
        
        # Filtrar por tipo
        if filter_type != "Todos":
            events = [e for e in events if e['event_type'] == filter_type]
        
        # Filtrar por período
        now = datetime.now()
        if filter_period == "Próximos 30 dias":
            end_date = now + timedelta(days=30)
            filtered_events = []
            for e in events:
                try:
                    start_datetime = e['start_datetime']
                    if isinstance(start_datetime, str):
                        event_dt = datetime.fromisoformat(start_datetime.replace('Z', ''))
                    else:
                        event_dt = start_datetime
                    if now <= event_dt <= end_date:
                        filtered_events.append(e)
                except:
                    continue
            events = filtered_events
        elif filter_period == "Este mês":
            start_month = now.replace(day=1)
            next_month = (start_month + timedelta(days=32)).replace(day=1)
            filtered_events = []
            for e in events:
                try:
                    start_datetime = e['start_datetime']
                    if isinstance(start_datetime, str):
                        event_dt = datetime.fromisoformat(start_datetime.replace('Z', ''))
                    else:
                        event_dt = start_datetime
                    if start_month <= event_dt < next_month:
                        filtered_events.append(e)
                except:
                    continue
            events = filtered_events
        elif filter_period == "Próximo mês":
            next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
            month_after = (next_month + timedelta(days=32)).replace(day=1)
            filtered_events = []
            for e in events:
                try:
                    start_datetime = e['start_datetime']
                    if isinstance(start_datetime, str):
                        event_dt = datetime.fromisoformat(start_datetime.replace('Z', ''))
                    else:
                        event_dt = start_datetime
                    if next_month <= event_dt < month_after:
                        filtered_events.append(e)
                except:
                    continue
            events = filtered_events
        
        # Filtrar por termo de busca
        if search_term:
            search_term = search_term.lower()
            events = [e for e in events if 
                     search_term in e['title'].lower() or 
                     search_term in (e['description'] or '').lower() or
                     search_term in (e['location'] or '').lower()]
        
        # Ordenar por data
        events.sort(key=lambda x: x['start_datetime'])
        
        return events
    except Exception as e:
        st.error(f"Erro ao buscar eventos: {e}")
        return []

def get_event_by_id(event_id):
    """Busca evento por ID"""
    try:
        query = "SELECT * FROM events WHERE id = ?"
        result = db_manager.fetch_all(query, (event_id,))
        return result[0] if result else None
    except Exception as e:
        st.error(f"Erro ao buscar evento: {e}")
        return None

def delete_event(event_id):
    """Exclui evento"""
    try:
        query = "DELETE FROM events WHERE id = ?"
        db_manager.execute_query(query, (event_id,))
        return True
    except Exception as e:
        st.error(f"Erro ao excluir evento: {e}")
        return False

def process_event_submission(title, description, event_type, start_datetime, end_datetime, location, editing_event_id=None):
    """Processa criação ou edição de evento"""
    try:
        current_user = get_current_user()
        user_id = current_user.get('id') if current_user else 1
        
        if editing_event_id:
            # Atualizar evento existente
            query = """
                UPDATE events 
                SET title = ?, description = ?, event_type = ?, 
                    start_datetime = ?, end_datetime = ?, location = ?, 
                    updated_at = ?
                WHERE id = ?
            """
            params = (
                title, description, event_type,
                start_datetime.isoformat(), end_datetime.isoformat(), location,
                datetime.now().isoformat(), editing_event_id
            )
        else:
            # Criar novo evento
            query = """
                INSERT INTO events (title, description, event_type, start_datetime, end_datetime, 
                                  location, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                title, description, event_type,
                start_datetime.isoformat(), end_datetime.isoformat(), location,
                user_id, datetime.now().isoformat(), datetime.now().isoformat()
            )
        
        db_manager.execute_query(query, params)
        return True
    except Exception as e:
        st.error(f"Erro ao processar evento: {e}")
        return False