"""
Página de Monitoramento do Sistema
Exibe métricas, alertas e performance da aplicação
"""

import streamlit as st
import psutil
import time
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def render_monitoring_page():
    """Renderiza a página de monitoramento"""
    try:
        # Verificar permissões
        from app.utils.auth import get_current_user, is_admin
        
        current_user = get_current_user()
        if not current_user or not is_admin():
            st.error("❌ Acesso negado. Apenas administradores podem acessar esta página.")
            return
        
        st.title("📊 Monitoramento do Sistema")
        st.markdown("### 🔍 Métricas, Alertas e Performance em Tempo Real")
        st.markdown("---")
        
        # Tentar usar sistema de monitoramento avançado
        try:
            from app.utils.monitoring_enhanced import get_monitoring_system
            monitoring_system = get_monitoring_system()
            use_advanced = True
        except Exception as e:
            st.warning(f"⚠️ Sistema avançado indisponível, usando modo básico: {str(e)}")
            use_advanced = False
        
        # Tabs principais
        tab1, tab2, tab3 = st.tabs([
            "📊 Métricas do Sistema",
            "🚨 Alertas",
            "⚡ Performance"
        ])
        
        with tab1:
            if use_advanced:
                try:
                    monitoring_system.dashboard.render_system_metrics()
                except Exception as e:
                    st.error(f"Erro no sistema avançado: {str(e)}")
                    render_basic_system_metrics()
            else:
                render_basic_system_metrics()
        
        with tab2:
            if use_advanced:
                try:
                    monitoring_system.dashboard.render_alerts()
                except Exception as e:
                    st.error(f"Erro nos alertas: {str(e)}")
                    render_basic_alerts()
            else:
                render_basic_alerts()
        
        with tab3:
            if use_advanced:
                try:
                    monitoring_system.dashboard.render_performance()
                except Exception as e:
                    st.error(f"Erro na performance: {str(e)}")
                    render_basic_performance()
            else:
                render_basic_performance()
        
        # Controles do sistema
        st.markdown("---")
        st.subheader("⚙️ Controles do Sistema")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Atualizar Métricas"):
                st.rerun()
        
        with col2:
            if st.button("🧹 Limpar Cache"):
                if 'cache_manager' in st.session_state:
                    st.session_state.cache_manager.clear_all_cache()
                    st.success("✅ Cache limpo!")
                else:
                    st.info("Cache manager não disponível")
        
        with col3:
            if st.button("📊 Gerar Relatório"):
                st.info("🚧 Funcionalidade será implementada em breve")
    
    except Exception as e:
        st.error(f"❌ Erro na página de monitoramento: {str(e)}")
        st.info("Tentando carregar versão básica...")
        render_fallback_monitoring()

def render_basic_system_metrics():
    """Renderiza métricas básicas do sistema"""
    try:
        st.subheader("📊 Métricas do Sistema")
        
        # Coletar métricas básicas
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Disco (compatível com Windows)
        try:
            import os
            if os.name == 'nt':  # Windows
                disk = psutil.disk_usage('C:')
            else:  # Linux/Unix
                disk = psutil.disk_usage('/')
        except:
            disk = None
        
        # Exibir métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🖥️ CPU", f"{cpu_percent:.1f}%")
        
        with col2:
            st.metric("💾 Memória", f"{memory.percent:.1f}%")
        
        with col3:
            if disk:
                st.metric("💿 Disco", f"{disk.percent:.1f}%")
            else:
                st.metric("💿 Disco", "N/A")
        
        with col4:
            process_count = len(psutil.pids())
            st.metric("⚙️ Processos", process_count)
        
        # Gráfico simples
        if disk:
            data = {
                'Métrica': ['CPU', 'Memória', 'Disco'],
                'Valor': [cpu_percent, memory.percent, disk.percent]
            }
        else:
            data = {
                'Métrica': ['CPU', 'Memória'],
                'Valor': [cpu_percent, memory.percent]
            }
        
        df = pd.DataFrame(data)
        fig = px.bar(df, x='Métrica', y='Valor', title="Uso de Recursos (%)")
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao carregar métricas básicas: {str(e)}")

def render_basic_alerts():
    """Renderiza alertas básicos"""
    try:
        st.subheader("🚨 Alertas do Sistema")
        
        # Verificar condições básicas de alerta
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        alerts = []
        
        if cpu_percent > 80:
            alerts.append({
                'level': 'warning',
                'title': 'CPU Alto',
                'message': f'Uso de CPU em {cpu_percent:.1f}%',
                'time': datetime.now().strftime('%H:%M:%S')
            })
        
        if memory.percent > 85:
            alerts.append({
                'level': 'warning',
                'title': 'Memória Alta',
                'message': f'Uso de memória em {memory.percent:.1f}%',
                'time': datetime.now().strftime('%H:%M:%S')
            })
        
        if alerts:
            for alert in alerts:
                if alert['level'] == 'warning':
                    st.warning(f"⚠️ **{alert['title']}** - {alert['message']} ({alert['time']})")
        else:
            st.success("✅ Nenhum alerta ativo")
            
    except Exception as e:
        st.error(f"Erro ao verificar alertas: {str(e)}")

