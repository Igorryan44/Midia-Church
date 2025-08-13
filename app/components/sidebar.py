import streamlit as st
from app.utils.auth import logout, get_current_user, is_admin
from app.database.local_connection import db_manager

def render_sidebar():
    """Renderiza a barra lateral com navegação"""
    
    with st.sidebar:
        try:
            # Verificar se há usuário autenticado
            user_info = get_current_user()
            if not user_info:
                st.error("⚠️ Sessão expirada")
                return "Dashboard"
            
            user_role = user_info.get('role', 'member')
            
            # Header personalizado baseado no tipo de usuário
            if user_role == 'admin':
                st.markdown("### 👑 Painel Administrativo")
                st.markdown(f"**{user_info.get('full_name', 'Administrador')}**")
                st.markdown("*Administrador do Sistema*")
            else:
                st.markdown("### 🙏 Bem-vindo!")
                st.markdown(f"**{user_info.get('full_name', 'Usuário')}**")
                st.markdown("*Membro da Igreja*")
            
            st.divider()
            
            # Menu de navegação
            st.markdown("### 📋 Menu Principal")
            
            # Páginas básicas para todos os usuários
            basic_pages = [
                ("🏠", "Dashboard"),
                ("📅", "Planner"),
                ("✅", "Controle de Presença"),
                ("💬", "Comunicação"),
                ("📱", "WhatsApp API"),
                ("🔔", "Notificações"),
                ("📖", "Bíblia"),
                ("🔐", "Dispositivos")
            ]
            
            # Páginas administrativas (apenas para admins)
            admin_pages = [
                ("⏰", "Agendamento"),
                ("📁", "Gerenciamento de Conteúdo"),
                ("🤖", "Assistente IA"),
                ("📊", "Monitoramento"),
                ("⚡", "Performance"),
                ("🛡️", "Segurança"),
                ("💾", "Backups"),
                ("🔧", "Administração")
            ]
            
            # Inicializar página atual se não existir
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 'Dashboard'
            
            selected_page = st.session_state.current_page
            
            # Renderizar páginas básicas
            for icon, page_name in basic_pages:
                button_type = "primary" if st.session_state.current_page == page_name else "secondary"
                if st.button(f"{icon} {page_name}", use_container_width=True, type=button_type, key=f"btn_{page_name}"):
                    st.session_state.current_page = page_name
                    selected_page = page_name
                    st.rerun()
            
            # Renderizar páginas administrativas apenas para admins
            try:
                if is_admin():
                    st.markdown("---")
                    st.markdown("### ⚙️ Administração")
                    for icon, page_name in admin_pages:
                        button_type = "primary" if st.session_state.current_page == page_name else "secondary"
                        if st.button(f"{icon} {page_name}", use_container_width=True, type=button_type, key=f"btn_admin_{page_name}"):
                            st.session_state.current_page = page_name
                            selected_page = page_name
                            st.rerun()
            except Exception:
                # Se houver erro ao verificar admin, não mostrar páginas admin
                pass
            
            # Verificar se usuário comum está tentando acessar página admin
            admin_only_pages = ["Agendamento", "Gerenciamento de Conteúdo", "Assistente IA", "Monitoramento", "Segurança", "Backups", "Administração"]
            try:
                if not is_admin() and selected_page in admin_only_pages:
                    st.session_state.current_page = "Dashboard"
                    selected_page = "Dashboard"
                    st.warning("⚠️ Acesso restrito a administradores!")
            except Exception:
                # Se houver erro ao verificar admin, redirecionar para dashboard
                if selected_page in admin_only_pages:
                    st.session_state.current_page = "Dashboard"
                    selected_page = "Dashboard"
            
            st.divider()
            
            # Estatísticas rápidas
            render_quick_stats()
            
            st.divider()
            
            # Botão de logout
            if st.button("🚪 Sair", use_container_width=True, type="secondary", key="btn_logout"):
                logout()
                st.rerun()
            
            # Informações adicionais
            st.markdown("---")
            st.markdown("### ℹ️ Informações")
            st.markdown("**Mídia Church v1.0**")
            st.markdown("Sistema de Gerenciamento para Igrejas")
            
            # Mostrar informações técnicas apenas para admins
            try:
                if is_admin():
                    st.caption("🔧 Modo Administrador Ativo")
            except Exception:
                pass
            
            return selected_page
            
        except Exception as e:
            # Em caso de erro crítico na sidebar
            st.error("⚠️ Erro na navegação")
            if st.session_state.get('debug_mode', False):
                st.exception(e)
            return "Dashboard"

def render_quick_stats():
    """Renderiza estatísticas rápidas na sidebar"""
    
    st.markdown("### 📊 Resumo Rápido")
    
    try:
        from app.database.local_connection import db_manager
        
        # Verificar se há usuário autenticado antes de buscar estatísticas
        user_info = get_current_user()
        if not user_info:
            st.caption("📊 Faça login para ver estatísticas")
            return
        
        # Próximos eventos
        try:
            query = """
            SELECT COUNT(*) as count FROM events 
            WHERE start_datetime > datetime('now') AND is_active = 1
            """
            result = db_manager.fetch_all(query)
            next_events = result[0]['count'] if result and len(result) > 0 else 0
        except Exception:
            next_events = "N/A"
        
        # Eventos hoje
        try:
            query = """
            SELECT COUNT(*) as count FROM events 
            WHERE date(start_datetime) = date('now') AND is_active = 1
            """
            result = db_manager.fetch_all(query)
            today_events = result[0]['count'] if result and len(result) > 0 else 0
        except Exception:
            today_events = "N/A"
        
        # Total de usuários (apenas para admins)
        try:
            if is_admin():
                query = "SELECT COUNT(*) as count FROM users WHERE is_active = 1"
                result = db_manager.fetch_all(query)
                total_users = result[0]['count'] if result and len(result) > 0 else 0
                st.metric("👥 Usuários", total_users)
        except Exception:
            if user_info.get('role') == 'admin':
                st.metric("👥 Usuários", "N/A")
        
        st.metric("📅 Próximos Eventos", next_events)
        st.metric("🗓️ Eventos Hoje", today_events)
        
    except Exception as e:
        # Em caso de erro geral, mostrar estatísticas básicas
        st.caption("📊 Estatísticas temporariamente indisponíveis")
        if st.session_state.get('debug_mode', False):
            st.caption(f"Erro: {str(e)}")
        
        # Mostrar métricas padrão
        st.metric("📅 Próximos Eventos", "N/A")
        st.metric("🗓️ Eventos Hoje", "N/A")