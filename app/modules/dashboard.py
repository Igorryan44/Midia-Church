import streamlit as st
from datetime import datetime, timedelta
from app.database.local_connection import db_manager, get_all_users, get_events
from app.utils.auth import get_current_user, is_admin
from app.utils.cache_manager import smart_cache
from app.utils.lazy_loading import lazy_component, lazy_load_dashboard_stats
from app.utils.memory_optimizer import optimize_dataframe
from app.utils.database_optimizer import monitor_db_performance
from app.components.widgets import (
    render_metric_card, render_progress_ring, render_activity_timeline,
    render_quick_stats_grid, render_chart_card, render_weather_widget,
    render_calendar_widget
)
from app.config.timezone import get_local_time, get_local_date

def render_dashboard():
    """Renderiza o dashboard principal"""
    
    st.title("🏠 Dashboard")
    
    # Métricas principais com cards modernos
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_members = get_total_members()
        render_metric_card(
            title="Total de Membros",
            value=total_members,
            icon="👥"
        )
    
    with col2:
        upcoming_events = get_upcoming_events_count()
        render_metric_card(
            title="Próximos Eventos",
            value=upcoming_events,
            icon="📅"
        )
    
    with col3:
        total_content = get_total_content()
        render_metric_card(
            title="Conteúdos",
            value=total_content,
            icon="📁"
        )
    
    with col4:
        avg_attendance = get_average_attendance()
        render_metric_card(
            title="Presença Média",
            value=f"{avg_attendance}%" if avg_attendance > 0 else "N/A",
            icon="✅"
        )
    
    st.divider()
    
    # Segunda linha com widgets adicionais
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        st.subheader("📊 Presença nos Últimos Eventos")
        attendance_chart = create_attendance_chart()
        if attendance_chart:
            st.plotly_chart(attendance_chart, use_container_width=True)
        else:
            st.info("Nenhum dado de presença disponível ainda.")
    
    with col2:
        st.subheader("📈 Eventos por Tipo")
        events_chart = create_events_by_type_chart()
        if events_chart:
            st.plotly_chart(events_chart, use_container_width=True)
        else:
            st.info("Nenhum evento cadastrado ainda.")
    
    with col3, col4:
        # Horário e Tempo
        render_weather_widget()
    
    st.divider()
    
    # Terceira linha com eventos e atividades
    col1, col2 = st.columns(2)
    
    with col1:
        upcoming_events_data = get_upcoming_events()
        render_calendar_widget(upcoming_events_data)
        
        if upcoming_events_data:
            import pandas as pd  # Lazy import
            df_events = pd.DataFrame(upcoming_events_data)
            df_events['start_datetime'] = pd.to_datetime(df_events['start_datetime'])
            df_events['Data'] = df_events['start_datetime'].dt.strftime('%d/%m/%Y %H:%M')
            
            with st.expander("Ver todos os eventos"):
                st.dataframe(
                    df_events[['title', 'event_type', 'Data', 'location']].rename(columns={
                        'title': 'Evento',
                        'event_type': 'Tipo',
                        'location': 'Local'
                    }),
                    use_container_width=True
                )
    
    with col2:
        recent_activities = get_recent_activities_formatted()
        render_activity_timeline(recent_activities)
    
    # Verificar se há conteúdo para mostrar seção adicional
    total_content = get_total_content()
    if total_content > 0:
        st.divider()
        
        # Quarta linha com estatísticas de conteúdo
        st.subheader("📁 Estatísticas de Conteúdo")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            content_stats = get_content_stats()
            st.metric("📤 Uploads Recentes (7 dias)", content_stats.get('recent_uploads', 0))
            st.metric("💾 Tamanho Total", f"{content_stats.get('total_size_mb', 0)} MB")
        
        with col2:
            content_chart = create_content_by_type_chart()
            if content_chart:
                st.plotly_chart(content_chart, use_container_width=True)
            else:
                st.info("Nenhum conteúdo disponível para análise.")
        
        with col3:
            if content_stats:
                st.write("**Detalhes por Tipo:**")
                type_translation = {
                    'image': '🖼️ Imagens',
                    'video': '🎥 Vídeos', 
                    'audio': '🎵 Áudios',
                    'document': '📄 Documentos'
                }
                for file_type, count in content_stats.items():
                    if file_type not in ['recent_uploads', 'total_size_mb']:
                        display_name = type_translation.get(file_type, file_type.title())
                        st.write(f"{display_name}: {count}")