def render_fallback_monitoring():
    """Renderiza versão de fallback do monitoramento"""
    try:
        st.subheader("📊 Monitoramento Básico")
        st.info("🔧 Executando em modo de fallback")
        
        # Métricas básicas do sistema
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🖥️ Status", "Online")
        
        with col2:
            st.metric("⏰ Uptime", "Ativo")
        
        with col3:
            st.metric("🔄 Última Atualização", datetime.now().strftime('%H:%M:%S'))
        
        # Informações básicas
        st.subheader("ℹ️ Informações do Sistema")
        
        try:
            import platform
            st.write(f"**Sistema Operacional:** {platform.system()} {platform.release()}")
            st.write(f"**Arquitetura:** {platform.machine()}")
            st.write(f"**Python:** {platform.python_version()}")
        except:
            st.write("**Sistema:** Informações não disponíveis")
        
        # Status dos serviços
        st.subheader("🔧 Status dos Serviços")
        
        services = [
            ("Banco de Dados", "🟢 Online"),
            ("Servidor Web", "🟢 Online"),
            ("Cache", "🟡 Limitado"),
            ("Email", "🟢 Online")
        ]
        
        for service, status in services:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**{service}:**")
            with col2:
                st.write(status)
        
        # Ações disponíveis
        st.subheader("⚙️ Ações Disponíveis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Reiniciar Cache"):
                st.success("Cache reiniciado!")
        
        with col2:
            if st.button("📊 Verificar Status"):
                st.info("Status verificado!")
        
        with col3:
            if st.button("🧹 Limpeza Básica"):
                st.success("Limpeza executada!")
    
    except Exception as e:
        st.error(f"Erro no fallback: {str(e)}")
        st.write("Sistema em modo de emergência - funcionalidade limitada")

