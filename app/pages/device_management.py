"""
Página de Gerenciamento de Dispositivos
Permite aos usuários visualizar e gerenciar dispositivos confiáveis
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text
from app.database.local_connection import db_manager
from app.utils.auth import check_authentication, get_device_fingerprint, get_client_ip
from app.utils.security_monitor import SecurityMonitor

def show_device_management():
    """Exibe a página de gerenciamento de dispositivos"""
    
    # Verificar autenticação
    if not check_authentication():
        st.error("❌ Acesso negado. Faça login para continuar.")
        return
    
    st.title("🔐 Gerenciamento de Dispositivos")
    st.markdown("---")
    
    # Obter informações do usuário atual
    user_id = st.session_state.user_info.get('id')
    current_device_fingerprint, current_user_agent = get_device_fingerprint()
    current_ip = get_client_ip()
    
    # Tabs para diferentes seções
    tab1, tab2, tab3 = st.tabs(["📱 Dispositivos Ativos", "🔒 Dispositivos Confiáveis", "📊 Histórico de Acesso"])
    
    with tab1:
        show_active_devices(user_id, current_device_fingerprint)
    
    with tab2:
        show_trusted_devices(user_id, current_device_fingerprint)
    
    with tab3:
        show_access_history(user_id)

def show_active_devices(user_id, current_device_fingerprint):
    """Mostra dispositivos com sessões ativas"""
    st.subheader("📱 Dispositivos com Sessões Ativas")
    
    try:
        with db_manager.get_db_session() as session:
            result = session.execute(
                text("""
                SELECT 
                    device_fingerprint,
                    user_agent,
                    ip_address,
                    created_at,
                    last_accessed,
                    is_trusted,
                    COUNT(*) as session_count
                FROM user_sessions 
                WHERE user_id = :user_id 
                AND is_active = 1 
                AND datetime(expires_at) > datetime('now')
                GROUP BY device_fingerprint, user_agent, ip_address
                ORDER BY last_accessed DESC
                """),
                {"user_id": user_id}
            ).fetchall()
            
            if result:
                for row in result:
                    device_fp = row.device_fingerprint or "N/A"
                    is_current = device_fp == current_device_fingerprint
                    is_trusted = bool(row.is_trusted)
                    
                    # Container para cada dispositivo
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            # Ícone e informações do dispositivo
                            icon = "🟢" if is_current else "📱"
                            trust_icon = "🔒" if is_trusted else "🔓"
                            current_text = " (Este dispositivo)" if is_current else ""
                            
                            st.markdown(f"**{icon} {trust_icon} Dispositivo{current_text}**")
                            st.caption(f"**User Agent:** {row.user_agent or 'N/A'}")
                            st.caption(f"**IP:** {row.ip_address or 'N/A'}")
                            st.caption(f"**Primeiro acesso:** {row.created_at}")
                            st.caption(f"**Último acesso:** {row.last_accessed}")
                            st.caption(f"**Sessões ativas:** {row.session_count}")
                        
                        with col2:
                            if not is_trusted and not is_current:
                                if st.button("🔒 Confiar", key=f"trust_{device_fp}"):
                                    trust_device(user_id, device_fp)
                                    st.rerun()
                            elif is_trusted and not is_current:
                                if st.button("🔓 Remover Confiança", key=f"untrust_{device_fp}"):
                                    untrust_device(user_id, device_fp)
                                    st.rerun()
                        
                        with col3:
                            if not is_current:
                                if st.button("🚫 Revogar Sessões", key=f"revoke_{device_fp}"):
                                    revoke_device_sessions(user_id, device_fp)
                                    st.success("Sessões revogadas!")
                                    st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("Nenhum dispositivo ativo encontrado.")
                
    except Exception as e:
        st.error(f"Erro ao carregar dispositivos ativos: {str(e)}")

def show_trusted_devices(user_id, current_device_fingerprint):
    """Mostra dispositivos confiáveis"""
    st.subheader("🔒 Dispositivos Confiáveis")
    
    try:
        with db_manager.get_db_session() as session:
            result = session.execute(
                text("""
                SELECT DISTINCT
                    device_fingerprint,
                    user_agent,
                    ip_address,
                    MIN(created_at) as first_trusted,
                    MAX(last_accessed) as last_access,
                    COUNT(*) as total_sessions
                FROM user_sessions 
                WHERE user_id = :user_id 
                AND is_trusted = 1
                AND device_fingerprint IS NOT NULL
                GROUP BY device_fingerprint
                ORDER BY last_access DESC
                """),
                {"user_id": user_id}
            ).fetchall()
            
            if result:
                for row in result:
                    device_fp = row.device_fingerprint
                    is_current = device_fp == current_device_fingerprint
                    
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            icon = "🟢" if is_current else "🔒"
                            current_text = " (Este dispositivo)" if is_current else ""
                            
                            st.markdown(f"**{icon} Dispositivo Confiável{current_text}**")
                            st.caption(f"**User Agent:** {row.user_agent or 'N/A'}")
                            st.caption(f"**IP:** {row.ip_address or 'N/A'}")
                            st.caption(f"**Confiável desde:** {row.first_trusted}")
                            st.caption(f"**Último acesso:** {row.last_access}")
                            st.caption(f"**Total de sessões:** {row.total_sessions}")
                        
                        with col2:
                            if st.button("🗑️ Remover", key=f"remove_trust_{device_fp}"):
                                if remove_trusted_device(user_id, device_fp):
                                    st.success("Dispositivo removido da lista de confiáveis!")
                                    st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("Nenhum dispositivo confiável encontrado.")
                
    except Exception as e:
        st.error(f"Erro ao carregar dispositivos confiáveis: {str(e)}")

def show_access_history(user_id):
    """Mostra histórico de acessos"""
    st.subheader("📊 Histórico de Acessos")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        days_back = st.selectbox("Período", [7, 15, 30, 60, 90], index=2)
    with col2:
        show_only_new = st.checkbox("Apenas novos dispositivos")
    
    try:
        with db_manager.get_db_session() as session:
            # Query base
            query = """
            SELECT 
                device_fingerprint,
                user_agent,
                ip_address,
                created_at,
                is_trusted,
                CASE 
                    WHEN is_trusted = 1 THEN 'Confiável'
                    ELSE 'Não Confiável'
                END as trust_status
            FROM user_sessions 
            WHERE user_id = :user_id 
            AND datetime(created_at) > datetime('now', '-{} days')
            """.format(days_back)
            
            if show_only_new:
                query += " AND is_trusted = 0"
            
            query += " ORDER BY created_at DESC LIMIT 100"
            
            result = session.execute(text(query), {"user_id": user_id}).fetchall()
            
            if result:
                # Converter para DataFrame para melhor visualização
                df = pd.DataFrame([
                    {
                        "Data/Hora": row.created_at,
                        "User Agent": row.user_agent or "N/A",
                        "IP": row.ip_address or "N/A",
                        "Status": row.trust_status,
                        "Fingerprint": row.device_fingerprint[:16] + "..." if row.device_fingerprint else "N/A"
                    }
                    for row in result
                ])
                
                st.dataframe(df, use_container_width=True)
                
                # Estatísticas
                st.markdown("### 📈 Estatísticas")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_accesses = len(df)
                    st.metric("Total de Acessos", total_accesses)
                
                with col2:
                    unique_devices = df['Fingerprint'].nunique()
                    st.metric("Dispositivos Únicos", unique_devices)
                
                with col3:
                    trusted_accesses = len(df[df['Status'] == 'Confiável'])
                    st.metric("Acessos Confiáveis", trusted_accesses)
                
            else:
                st.info(f"Nenhum acesso encontrado nos últimos {days_back} dias.")
                
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {str(e)}")

def trust_device(user_id, device_fingerprint):
    """Marca um dispositivo como confiável"""
    try:
        with db_manager.get_db_session() as session:
            session.execute(
                text("""
                UPDATE user_sessions 
                SET is_trusted = 1 
                WHERE user_id = :user_id 
                AND device_fingerprint = :device_fingerprint
                """),
                {
                    "user_id": user_id,
                    "device_fingerprint": device_fingerprint
                }
            )
            session.commit()
            
            # Log de segurança
            SecurityMonitor.log_security_event(
                "device_trusted",
                f"Dispositivo marcado como confiável: {device_fingerprint[:16]}...",
                user_id
            )
            
            return True
            
    except Exception as e:
        st.error(f"Erro ao confiar no dispositivo: {str(e)}")
        return False

def untrust_device(user_id, device_fingerprint):
    """Remove a confiança de um dispositivo"""
    try:
        with db_manager.get_db_session() as session:
            session.execute(
                text("""
                UPDATE user_sessions 
                SET is_trusted = 0 
                WHERE user_id = :user_id 
                AND device_fingerprint = :device_fingerprint
                """),
                {
                    "user_id": user_id,
                    "device_fingerprint": device_fingerprint
                }
            )
            session.commit()
            
            # Log de segurança
            SecurityMonitor.log_security_event(
                "device_untrusted",
                f"Confiança removida do dispositivo: {device_fingerprint[:16]}...",
                user_id
            )
            
            return True
            
    except Exception as e:
        st.error(f"Erro ao remover confiança do dispositivo: {str(e)}")
        return False

def remove_trusted_device(user_id, device_fingerprint):
    """Remove completamente um dispositivo confiável"""
    try:
        with db_manager.get_db_session() as session:
            # Primeiro, revogar todas as sessões do dispositivo
            session.execute(
                text("""
                UPDATE user_sessions 
                SET is_active = 0 
                WHERE user_id = :user_id 
                AND device_fingerprint = :device_fingerprint
                """),
                {
                    "user_id": user_id,
                    "device_fingerprint": device_fingerprint
                }
            )
            
            # Depois, remover a confiança
            session.execute(
                text("""
                UPDATE user_sessions 
                SET is_trusted = 0 
                WHERE user_id = :user_id 
                AND device_fingerprint = :device_fingerprint
                """),
                {
                    "user_id": user_id,
                    "device_fingerprint": device_fingerprint
                }
            )
            
            session.commit()
            
            # Log de segurança
            SecurityMonitor.log_security_event(
                "trusted_device_removed",
                f"Dispositivo confiável removido: {device_fingerprint[:16]}...",
                user_id
            )
            
            return True
            
    except Exception as e:
        st.error(f"Erro ao remover dispositivo confiável: {str(e)}")
        return False

def revoke_device_sessions(user_id, device_fingerprint):
    """Revoga todas as sessões de um dispositivo"""
    try:
        with db_manager.get_db_session() as session:
            session.execute(
                text("""
                UPDATE user_sessions 
                SET is_active = 0 
                WHERE user_id = :user_id 
                AND device_fingerprint = :device_fingerprint
                """),
                {
                    "user_id": user_id,
                    "device_fingerprint": device_fingerprint
                }
            )
            session.commit()
            
            # Log de segurança
            SecurityMonitor.log_security_event(
                "device_sessions_revoked",
                f"Sessões revogadas para dispositivo: {device_fingerprint[:16]}...",
                user_id
            )
            
            return True
            
    except Exception as e:
        st.error(f"Erro ao revogar sessões: {str(e)}")
        return False

def show_device_management_page():
    """Dashboard de dispositivos"""
    st.header("📊 Dashboard de Dispositivos")
    
    current_user = get_current_user()
    
    # Obter estatísticas
    stats = get_device_statistics()
    user_stats = get_user_device_statistics(current_user['id'])
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📱 Total de Dispositivos",
            stats.get('total_devices', 0),
            help="Dispositivos registrados no sistema"
        )
    
    with col2:
        active_devices = stats.get('active_devices', 0)
        total_devices = stats.get('total_devices', 1)
        percentage = (active_devices / total_devices) * 100 if total_devices > 0 else 0
        
        st.metric(
            "✅ Dispositivos Ativos",
            active_devices,
            delta=f"{percentage:.1f}%",
            help="Dispositivos com acesso nos últimos 30 dias"
        )
    
    with col3:
        st.metric(
            "👤 Meus Dispositivos",
            user_stats.get('my_devices', 0),
            help="Dispositivos registrados em seu nome"
        )
    
    with col4:
        blocked_devices = stats.get('blocked_devices', 0)
        st.metric(
            "🚫 Dispositivos Bloqueados",
            blocked_devices,
            delta=f"-{blocked_devices}" if blocked_devices > 0 else None,
            delta_color="inverse",
            help="Dispositivos com acesso bloqueado"
        )
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        show_device_types_chart(stats)
    
    with col2:
        show_device_activity_chart()
    
    # Alertas de segurança
    show_security_alerts()

def show_device_types_chart(stats):
    """Gráfico de tipos de dispositivos"""
    st.subheader("📊 Tipos de Dispositivos")
    
    device_types = stats.get('device_types', {})
    
    if device_types:
        # Traduzir tipos para português
        type_translation = {
            'mobile': '📱 Mobile',
            'desktop': '🖥️ Desktop',
            'tablet': '📱 Tablet',
            'laptop': '💻 Laptop',
            'unknown': '❓ Desconhecido'
        }
        
        translated_types = {
            type_translation.get(k, k): v 
            for k, v in device_types.items()
        }
        
        fig = px.pie(
            values=list(translated_types.values()),
            names=list(translated_types.keys()),
            title="Distribuição por Tipo",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Nenhum dispositivo encontrado para análise")

def show_device_activity_chart():
    """Gráfico de atividade de dispositivos"""
    st.subheader("📈 Atividade dos Últimos 7 Dias")
    
    activity_data = get_device_activity_data(7)
    
    if activity_data:
        df = pd.DataFrame(activity_data)
        
        fig = px.line(
            df,
            x='date',
            y='active_devices',
            title="Dispositivos Ativos por Dia",
            markers=True
        )
        
        fig.update_layout(
            height=400,
            xaxis_title="Data",
            yaxis_title="Dispositivos Ativos"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📈 Dados insuficientes para gráfico de atividade")

def show_security_alerts():
    """Exibe alertas de segurança"""
    st.subheader("🚨 Alertas de Segurança")
    
    alerts = get_security_alerts()
    
    if alerts:
        for alert in alerts:
            if alert['severity'] == 'high':
                st.error(f"🚨 **{alert['title']}**: {alert['message']}")
            elif alert['severity'] == 'medium':
                st.warning(f"⚠️ **{alert['title']}**: {alert['message']}")
            else:
                st.info(f"ℹ️ **{alert['title']}**: {alert['message']}")
    else:
        st.success("✅ Nenhum alerta de segurança no momento")

def show_my_devices():
    """Página de dispositivos do usuário atual"""
    st.header("📱 Meus Dispositivos")
    
    current_user = get_current_user()
    
    # Dispositivo atual
    current_device = get_current_device_info()
    
    if current_device:
        st.subheader("🔍 Dispositivo Atual")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**🏷️ Nome:** {current_device.get('name', 'Não identificado')}")
            st.info(f"**📱 Tipo:** {get_device_type_display(current_device.get('type'))}")
        
        with col2:
            st.info(f"**🌐 Sistema:** {current_device.get('os', 'Desconhecido')}")
            st.info(f"**🔗 IP:** {current_device.get('ip_address', 'N/A')}")
        
        with col3:
            last_access = current_device.get('last_access')
            if last_access:
                st.info(f"**🕒 Último Acesso:** {last_access.strftime('%d/%m/%Y %H:%M')}")
            
            is_trusted = current_device.get('is_trusted', False)
            trust_status = "✅ Confiável" if is_trusted else "⚠️ Não Confiável"
            st.info(f"**🔒 Status:** {trust_status}")
        
        # Ações para o dispositivo atual
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if not current_device.get('is_trusted', False):
                if st.button("✅ Marcar como Confiável", use_container_width=True):
                    if mark_device_as_trusted(current_device['id']):
                        st.success("✅ Dispositivo marcado como confiável!")
                        st.rerun()
        
        with col2:
            if st.button("✏️ Editar Nome", use_container_width=True):
                st.session_state['edit_current_device'] = True
        
        with col3:
            if st.button("🔄 Atualizar Informações", use_container_width=True):
                update_current_device_info()
                st.success("✅ Informações atualizadas!")
                st.rerun()
        
        # Interface de edição
        if st.session_state.get('edit_current_device'):
            show_edit_device_form(current_device)
    
    st.markdown("---")
    
    # Lista de todos os dispositivos do usuário
    st.subheader("📋 Todos os Meus Dispositivos")
    
    user_devices = get_user_devices(current_user['id'])
    
    if user_devices:
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_type = st.selectbox(
                "Filtrar por tipo",
                ["Todos", "mobile", "desktop", "tablet", "laptop"],
                format_func=lambda x: get_device_type_display(x) if x != "Todos" else "📋 Todos"
            )
        
        with col2:
            filter_status = st.selectbox(
                "Filtrar por status",
                ["Todos", "trusted", "untrusted", "blocked"],
                format_func=lambda x: {
                    "Todos": "📋 Todos",
                    "trusted": "✅ Confiáveis",
                    "untrusted": "⚠️ Não Confiáveis",
                    "blocked": "🚫 Bloqueados"
                }.get(x, x)
            )
        
        with col3:
            sort_by = st.selectbox(
                "Ordenar por",
                ["last_access", "created_at", "name"],
                format_func=lambda x: {
                    "last_access": "🕒 Último Acesso",
                    "created_at": "📅 Data de Criação",
                    "name": "🏷️ Nome"
                }.get(x, x)
            )
        
        # Aplicar filtros
        filtered_devices = filter_user_devices(user_devices, filter_type, filter_status)
        sorted_devices = sort_devices(filtered_devices, sort_by)
        
        # Exibir dispositivos
        for i, device in enumerate(sorted_devices):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    # Informações do dispositivo
                    device_icon = get_device_icon(device.get('type'))
                    trust_icon = "✅" if device.get('is_trusted') else "⚠️"
                    
                    st.markdown(f"**{device_icon} {device.get('name', 'Dispositivo sem nome')}** {trust_icon}")
                    st.caption(f"🌐 {device.get('os', 'SO desconhecido')} | 🔗 {device.get('ip_address', 'IP não disponível')}")
                    
                    last_access = device.get('last_access')
                    if last_access:
                        time_ago = get_time_ago(last_access)
                        st.caption(f"🕒 Último acesso: {time_ago}")
                
                with col2:
                    # Status
                    if device.get('is_blocked'):
                        st.error("🚫 Bloqueado")
                    elif device.get('is_trusted'):
                        st.success("✅ Confiável")
                    else:
                        st.warning("⚠️ Não confiável")
                
                with col3:
                    # Ações
                    if not device.get('is_trusted') and not device.get('is_blocked'):
                        if st.button("✅ Confiar", key=f"trust_{i}"):
                            mark_device_as_trusted(device['id'])
                            st.rerun()
                    
                    if device.get('is_trusted'):
                        if st.button("⚠️ Remover Confiança", key=f"untrust_{i}"):
                            remove_device_trust(device['id'])
                            st.rerun()
                
                with col4:
                    # Mais ações
                    if st.button("✏️ Editar", key=f"edit_{i}"):
                        st.session_state[f'edit_device_{i}'] = device
                        st.rerun()
                    
                    if st.button("🗑️ Remover", key=f"remove_{i}"):
                        if remove_user_device(device['id']):
                            st.success("✅ Dispositivo removido!")
                            st.rerun()
                
                # Interface de edição
                if st.session_state.get(f'edit_device_{i}'):
                    show_edit_device_form(device, i)
                
                st.markdown("---")
    else:
        st.info("📱 Nenhum dispositivo registrado")
        
        # Botão para registrar dispositivo atual
        if st.button("📱 Registrar Dispositivo Atual", type="primary"):
            if register_current_device():
                st.success("✅ Dispositivo registrado com sucesso!")
                st.rerun()

def show_edit_device_form(device, index=None):
    """Formulário para editar dispositivo"""
    key_suffix = f"_{index}" if index is not None else "_current"
    
    with st.form(f"edit_device_form{key_suffix}"):
        st.subheader(f"✏️ Editar Dispositivo: {device.get('name', 'Sem nome')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input(
                "Nome do Dispositivo",
                value=device.get('name', ''),
                placeholder="Ex: iPhone do João"
            )
            
            device_type = st.selectbox(
                "Tipo do Dispositivo",
                ["mobile", "desktop", "tablet", "laptop"],
                index=["mobile", "desktop", "tablet", "laptop"].index(device.get('type', 'mobile')),
                format_func=get_device_type_display
            )
        
        with col2:
            description = st.text_area(
                "Descrição (opcional)",
                value=device.get('description', ''),
                placeholder="Informações adicionais sobre o dispositivo..."
            )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("💾 Salvar", type="primary"):
                update_data = {
                    'name': new_name,
                    'type': device_type,
                    'description': description
                }
                
                if update_device(device['id'], update_data):
                    st.success("✅ Dispositivo atualizado!")
                    # Limpar estado de edição
                    if index is not None:
                        if f'edit_device_{index}' in st.session_state:
                            del st.session_state[f'edit_device_{index}']
                    else:
                        if 'edit_current_device' in st.session_state:
                            del st.session_state['edit_current_device']
                    st.rerun()
                else:
                    st.error("❌ Erro ao atualizar dispositivo")
        
        with col2:
            if st.form_submit_button("❌ Cancelar"):
                # Limpar estado de edição
                if index is not None:
                    if f'edit_device_{index}' in st.session_state:
                        del st.session_state[f'edit_device_{index}']
                else:
                    if 'edit_current_device' in st.session_state:
                        del st.session_state['edit_current_device']
                st.rerun()

def show_manage_devices():
    """Página de gerenciamento de dispositivos (admin)"""
    st.header("🔧 Gerenciar Todos os Dispositivos")
    
    # Estatísticas administrativas
    admin_stats = get_admin_device_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📱 Total", admin_stats.get('total', 0))
    
    with col2:
        st.metric("✅ Ativos", admin_stats.get('active', 0))
    
    with col3:
        st.metric("🚫 Bloqueados", admin_stats.get('blocked', 0))
    
    with col4:
        st.metric("⚠️ Suspeitos", admin_stats.get('suspicious', 0))
    
    # Filtros avançados
    with st.expander("🔍 Filtros Avançados"):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filter_user = st.text_input("Filtrar por usuário", placeholder="Nome ou email")
        
        with col2:
            filter_ip = st.text_input("Filtrar por IP", placeholder="192.168.1.1")
        
        with col3:
            filter_days = st.number_input("Últimos X dias", min_value=1, max_value=365, value=30)
        
        with col4:
            filter_status = st.selectbox(
                "Status",
                ["Todos", "trusted", "untrusted", "blocked", "suspicious"]
            )
    
    # Lista de dispositivos
    all_devices = get_all_devices_admin(filter_user, filter_ip, filter_days, filter_status)
    
    if all_devices:
        st.subheader(f"📋 {len(all_devices)} dispositivo(s) encontrado(s)")
        
        # Ações em lote
        with st.expander("🔧 Ações em Lote"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🚫 Bloquear Dispositivos Suspeitos"):
                    blocked_count = block_suspicious_devices()
                    st.success(f"✅ {blocked_count} dispositivo(s) bloqueado(s)")
                    st.rerun()
            
            with col2:
                if st.button("🧹 Limpar Dispositivos Inativos"):
                    cleaned_count = cleanup_inactive_devices(90)  # 90 dias
                    st.success(f"✅ {cleaned_count} dispositivo(s) removido(s)")
                    st.rerun()
            
            with col3:
                if st.button("📊 Gerar Relatório"):
                    generate_device_report(all_devices)
            
            with col4:
                if st.button("🔄 Atualizar Lista"):
                    st.rerun()
        
        # Tabela de dispositivos
        df_devices = prepare_devices_dataframe(all_devices)
        
        # Configurar colunas editáveis
        edited_df = st.data_editor(
            df_devices,
            column_config={
                "Ações": st.column_config.Column(
                    "Ações",
                    width="small",
                ),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["trusted", "untrusted", "blocked"],
                    required=True,
                ),
                "Confiável": st.column_config.CheckboxColumn(
                    "Confiável",
                    default=False,
                ),
            },
            disabled=["ID", "Usuário", "Tipo", "IP", "Último Acesso"],
            hide_index=True,
            use_container_width=True
        )
        
        # Aplicar mudanças
        if st.button("💾 Aplicar Alterações"):
            apply_device_changes(df_devices, edited_df)
            st.success("✅ Alterações aplicadas!")
            st.rerun()
    
    else:
        st.info("📭 Nenhum dispositivo encontrado com os filtros aplicados")

def show_access_analysis():
    """Análise de padrões de acesso"""
    st.header("📈 Análise de Padrões de Acesso")
    
    # Período de análise
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Data inicial",
            value=datetime.now() - timedelta(days=30)
        )
    
    with col2:
        end_date = st.date_input(
            "Data final",
            value=datetime.now()
        )
    
    # Análises
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Visão Geral",
        "🕒 Padrões Temporais",
        "🌍 Análise Geográfica",
        "🔍 Detecção de Anomalias"
    ])
    
    with tab1:
        show_access_overview(start_date, end_date)
    
    with tab2:
        show_temporal_patterns(start_date, end_date)
    
    with tab3:
        show_geographic_analysis(start_date, end_date)
    
    with tab4:
        show_anomaly_detection(start_date, end_date)

def show_access_overview(start_date, end_date):
    """Visão geral dos acessos"""
    st.subheader("📊 Visão Geral dos Acessos")
    
    access_data = get_access_data(start_date, end_date)
    
    if access_data:
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📈 Total de Acessos", access_data.get('total_accesses', 0))
        
        with col2:
            st.metric("👥 Usuários Únicos", access_data.get('unique_users', 0))
        
        with col3:
            st.metric("📱 Dispositivos Únicos", access_data.get('unique_devices', 0))
        
        with col4:
            avg_daily = access_data.get('avg_daily_accesses', 0)
            st.metric("📅 Média Diária", f"{avg_daily:.1f}")
        
        # Gráfico de acessos por dia
        daily_data = access_data.get('daily_accesses', [])
        if daily_data:
            df_daily = pd.DataFrame(daily_data)
            
            fig = px.line(
                df_daily,
                x='date',
                y='accesses',
                title="Acessos por Dia",
                markers=True
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Top dispositivos
        top_devices = access_data.get('top_devices', [])
        if top_devices:
            st.subheader("🏆 Top 10 Dispositivos")
            
            df_top = pd.DataFrame(top_devices)
            
            fig = px.bar(
                df_top,
                x='accesses',
                y='device_name',
                orientation='h',
                title="Dispositivos com Mais Acessos"
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("📊 Nenhum dado de acesso encontrado para o período selecionado")

def show_temporal_patterns(start_date, end_date):
    """Análise de padrões temporais"""
    st.subheader("🕒 Padrões Temporais de Acesso")
    
    temporal_data = get_temporal_patterns(start_date, end_date)
    
    if temporal_data:
        # Heatmap de acessos por hora e dia da semana
        hourly_data = temporal_data.get('hourly_patterns', [])
        
        if hourly_data:
            df_hourly = pd.DataFrame(hourly_data)
            
            # Criar matriz para heatmap
            pivot_data = df_hourly.pivot(index='day_of_week', columns='hour', values='accesses')
            
            fig = px.imshow(
                pivot_data,
                title="Padrão de Acessos por Hora e Dia da Semana",
                labels=dict(x="Hora do Dia", y="Dia da Semana", color="Acessos"),
                aspect="auto"
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de acessos por hora
        hourly_summary = temporal_data.get('hourly_summary', [])
        if hourly_summary:
            df_hour = pd.DataFrame(hourly_summary)
            
            fig = px.bar(
                df_hour,
                x='hour',
                y='total_accesses',
                title="Distribuição de Acessos por Hora"
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("🕒 Dados insuficientes para análise temporal")

def show_geographic_analysis(start_date, end_date):
    """Análise geográfica dos acessos"""
    st.subheader("🌍 Análise Geográfica")
    
    geo_data = get_geographic_data(start_date, end_date)
    
    if geo_data:
        # Top países/regiões
        top_locations = geo_data.get('top_locations', [])
        
        if top_locations:
            df_locations = pd.DataFrame(top_locations)
            
            fig = px.pie(
                df_locations,
                values='accesses',
                names='location',
                title="Acessos por Localização"
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # IPs suspeitos
        suspicious_ips = geo_data.get('suspicious_ips', [])
        
        if suspicious_ips:
            st.subheader("🚨 IPs Suspeitos")
            
            for ip_data in suspicious_ips:
                st.warning(
                    f"🔍 **IP:** {ip_data['ip']} | "
                    f"**Acessos:** {ip_data['accesses']} | "
                    f"**Localização:** {ip_data.get('location', 'Desconhecida')}"
                )
    
    else:
        st.info("🌍 Dados geográficos não disponíveis")

def show_anomaly_detection(start_date, end_date):
    """Detecção de anomalias"""
    st.subheader("🔍 Detecção de Anomalias")
    
    anomalies = detect_access_anomalies(start_date, end_date)
    
    if anomalies:
        # Classificar anomalias por severidade
        high_severity = [a for a in anomalies if a['severity'] == 'high']
        medium_severity = [a for a in anomalies if a['severity'] == 'medium']
        low_severity = [a for a in anomalies if a['severity'] == 'low']
        
        # Exibir anomalias de alta severidade
        if high_severity:
            st.subheader("🚨 Anomalias de Alta Severidade")
            for anomaly in high_severity:
                st.error(
                    f"**{anomaly['type']}**: {anomaly['description']} "
                    f"(Detectado em: {anomaly['detected_at']})"
                )
        
        # Exibir anomalias de média severidade
        if medium_severity:
            st.subheader("⚠️ Anomalias de Média Severidade")
            for anomaly in medium_severity:
                st.warning(
                    f"**{anomaly['type']}**: {anomaly['description']} "
                    f"(Detectado em: {anomaly['detected_at']})"
                )
        
        # Exibir anomalias de baixa severidade
        if low_severity:
            with st.expander("ℹ️ Anomalias de Baixa Severidade"):
                for anomaly in low_severity:
                    st.info(
                        f"**{anomaly['type']}**: {anomaly['description']} "
                        f"(Detectado em: {anomaly['detected_at']})"
                    )
        
        # Gráfico de anomalias ao longo do tempo
        anomaly_timeline = prepare_anomaly_timeline(anomalies)
        
        if anomaly_timeline:
            df_timeline = pd.DataFrame(anomaly_timeline)
            
            fig = px.scatter(
                df_timeline,
                x='date',
                y='severity_score',
                color='severity',
                size='count',
                title="Timeline de Anomalias",
                hover_data=['type', 'description']
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.success("✅ Nenhuma anomalia detectada no período selecionado")

def show_device_settings():
    """Configurações de dispositivos (admin)"""
    st.header("⚙️ Configurações de Dispositivos")
    
    # Carregar configurações atuais
    settings = load_device_settings()
    
    with st.form("device_settings_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔒 Segurança")
            
            auto_trust_enabled = st.checkbox(
                "Confiança automática para dispositivos conhecidos",
                value=settings.get('auto_trust_enabled', False),
                help="Marcar automaticamente como confiáveis dispositivos que já foram usados"
            )
            
            max_devices_per_user = st.number_input(
                "Máximo de dispositivos por usuário",
                min_value=1,
                max_value=20,
                value=settings.get('max_devices_per_user', 5)
            )
            
            device_session_timeout = st.number_input(
                "Timeout de sessão (minutos)",
                min_value=5,
                max_value=1440,
                value=settings.get('device_session_timeout', 60)
            )
        
        with col2:
            st.subheader("🔍 Monitoramento")
            
            anomaly_detection_enabled = st.checkbox(
                "Detecção de anomalias",
                value=settings.get('anomaly_detection_enabled', True)
            )
            
            suspicious_activity_threshold = st.number_input(
                "Limite para atividade suspeita (acessos/hora)",
                min_value=1,
                max_value=100,
                value=settings.get('suspicious_activity_threshold', 10)
            )
            
            auto_block_suspicious = st.checkbox(
                "Bloquear automaticamente dispositivos suspeitos",
                value=settings.get('auto_block_suspicious', False)
            )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📧 Notificações")
            
            notify_new_device = st.checkbox(
                "Notificar sobre novos dispositivos",
                value=settings.get('notify_new_device', True)
            )
            
            notify_suspicious_activity = st.checkbox(
                "Notificar sobre atividade suspeita",
                value=settings.get('notify_suspicious_activity', True)
            )
        
        with col2:
            st.subheader("🧹 Limpeza")
            
            auto_cleanup_enabled = st.checkbox(
                "Limpeza automática de dispositivos inativos",
                value=settings.get('auto_cleanup_enabled', False)
            )
            
            cleanup_inactive_days = st.number_input(
                "Remover dispositivos inativos após (dias)",
                min_value=30,
                max_value=365,
                value=settings.get('cleanup_inactive_days', 90)
            )
        
        # Botão de salvamento
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.form_submit_button("💾 Salvar Configurações", type="primary", use_container_width=True):
                new_settings = {
                    'auto_trust_enabled': auto_trust_enabled,
                    'max_devices_per_user': max_devices_per_user,
                    'device_session_timeout': device_session_timeout,
                    'anomaly_detection_enabled': anomaly_detection_enabled,
                    'suspicious_activity_threshold': suspicious_activity_threshold,
                    'auto_block_suspicious': auto_block_suspicious,
                    'notify_new_device': notify_new_device,
                    'notify_suspicious_activity': notify_suspicious_activity,
                    'auto_cleanup_enabled': auto_cleanup_enabled,
                    'cleanup_inactive_days': cleanup_inactive_days
                }
                
                if save_device_settings(new_settings):
                    st.success("✅ Configurações salvas com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar configurações!")

# Funções auxiliares para gerenciamento de dispositivos

def get_device_statistics():
    """Obtém estatísticas gerais de dispositivos"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total de dispositivos
            cursor.execute("SELECT COUNT(*) FROM trusted_devices")
            total_devices = cursor.fetchone()[0]
            
            # Dispositivos ativos (últimos 30 dias)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            cursor.execute(
                "SELECT COUNT(*) FROM trusted_devices WHERE last_access >= ?",
                (thirty_days_ago,)
            )
            active_devices = cursor.fetchone()[0]
            
            # Dispositivos bloqueados
            cursor.execute("SELECT COUNT(*) FROM trusted_devices WHERE is_blocked = 1")
            blocked_devices = cursor.fetchone()[0]
            
            # Tipos de dispositivos
            cursor.execute("""
                SELECT device_type, COUNT(*) 
                FROM trusted_devices 
                GROUP BY device_type
            """)
            device_types = dict(cursor.fetchall())
            
            return {
                'total_devices': total_devices,
                'active_devices': active_devices,
                'blocked_devices': blocked_devices,
                'device_types': device_types
            }
            
    except Exception as e:
        st.error(f"Erro ao obter estatísticas: {str(e)}")
        return {}