@smart_cache(max_age_minutes=5, key_prefix="dashboard_stats")
@monitor_db_performance
@optimize_dataframe
def get_total_members():
    """Retorna o total de membros ativos"""
    try:
        result = db_manager.fetch_all("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
        return result[0]['count'] if result else 0
    except:
        return 0

def get_upcoming_events_count():
    """Retorna o número de eventos próximos"""
    try:
        query = "SELECT COUNT(*) as count FROM events WHERE start_datetime > datetime('now') AND is_active = 1"
        result = db_manager.fetch_all(query)
        return result[0]['count'] if result else 0
    except:
        return 0

def get_total_content():
    """Retorna o total de conteúdos"""
    try:
        query = "SELECT COUNT(*) as total FROM media_content WHERE is_active = 1"
        result = db_manager.fetch_all(query)
        return result[0]['total'] if result else 0
    except:
        return 0

def get_average_attendance():
    """Retorna a média de presença"""
    try:
        query = """
        SELECT AVG(CASE WHEN present = 1 THEN 100.0 ELSE 0.0 END) as avg_attendance
        FROM attendance a
        JOIN events e ON a.event_id = e.id
        WHERE e.start_datetime > datetime('now', '-30 days')
        """
        result = db_manager.fetch_all(query)
        return round(result[0]['avg_attendance'] or 0, 1) if result else 0
    except:
        return 0

def create_attendance_chart():
    """Cria gráfico de presença"""
    try:
        import pandas as pd  # Lazy import
        import plotly.express as px  # Lazy import
        
        query = """
        SELECT e.title, 
               COUNT(a.id) as total_registered,
               SUM(CASE WHEN a.present = 1 THEN 1 ELSE 0 END) as present_count
        FROM events e
        LEFT JOIN attendance a ON e.id = a.event_id
        WHERE e.start_datetime > datetime('now', '-30 days')
        AND e.is_active = 1
        GROUP BY e.id, e.title
        ORDER BY e.start_datetime DESC
        LIMIT 5
        """
        result = db_manager.fetch_all(query)
        
        if result:
            df = pd.DataFrame(result)
            df['attendance_rate'] = (df['present_count'] / df['total_registered'] * 100).fillna(0)
            
            fig = px.bar(
                df, 
                x='title', 
                y='attendance_rate',
                title="Taxa de Presença (%)",
                labels={'title': 'Evento', 'attendance_rate': 'Presença (%)'}
            )
            fig.update_layout(showlegend=False)
            return fig
        return None
    except:
        return None

def create_events_by_type_chart():
    """Cria gráfico de eventos por tipo"""
    try:
        import pandas as pd  # Lazy import
        import plotly.express as px  # Lazy import
        
        query = """
        SELECT event_type, COUNT(*) as count
        FROM events
        WHERE is_active = 1
        GROUP BY event_type
        """
        result = db_manager.fetch_all(query)
        
        if result:
            df = pd.DataFrame(result)
            fig = px.pie(
                df, 
                values='count', 
                names='event_type',
                title="Distribuição de Eventos por Tipo"
            )
            return fig
        return None
    except:
        return None

def create_content_by_type_chart():
    """Cria gráfico de conteúdo por tipo"""
    try:
        import pandas as pd  # Lazy import
        import plotly.express as px  # Lazy import
        
        query = """
        SELECT file_type, COUNT(*) as count
        FROM media_content
        WHERE is_active = 1
        GROUP BY file_type
        """
        result = db_manager.fetch_all(query)
        
        if result:
            df = pd.DataFrame(result)
            # Traduzir tipos de arquivo para português
            type_translation = {
                'image': 'Imagens',
                'video': 'Vídeos', 
                'audio': 'Áudios',
                'document': 'Documentos'
            }
            df['file_type_pt'] = df['file_type'].map(type_translation).fillna(df['file_type'].str.title())
            
            fig = px.pie(
                df, 
                values='count', 
                names='file_type_pt',
                title="Distribuição de Conteúdo por Tipo"
            )
            return fig
        return None
    except:
        return None

def get_content_stats():
    """Retorna estatísticas detalhadas de conteúdo"""
    try:
        stats = {}
        
        # Total por tipo
        query = """
        SELECT file_type, COUNT(*) as count
        FROM media_content
        WHERE is_active = 1
        GROUP BY file_type
        """
        result = db_manager.fetch_all(query)
        if result:
            for row in result:
                stats[row['file_type']] = row['count']
        
        # Conteúdo adicionado nos últimos 7 dias
        seven_days_ago = (get_local_time() - timedelta(days=7)).isoformat()
        query = """
        SELECT COUNT(*) as recent_count
        FROM media_content
        WHERE uploaded_at > ? AND is_active = 1
        """
        result = db_manager.fetch_all(query, [seven_days_ago])
        stats['recent_uploads'] = result[0]['recent_count'] if result else 0
        
        # Tamanho total dos arquivos (em MB)
        query = """
        SELECT SUM(file_size) as total_size
        FROM media_content
        WHERE is_active = 1 AND file_size IS NOT NULL
        """
        result = db_manager.fetch_all(query)
        total_size_bytes = result[0]['total_size'] if result and result[0]['total_size'] else 0
        stats['total_size_mb'] = round(total_size_bytes / (1024 * 1024), 2)
        
        return stats
    except:
        return {}

def get_upcoming_events():
    """Retorna próximos eventos"""
    try:
        current_time = get_local_time()
        query = """
        SELECT title, start_datetime, event_type, location
        FROM events 
        WHERE start_datetime >= ?
        ORDER BY start_datetime ASC
        LIMIT 5
        """
        events = db_manager.fetch_all(query, [current_time.isoformat()])
        
        if events:
            for event in events:
                # Converter string para datetime se necessário
                if isinstance(event['start_datetime'], str):
                    event['start_datetime'] = datetime.fromisoformat(event['start_datetime'])
        
        return events or []
    except Exception as e:
        return []

def get_recent_activities():
    """Retorna atividades recentes do banco de dados"""
    try:
        activities = []
        seven_days_ago = (get_local_time() - timedelta(days=7)).isoformat()
        
        # Buscar eventos recentes
        events_query = """
        SELECT 'event' as type, 'Evento Criado' as title, 
               title as event_title, created_at
        FROM events 
        WHERE created_at > ?
        ORDER BY created_at DESC
        LIMIT 3
        """
        events = db_manager.fetch_all(events_query, [seven_days_ago])
        if events:
            for event in events:
                activities.append({
                    'type': 'event',
                    'title': 'Evento Criado',
                    'description': f'Evento "{event["event_title"]}" foi criado',
                    'created_at': event['created_at']
                })
        
        # Buscar novos usuários
        users_query = """
        SELECT 'member' as type, 'Novo Membro' as title,
               username, created_at
        FROM users 
        WHERE created_at > ?
        ORDER BY created_at DESC
        LIMIT 3
        """
        users = db_manager.fetch_all(users_query, [seven_days_ago])
        if users:
            for user in users:
                activities.append({
                    'type': 'member',
                    'title': 'Novo Membro',
                    'description': f'Usuário "{user["username"]}" se juntou ao sistema',
                    'created_at': user['created_at']
                })
        
        # Buscar conteúdos recentes
        content_query = """
        SELECT 'content' as type, 'Conteúdo Adicionado' as title,
               title as content_title, file_type, category, uploaded_at
        FROM media_content 
        WHERE uploaded_at > ? AND is_active = 1
        ORDER BY uploaded_at DESC
        LIMIT 3
        """
        content = db_manager.fetch_all(content_query, [seven_days_ago])
        if content:
            for item in content:
                file_type_display = {
                    'image': 'Imagem',
                    'video': 'Vídeo', 
                    'audio': 'Áudio',
                    'document': 'Documento'
                }.get(item['file_type'], item['file_type'].title())
                
                category_display = f" ({item['category']})" if item['category'] else ""
                
                activities.append({
                    'type': 'content',
                    'title': 'Conteúdo Adicionado',
                    'description': f'{file_type_display} "{item["content_title"]}"{category_display} foi adicionado',
                    'created_at': item['uploaded_at']
                })
        
        # Ordenar por data
        activities.sort(key=lambda x: x['created_at'], reverse=True)
        return activities[:10]
        
    except Exception as e:
        return []

def get_recent_activities_formatted():
    """Retorna atividades recentes formatadas para o widget de timeline"""
    try:
        activities = []
        seven_days_ago = (get_local_time() - timedelta(days=7)).isoformat()
        
        # Buscar eventos recentes
        events_query = """
        SELECT 'event' as type, 'Evento Criado' as title, 
               title as event_title, start_datetime, created_at
        FROM events 
        WHERE created_at > ?
        ORDER BY created_at DESC
        LIMIT 3
        """
        events = db_manager.fetch_all(events_query, [seven_days_ago])
        if events:
            for event in events:
                activities.append({
                    'title': 'Evento Criado',
                    'description': f'Evento "{event["event_title"]}" foi criado',
                    'type': 'event',
                    'created_at': datetime.fromisoformat(event['created_at']) if isinstance(event['created_at'], str) else event['created_at']
                })
        
        # Buscar novos usuários
        users_query = """
        SELECT 'member' as type, 'Novo Membro' as title,
               username, created_at
        FROM users 
        WHERE created_at > ?
        ORDER BY created_at DESC
        LIMIT 3
        """
        users = db_manager.fetch_all(users_query, [seven_days_ago])
        if users:
            for user in users:
                activities.append({
                    'title': 'Novo Membro',
                    'description': f'Usuário "{user["username"]}" se juntou ao sistema',
                    'type': 'member',
                    'created_at': datetime.fromisoformat(user['created_at']) if isinstance(user['created_at'], str) else user['created_at']
                })
        
        # Buscar conteúdos recentes
        content_query = """
        SELECT 'content' as type, 'Conteúdo Adicionado' as title,
               title as content_title, file_type, category, uploaded_at
        FROM media_content 
        WHERE uploaded_at > ? AND is_active = 1
        ORDER BY uploaded_at DESC
        LIMIT 3
        """
        content = db_manager.fetch_all(content_query, [seven_days_ago])
        if content:
            for item in content:
                file_type_display = {
                    'image': 'Imagem',
                    'video': 'Vídeo', 
                    'audio': 'Áudio',
                    'document': 'Documento'
                }.get(item['file_type'], item['file_type'].title())
                
                category_display = f" ({item['category']})" if item['category'] else ""
                
                activities.append({
                    'title': 'Conteúdo Adicionado',
                    'description': f'{file_type_display} "{item["content_title"]}"{category_display} foi adicionado',
                    'type': 'content',
                    'created_at': datetime.fromisoformat(item['uploaded_at']) if isinstance(item['uploaded_at'], str) else item['uploaded_at']
                })
        
        # Ordenar por data e retornar apenas os mais recentes
        activities.sort(key=lambda x: x['created_at'], reverse=True)
        return activities[:10] if activities else []
        
    except Exception as e:
        return []