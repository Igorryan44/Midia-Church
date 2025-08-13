import streamlit as st
import os
import mimetypes
import zipfile
import io
from datetime import datetime
from pathlib import Path
from app.database.local_connection import db_manager, get_all_users
from app.utils.auth import get_current_user, is_admin
from app.config.settings import CONFIG

def render_content_management():
    """Renderiza o módulo de gerenciamento de conteúdo"""
    
    st.title("📁 Gerenciamento de Conteúdo")
    
    # Verificar se é administrador para funcionalidades avançadas
    user_is_admin = is_admin()
    
    if user_is_admin:
        # Tabs para administradores (com funcionalidades completas)
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📂 Biblioteca", 
            "⬆️ Upload", 
            "⬇️ Downloads", 
            "🏷️ Categorias", 
            "📊 Relatórios"
        ])
        
        with tab1:
            render_media_library()
        
        with tab2:
            render_upload_section()
        
        with tab3:
            render_download_management()
        
        with tab4:
            render_categories_management()
        
        with tab5:
            render_content_reports()
    else:
        # Tabs para usuários comuns (funcionalidades limitadas)
        tab1, tab2, tab3 = st.tabs(["📂 Biblioteca", "⬆️ Upload", "📊 Relatórios"])
        
        with tab1:
            render_media_library()
        
        with tab2:
            render_upload_section()
        
        with tab3:
            render_content_reports()

