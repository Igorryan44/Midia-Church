import streamlit as st
import pandas as pd
from datetime import datetime, date
from app.database.local_connection import db_manager, get_events, get_all_users
from app.utils.auth import get_current_user

def render_attendance():
    """Renderiza o módulo de controle de presença"""
    
    st.title("✅ Controle de Presença")
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Registro", "📊 Relatórios", "👥 Eventos", "📈 Estatísticas"])
    
    with tab1:
        render_attendance_registration()
    
    with tab2:
        render_attendance_reports()
    
    with tab3:
        render_event_attendance()
    
    with tab4:
        render_attendance_statistics()

def render_attendance_registration():
    """Renderiza o registro de presença"""
    
    st.subheader("📋 Registro de Presença")
    
    # Seleção do evento
    events = get_upcoming_events()
    
    if not events:
        st.warning("Nenhum evento disponível para registro de presença.")
        return
    
    event_options = {f"{event['title']} - {datetime.fromisoformat(event['start_datetime']).strftime('%d/%m/%Y %H:%M')}": event['id'] for event in events}
    
    selected_event_name = st.selectbox(
        "Selecione o Evento",
        options=list(event_options.keys())
    )
    
    selected_event_id = event_options[selected_event_name]
    
    # Buscar membros e suas presenças
    members_attendance = get_members_attendance(selected_event_id)
    
    st.divider()
    
    # Formulário de presença
    st.subheader("👥 Lista de Membros")
    
    with st.form("attendance_form"):
        attendance_data = {}
        
        # Criar colunas para organizar melhor
        cols_per_row = 2
        member_list = list(members_attendance)
        
        for i in range(0, len(member_list), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j, col in enumerate(cols):
                if i + j < len(member_list):
                    member = member_list[i + j]
                    
                    with col:
                        # Checkbox para presença
                        is_present = st.checkbox(
                            f"👤 {member['full_name']}",
                            value=member['present'] or False,
                            key=f"member_{member['user_id']}"
                        )
                        
                        attendance_data[member['user_id']] = is_present
                        
                        # Campo para observações
                        notes = st.text_input(
                            "Observações",
                            value=member['notes'] or "",
                            key=f"notes_{member['user_id']}",
                            placeholder="Observações sobre a presença..."
                        )
                        
                        attendance_data[f"notes_{member['user_id']}"] = notes
        
        # Botão para salvar
        if st.form_submit_button("💾 Salvar Presença", use_container_width=True):
            success = save_attendance(selected_event_id, attendance_data)
            
            if success:
                st.success("✅ Presença registrada com sucesso!")
                st.rerun()
            else:
                st.error("❌ Erro ao registrar presença. Tente novamente.")
    
    # Resumo da presença atual
    st.divider()
    render_attendance_summary(selected_event_id)

def render_attendance_reports():
    """Renderiza relatórios de presença"""
    
    st.subheader("📊 Relatórios de Presença")
    
    # Filtros para relatórios
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input("Data Inicial", value=date.today().replace(day=1))
    
    with col2:
        end_date = st.date_input("Data Final", value=date.today())
    
    with col3:
        event_type_filter = st.selectbox(
            "Tipo de Evento",
            options=["Todos", "Culto", "Reunião", "Celebração", "Estudo Bíblico", "Evento Especial"]
        )
    
    # Gerar relatório
    if st.button("📈 Gerar Relatório", use_container_width=True):
        report_data = generate_attendance_report(start_date, end_date, event_type_filter)
        
        if report_data:
            st.subheader("📋 Relatório de Presença")
            
            # Converter para DataFrame
            df_report = pd.DataFrame(report_data)
            
            # Calcular estatísticas
            total_events = len(df_report)
            avg_attendance = df_report['attendance_rate'].mean() if not df_report.empty else 0
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📅 Total de Eventos", total_events)
            
            with col2:
                st.metric("👥 Presença Média", f"{avg_attendance:.1f}%")
            
            with col3:
                best_event = df_report.loc[df_report['attendance_rate'].idxmax()] if not df_report.empty else None
                if best_event is not None:
                    st.metric("🏆 Melhor Presença", f"{best_event['attendance_rate']:.1f}%")
            
            # Tabela detalhada
            st.dataframe(
                df_report[['event_title', 'event_date', 'total_members', 'present_count', 'attendance_rate']].rename(columns={
                    'event_title': 'Evento',
                    'event_date': 'Data',
                    'total_members': 'Total Membros',
                    'present_count': 'Presentes',
                    'attendance_rate': 'Taxa (%)'
                }),
                use_container_width=True
            )
            
            # Gráfico de presença ao longo do tempo
            st.subheader("📈 Tendência de Presença")
            st.line_chart(df_report.set_index('event_date')['attendance_rate'])
            
        else:
            st.info("Nenhum dado encontrado para o período selecionado.")

def render_event_attendance():
    """Renderiza presença por evento específico"""
    
    st.subheader("👥 Presença por Evento")
    
    # Seleção do evento
    all_events = get_all_events_with_attendance()
    
    if not all_events:
        st.info("Nenhum evento com registro de presença encontrado.")
        return
    
    event_options = {f"{event['title']} - {datetime.fromisoformat(event['start_datetime']).strftime('%d/%m/%Y')}": event['id'] for event in all_events}
    
    selected_event_name = st.selectbox(
        "Selecione o Evento",
        options=list(event_options.keys())
    )
    
    selected_event_id = event_options[selected_event_name]
    
    # Buscar detalhes da presença
    attendance_details = get_event_attendance_details(selected_event_id)
    
    if attendance_details:
        # Estatísticas do evento
        total_registered = len(attendance_details)
        present_count = sum(1 for member in attendance_details if member['present'])
        attendance_rate = (present_count / total_registered * 100) if total_registered > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Total Registrados", total_registered)
        
        with col2:
            st.metric("✅ Presentes", present_count)
        
        with col3:
            st.metric("📊 Taxa de Presença", f"{attendance_rate:.1f}%")
        
        st.divider()
        
        # Lista detalhada
        st.subheader("📋 Lista Detalhada")
        
        # Separar presentes e ausentes
        present_members = [m for m in attendance_details if m['present']]
        absent_members = [m for m in attendance_details if not m['present']]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ✅ Presentes")
            for member in present_members:
                st.write(f"👤 {member['full_name']}")
                if member['check_in_time']:
                    check_in = datetime.fromisoformat(member['check_in_time'])
                    st.caption(f"⏰ Check-in: {check_in.strftime('%H:%M')}")
                if member['notes']:
                    st.caption(f"📝 {member['notes']}")
                st.divider()
        
        with col2:
            st.markdown("### ❌ Ausentes")
            for member in absent_members:
                st.write(f"👤 {member['full_name']}")
                if member['notes']:
                    st.caption(f"📝 {member['notes']}")
                st.divider()

def render_attendance_statistics():
    """Renderiza estatísticas de presença"""
    
    st.subheader("📈 Estatísticas de Presença")
    
    # Estatísticas gerais
    stats = get_general_attendance_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📅 Total de Eventos", stats['total_events'])
    
    with col2:
        st.metric("👥 Membros Ativos", stats['active_members'])
    
    with col3:
        st.metric("📊 Presença Média Geral", f"{stats['avg_attendance']:.1f}%")
    
    with col4:
        st.metric("🏆 Melhor Mês", stats['best_month'])
    
    st.divider()
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Presença por Tipo de Evento")
        attendance_by_type = get_attendance_by_event_type()
        
        if attendance_by_type:
            df_type = pd.DataFrame(attendance_by_type)
            st.bar_chart(df_type.set_index('event_type')['avg_attendance'])
        else:
            st.info("Nenhum dado disponível")
    
    with col2:
        st.subheader("📈 Tendência Mensal")
        monthly_trend = get_monthly_attendance_trend()
        
        if monthly_trend:
            df_monthly = pd.DataFrame(monthly_trend)
            st.line_chart(df_monthly.set_index('month')['avg_attendance'])
        else:
            st.info("Nenhum dado disponível")
    
    # Top membros mais assíduos
    st.subheader("🏆 Membros Mais Assíduos")
    top_members = get_top_attending_members()
    
    if top_members:
        for i, member in enumerate(top_members[:10], 1):
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}º"
                st.markdown(f"**{medal}**")
            
            with col2:
                st.write(f"👤 {member['full_name']}")
            
            with col3:
                st.write(f"{member['attendance_rate']:.1f}%")