def get_user_device_statistics(user_id):
    """Obtém estatísticas de dispositivos do usuário"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) FROM trusted_devices WHERE user_id = ?",
                (user_id,)
            )
            my_devices = cursor.fetchone()[0]
            
            return {'my_devices': my_devices}
            
    except Exception as e:
        st.error(f"Erro ao obter estatísticas do usuário: {str(e)}")
        return {}

def get_device_activity_data(days):
    """Obtém dados de atividade de dispositivos"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Simular dados de atividade (implementar com dados reais)
            activity_data = []
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                # Aqui você implementaria a consulta real para contar dispositivos ativos por dia
                active_count = max(0, 10 - i + (i % 3))  # Dados simulados
                
                activity_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'active_devices': active_count
                })
            
            return list(reversed(activity_data))
            
    except Exception as e:
        st.error(f"Erro ao obter dados de atividade: {str(e)}")
        return []

def get_security_alerts():
    """Obtém alertas de segurança"""
    try:
        # Implementar lógica real de alertas
        alerts = []
        
        # Verificar dispositivos suspeitos
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Dispositivos com muitos acessos recentes
            cursor.execute("""
                SELECT device_name, COUNT(*) as access_count
                FROM access_history 
                WHERE created_at >= datetime('now', '-1 hour')
                GROUP BY device_id
                HAVING COUNT(*) > 10
            """)
            
            suspicious_devices = cursor.fetchall()
            
            for device_name, count in suspicious_devices:
                alerts.append({
                    'severity': 'high',
                    'title': 'Atividade Suspeita',
                    'message': f'Dispositivo "{device_name}" com {count} acessos na última hora'
                })
        
        return alerts
        
    except Exception as e:
        return []

