"""
Sistema de notificações moderno para a aplicação
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.database.local_connection import db_manager
from app.utils.auth import get_current_user

class NotificationManager:
    """Gerenciador de notificações da aplicação"""
    
    @staticmethod
    def create_notification(user_id: str, title: str, message: str, 
                          notification_type: str = "info", priority: str = "normal",
                          action_url: str = None, expires_at: datetime = None):
        """Cria uma nova notificação"""
        try:
            if expires_at is None:
                expires_at = datetime.now() + timedelta(days=7)
            
            query = """
            INSERT INTO notifications (user_id, title, message, type, priority, action_url, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            db_manager.execute_query(query, (
                user_id, title, message, notification_type, priority, 
                action_url, expires_at.isoformat(), datetime.now().isoformat()
            ))
            
            return True
        except Exception as e:
            st.error(f"Erro ao criar notificação: {str(e)}")
            return False
    
    @staticmethod
    def get_user_notifications(user_id: str, unread_only: bool = False, limit: int = 50):
        """Obtém notificações do usuário"""
        try:
            base_query = """
            SELECT id, title, message, type, priority, action_url, is_read, created_at, expires_at
            FROM notifications 
            WHERE user_id = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
            """
            
            if unread_only:
                base_query += " AND is_read = 0"
            
            base_query += " ORDER BY priority DESC, created_at DESC LIMIT ?"
            
            result = db_manager.fetch_all(base_query, (user_id, limit))
            return result or []
        except Exception as e:
            st.error(f"Erro ao buscar notificações: {str(e)}")
            return []
    
    @staticmethod
    def mark_as_read(notification_id: int, user_id: str):
        """Marca notificação como lida"""
        try:
            query = "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?"
            db_manager.execute_query(query, (notification_id, user_id))
            return True
        except Exception as e:
            st.error(f"Erro ao marcar notificação como lida: {str(e)}")
            return False
    
    @staticmethod
    def mark_all_as_read(user_id: str):
        """Marca todas as notificações como lidas"""
        try:
            query = "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0"
            db_manager.execute_query(query, (user_id,))
            return True
        except Exception as e:
            st.error(f"Erro ao marcar todas as notificações como lidas: {str(e)}")
            return False
    
    @staticmethod
    def delete_notification(notification_id: int, user_id: str):
        """Deleta uma notificação"""
        try:
            query = "DELETE FROM notifications WHERE id = ? AND user_id = ?"
            db_manager.execute_query(query, (notification_id, user_id))
            return True
        except Exception as e:
            st.error(f"Erro ao deletar notificação: {str(e)}")
            return False
    
    @staticmethod
    def get_unread_count(user_id: str):
        """Obtém contagem de notificações não lidas"""
        try:
            query = """
            SELECT COUNT(*) as count 
            FROM notifications 
            WHERE user_id = ? AND is_read = 0 AND (expires_at IS NULL OR expires_at > datetime('now'))
            """
            result = db_manager.fetch_all(query, (user_id,))
            return result[0]['count'] if result else 0
        except Exception as e:
            return 0
    
    @staticmethod
    def cleanup_expired_notifications():
        """Remove notificações expiradas"""
        try:
            query = "DELETE FROM notifications WHERE expires_at IS NOT NULL AND expires_at <= datetime('now')"
            db_manager.execute_query(query)
            return True
        except Exception as e:
            return False
    
    @staticmethod
    def cleanup_old_notifications(user_id: str, days: int = 30, read_only: bool = False):
        """Remove notificações antigas"""
        try:
            if read_only:
                query = """
                DELETE FROM notifications 
                WHERE user_id = ? AND is_read = 1 AND created_at <= datetime('now', '-' || ? || ' days')
                """
            else:
                query = """
                DELETE FROM notifications 
                WHERE user_id = ? AND created_at <= datetime('now', '-' || ? || ' days')
                """
            db_manager.execute_query(query, (user_id, days))
            return True
        except Exception as e:
            st.error(f"Erro ao limpar notificações antigas: {str(e)}")
            return False

def render_notification_center():
    """Renderiza o centro de notificações"""
    current_user = get_current_user()
    if not current_user:
        return
    
    user_id = current_user.get('id')
    
    st.subheader("🔔 Central de Notificações")
    
    # Estatísticas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        unread_count = NotificationManager.get_unread_count(user_id)
        st.metric("Não Lidas", unread_count)
    
    with col2:
        all_notifications = NotificationManager.get_user_notifications(user_id)
        st.metric("Total", len(all_notifications))
    
    with col3:
        if st.button("✅ Marcar Todas como Lidas", use_container_width=True):
            if NotificationManager.mark_all_as_read(user_id):
                st.success("Todas as notificações foram marcadas como lidas!")
                st.rerun()
    
    st.divider()
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        show_unread_only = st.checkbox("Mostrar apenas não lidas", value=False)
    with col2:
        notification_limit = st.selectbox("Limite", [10, 25, 50, 100], index=1)
    
    # Lista de notificações
    notifications = NotificationManager.get_user_notifications(
        user_id, unread_only=show_unread_only, limit=notification_limit
    )
    
    if not notifications:
        st.info("📭 Nenhuma notificação encontrada.")
        return
    
    for notification in notifications:
        render_notification_card(notification, user_id)

def render_notification_card(notification: Dict, user_id: str):
    """Renderiza um card de notificação"""
    
    # Ícones por tipo
    type_icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "event": "📅",
        "message": "💬",
        "system": "⚙️"
    }
    
    # Cores por prioridade
    priority_colors = {
        "high": "#EF4444",
        "normal": "#3B82F6",
        "low": "#6B7280"
    }
    
    icon = type_icons.get(notification['type'], "📢")
    priority_color = priority_colors.get(notification['priority'], "#3B82F6")
    
    # Container da notificação
    with st.container():
        # Estilo baseado no status de leitura
        border_style = "2px solid #E5E7EB" if notification['is_read'] else f"2px solid {priority_color}"
        bg_color = "#F9FAFB" if notification['is_read'] else "#FFFFFF"
        
        st.markdown(f"""
        <div style="
            border: {border_style};
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            background-color: {bg_color};
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.2rem; margin-right: 0.5rem;">{icon}</span>
                        <h4 style="margin: 0; color: #1F2937; font-weight: 600;">
                            {notification['title']}
                        </h4>
                        {'' if notification['is_read'] else '<span style="background: #EF4444; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; margin-left: 0.5rem;">NOVO</span>'}
                    </div>
                    <p style="margin: 0 0 0.5rem 0; color: #4B5563; line-height: 1.5;">
                        {notification['message']}
                    </p>
                    <small style="color: #9CA3AF;">
                        📅 {datetime.fromisoformat(notification['created_at']).strftime('%d/%m/%Y às %H:%M')}
                    </small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botões de ação
        col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
        
        with col1:
            if not notification['is_read']:
                if st.button("👁️ Marcar como Lida", key=f"read_{notification['id']}", use_container_width=True):
                    if NotificationManager.mark_as_read(notification['id'], user_id):
                        st.rerun()
        
        with col2:
            if st.button("🗑️ Excluir", key=f"delete_{notification['id']}", use_container_width=True):
                if NotificationManager.delete_notification(notification['id'], user_id):
                    st.success("Notificação excluída!")
                    st.rerun()
        
        with col3:
            if notification['action_url']:
                st.markdown(f"[🔗 Ação]({notification['action_url']})")

def show_notification_badge(user_id: str):
    """Mostra badge de notificações não lidas"""
    unread_count = NotificationManager.get_unread_count(user_id)
    
    if unread_count > 0:
        st.markdown(f"""
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: #EF4444;
            color: white;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.875rem;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        ">
            {min(unread_count, 99)}
        </div>
        """, unsafe_allow_html=True)

def create_system_notifications():
    """Cria notificações do sistema para todos os usuários"""
    try:
        # Buscar todos os usuários ativos
        users_query = "SELECT id FROM users WHERE is_active = 1"
        users = db_manager.fetch_all(users_query)
        
        if not users:
            return
        
        # Notificação de boas-vindas para novos usuários
        welcome_title = "🎉 Bem-vindo ao Mídia Church!"
        welcome_message = """
        Seja bem-vindo à nossa plataforma! Aqui você pode:
        • Gerenciar eventos e atividades
        • Acompanhar presenças
        • Compartilhar conteúdos
        • Usar nosso assistente IA
        • E muito mais!
        """
        
        for user in users:
            # Verificar se já existe notificação de boas-vindas
            existing_query = """
            SELECT id FROM notifications 
            WHERE user_id = ? AND title = ? AND type = 'system'
            """
            existing = db_manager.fetch_all(existing_query, (user['id'], welcome_title))
            
            if not existing:
                NotificationManager.create_notification(
                    user_id=user['id'],
                    title=welcome_title,
                    message=welcome_message,
                    notification_type="system",
                    priority="normal"
                )
        
        return True
    except Exception as e:
        st.error(f"Erro ao criar notificações do sistema: {str(e)}")
        return False

def create_notification_tables():
    """Cria tabelas necessárias para notificações"""
    try:
        query = """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            priority TEXT DEFAULT 'normal',
            action_url TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        db_manager.execute_query(query)
        
        # Criar índices para melhor performance
        db_manager.execute_query("CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)")
        db_manager.execute_query("CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)")
        db_manager.execute_query("CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at)")
        
        return True
    except Exception as e:
        st.error(f"Erro ao criar tabelas de notificações: {str(e)}")
        return False