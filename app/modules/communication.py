import streamlit as st
import pandas as pd
from datetime import datetime
from app.database.local_connection import db_manager, get_all_users
from app.utils.auth import get_current_user
from app.utils.validation import DataValidator, SecurityHelper
from app.utils.responsive import apply_responsive_layout, responsive_metric_cards

def render_communication():
    """Renderiza o módulo de comunicação interna"""
    
    st.title("💬 Comunicação Interna")
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3, tab4 = st.tabs(["📢 Anúncios", "💬 Fórum", "📝 Nova Postagem", "📊 Estatísticas"])
    
    with tab1:
        render_announcements()
    
    with tab2:
        render_forum()
    
    with tab3:
        render_new_post()
    
    with tab4:
        render_communication_stats()

def render_announcements():
    """Renderiza a seção de anúncios"""
    
    st.subheader("📢 Anúncios e Notícias")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        filter_type = st.selectbox(
            "Tipo de Postagem",
            options=["Todos", "Anúncio", "Notícia", "Aviso", "Comunicado"]
        )
    
    with col2:
        show_pinned_only = st.checkbox("Apenas postagens fixadas")
    
    # Buscar anúncios
    announcements = get_filtered_posts("announcement", filter_type, show_pinned_only)
    
    if announcements:
        for post in announcements:
            render_post_card(post, show_comments=True)
    else:
        st.info("Nenhum anúncio encontrado.")

def render_forum():
    """Renderiza o fórum de discussões"""
    
    st.subheader("💬 Fórum de Discussões")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        sort_by = st.selectbox(
            "Ordenar por",
            options=["Mais Recente", "Mais Antigo", "Mais Comentado"]
        )
    
    with col2:
        search_term = st.text_input("🔍 Buscar discussões", placeholder="Digite para buscar...")
    
    # Buscar discussões do fórum
    forum_posts = get_filtered_posts("discussion", search_term=search_term, sort_by=sort_by)
    
    if forum_posts:
        for post in forum_posts:
            render_post_card(post, show_comments=True, is_forum=True)
    else:
        st.info("Nenhuma discussão encontrada.")

def render_new_post():
    """Renderiza o formulário para nova postagem"""
    
    st.subheader("📝 Nova Postagem")
    
    # Verificar permissões
    user_info = get_current_user()
    is_admin = user_info.get('role') == 'admin'
    
    with st.form("new_post_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Título *", placeholder="Título da postagem")
            
            post_type = st.selectbox(
                "Tipo de Postagem *",
                options=["Discussão", "Anúncio", "Notícia", "Aviso", "Comunicado"] if is_admin else ["Discussão"]
            )
        
        with col2:
            if is_admin:
                is_pinned = st.checkbox("📌 Fixar postagem")
                priority = st.selectbox(
                    "Prioridade",
                    options=["Normal", "Alta", "Urgente"]
                )
            else:
                is_pinned = False
                priority = "Normal"
        
        content = st.text_area(
            "Conteúdo *", 
            placeholder="Escreva o conteúdo da postagem...",
            height=200
        )
        
        # Tags
        tags = st.text_input("Tags", placeholder="tag1, tag2, tag3")
        
        submitted = st.form_submit_button("📤 Publicar", use_container_width=True)
        
        if submitted:
            if title and content:
                success = create_post(
                    title=title,
                    content=content,
                    post_type=post_type.lower(),
                    is_pinned=is_pinned,
                    author_id=get_user_id(user_info['username'])
                )
                
                if success:
                    st.success("✅ Postagem criada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao criar postagem. Tente novamente.")
            else:
                st.error("⚠️ Preencha todos os campos obrigatórios!")

