import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from app.config.settings import load_config
from app.database.local_connection import init_database
from app.components.sidebar import render_sidebar
from app.modules.dashboard import render_dashboard
from app.modules.planner import render_planner
from app.modules.scheduling import render_scheduling
from app.modules.content_management import render_content_management
from app.modules.attendance import render_attendance
from app.modules.communication import render_communication
from app.modules.whatsapp_api_refactored import render_whatsapp_api
from app.modules.ai_assistant import render_ai_assistant
from app.modules.admin import render_admin
from app.modules.bible import render_bible_module
from app.pages.notifications import render_notifications
from app.utils.auth import check_authentication, show_auth_form, get_current_user, is_admin, create_password_recovery_table, create_user_sessions_table
from app.utils.security_monitor import SecurityMonitor
from app.utils.notifications import create_notification_tables, show_notification_badge
from app.utils.styles import get_custom_css

# Importar melhorias implementadas
from app.utils.cache_manager import CacheManager, smart_cache, cache_manager
from app.utils.security_enhanced import SecurityLogger, create_security_tables
from app.utils.monitoring_enhanced import get_monitoring_system, PerformanceMonitor
from app.components.ui_enhanced import LoadingManager, NotificationManager
from app.utils.performance_optimizer import PerformanceOptimizer
from app.utils.memory_optimizer import memory_optimizer, start_memory_monitoring
from app.utils.lazy_loading import lazy_loader

def main():
    """Função principal da aplicação"""
    try:
        # Configuração da página
        st.set_page_config(
            page_title="Ujoad - Aplicação de Gestão",
            page_icon="⛪",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Carregar configurações
        load_config()
        
        # Inicializar banco de dados
        init_database()
        
        # Inicializar sistemas adicionais
        create_notification_tables()
        create_password_recovery_table()
        
        # Criar/atualizar tabela de sessões com suporte a dispositivos
        try:
            create_user_sessions_table()
        except Exception as e:
            if st.session_state.get('debug_mode', False):
                st.warning(f"Aviso: Erro ao criar/atualizar tabela de sessões: {e}")
        
        SecurityMonitor.create_security_tables()
        
        # Inicializar melhorias implementadas
        try:
            # Sistema de cache
            if 'cache_manager' not in st.session_state:
                st.session_state.cache_manager = CacheManager()
            
            # Sistema de segurança melhorado
            create_security_tables()
            
            # Sistema de monitoramento
            monitoring_system = get_monitoring_system()
            
            # Managers de UI
            if 'loading_manager' not in st.session_state:
                st.session_state.loading_manager = LoadingManager()
            if 'notification_manager' not in st.session_state:
                st.session_state.notification_manager = NotificationManager()
            
            # Inicializar novos sistemas de otimização
            performance_optimizer = PerformanceOptimizer()
            
            # Iniciar monitoramento de memória
            start_memory_monitoring()
            
            # Configurar otimizações do Streamlit
            performance_optimizer.optimize_streamlit_config()
                
        except Exception as init_error:
            # Log do erro mas não interromper a aplicação
            if st.session_state.get('debug_mode', False):
                st.warning(f"Aviso: Algumas melhorias não foram inicializadas: {init_error}")
        
        # Aplicar CSS customizado
        st.markdown(get_custom_css(), unsafe_allow_html=True)
        
        # Verificar autenticação
        authenticated = False
        try:
            authenticated = check_authentication()
        except Exception as auth_error:
            # Log do erro apenas em modo debug
            if st.session_state.get('debug_mode', False):
                st.error(f"Erro de autenticação: {auth_error}")
            # Continuar com authenticated = False
        
        if authenticated:
            # Usuário autenticado - mostrar interface completa
            try:
                # Mostrar badge de notificações
                current_user = get_current_user()
                if current_user:
                    show_notification_badge(current_user.get('id'))
                
                # Header principal
                st.markdown("""
                <div class="main-header">
                    <h1>⛪ Ujoad - Sistema de Gerenciamento</h1>
                </div>
                """, unsafe_allow_html=True)
                
                # Renderizar sidebar e obter página selecionada
                selected_page = render_sidebar()
                
                # Renderizar página selecionada
                if selected_page == "Dashboard":
                    render_dashboard()
                elif selected_page == "Planner":
                    render_planner()
                elif selected_page == "Agendamento":
                    render_scheduling()
                elif selected_page == "Gerenciamento de Conteúdo":
                    render_content_management()
                elif selected_page == "Controle de Presença":
                    render_attendance()
                elif selected_page == "Comunicação":
                    render_communication()
                elif selected_page == "WhatsApp API":
                    render_whatsapp_api()
                elif selected_page == "Assistente IA":
                    render_ai_assistant()
                elif selected_page == "Notificações":
                    render_notifications()
                elif selected_page == "Bíblia":
                    render_bible_module()
                elif selected_page == "Dispositivos":
                    from app.pages.device_management import show_device_management
                    show_device_management()
                elif selected_page == "Monitoramento":
                    from app.pages.monitoring import render_monitoring_page
                    render_monitoring_page()
                elif selected_page == "performance_dashboard":
                    from app.pages.performance_dashboard import render_performance_dashboard
                    render_performance_dashboard()
                elif selected_page == "Segurança":
                    from app.pages.security import show_security_page
                    show_security_page()
                elif selected_page == "Backups":
                    from app.pages.backup import show_backup_page
                    show_backup_page()
                elif selected_page == "Administração":
                    render_admin()
                    
            except Exception as app_error:
                st.error("⚠️ Erro na aplicação")
                if st.session_state.get('debug_mode', False):
                    st.exception(app_error)
                st.info("🔄 Tente recarregar a página")
        else:
            # Usuário não autenticado - ocultar sidebar
            st.markdown("""
            <style>
            .css-1d391kg, .css-1rs6os, .css-17eq0hr {display: none !important;}
            .css-1lcbmhc {margin-left: 0 !important;}
            .main .block-container {padding-top: 2rem;}
            section[data-testid="stSidebar"] {display: none}
            </style>
            """, unsafe_allow_html=True)
            
            # Não mostrar erros de sidebar/estatísticas durante login
            with st.container():
                # Apenas mostrar o formulário de autenticação
                pass  # check_authentication() já cuida de mostrar o formulário
                
    except Exception as main_error:
        # Erro crítico da aplicação
        st.error("❌ Erro crítico na aplicação")
        st.markdown("### 🔧 Informações para o administrador:")
        
        if st.session_state.get('debug_mode', False):
            st.exception(main_error)
        else:
            st.code(str(main_error))
            
        st.markdown("### 🔄 Soluções possíveis:")
        st.markdown("""
        1. **Recarregue a página** (F5 ou Ctrl+R)
        2. **Limpe o cache** do navegador
        3. **Verifique a conexão** com o banco de dados
        4. **Entre em contato** com o suporte técnico
        """)
        
        # Botão para tentar novamente
        if st.button("🔄 Tentar Novamente", type="primary"):
            st.rerun()

if __name__ == "__main__":
    main()