def render_media_library():
    """Renderiza a biblioteca de mídia"""
    
    st.subheader("📂 Biblioteca de Mídia")
    
    # Filtros e busca
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_term = st.text_input("🔍 Buscar", placeholder="Digite para buscar...")
    
    with col2:
        filter_category = st.selectbox(
            "Categoria",
            options=["Todas"] + get_categories()
        )
    
    with col3:
        filter_type = st.selectbox(
            "Tipo de Arquivo",
            options=["Todos", "Imagem", "Vídeo", "Áudio", "Documento"]
        )
    
    with col4:
        sort_by = st.selectbox(
            "Ordenar por",
            options=["Mais Recente", "Mais Antigo", "Nome A-Z", "Nome Z-A", "Tamanho"]
        )
    
    # Buscar conteúdo
    content_items = get_filtered_content(search_term, filter_category, filter_type, sort_by)
    
    if content_items:
        # Visualização em grid
        cols_per_row = 3
        for i in range(0, len(content_items), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j, col in enumerate(cols):
                if i + j < len(content_items):
                    item = content_items[i + j]
                    
                    with col:
                        render_content_card(item)
    else:
        st.info("Nenhum conteúdo encontrado com os filtros selecionados.")

def render_content_card(item):
    """Renderiza um card de conteúdo"""
    
    with st.container():
        # Ícone baseado no tipo de arquivo
        file_icon = get_file_icon(item['file_type'])
        
        st.markdown(f"### {file_icon} {item['title']}")
        
        # Informações do arquivo
        file_size = format_file_size(item['file_size']) if item['file_size'] else "N/A"
        upload_date = datetime.fromisoformat(item['uploaded_at']).strftime('%d/%m/%Y')
        
        st.caption(f"📅 {upload_date} | 📏 {file_size}")
        
        if item['description']:
            st.write(item['description'])
        
        # Tags
        if item['tags']:
            tags = item['tags'].split(',')
            tag_html = " ".join([f"<span style='background-color: #EFF6FF; color: #1E40AF; padding: 4px 8px; border-radius: 8px; font-size: 12px; font-weight: 600; border: 1px solid #DBEAFE;'>#{tag.strip()}</span>" for tag in tags])
            st.markdown(tag_html, unsafe_allow_html=True)
        
        # Botões de ação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👁️ Ver", key=f"view_{item['id']}", use_container_width=True):
                view_content(item)
        
        with col2:
            if st.button("⬇️ Download", key=f"download_{item['id']}", use_container_width=True):
                download_content(item)
        
        with col3:
            if st.button("🗑️ Excluir", key=f"delete_{item['id']}", use_container_width=True):
                if delete_content(item['id']):
                    st.success("Conteúdo excluído!")
                    st.rerun()
        
        st.divider()

def render_upload_section():
    """Renderiza a seção de upload"""
    
    st.subheader("⬆️ Upload de Arquivos")
    
    # Verificar se é admin para funcionalidades avançadas
    user_is_admin = is_admin()
    
    # Informações sobre limites
    max_size = CONFIG.get('MAX_UPLOAD_SIZE', '50MB')
    allowed_extensions = CONFIG.get('ALLOWED_EXTENSIONS', ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mp3', 'pdf', 'doc', 'docx'])
    
    st.info(f"""
    **Limites de Upload:**
    - Tamanho máximo: {max_size}
    - Tipos permitidos: {', '.join(allowed_extensions)}
    - Status: {'👑 Administrador' if user_is_admin else '👤 Usuário'}
    """)
    
    with st.form("upload_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Título *", placeholder="Nome do arquivo")
            category = st.selectbox(
                "Categoria *",
                options=get_categories()
            )
            tags = st.text_input("Tags", placeholder="tag1, tag2, tag3")
        
        with col2:
            uploaded_file = st.file_uploader(
                "Escolher arquivo *",
                type=allowed_extensions
            )
            
            if uploaded_file:
                # Validações de segurança
                file_valid, validation_message = validate_uploaded_file(uploaded_file, user_is_admin)
                
                if file_valid:
                    st.success(f"✅ Arquivo válido: {uploaded_file.name}")
                    st.info(f"📏 Tamanho: {format_file_size(uploaded_file.size)}")
                    
                    # Informações adicionais para admins
                    if user_is_admin:
                        st.caption(f"🔍 Tipo MIME: {uploaded_file.type}")
                else:
                    st.error(f"❌ {validation_message}")
        
        description = st.text_area("Descrição", placeholder="Descreva o conteúdo...")
        
        # Opções avançadas para administradores
        if user_is_admin:
            with st.expander("⚙️ Opções Avançadas (Admin)", expanded=False):
                priority = st.selectbox(
                    "Prioridade",
                    options=["Normal", "Alta", "Crítica"],
                    help="Define a prioridade do arquivo no sistema"
                )
                
                visibility = st.selectbox(
                    "Visibilidade",
                    options=["Público", "Restrito", "Privado"],
                    help="Define quem pode acessar este arquivo"
                )
                
                auto_backup = st.checkbox(
                    "Backup automático",
                    value=True,
                    help="Incluir este arquivo nos backups automáticos"
                )
        else:
            priority = "Normal"
            visibility = "Público"
            auto_backup = True
        
        submitted = st.form_submit_button("📤 Fazer Upload", use_container_width=True)
        
        if submitted:
            if title and category and uploaded_file:
                # Validar arquivo novamente antes do upload
                file_valid, validation_message = validate_uploaded_file(uploaded_file, user_is_admin)
                
                if file_valid:
                    success = upload_file_enhanced(
                        uploaded_file, title, description, category, tags,
                        priority, visibility, auto_backup
                    )
                    
                    if success:
                        st.success("✅ Arquivo enviado com sucesso!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao enviar arquivo. Tente novamente.")
                else:
                    st.error(f"❌ {validation_message}")
            else:
                st.error("⚠️ Preencha todos os campos obrigatórios!")

def render_download_management():
    """Renderiza o gerenciamento de downloads para administradores"""
    
    if not is_admin():
        st.error("🚫 Acesso negado! Esta funcionalidade é restrita a administradores.")
        return
    
    st.subheader("⬇️ Gerenciamento de Downloads")
    st.markdown("*Funcionalidades avançadas de download para administradores*")
    
    # Seção de downloads em lote
    st.markdown("### 📦 Downloads em Lote")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Filtros para Download")
        
        # Filtros para seleção
        download_category = st.selectbox(
            "Categoria",
            options=["Todas"] + get_categories(),
            key="download_category"
        )
        
        download_type = st.selectbox(
            "Tipo de Arquivo",
            options=["Todos", "Imagem", "Vídeo", "Áudio", "Documento"],
            key="download_type"
        )
        
        date_range = st.date_input(
            "Período de Upload",
            value=[],
            key="download_date_range"
        )
        
        # Buscar arquivos baseado nos filtros
        filtered_files = get_filtered_content_for_download(download_category, download_type, date_range)
        
        if filtered_files:
            st.success(f"✅ {len(filtered_files)} arquivo(s) encontrado(s)")
            
            # Mostrar lista de arquivos selecionados
            with st.expander("📋 Arquivos Selecionados", expanded=True):
                for file in filtered_files[:10]:  # Mostrar apenas os primeiros 10
                    st.write(f"• {file['title']} ({format_file_size(file['file_size'])})")
                
                if len(filtered_files) > 10:
                    st.caption(f"... e mais {len(filtered_files) - 10} arquivo(s)")
        else:
            st.info("ℹ️ Nenhum arquivo encontrado com os filtros selecionados")
    
    with col2:
        st.markdown("#### Opções de Download")
        
        if filtered_files:
            # Calcular tamanho total
            total_size = sum(file.get('file_size', 0) for file in filtered_files)
            st.metric("📊 Tamanho Total", format_file_size(total_size))
            
            # Opções de download
            download_format = st.radio(
                "Formato de Download",
                options=["ZIP Compactado", "Arquivos Individuais"],
                key="download_format"
            )
            
            include_metadata = st.checkbox(
                "Incluir arquivo de metadados (CSV)",
                value=True,
                key="include_metadata"
            )
            
            # Botão de download em lote
            if st.button("📦 Baixar Arquivos Selecionados", use_container_width=True):
                if download_format == "ZIP Compactado":
                    download_zip_package(filtered_files, include_metadata)
                else:
                    st.info("💡 Use os botões individuais na biblioteca para baixar arquivos separadamente")
        else:
            st.info("🔍 Configure os filtros para selecionar arquivos")
    
    st.divider()
    
    # Seção de estatísticas de download
    st.markdown("### 📈 Estatísticas de Download")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_downloads = get_total_downloads_count()
        st.metric("📥 Total de Downloads", total_downloads)
    
    with col2:
        downloads_today = get_downloads_today_count()
        st.metric("📅 Downloads Hoje", downloads_today)
    
    with col3:
        most_downloaded = get_most_downloaded_file()
        st.metric("🏆 Mais Baixado", most_downloaded or "N/A")
    
    with col4:
        avg_file_size = get_average_file_size()
        st.metric("📊 Tamanho Médio", format_file_size(avg_file_size))
    
    # Gráfico de downloads por período
    st.markdown("### 📊 Downloads por Período")
    downloads_data = get_downloads_by_period()
    
    if downloads_data:
        df_downloads = pd.DataFrame(downloads_data)
        st.line_chart(df_downloads.set_index('date')['count'])
    else:
        st.info("📊 Dados insuficientes para gerar gráfico")

def render_categories_management():
    """Renderiza o gerenciamento de categorias"""
    
    st.subheader("🏷️ Gerenciamento de Categorias")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Categorias Existentes")
        
        categories = get_categories()
        
        for category in categories:
            col_cat, col_count, col_action = st.columns([2, 1, 1])
            
            with col_cat:
                st.write(f"📁 {category}")
            
            with col_count:
                count = get_content_count_by_category(category)
                st.caption(f"{count} itens")
            
            with col_action:
                if st.button("🗑️", key=f"del_cat_{category}"):
                    # Aqui você implementaria a exclusão da categoria
                    st.warning("Funcionalidade em desenvolvimento")
    
    with col2:
        st.markdown("### Adicionar Nova Categoria")
        
        with st.form("new_category_form"):
            new_category = st.text_input("Nome da Categoria")
            category_description = st.text_area("Descrição")
            
            if st.form_submit_button("➕ Adicionar Categoria"):
                if new_category:
                    # Aqui você salvaria a nova categoria
                    st.success(f"Categoria '{new_category}' adicionada!")
                else:
                    st.error("Digite o nome da categoria!")

def render_content_reports():
    """Renderiza relatórios de conteúdo"""
    
    st.subheader("📊 Relatórios de Conteúdo")
    
    # Métricas gerais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_files = get_total_content_count()
        st.metric("📁 Total de Arquivos", total_files)
    
    with col2:
        total_size = get_total_content_size()
        st.metric("💾 Espaço Usado", format_file_size(total_size))
    
    with col3:
        total_categories = len(get_categories())
        st.metric("🏷️ Categorias", total_categories)
    
    with col4:
        recent_uploads = get_recent_uploads_count()
        st.metric("📤 Uploads Recentes", f"{recent_uploads} (7 dias)")
    
    st.divider()
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Conteúdo por Categoria")
        category_data = get_content_by_category_data()
        
        if category_data:
            df_categories = pd.DataFrame(category_data)
            st.bar_chart(df_categories.set_index('category')['count'])
        else:
            st.info("Nenhum dado disponível")
    
    with col2:
        st.markdown("### 📈 Uploads por Mês")
        monthly_data = get_monthly_uploads_data()
        
        if monthly_data:
            df_monthly = pd.DataFrame(monthly_data)
            st.line_chart(df_monthly.set_index('month')['count'])
        else:
            st.info("Nenhum dado disponível")

def get_file_icon(file_type):
    """Retorna ícone baseado no tipo de arquivo"""
    icons = {
        'image': '🖼️',
        'video': '🎥',
        'audio': '🎵',
        'document': '📄',
        'pdf': '📕',
        'default': '📄'
    }
    
    file_type_lower = file_type.lower()
    
    if any(ext in file_type_lower for ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']):
        return icons['image']
    elif any(ext in file_type_lower for ext in ['mp4', 'avi', 'mov', 'wmv']):
        return icons['video']
    elif any(ext in file_type_lower for ext in ['mp3', 'wav', 'flac', 'aac']):
        return icons['audio']
    elif 'pdf' in file_type_lower:
        return icons['pdf']
    elif any(ext in file_type_lower for ext in ['doc', 'docx', 'txt']):
        return icons['document']
    else:
        return icons['default']

def format_file_size(size_bytes):
    """Formata o tamanho do arquivo"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_categories():
    """Retorna lista de categorias"""
    # Categorias padrão - em uma implementação real, viria do banco de dados
    return ["Pregações", "Música", "Fotos de Eventos", "Documentos", "Vídeos", "Outros"]

def get_filtered_content(search_term, filter_category, filter_type, sort_by):
    """Busca conteúdo com filtros aplicados"""
    try:
        query = "SELECT * FROM media_content WHERE is_active = 1"
        params = []
        
        # Filtro por termo de busca
        if search_term:
            query += " AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)"
            search_param = f"%{search_term}%"
            params.extend([search_param, search_param, search_param])
        
        # Filtro por categoria
        if filter_category != "Todas":
            query += " AND category = ?"
            params.append(filter_category)
        
        # Filtro por tipo de arquivo
        if filter_type != "Todos":
            type_extensions = {
                "Imagem": ["jpg", "jpeg", "png", "gif", "bmp"],
                "Vídeo": ["mp4", "avi", "mov", "wmv"],
                "Áudio": ["mp3", "wav", "flac", "aac"],
                "Documento": ["pdf", "doc", "docx", "txt"]
            }
            
            if filter_type in type_extensions:
                extensions = type_extensions[filter_type]
                extension_conditions = " OR ".join(["file_type LIKE ?" for _ in extensions])
                query += f" AND ({extension_conditions})"
                params.extend([f"%{ext}%" for ext in extensions])
        
        # Ordenação
        if sort_by == "Mais Recente":
            query += " ORDER BY uploaded_at DESC"
        elif sort_by == "Mais Antigo":
            query += " ORDER BY uploaded_at ASC"
        elif sort_by == "Nome A-Z":
            query += " ORDER BY title ASC"
        elif sort_by == "Nome Z-A":
            query += " ORDER BY title DESC"
        elif sort_by == "Tamanho":
            query += " ORDER BY file_size DESC"
        
        return db_manager.fetch_all(query, params)
    except:
        return []

def upload_file(uploaded_file, title, description, category, tags):
    """Faz upload de um arquivo"""
    try:
        # Criar diretório se não existir
        upload_dir = CONFIG['UPLOAD_DIR']
        upload_dir.mkdir(exist_ok=True)
        
        # Gerar nome único para o arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = uploaded_file.name.split('.')[-1]
        unique_filename = f"{timestamp}_{uploaded_file.name}"
        file_path = upload_dir / unique_filename
        
        # Salvar arquivo
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Salvar informações no banco de dados
        user_info = get_current_user()
        user_id = get_user_id(user_info['username'])
        
        query = """
        INSERT INTO media_content (title, description, file_path, file_type, category, tags, uploaded_by, file_size)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            title,
            description,
            str(file_path),
            file_extension,
            category,
            tags,
            user_id,
            uploaded_file.size
        )
        
        db_manager.execute_query(query, params)
        return True
        
    except Exception as e:
        st.error(f"Erro ao fazer upload: {e}")
        return False

def view_content(item):
    """Visualiza um conteúdo"""
    st.info("Funcionalidade de visualização em desenvolvimento")

def download_content(item):
    """Faz download de um conteúdo"""
    try:
        file_path = Path(item['file_path'])
        
        if file_path.exists():
            # Ler o arquivo
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            # Determinar o tipo MIME
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Criar botão de download
            st.download_button(
                label=f"⬇️ Baixar {item['title']}",
                data=file_data,
                file_name=file_path.name,
                mime=mime_type,
                key=f"download_btn_{item['id']}",
                use_container_width=True
            )
            
            # Registrar o download no log (se for admin)
            if is_admin():
                log_download_activity(item['id'], item['title'])
                
        else:
            st.error("❌ Arquivo não encontrado no servidor!")
            
    except Exception as e:
        st.error(f"❌ Erro ao preparar download: {str(e)}")

def delete_content(content_id):
    """Exclui um conteúdo"""
    try:
        query = "UPDATE media_content SET is_active = 0 WHERE id = ?"
        db_manager.execute_query(query, (content_id,))
        return True
    except:
        return False

def get_user_id(username):
    """Busca o ID do usuário pelo username"""
    try:
        query = "SELECT id FROM users WHERE username = ?"
        result = db_manager.fetch_all(query, (username,))
        return result[0]['id'] if result else None
    except:
        return None

def get_total_content_count():
    """Retorna o total de conteúdos"""
    try:
        result = db_manager.fetch_all("SELECT COUNT(*) as count FROM media_content WHERE is_active = 1")
        return result[0]['count'] if result else 0
    except:
        return 0

def get_total_content_size():
    """Retorna o tamanho total dos conteúdos"""
    try:
        result = db_manager.fetch_all("SELECT SUM(file_size) as total_size FROM media_content WHERE is_active = 1")
        return result[0]['total_size'] or 0 if result else 0
    except:
        return 0

def get_recent_uploads_count():
    """Retorna o número de uploads recentes"""
    try:
        query = "SELECT COUNT(*) as count FROM media_content WHERE uploaded_at > datetime('now', '-7 days') AND is_active = 1"
        result = db_manager.fetch_all(query)
        return result[0]['count'] if result else 0
    except:
        return 0

def get_content_count_by_category(category):
    """Retorna o número de conteúdos por categoria"""
    try:
        query = "SELECT COUNT(*) as count FROM media_content WHERE category = ? AND is_active = 1"
        result = db_manager.fetch_all(query, (category,))
        return result[0]['count'] if result else 0
    except:
        return 0

def get_content_by_category_data():
    """Retorna dados de conteúdo por categoria para gráfico"""
    try:
        query = "SELECT category, COUNT(*) as count FROM media_content WHERE is_active = 1 GROUP BY category"
        result = db_manager.fetch_all(query)
        return [{'category': row['category'], 'count': row['count']} for row in result] if result else []
    except:
        return []

def get_monthly_uploads_data():
    """Retorna dados de uploads mensais para gráfico"""
    try:
        query = """
        SELECT strftime('%Y-%m', uploaded_at) as month, COUNT(*) as count
        FROM media_content
        WHERE is_active = 1
        GROUP BY strftime('%Y-%m', uploaded_at)
        ORDER BY month
        """
        result = db_manager.fetch_all(query)
        return [{'month': row['month'], 'count': row['count']} for row in result] if result else []
    except:
        return []

# ===== FUNÇÕES PARA SISTEMA DE DOWNLOADS =====

def get_filtered_content_for_download(category, file_type, date_range):
    """Busca conteúdo filtrado para download em lote"""
    try:
        query = "SELECT * FROM media_content WHERE is_active = 1"
        params = []
        
        # Filtro por categoria
        if category != "Todas":
            query += " AND category = ?"
            params.append(category)
        
        # Filtro por tipo de arquivo
        if file_type != "Todos":
            type_extensions = {
                "Imagem": ["jpg", "jpeg", "png", "gif", "bmp"],
                "Vídeo": ["mp4", "avi", "mov", "wmv"],
                "Áudio": ["mp3", "wav", "flac", "aac"],
                "Documento": ["pdf", "doc", "docx", "txt"]
            }
            
            if file_type in type_extensions:
                extensions = type_extensions[file_type]
                extension_conditions = " OR ".join(["file_type LIKE ?" for _ in extensions])
                query += f" AND ({extension_conditions})"
                params.extend([f"%{ext}%" for ext in extensions])
        
        # Filtro por data
        if date_range and len(date_range) == 2:
            query += " AND DATE(uploaded_at) BETWEEN ? AND ?"
            params.extend([str(date_range[0]), str(date_range[1])])
        
        query += " ORDER BY uploaded_at DESC"
        
        return db_manager.fetch_all(query, params)
    except:
        return []

def download_zip_package(files, include_metadata=True):
    """Cria e oferece download de um pacote ZIP com múltiplos arquivos"""
    try:
        # Criar buffer para o ZIP
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Adicionar arquivos ao ZIP
            for file_info in files:
                file_path = Path(file_info['file_path'])
                
                if file_path.exists():
                    # Criar nome único para evitar conflitos
                    safe_filename = f"{file_info['id']}_{file_path.name}"
                    zip_file.write(file_path, safe_filename)
            
            # Adicionar arquivo de metadados se solicitado
            if include_metadata:
                metadata_csv = create_metadata_csv(files)
                zip_file.writestr("metadata.csv", metadata_csv)
        
        zip_buffer.seek(0)
        
        # Criar nome do arquivo ZIP
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"midia_church_backup_{timestamp}.zip"
        
        # Oferecer download
        st.download_button(
            label="📦 Baixar Pacote ZIP",
            data=zip_buffer.getvalue(),
            file_name=zip_filename,
            mime="application/zip",
            use_container_width=True
        )
        
        st.success(f"✅ Pacote ZIP criado com {len(files)} arquivo(s)!")
        
        # Registrar atividade
        log_bulk_download_activity(len(files))
        
    except Exception as e:
        st.error(f"❌ Erro ao criar pacote ZIP: {str(e)}")

def create_metadata_csv(files):
    """Cria arquivo CSV com metadados dos arquivos"""
    try:
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow([
            'ID', 'Título', 'Descrição', 'Categoria', 'Tipo de Arquivo',
            'Tamanho (bytes)', 'Tags', 'Data de Upload', 'Enviado por'
        ])
        
        # Dados dos arquivos
        for file_info in files:
            writer.writerow([
                file_info.get('id', ''),
                file_info.get('title', ''),
                file_info.get('description', ''),
                file_info.get('category', ''),
                file_info.get('file_type', ''),
                file_info.get('file_size', 0),
                file_info.get('tags', ''),
                file_info.get('uploaded_at', ''),
                get_username_by_id(file_info.get('uploaded_by', ''))
            ])
        
        return output.getvalue()
    except:
        return "Erro ao gerar metadados"

def log_download_activity(content_id, content_title):
    """Registra atividade de download individual"""
    try:
        user_info = get_current_user()
        user_id = get_user_id(user_info['username']) if user_info else None
        
        # Criar tabela de logs de download se não existir
        create_download_logs_table()
        
        query = """
        INSERT INTO download_logs (content_id, content_title, downloaded_by, download_type)
        VALUES (?, ?, ?, ?)
        """
        db_manager.execute_query(query, (content_id, content_title, user_id, 'individual'))
        
    except Exception as e:
        print(f"Erro ao registrar download: {e}")

def log_bulk_download_activity(file_count):
    """Registra atividade de download em lote"""
    try:
        user_info = get_current_user()
        user_id = get_user_id(user_info['username']) if user_info else None
        
        # Criar tabela de logs de download se não existir
        create_download_logs_table()
        
        query = """
        INSERT INTO download_logs (content_title, downloaded_by, download_type, file_count)
        VALUES (?, ?, ?, ?)
        """
        db_manager.execute_query(query, (f"Pacote com {file_count} arquivos", user_id, 'bulk', file_count))
        
    except Exception as e:
        print(f"Erro ao registrar download em lote: {e}")

def create_download_logs_table():
    """Cria tabela de logs de download se não existir"""
    try:
        query = """
        CREATE TABLE IF NOT EXISTS download_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER,
            content_title TEXT,
            downloaded_by INTEGER,
            download_type TEXT DEFAULT 'individual',
            file_count INTEGER DEFAULT 1,
            downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (content_id) REFERENCES media_content (id),
            FOREIGN KEY (downloaded_by) REFERENCES users (id)
        )
        """
        db_manager.execute_query(query)
    except:
        pass

def get_total_downloads_count():
    """Retorna o total de downloads realizados"""
    try:
        create_download_logs_table()
        result = db_manager.fetch_all("SELECT SUM(file_count) as total FROM download_logs")
        return result[0]['total'] or 0 if result else 0
    except:
        return 0

def get_downloads_today_count():
    """Retorna o número de downloads de hoje"""
    try:
        create_download_logs_table()
        query = "SELECT SUM(file_count) as count FROM download_logs WHERE DATE(downloaded_at) = DATE('now')"
        result = db_manager.fetch_all(query)
        return result[0]['count'] or 0 if result else 0
    except:
        return 0

def get_most_downloaded_file():
    """Retorna o arquivo mais baixado"""
    try:
        create_download_logs_table()
        query = """
        SELECT content_title, COUNT(*) as download_count
        FROM download_logs
        WHERE download_type = 'individual'
        GROUP BY content_title
        ORDER BY download_count DESC
        LIMIT 1
        """
        result = db_manager.fetch_all(query)
        return result[0]['content_title'] if result else None
    except:
        return None

def get_average_file_size():
    """Retorna o tamanho médio dos arquivos"""
    try:
        result = db_manager.fetch_all("SELECT AVG(file_size) as avg_size FROM media_content WHERE is_active = 1")
        return result[0]['avg_size'] or 0 if result else 0
    except:
        return 0

def get_downloads_by_period():
    """Retorna dados de downloads por período"""
    try:
        create_download_logs_table()
        query = """
        SELECT DATE(downloaded_at) as date, SUM(file_count) as count
        FROM download_logs
        WHERE downloaded_at > datetime('now', '-30 days')
        GROUP BY DATE(downloaded_at)
        ORDER BY date
        """
        result = db_manager.fetch_all(query)
        return [{'date': row['date'], 'count': row['count']} for row in result] if result else []
    except:
        return []

def get_username_by_id(user_id):
    """Retorna o nome de usuário pelo ID"""
    try:
        if not user_id:
            return "Desconhecido"
        query = "SELECT username FROM users WHERE id = ?"
        result = db_manager.fetch_all(query, (user_id,))
        return result[0]['username'] if result else "Desconhecido"
    except:
        return "Desconhecido"

# ===== FUNÇÕES DE VALIDAÇÃO E UPLOAD APRIMORADO =====

def validate_uploaded_file(uploaded_file, is_admin_user=False):
    """Valida arquivo enviado com verificações de segurança"""
    try:
        # Verificar tamanho do arquivo
        max_size_mb = 100 if is_admin_user else 50  # Admins podem enviar arquivos maiores
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if uploaded_file.size > max_size_bytes:
            return False, f"Arquivo muito grande! Máximo permitido: {max_size_mb}MB"
        
        # Verificar extensão do arquivo
        file_extension = uploaded_file.name.split('.')[-1].lower()
        allowed_extensions = get_allowed_extensions(is_admin_user)
        
        if file_extension not in allowed_extensions:
            return False, f"Tipo de arquivo não permitido! Extensões aceitas: {', '.join(allowed_extensions)}"
        
        # Verificar nome do arquivo
        if len(uploaded_file.name) > 255:
            return False, "Nome do arquivo muito longo! Máximo: 255 caracteres"
        
        # Verificar caracteres especiais no nome
        import re
        if not re.match(r'^[a-zA-Z0-9._\-\s()]+$', uploaded_file.name):
            return False, "Nome do arquivo contém caracteres não permitidos!"
        
        # Verificações adicionais para tipos específicos
        if file_extension in ['exe', 'bat', 'cmd', 'scr', 'com']:
            return False, "Arquivos executáveis não são permitidos por segurança!"
        
        # Verificar tipo MIME
        if uploaded_file.type:
            dangerous_mimes = [
                'application/x-executable',
                'application/x-msdownload',
                'application/x-msdos-program'
            ]
            
            if uploaded_file.type in dangerous_mimes:
                return False, "Tipo de arquivo perigoso detectado!"
        
        return True, "Arquivo válido"
        
    except Exception as e:
        return False, f"Erro na validação: {str(e)}"

def get_allowed_extensions(is_admin_user=False):
    """Retorna extensões permitidas baseado no tipo de usuário"""
    base_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'mp4', 'avi', 'mov', 'mp3', 'wav', 'pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx', 'xls', 'xlsx']
    
    if is_admin_user:
        # Admins podem enviar mais tipos de arquivo
        admin_extensions = ['zip', 'rar', '7z', 'tar', 'gz', 'svg', 'eps', 'ai', 'psd', 'flv', 'wmv', 'mkv', 'flac', 'aac', 'ogg']
        return base_extensions + admin_extensions
    
    return base_extensions

def upload_file_enhanced(uploaded_file, title, description, category, tags, priority="Normal", visibility="Público", auto_backup=True):
    """Versão aprimorada da função de upload com recursos avançados"""
    try:
        # Criar diretório se não existir
        upload_dir = CONFIG.get('UPLOAD_DIR', Path('uploads'))
        if isinstance(upload_dir, str):
            upload_dir = Path(upload_dir)
        upload_dir.mkdir(exist_ok=True)
        
        # Gerar nome único para o arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        # Sanitizar nome do arquivo
        safe_title = sanitize_filename(title)
        unique_filename = f"{timestamp}_{safe_title}.{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Salvar arquivo
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Calcular hash do arquivo para verificação de integridade
        file_hash = calculate_file_hash(file_path)
        
        # Salvar informações no banco de dados
        user_info = get_current_user()
        user_id = get_user_id(user_info['username']) if user_info else None
        
        # Atualizar esquema da tabela se necessário
        update_media_content_schema()
        
        query = """
        INSERT INTO media_content (
            title, description, file_path, file_type, category, tags, 
            uploaded_by, file_size, priority, visibility, auto_backup, file_hash
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            title,
            description,
            str(file_path),
            file_extension,
            category,
            tags,
            user_id,
            uploaded_file.size,
            priority,
            visibility,
            auto_backup,
            file_hash
        )
        
        db_manager.execute_query(query, params)
        
        # Log da atividade
        log_upload_activity(title, uploaded_file.size, user_id)
        
        return True
        
    except Exception as e:
        st.error(f"Erro detalhado no upload: {e}")
        return False

def sanitize_filename(filename):
    """Sanitiza nome do arquivo removendo caracteres perigosos"""
    import re
    # Remover caracteres especiais e manter apenas alfanuméricos, espaços, pontos e hífens
    sanitized = re.sub(r'[^\w\s.-]', '', filename)
    # Remover espaços extras e substituir por underscore
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    return sanitized[:50]  # Limitar tamanho

def calculate_file_hash(file_path):
    """Calcula hash SHA-256 do arquivo para verificação de integridade"""
    try:
        import hashlib
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    except:
        return None

def update_media_content_schema():
    """Atualiza esquema da tabela media_content com novos campos"""
    try:
        # Verificar se as colunas já existem
        result = db_manager.fetch_all("PRAGMA table_info(media_content)")
        existing_columns = [row['name'] for row in result] if result else []
        
        # Adicionar colunas se não existirem
        new_columns = [
            ("priority", "TEXT DEFAULT 'Normal'"),
            ("visibility", "TEXT DEFAULT 'Público'"),
            ("auto_backup", "BOOLEAN DEFAULT 1"),
            ("file_hash", "TEXT"),
            ("download_count", "INTEGER DEFAULT 0")
        ]
        
        for column_name, column_def in new_columns:
            if column_name not in existing_columns:
                query = f"ALTER TABLE media_content ADD COLUMN {column_name} {column_def}"
                db_manager.execute_query(query)
                
    except Exception as e:
        print(f"Erro ao atualizar esquema: {e}")

def log_upload_activity(title, file_size, user_id):
    """Registra atividade de upload"""
    try:
        # Criar tabela de logs de upload se não existir
        create_upload_logs_table()
        
        query = """
        INSERT INTO upload_logs (file_title, file_size, uploaded_by)
        VALUES (?, ?, ?)
        """
        db_manager.execute_query(query, (title, file_size, user_id))
        
    except Exception as e:
        print(f"Erro ao registrar upload: {e}")

def create_upload_logs_table():
    """Cria tabela de logs de upload se não existir"""
    try:
        query = """
        CREATE TABLE IF NOT EXISTS upload_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_title TEXT,
            file_size INTEGER,
            uploaded_by INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uploaded_by) REFERENCES users (id)
        )
        """
        db_manager.execute_query(query)
    except:
        pass