def render_communication_stats():
    """Renderiza estatísticas de comunicação"""
    
    st.subheader("📊 Estatísticas de Comunicação")
    
    # Métricas gerais
    stats = get_communication_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Total de Postagens", stats['total_posts'])
    
    with col2:
        st.metric("💬 Total de Comentários", stats['total_comments'])
    
    with col3:
        st.metric("👥 Usuários Ativos", stats['active_users'])
    
    with col4:
        st.metric("📈 Postagens este Mês", stats['posts_this_month'])
    
    st.divider()
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Postagens por Tipo")
        posts_by_type = get_posts_by_type_data()
        
        if posts_by_type:
            df_types = pd.DataFrame(posts_by_type)
            st.bar_chart(df_types.set_index('post_type')['count'])
        else:
            st.info("Nenhum dado disponível")
    
    with col2:
        st.subheader("📈 Atividade Mensal")
        monthly_activity = get_monthly_activity_data()
        
        if monthly_activity:
            df_monthly = pd.DataFrame(monthly_activity)
            st.line_chart(df_monthly.set_index('month')[['posts', 'comments']])
        else:
            st.info("Nenhum dado disponível")
    
    # Usuários mais ativos
    st.subheader("🏆 Usuários Mais Ativos")
    top_users = get_top_active_users()
    
    if top_users:
        for i, user in enumerate(top_users[:10], 1):
            col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
            
            with col1:
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}º"
                st.markdown(f"**{medal}**")
            
            with col2:
                st.write(f"👤 {user['full_name']}")
            
            with col3:
                st.write(f"📝 {user['post_count']}")
            
            with col4:
                st.write(f"💬 {user['comment_count']}")

def render_post_card(post, show_comments=False, is_forum=False):
    """Renderiza um card de postagem"""
    
    with st.container():
        # Header do post
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # Ícone de prioridade/tipo
            post_icon = get_post_icon(post['post_type'])
            pin_icon = "📌 " if post['is_pinned'] else ""
            
            st.markdown(f"### {pin_icon}{post_icon} {post['title']}")
        
        with col2:
            created_date = datetime.fromisoformat(post['created_at'])
            st.caption(f"📅 {created_date.strftime('%d/%m/%Y')}")
        
        with col3:
            st.caption(f"👤 {post['author_name']}")
        
        # Conteúdo do post
        st.write(post['content'])
        
        # Ações e estatísticas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            comment_count = get_comment_count(post['id'])
            st.caption(f"💬 {comment_count} comentários")
        
        with col2:
            if st.button("💬 Comentar", key=f"comment_{post['id']}"):
                st.session_state[f"show_comment_form_{post['id']}"] = True
        
        with col3:
            if is_forum and st.button("👍 Curtir", key=f"like_{post['id']}"):
                st.success("Curtido!")
        
        with col4:
            user_info = get_current_user()
            if (user_info.get('role') == 'admin' or 
                post['author_name'] == user_info.get('full_name')):
                if st.button("✏️ Editar", key=f"edit_{post['id']}"):
                    st.session_state[f"editing_post_{post['id']}"] = True
        
        # Formulário de comentário
        if st.session_state.get(f"show_comment_form_{post['id']}", False):
            render_comment_form(post['id'])
        
        # Mostrar comentários
        if show_comments:
            render_comments(post['id'])
        
        st.divider()

def render_comment_form(post_id):
    """Renderiza formulário de comentário"""
    
    with st.form(f"comment_form_{post_id}"):
        comment_content = st.text_area("Seu comentário", placeholder="Escreva seu comentário...")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💬 Comentar"):
                if comment_content:
                    user_info = get_current_user()
                    success = create_comment(
                        post_id=post_id,
                        content=comment_content,
                        author_id=get_user_id(user_info['username'])
                    )
                    
                    if success:
                        st.success("Comentário adicionado!")
                        st.session_state[f"show_comment_form_{post_id}"] = False
                        st.rerun()
                    else:
                        st.error("Erro ao adicionar comentário.")
                else:
                    st.error("Digite um comentário!")
        
        with col2:
            if st.form_submit_button("❌ Cancelar"):
                st.session_state[f"show_comment_form_{post_id}"] = False
                st.rerun()

def render_comments(post_id):
    """Renderiza comentários de uma postagem"""
    
    comments = get_post_comments(post_id)
    
    if comments:
        st.markdown("#### 💬 Comentários")
        
        for comment in comments:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**👤 {comment['author_name']}**")
                    st.write(comment['content'])
                
                with col2:
                    created_date = datetime.fromisoformat(comment['created_at'])
                    st.caption(f"📅 {created_date.strftime('%d/%m/%Y %H:%M')}")
                
                st.markdown("---")

def get_post_icon(post_type):
    """Retorna ícone para o tipo de postagem"""
    icons = {
        'announcement': '📢',
        'discussion': '💬',
        'news': '📰',
        'notice': '📋',
        'communication': '📨'
    }
    return icons.get(post_type, '📝')

