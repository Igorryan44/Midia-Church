import streamlit as st
from datetime import datetime, timedelta
import json
from app.utils.notifications import NotificationManager, render_notification_center, render_notification_card
from app.utils.auth import get_current_user, is_admin

def render_notifications():
    """Renderiza a página de notificações"""
    st.title("🔔 Central de Notificações")
    
    current_user = get_current_user()
    if not current_user:
        st.error("Usuário não autenticado")
        return
    
    user_id = current_user.get('id')
    notification_manager = NotificationManager()
    
    # Mostrar estatísticas rápidas
    show_notification_stats(notification_manager, user_id)
    
    # Tabs para diferentes seções
    if is_admin():
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📬 Minhas Notificações", 
            "🔔 Não Lidas", 
            "⚙️ Configurações",
            "👥 Administração",
            "📊 Relatórios"
        ])
    else:
        tab1, tab2, tab3 = st.tabs(["📬 Todas", "🔔 Não Lidas", "⚙️ Configurações"])
        tab4 = tab5 = None
    
    with tab1:
        show_user_notifications(notification_manager, user_id, "Todas as Notificações", unread_only=False)
    
    with tab2:
        show_user_notifications(notification_manager, user_id, "Notificações Não Lidas", unread_only=True)
    
    with tab3:
        show_notification_settings(notification_manager, user_id)
    
    # Tabs administrativas (apenas para admins)
    if tab4:
        with tab4:
            show_admin_notifications(notification_manager)
    
    if tab5:
        with tab5:
            show_notification_reports(notification_manager)

def show_notification_stats(notification_manager, user_id):
    """Mostra estatísticas rápidas das notificações"""
    try:
        # Buscar estatísticas
        total_notifications = len(notification_manager.get_user_notifications(user_id, unread_only=False, limit=1000))
        unread_notifications = len(notification_manager.get_user_notifications(user_id, unread_only=True, limit=1000))
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📬 Total", total_notifications)
        
        with col2:
            st.metric("🔔 Não Lidas", unread_notifications)
        
        with col3:
            read_notifications = total_notifications - unread_notifications
            st.metric("✅ Lidas", read_notifications)
        
        with col4:
            read_rate = (read_notifications / total_notifications * 100) if total_notifications > 0 else 0
            st.metric("📊 Taxa de Leitura", f"{read_rate:.1f}%")
        
        st.markdown("---")
    
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar estatísticas: {str(e)}")

def show_user_notifications(notification_manager, user_id, title, unread_only=False):
    """Mostra notificações do usuário com filtros e paginação"""
    st.subheader(title)
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        notification_type = st.selectbox(
            "Tipo:",
            ["Todos", "info", "warning", "error", "success"],
            key=f"type_filter_{unread_only}"
        )
    
    with col2:
        days_filter = st.selectbox(
            "Período:",
            ["Todos", "Hoje", "Últimos 7 dias", "Últimos 30 dias"],
            key=f"days_filter_{unread_only}"
        )
    
    with col3:
        limit = st.number_input(
            "Limite:",
            min_value=10,
            max_value=200,
            value=50,
            key=f"limit_filter_{unread_only}"
        )
    
    # Buscar notificações com filtros
    notifications = notification_manager.get_user_notifications(
        user_id, 
        unread_only=unread_only, 
        limit=limit
    )
    
    # Aplicar filtros adicionais
    if notification_type != "Todos":
        notifications = [n for n in notifications if n.get('type') == notification_type]
    
    if days_filter != "Todos":
        days_map = {"Hoje": 1, "Últimos 7 dias": 7, "Últimos 30 dias": 30}
        days = days_map[days_filter]
        cutoff_date = datetime.now() - timedelta(days=days)
        notifications = [n for n in notifications if datetime.fromisoformat(n.get('created_at', '')) >= cutoff_date]
    
    if not notifications:
        st.info("📭 Nenhuma notificação encontrada com os filtros selecionados.")
    else:
        # Ações em lote
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"✅ Marcar Todas como Lidas ({len(notifications)})", key=f"mark_read_{unread_only}"):
                for notification in notifications:
                    notification_manager.mark_as_read(notification['id'])
                st.success("Notificações marcadas como lidas!")
                st.rerun()
        
        with col2:
            if st.button(f"🗑️ Excluir Selecionadas", key=f"delete_{unread_only}"):
                st.warning("Funcionalidade será implementada em breve")
        
        with col3:
            if st.button(f"📤 Exportar ({len(notifications)})", key=f"export_{unread_only}"):
                export_notifications(notifications)
        
        st.markdown("---")
        
        # Exibir notificações
        for notification in notifications:
            render_notification_card(notification, user_id)

