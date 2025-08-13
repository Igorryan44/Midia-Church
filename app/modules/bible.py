"""
Módulo da Bíblia - Sistema completo de leitura e estudo bíblico
"""
import streamlit as st
import json
from typing import Dict, List, Optional
from app.data.bible_loader import bible_loader
from app.data.bible_structure import BIBLE_VERSIONS, BIBLE_BOOKS_INFO, get_book_by_name, get_testament_books
from app.database.local_connection import db_manager

def render_bible_module():
    """Renderiza o módulo principal da Bíblia"""
    try:
        st.title("📖 Bíblia Sagrada")
        
        # Verificar se os dados estão carregados
        if not check_bible_data():
            show_bible_setup()
            return
        
        # Tabs principais
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📖 Leitura", 
            "🔍 Busca", 
            "📝 Anotações", 
            "⭐ Favoritos", 
            "📅 Planos de Leitura"
        ])
        
        with tab1:
            try:
                render_bible_reading()
            except Exception as e:
                st.error(f"Erro na aba de Leitura: {str(e)}")
                st.exception(e)
        
        with tab2:
            try:
                render_bible_search()
            except Exception as e:
                st.error(f"Erro na aba de Busca: {str(e)}")
                st.exception(e)
        
        with tab3:
            try:
                render_bible_notes()
            except Exception as e:
                st.error(f"Erro na aba de Anotações: {str(e)}")
                st.exception(e)
        
        with tab4:
            try:
                render_bible_favorites()
            except Exception as e:
                st.error(f"Erro na aba de Favoritos: {str(e)}")
                st.exception(e)
        
        with tab5:
            try:
                render_reading_plans()
            except Exception as e:
                st.error(f"Erro na aba de Planos de Leitura: {str(e)}")
                st.exception(e)
                
    except Exception as e:
        st.error(f"Erro geral no módulo da Bíblia: {str(e)}")
        st.exception(e)
        st.info("Por favor, reporte este erro ao administrador do sistema.")

def check_bible_data() -> bool:
    """Verifica se os dados da Bíblia estão disponíveis"""
    try:
        # Verificar se pelo menos uma versão está carregada
        for version in ['nvi', 'acf', 'aa']:
            if bible_loader.load_bible_version(version):
                return True
        return False
    except:
        return False

