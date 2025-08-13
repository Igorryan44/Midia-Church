import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import locale

def render_metric_card(title, value, delta=None, delta_color="normal", icon="📊"):
    """Renderiza um card de métrica moderno"""
    # Usar st.metric nativo do Streamlit para evitar problemas de renderização HTML
    if delta is not None:
        st.metric(
            label=f"{icon} {title}",
            value=value,
            delta=f"{delta:+.1f}%"
        )
    else:
        st.metric(
            label=f"{icon} {title}",
            value=value
        )

def render_progress_ring(percentage, title, color="#667eea"):
    """Renderiza um anel de progresso"""
    fig = go.Figure(data=[go.Pie(
        values=[percentage, 100-percentage],
        hole=0.7,
        marker_colors=[color, '#f8f9fa'],
        textinfo='none',
        hoverinfo='none',
        showlegend=False
    )])
    
    fig.update_layout(
        annotations=[dict(text=f'{percentage}%', x=0.5, y=0.5, font_size=20, showarrow=False)],
        height=200,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"<div style='text-align: center; margin-top: -20px; font-weight: bold;'>{title}</div>", 
                unsafe_allow_html=True)

def render_activity_timeline(activities):
    """Renderiza uma timeline de atividades"""
    if not activities:
        st.info("Nenhuma atividade recente")
        return
    
    st.subheader("📋 Atividades Recentes")
    
    for activity in activities[:10]:  # Mostrar apenas as 10 mais recentes
        time_ago = get_time_ago(activity.get('created_at', datetime.now()))
        icon = get_activity_icon(activity.get('type', 'default'))
        
        with st.container():
            col1, col2 = st.columns([1, 10])
            
            with col1:
                st.write(icon)
            
            with col2:
                st.write(f"**{activity.get('title', 'Atividade')}**")
                if activity.get('description'):
                    st.write(activity.get('description', ''))
                st.caption(time_ago)
            
            st.divider()

def render_quick_stats_grid(stats):
    """Renderiza uma grade de estatísticas rápidas"""
    cols = st.columns(len(stats))
    
    for i, (key, data) in enumerate(stats.items()):
        with cols[i]:
            render_metric_card(
                title=data.get('title', key),
                value=data.get('value', 0),
                delta=data.get('delta'),
                icon=data.get('icon', '📊')
            )

def render_chart_card(title, chart_type, data, height=400):
    """Renderiza um card com gráfico"""
    st.markdown(f"""
    <div style="
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 20px 0;
    ">
        <h3 style="margin-bottom: 20px; color: #333;">{title}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if chart_type == "line":
        fig = px.line(data, x='date', y='value', title="")
    elif chart_type == "bar":
        fig = px.bar(data, x='category', y='value', title="")
    elif chart_type == "pie":
        fig = px.pie(data, values='value', names='category', title="")
    else:
        fig = px.scatter(data, x='x', y='y', title="")
    
    fig.update_layout(
        height=height,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def get_time_ago(timestamp):
    """Calcula tempo decorrido desde um timestamp"""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} dia{'s' if diff.days > 1 else ''} atrás"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hora{'s' if hours > 1 else ''} atrás"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minuto{'s' if minutes > 1 else ''} atrás"
    else:
        return "Agora mesmo"

def get_activity_icon(activity_type):
    """Retorna ícone baseado no tipo de atividade"""
    icons = {
        'login': '🔐',
        'event': '📅',
        'content': '📝',
        'member': '👤',
        'communication': '💬',
        'attendance': '✅',
        'admin': '⚙️',
        'default': '📊'
    }
    return icons.get(activity_type, icons['default'])

# Estilo e animação em HTML + CSS + JS
def typing_effect(text: str, tag: str = "h3", delay=50, width="auto"):
    html = f"""
    <div style="width: {width}; overflow-wrap: break-word;">
        <{tag} id="typewriter"></{tag}>
    </div>

    <script>
    const text = `{text}`;
    const element = document.getElementById("typewriter");
    let i = 0;

    function typeWriter() {{
        if (i < text.length) {{
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(typeWriter, {delay});
        }}
    }}
    typeWriter();
    </script>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_weather_widget():
    """Renderiza widget de tempo local para Palmas-TO"""
    from app.config.timezone import get_local_time
    
    current_time = get_local_time()
    
    with st.container():
        typing_effect("🌤️ Palmas - TO", tag="h2", delay=50, width="500px")  # ou "100%", "50vw", etc.

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Horário Local", current_time.strftime('%H:%M'))

        with col2:
            st.metric("Data", current_time.strftime('%d/%m'))


        locale.setlocale(locale.LC_TIME, 'pt_BR')
        # Data atual
        current_time = datetime.now()

        # Dia da semana em português
        st.info(f"📅 {current_time.strftime('%A').title()}")

def render_calendar_widget(events):
    """Renderiza widget de calendário com próximos eventos"""
    st.markdown("""
    <div style="
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 10px 0;
    ">
        <h4 style="margin-bottom: 15px; color: #333;">📅 Próximos Eventos</h4>
    """, unsafe_allow_html=True)
    
    if not events:
        st.markdown("<p style='color: #666; text-align: center;'>Nenhum evento próximo</p>", 
                   unsafe_allow_html=True)
    else:
        for event in events[:3]:  # Mostrar apenas os 3 próximos
            date_str = event.get('date', 'Data não definida')
            st.markdown(f"""
            <div style="
                padding: 10px;
                margin: 5px 0;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 3px solid #667eea;
            ">
                <div style="font-weight: bold; color: #333;">{event.get('title', 'Evento')}</div>
                <div style="color: #666; font-size: 0.9rem;">{date_str}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)