def show_notification_settings(notification_manager, user_id):
    """Mostra configurações de notificação"""
    st.subheader("⚙️ Configurações de Notificação")
    
    # Carregar configurações atuais
    try:
        current_settings = notification_manager.get_user_settings(user_id)
    except:
        current_settings = {}
    
    with st.form("notification_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Tipos de Notificação:**")
            email_notifications = st.checkbox(
                "📧 Notificações por Email", 
                value=current_settings.get('email_notifications', True)
            )
            push_notifications = st.checkbox(
                "📱 Notificações Push", 
                value=current_settings.get('push_notifications', True)
            )
            system_notifications = st.checkbox(
                "🔔 Notificações do Sistema", 
                value=current_settings.get('system_notifications', True)
            )
            
            st.write("**Categorias:**")
            notify_events = st.checkbox(
                "📅 Eventos", 
                value=current_settings.get('notify_events', True)
            )
            notify_messages = st.checkbox(
                "💬 Mensagens", 
                value=current_settings.get('notify_messages', True)
            )
            notify_admin = st.checkbox(
                "⚙️ Administrativo", 
                value=current_settings.get('notify_admin', True)
            )
        
        with col2:
            st.write("**Frequência:**")
            frequency = st.selectbox(
                "Frequência de Email:",
                ["Imediata", "Diária", "Semanal", "Nunca"],
                index=["Imediata", "Diária", "Semanal", "Nunca"].index(
                    current_settings.get('email_frequency', 'Imediata')
                )
            )
            
            quiet_hours = st.checkbox(
                "🌙 Modo Silencioso (22h-8h)", 
                value=current_settings.get('quiet_hours', False)
            )
            
            st.write("**Prioridade Mínima:**")
            min_priority = st.selectbox(
                "Notificar apenas:",
                ["Todas", "Normal e acima", "Importantes", "Críticas"],
                index=["Todas", "Normal e acima", "Importantes", "Críticas"].index(
                    current_settings.get('min_priority', 'Todas')
                )
            )
            
            auto_cleanup = st.checkbox(
                "🧹 Limpeza Automática (30 dias)", 
                value=current_settings.get('auto_cleanup', True)
            )
        
        if st.form_submit_button("💾 Salvar Configurações", type="primary"):
            new_settings = {
                'email_notifications': email_notifications,
                'push_notifications': push_notifications,
                'system_notifications': system_notifications,
                'notify_events': notify_events,
                'notify_messages': notify_messages,
                'notify_admin': notify_admin,
                'email_frequency': frequency,
                'quiet_hours': quiet_hours,
                'min_priority': min_priority,
                'auto_cleanup': auto_cleanup
            }
            
            try:
                notification_manager.save_user_settings(user_id, new_settings)
                st.success("✅ Configurações salvas com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao salvar configurações: {str(e)}")
    
    st.divider()
    
    # Ações em lote
    st.subheader("🔧 Ações em Lote")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Marcar Todas como Lidas"):
            if notification_manager.mark_all_as_read(user_id):
                st.success("Todas as notificações foram marcadas como lidas!")
                st.rerun()
    
    with col2:
        if st.button("🗑️ Limpar Lidas"):
            notification_manager.cleanup_old_notifications(user_id, days=0, read_only=True)
            st.success("Notificações lidas foram removidas!")
            st.rerun()
    
    with col3:
        if st.button("🧹 Limpar Antigas (30+ dias)"):
            notification_manager.cleanup_old_notifications(user_id, days=30)
            st.success("Notificações antigas foram removidas!")
            st.rerun()