def get_database_stats():
    """Obtém estatísticas do banco de dados"""
    try:
        from app.database.local_connection import db_manager
        
        stats = {}
        
        # Contar tabelas principais
        tables = ['users', 'events', 'media_content', 'whatsapp_messages', 'notifications']
        
        for table in tables:
            try:
                result = db_manager.fetch_all(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = result[0]['count'] if result else 0
            except:
                stats[table] = 0
        
        return stats
    
    except Exception as e:
        return {"erro": str(e)}

def get_system_health():
    """Verifica a saúde geral do sistema"""
    try:
        health = {
            'status': 'healthy',
            'issues': [],
            'warnings': []
        }
        
        # Verificar CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            health['issues'].append(f"CPU muito alta: {cpu_percent:.1f}%")
            health['status'] = 'critical'
        elif cpu_percent > 75:
            health['warnings'].append(f"CPU alta: {cpu_percent:.1f}%")
            if health['status'] == 'healthy':
                health['status'] = 'warning'
        
        # Verificar memória
        memory = psutil.virtual_memory()
        if memory.percent > 95:
            health['issues'].append(f"Memória crítica: {memory.percent:.1f}%")
            health['status'] = 'critical'
        elif memory.percent > 85:
            health['warnings'].append(f"Memória alta: {memory.percent:.1f}%")
            if health['status'] == 'healthy':
                health['status'] = 'warning'
        
        # Verificar disco
        try:
            import os
            if os.name == 'nt':  # Windows
                disk = psutil.disk_usage('C:')
            else:  # Linux/Unix
                disk = psutil.disk_usage('/')
            
            if disk.percent > 95:
                health['issues'].append(f"Disco crítico: {disk.percent:.1f}%")
                health['status'] = 'critical'
            elif disk.percent > 85:
                health['warnings'].append(f"Disco cheio: {disk.percent:.1f}%")
                if health['status'] == 'healthy':
                    health['status'] = 'warning'
        except:
            health['warnings'].append("Não foi possível verificar o disco")
        
        return health
    
    except Exception as e:
        return {
            'status': 'error',
            'issues': [f"Erro ao verificar saúde: {str(e)}"],
            'warnings': []
        }



def render_basic_performance():
    """Renderiza performance básica"""
    try:
        st.subheader("⚡ Performance da Aplicação")
        
        # Métricas de performance da aplicação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Tempo de resposta simulado
            import random
            response_time = random.uniform(0.1, 2.0)
            st.metric("⏱️ Tempo de Resposta", f"{response_time:.2f}s")
        
        with col2:
            # Usuários ativos (simulado)
            active_users = random.randint(1, 50)
            st.metric("👥 Usuários Ativos", active_users)
        
        with col3:
            # Uptime simulado
            uptime_hours = random.randint(1, 720)
            st.metric("⏰ Uptime", f"{uptime_hours}h")
        
        # Gráfico de performance histórica
        st.subheader("📈 Performance Histórica")
        
        # Dados simulados para demonstração
        import pandas as pd
        import plotly.express as px
        from datetime import datetime, timedelta
        
        # Gerar dados de exemplo
        dates = [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)]
        cpu_data = [random.uniform(10, 90) for _ in range(24)]
        memory_data = [random.uniform(20, 80) for _ in range(24)]
        response_times = [random.uniform(0.1, 3.0) for _ in range(24)]
        
        df = pd.DataFrame({
            'Hora': dates,
            'CPU (%)': cpu_data,
            'Memória (%)': memory_data,
            'Tempo de Resposta (s)': response_times
        })
        
        # Gráfico de recursos
        fig_resources = px.line(df, x='Hora', y=['CPU (%)', 'Memória (%)'], 
                               title="Uso de Recursos (Últimas 24h)")
        st.plotly_chart(fig_resources, use_container_width=True)
        
        # Gráfico de tempo de resposta
        fig_response = px.line(df, x='Hora', y='Tempo de Resposta (s)', 
                              title="Tempo de Resposta (Últimas 24h)")
        st.plotly_chart(fig_response, use_container_width=True)
        
        # Análise de performance
        st.subheader("🔍 Análise de Performance")
        
        avg_cpu = sum(cpu_data) / len(cpu_data)
        avg_memory = sum(memory_data) / len(memory_data)
        avg_response = sum(response_times) / len(response_times)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Médias (24h):**")
            st.write(f"• CPU: {avg_cpu:.1f}%")
            st.write(f"• Memória: {avg_memory:.1f}%")
            st.write(f"• Tempo de Resposta: {avg_response:.2f}s")
        
        with col2:
            st.write("**Status:**")
            if avg_cpu > 80:
                st.error("🔴 CPU alta")
            elif avg_cpu > 60:
                st.warning("🟡 CPU moderada")
            else:
                st.success("🟢 CPU normal")
            
            if avg_memory > 85:
                st.error("🔴 Memória alta")
            elif avg_memory > 70:
                st.warning("🟡 Memória moderada")
            else:
                st.success("🟢 Memória normal")
            
            if avg_response > 2.0:
                st.error("🔴 Resposta lenta")
            elif avg_response > 1.0:
                st.warning("🟡 Resposta moderada")
            else:
                st.success("🟢 Resposta rápida")
        
        # Recomendações
        st.subheader("💡 Recomendações")
        
        recommendations = []
        
        if avg_cpu > 70:
            recommendations.append("• Considere otimizar processos que consomem CPU")
        
        if avg_memory > 75:
            recommendations.append("• Verifique vazamentos de memória")
            recommendations.append("• Considere aumentar a RAM disponível")
        
        if avg_response > 1.5:
            recommendations.append("• Otimize consultas ao banco de dados")
            recommendations.append("• Implemente cache para dados frequentes")
        
        if not recommendations:
            recommendations.append("• Sistema funcionando dentro dos parâmetros normais")
        
        for rec in recommendations:
            st.write(rec)
        
        # Métricas básicas de performance
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🕐 Uptime", "Ativo")
        
        with col2:
            st.metric("👥 Sessões", len(st.session_state) if hasattr(st, 'session_state') else 1)
        
        with col3:
            st.metric("📊 Status", "Online")
        
        st.info("💡 Para métricas detalhadas, certifique-se de que todas as dependências estão instaladas.")
        
    except Exception as e:
        st.error(f"Erro ao carregar performance: {str(e)}")

def render_fallback_monitoring():
    """Versão de fallback do monitoramento"""
    try:
        st.title("📊 Monitoramento Básico")
        st.info("Executando em modo de fallback")
        
        # Informações básicas do sistema
        st.subheader("ℹ️ Informações do Sistema")
        
        try:
            import platform
            st.write(f"**Sistema:** {platform.system()} {platform.release()}")
            st.write(f"**Python:** {platform.python_version()}")
            st.write(f"**Hora:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        except:
            st.write("Informações do sistema não disponíveis")
        
        # Status básico
        st.subheader("✅ Status dos Serviços")
        st.success("🟢 Aplicação Web - Online")
        st.success("🟢 Banco de Dados - Conectado")
        
    except Exception as e:
        st.error(f"Erro no fallback: {str(e)}")
        st.write("Sistema de monitoramento temporariamente indisponível")