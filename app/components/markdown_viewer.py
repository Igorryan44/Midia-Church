import streamlit as st
import re
from datetime import datetime

def render_form_compatible_markdown_editor(content, key="markdown_editor"):
    """Renderiza um editor de Markdown compatível com formulários (sem botões)"""
    
    # CSS para o editor
    st.markdown("""
    <style>
    .form-editor-container {
        border: 1px solid #dee2e6;
        border-radius: 5px;
        background-color: #ffffff;
    }
    
    .format-help {
        background-color: #e7f3ff;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-size: 0.875rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### ✏️ Editor de Conteúdo")
        
        # Editor de texto principal (sem botões)
        st.markdown('<div class="form-editor-container">', unsafe_allow_html=True)
        edited_content = st.text_area(
            "Conteúdo (Markdown)",
            value=content,
            height=500,
            key=key,
            help="Use formatação Markdown para estruturar seu texto"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Ajuda de formatação (sem botões interativos)
        with st.expander("📚 Guia de Formatação Markdown"):
            st.markdown("""
            <div class="format-help">
            <strong>Formatação Básica:</strong><br>
            • <code>**negrito**</code> → <strong>negrito</strong><br>
            • <code>*itálico*</code> → <em>itálico</em><br>
            • <code># Título</code> → Título principal<br>
            • <code>## Subtítulo</code> → Subtítulo<br>
            • <code>- item</code> → Lista com marcadores<br>
            • <code>1. item</code> → Lista numerada<br>
            • <code>- [ ] tarefa</code> → Lista de tarefas<br>
            • <code>[link](url)</code> → Link<br>
            • <code>`código`</code> → Código inline<br>
            • <code>> citação</code> → Citação<br>
            • <code>| Col1 | Col2 |</code> → Tabela<br>
            • <code>```código```</code> → Bloco de código<br>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 👁️ Preview em Tempo Real")
        if edited_content:
            render_markdown_preview(edited_content, "Preview Atualizado")
            
            # Estatísticas do documento
            stats = get_document_stats(edited_content)
            st.markdown(f"""
            **📊 Estatísticas:**
            - Palavras: {stats['words']}
            - Caracteres: {stats['characters']}
            - Linhas: {stats['lines']}
            - Títulos: {stats['headers']}
            - Listas: {stats['lists']}
            """)
        else:
            st.info("👆 Digite no editor para ver o preview")
    
    return edited_content

def render_markdown_report(report_data):
    """Renderiza um relatório em formato Markdown com estilo personalizado e melhorado"""
    
    # Indicador de carregamento
    with st.spinner('🎨 Renderizando relatório com design aprimorado...'):
        
        # CSS personalizado aprimorado para melhor aparência e responsividade
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Animações e transições */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .report-container {
            background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
            padding: 0;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin: 1.5rem 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
            overflow: hidden;
            font-family: 'Inter', sans-serif;
            animation: fadeInUp 0.6s ease-out;
            transition: all 0.3s ease;
        }
        
        .report-container:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }
        
        .report-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            position: relative;
            overflow: hidden;
        }
        
        .report-header h1 {
            margin: 0;
            color: white;
            font-size: 2.2rem;
            font-weight: 700;
            line-height: 1.2;
            position: relative;
            z-index: 1;
        }
        
        .report-header-meta {
            margin: 1rem 0 0 0;
            opacity: 0.95;
            position: relative;
            z-index: 1;
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: center;
        }
        
        .report-content-wrapper {
            padding: 2rem;
        }
        
        .report-meta {
            background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1.5rem 0;
            border-left: 4px solid #2196f3;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            animation: slideInLeft 0.5s ease-out 0.2s both;
            transition: all 0.3s ease;
        }
        
        .report-meta h4 {
            margin: 0 0 0.75rem 0;
            color: #1565c0;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .action-item {
            background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
            padding: 1rem;
            margin: 0.75rem 0;
            border-radius: 10px;
            border-left: 4px solid #ff9800;
            box-shadow: 0 2px 8px rgba(255, 152, 0, 0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .action-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(255, 152, 0, 0.2);
        }
        
        .decision-item {
            background: linear-gradient(135deg, #e0f2f1 0%, #b2dfdb 100%);
            padding: 1.5rem;
            margin: 1rem 0;
            border-radius: 12px;
            border-left: 4px solid #009688;
            box-shadow: 0 2px 8px rgba(0, 150, 136, 0.1);
            animation: slideInLeft 0.5s ease-out 0.4s both;
            transition: all 0.3s ease;
        }
        
        .decision-item h4 {
            margin: 0 0 1rem 0;
            color: #00695c;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .report-content {
            line-height: 1.7;
            color: #2c3e50;
        }
        
        .report-content h1 {
            color: #1a237e;
            border-bottom: 3px solid #3f51b5;
            padding-bottom: 0.75rem;
            margin-top: 2rem;
            margin-bottom: 1.5rem;
            font-weight: 600;
        }
        
        .report-content h2 {
            color: #283593;
            margin-top: 2.5rem;
            margin-bottom: 1.25rem;
            font-weight: 600;
            position: relative;
            padding-left: 1rem;
        }
        
        .report-content h2::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0.25rem;
            width: 4px;
            height: 1.5rem;
            background: linear-gradient(135deg, #3f51b5, #9c27b0);
            border-radius: 2px;
        }
        
        .participants-list {
            background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 4px solid #4caf50;
            box-shadow: 0 2px 8px rgba(76, 175, 80, 0.1);
            margin: 1.5rem 0;
            animation: slideInLeft 0.5s ease-out 0.3s both;
            transition: all 0.3s ease;
        }
        
        .participants-list h4 {
            margin: 0 0 1rem 0;
            color: #2e7d32;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.5rem 1rem;
            border-radius: 25px;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .status-draft {
            background: linear-gradient(135deg, #fff3e0 0%, #ffcc02 100%);
            color: #e65100;
            border: 1px solid #ffb74d;
        }
        
        .status-published {
            background: linear-gradient(135deg, #e8f5e8 0%, #4caf50 100%);
            color: white;
            border: 1px solid #66bb6a;
        }
        
        .status-archived {
            background: linear-gradient(135deg, #f5f5f5 0%, #9e9e9e 100%);
            color: white;
            border: 1px solid #bdbdbd;
        }
        
        .report-footer {
            margin-top: 3rem;
            padding: 1.5rem;
            border-top: 2px solid #e0e0e0;
            background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
            border-radius: 0 0 16px 16px;
            color: #616161;
            font-size: 0.9rem;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Container principal do relatório
    st.markdown('<div class="report-container">', unsafe_allow_html=True)
    
    # Cabeçalho do relatório
    # Tratar event_date de forma segura
    try:
        if report_data.get('event_date'):
            event_date_str = datetime.fromisoformat(report_data['event_date']).strftime('%d/%m/%Y')
        else:
            event_date_str = "Data não disponível"
    except:
        event_date_str = "Data não disponível"
    
    st.markdown(f'''
    <div class="report-header">
        <h1 style="margin: 0; color: white;">{report_data['title']}</h1>
        <div class="report-header-meta">
            <span>📅 {event_date_str}</span>
            <span>🏷️ {report_data.get('event_type', 'Tipo não disponível')}</span>
            <span class="status-badge status-{report_data['status']}">{get_status_text(report_data['status'])}</span>
        </div>
    </div>
    <div class="report-content-wrapper">
    ''', unsafe_allow_html=True)
    
    # Metadados do relatório
    if report_data.get('summary'):
        st.markdown(f'''
        <div class="report-meta">
            <h4>📋 Resumo Executivo</h4>
            <p>{report_data['summary']}</p>
        </div>
        ''', unsafe_allow_html=True)

    # Participantes
    if report_data.get('participants'):
        try:
            import json
            participants_list = json.loads(report_data['participants'])
            if participants_list:
                participants_html = "<br>".join([f'<div class="participant-item">{participant}</div>' for participant in participants_list])
                st.markdown(f'''
                <div class="participants-list">
                    <h4>👥 Participantes</h4>
                    {participants_html}
                </div>
                ''', unsafe_allow_html=True)
        except:
            pass

    # Conteúdo principal do relatório
    st.markdown('<div class="report-content">', unsafe_allow_html=True)
    st.markdown(report_data['content'])
    st.markdown('</div>', unsafe_allow_html=True)

    # Decisões tomadas
    if report_data.get('decisions'):
        st.markdown(f'''
        <div class="decision-item">
            <h4>⚖️ Decisões Tomadas</h4>
            {format_text_with_markdown(report_data['decisions'])}
        </div>
        ''', unsafe_allow_html=True)

    # Itens de ação
    if report_data.get('action_items'):
        try:
            import json
            action_items = json.loads(report_data['action_items'])
            if action_items:
                st.markdown('<h4 style="margin: 2rem 0 1rem 0; color: #ff9800;">📋 Itens de Ação</h4>', unsafe_allow_html=True)
                for item in action_items:
                    status_icon = "✅" if item.get('completed') else "⏳"
                    st.markdown(f'''
                    <div class="action-item">
                        {status_icon} {item['text']}
                    </div>
                    ''', unsafe_allow_html=True)
        except:
            pass

    # Próximos passos
    if report_data.get('next_steps'):
        st.markdown(f'''
        <hr class="section-divider">
        <div class="report-meta">
            <h4>🚀 Próximos Passos</h4>
            {format_text_with_markdown(report_data['next_steps'])}
        </div>
        ''', unsafe_allow_html=True)

    # Rodapé com informações de criação
    created_date = datetime.fromisoformat(report_data['created_at']).strftime('%d/%m/%Y às %H:%M')
    st.markdown(f'''
        <div class="report-footer">
            📝 Relatório criado em {created_date}
        </div>
    </div>
    </div>
    ''', unsafe_allow_html=True)

def format_text_with_markdown(text):
    """Formata texto com Markdown básico para HTML"""
    if not text:
        return ""
    
    # Converter quebras de linha para HTML
    text = text.replace('\n', '<br>')
    
    # Converter markdown básico para HTML
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    
    return text

def render_markdown_preview(content, title="Preview do Relatório"):
    """Renderiza uma prévia do conteúdo Markdown com design aprimorado"""
    
    st.markdown(f"""
    <style>
    .preview-container {{
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        padding: 0;
        border-radius: 16px;
        border: 2px dashed #667eea;
        margin: 1.5rem 0;
        max-height: 500px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.1);
        font-family: 'Inter', sans-serif;
    }}
    
    .preview-header {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        font-weight: 600;
        font-size: 1.1rem;
        position: sticky;
        top: 0;
        z-index: 10;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .preview-content {{
        padding: 1.5rem;
        max-height: 400px;
        overflow-y: auto;
        line-height: 1.6;
    }}
    
    .preview-content h1, .preview-content h2, .preview-content h3 {{
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }}
    
    .preview-content h1 {{
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }}
    
    .preview-content p {{
        margin-bottom: 1rem;
        color: #34495e;
    }}
    
    .preview-content ul, .preview-content ol {{
        margin: 1rem 0;
        padding-left: 1.5rem;
    }}
    
    .preview-content li {{
        margin-bottom: 0.5rem;
        color: #34495e;
    }}
    
    .preview-content blockquote {{
        border-left: 4px solid #667eea;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 0 8px 8px 0;
        font-style: italic;
    }}
    
    .preview-content code {{
        background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%);
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 0.9rem;
        color: #d32f2f;
    }}
    
    .preview-content pre {{
        background: linear-gradient(135deg, #263238 0%, #37474f 100%);
        color: #eceff1;
        padding: 1rem;
        border-radius: 8px;
        overflow-x: auto;
        margin: 1rem 0;
    }}
    
    .preview-content table {{
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }}
    
    .preview-content table th,
    .preview-content table td {{
        border: none;
        padding: 0.75rem;
        text-align: left;
        border-bottom: 1px solid #e0e0e0;
    }}
    
    .preview-content table th {{
        background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%);
        font-weight: 600;
        color: #424242;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="preview-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="preview-header">👁️ {title}</div>', unsafe_allow_html=True)
    st.markdown('<div class="preview-content">', unsafe_allow_html=True)
    st.markdown(content)
    st.markdown('</div></div>', unsafe_allow_html=True)

def render_advanced_markdown_editor(content, key="markdown_editor"):
    """Renderiza um editor de Markdown avançado com formatação automática"""
    
    # CSS para o editor
    st.markdown("""
    <style>
    .editor-toolbar {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 5px 5px 0 0;
        border: 1px solid #dee2e6;
        border-bottom: none;
    }
    
    .toolbar-button {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 3px;
        padding: 0.25rem 0.5rem;
        margin: 0.1rem;
        cursor: pointer;
        font-size: 0.875rem;
    }
    
    .toolbar-button:hover {
        background-color: #e9ecef;
    }
    
    .editor-container {
        border: 1px solid #dee2e6;
        border-radius: 0 0 5px 5px;
    }
    
    .format-help {
        background-color: #e7f3ff;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-size: 0.875rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### ✏️ Editor Avançado")
        
        # Toolbar de formatação
        st.markdown('<div class="editor-toolbar">', unsafe_allow_html=True)
        
        # Primeira linha de botões
        col1a, col1b, col1c, col1d, col1e = st.columns(5)
        
        with col1a:
            if st.button("**B**", help="Negrito", key=f"{key}_bold"):
                st.session_state[f"{key}_insert"] = "**texto em negrito**"
        
        with col1b:
            if st.button("*I*", help="Itálico", key=f"{key}_italic"):
                st.session_state[f"{key}_insert"] = "*texto em itálico*"
        
        with col1c:
            if st.button("H1", help="Título Principal", key=f"{key}_h1"):
                st.session_state[f"{key}_insert"] = "# Título Principal"
        
        with col1d:
            if st.button("H2", help="Subtítulo", key=f"{key}_h2"):
                st.session_state[f"{key}_insert"] = "## Subtítulo"
        
        with col1e:
            if st.button("H3", help="Título Menor", key=f"{key}_h3"):
                st.session_state[f"{key}_insert"] = "### Título Menor"
        
        # Segunda linha de botões
        col2a, col2b, col2c, col2d, col2e = st.columns(5)
        
        with col2a:
            if st.button("• Lista", help="Lista com marcadores", key=f"{key}_list"):
                st.session_state[f"{key}_insert"] = "- Item da lista\n- Outro item"
        
        with col2b:
            if st.button("1. Lista", help="Lista numerada", key=f"{key}_numbered"):
                st.session_state[f"{key}_insert"] = "1. Primeiro item\n2. Segundo item"
        
        with col2c:
            if st.button("[ ] Todo", help="Lista de tarefas", key=f"{key}_todo"):
                st.session_state[f"{key}_insert"] = "- [ ] Tarefa pendente\n- [x] Tarefa concluída"
        
        with col2d:
            if st.button("📋 Tabela", help="Inserir tabela", key=f"{key}_table"):
                st.session_state[f"{key}_insert"] = "| Coluna 1 | Coluna 2 |\n|----------|----------|\n| Dados 1  | Dados 2  |"
        
        with col2e:
            if st.button("> Quote", help="Citação", key=f"{key}_quote"):
                st.session_state[f"{key}_insert"] = "> Esta é uma citação"
        
        # Terceira linha de botões
        col3a, col3b, col3c, col3d, col3e = st.columns(5)
        
        with col3a:
            if st.button("🔗 Link", help="Inserir link", key=f"{key}_link"):
                st.session_state[f"{key}_insert"] = "[texto do link](https://exemplo.com)"
        
        with col3b:
            if st.button("📷 Imagem", help="Inserir imagem", key=f"{key}_image"):
                st.session_state[f"{key}_insert"] = "![alt text](url_da_imagem)"
        
        with col3c:
            if st.button("💻 Código", help="Código inline", key=f"{key}_code"):
                st.session_state[f"{key}_insert"] = "`código`"
        
        with col3d:
            if st.button("📝 Bloco", help="Bloco de código", key=f"{key}_codeblock"):
                st.session_state[f"{key}_insert"] = "```\nbloco de código\n```"
        
        with col3e:
            if st.button("📊 Gráfico", help="Inserir gráfico", key=f"{key}_chart"):
                st.session_state[f"{key}_insert"] = "```mermaid\ngraph TD\n    A[Início] --> B[Processo]\n    B --> C[Fim]\n```"
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Verificar se há texto para inserir
        insert_key = f"{key}_insert"
        if insert_key in st.session_state:
            insert_text = st.session_state[insert_key]
            # Adicionar o texto ao conteúdo atual
            if content:
                content += f"\n\n{insert_text}"
            else:
                content = insert_text
            del st.session_state[insert_key]
        
        # Editor de texto principal
        st.markdown('<div class="editor-container">', unsafe_allow_html=True)
        edited_content = st.text_area(
            "Conteúdo (Markdown)",
            value=content,
            height=500,
            key=key,
            help="Use a toolbar acima para formatação rápida ou digite diretamente em Markdown"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botões de formatação automática
        st.markdown("**Formatação Automática:**")
        col_auto1, col_auto2, col_auto3 = st.columns(3)
        
        with col_auto1:
            if st.button("🔧 Auto-Format", key=f"{key}_autoformat"):
                edited_content = auto_format_markdown(edited_content)
                st.session_state[key] = edited_content
                st.rerun()
        
        with col_auto2:
            if st.button("📝 Estruturar", key=f"{key}_structure"):
                edited_content = add_structure_to_text(edited_content)
                st.session_state[key] = edited_content
                st.rerun()
        
        with col_auto3:
            if st.button("✨ Melhorar", key=f"{key}_enhance"):
                edited_content = enhance_markdown_formatting(edited_content)
                st.session_state[key] = edited_content
                st.rerun()
        
        # Ajuda de formatação
        with st.expander("📚 Guia de Formatação Markdown"):
            st.markdown("""
            <div class="format-help">
            <strong>Formatação Básica:</strong><br>
            • <code>**negrito**</code> → <strong>negrito</strong><br>
            • <code>*itálico*</code> → <em>itálico</em><br>
            • <code># Título</code> → Título principal<br>
            • <code>## Subtítulo</code> → Subtítulo<br>
            • <code>- item</code> → Lista com marcadores<br>
            • <code>1. item</code> → Lista numerada<br>
            • <code>- [ ] tarefa</code> → Lista de tarefas<br>
            • <code>[link](url)</code> → Link<br>
            • <code>`código`</code> → Código inline<br>
            • <code>> citação</code> → Citação<br>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 👁️ Preview em Tempo Real")
        if edited_content:
            render_markdown_preview(edited_content, "Preview Atualizado")
            
            # Estatísticas do documento
            stats = get_document_stats(edited_content)
            st.markdown(f"""
            **📊 Estatísticas:**
            - Palavras: {stats['words']}
            - Caracteres: {stats['characters']}
            - Linhas: {stats['lines']}
            - Títulos: {stats['headers']}
            - Listas: {stats['lists']}
            """)
        else:
            st.info("Digite algo no editor para ver o preview")
    
    return edited_content

def render_markdown_editor(content, key="markdown_editor"):
    """Renderiza um editor de Markdown com preview lado a lado (versão simplificada)"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✏️ Editor")
        edited_content = st.text_area(
            "Conteúdo (Markdown)",
            value=content,
            height=400,
            key=key,
            help="Use formatação Markdown para estruturar seu texto"
        )
        
        # Toolbar com botões de formatação
        st.markdown("**Formatação rápida:**")
        col1a, col1b, col1c, col1d = st.columns(4)
        
        with col1a:
            if st.button("**Negrito**", key=f"{key}_bold"):
                st.session_state[f"{key}_insert"] = "**texto**"
        
        with col1b:
            if st.button("*Itálico*", key=f"{key}_italic"):
                st.session_state[f"{key}_insert"] = "*texto*"
        
        with col1c:
            if st.button("# Título", key=f"{key}_header"):
                st.session_state[f"{key}_insert"] = "## Título"
        
        with col1d:
            if st.button("• Lista", key=f"{key}_list"):
                st.session_state[f"{key}_insert"] = "- Item da lista"
    
    with col2:
        st.markdown("### 👁️ Preview")
        if edited_content:
            render_markdown_preview(edited_content, "Preview em Tempo Real")
        else:
            st.info("Digite algo no editor para ver o preview")
    
    return edited_content

def auto_format_markdown(text):
    """Aplica formatação automática ao texto Markdown"""
    if not text:
        return text
    
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
        
        # Auto-formatação de títulos
        if line.startswith('titulo:') or line.startswith('Titulo:'):
            line = f"## {line.split(':', 1)[1].strip()}"
        elif line.startswith('subtitulo:') or line.startswith('Subtitulo:'):
            line = f"### {line.split(':', 1)[1].strip()}"
        
        # Auto-formatação de listas
        elif line.startswith('- ') and not line.startswith('- [ ]') and not line.startswith('- [x]'):
            # Já é uma lista, manter
            pass
        elif re.match(r'^\d+\.?\s', line):
            # Converter para lista numerada
            line = re.sub(r'^\d+\.?\s', lambda m: f"{m.group().rstrip()}. ", line)
        elif line.startswith('*') and not line.startswith('**'):
            # Converter asterisco para lista
            line = f"- {line[1:].strip()}"
        
        # Auto-formatação de ênfase
        line = re.sub(r'\b(importante|IMPORTANTE|atenção|ATENÇÃO)\b', r'**\1**', line, flags=re.IGNORECASE)
        line = re.sub(r'\b(nota|observação|lembrete)\b', r'*\1*', line, flags=re.IGNORECASE)
        
        formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

def add_structure_to_text(text):
    """Adiciona estrutura básica ao texto não formatado"""
    if not text:
        return text
    
    lines = text.split('\n')
    structured_lines = []
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            structured_lines.append('')
            continue
        
        # Detectar seções comuns
        lower_line = line.lower()
        
        if any(keyword in lower_line for keyword in ['resumo', 'introdução', 'objetivo']):
            structured_lines.append(f"## {line}")
            current_section = 'intro'
        elif any(keyword in lower_line for keyword in ['participantes', 'presentes']):
            structured_lines.append(f"## {line}")
            current_section = 'participants'
        elif any(keyword in lower_line for keyword in ['discussão', 'desenvolvimento', 'conteúdo']):
            structured_lines.append(f"## {line}")
            current_section = 'content'
        elif any(keyword in lower_line for keyword in ['decisões', 'conclusões', 'resultados']):
            structured_lines.append(f"## {line}")
            current_section = 'decisions'
        elif any(keyword in lower_line for keyword in ['próximos passos', 'ações', 'tarefas']):
            structured_lines.append(f"## {line}")
            current_section = 'actions'
        else:
            # Aplicar formatação baseada na seção atual
            if current_section == 'participants' and not line.startswith('-'):
                structured_lines.append(f"- {line}")
            elif current_section == 'actions' and not line.startswith('-'):
                structured_lines.append(f"- [ ] {line}")
            else:
                structured_lines.append(line)
    
    return '\n'.join(structured_lines)

def enhance_markdown_formatting(text):
    """Melhora a formatação do Markdown existente"""
    if not text:
        return text
    
    # Aplicar melhorias
    text = auto_format_markdown(text)
    
    # Adicionar espaçamento adequado
    lines = text.split('\n')
    enhanced_lines = []
    prev_line_type = None
    
    for i, line in enumerate(lines):
        current_line_type = get_line_type(line)
        
        # Adicionar espaçamento antes de títulos
        if current_line_type == 'header' and prev_line_type and prev_line_type != 'empty':
            enhanced_lines.append('')
        
        enhanced_lines.append(line)
        
        # Adicionar espaçamento depois de títulos
        if current_line_type == 'header' and i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if next_line and not next_line.startswith('#'):
                enhanced_lines.append('')
        
        prev_line_type = current_line_type
    
    return '\n'.join(enhanced_lines)

def get_line_type(line):
    """Identifica o tipo de linha Markdown"""
    line = line.strip()
    if not line:
        return 'empty'
    elif line.startswith('#'):
        return 'header'
    elif line.startswith('-') or line.startswith('*') or line.startswith('+'):
        return 'list'
    elif re.match(r'^\d+\.', line):
        return 'numbered_list'
    elif line.startswith('>'):
        return 'quote'
    elif line.startswith('```'):
        return 'code_block'
    else:
        return 'text'

def get_document_stats(text):
    """Calcula estatísticas do documento"""
    if not text:
        return {'words': 0, 'characters': 0, 'lines': 0, 'headers': 0, 'lists': 0}
    
    lines = text.split('\n')
    words = len(text.split())
    characters = len(text)
    headers = len([line for line in lines if line.strip().startswith('#')])
    lists = len([line for line in lines if line.strip().startswith(('-', '*', '+')) or re.match(r'^\d+\.', line.strip())])
    
    return {
        'words': words,
        'characters': characters,
        'lines': len(lines),
        'headers': headers,
        'lists': lists
    }

def format_text_with_markdown(text):
    """Converte texto simples em HTML com formatação básica de Markdown"""
    if not text:
        return ""
    
    # Converter quebras de linha em <br>
    text = text.replace('\n', '<br>')
    
    # Converter listas simples
    text = re.sub(r'^- (.+)', r'• \1', text, flags=re.MULTILINE)
    
    return text

def get_status_text(status):
    """Converte status do banco para texto legível"""
    status_map = {
        'draft': 'Rascunho',
        'published': 'Publicado',
        'archived': 'Arquivado'
    }
    return status_map.get(status, status)

def export_report_to_markdown(report_data):
    """Exporta relatório para arquivo Markdown"""
    
    # Tratar event_date de forma segura
    try:
        if report_data.get('event_date'):
            event_date_str = datetime.fromisoformat(report_data['event_date']).strftime('%d/%m/%Y')
        else:
            event_date_str = "Data não disponível"
    except:
        event_date_str = "Data não disponível"
    
    content = f"""# {report_data['title']}

**Data do Evento:** {event_date_str}
**Tipo:** {report_data.get('event_type', 'Tipo não disponível')}
**Status:** {get_status_text(report_data['status'])}

"""
    
    if report_data.get('summary'):
        content += f"""## Resumo Executivo

{report_data['summary']}

"""
    
    if report_data.get('participants'):
        try:
            import json
            participants_list = json.loads(report_data['participants'])
            if participants_list:
                content += "## Participantes\n\n"
                for participant in participants_list:
                    content += f"- {participant}\n"
                content += "\n"
        except:
            pass
    
    content += f"""## Conteúdo do Relatório

{report_data['content']}

"""
    
    if report_data.get('decisions'):
        content += f"""## Decisões Tomadas

{report_data['decisions']}

"""
    
    if report_data.get('action_items'):
        try:
            import json
            action_items = json.loads(report_data['action_items'])
            if action_items:
                content += "## Itens de Ação\n\n"
                for item in action_items:
                    status = "[CONCLUÍDO]" if item.get('completed') else "[PENDENTE]"
                    content += f"- {status} {item['text']}\n"
                content += "\n"
        except:
            pass
    
    if report_data.get('next_steps'):
        content += f"""## Próximos Passos

{report_data['next_steps']}

"""
    
    # Rodapé
    try:
        created_date = datetime.fromisoformat(report_data['created_at']).strftime('%d/%m/%Y às %H:%M')
    except:
        created_date = "Data não disponível"
    
    content += f"""---

*Relatório criado em {created_date}*
"""
    
    return content

def render_markdown_preview(content, title="Preview do Relatório"):
    """Renderiza uma prévia do conteúdo Markdown com design aprimorado"""
    
    st.markdown(f"""
    <style>
    .preview-container {{
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        padding: 0;
        border-radius: 16px;
        border: 2px dashed #667eea;
        margin: 1.5rem 0;
        max-height: 500px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.1);
        font-family: 'Inter', sans-serif;
    }}
    
    .preview-header {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        font-weight: 600;
        font-size: 1.1rem;
        position: sticky;
        top: 0;
        z-index: 10;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .preview-content {{
        padding: 1.5rem;
        max-height: 400px;
        overflow-y: auto;
        line-height: 1.6;
    }}
    
    .preview-content h1, .preview-content h2, .preview-content h3 {{
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }}
    
    .preview-content h1 {{
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }}
    
    .preview-content p {{
        margin-bottom: 1rem;
        color: #34495e;
    }}
    
    .preview-content ul, .preview-content ol {{
        margin: 1rem 0;
        padding-left: 1.5rem;
    }}
    
    .preview-content li {{
        margin-bottom: 0.5rem;
        color: #34495e;
    }}
    
    .preview-content blockquote {{
        border-left: 4px solid #667eea;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 0 8px 8px 0;
        font-style: italic;
    }}
    
    .preview-content code {{
        background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%);
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 0.9rem;
        color: #d32f2f;
    }}
    
    .preview-content pre {{
        background: linear-gradient(135deg, #263238 0%, #37474f 100%);
        color: #eceff1;
        padding: 1rem;
        border-radius: 8px;
        overflow-x: auto;
        margin: 1rem 0;
    }}
    
    .preview-content table {{
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }}
    
    .preview-content table th,
    .preview-content table td {{
        border: none;
        padding: 0.75rem;
        text-align: left;
        border-bottom: 1px solid #e0e0e0;
    }}
    
    .preview-content table th {{
        background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%);
        font-weight: 600;
        color: #424242;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="preview-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="preview-header">👁️ {title}</div>', unsafe_allow_html=True)
    st.markdown('<div class="preview-content">', unsafe_allow_html=True)
    st.markdown(content)
    st.markdown('</div></div>', unsafe_allow_html=True)

def render_advanced_markdown_editor(content, key="markdown_editor"):
    """Renderiza um editor de Markdown avançado com formatação automática"""
    
    # CSS para o editor
    st.markdown("""
    <style>
    .editor-toolbar {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 5px 5px 0 0;
        border: 1px solid #dee2e6;
        border-bottom: none;
    }
    
    .toolbar-button {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 3px;
        padding: 0.25rem 0.5rem;
        margin: 0.1rem;
        cursor: pointer;
        font-size: 0.875rem;
    }
    
    .toolbar-button:hover {
        background-color: #e9ecef;
    }
    
    .editor-container {
        border: 1px solid #dee2e6;
        border-radius: 0 0 5px 5px;
    }
    
    .format-help {
        background-color: #e7f3ff;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-size: 0.875rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### ✏️ Editor Avançado")
        
        # Toolbar de formatação
        st.markdown('<div class="editor-toolbar">', unsafe_allow_html=True)
        
        # Primeira linha de botões
        col1a, col1b, col1c, col1d, col1e = st.columns(5)
        
        with col1a:
            if st.button("**B**", help="Negrito", key=f"{key}_bold"):
                st.session_state[f"{key}_insert"] = "**texto em negrito**"
        
        with col1b:
            if st.button("*I*", help="Itálico", key=f"{key}_italic"):
                st.session_state[f"{key}_insert"] = "*texto em itálico*"
        
        with col1c:
            if st.button("H1", help="Título Principal", key=f"{key}_h1"):
                st.session_state[f"{key}_insert"] = "# Título Principal"
        
        with col1d:
            if st.button("H2", help="Subtítulo", key=f"{key}_h2"):
                st.session_state[f"{key}_insert"] = "## Subtítulo"
        
        with col1e:
            if st.button("H3", help="Título Menor", key=f"{key}_h3"):
                st.session_state[f"{key}_insert"] = "### Título Menor"
        
        # Segunda linha de botões
        col2a, col2b, col2c, col2d, col2e = st.columns(5)
        
        with col2a:
            if st.button("• Lista", help="Lista com marcadores", key=f"{key}_list"):
                st.session_state[f"{key}_insert"] = "- Item da lista\n- Outro item"
        
        with col2b:
            if st.button("1. Lista", help="Lista numerada", key=f"{key}_numbered"):
                st.session_state[f"{key}_insert"] = "1. Primeiro item\n2. Segundo item"
        
        with col2c:
            if st.button("[ ] Todo", help="Lista de tarefas", key=f"{key}_todo"):
                st.session_state[f"{key}_insert"] = "- [ ] Tarefa pendente\n- [x] Tarefa concluída"
        
        with col2d:
            if st.button("📋 Tabela", help="Inserir tabela", key=f"{key}_table"):
                st.session_state[f"{key}_insert"] = "| Coluna 1 | Coluna 2 |\n|----------|----------|\n| Dados 1  | Dados 2  |"
        
        with col2e:
            if st.button("> Quote", help="Citação", key=f"{key}_quote"):
                st.session_state[f"{key}_insert"] = "> Esta é uma citação"
        
        # Terceira linha de botões
        col3a, col3b, col3c, col3d, col3e = st.columns(5)
        
        with col3a:
            if st.button("🔗 Link", help="Inserir link", key=f"{key}_link"):
                st.session_state[f"{key}_insert"] = "[texto do link](https://exemplo.com)"
        
        with col3b:
            if st.button("📷 Imagem", help="Inserir imagem", key=f"{key}_image"):
                st.session_state[f"{key}_insert"] = "![alt text](url_da_imagem)"
        
        with col3c:
            if st.button("💻 Código", help="Código inline", key=f"{key}_code"):
                st.session_state[f"{key}_insert"] = "`código`"
        
        with col3d:
            if st.button("📝 Bloco", help="Bloco de código", key=f"{key}_codeblock"):
                st.session_state[f"{key}_insert"] = "```\nbloco de código\n```"
        
        with col3e:
            if st.button("📊 Gráfico", help="Inserir gráfico", key=f"{key}_chart"):
                st.session_state[f"{key}_insert"] = "```mermaid\ngraph TD\n    A[Início] --> B[Processo]\n    B --> C[Fim]\n```"
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Verificar se há texto para inserir
        insert_key = f"{key}_insert"
        if insert_key in st.session_state:
            insert_text = st.session_state[insert_key]
            # Adicionar o texto ao conteúdo atual
            if content:
                content += f"\n\n{insert_text}"
            else:
                content = insert_text
            del st.session_state[insert_key]
        
        # Editor de texto principal
        st.markdown('<div class="editor-container">', unsafe_allow_html=True)
        edited_content = st.text_area(
            "Conteúdo (Markdown)",
            value=content,
            height=500,
            key=key,
            help="Use a toolbar acima para formatação rápida ou digite diretamente em Markdown"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botões de formatação automática
        st.markdown("**Formatação Automática:**")
        col_auto1, col_auto2, col_auto3 = st.columns(3)
        
        with col_auto1:
            if st.button("🔧 Auto-Format", key=f"{key}_autoformat"):
                edited_content = auto_format_markdown(edited_content)
                st.session_state[key] = edited_content
                st.rerun()
        
        with col_auto2:
            if st.button("📝 Estruturar", key=f"{key}_structure"):
                edited_content = add_structure_to_text(edited_content)
                st.session_state[key] = edited_content
                st.rerun()
        
        with col_auto3:
            if st.button("✨ Melhorar", key=f"{key}_enhance"):
                edited_content = enhance_markdown_formatting(edited_content)
                st.session_state[key] = edited_content
                st.rerun()
        
        # Ajuda de formatação
        with st.expander("📚 Guia de Formatação Markdown"):
            st.markdown("""
            <div class="format-help">
            <strong>Formatação Básica:</strong><br>
            • <code>**negrito**</code> → <strong>negrito</strong><br>
            • <code>*itálico*</code> → <em>itálico</em><br>
            • <code># Título</code> → Título principal<br>
            • <code>## Subtítulo</code> → Subtítulo<br>
            • <code>- item</code> → Lista com marcadores<br>
            • <code>1. item</code> → Lista numerada<br>
            • <code>- [ ] tarefa</code> → Lista de tarefas<br>
            • <code>[link](url)</code> → Link<br>
            • <code>`código`</code> → Código inline<br>
            • <code>> citação</code> → Citação<br>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 👁️ Preview em Tempo Real")
        if edited_content:
            render_markdown_preview(edited_content, "Preview Atualizado")
            
            # Estatísticas do documento
            stats = get_document_stats(edited_content)
            st.markdown(f"""
            **📊 Estatísticas:**
            - Palavras: {stats['words']}
            - Caracteres: {stats['characters']}
            - Linhas: {stats['lines']}
            - Títulos: {stats['headers']}
            - Listas: {stats['lists']}
            """)
        else:
            st.info("Digite algo no editor para ver o preview")
    
    return edited_content

def render_markdown_editor(content, key="markdown_editor"):
    """Renderiza um editor de Markdown com preview lado a lado (versão simplificada)"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✏️ Editor")
        edited_content = st.text_area(
            "Conteúdo (Markdown)",
            value=content,
            height=400,
            key=key,
            help="Use formatação Markdown para estruturar seu texto"
        )
        
        # Toolbar com botões de formatação
        st.markdown("**Formatação rápida:**")
        col1a, col1b, col1c, col1d = st.columns(4)
        
        with col1a:
            if st.button("**Negrito**", key=f"{key}_bold"):
                st.session_state[f"{key}_insert"] = "**texto**"
        
        with col1b:
            if st.button("*Itálico*", key=f"{key}_italic"):
                st.session_state[f"{key}_insert"] = "*texto*"
        
        with col1c:
            if st.button("# Título", key=f"{key}_header"):
                st.session_state[f"{key}_insert"] = "## Título"
        
        with col1d:
            if st.button("• Lista", key=f"{key}_list"):
                st.session_state[f"{key}_insert"] = "- Item da lista"
    
    with col2:
        st.markdown("### 👁️ Preview")
        if edited_content:
            render_markdown_preview(edited_content, "Preview em Tempo Real")
        else:
            st.info("Digite algo no editor para ver o preview")
    
    return edited_content

def auto_format_markdown(text):
    """Aplica formatação automática ao texto Markdown"""
    if not text:
        return text
    
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
        
        # Auto-formatação de títulos
        if line.startswith('titulo:') or line.startswith('Titulo:'):
            line = f"## {line.split(':', 1)[1].strip()}"
        elif line.startswith('subtitulo:') or line.startswith('Subtitulo:'):
            line = f"### {line.split(':', 1)[1].strip()}"
        
        # Auto-formatação de listas
        elif line.startswith('- ') and not line.startswith('- [ ]') and not line.startswith('- [x]'):
            # Já é uma lista, manter
            pass
        elif re.match(r'^\d+\.?\s', line):
            # Converter para lista numerada
            line = re.sub(r'^\d+\.?\s', lambda m: f"{m.group().rstrip()}. ", line)
        elif line.startswith('*') and not line.startswith('**'):
            # Converter asterisco para lista
            line = f"- {line[1:].strip()}"
        
        # Auto-formatação de ênfase
        line = re.sub(r'\b(importante|IMPORTANTE|atenção|ATENÇÃO)\b', r'**\1**', line, flags=re.IGNORECASE)
        line = re.sub(r'\b(nota|observação|lembrete)\b', r'*\1*', line, flags=re.IGNORECASE)
        
        formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

def add_structure_to_text(text):
    """Adiciona estrutura básica ao texto não formatado"""
    if not text:
        return text
    
    lines = text.split('\n')
    structured_lines = []
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            structured_lines.append('')
            continue
        
        # Detectar seções comuns
        lower_line = line.lower()
        
        if any(keyword in lower_line for keyword in ['resumo', 'introdução', 'objetivo']):
            structured_lines.append(f"## {line}")
            current_section = 'intro'
        elif any(keyword in lower_line for keyword in ['participantes', 'presentes']):
            structured_lines.append(f"## {line}")
            current_section = 'participants'
        elif any(keyword in lower_line for keyword in ['discussão', 'desenvolvimento', 'conteúdo']):
            structured_lines.append(f"## {line}")
            current_section = 'content'
        elif any(keyword in lower_line for keyword in ['decisões', 'conclusões', 'resultados']):
            structured_lines.append(f"## {line}")
            current_section = 'decisions'
        elif any(keyword in lower_line for keyword in ['próximos passos', 'ações', 'tarefas']):
            structured_lines.append(f"## {line}")
            current_section = 'actions'
        else:
            # Aplicar formatação baseada na seção atual
            if current_section == 'participants' and not line.startswith('-'):
                structured_lines.append(f"- {line}")
            elif current_section == 'actions' and not line.startswith('-'):
                structured_lines.append(f"- [ ] {line}")
            else:
                structured_lines.append(line)
    
    return '\n'.join(structured_lines)

def enhance_markdown_formatting(text):
    """Melhora a formatação do Markdown existente"""
    if not text:
        return text
    
    # Aplicar melhorias
    text = auto_format_markdown(text)
    
    # Adicionar espaçamento adequado
    lines = text.split('\n')
    enhanced_lines = []
    prev_line_type = None
    
    for i, line in enumerate(lines):
        current_line_type = get_line_type(line)
        
        # Adicionar espaçamento antes de títulos
        if current_line_type == 'header' and prev_line_type and prev_line_type != 'empty':
            enhanced_lines.append('')
        
        enhanced_lines.append(line)
        
        # Adicionar espaçamento depois de títulos
        if current_line_type == 'header' and i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if next_line and not next_line.startswith('#'):
                enhanced_lines.append('')
        
        prev_line_type = current_line_type
    
    return '\n'.join(enhanced_lines)

def get_line_type(line):
    """Identifica o tipo de linha Markdown"""
    line = line.strip()
    if not line:
        return 'empty'
    elif line.startswith('#'):
        return 'header'
    elif line.startswith('-') or line.startswith('*') or line.startswith('+'):
        return 'list'
    elif re.match(r'^\d+\.', line):
        return 'numbered_list'
    elif line.startswith('>'):
        return 'quote'
    elif line.startswith('```'):
        return 'code_block'
    else:
        return 'text'

def get_document_stats(text):
    """Calcula estatísticas do documento"""
    if not text:
        return {'words': 0, 'characters': 0, 'lines': 0, 'headers': 0, 'lists': 0}
    
    lines = text.split('\n')
    words = len(text.split())
    characters = len(text)
    headers = len([line for line in lines if line.strip().startswith('#')])
    lists = len([line for line in lines if line.strip().startswith(('-', '*', '+')) or re.match(r'^\d+\.', line.strip())])
    
    return {
        'words': words,
        'characters': characters,
        'lines': len(lines),
        'headers': headers,
        'lists': lists
    }

def format_text_with_markdown(text):
    """Converte texto simples em HTML com formatação básica de Markdown"""
    if not text:
        return ""
    
    # Converter quebras de linha em <br>
    text = text.replace('\n', '<br>')
    
    # Converter listas simples
    text = re.sub(r'^- (.+)', r'• \1', text, flags=re.MULTILINE)
    
    return text

def get_status_text(status):
    """Converte status do banco para texto legível"""
    status_map = {
        'draft': 'Rascunho',
        'published': 'Publicado',
        'archived': 'Arquivado'
    }
    return status_map.get(status, status)

def export_report_to_markdown(report_data):
    """Exporta relatório para arquivo Markdown"""
    
    # Tratar event_date de forma segura
    try:
        if report_data.get('event_date'):
            event_date_str = datetime.fromisoformat(report_data['event_date']).strftime('%d/%m/%Y')
        else:
            event_date_str = "Data não disponível"
    except:
        event_date_str = "Data não disponível"
    
    content = f"""# {report_data['title']}

**Data do Evento:** {event_date_str}
**Tipo:** {report_data.get('event_type', 'Tipo não disponível')}
**Status:** {get_status_text(report_data['status'])}

"""
    
    if report_data.get('summary'):
        content += f"""## Resumo Executivo

{report_data['summary']}

"""
    
    if report_data.get('participants'):
        try:
            import json
            participants_list = json.loads(report_data['participants'])
            if participants_list:
                content += "## Participantes\n\n"
                for participant in participants_list:
                    content += f"- {participant}\n"
                content += "\n"
        except:
            pass
    
    content += f"""## Conteúdo do Relatório

{report_data['content']}

"""
    
    if report_data.get('decisions'):
        content += f"""## Decisões Tomadas

{report_data['decisions']}

"""
    
    if report_data.get('action_items'):
        try:
            import json
            action_items = json.loads(report_data['action_items'])
            if action_items:
                content += "## Itens de Ação\n\n"
                for item in action_items:
                    status = "[CONCLUÍDO]" if item.get('completed') else "[PENDENTE]"
                    content += f"- {status} {item['text']}\n"
                content += "\n"
        except:
            pass
    
    if report_data.get('next_steps'):
        content += f"""## Próximos Passos

{report_data['next_steps']}

"""
    
    # Rodapé
    try:
        created_date = datetime.fromisoformat(report_data['created_at']).strftime('%d/%m/%Y às %H:%M')
    except:
        created_date = "Data não disponível"
    
    content += f"""---

*Relatório criado em {created_date}*
"""
    
    return content

def render_markdown_preview(content, title="Preview do Relatório"):
    """Renderiza uma prévia do conteúdo Markdown com design aprimorado"""
    
    st.markdown(f"""
    <style>
    .preview-container {{
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        padding: 0;
        border-radius: 16px;
        border: 2px dashed #667eea;
        margin: 1.5rem 0;
        max-height: 500px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.1);
        font-family: 'Inter', sans-serif;
    }}
    
    .preview-header {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        font-weight: 600;
        font-size: 1.1rem;
        position: sticky;
        top: 0;
        z-index: 10;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .preview-content {{
        padding: 1.5rem;
        max-height: 400px;
        overflow-y: auto;
        line-height: 1.6;
    }}
    
    .preview-content h1, .preview-content h2, .preview-content h3 {{
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }}
    
    .preview-content h1 {{
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }}
    
    .preview-content p {{
        margin-bottom: 1rem;
        color: #34495e;
    }}
    
    .preview-content ul, .preview-content ol {{
        margin: 1rem 0;
        padding-left: 1.5rem;
    }}
    
    .preview-content li {{
        margin-bottom: 0.5rem;
        color: #34495e;
    }}
    
    .preview-content blockquote {{
        border-left: 4px solid #667eea;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 0 8px 8px 0;
        font-style: italic;
    }}
    
    .preview-content code {{
        background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%);
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 0.9rem;
        color: #d32f2f;
    }}
    
    .preview-content pre {{
        background: linear-gradient(135deg, #263238 0%, #37474f 100%);
        color: #eceff1;
        padding: 1rem;
        border-radius: 8px;
        overflow-x: auto;
        margin: 1rem 0;
    }}
    
    .preview-content table {{
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }}
    
    .preview-content table th,
    .preview-content table td {{
        border: none;
        padding: 0.75rem;
        text-align: left;
        border-bottom: 1px solid #e0e0e0;
    }}
    
    .preview-content table th {{
        background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%);
        font-weight: 600;
        color: #424242;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="preview-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="preview-header">👁️ {title}</div>', unsafe_allow_html=True)
    st.markdown('<div class="preview-content">', unsafe_allow_html=True)
    st.markdown(content)
    st.markdown('</div></div>', unsafe_allow_html=True)

def render_advanced_markdown_editor(content, key="markdown_editor"):
    """Renderiza um editor de Markdown avançado com formatação automática"""
    
    # CSS para o editor
    st.markdown("""
    <style>
    .editor-toolbar {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 5px 5px 0 0;
        border: 1px solid #dee2e6;
        border-bottom: none;
    }
    
    .toolbar-button {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 3px;
        padding: 0.25rem 0.5rem;
        margin: 0.1rem;
        cursor: pointer;
        font-size: 0.875rem;
    }
    
    .toolbar-button:hover {
        background-color: #e9ecef;
    }
    
    .editor-container {
        border: 1px solid #dee2e6;
        border-radius: 0 0 5px 5px;
    }
    
    .format-help {
        background-color: #e7f3ff;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-size: 0.875rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### ✏️ Editor Avançado")
        
        # Toolbar de formatação
        st.markdown('<div class="editor-toolbar">', unsafe_allow_html=True)
        
        # Primeira linha de botões
        col1a, col1b, col1c, col1d, col1e = st.columns(5)
        
        with col1a:
            if st.button("**B**", help="Negrito", key=f"{key}_bold"):
                st.session_state[f"{key}_insert"] = "**texto em negrito**"
        
        with col1b:
            if st.button("*I*", help="Itálico", key=f"{key}_italic"):
                st.session_state[f"{key}_insert"] = "*texto em itálico*"
        
        with col1c:
            if st.button("H1", help="Título Principal", key=f"{key}_h1"):
                st.session_state[f"{key}_insert"] = "# Título Principal"
        
        with col1d:
            if st.button("H2", help="Subtítulo", key=f"{key}_h2"):
                st.session_state[f"{key}_insert"] = "## Subtítulo"
        
        with col1e:
            if st.button("H3", help="Título Menor", key=f"{key}_h3"):
                st.session_state[f"{key}_insert"] = "### Título Menor"
        
        # Segunda linha de botões
        col2a, col2b, col2c, col2d, col2e = st.columns(5)
        
        with col2a:
            if st.button("• Lista", help="Lista com marcadores", key=f"{key}_list"):
                st.session_state[f"{key}_insert"] = "- Item da lista\n- Outro item"
        
        with col2b:
            if st.button("1. Lista", help="Lista numerada", key=f"{key}_numbered"):
                st.session_state[f"{key}_insert"] = "1. Primeiro item\n2. Segundo item"
        
        with col2c:
            if st.button("[ ] Todo", help="Lista de tarefas", key=f"{key}_todo"):
                st.session_state[f"{key}_insert"] = "- [ ] Tarefa pendente\n- [x] Tarefa concluída"
        
        with col2d:
            if st.button("📋 Tabela", help="Inserir tabela", key=f"{key}_table"):
                st.session_state[f"{key}_insert"] = "| Coluna 1 | Coluna 2 |\n|----------|----------|\n| Dados 1  | Dados 2  |"
        
        with col2e:
            if st.button("> Quote", help="Citação", key=f"{key}_quote"):
                st.session_state[f"{key}_insert"] = "> Esta é uma citação"
        
        # Terceira linha de botões
        col3a, col3b, col3c, col3d, col3e = st.columns(5)
        
        with col3a:
            if st.button("🔗 Link", help="Inserir link", key=f"{key}_link"):
                st.session_state[f"{key}_insert"] = "[texto do link](https://exemplo.com)"
        
        with col3b:
            if st.button("📷 Imagem", help="Inserir imagem", key=f"{key}_image"):
                st.session_state[f"{key}_insert"] = "![alt text](url_da_imagem)"
        
        with col3c:
            if st.button("💻 Código", help="Código inline", key=f"{key}_code"):
                st.session_state[f"{key}_insert"] = "`código`"
        
        with col3d:
            if st.button("📝 Bloco", help="Bloco de código", key=f"{key}_codeblock"):
                st.session_state[f"{key}_insert"] = "```\nbloco de código\n```"
        
        with col3e:
            if st.button("📊 Gráfico", help="Inserir gráfico", key=f"{key}_chart"):
                st.session_state[f"{key}_insert"] = "```mermaid\ngraph TD\n    A[Início] --> B[Processo]\n    B --> C[Fim]\n```"
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Verificar se há texto para inserir
        insert_key = f"{key}_insert"
        if insert_key in st.session_state:
            insert_text = st.session_state[insert_key]
            # Adicionar o texto ao conteúdo atual
            if content:
                content += f"\n\n{insert_text}"
            else:
                content = insert_text
            del st.session_state[insert_key]
        
        # Editor de texto principal
        st.markdown('<div class="editor-container">', unsafe_allow_html=True)
        edited_content = st.text_area(
            "Conteúdo (Markdown)",
            value=content,
            height=500,
            key=key,
            help="Use a toolbar acima para formatação rápida ou digite diretamente em Markdown"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botões de formatação automática
        st.markdown("**Formatação Automática:**")
        col_auto1, col_auto2, col_auto3 = st.columns(3)
        
        with col_auto1:
            if st.button("🔧 Auto-Format", key=f"{key}_autoformat"):
                edited_content = auto_format_markdown(edited_content)
                st.session_state[key] = edited_content
                st.rerun()
        
        with col_auto2:
            if st.button("📝 Estruturar", key=f"{key}_structure"):
                edited_content = add_structure_to_text(edited_content)
                st.session_state[key] = edited_content
                st.rerun()
        
        with col_auto3:
            if st.button("✨ Melhorar", key=f"{key}_enhance"):
                edited_content = enhance_markdown_formatting(edited_content)
                st.session_state[key] = edited_content
                st.rerun()
        
        # Ajuda de formatação
        with st.expander("📚 Guia de Formatação Markdown"):
            st.markdown("""
            <div class="format-help">
            <strong>Formatação Básica:</strong><br>
            • <code>**negrito**</code> → <strong>negrito</strong><br>
            • <code>*itálico*</code> → <em>itálico</em><br>
            • <code># Título</code> → Título principal<br>
            • <code>## Subtítulo</code> → Subtítulo<br>
            • <code>- item</code> → Lista com marcadores<br>
            • <code>1. item</code> → Lista numerada<br>
            • <code>- [ ] tarefa</code> → Lista de tarefas<br>
            • <code>[link](url)</code> → Link<br>
            • <code>`código`</code> → Código inline<br>
            • <code>> citação</code> → Citação<br>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 👁️ Preview em Tempo Real")
        if edited_content:
            render_markdown_preview(edited_content, "Preview Atualizado")
            
            # Estatísticas do documento
            stats = get_document_stats(edited_content)
            st.markdown(f"""
            **📊 Estatísticas:**
            - Palavras: {stats['words']}
            - Caracteres: {stats['characters']}
            - Linhas: {stats['lines']}
            - Títulos: {stats['headers']}
            - Listas: {stats['lists']}
            """)
        else:
            st.info("Digite algo no editor para ver o preview")
    
    return edited_content

def render_markdown_editor(content, key="markdown_editor"):
    """Renderiza um editor de Markdown com preview lado a lado (versão simplificada)"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✏️ Editor")
        edited_content = st.text_area(
            "Conteúdo (Markdown)",
            value=content,
            height=400,
            key=key,
            help="Use formatação Markdown para estruturar seu texto"
        )
        
        # Toolbar com botões de formatação
        st.markdown("**Formatação rápida:**")
        col1a, col1b, col1c, col1d = st.columns(4)
        
        with col1a:
            if st.button("**Negrito**", key=f"{key}_bold"):
                st.session_state[f"{key}_insert"] = "**texto**"
        
        with col1b:
            if st.button("*Itálico*", key=f"{key}_italic"):
                st.session_state[f"{key}_insert"] = "*texto*"
        
        with col1c:
            if st.button("# Título", key=f"{key}_header"):
                st.session_state[f"{key}_insert"] = "## Título"
        
        with col1d:
            if st.button("• Lista", key=f"{key}_list"):
                st.session_state[f"{key}_insert"] = "- Item da lista"
    
    with col2:
        st.markdown("### 👁️ Preview")
        if edited_content:
            render_markdown_preview(edited_content, "Preview em Tempo Real")
        else:
            st.info("Digite algo no editor para ver o preview")
    
    return edited_content

def auto_format_markdown(text):
    """Aplica formatação automática ao texto Markdown"""
    if not text:
        return text
    
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
        
        # Auto-formatação de títulos
        if line.startswith('titulo:') or line.startswith('Titulo:'):
            line = f"## {line.split(':', 1)[1].strip()}"
        elif line.startswith('subtitulo:') or line.startswith('Subtitulo:'):
            line = f"### {line.split(':', 1)[1].strip()}"
        
        # Auto-formatação de listas
        elif line.startswith('- ') and not line.startswith('- [ ]') and not line.startswith('- [x]'):
            # Já é uma lista, manter
            pass
        elif re.match(r'^\d+\.?\s', line):
            # Converter para lista numerada
            line = re.sub(r'^\d+\.?\s', lambda m: f"{m.group().rstrip()}. ", line)
        elif line.startswith('*') and not line.startswith('**'):
            # Converter asterisco para lista
            line = f"- {line[1:].strip()}"
        
        # Auto-formatação de ênfase
        line = re.sub(r'\b(importante|IMPORTANTE|atenção|ATENÇÃO)\b', r'**\1**', line, flags=re.IGNORECASE)
        line = re.sub(r'\b(nota|observação|lembrete)\b', r'*\1*', line, flags=re.IGNORECASE)
        
        formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)