def get_filtered_posts(post_type_filter=None, filter_type=None, show_pinned_only=False, search_term=None, sort_by="Mais Recente"):
    """Busca postagens com filtros aplicados"""
    try:
        query = """
        SELECT p.*, u.full_name as author_name
        FROM posts p
        JOIN users u ON p.author_id = u.id
        WHERE p.is_active = 1
        """
        params = []
        
        # Filtro por tipo de postagem
        if post_type_filter:
            query += " AND p.post_type = ?"
            params.append(post_type_filter)
        
        # Filtro adicional por tipo
        if filter_type and filter_type != "Todos":
            query += " AND p.post_type = ?"
            params.append(filter_type.lower())
        
        # Filtro por postagens fixadas
        if show_pinned_only:
            query += " AND p.is_pinned = 1"
        
        # Filtro por termo de busca
        if search_term:
            query += " AND (p.title LIKE ? OR p.content LIKE ?)"
            search_param = f"%{search_term}%"
            params.extend([search_param, search_param])
        
        # Ordenação
        if sort_by == "Mais Recente":
            query += " ORDER BY p.is_pinned DESC, p.created_at DESC"
        elif sort_by == "Mais Antigo":
            query += " ORDER BY p.is_pinned DESC, p.created_at ASC"
        elif sort_by == "Mais Comentado":
            query += """
            ORDER BY p.is_pinned DESC, 
            (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) DESC,
            p.created_at DESC
            """
        
        return db_manager.fetch_all(query, params)
    except:
        return []