def get_current_device_info():
    """Obtém informações do dispositivo atual"""
    try:
        # Implementar detecção real do dispositivo
        # Por enquanto, retornar dados simulados
        return {
            'id': 'current_device_id',
            'name': 'Meu Dispositivo',
            'type': 'desktop',
            'os': 'Windows 11',
            'ip_address': '192.168.1.100',
            'last_access': datetime.now(),
            'is_trusted': False
        }
        
    except Exception as e:
        st.error(f"Erro ao obter informações do dispositivo: {str(e)}")
        return None

def get_user_devices(user_id):
    """Obtém dispositivos do usuário"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, device_name, device_type, ip_address, 
                       is_trusted, is_blocked, last_access, created_at,
                       description
                FROM trusted_devices 
                WHERE user_id = ?
                ORDER BY last_access DESC
            """, (user_id,))
            
            devices = []
            for row in cursor.fetchall():
                devices.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'ip_address': row[3],
                    'is_trusted': bool(row[4]),
                    'is_blocked': bool(row[5]),
                    'last_access': datetime.fromisoformat(row[6]) if row[6] else None,
                    'created_at': datetime.fromisoformat(row[7]) if row[7] else None,
                    'description': row[8]
                })
            
            return devices
            
    except Exception as e:
        st.error(f"Erro ao obter dispositivos do usuário: {str(e)}")
        return []

