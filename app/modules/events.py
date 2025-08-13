"""
Módulo de Gerenciamento de Eventos
Funcionalidades para criar, editar e gerenciar eventos da igreja
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text
from app.database.local_connection import db_manager
from app.utils.auth import is_admin
from app.utils.validation import DataValidator

def show_events_management():
    """Interface principal para gerenciamento de eventos"""
    
    st.title("📅 Gerenciamento de Eventos")
    
    # Verificar se é admin
    if not is_admin():
        st.warning("⚠️ Acesso restrito a administradores")
        return
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3 = st.tabs(["📋 Lista de Eventos", "➕ Novo Evento", "📊 Relatórios"])
    
    with tab1:
        show_events_list()
    
    with tab2:
        show_create_event()
    
    with tab3:
        show_events_reports()

def show_events_list():
    """Exibe lista de eventos"""
    
    st.subheader("📋 Lista de Eventos")
    
    try:
        with db_manager.get_db_session() as session:
            # Buscar eventos
            result = session.execute(
                text("""
                SELECT 
                    e.id,
                    e.title,
                    e.description,
                    e.event_type,
                    e.start_datetime,
                    e.end_datetime,
                    e.location,
                    e.created_at,
                    u.full_name as created_by_name
                FROM events e
                LEFT JOIN users u ON e.created_by = u.id
                WHERE e.is_active = 1
                ORDER BY e.start_datetime DESC
                """)
            ).fetchall()
            
            if result:
                # Converter para DataFrame
                events_data = []
                for row in result:
                    events_data.append({
                        'ID': row.id,
                        'Título': row.title,
                        'Tipo': row.event_type,
                        'Data/Hora Início': row.start_datetime,
                        'Data/Hora Fim': row.end_datetime,
                        'Local': row.location or 'Não informado',
                        'Criado por': row.created_by_name or 'Sistema'
                    })
                
                df = pd.DataFrame(events_data)
                
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    tipo_filtro = st.selectbox(
                        "Filtrar por tipo:",
                        ["Todos"] + list(df['Tipo'].unique())
                    )
                
                with col2:
                    data_filtro = st.date_input("Filtrar por data:")
                
                # Aplicar filtros
                df_filtrado = df.copy()
                if tipo_filtro != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['Tipo'] == tipo_filtro]
                
                # Exibir tabela
                st.dataframe(df_filtrado, use_container_width=True)
                
                # Ações em lote
                if st.button("🗑️ Excluir Eventos Selecionados"):
                    st.warning("Funcionalidade em desenvolvimento")
                
            else:
                st.info("📅 Nenhum evento encontrado")
                
    except Exception as e:
        st.error(f"❌ Erro ao carregar eventos: {str(e)}")

def show_create_event():
    """Interface para criar novo evento"""
    
    st.subheader("➕ Criar Novo Evento")
    
    with st.form("create_event_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Título do Evento*", placeholder="Ex: Culto Dominical")
            event_type = st.selectbox(
                "Tipo de Evento*",
                ["Culto", "Reunião", "Evento Especial", "Conferência", "Retiro", "Outro"]
            )
            location = st.text_input("Local", placeholder="Ex: Santuário Principal")
        
        with col2:
            start_date = st.date_input("Data de Início*")
            start_time = st.time_input("Hora de Início*")
            end_date = st.date_input("Data de Fim*")
            end_time = st.time_input("Hora de Fim*")
        
        description = st.text_area(
            "Descrição",
            placeholder="Descreva os detalhes do evento...",
            height=100
        )
        
        submitted = st.form_submit_button("✅ Criar Evento")
        
        if submitted:
            # Validações
            if not title or not event_type:
                st.error("❌ Título e tipo são obrigatórios")
                return
            
            # Combinar data e hora
            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)
            
            if end_datetime <= start_datetime:
                st.error("❌ Data/hora de fim deve ser posterior ao início")
                return
            
            try:
                with db_manager.get_db_session() as session:
                    # Inserir evento
                    session.execute(
                        text("""
                        INSERT INTO events (
                            title, description, event_type, start_datetime, 
                            end_datetime, location, created_by
                        ) VALUES (
                            :title, :description, :event_type, :start_datetime,
                            :end_datetime, :location, :created_by
                        )
                        """),
                        {
                            'title': title,
                            'description': description,
                            'event_type': event_type,
                            'start_datetime': start_datetime.isoformat(),
                            'end_datetime': end_datetime.isoformat(),
                            'location': location,
                            'created_by': st.session_state.get('user_info', {}).get('id', 1)
                        }
                    )
                    session.commit()
                
                st.success("✅ Evento criado com sucesso!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erro ao criar evento: {str(e)}")

def show_events_reports():
    """Exibe relatórios de eventos"""
    
    st.subheader("📊 Relatórios de Eventos")
    
    try:
        with db_manager.get_db_session() as session:
            # Estatísticas gerais
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_events = session.execute(
                    text("SELECT COUNT(*) as count FROM events WHERE is_active = 1")
                ).fetchone().count
                st.metric("Total de Eventos", total_events)
            
            with col2:
                events_this_month = session.execute(
                    text("""
                    SELECT COUNT(*) as count FROM events 
                    WHERE is_active = 1 
                    AND strftime('%Y-%m', start_datetime) = strftime('%Y-%m', 'now')
                    """)
                ).fetchone().count
                st.metric("Eventos Este Mês", events_this_month)
            
            with col3:
                upcoming_events = session.execute(
                    text("""
                    SELECT COUNT(*) as count FROM events 
                    WHERE is_active = 1 
                    AND start_datetime > datetime('now')
                    """)
                ).fetchone().count
                st.metric("Próximos Eventos", upcoming_events)
            
            # Gráfico por tipo
            st.subheader("📈 Eventos por Tipo")
            
            events_by_type = session.execute(
                text("""
                SELECT event_type, COUNT(*) as count 
                FROM events 
                WHERE is_active = 1 
                GROUP BY event_type
                ORDER BY count DESC
                """)
            ).fetchall()
            
            if events_by_type:
                df_types = pd.DataFrame(events_by_type, columns=['Tipo', 'Quantidade'])
                st.bar_chart(df_types.set_index('Tipo'))
            else:
                st.info("📊 Dados insuficientes para gráficos")
                
    except Exception as e:
        st.error(f"❌ Erro ao gerar relatórios: {str(e)}")

def get_upcoming_events(limit=5):
    """Retorna próximos eventos (para uso em outros módulos)"""
    
    try:
        with db_manager.get_db_session() as session:
            result = session.execute(
                text("""
                SELECT title, start_datetime, event_type, location
                FROM events 
                WHERE is_active = 1 
                AND start_datetime > datetime('now')
                ORDER BY start_datetime ASC
                LIMIT :limit
                """),
                {'limit': limit}
            ).fetchall()
            
            return [dict(row._mapping) for row in result]
            
    except Exception:
        return []

def get_events_stats():
    """Retorna estatísticas de eventos (para dashboard)"""
    
    try:
        with db_manager.get_db_session() as session:
            stats = {}
            
            # Total de eventos
            stats['total'] = session.execute(
                text("SELECT COUNT(*) as count FROM events WHERE is_active = 1")
            ).fetchone().count
            
            # Eventos este mês
            stats['this_month'] = session.execute(
                text("""
                SELECT COUNT(*) as count FROM events 
                WHERE is_active = 1 
                AND strftime('%Y-%m', start_datetime) = strftime('%Y-%m', 'now')
                """)
            ).fetchone().count
            
            # Próximos eventos
            stats['upcoming'] = session.execute(
                text("""
                SELECT COUNT(*) as count FROM events 
                WHERE is_active = 1 
                AND start_datetime > datetime('now')
                """)
            ).fetchone().count
            
            return stats
            
    except Exception:
        return {'total': 0, 'this_month': 0, 'upcoming': 0}

# Função principal para ser chamada pelo main.py
def main():
    """Função principal do módulo"""
    show_events_management()

if __name__ == "__main__":
    main()