def render_attendance_summary(event_id):
    """Renderiza resumo da presença de um evento"""
    
    st.subheader("📊 Resumo da Presença")
    
    summary = get_attendance_summary(event_id)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("👥 Total de Membros", summary['total_members'])
    
    with col2:
        st.metric("✅ Presentes", summary['present_count'])
    
    with col3:
        attendance_rate = (summary['present_count'] / summary['total_members'] * 100) if summary['total_members'] > 0 else 0
        st.metric("📊 Taxa de Presença", f"{attendance_rate:.1f}%")

# Funções auxiliares para buscar dados

def get_upcoming_events():
    """Busca eventos próximos"""
    try:
        query = """
        SELECT id, title, start_datetime
        FROM events
        WHERE start_datetime >= date('now')
        AND is_active = 1
        ORDER BY start_datetime
        """
        return db_manager.fetch_all(query)
    except:
        return []

def get_members_attendance(event_id):
    """Busca membros e suas presenças para um evento"""
    try:
        query = """
        SELECT u.id as user_id, u.full_name,
               COALESCE(a.present, 0) as present,
               a.notes,
               a.check_in_time
        FROM users u
        LEFT JOIN attendance a ON u.id = a.user_id AND a.event_id = ?
        WHERE u.is_active = 1
        ORDER BY u.full_name
        """
        return db_manager.fetch_all(query, (event_id,))
    except:
        return []