def get_device_type_display(device_type):
    """Retorna display amigável para tipo de dispositivo"""
    type_map = {
        'mobile': '📱 Mobile',
        'desktop': '🖥️ Desktop',
        'tablet': '📱 Tablet',
        'laptop': '💻 Laptop',
        'unknown': '❓ Desconhecido'
    }
    return type_map.get(device_type, f'❓ {device_type}')

def get_device_icon(device_type):
    """Retorna ícone para tipo de dispositivo"""
    icon_map = {
        'mobile': '📱',
        'desktop': '🖥️',
        'tablet': '📱',
        'laptop': '💻',
        'unknown': '❓'
    }
    return icon_map.get(device_type, '❓')

def get_time_ago(timestamp):
    """Retorna string de tempo relativo"""
    if not timestamp:
        return "Nunca"
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} dia(s) atrás"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hora(s) atrás"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minuto(s) atrás"
    else:
        return "Agora mesmo"

def mark_device_as_trusted(device_id):
    """Marca dispositivo como confiável"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE trusted_devices SET is_trusted = 1 WHERE id = ?",
                (device_id,)
            )
            
            conn.commit()
            return True
            
    except Exception as e:
        st.error(f"Erro ao marcar dispositivo como confiável: {str(e)}")
        return False

def remove_device_trust(device_id):
    """Remove confiança do dispositivo"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE trusted_devices SET is_trusted = 0 WHERE id = ?",
                (device_id,)
            )
            
            conn.commit()
            return True
            
    except Exception as e:
        st.error(f"Erro ao remover confiança: {str(e)}")
        return False

