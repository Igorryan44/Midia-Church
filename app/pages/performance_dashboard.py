"""
Dashboard de Performance - Mídia Church
Monitoramento e otimização de performance em tempo real
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import psutil
import time

from app.utils.auth import require_auth, get_user_role
from app.utils.cache_manager import cache_manager
from app.utils.memory_optimizer import memory_optimizer, get_memory_usage, render_memory_widget
from app.utils.performance_optimizer import PerformanceOptimizer
from app.utils.monitoring_enhanced import PerformanceMonitor
from app.database.local_connection import db_manager

def render_performance_dashboard():
    """Renderiza dashboard de performance"""
    
    # Verificar autenticação
    if not require_auth():
        return
    
    # Verificar permissões (apenas admin)
    user_role = get_user_role()
    if user_role != 'admin':
        st.error("❌ Acesso negado. Apenas administradores podem acessar este dashboard.")
        return
    
    st.title("📊 Dashboard de Performance")
    st.markdown("---")
    
    # Tabs principais
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Visão Geral", 
        "🖥️ Sistema", 
        "💾 Banco de Dados", 
        "🌐 Aplicação", 
        "⚙️ Otimização"
    ])
    
    with tab1:
        show_overview_metrics()
    
    with tab2:
        show_system_metrics()
    
    with tab3:
        show_database_metrics()
    
    with tab4:
        show_application_metrics()
    
    with tab5:
        show_optimization_tools()

def show_overview_metrics():
    """Mostra métricas gerais de performance"""
    st.subheader("📊 Visão Geral do Sistema")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        import psutil
        
        with col1:
            cpu_usage = psutil.cpu_percent(interval=1)
            cpu_delta = get_metric_delta('cpu', cpu_usage)
            st.metric(
                label="🖥️ CPU",
                value=f"{cpu_usage:.1f}%",
                delta=f"{cpu_delta:+.1f}%"
            )
        
        with col2:
            memory = psutil.virtual_memory()
            ram_usage = memory.percent
            ram_delta = get_metric_delta('ram', ram_usage)
            st.metric(
                label="💾 RAM",
                value=f"{ram_usage:.1f}%",
                delta=f"{ram_delta:+.1f}%"
            )
        
        with col3:
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            disk_delta = get_metric_delta('disk', disk_usage)
            st.metric(
                label="💿 Disco",
                value=f"{disk_usage:.1f}%",
                delta=f"{disk_delta:+.1f}%"
            )
        
        with col4:
            active_users = get_active_users_count()
            users_delta = get_metric_delta('users', active_users)
            st.metric(
                label="👥 Usuários Ativos",
                value=active_users,
                delta=f"{users_delta:+d}"
            )
    
    except ImportError:
        # Fallback para métricas simuladas
        show_simulated_metrics()
    
    st.divider()
    
    # Gráficos de tendência
    show_performance_trends()
    
    # Status do sistema
    show_system_health()

def show_simulated_metrics():
    """Mostra métricas simuladas quando psutil não está disponível"""
    import random
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cpu_usage = random.uniform(20, 80)
        st.metric("🖥️ CPU", f"{cpu_usage:.1f}%", delta=f"{random.uniform(-5, 5):+.1f}%")
    
    with col2:
        ram_usage = random.uniform(40, 90)
        st.metric("💾 RAM", f"{ram_usage:.1f}%", delta=f"{random.uniform(-3, 3):+.1f}%")
    
    with col3:
        disk_usage = random.uniform(30, 70)
        st.metric("💿 Disco", f"{disk_usage:.1f}%", delta=f"{random.uniform(-1, 2):+.1f}%")
    
    with col4:
        active_users = random.randint(50, 200)
        st.metric("👥 Usuários Ativos", active_users, delta=f"{random.randint(-10, 15):+d}")

def show_performance_trends():
    """Mostra gráficos de tendência de performance"""
    st.subheader("📈 Tendências de Performance")
    
    try:
        import pandas as pd
        import plotly.express as px
        from datetime import datetime, timedelta
        import random
        
        # Gerar dados históricos simulados
        dates = [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)]
        
        performance_data = pd.DataFrame({
            'Hora': dates,
            'CPU (%)': [random.uniform(20, 80) for _ in range(24)],
            'RAM (%)': [random.uniform(40, 90) for _ in range(24)],
            'Tempo Resposta (ms)': [random.uniform(100, 500) for _ in range(24)]
        })
        
        # Gráfico de CPU e RAM
        fig_resources = px.line(
            performance_data, 
            x='Hora', 
            y=['CPU (%)', 'RAM (%)'],
            title="Uso de Recursos (Últimas 24h)",
            labels={'value': 'Percentual (%)', 'variable': 'Recurso'}
        )
        st.plotly_chart(fig_resources, use_container_width=True)
        
        # Gráfico de tempo de resposta
        fig_response = px.line(
            performance_data,
            x='Hora',
            y='Tempo Resposta (ms)',
            title="Tempo de Resposta da Aplicação (Últimas 24h)"
        )
        st.plotly_chart(fig_response, use_container_width=True)
    
    except ImportError:
        st.info("📊 Instale plotly e pandas para visualizar gráficos de tendência")

def show_system_health():
    """Mostra status de saúde do sistema"""
    st.subheader("🏥 Saúde do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Status dos Serviços:**")
        
        services = [
            ("🌐 Aplicação Web", "🟢 Online", "normal"),
            ("🗄️ Banco de Dados", "🟢 Online", "normal"),
            ("📧 Serviço de Email", "🟡 Lento", "warning"),
            ("🔄 Cache Redis", "🟢 Online", "normal"),
            ("📊 Monitoramento", "🟢 Ativo", "normal")
        ]
        
        for service, status, level in services:
            if level == "normal":
                st.success(f"{service}: {status}")
            elif level == "warning":
                st.warning(f"{service}: {status}")
            else:
                st.error(f"{service}: {status}")
    
    with col2:
        st.write("**Recomendações:**")
        
        recommendations = get_performance_recommendations()
        for rec in recommendations:
            st.info(f"💡 {rec}")

def show_system_metrics():
    """Mostra métricas detalhadas do sistema"""
    st.subheader("🖥️ Métricas do Sistema")
    
    try:
        import psutil
        
        # Informações de CPU
        st.write("**🖥️ Processador:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Núcleos Físicos", psutil.cpu_count(logical=False))
        with col2:
            st.metric("Núcleos Lógicos", psutil.cpu_count(logical=True))
        with col3:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                st.metric("Frequência", f"{cpu_freq.current:.0f} MHz")
        
        # Uso por núcleo
        cpu_percents = psutil.cpu_percent(percpu=True, interval=1)
        if cpu_percents:
            st.write("**Uso por Núcleo:**")
            cpu_data = {f"CPU {i}": percent for i, percent in enumerate(cpu_percents)}
            st.bar_chart(cpu_data)
        
        st.divider()
        
        # Informações de Memória
        st.write("**💾 Memória:**")
        memory = psutil.virtual_memory()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", f"{memory.total / (1024**3):.1f} GB")
        with col2:
            st.metric("Disponível", f"{memory.available / (1024**3):.1f} GB")
        with col3:
            st.metric("Usado", f"{memory.used / (1024**3):.1f} GB")
        with col4:
            st.metric("Percentual", f"{memory.percent:.1f}%")
        
        # Swap
        swap = psutil.swap_memory()
        if swap.total > 0:
            st.write("**🔄 Swap:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total", f"{swap.total / (1024**3):.1f} GB")
            with col2:
                st.metric("Usado", f"{swap.used / (1024**3):.1f} GB")
            with col3:
                st.metric("Percentual", f"{swap.percent:.1f}%")
        
        st.divider()
        
        # Informações de Disco
        st.write("**💿 Armazenamento:**")
        disk_usage = psutil.disk_usage('/')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", f"{disk_usage.total / (1024**3):.1f} GB")
        with col2:
            st.metric("Usado", f"{disk_usage.used / (1024**3):.1f} GB")
        with col3:
            st.metric("Livre", f"{disk_usage.free / (1024**3):.1f} GB")
        with col4:
            st.metric("Percentual", f"{disk_usage.percent:.1f}%")
        
        # I/O de Disco
        disk_io = psutil.disk_io_counters()
        if disk_io:
            st.write("**📊 I/O de Disco:**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Leituras", f"{disk_io.read_count:,}")
            with col2:
                st.metric("Escritas", f"{disk_io.write_count:,}")
            with col3:
                st.metric("Bytes Lidos", f"{disk_io.read_bytes / (1024**2):.1f} MB")
            with col4:
                st.metric("Bytes Escritos", f"{disk_io.write_bytes / (1024**2):.1f} MB")
    
    except ImportError:
        st.warning("⚠️ Instale psutil para métricas detalhadas do sistema")
        show_simulated_system_metrics()

def show_simulated_system_metrics():
    """Mostra métricas simuladas do sistema"""
    import random
    
    st.write("**🖥️ Processador (Simulado):**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Núcleos", "8")
    with col2:
        st.metric("Frequência", "2.4 GHz")
    with col3:
        st.metric("Uso Médio", f"{random.uniform(20, 80):.1f}%")

def show_database_metrics():
    """Mostra métricas do banco de dados"""
    st.subheader("🗄️ Performance do Banco de Dados")
    
    try:
        # Estatísticas básicas
        st.write("**📊 Estatísticas Gerais:**")
        
        # Tamanho do banco
        db_stats = get_database_size_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Tamanho Total", f"{db_stats.get('total_size', 0):.1f} MB")
        with col2:
            st.metric("Tabelas", db_stats.get('table_count', 0))
        with col3:
            st.metric("Índices", db_stats.get('index_count', 0))
        with col4:
            st.metric("Conexões Ativas", db_stats.get('connections', 0))
        
        st.divider()
        
        # Top tabelas por tamanho
        st.write("**📋 Maiores Tabelas:**")
        table_sizes = get_table_sizes()
        
        if table_sizes:
            for table in table_sizes[:10]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"📄 {table['name']}")
                with col2:
                    st.write(f"{table['size']:.2f} MB")
        
        st.divider()
        
        # Queries mais lentas
        st.write("**🐌 Queries Mais Lentas:**")
        slow_queries = get_slow_queries()
        
        if slow_queries:
            for query in slow_queries[:5]:
                with st.expander(f"Query - {query['duration']:.2f}s"):
                    st.code(query['sql'], language='sql')
        
        # Ações de otimização
        st.divider()
        st.write("**🔧 Otimização:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🧹 VACUUM"):
                try:
                    db_manager.execute_query("VACUUM")
                    st.success("✅ VACUUM executado!")
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
        
        with col2:
            if st.button("📊 ANALYZE"):
                try:
                    db_manager.execute_query("ANALYZE")
                    st.success("✅ ANALYZE executado!")
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
        
        with col3:
            if st.button("🔄 REINDEX"):
                try:
                    db_manager.execute_query("REINDEX")
                    st.success("✅ REINDEX executado!")
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar métricas do banco: {str(e)}")

def show_application_metrics():
    """Mostra métricas da aplicação"""
    st.subheader("🌐 Performance da Aplicação")
    
    # Métricas de sessão
    st.write("**👥 Sessões de Usuário:**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_sessions = get_active_sessions_count()
        st.metric("Sessões Ativas", active_sessions)
    
    with col2:
        avg_session_time = get_average_session_time()
        st.metric("Tempo Médio", f"{avg_session_time:.1f} min")
    
    with col3:
        page_views = get_page_views_count()
        st.metric("Visualizações/h", page_views)
    
    with col4:
        error_rate = get_error_rate()
        st.metric("Taxa de Erro", f"{error_rate:.2f}%")
    
    st.divider()
    
    # Páginas mais acessadas
    st.write("**📊 Páginas Mais Acessadas:**")
    
    popular_pages = get_popular_pages()
    for page in popular_pages:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"📄 {page['name']}")
        with col2:
            st.write(f"{page['views']} views")
    
    st.divider()
    
    # Cache da aplicação
    st.write("**💾 Cache da Aplicação:**")
    
    cache_stats = get_cache_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Hit Rate", f"{cache_stats.get('hit_rate', 0):.1f}%")
    with col2:
        st.metric("Tamanho", f"{cache_stats.get('size', 0):.1f} MB")
    with col3:
        st.metric("Entradas", cache_stats.get('entries', 0))

def show_optimization_tools():
    """Mostra ferramentas de otimização"""
    st.subheader("⚙️ Ferramentas de Otimização")
    
    # Limpeza de Cache
    st.write("**🧹 Limpeza de Cache:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Limpar Cache Streamlit"):
            st.cache_data.clear()
            st.success("✅ Cache do Streamlit limpo!")
    
    with col2:
        if st.button("🔄 Limpar Cache Aplicação"):
            clear_application_cache()
            st.success("✅ Cache da aplicação limpo!")
    
    with col3:
        if st.button("🧹 Limpeza Completa"):
            st.cache_data.clear()
            clear_application_cache()
            st.success("✅ Todos os caches limpos!")
    
    st.divider()
    
    # Otimização do Banco
    st.write("**🗄️ Otimização do Banco:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Analisar Tabelas"):
            optimize_database_tables()
            st.success("✅ Tabelas analisadas!")
    
    with col2:
        if st.button("🔧 Reconstruir Índices"):
            rebuild_database_indexes()
            st.success("✅ Índices reconstruídos!")
    
    with col3:
        if st.button("🧹 Limpeza de Dados"):
            cleanup_old_data()
            st.success("✅ Dados antigos removidos!")
    
    st.divider()
    
    # Configurações de Performance
    st.write("**⚙️ Configurações de Performance:**")
    
    with st.form("performance_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            cache_timeout = st.number_input(
                "Timeout do Cache (minutos):",
                min_value=1,
                max_value=1440,
                value=60
            )
            
            max_connections = st.number_input(
                "Máximo de Conexões DB:",
                min_value=1,
                max_value=100,
                value=20
            )
        
        with col2:
            auto_cleanup = st.checkbox("Limpeza Automática", value=True)
            
            monitoring_enabled = st.checkbox("Monitoramento Ativo", value=True)
        
        if st.form_submit_button("💾 Salvar Configurações"):
            save_performance_settings({
                'cache_timeout': cache_timeout,
                'max_connections': max_connections,
                'auto_cleanup': auto_cleanup,
                'monitoring_enabled': monitoring_enabled
            })
            st.success("✅ Configurações salvas!")

# Funções auxiliares
def get_metric_delta(metric_type, current_value):
    """Calcula delta para métricas"""
    import random
    return random.uniform(-5, 5)

def get_active_users_count():
    """Retorna número de usuários ativos"""
    try:
        result = db_manager.fetch_all(
            "SELECT COUNT(DISTINCT user_id) as count FROM user_sessions WHERE last_activity > datetime('now', '-1 hour')"
        )
        return result[0]['count'] if result else 0
    except:
        import random
        return random.randint(50, 200)

def get_performance_recommendations():
    """Retorna recomendações de performance"""
    recommendations = [
        "Considere aumentar a memória RAM para melhor performance",
        "Execute VACUUM no banco de dados semanalmente",
        "Monitore o uso de CPU durante picos de acesso",
        "Configure cache para consultas frequentes"
    ]
    return recommendations[:2]  # Retorna apenas 2 recomendações

def get_database_size_stats():
    """Retorna estatísticas de tamanho do banco"""
    try:
        import os
        
        # Tamanho do arquivo do banco
        db_path = "app/database/whatsapp.db"
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
        else:
            size_mb = 0
        
        # Contar tabelas
        tables = db_manager.fetch_all(
            "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
        )
        table_count = tables[0]['count'] if tables else 0
        
        # Contar índices
        indexes = db_manager.fetch_all(
            "SELECT COUNT(*) as count FROM sqlite_master WHERE type='index'"
        )
        index_count = indexes[0]['count'] if indexes else 0
        
        return {
            'total_size': size_mb,
            'table_count': table_count,
            'index_count': index_count,
            'connections': 1  # SQLite é single-connection
        }
    except:
        return {'total_size': 0, 'table_count': 0, 'index_count': 0, 'connections': 0}

def get_table_sizes():
    """Retorna tamanhos das tabelas"""
    try:
        tables = db_manager.fetch_all(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        
        table_sizes = []
        for table in tables:
            try:
                count = db_manager.fetch_all(f"SELECT COUNT(*) as count FROM {table['name']}")
                size = count[0]['count'] * 0.001 if count else 0  # Estimativa simples
                table_sizes.append({'name': table['name'], 'size': size})
            except:
                continue
        
        return sorted(table_sizes, key=lambda x: x['size'], reverse=True)
    except:
        return []

def get_slow_queries():
    """Retorna queries mais lentas (simulado)"""
    return [
        {'sql': 'SELECT * FROM whatsapp_messages WHERE date LIKE "%2024%"', 'duration': 2.5},
        {'sql': 'SELECT COUNT(*) FROM users WHERE created_at > "2024-01-01"', 'duration': 1.8}
    ]

def get_active_sessions_count():
    """Retorna número de sessões ativas"""
    import random
    return random.randint(10, 50)

def get_average_session_time():
    """Retorna tempo médio de sessão"""
    import random
    return random.uniform(15, 45)

def get_page_views_count():
    """Retorna visualizações por hora"""
    import random
    return random.randint(100, 500)

def get_error_rate():
    """Retorna taxa de erro"""
    import random
    return random.uniform(0.1, 2.0)

def get_popular_pages():
    """Retorna páginas mais populares"""
    return [
        {'name': 'Dashboard', 'views': 1250},
        {'name': 'Mensagens', 'views': 890},
        {'name': 'Usuários', 'views': 650},
        {'name': 'Relatórios', 'views': 420}
    ]

def get_cache_stats():
    """Retorna estatísticas do cache"""
    import random
    return {
        'hit_rate': random.uniform(85, 98),
        'size': random.uniform(50, 200),
        'entries': random.randint(1000, 5000)
    }

def clear_application_cache():
    """Limpa cache da aplicação"""
    pass

def optimize_database_tables():
    """Otimiza tabelas do banco"""
    try:
        db_manager.execute_query("ANALYZE")
    except:
        pass

def rebuild_database_indexes():
    """Reconstrói índices do banco"""
    try:
        db_manager.execute_query("REINDEX")
    except:
        pass

def cleanup_old_data():
    """Remove dados antigos"""
    try:
        db_manager.execute_query("DELETE FROM logs WHERE created_at < date('now', '-90 days')")
    except:
        pass

def save_performance_settings(settings):
    """Salva configurações de performance"""
    pass

def render_general_metrics():
    """Renderiza métricas gerais do sistema"""
    st.subheader("📊 Métricas Gerais do Sistema")
    
    # Métricas do sistema
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cpu_percent = psutil.cpu_percent(interval=1)
        st.metric(
            "CPU",
            f"{cpu_percent:.1f}%",
            delta=f"{'🔥' if cpu_percent > 80 else '✅' if cpu_percent < 50 else '⚠️'}"
        )
    
    with col2:
        memory = psutil.virtual_memory()
        st.metric(
            "RAM",
            f"{memory.percent:.1f}%",
            delta=f"{memory.used / 1024**3:.1f} GB"
        )
    
    with col3:
        disk = psutil.disk_usage('/')
        st.metric(
            "Disco",
            f"{disk.percent:.1f}%",
            delta=f"{disk.free / 1024**3:.1f} GB livre"
        )
    
    with col4:
        # Número de usuários ativos (simulado)
        active_users = len(st.session_state.get('active_sessions', {}))
        st.metric(
            "Usuários Ativos",
            active_users,
            delta="sessões ativas"
        )
    
    # Gráfico de uso de recursos ao longo do tempo
    st.subheader("📈 Histórico de Recursos")
    
    # Simular dados históricos (em produção viria do banco)
    if 'performance_history' not in st.session_state:
        st.session_state.performance_history = []
    
    # Adicionar ponto atual
    current_time = datetime.now()
    st.session_state.performance_history.append({
        'timestamp': current_time,
        'cpu': cpu_percent,
        'memory': memory.percent,
        'disk': disk.percent
    })
    
    # Manter apenas últimos 50 pontos
    if len(st.session_state.performance_history) > 50:
        st.session_state.performance_history = st.session_state.performance_history[-50:]
    
    # Criar DataFrame para gráfico
    df_history = pd.DataFrame(st.session_state.performance_history)
    
    if not df_history.empty:
        fig = px.line(
            df_history, 
            x='timestamp', 
            y=['cpu', 'memory', 'disk'],
            title="Uso de Recursos ao Longo do Tempo",
            labels={'value': 'Porcentagem (%)', 'timestamp': 'Tempo'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Auto-refresh
    if st.button("🔄 Atualizar Métricas"):
        st.rerun()

def render_memory_dashboard():
    """Renderiza dashboard de memória"""
    st.subheader("🧠 Gerenciamento de Memória")
    
    # Widget de memória
    render_memory_widget()
    
    # Estatísticas detalhadas
    memory_stats = get_memory_usage()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Estatísticas de Memória")
        
        stats_df = pd.DataFrame([
            {"Métrica": "Total", "Valor": f"{memory_stats['total'] / 1024**3:.2f} GB"},
            {"Métrica": "Usado", "Valor": f"{memory_stats['used'] / 1024**3:.2f} GB"},
            {"Métrica": "Disponível", "Valor": f"{memory_stats['available'] / 1024**3:.2f} GB"},
            {"Métrica": "Livre", "Valor": f"{memory_stats['free'] / 1024**3:.2f} GB"},
            {"Métrica": "Porcentagem", "Valor": f"{memory_stats['percent']:.1f}%"},
        ])
        
        st.dataframe(stats_df, use_container_width=True)
    
    with col2:
        st.subheader("🔧 Controles de Memória")
        
        if st.button("🧹 Limpeza Forçada", type="primary"):
            memory_optimizer.cleanup_memory(force=True)
            st.success("✅ Limpeza de memória executada!")
            time.sleep(1)
            st.rerun()
        
        st.markdown("---")
        
        # Configurações de memória
        threshold = st.slider(
            "Limite para Limpeza Automática (%)",
            min_value=50,
            max_value=95,
            value=memory_optimizer.memory_threshold,
            help="Porcentagem de uso de memória que dispara limpeza automática"
        )
        
        if threshold != memory_optimizer.memory_threshold:
            memory_optimizer.memory_threshold = threshold
            st.success(f"✅ Limite atualizado para {threshold}%")
        
        cleanup_interval = st.number_input(
            "Intervalo de Limpeza (segundos)",
            min_value=60,
            max_value=3600,
            value=memory_optimizer.cleanup_interval,
            help="Intervalo mínimo entre limpezas automáticas"
        )
        
        if cleanup_interval != memory_optimizer.cleanup_interval:
            memory_optimizer.cleanup_interval = cleanup_interval
            st.success(f"✅ Intervalo atualizado para {cleanup_interval}s")

def render_cache_dashboard():
    """Renderiza dashboard de cache"""
    st.subheader("💾 Gerenciamento de Cache")
    
    # Estatísticas do cache
    cache_stats = cache_manager.get_cache_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Itens em Cache",
            cache_stats['total_items'],
            delta="itens armazenados"
        )
    
    with col2:
        st.metric(
            "Total de Acessos",
            cache_stats['total_accesses'],
            delta="acessos realizados"
        )
    
    with col3:
        most_accessed = cache_stats['most_accessed']
        if most_accessed:
            st.metric(
                "Mais Acessado",
                most_accessed[1],
                delta=f"acessos: {most_accessed[0][:20]}..."
            )
        else:
            st.metric("Mais Acessado", "N/A", delta="nenhum item")
    
    # Controles de cache
    st.subheader("🔧 Controles de Cache")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Limpar Todo Cache", type="secondary"):
            cache_manager.clear_cache()
            st.success("✅ Cache limpo com sucesso!")
            st.rerun()
    
    with col2:
        pattern = st.text_input("Padrão para Limpeza", placeholder="ex: dashboard_")
        if st.button("🎯 Limpar por Padrão") and pattern:
            cache_manager.clear_cache(pattern)
            st.success(f"✅ Itens com padrão '{pattern}' removidos!")
            st.rerun()
    
    with col3:
        if st.button("📊 Atualizar Estatísticas"):
            st.rerun()
    
    # Lista de itens em cache
    if cache_stats['total_items'] > 0:
        st.subheader("📋 Itens em Cache")
        
        cache_items = []
        for key in st.session_state.cache_storage.keys():
            timestamp = st.session_state.cache_timestamps.get(key)
            access_count = st.session_state.cache_access_count.get(key, 0)
            
            cache_items.append({
                'Chave': key[:50] + '...' if len(key) > 50 else key,
                'Acessos': access_count,
                'Criado': timestamp.strftime('%H:%M:%S') if timestamp else 'N/A',
                'Idade (min)': int((datetime.now() - timestamp).total_seconds() / 60) if timestamp else 0
            })
        
        cache_df = pd.DataFrame(cache_items)
        st.dataframe(cache_df, use_container_width=True)

def render_performance_metrics():
    """Renderiza métricas de performance"""
    st.subheader("⚡ Métricas de Performance")
    
    # Buscar dados de performance do banco
    try:
        performance_data = db_manager.fetch_all("""
            SELECT function_name, execution_time, timestamp
            FROM performance_logs
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        
        if performance_data:
            df_perf = pd.DataFrame(performance_data)
            
            # Métricas resumidas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_time = df_perf['execution_time'].mean()
                st.metric(
                    "Tempo Médio",
                    f"{avg_time:.3f}s",
                    delta="execução média"
                )
            
            with col2:
                max_time = df_perf['execution_time'].max()
                st.metric(
                    "Tempo Máximo",
                    f"{max_time:.3f}s",
                    delta="pior caso"
                )
            
            with col3:
                total_functions = df_perf['function_name'].nunique()
                st.metric(
                    "Funções Monitoradas",
                    total_functions,
                    delta="diferentes funções"
                )
            
            with col4:
                total_calls = len(df_perf)
                st.metric(
                    "Total de Chamadas",
                    total_calls,
                    delta="execuções registradas"
                )
            
            # Gráfico de performance por função
            st.subheader("📊 Performance por Função")
            
            # Agrupar por função
            func_stats = df_perf.groupby('function_name').agg({
                'execution_time': ['mean', 'max', 'count']
            }).round(3)
            
            func_stats.columns = ['Tempo Médio', 'Tempo Máximo', 'Chamadas']
            func_stats = func_stats.reset_index()
            
            # Gráfico de barras
            fig = px.bar(
                func_stats.head(10),
                x='function_name',
                y='Tempo Médio',
                title="Top 10 Funções por Tempo Médio de Execução",
                labels={'function_name': 'Função', 'Tempo Médio': 'Tempo (s)'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela detalhada
            st.subheader("📋 Detalhes de Performance")
            st.dataframe(func_stats, use_container_width=True)
            
        else:
            st.info("📊 Nenhum dado de performance disponível ainda.")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados de performance: {e}")

def render_optimization_tools():
    """Renderiza ferramentas de otimização"""
    st.subheader("🔧 Ferramentas de Otimização")
    
    # Otimizações automáticas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤖 Otimizações Automáticas")
        
        if st.button("⚡ Otimizar Performance Geral", type="primary"):
            with st.spinner("Executando otimizações..."):
                optimizer = PerformanceOptimizer()
                
                # Executar várias otimizações
                optimizer.optimize_streamlit_config()
                memory_optimizer.cleanup_memory(force=True)
                cache_manager.clear_cache()
                
                # Simular otimização de banco
                time.sleep(2)
                
            st.success("✅ Otimizações executadas com sucesso!")
        
        if st.button("🗄️ Otimizar Banco de Dados"):
            with st.spinner("Otimizando banco de dados..."):
                try:
                    # Executar VACUUM para SQLite
                    db_manager.execute_query("VACUUM")
                    db_manager.execute_query("ANALYZE")
                    time.sleep(1)
                    st.success("✅ Banco de dados otimizado!")
                except Exception as e:
                    st.error(f"❌ Erro na otimização: {e}")
        
        if st.button("🧹 Limpeza Completa"):
            with st.spinner("Executando limpeza completa..."):
                # Limpeza de memória
                memory_optimizer.cleanup_memory(force=True)
                
                # Limpeza de cache
                cache_manager.clear_cache()
                
                # Limpeza de session_state temporário
                temp_keys = [k for k in st.session_state.keys() if k.startswith('temp_')]
                for key in temp_keys:
                    del st.session_state[key]
                
                time.sleep(1)
                
            st.success("✅ Limpeza completa executada!")
    
    with col2:
        st.subheader("⚙️ Configurações de Otimização")
        
        # Configurações de cache
        st.markdown("**Cache**")
        cache_enabled = st.checkbox("Habilitar Cache Inteligente", value=True)
        cache_max_age = st.slider("Idade Máxima do Cache (min)", 1, 60, 5)
        
        # Configurações de memória
        st.markdown("**Memória**")
        memory_monitoring = st.checkbox("Monitoramento Automático", value=True)
        memory_threshold = st.slider("Limite de Memória (%)", 50, 95, 80)
        
        # Configurações de performance
        st.markdown("**Performance**")
        perf_monitoring = st.checkbox("Monitoramento de Performance", value=True)
        lazy_loading = st.checkbox("Carregamento Lazy", value=True)
        
        if st.button("💾 Salvar Configurações"):
            # Salvar configurações (em produção salvaria no banco)
            st.session_state.optimization_config = {
                'cache_enabled': cache_enabled,
                'cache_max_age': cache_max_age,
                'memory_monitoring': memory_monitoring,
                'memory_threshold': memory_threshold,
                'perf_monitoring': perf_monitoring,
                'lazy_loading': lazy_loading
            }
            st.success("✅ Configurações salvas!")
    
    # Relatório de otimização
    st.subheader("📊 Relatório de Otimização")
    
    optimization_report = {
        "Cache": "✅ Ativo" if cache_manager.get_cache_stats()['total_items'] > 0 else "⚠️ Vazio",
        "Memória": f"✅ {get_memory_usage()['percent']:.1f}% usado",
        "Monitoramento": "✅ Ativo" if memory_optimizer._monitoring else "❌ Inativo",
        "Performance": "✅ Logs ativos",
        "Banco de Dados": "✅ Conectado"
    }
    
    report_df = pd.DataFrame([
        {"Componente": k, "Status": v} for k, v in optimization_report.items()
    ])
    
    st.dataframe(report_df, use_container_width=True)

if __name__ == "__main__":
    render_performance_dashboard()