def save_attendance(event_id, attendance_data):
    """Salva os dados de presença"""
    try:
        for key, value in attendance_data.items():
            if key.startswith('notes_'):
                continue  # Processar notas separadamente
            
            user_id = key.replace('member_', '')
            if not user_id.isdigit():
                continue
            
            user_id = int(user_id)
            is_present = value
            notes = attendance_data.get(f'notes_{user_id}', '')
            
            # Verificar se já existe registro
            existing_query = "SELECT id FROM attendance WHERE event_id = ? AND user_id = ?"
            existing = db_manager.fetch_all(existing_query, (event_id, user_id))
            
            if existing:
                # Atualizar registro existente
                update_query = """
                UPDATE attendance 
                SET present = ?, notes = ?, check_in_time = ?
                WHERE event_id = ? AND user_id = ?
                """
                check_in_time = datetime.now() if is_present else None
                db_manager.execute_query(update_query, (is_present, notes, check_in_time, event_id, user_id))
            else:
                # Criar novo registro
                insert_query = """
                INSERT INTO attendance (event_id, user_id, present, notes, check_in_time)
                VALUES (?, ?, ?, ?, ?)
                """
                check_in_time = datetime.now() if is_present else None
                db_manager.execute_query(insert_query, (event_id, user_id, is_present, notes, check_in_time))
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar presença: {e}")
        return False

def get_attendance_summary(event_id):
    """Busca resumo da presença de um evento"""
    try:
        query = """
        SELECT 
            COUNT(u.id) as total_members,
            SUM(CASE WHEN a.present = 1 THEN 1 ELSE 0 END) as present_count
        FROM users u
        LEFT JOIN attendance a ON u.id = a.user_id AND a.event_id = ?
        WHERE u.is_active = 1
        """
        result = db_manager.fetch_all(query, (event_id,))
        
        if result:
            return {
                'total_members': result[0]['total_members'],
                'present_count': result[0]['present_count'] or 0
            }
        return {'total_members': 0, 'present_count': 0}
    except:
        return {'total_members': 0, 'present_count': 0}

def generate_attendance_report(start_date, end_date, event_type_filter):
    """Gera relatório de presença"""
    try:
        query = """
        SELECT 
            e.title as event_title,
            e.start_datetime as event_date,
            e.event_type,
            COUNT(u.id) as total_members,
            SUM(CASE WHEN a.present = 1 THEN 1 ELSE 0 END) as present_count,
            ROUND(AVG(CASE WHEN a.present = 1 THEN 100.0 ELSE 0.0 END), 1) as attendance_rate
        FROM events e
        LEFT JOIN attendance a ON e.id = a.event_id
        LEFT JOIN users u ON a.user_id = u.id AND u.is_active = 1
        WHERE date(e.start_datetime) BETWEEN ? AND ?
        AND e.is_active = 1
        """
        
        params = [start_date, end_date]
        
        if event_type_filter != "Todos":
            query += " AND e.event_type = ?"
            params.append(event_type_filter)
        
        query += """
        GROUP BY e.id, e.title, e.start_datetime, e.event_type
        ORDER BY e.start_datetime DESC
        """
        
        return db_manager.fetch_all(query, params)
    except:
        return []