def update_device(device_id, update_data):
    """Atualiza informações do dispositivo"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
            values = list(update_data.values()) + [device_id]
            
            cursor.execute(
                f"UPDATE trusted_devices SET {set_clause} WHERE id = ?",
                values
            )
            
            conn.commit()
            return True
            
    except Exception as e:
        st.error(f"Erro ao atualizar dispositivo: {str(e)}")
        return False

def remove_user_device(device_id):
    """Remove dispositivo do usuário"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM trusted_devices WHERE id = ?", (device_id,))
            
            conn.commit()
            return True
            
    except Exception as e:
        st.error(f"Erro ao remover dispositivo: {str(e)}")
        return False

def filter_user_devices(devices, filter_type, filter_status):
    """Filtra dispositivos do usuário"""
    filtered = devices.copy()
    
    if filter_type != "Todos":
        filtered = [d for d in filtered if d.get('type') == filter_type]
    
    if filter_status != "Todos":
        if filter_status == "trusted":
            filtered = [d for d in filtered if d.get('is_trusted')]
        elif filter_status == "untrusted":
            filtered = [d for d in filtered if not d.get('is_trusted') and not d.get('is_blocked')]
        elif filter_status == "blocked":
            filtered = [d for d in filtered if d.get('is_blocked')]
    
    return filtered