def show_bible_setup():
    """Mostra interface de configuração inicial da Bíblia"""
    st.warning("⚠️ Os dados da Bíblia precisam ser carregados no banco de dados.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("""
        **Configuração Inicial da Bíblia**
        
        Para usar o módulo da Bíblia, é necessário carregar os dados no banco de dados.
        Este processo será executado apenas uma vez.
        """)
    
    with col2:
        version = st.selectbox(
            "Versão da Bíblia:",
            options=list(BIBLE_VERSIONS.keys()),
            format_func=lambda x: BIBLE_VERSIONS[x]
        )
        
        if st.button("🔄 Carregar Bíblia", type="primary"):
            with st.spinner("Carregando dados da Bíblia..."):
                success = bible_loader.save_to_database(version)
                if success:
                    st.success("✅ Bíblia carregada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao carregar a Bíblia.")

def render_bible_reading():
    """Renderiza a interface de leitura da Bíblia"""
    st.header("📖 Leitura da Bíblia")
    
    # Seleção de versão
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        version = st.selectbox(
            "Versão:",
            options=list(BIBLE_VERSIONS.keys()),
            format_func=lambda x: BIBLE_VERSIONS[x],
            key="reading_version"
        )
    
    with col2:
        # Carregar lista de livros
        books = bible_loader.get_books(version)
        if not books:
            st.error("Erro ao carregar livros da Bíblia")
            return
        
        book_options = [f"{book['name']}" for book in books]
        selected_book_name = st.selectbox("Livro:", book_options, key="reading_book")
        
        # Encontrar o livro selecionado
        selected_book = next((book for book in books if book['name'] == selected_book_name), None)
    
    with col3:
        if selected_book:
            chapter = st.number_input(
                "Capítulo:", 
                min_value=1, 
                max_value=selected_book['chapters'], 
                value=1,
                key="reading_chapter"
            )
    
    with col4:
        # Botão de capítulo aleatório
        if st.button("🎲 Aleatório"):
            random_verse = bible_loader.get_random_verse(version)
            if random_verse:
                st.session_state.reading_book = random_verse['book']
                st.session_state.reading_chapter = random_verse['chapter']
                st.rerun()
    
    # Exibir capítulo
    if selected_book:
        verses = bible_loader.get_chapter(selected_book['name'], chapter, version)
        if verses:
            st.markdown("---")
            
            # Cabeçalho do capítulo
            st.markdown(f"### {selected_book['name']} {chapter}")
            
            # Exibir versículos
            for i, verse_text in enumerate(verses, 1):
                verse_col, actions_col = st.columns([10, 1])
                
                with verse_col:
                    st.markdown(f"**{i}.** {verse_text}")
                
                with actions_col:
                    # Botões de ação para cada versículo
                    if st.button("⭐", key=f"fav_{selected_book['name']}_{chapter}_{i}", help="Adicionar aos favoritos"):
                        add_to_favorites(selected_book['name'], chapter, i, verse_text, version)
                        st.success("Adicionado aos favoritos!")
            
            # Navegação entre capítulos
            st.markdown("---")
            nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
            
            with nav_col1:
                if chapter > 1:
                    if st.button("⬅️ Capítulo Anterior"):
                        st.session_state.reading_chapter = chapter - 1
                        st.rerun()
            
            with nav_col3:
                if chapter < selected_book['chapters']:
                    if st.button("Próximo Capítulo ➡️"):
                        st.session_state.reading_chapter = chapter + 1
                        st.rerun()

def render_bible_search():
    """Renderiza a interface de busca na Bíblia"""
    st.header("🔍 Busca na Bíblia")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Digite sua busca:",
            placeholder="Ex: amor, fé, esperança...",
            key="bible_search"
        )
    
    with col2:
        version = st.selectbox(
            "Versão:",
            options=list(BIBLE_VERSIONS.keys()),
            format_func=lambda x: BIBLE_VERSIONS[x],
            key="search_version"
        )
    
    if search_query:
        with st.spinner("Buscando..."):
            results = bible_loader.search_verses(search_query, version, limit=100)
        
        if results:
            st.success(f"Encontrados {len(results)} versículos")
            
            # Filtros
            with st.expander("🔧 Filtros"):
                testaments = list(set([
                    'Antigo' if any(book['name'] == result['book'] for book in bible_loader.get_books(version)[:39]) else 'Novo'
                    for result in results
                ]))
                
                selected_testament = st.selectbox(
                    "Testamento:",
                    options=['Todos'] + testaments,
                    key="search_testament"
                )
            
            # Exibir resultados
            for result in results:
                # Aplicar filtro de testamento
                book_info = next((book for book in bible_loader.get_books(version) if book['name'] == result['book']), None)
                if book_info:
                    testament = book_info['testament']
                    if selected_testament != 'Todos' and testament != selected_testament:
                        continue
                
                with st.container():
                    col1, col2 = st.columns([10, 1])
                    
                    with col1:
                        st.markdown(f"**{result['reference']}**")
                        # Destacar termo buscado
                        highlighted_text = result['text'].replace(
                            search_query, 
                            f"**{search_query}**"
                        )
                        st.markdown(highlighted_text)
                    
                    with col2:
                        if st.button("⭐", key=f"search_fav_{result['reference']}", help="Adicionar aos favoritos"):
                            add_to_favorites(result['book'], result['chapter'], result['verse'], result['text'], version)
                            st.success("Adicionado!")
                    
                    st.markdown("---")
        else:
            st.info("Nenhum versículo encontrado para esta busca.")

def render_bible_notes():
    """Renderiza a interface de anotações bíblicas"""
    st.header("📝 Anotações Bíblicas")
    
    # Criar tabela de anotações se não existir
    db_manager.execute_query("""
        CREATE TABLE IF NOT EXISTS bible_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_name TEXT NOT NULL,
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            note TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version TEXT DEFAULT 'nvi'
        )
    """)
    
    tab1, tab2 = st.tabs(["➕ Nova Anotação", "📋 Minhas Anotações"])
    
    with tab1:
        # Formulário para nova anotação
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            version = st.selectbox(
                "Versão:",
                options=list(BIBLE_VERSIONS.keys()),
                format_func=lambda x: BIBLE_VERSIONS[x],
                key="note_version"
            )
        
        with col2:
            books = bible_loader.get_books(version)
            book_options = [book['name'] for book in books]
            selected_book = st.selectbox("Livro:", book_options, key="note_book")
        
        with col3:
            book_info = next((book for book in books if book['name'] == selected_book), None)
            if book_info:
                chapter = st.number_input("Cap:", min_value=1, max_value=book_info['chapters'], value=1, key="note_chapter")
        
        with col4:
            verse = st.number_input("Vers:", min_value=1, value=1, key="note_verse")
        
        # Exibir versículo selecionado
        if selected_book and chapter and verse:
            verse_text = bible_loader.get_verse(selected_book, chapter, verse, version)
            if verse_text:
                st.info(f"**{selected_book} {chapter}:{verse}** - {verse_text}")
            else:
                st.warning("Versículo não encontrado")
        
        # Campo de anotação
        note_text = st.text_area("Sua anotação:", height=100, key="note_text")
        
        if st.button("💾 Salvar Anotação", type="primary"):
            if note_text.strip():
                db_manager.execute_query("""
                    INSERT INTO bible_notes (book_name, chapter, verse, note, version)
                    VALUES (?, ?, ?, ?, ?)
                """, (selected_book, chapter, verse, note_text.strip(), version))
                st.success("Anotação salva com sucesso!")
                st.rerun()
            else:
                st.warning("Digite uma anotação antes de salvar.")
    
    with tab2:
        # Listar anotações existentes
        notes = db_manager.fetch_all("""
            SELECT * FROM bible_notes 
            ORDER BY created_at DESC
        """)
        
        if notes:
            for note in notes:
                with st.expander(f"📝 {note['book_name']} {note['chapter']}:{note['verse']} - {note['created_at'][:10]}"):
                    # Exibir versículo
                    verse_text = bible_loader.get_verse(note['book_name'], note['chapter'], note['verse'], note['version'])
                    if verse_text:
                        st.markdown(f"**Versículo:** {verse_text}")
                    
                    st.markdown(f"**Anotação:** {note['note']}")
                    
                    if st.button("🗑️ Excluir", key=f"delete_note_{note['id']}"):
                        db_manager.execute_query("DELETE FROM bible_notes WHERE id = ?", (note['id'],))
                        st.success("Anotação excluída!")
                        st.rerun()
        else:
            st.info("Você ainda não tem anotações. Crie sua primeira anotação na aba anterior.")

def render_bible_favorites():
    """Renderiza a interface de versículos favoritos"""
    st.header("⭐ Versículos Favoritos")
    
    # Criar tabela de favoritos se não existir
    db_manager.execute_query("""
        CREATE TABLE IF NOT EXISTS bible_favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_name TEXT NOT NULL,
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version TEXT DEFAULT 'nvi'
        )
    """)
    
    # Listar favoritos
    favorites = db_manager.fetch_all("""
        SELECT * FROM bible_favorites 
        ORDER BY created_at DESC
    """)
    
    if favorites:
        for favorite in favorites:
            with st.container():
                col1, col2 = st.columns([10, 1])
                
                with col1:
                    st.markdown(f"**{favorite['book_name']} {favorite['chapter']}:{favorite['verse']}**")
                    st.markdown(favorite['text'])
                    st.caption(f"Adicionado em: {favorite['created_at'][:10]}")
                
                with col2:
                    if st.button("🗑️", key=f"remove_fav_{favorite['id']}", help="Remover dos favoritos"):
                        db_manager.execute_query("DELETE FROM bible_favorites WHERE id = ?", (favorite['id'],))
                        st.success("Removido dos favoritos!")
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("Você ainda não tem versículos favoritos. Adicione alguns durante a leitura ou busca!")

def render_reading_plans():
    """Renderiza a interface de planos de leitura"""
    st.header("📅 Planos de Leitura")
    
    # Criar tabela de planos se não existir
    db_manager.execute_query("""
        CREATE TABLE IF NOT EXISTS reading_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    
    db_manager.execute_query("""
        CREATE TABLE IF NOT EXISTS reading_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER,
            book_name TEXT NOT NULL,
            chapter INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES reading_plans (id)
        )
    """)
    
    tab1, tab2 = st.tabs(["📋 Planos Disponíveis", "📊 Meu Progresso"])
    
    with tab1:
        # Planos pré-definidos
        predefined_plans = [
            {
                "name": "Bíblia em 1 Ano",
                "description": "Leia toda a Bíblia em 365 dias",
                "books": list(BIBLE_BOOKS_INFO.keys())
            },
            {
                "name": "Novo Testamento em 3 Meses",
                "description": "Leia todo o Novo Testamento em 90 dias",
                "books": [k for k, v in BIBLE_BOOKS_INFO.items() if v['testament'] == 'Novo']
            },
            {
                "name": "Salmos e Provérbios",
                "description": "Leia Salmos e Provérbios para sabedoria diária",
                "books": ['psalms', 'proverbs']
            }
        ]
        
        for plan in predefined_plans:
            with st.expander(f"📖 {plan['name']}"):
                st.write(plan['description'])
                st.write(f"**Livros incluídos:** {len(plan['books'])}")
                
                if st.button(f"🚀 Iniciar {plan['name']}", key=f"start_plan_{plan['name']}"):
                    # Criar plano no banco
                    plan_id = db_manager.execute_query("""
                        INSERT INTO reading_plans (name, description)
                        VALUES (?, ?)
                    """, (plan['name'], plan['description']))
                    
                    st.success(f"Plano '{plan['name']}' iniciado!")
    
    with tab2:
        # Mostrar progresso dos planos ativos
        active_plans = db_manager.fetch_all("""
            SELECT * FROM reading_plans 
            WHERE is_active = 1 
            ORDER BY created_at DESC
        """)
        
        if active_plans:
            for plan in active_plans:
                with st.expander(f"📊 {plan['name']}"):
                    # Calcular progresso
                    progress = db_manager.fetch_all("""
                        SELECT COUNT(*) as completed_chapters
                        FROM reading_progress 
                        WHERE plan_id = ?
                    """, (plan['id'],))
                    
                    completed = progress[0]['completed_chapters'] if progress else 0
                    
                    st.metric("Capítulos Lidos", completed)
                    st.progress(min(completed / 100, 1.0))  # Progresso básico
                    
                    if st.button(f"📖 Continuar Leitura", key=f"continue_plan_{plan['id']}"):
                        st.info("Funcionalidade de leitura guiada em desenvolvimento!")
        else:
            st.info("Você não tem planos de leitura ativos. Inicie um plano na aba anterior!")

def add_to_favorites(book_name: str, chapter: int, verse: int, text: str, version: str = 'nvi'):
    """Adiciona um versículo aos favoritos"""
    try:
        db_manager.execute_query("""
            INSERT OR REPLACE INTO bible_favorites (book_name, chapter, verse, text, version)
            VALUES (?, ?, ?, ?, ?)
        """, (book_name, chapter, verse, text, version))
        return True
    except:
        return False

def get_verse_of_the_day(version: str = 'nvi') -> Optional[Dict]:
    """Retorna o versículo do dia"""
    return bible_loader.get_random_verse(version)

def get_bible_stats(version: str = 'nvi') -> Dict:
    """Retorna estatísticas da Bíblia"""
    books = bible_loader.get_books(version)
    if not books:
        return {}
    
    total_books = len(books)
    total_chapters = sum(book['chapters'] for book in books)
    old_testament = len([book for book in books if book['testament'] == 'Antigo'])
    new_testament = len([book for book in books if book['testament'] == 'Novo'])
    
    return {
        'total_books': total_books,
        'total_chapters': total_chapters,
        'old_testament_books': old_testament,
        'new_testament_books': new_testament
    }