def get_all_events_with_attendance():
    """Busca todos os eventos que têm registro de presença"""
    try:
        query = """
        SELECT DISTINCT e.id, e.title, e.start_datetime
        FROM events e
        INNER JOIN attendance a ON e.id = a.event_id
        WHERE e.is_active = 1
        ORDER BY e.start_datetime DESC
        """
        return db_manager.fetch_all(query)
    except:
        return []

def get_event_attendance_details(event_id):
    """Busca detalhes da presença de um evento específico"""
    try:
        query = """
        SELECT u.full_name, a.present, a.check_in_time, a.notes
        FROM attendance a
        JOIN users u ON a.user_id = u.id
        WHERE a.event_id = ? AND u.is_active = 1
        ORDER BY u.full_name
        """
        return db_manager.fetch_all(query, (event_id,))
    except:
        return []

def get_general_attendance_stats():
    """Busca estatísticas gerais de presença"""
    try:
        # Total de eventos
        total_events_query = "SELECT COUNT(*) as count FROM events WHERE is_active = 1"
        total_events = db_manager.fetch_all(total_events_query)[0]['count']
        
        # Membros ativos
        active_members_query = "SELECT COUNT(*) as count FROM users WHERE is_active = 1"
        active_members = db_manager.fetch_all(active_members_query)[0]['count']
        
        # Presença média geral
        avg_attendance_query = """
        SELECT AVG(CASE WHEN present = 1 THEN 100.0 ELSE 0.0 END) as avg_attendance
        FROM attendance a
        JOIN events e ON a.event_id = e.id
        WHERE e.is_active = 1
        """
        avg_result = db_manager.fetch_all(avg_attendance_query)
        avg_attendance = avg_result[0]['avg_attendance'] or 0 if avg_result else 0
        
        return {
            'total_events': total_events,
            'active_members': active_members,
            'avg_attendance': avg_attendance,
            'best_month': 'Dezembro'  # Placeholder
        }
    except:
        return {
            'total_events': 0,
            'active_members': 0,
            'avg_attendance': 0,
            'best_month': 'N/A'
        }

def get_attendance_by_event_type():
    """Busca presença média por tipo de evento"""
    try:
        query = """
        SELECT 
            e.event_type,
            AVG(CASE WHEN a.present = 1 THEN 100.0 ELSE 0.0 END) as avg_attendance
        FROM events e
        LEFT JOIN attendance a ON e.id = a.event_id
        WHERE e.is_active = 1
        GROUP BY e.event_type
        """
        return db_manager.fetch_all(query)
    except:
        return []

def get_monthly_attendance_trend():
    """Busca tendência mensal de presença"""
    try:
        query = """
        SELECT 
            strftime('%Y-%m', e.start_datetime) as month,
            AVG(CASE WHEN a.present = 1 THEN 100.0 ELSE 0.0 END) as avg_attendance
        FROM events e
        LEFT JOIN attendance a ON e.id = a.event_id
        WHERE e.is_active = 1
        GROUP BY strftime('%Y-%m', e.start_datetime)
        ORDER BY month
        """
        return db_manager.fetch_all(query)
    except:
        return []

def get_top_attending_members():
    """Busca membros com maior taxa de presença"""
    try:
        query = """
        SELECT 
            u.full_name,
            AVG(CASE WHEN a.present = 1 THEN 100.0 ELSE 0.0 END) as attendance_rate,
            COUNT(a.id) as total_events
        FROM users u
        LEFT JOIN attendance a ON u.id = a.user_id
        WHERE u.is_active = 1
        GROUP BY u.id, u.full_name
        HAVING COUNT(a.id) >= 3
        ORDER BY attendance_rate DESC
        """
        return db_manager.fetch_all(query)
    except:
        return []