def sort_devices(devices, sort_by):
    """Ordena lista de dispositivos"""
    if sort_by == "last_access":
        return sorted(devices, key=lambda x: x.get('last_access') or datetime.min, reverse=True)
    elif sort_by == "created_at":
        return sorted(devices, key=lambda x: x.get('created_at') or datetime.min, reverse=True)
    elif sort_by == "name":
        return sorted(devices, key=lambda x: x.get('name', '').lower())
    else:
        return devices

def register_current_device():
    """Registra o dispositivo atual"""
    try:
        current_user = get_current_user()
        if not current_user:
            return False
        
        # Implementar registro real do dispositivo
        # Por enquanto, simular sucesso
        return True
        
    except Exception as e:
        st.error(f"Erro ao registrar dispositivo: {str(e)}")
        return False

def update_current_device_info():
    """Atualiza informações do dispositivo atual"""
    try:
        # Implementar atualização real
        return True
        
    except Exception as e:
        st.error(f"Erro ao atualizar informações: {str(e)}")
        return False

# Funções administrativas

def get_admin_device_statistics():
    """Obtém estatísticas administrativas"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total
            cursor.execute("SELECT COUNT(*) FROM trusted_devices")
            total = cursor.fetchone()[0]
            
            # Ativos (últimos 7 dias)
            week_ago = datetime.now() - timedelta(days=7)
            cursor.execute(
                "SELECT COUNT(*) FROM trusted_devices WHERE last_access >= ?",
                (week_ago,)
            )
            active = cursor.fetchone()[0]
            
            # Bloqueados
            cursor.execute("SELECT COUNT(*) FROM trusted_devices WHERE is_blocked = 1")
            blocked = cursor.fetchone()[0]
            
            # Suspeitos (implementar lógica real)
            suspicious = 0
            
            return {
                'total': total,
                'active': active,
                'blocked': blocked,
                'suspicious': suspicious
            }
            
    except Exception as e:
        st.error(f"Erro ao obter estatísticas administrativas: {str(e)}")
        return {}

def get_all_devices_admin(filter_user, filter_ip, filter_days, filter_status):
    """Obtém todos os dispositivos para administração"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Construir query com filtros
            query = """
                SELECT td.id, td.device_name, td.device_type, td.ip_address,
                       td.is_trusted, td.is_blocked, td.last_access,
                       u.username, u.email
                FROM trusted_devices td
                LEFT JOIN users u ON td.user_id = u.id
                WHERE 1=1
            """
            params = []
            
            if filter_user:
                query += " AND (u.username LIKE ? OR u.email LIKE ?)"
                params.extend([f"%{filter_user}%", f"%{filter_user}%"])
            
            if filter_ip:
                query += " AND td.ip_address LIKE ?"
                params.append(f"%{filter_ip}%")
            
            if filter_days:
                cutoff_date = datetime.now() - timedelta(days=filter_days)
                query += " AND td.last_access >= ?"
                params.append(cutoff_date)
            
            if filter_status != "Todos":
                if filter_status == "trusted":
                    query += " AND td.is_trusted = 1"
                elif filter_status == "untrusted":
                    query += " AND td.is_trusted = 0 AND td.is_blocked = 0"
                elif filter_status == "blocked":
                    query += " AND td.is_blocked = 1"
            
            query += " ORDER BY td.last_access DESC"
            
            cursor.execute(query, params)
            
            devices = []
            for row in cursor.fetchall():
                devices.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'ip_address': row[3],
                    'is_trusted': bool(row[4]),
                    'is_blocked': bool(row[5]),
                    'last_access': datetime.fromisoformat(row[6]) if row[6] else None,
                    'username': row[7],
                    'email': row[8]
                })
            
            return devices
            
    except Exception as e:
        st.error(f"Erro ao obter dispositivos: {str(e)}")
        return []