def show_admin_notifications(notification_manager):
    """Mostra painel administrativo de notificações"""
    st.subheader("👥 Administração de Notificações")
    
    # Estatísticas gerais
    st.write("**📊 Estatísticas Gerais:**")
    
    try:
        from app.database.local_connection import db_manager
        
        # Total de notificações
        total_notifications = db_manager.fetch_all(
            "SELECT COUNT(*) as count FROM notifications"
        )[0]['count']
        
        # Notificações não lidas
        unread_notifications = db_manager.fetch_all(
            "SELECT COUNT(*) as count FROM notifications WHERE is_read = 0"
        )[0]['count']
        
        # Usuários com notificações
        users_with_notifications = db_manager.fetch_all(
            "SELECT COUNT(DISTINCT user_id) as count FROM notifications"
        )[0]['count']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📬 Total de Notificações", total_notifications)
        
        with col2:
            st.metric("🔔 Não Lidas", unread_notifications)
        
        with col3:
            st.metric("👥 Usuários Ativos", users_with_notifications)
        
        with col4:
            read_rate = ((total_notifications - unread_notifications) / total_notifications * 100) if total_notifications > 0 else 0
            st.metric("📊 Taxa de Leitura", f"{read_rate:.1f}%")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar estatísticas: {str(e)}")
    
    st.divider()
    
    # Enviar notificação para todos
    st.subheader("📢 Enviar Notificação Global")
    
    with st.form("global_notification"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Título da Notificação:")
            message = st.text_area("Mensagem:", height=100)
            
        with col2:
            notification_type = st.selectbox(
                "Tipo:",
                ["info", "success", "warning", "error"]
            )
            priority = st.selectbox(
                "Prioridade:",
                ["normal", "high", "critical"]
            )
            
            send_email = st.checkbox("📧 Enviar também por email")
        
        if st.form_submit_button("📢 Enviar para Todos os Usuários"):
            if title and message:
                try:
                    # Buscar todos os usuários ativos
                    users = db_manager.fetch_all(
                        "SELECT id FROM users WHERE is_active = 1"
                    )
                    
                    success_count = 0
                    for user in users:
                        try:
                            notification_manager.create_notification(
                                user_id=user['id'],
                                title=title,
                                message=message,
                                notification_type=notification_type,
                                priority=priority
                            )
                            success_count += 1
                        except:
                            continue
                    
                    st.success(f"✅ Notificação enviada para {success_count} usuários!")
                    
                    if send_email:
                        st.info("📧 Emails serão enviados em segundo plano")
                
                except Exception as e:
                    st.error(f"❌ Erro ao enviar notificações: {str(e)}")
            else:
                st.error("❌ Título e mensagem são obrigatórios!")
    
    st.divider()
    
    # Limpeza em massa
    st.subheader("🧹 Limpeza em Massa")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Limpar Notificações Lidas (Todos)"):
            try:
                db_manager.execute_query("DELETE FROM notifications WHERE is_read = 1")
                st.success("✅ Notificações lidas removidas!")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
    
    with col2:
        if st.button("🧹 Limpar Antigas (90+ dias)"):
            try:
                db_manager.execute_query(
                    "DELETE FROM notifications WHERE created_at < DATE('now', '-90 days')"
                )
                st.success("✅ Notificações antigas removidas!")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
    
    with col3:
        # Usar session state para controlar a confirmação
        if st.button("⚠️ Limpar TODAS as Notificações"):
            if st.session_state.get('confirm_clear_all', False):
                try:
                    db_manager.execute_query("DELETE FROM notifications")
                    st.success("✅ Todas as notificações foram removidas!")
                    st.session_state.confirm_clear_all = False
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
            else:
                st.session_state.confirm_clear_all = True
                st.warning("⚠️ Clique novamente para confirmar a limpeza total!")
        
        # Mostrar checkbox de confirmação se necessário
        if st.session_state.get('confirm_clear_all', False):
            if st.checkbox("✅ Confirmo que quero limpar TODAS as notificações"):
                if st.button("🗑️ CONFIRMAR LIMPEZA TOTAL", type="primary"):
                    try:
                        db_manager.execute_query("DELETE FROM notifications")
                        st.success("✅ Todas as notificações foram removidas!")
                        st.session_state.confirm_clear_all = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
            
            if st.button("❌ Cancelar"):
                st.session_state.confirm_clear_all = False
                st.rerun()

def show_notification_reports(notification_manager):
    """Mostra relatórios de notificações"""
    st.subheader("📊 Relatórios de Notificações")
    
    try:
        from app.database.local_connection import db_manager
        import pandas as pd
        import plotly.express as px
        
        # Notificações por dia (últimos 30 dias)
        daily_stats = db_manager.fetch_all("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total,
                SUM(CASE WHEN is_read = 1 THEN 1 ELSE 0 END) as read,
                SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) as unread
            FROM notifications 
            WHERE created_at >= DATE('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        
        if daily_stats:
            df = pd.DataFrame(daily_stats)
            
            fig = px.line(df, x='date', y=['total', 'read', 'unread'], 
                         title="Notificações por Dia (Últimos 30 dias)")
            st.plotly_chart(fig, use_container_width=True)
        
        # Notificações por tipo
        type_stats = db_manager.fetch_all("""
            SELECT 
                type,
                COUNT(*) as count
            FROM notifications 
            GROUP BY type
            ORDER BY count DESC
        """)
        
        if type_stats:
            df_types = pd.DataFrame(type_stats)
            
            fig_types = px.pie(df_types, values='count', names='type', 
                              title="Distribuição por Tipo")
            st.plotly_chart(fig_types, use_container_width=True)
        
        # Top usuários com mais notificações
        user_stats = db_manager.fetch_all("""
            SELECT 
                u.username,
                u.full_name,
                COUNT(n.id) as notification_count,
                SUM(CASE WHEN n.is_read = 1 THEN 1 ELSE 0 END) as read_count
            FROM users u
            LEFT JOIN notifications n ON u.id = n.user_id
            GROUP BY u.id, u.username, u.full_name
            HAVING notification_count > 0
            ORDER BY notification_count DESC
            LIMIT 10
        """)
        
        if user_stats:
            st.subheader("🏆 Top Usuários (Mais Notificações)")
            
            for user in user_stats:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{user['full_name']}** ({user['username']})")
                with col2:
                    st.write(f"Total: {user['notification_count']}")
                with col3:
                    st.write(f"Lidas: {user['read_count']}")
    
    except Exception as e:
        st.error(f"❌ Erro ao gerar relatórios: {str(e)}")

def export_notifications(notifications):
    """Exporta notificações para CSV"""
    try:
        import pandas as pd
        
        df = pd.DataFrame(notifications)
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="📥 Baixar CSV",
            data=csv,
            file_name=f"notifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"❌ Erro ao exportar: {str(e)}")