def create_post(title, content, post_type, is_pinned, author_id):
    """Cria uma nova postagem"""
    try:
        query = """
        INSERT INTO posts (title, content, post_type, is_pinned, author_id)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (title, content, post_type, is_pinned, author_id)
        db_manager.execute_query(query, params)
        return True
    except Exception as e:
        st.error(f"Erro ao criar postagem: {e}")
        return False

def create_comment(post_id, content, author_id):
    """Cria um novo comentário"""
    try:
        query = """
        INSERT INTO comments (post_id, content, author_id)
        VALUES (?, ?, ?)
        """
        params = (post_id, content, author_id)
        db_manager.execute_query(query, params)
        return True
    except Exception as e:
        st.error(f"Erro ao criar comentário: {e}")
        return False

def get_comment_count(post_id):
    """Retorna o número de comentários de uma postagem"""
    try:
        query = "SELECT COUNT(*) as count FROM comments WHERE post_id = ? AND is_active = 1"
        result = db_manager.fetch_all(query, (post_id,))
        return result[0]['count'] if result else 0
    except:
        return 0

def get_post_comments(post_id):
    """Busca comentários de uma postagem"""
    try:
        query = """
        SELECT c.*, u.full_name as author_name
        FROM comments c
        JOIN users u ON c.author_id = u.id
        WHERE c.post_id = ? AND c.is_active = 1
        ORDER BY c.created_at ASC
        """
        return db_manager.fetch_all(query, (post_id,))
    except:
        return []

def get_user_id(username):
    """Busca o ID do usuário pelo username"""
    try:
        query = "SELECT id FROM users WHERE username = ?"
        result = db_manager.fetch_all(query, (username,))
        return result[0]['id'] if result else None
    except:
        return None

def get_user_id_by_username(username):
    """Busca o ID do usuário pelo username (alias para compatibilidade)"""
    return get_user_id(username)

def send_message(recipient_type, recipients, subject, message, priority):
    """Envia mensagem com validação completa"""
    try:
        # Validar dados de entrada
        if not subject or len(subject.strip()) == 0:
            st.error("Assunto é obrigatório")
            return False
            
        if not message or len(message.strip()) == 0:
            st.error("Mensagem é obrigatória")
            return False
            
        if not recipients:
            st.error("Pelo menos um destinatário deve ser selecionado")
            return False
        
        # Sanitizar dados
        subject = DataValidator.sanitize_string(subject, 200)
        message = DataValidator.sanitize_html(message)
        priority = DataValidator.sanitize_string(priority, 20)
        
        # Obter usuário atual
        user_info = get_current_user()
        sender_id = get_user_id_by_username(user_info.get('username', ''))
        
        # Log de segurança
        SecurityHelper.log_security_event(
            "MESSAGE_SEND_ATTEMPT", 
            f"User {user_info.get('username')} attempting to send message: {subject}",
            str(sender_id)
        )
        
        # Inserir mensagem
        query = """
        INSERT INTO messages (sender_id, recipient_type, subject, message, priority, sent_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        message_id = db_manager.execute_query(query, (
            sender_id, recipient_type, subject, message, priority, datetime.now()
        ), return_id=True)
        
        # Inserir destinatários
        for recipient_id in recipients:
            recipient_query = """
            INSERT INTO message_recipients (message_id, recipient_id, status)
            VALUES (?, ?, 'sent')
            """
            db_manager.execute_query(recipient_query, (message_id, recipient_id))
        
        # Log de sucesso
        SecurityHelper.log_security_event(
            "MESSAGE_SENT", 
            f"Message sent successfully: {subject} to {len(recipients)} recipients by {user_info.get('username')}",
            str(sender_id)
        )
        
        return True
        
    except Exception as e:
        # Log de erro
        user_info = get_current_user()
        SecurityHelper.log_security_event(
            "MESSAGE_SEND_ERROR", 
            f"Error sending message: {str(e)} by {user_info.get('username')}",
            str(get_user_id_by_username(user_info.get('username', '')))
        )
        st.error(f"Erro ao enviar mensagem: {e}")
        return False

def get_communication_stats():
    """Busca estatísticas de comunicação"""
    try:
        # Total de postagens
        total_posts_query = "SELECT COUNT(*) as count FROM posts WHERE is_active = 1"
        total_posts = db_manager.fetch_all(total_posts_query)[0]['count']
        
        # Total de comentários
        total_comments_query = "SELECT COUNT(*) as count FROM comments WHERE is_active = 1"
        total_comments = db_manager.fetch_all(total_comments_query)[0]['count']
        
        # Usuários ativos (que fizeram pelo menos uma postagem ou comentário)
        active_users_query = """
        SELECT COUNT(DISTINCT user_id) as count FROM (
            SELECT author_id as user_id FROM posts WHERE is_active = 1
            UNION
            SELECT author_id as user_id FROM comments WHERE is_active = 1
        )
        """
        active_users = db_manager.fetch_all(active_users_query)[0]['count']
        
        # Postagens este mês
        posts_this_month_query = """
        SELECT COUNT(*) as count FROM posts 
        WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
        AND is_active = 1
        """
        posts_this_month = db_manager.fetch_all(posts_this_month_query)[0]['count']
        
        return {
            'total_posts': total_posts,
            'total_comments': total_comments,
            'active_users': active_users,
            'posts_this_month': posts_this_month
        }
    except:
        return {
            'total_posts': 0,
            'total_comments': 0,
            'active_users': 0,
            'posts_this_month': 0
        }

def get_posts_by_type_data():
    """Busca dados de postagens por tipo"""
    try:
        query = """
        SELECT post_type, COUNT(*) as count
        FROM posts
        WHERE is_active = 1
        GROUP BY post_type
        """
        return db_manager.fetch_all(query)
    except:
        return []

def get_monthly_activity_data():
    """Busca dados de atividade mensal"""
    try:
        query = """
        SELECT 
            strftime('%Y-%m', created_at) as month,
            COUNT(*) as posts,
            (SELECT COUNT(*) FROM comments c WHERE strftime('%Y-%m', c.created_at) = strftime('%Y-%m', p.created_at)) as comments
        FROM posts p
        WHERE is_active = 1
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY month
        """
        return db_manager.fetch_all(query)
    except:
        return []

def get_top_active_users():
    """Busca usuários mais ativos"""
    try:
        query = """
        SELECT 
            u.full_name,
            COUNT(DISTINCT p.id) as post_count,
            COUNT(DISTINCT c.id) as comment_count,
            (COUNT(DISTINCT p.id) + COUNT(DISTINCT c.id)) as total_activity
        FROM users u
        LEFT JOIN posts p ON u.id = p.author_id AND p.is_active = 1
        LEFT JOIN comments c ON u.id = c.author_id AND c.is_active = 1
        WHERE u.is_active = 1
        GROUP BY u.id, u.full_name
        HAVING total_activity > 0
        ORDER BY total_activity DESC
        """
        return db_manager.fetch_all(query)
    except:
        return []