def prepare_devices_dataframe(devices):
    """Prepara DataFrame para exibição de dispositivos"""
    data = []
    
    for device in devices:
        data.append({
            'ID': device['id'],
            'Nome': device.get('name', 'Sem nome'),
            'Tipo': get_device_type_display(device.get('type')),
            'IP': device.get('ip_address', 'N/A'),
            'Usuário': device.get('username', 'N/A'),
            'Último Acesso': device.get('last_access').strftime('%d/%m/%Y %H:%M') if device.get('last_access') else 'Nunca',
            'Confiável': device.get('is_trusted', False),
            'Status': 'blocked' if device.get('is_blocked') else ('trusted' if device.get('is_trusted') else 'untrusted')
        })
    
    return pd.DataFrame(data)

def apply_device_changes(original_df, edited_df):
    """Aplica mudanças feitas na tabela de dispositivos"""
    try:
        # Implementar aplicação de mudanças
        # Comparar DataFrames e aplicar alterações no banco
        return True
        
    except Exception as e:
        st.error(f"Erro ao aplicar mudanças: {str(e)}")
        return False

def block_suspicious_devices():
    """Bloqueia dispositivos suspeitos"""
    try:
        # Implementar lógica para identificar e bloquear dispositivos suspeitos
        return 0
        
    except Exception as e:
        st.error(f"Erro ao bloquear dispositivos: {str(e)}")
        return 0

def cleanup_inactive_devices(days):
    """Remove dispositivos inativos"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute(
                "DELETE FROM trusted_devices WHERE last_access < ? AND is_trusted = 0",
                (cutoff_date,)
            )
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count
            
    except Exception as e:
        st.error(f"Erro na limpeza: {str(e)}")
        return 0

def generate_device_report(devices):
    """Gera relatório de dispositivos"""
    try:
        df = prepare_devices_dataframe(devices)
        
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="📊 Baixar Relatório (CSV)",
            data=csv,
            file_name=f"relatorio_dispositivos_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Erro ao gerar relatório: {str(e)}")

# Funções de análise

def get_access_data(start_date, end_date):
    """Obtém dados de acesso para análise"""
    try:
        # Implementar consulta real de dados de acesso
        # Por enquanto, retornar dados simulados
        return {
            'total_accesses': 1250,
            'unique_users': 45,
            'unique_devices': 78,
            'avg_daily_accesses': 41.7,
            'daily_accesses': [
                {'date': '2024-01-01', 'accesses': 35},
                {'date': '2024-01-02', 'accesses': 42},
                {'date': '2024-01-03', 'accesses': 38},
                # ... mais dados
            ],
            'top_devices': [
                {'device_name': 'iPhone do João', 'accesses': 125},
                {'device_name': 'Desktop da Maria', 'accesses': 98},
                # ... mais dados
            ]
        }
        
    except Exception as e:
        st.error(f"Erro ao obter dados de acesso: {str(e)}")
        return None

def get_temporal_patterns(start_date, end_date):
    """Obtém padrões temporais de acesso"""
    try:
        # Implementar análise temporal real
        return None
        
    except Exception as e:
        return None

def get_geographic_data(start_date, end_date):
    """Obtém dados geográficos de acesso"""
    try:
        # Implementar análise geográfica real
        return None
        
    except Exception as e:
        return None

def detect_access_anomalies(start_date, end_date):
    """Detecta anomalias nos padrões de acesso"""
    try:
        # Implementar detecção de anomalias real
        return []
        
    except Exception as e:
        return []

def prepare_anomaly_timeline(anomalies):
    """Prepara timeline de anomalias"""
    try:
        # Implementar preparação de timeline
        return []
        
    except Exception as e:
        return []

def load_device_settings():
    """Carrega configurações de dispositivos"""
    try:
        # Implementar carregamento de configurações
        return {}
        
    except Exception as e:
        return {}

def save_device_settings(settings):
    """Salva configurações de dispositivos"""
    try:
        # Implementar salvamento de configurações
        return True
        
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {str(e)}")
        return False

if __name__ == "__main__":
    show_device_management()