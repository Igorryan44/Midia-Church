import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import re
from app.database.local_connection import db_manager
from app.utils.auth import get_current_user
from app.utils.validation import DataValidator, SecurityHelper
from app.components.markdown_viewer import render_markdown_report, render_markdown_preview, render_markdown_editor, export_report_to_markdown

def render_meeting_reports():
    """Renderiza o módulo de relatórios de reuniões"""
    
    # Verificar se está visualizando um relatório específico
    if 'viewing_report' in st.session_state:
        render_report_viewer()
        return
    
    # Verificar se está editando um relatório
    if 'editing_report' in st.session_state:
        report_id = st.session_state.editing_report
        report_data = get_report_by_id(report_id)
        if report_data:
            render_report_editor(report_data)
        else:
            st.error("Relatório não encontrado!")
            del st.session_state.editing_report
            st.rerun()
        return
    
    # Verificar se está editando um template
    if 'editing_template' in st.session_state:
        render_template_editor()
        return
    
    st.title("📝 Relatórios de Reuniões")
    st.markdown("Crie e gerencie relatórios detalhados de reuniões com formatação automática em Markdown.")
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Meus Relatórios", 
        "➕ Novo Relatório", 
        "📄 Templates", 
        "🔍 Buscar Relatórios"
    ])
    
    with tab1:
        render_my_reports()
    
    with tab2:
        render_new_report()
    
    with tab3:
        render_templates()
    
    with tab4:
        render_search_reports()

def render_report_viewer():
    """Renderiza a visualização completa de um relatório"""
    
    report_id = st.session_state.viewing_report
    report = get_report_by_id(report_id)
    
    if not report:
        st.error("Relatório não encontrado!")
        if st.button("⬅️ Voltar"):
            del st.session_state.viewing_report
            st.rerun()
        return
    
    # Botões de navegação
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("⬅️ Voltar"):
            del st.session_state.viewing_report
            st.rerun()
    
    with col2:
        if st.button("✏️ Editar"):
            st.session_state.editing_report = report_id
            del st.session_state.viewing_report
            st.rerun()
    
    with col3:
        if st.button("📥 Exportar MD"):
            markdown_content = export_report_to_markdown(report)
            st.download_button(
                label="💾 Baixar Markdown",
                data=markdown_content,
                file_name=f"relatorio_{report['title'].replace(' ', '_')}.md",
                mime="text/markdown"
            )
    
    with col4:
        if st.button("🖨️ Imprimir"):
            st.info("💡 Use Ctrl+P para imprimir esta página")
    
    st.divider()
    
    # Renderizar o relatório
    render_markdown_report(report)

def render_report_editor(report_data):
    """Renderiza o editor de relatório"""
    from app.components.markdown_viewer import render_form_compatible_markdown_editor, export_report_to_markdown
    
    st.markdown("### ✏️ Editar Relatório")
    
    # Formulário de edição
    with st.form("edit_report_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            title = st.text_input("Título do Relatório", value=report_data['title'])
            summary = st.text_area("Resumo Executivo", value=report_data.get('summary', ''), height=100)
        
        with col2:
            status = st.selectbox(
                "Status",
                options=['draft', 'published', 'archived'],
                index=['draft', 'published', 'archived'].index(report_data['status']),
                format_func=lambda x: {'draft': '📝 Rascunho', 'published': '✅ Publicado', 'archived': '📦 Arquivado'}[x]
            )
        
        # Editor de conteúdo avançado
        st.markdown("---")
        content = render_form_compatible_markdown_editor(
            report_data.get('content', ''),
            key="edit_content"
        )
        
        # Seção de participantes
        st.markdown("---")
        st.markdown("### 👥 Participantes")
        
        # Carregar participantes existentes
        try:
            import json
            existing_participants = json.loads(report_data.get('participants', '[]'))
        except:
            existing_participants = []
        
        participants_text = '\n'.join(existing_participants)
        participants_input = st.text_area(
            "Participantes (um por linha)",
            value=participants_text,
            height=100,
            help="Digite um participante por linha"
        )
        
        # Seção de decisões
        st.markdown("### ⚖️ Decisões Tomadas")
        decisions = st.text_area(
            "Decisões",
            value=report_data.get('decisions', ''),
            height=150,
            help="Use formatação Markdown para estruturar as decisões"
        )
        
        # Seção de itens de ação
        st.markdown("### 📋 Itens de Ação")
        
        # Carregar itens de ação existentes
        try:
            import json
            existing_action_items = json.loads(report_data.get('action_items', '[]'))
        except:
            existing_action_items = []
        
        # Interface para gerenciar itens de ação
        action_items = manage_action_items(existing_action_items, key="edit_actions", in_form=True)
        
        # Próximos passos
        st.markdown("### 🚀 Próximos Passos")
        next_steps = st.text_area(
            "Próximos Passos",
            value=report_data.get('next_steps', ''),
            height=150,
            help="Use formatação Markdown para estruturar os próximos passos"
        )
        
        # Botões de ação
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            submit_button = st.form_submit_button("💾 Salvar Alterações", type="primary")
        
        with col2:
            preview_button = st.form_submit_button("👁️ Preview")
        
        with col3:
            export_button = st.form_submit_button("📄 Exportar MD")
        
        with col4:
            if st.form_submit_button("🗑️ Excluir", type="secondary"):
                if st.session_state.get('confirm_delete'):
                    delete_meeting_report(report_data['id'])
                    st.success("Relatório excluído com sucesso!")
                    st.session_state.current_view = 'list'
                    st.rerun()
                else:
                    st.session_state.confirm_delete = True
                    st.warning("Clique novamente para confirmar a exclusão")
        
        # Processar ações
        if submit_button:
            # Processar participantes
            participants_list = [p.strip() for p in participants_input.split('\n') if p.strip()]
            
            # Atualizar relatório
            success = update_meeting_report(
                report_data['id'],
                title=title,
                summary=summary,
                content=content,
                participants=json.dumps(participants_list),
                decisions=decisions,
                action_items=json.dumps(action_items),
                next_steps=next_steps,
                status=status
            )
            
            if success:
                st.success("✅ Relatório atualizado com sucesso!")
                st.session_state.current_view = 'view'
                st.session_state.selected_report_id = report_data['id']
                st.rerun()
            else:
                st.error("❌ Erro ao atualizar o relatório")
        
        elif preview_button:
            # Mostrar preview do relatório
            st.markdown("---")
            st.markdown("## 👁️ Preview do Relatório")
            
            # Criar dados temporários para preview
            preview_data = {
                'title': title,
                'summary': summary,
                'content': content,
                'participants': json.dumps([p.strip() for p in participants_input.split('\n') if p.strip()]),
                'decisions': decisions,
                'action_items': json.dumps(action_items),
                'next_steps': next_steps,
                'status': status,
                'event_date': report_data.get('event_date'),
                'event_type': report_data.get('event_type'),
                'created_at': report_data.get('created_at')
            }
            
            from app.components.markdown_viewer import render_markdown_report
            render_markdown_report(preview_data)
        
        elif export_button:
            # Exportar para Markdown
            export_data = {
                'title': title,
                'summary': summary,
                'content': content,
                'participants': json.dumps([p.strip() for p in participants_input.split('\n') if p.strip()]),
                'decisions': decisions,
                'action_items': json.dumps(action_items),
                'next_steps': next_steps,
                'status': status,
                'event_date': report_data.get('event_date'),
                'event_type': report_data.get('event_type'),
                'created_at': report_data.get('created_at')
            }
            
            markdown_content = export_report_to_markdown(export_data)
            
            st.download_button(
                label="📥 Baixar Arquivo Markdown",
                data=markdown_content,
                file_name=f"relatorio_{title.replace(' ', '_').lower()}.md",
                mime="text/markdown"
            )

def render_template_editor():
    """Renderiza o editor de templates"""
    
    template_id = st.session_state.editing_template
    
    st.title("✏️ Editando Template")
    
    # Botão voltar (fora de qualquer formulário)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Voltar sem salvar"):
            del st.session_state.editing_template
            st.rerun()
    
    st.divider()
    
    # Renderizar formulário de template
    render_template_form(template_id)

def render_my_reports():
    """Renderiza a lista de relatórios do usuário"""
    
    st.subheader("📋 Meus Relatórios")
    
    try:
        user_info = get_current_user()
        user_id = get_user_id(user_info['username'])
        
        if not user_id:
            st.error("Erro ao identificar usuário")
            return
        
        # Buscar relatórios do usuário
        reports = get_user_reports(user_id)
        if reports is None:
            st.error("Erro ao buscar relatórios")
            return
        
        if reports:
            # Filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.selectbox(
                    "Status",
                    options=["Todos", "Rascunho", "Publicado", "Arquivado"],
                    key="my_reports_status"
                )
            
            with col2:
                # Buscar tipos de eventos únicos
                event_types = get_unique_event_types_from_reports(user_id)
                type_filter = st.selectbox(
                    "Tipo de Evento",
                    options=["Todos"] + event_types,
                    key="my_reports_type"
                )
            
            with col3:
                sort_by = st.selectbox(
                    "Ordenar por",
                    options=["Mais Recente", "Mais Antigo", "Título A-Z", "Título Z-A"],
                    key="my_reports_sort"
                )
            
            # Aplicar filtros
            try:
                filtered_reports = filter_reports(reports, status_filter, type_filter, sort_by)
            except Exception as e:
                st.error(f"Erro ao filtrar relatórios: {e}")
                filtered_reports = reports  # Usar relatórios sem filtro em caso de erro
            
            # Exibir relatórios
            for i, report in enumerate(filtered_reports):
                try:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            status_emoji = get_status_emoji(report.get('status', 'draft'))
                            st.markdown(f"{status_emoji} **{report.get('title', 'Título não disponível')}**")
                            if report.get('summary'):
                                st.caption(report['summary'][:100] + "..." if len(report['summary']) > 100 else report['summary'])
                        
                        with col2:
                            try:
                                # Tratar conversão de datetime de forma segura
                                event_date_raw = report.get('event_date')
                                if event_date_raw:
                                    if isinstance(event_date_raw, str):
                                        event_date = datetime.fromisoformat(event_date_raw.replace('Z', '')).strftime('%d/%m/%Y')
                                    else:
                                        event_date = event_date_raw.strftime('%d/%m/%Y')
                                    st.markdown(f"📅 {event_date}")
                                else:
                                    st.markdown(f"📅 Data não disponível")
                            except:
                                st.markdown(f"📅 Data não disponível")
                            
                            st.markdown(f"🏷️ {report.get('event_type', 'Tipo não disponível')}")
                            
                            try:
                                created_at = report.get('created_at')
                                if created_at:
                                    created_date = datetime.fromisoformat(created_at).strftime('%d/%m/%Y')
                                    st.caption(f"Criado em {created_date}")
                                else:
                                    st.caption("Data de criação não disponível")
                            except:
                                st.caption("Data de criação não disponível")
                        
                        with col3:
                            report_id = report.get('id')
                            if report_id:
                                # Usar colunas para organizar os botões
                                btn_col1, btn_col2 = st.columns(2)
                                
                                with btn_col1:
                                    if st.button("👁️", key=f"view_{report_id}_{i}", help="Ver relatório"):
                                        st.session_state.viewing_report = report_id
                                        st.rerun()
                                    
                                    if st.button("📥", key=f"export_{report_id}_{i}", help="Exportar"):
                                        try:
                                            markdown_content = export_report_to_markdown(report)
                                            st.download_button(
                                                label="💾 Baixar",
                                                data=markdown_content,
                                                file_name=f"relatorio_{report.get('title', 'relatorio').replace(' ', '_')}.md",
                                                mime="text/markdown",
                                                key=f"download_{report_id}_{i}"
                                            )
                                        except Exception as e:
                                            st.error(f"Erro ao exportar: {e}")
                                
                                with btn_col2:
                                    if st.button("✏️", key=f"edit_{report_id}_{i}", help="Editar relatório"):
                                        st.session_state.editing_report = report_id
                                        st.rerun()
                                    
                                    if st.button("🗑️", key=f"delete_{report_id}_{i}", help="Excluir relatório"):
                                        if st.session_state.get(f"confirm_delete_{report_id}", False):
                                            success = delete_meeting_report(report_id)
                                            if success:
                                                st.success("🗑️ Relatório excluído!")
                                                # Limpar estado de confirmação
                                                if f"confirm_delete_{report_id}" in st.session_state:
                                                    del st.session_state[f"confirm_delete_{report_id}"]
                                                st.rerun()
                                            else:
                                                st.error("❌ Erro ao excluir relatório!")
                                        else:
                                            st.session_state[f"confirm_delete_{report_id}"] = True
                                            st.warning("⚠️ Clique novamente para confirmar a exclusão!")
                                            st.rerun()
                            else:
                                st.error("ID do relatório não disponível")
                        
                        st.divider()
                except Exception as e:
                    st.error(f"Erro ao exibir relatório {i+1}: {e}")
                    continue
        else:
            st.info("📝 Você ainda não criou nenhum relatório. Use a aba 'Novo Relatório' para começar!")
    except Exception as e:
        st.error(f"Erro ao carregar relatórios: {e}")
        st.info("Tente recarregar a página ou verifique se há dados disponíveis.")

def render_new_report():
    """Renderiza o formulário para criar um novo relatório"""
    from app.components.markdown_viewer import render_form_compatible_markdown_editor
    
    st.markdown("### ➕ Criar Novo Relatório")
    
    # Verificar se há evento selecionado do planner
    selected_event_from_planner = st.session_state.get('selected_event_for_report')
    
    # Seleção de evento
    available_events = get_available_events()
    
    if not available_events:
        st.warning("⚠️ Não há eventos disponíveis para criar relatórios.")
        if st.button("🔄 Atualizar Lista"):
            st.rerun()
        return
    
    # Formulário de criação
    with st.form("new_report_form"):
        # Seleção do evento
        event_options = []
        for event in available_events:
            try:
                # Tratar conversão de datetime de forma segura
                start_datetime = event['start_datetime']
                if isinstance(start_datetime, str):
                    event_date = datetime.fromisoformat(start_datetime.replace('Z', '')).strftime('%d/%m/%Y')
                else:
                    event_date = start_datetime.strftime('%d/%m/%Y')
                
                event_options.append((event['id'], f"{event['title']} - {event_date} ({event['event_type']})"))
            except Exception as e:
                # Se houver erro na conversão, usar formato simples
                event_options.append((event['id'], f"{event['title']} ({event['event_type']})"))
        
        if not event_options:
            st.error("❌ Erro ao processar eventos disponíveis")
            return
        
        # Definir evento padrão se selecionado do planner
        default_event_index = 0
        if selected_event_from_planner:
            try:
                default_event_index = next(i for i, event in enumerate(available_events) 
                                         if event['id'] == selected_event_from_planner)
                st.info(f"📅 Evento selecionado do planner: {available_events[default_event_index]['title']}")
                # Limpar a seleção após usar
                if 'selected_event_for_report' in st.session_state:
                    del st.session_state.selected_event_for_report
            except (StopIteration, IndexError):
                st.warning("⚠️ Evento selecionado não encontrado na lista de eventos disponíveis.")
        
        selected_event_id = st.selectbox(
            "Selecione o Evento",
            options=[opt[0] for opt in event_options],
            index=default_event_index,
            format_func=lambda x: next(opt[1] for opt in event_options if opt[0] == x),
            help="Escolha o evento para o qual deseja criar o relatório"
        )
        
        # Verificar se já existe relatório para este evento
        existing_report = get_report_by_event(selected_event_id)
        if existing_report:
            st.warning(f"⚠️ Já existe um relatório para este evento. Deseja editá-lo?")
            if st.form_submit_button("✏️ Editar Relatório Existente"):
                st.session_state.current_view = 'edit'
                st.session_state.selected_report_id = existing_report['id']
                st.rerun()
            return
        
        # Obter detalhes do evento selecionado
        selected_event = next(event for event in available_events if event['id'] == selected_event_id)
        
        # Seleção de template
        st.markdown("---")
        st.markdown("### 📋 Template do Relatório")
        
        templates = get_templates_by_event_type(selected_event['event_type'])
        
        if templates:
            template_options = [('blank', 'Relatório em Branco')] + \
                             [(t['id'], f"{t['name']} - {t['description']}") for t in templates]
            
            selected_template_id = st.selectbox(
                "Escolha um Template",
                options=[opt[0] for opt in template_options],
                format_func=lambda x: next(opt[1] for opt in template_options if opt[0] == x),
                help="Selecione um template para começar ou crie um relatório em branco"
            )
        else:
            selected_template_id = 'blank'
            st.info("📝 Nenhum template disponível para este tipo de evento. Criando relatório em branco.")
        
        # Campos do relatório
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            title = st.text_input(
                "Título do Relatório",
                value=f"Relatório - {selected_event['title']}",
                help="Digite um título descritivo para o relatório"
            )
            
            summary = st.text_area(
                "Resumo Executivo",
                height=100,
                help="Breve resumo dos principais pontos do evento"
            )
        
        with col2:
            status = st.selectbox(
                "Status Inicial",
                options=['draft', 'published'],
                index=0,
                format_func=lambda x: {'draft': '📝 Rascunho', 'published': '✅ Publicado'}[x],
                help="Escolha o status inicial do relatório"
            )
        
        # Gerar conteúdo inicial baseado no template
        initial_content = ""
        if selected_template_id != 'blank':
            template = get_template_by_id(selected_template_id)
            if template:
                initial_content = generate_report_from_template(template, selected_event)
        else:
            initial_content = generate_basic_report_template(selected_event)
        
        # Editor de conteúdo avançado
        st.markdown("---")
        st.markdown("### 📝 Conteúdo do Relatório")
        content = render_form_compatible_markdown_editor(
            initial_content,
            key="new_content"
        )
        
        # Seção de participantes
        st.markdown("---")
        st.markdown("### 👥 Participantes")
        participants_input = st.text_area(
            "Participantes (um por linha)",
            height=100,
            help="Digite um participante por linha"
        )
        
        # Seção de decisões
        st.markdown("### ⚖️ Decisões Tomadas")
        decisions = st.text_area(
            "Decisões",
            height=150,
            help="Use formatação Markdown para estruturar as decisões"
        )
        
        # Seção de itens de ação
        st.markdown("### 📋 Itens de Ação")
        action_items = manage_action_items([], key="new_actions", in_form=True)
        
        # Próximos passos
        st.markdown("### 🚀 Próximos Passos")
        next_steps = st.text_area(
            "Próximos Passos",
            height=150,
            help="Use formatação Markdown para estruturar os próximos passos"
        )
        
        # Botões de ação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submit_button = st.form_submit_button("💾 Criar Relatório", type="primary")
        
        with col2:
            preview_button = st.form_submit_button("👁️ Preview")
        
        with col3:
            draft_button = st.form_submit_button("📝 Salvar como Rascunho")
        
        # Processar ações
        if submit_button or draft_button:
            if draft_button:
                status = 'draft'
            
            # Validações
            if not title.strip():
                st.error("❌ O título é obrigatório")
                return
            
            if not content.strip():
                st.error("❌ O conteúdo é obrigatório")
                return
            
            # Processar participantes
            participants_list = [p.strip() for p in participants_input.split('\n') if p.strip()]
            
            # Criar relatório
            user_info = get_current_user()
            user_id = get_user_id(user_info['username'])
            
            report_id = create_meeting_report(
                event_id=selected_event_id,
                user_id=user_id,
                title=title,
                summary=summary,
                content=content,
                participants=json.dumps(participants_list),
                decisions=decisions,
                action_items=json.dumps(action_items),
                next_steps=next_steps,
                status=status
            )
            
            if report_id:
                st.success("✅ Relatório criado com sucesso!")
                st.session_state.current_view = 'view'
                st.session_state.selected_report_id = report_id
                st.rerun()
            else:
                st.error("❌ Erro ao criar o relatório")
        
        elif preview_button:
            # Mostrar preview do relatório
            st.markdown("---")
            st.markdown("## 👁️ Preview do Relatório")
            
            # Criar dados temporários para preview
            preview_data = {
                'title': title,
                'summary': summary,
                'content': content,
                'participants': json.dumps([p.strip() for p in participants_input.split('\n') if p.strip()]),
                'decisions': decisions,
                'action_items': json.dumps(action_items),
                'next_steps': next_steps,
                'status': status,
                'event_date': selected_event['start_datetime'],
                'event_type': selected_event['event_type'],
                'created_at': datetime.now().isoformat()
            }
            
            from app.components.markdown_viewer import render_markdown_report
            render_markdown_report(preview_data)

def manage_action_items(existing_items, key="action_items", in_form=False):
    """Interface para gerenciar itens de ação"""
    
    # Inicializar no session state se não existir
    session_key = f"{key}_items"
    if session_key not in st.session_state:
        st.session_state[session_key] = existing_items.copy() if existing_items else []
    
    action_items = st.session_state[session_key]
    
    if in_form:
        # Versão simplificada para uso dentro de formulários
        # Interface para adicionar novo item
        new_item_text = st.text_input(
            "Adicionar novo item de ação",
            key=f"{key}_new_text",
            placeholder="Digite um novo item de ação e pressione Enter..."
        )
        
        # Adicionar item automaticamente quando o texto for inserido
        if new_item_text.strip() and new_item_text.strip() not in [item['text'] for item in action_items]:
            action_items.append({
                'text': new_item_text.strip(),
                'completed': False
            })
            st.session_state[session_key] = action_items
        
        # Exibir itens existentes com opção de edição
        if action_items:
            st.markdown("**Itens de Ação:**")
            
            items_to_remove = []
            
            for i, item in enumerate(action_items):
                col1, col2, col3 = st.columns([1, 4, 1])
                
                with col1:
                    completed = st.checkbox(
                        "",
                        value=item.get('completed', False),
                        key=f"{key}_completed_{i}"
                    )
                    action_items[i]['completed'] = completed
                
                with col2:
                    # Permitir edição do texto do item
                    edited_text = st.text_input(
                        "",
                        value=item['text'],
                        key=f"{key}_edit_{i}",
                        label_visibility="collapsed"
                    )
                    action_items[i]['text'] = edited_text
                
                with col3:
                    # Usar checkbox para marcar itens para remoção
                    remove_item = st.checkbox("🗑️", key=f"{key}_remove_{i}", help="Marcar para remover")
                    if remove_item:
                        items_to_remove.append(i)
            
            # Remover itens marcados para remoção
            for i in reversed(items_to_remove):
                action_items.pop(i)
            
            # Atualizar session state
            st.session_state[session_key] = action_items
        else:
            st.info("Nenhum item de ação adicionado ainda.")
    
    else:
        # Versão completa para uso fora de formulários
        # Interface para adicionar novo item
        col1, col2 = st.columns([3, 1])
        
        with col1:
            new_item_text = st.text_input(
                "Novo item de ação",
                key=f"{key}_new_text",
                placeholder="Digite um novo item de ação..."
            )
        
        with col2:
            # Usar checkbox para adicionar item (compatível com formulários)
            add_item = st.checkbox("➕ Adicionar", key=f"{key}_add", help="Marcar para adicionar item")
            
            if add_item and new_item_text.strip():
                # Verificar se o item já não existe
                if new_item_text.strip() not in [item['text'] for item in action_items]:
                    action_items.append({
                        'text': new_item_text.strip(),
                        'completed': False
                    })
                    st.session_state[session_key] = action_items
        
        # Exibir itens existentes
        if action_items:
            st.markdown("**Itens de Ação:**")
            
            items_to_remove = []
            
            for i, item in enumerate(action_items):
                col1, col2, col3 = st.columns([1, 4, 1])
                
                with col1:
                    completed = st.checkbox(
                        "",
                        value=item.get('completed', False),
                        key=f"{key}_completed_{i}"
                    )
                    action_items[i]['completed'] = completed
                
                with col2:
                    # Mostrar texto com formatação baseada no status
                    if completed:
                        st.markdown(f"~~{item['text']}~~")
                    else:
                        st.markdown(item['text'])
                
                with col3:
                    # Usar checkbox para marcar itens para remoção quando fora de formulário
                    remove_item = st.checkbox("🗑️", key=f"{key}_remove_{i}", help="Marcar para remover")
                    if remove_item:
                        items_to_remove.append(i)
            
            # Remover itens marcados para remoção
            for i in reversed(items_to_remove):
                action_items.pop(i)
            
            # Atualizar session state
            st.session_state[session_key] = action_items
        
        else:
            st.info("Nenhum item de ação adicionado ainda.")
    
    return action_items

def render_templates():
    """Renderiza a gestão de templates"""
    
    st.subheader("📄 Templates de Relatórios")
    
    tab1, tab2 = st.tabs(["📋 Templates Disponíveis", "➕ Criar Template"])
    
    with tab1:
        templates = get_all_templates()
        
        if templates:
            for template in templates:
                with st.expander(f"📄 {template['name']}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Descrição:** {template['description'] or 'Sem descrição'}")
                        st.markdown(f"**Tipo de Evento:** {template['event_type'] or 'Geral'}")
                        st.markdown(f"**Padrão:** {'Sim' if template['is_default'] else 'Não'}")
                        
                        # Preview do template
                        if st.button(f"👁️ Visualizar", key=f"preview_template_{template['id']}", help="Visualizar conteúdo do template"):
                            st.code(template['template_content'], language='markdown')
                    
                    with col2:
                        # Organizar botões em colunas para melhor layout
                        btn_col1, btn_col2 = st.columns(2)
                        
                        with btn_col1:
                            if st.button(f"✏️ Editar", key=f"edit_template_{template['id']}", help="Editar template"):
                                st.session_state.editing_template = template['id']
                                st.rerun()
                        
                        with btn_col2:
                            if not template['is_default']:  # Não permitir excluir templates padrão
                                if st.button(f"🗑️ Excluir", key=f"delete_template_{template['id']}", help="Excluir template"):
                                    if delete_template(template['id']):
                                        st.success("Template excluído!")
                                        st.rerun()
        else:
            st.info("📄 Nenhum template disponível.")
    
    with tab2:
        render_template_form()

def render_template_form(template_id=None):
    """Renderiza formulário para criar/editar template"""
    
    # Se estiver editando, carregar dados do template
    if template_id:
        template = get_template_by_id(template_id)
        if not template:
            st.error("Template não encontrado!")
            return
    else:
        template = None
    
    with st.form("template_form"):
        name = st.text_input(
            "Nome do Template *",
            value=template['name'] if template else "",
            placeholder="Ex: Relatório de Reunião Semanal"
        )
        
        description = st.text_area(
            "Descrição",
            value=template['description'] if template else "",
            placeholder="Descrição do template e quando usar..."
        )
        
        event_type = st.selectbox(
            "Tipo de Evento",
            options=["", "Culto", "Reunião", "Celebração", "Estudo Bíblico", "Evento Especial", "Outro"],
            index=0 if not template else (["", "Culto", "Reunião", "Celebração", "Estudo Bíblico", "Evento Especial", "Outro"].index(template['event_type']) if template['event_type'] in ["", "Culto", "Reunião", "Celebração", "Estudo Bíblico", "Evento Especial", "Outro"] else 0),
            help="Deixe em branco para template geral"
        )
        
        template_content = st.text_area(
            "Conteúdo do Template (Markdown) *",
            value=template['template_content'] if template else "",
            height=400,
            help="Use {{variavel}} para campos que serão substituídos automaticamente"
        )
        
        st.markdown("**Variáveis disponíveis:**")
        st.markdown("- `{{title}}` - Título do evento")
        st.markdown("- `{{date}}` - Data do evento")
        st.markdown("- `{{time}}` - Horário do evento")
        st.markdown("- `{{location}}` - Local do evento")
        st.markdown("- `{{leader}}` - Responsável pelo evento")
        st.markdown("- `{{generated_date}}` - Data de geração do relatório")
        
        is_default = st.checkbox(
            "Template Padrão",
            value=template['is_default'] if template else False,
            help="Templates padrão aparecem primeiro na lista"
        )
        
        submitted = st.form_submit_button(
            "💾 Salvar Template" if not template else "💾 Atualizar Template",
            use_container_width=True
        )
        
        if submitted:
            if name and template_content:
                user_info = get_current_user()
                user_id = get_user_id(user_info['username'])
                
                if template:
                    # Atualizar template existente
                    success = update_template(
                        template_id=template['id'],
                        name=name,
                        description=description,
                        template_content=template_content,
                        event_type=event_type if event_type else None,
                        is_default=is_default
                    )
                else:
                    # Criar novo template
                    success = create_template(
                        name=name,
                        description=description,
                        template_content=template_content,
                        event_type=event_type if event_type else None,
                        is_default=is_default,
                        created_by=user_id
                    )
                
                if success:
                    st.success("✅ Template salvo com sucesso!")
                    if 'editing_template' in st.session_state:
                        del st.session_state.editing_template
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar template. Tente novamente.")
            else:
                st.error("⚠️ Preencha todos os campos obrigatórios!")

def render_search_reports():
    """Renderiza a busca de relatórios"""
    
    st.subheader("🔍 Buscar Relatórios")
    
    with st.form("search_reports_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("Buscar por título ou conteúdo", placeholder="Digite sua busca...")
        
        with col2:
            date_range = st.date_input(
                "Período",
                value=[],
                help="Selecione um período para filtrar"
            )
        
        with col3:
            status_filter = st.selectbox(
                "Status",
                options=["Todos", "Rascunho", "Publicado", "Arquivado"]
            )
        
        search_clicked = st.form_submit_button("🔍 Buscar", use_container_width=True)
    
    if search_clicked:
        results = search_reports(search_term, date_range, status_filter)
        
        if results:
            st.markdown(f"**{len(results)} relatório(s) encontrado(s):**")
            
            for report in results:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        status_emoji = get_status_emoji(report['status'])
                        st.markdown(f"{status_emoji} **{report['title']}**")
                        st.caption(f"Por: {report['author_name']}")
                    
                    with col2:
                        try:
                            # Tratar conversão de datetime de forma segura
                            event_date_raw = report['event_date']
                            if isinstance(event_date_raw, str):
                                event_date = datetime.fromisoformat(event_date_raw.replace('Z', '')).strftime('%d/%m/%Y')
                            else:
                                event_date = event_date_raw.strftime('%d/%m/%Y')
                            st.markdown(f"📅 {event_date}")
                        except:
                            st.markdown(f"📅 Data não disponível")
                        st.markdown(f"🏷️ {report['event_type']}")
                    
                    with col3:
                        if st.button("👁️ Ver", key=f"search_view_{report['id']}"):
                            st.session_state.viewing_report = report['id']
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("Nenhum relatório encontrado com os critérios especificados.")

# Funções auxiliares para banco de dados

def get_user_id(username):
    """Busca o ID do usuário pelo username"""
    try:
        query = "SELECT id FROM users WHERE username = ?"
        result = db_manager.fetch_all(query, (username,))
        return result[0]['id'] if result else None
    except:
        return None

def get_user_reports(user_id, limit=10):
    """Busca relatórios do usuário"""
    try:
        query = """
        SELECT mr.id, mr.title, mr.content, mr.summary, mr.participants, 
               mr.decisions, mr.action_items, mr.next_steps, mr.status, 
               mr.created_at, mr.updated_at, mr.created_by, mr.event_id,
               e.title as event_title, e.event_type, e.start_datetime as event_date
        FROM meeting_reports mr
        LEFT JOIN events e ON mr.event_id = e.id
        WHERE mr.created_by = ?
        ORDER BY mr.created_at DESC
        LIMIT ?
        """
        result = db_manager.fetch_all(query, (user_id, limit))
        
        # Garantir que event_date seja sempre definido
        if result:
            for report in result:
                if not report.get('event_date') and report.get('start_datetime'):
                    report['event_date'] = report['start_datetime']
                elif not report.get('event_date'):
                    report['event_date'] = None
        
        return result if result else []
    except Exception as e:
        st.error(f"Erro ao buscar relatórios do usuário: {e}")
        return []

def get_report_by_id(report_id):
    """Busca um relatório específico por ID"""
    try:
        query = """
        SELECT mr.*, e.title as event_title, e.start_datetime, e.location, e.event_type
        FROM meeting_reports mr
        LEFT JOIN events e ON mr.event_id = e.id
        WHERE mr.id = ?
        """
        result = db_manager.fetch_all(query, (report_id,))
        return result[0] if result else None
    except Exception as e:
        st.error(f"Erro ao buscar relatório: {e}")
        return None

def update_meeting_report(report_id, title, content, summary=None, participants=None, 
                         decisions=None, action_items=None, next_steps=None, 
                         status='draft', updated_by=None):
    """Atualiza um relatório existente"""
    try:
        query = """
        UPDATE meeting_reports 
        SET title = ?, content = ?, summary = ?, participants = ?, 
            decisions = ?, action_items = ?, next_steps = ?, status = ?,
            updated_by = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        db_manager.execute_query(query, (title, content, summary, participants, decisions, action_items, 
                             next_steps, status, updated_by, report_id))
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar relatório: {e}")
        return False

def get_available_events():
    """Busca eventos disponíveis para criar relatórios"""
    try:
        query = """
        SELECT * FROM events
        WHERE is_active = 1
        ORDER BY start_datetime DESC
        """
        return db_manager.fetch_all(query)
    except:
        return []

def get_report_by_event(event_id):
    """Verifica se já existe relatório para o evento"""
    try:
        query = "SELECT * FROM meeting_reports WHERE event_id = ?"
        result = db_manager.fetch_all(query, (event_id,))
        return result[0] if result else None
    except:
        return None

def get_templates_by_event_type(event_type):
    """Busca templates por tipo de evento"""
    try:
        query = """
        SELECT * FROM report_templates
        WHERE (event_type = ? OR event_type IS NULL)
        AND is_active = 1
        ORDER BY is_default DESC, name
        """
        return db_manager.fetch_all(query, (event_type,))
    except:
        return []

def get_template_by_id(template_id):
    """Busca template por ID"""
    try:
        query = "SELECT * FROM report_templates WHERE id = ?"
        result = db_manager.fetch_all(query, (template_id,))
        return result[0] if result else None
    except:
        return None

def get_all_templates():
    """Busca todos os templates"""
    try:
        query = """
        SELECT * FROM report_templates
        WHERE is_active = 1
        ORDER BY is_default DESC, name
        """
        return db_manager.fetch_all(query)
    except:
        return []

def create_meeting_report(event_id, user_id, title, summary, content, participants, decisions, action_items, next_steps, status):
    """Cria um novo relatório de reunião"""
    try:
        query = """
        INSERT INTO meeting_reports (
            event_id, title, content, summary, participants, decisions, 
            action_items, next_steps, status, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        result = db_manager.execute_query(query, (
            event_id, title, content, summary, participants, decisions,
            action_items, next_steps, status, user_id
        ))
        
        # Buscar o ID do relatório criado
        query_id = "SELECT last_insert_rowid() as id"
        id_result = db_manager.fetch_all(query_id)
        return id_result[0]['id'] if id_result else None
        
    except Exception as e:
        st.error(f"Erro ao criar relatório: {e}")
        return None

def create_template(name, description, template_content, event_type, is_default, created_by):
    """Cria um novo template"""
    try:
        query = """
        INSERT INTO report_templates (
            name, description, template_content, event_type, is_default, created_by
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        db_manager.execute_query(query, (name, description, template_content, event_type, is_default, created_by))
        return True
    except Exception as e:
        st.error(f"Erro ao criar template: {e}")
        return False

def update_template(template_id, name, description, template_content, event_type, is_default):
    """Atualiza um template existente"""
    try:
        query = """
        UPDATE report_templates 
        SET name = ?, description = ?, template_content = ?, event_type = ?, is_default = ?
        WHERE id = ?
        """
        db_manager.execute_query(query, (name, description, template_content, event_type, is_default, template_id))
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar template: {e}")
        return False

def delete_template(template_id):
    """Exclui um template"""
    try:
        query = "UPDATE report_templates SET is_active = 0 WHERE id = ?"
        db_manager.execute_query(query, (template_id,))
        return True
    except:
        return False

def generate_report_from_template(template, event):
    """Gera conteúdo do relatório a partir do template"""
    content = template['template_content']
    
    # Substituir variáveis
    replacements = {
        '{{title}}': event['title'],
        '{{date}}': datetime.fromisoformat(event['start_datetime']).strftime('%d/%m/%Y'),
        '{{time}}': datetime.fromisoformat(event['start_datetime']).strftime('%H:%M'),
        '{{location}}': event['location'] or 'Não informado',
        '{{leader}}': 'A definir',  # Pode ser expandido para buscar o responsável
        '{{generated_date}}': datetime.now().strftime('%d/%m/%Y às %H:%M')
    }
    
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    
    return content

def generate_basic_report_template(event):
    """Gera template básico para o evento"""
    return f"""# Relatório - {event['title']}

## Informações do Evento
- **Data:** {datetime.fromisoformat(event['start_datetime']).strftime('%d/%m/%Y')}
- **Horário:** {datetime.fromisoformat(event['start_datetime']).strftime('%H:%M')} - {datetime.fromisoformat(event['end_datetime']).strftime('%H:%M')}
- **Local:** {event['location'] or 'Não informado'}
- **Tipo:** {event['event_type']}

## Resumo
[Descreva brevemente o que aconteceu no evento]

## Participação
- **Total de Participantes:** 
- **Principais Presentes:** 

## Principais Pontos Abordados
1. 
2. 
3. 

## Decisões Tomadas
- 
- 

## Próximos Passos
- [ ] 
- [ ] 

## Observações
[Observações adicionais]

---
*Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}*"""

def parse_action_items(action_text):
    """Converte texto de itens de ação em lista estruturada"""
    if not action_text:
        return []
    
    items = []
    lines = action_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and (line.startswith('- [ ]') or line.startswith('- [x]')):
            # Extrair informações do item
            completed = '[x]' in line
            text = line.replace('- [ ]', '').replace('- [x]', '').strip()
            
            items.append({
                'text': text,
                'completed': completed,
                'created_at': datetime.now().isoformat()
            })
    
    return items

def get_status_emoji(status):
    """Retorna emoji para o status do relatório"""
    emojis = {
        'draft': '📝',
        'published': '✅',
        'archived': '📦'
    }
    return emojis.get(status, '📄')

def get_unique_event_types_from_reports(user_id):
    """Busca tipos únicos de eventos dos relatórios do usuário"""
    try:
        query = """
        SELECT DISTINCT e.event_type
        FROM meeting_reports mr
        LEFT JOIN events e ON mr.event_id = e.id
        WHERE mr.created_by = ? AND e.event_type IS NOT NULL
        ORDER BY e.event_type
        """
        result = db_manager.fetch_all(query, (user_id,))
        return [row['event_type'] for row in result if row['event_type']]
    except:
        return []

def filter_reports(reports, status_filter, type_filter, sort_by):
    """Aplica filtros aos relatórios"""
    try:
        filtered = reports
        
        # Filtro por status
        if status_filter != "Todos":
            status_map = {"Rascunho": "draft", "Publicado": "published", "Arquivado": "archived"}
            filtered = [r for r in filtered if r.get('status') == status_map[status_filter]]
        
        # Filtro por tipo
        if type_filter != "Todos":
            filtered = [r for r in filtered if r.get('event_type') == type_filter]
        
        # Ordenação
        if sort_by == "Mais Antigo":
            filtered = sorted(filtered, key=lambda x: x.get('created_at', ''))
        elif sort_by == "Título A-Z":
            filtered = sorted(filtered, key=lambda x: x.get('title', ''))
        elif sort_by == "Título Z-A":
            filtered = sorted(filtered, key=lambda x: x.get('title', ''), reverse=True)
        # "Mais Recente" já é a ordenação padrão
        
        return filtered
    except Exception as e:
        st.error(f"Erro ao filtrar relatórios: {e}")
        return reports

def search_reports(search_term, date_range, status_filter):
    """Busca relatórios com filtros"""
    try:
        query = """
        SELECT mr.*, e.title as event_title, e.event_type, e.start_datetime as event_date,
               u.full_name as author_name
        FROM meeting_reports mr
        LEFT JOIN events e ON mr.event_id = e.id
        LEFT JOIN users u ON mr.created_by = u.id
        WHERE 1=1
        """
        params = []
        
        # Filtro por termo de busca
        if search_term:
            query += " AND (mr.title LIKE ? OR mr.content LIKE ? OR mr.summary LIKE ?)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        # Filtro por data
        if date_range and len(date_range) == 2:
            query += " AND date(e.start_datetime) BETWEEN ? AND ?"
            params.extend([date_range[0].isoformat(), date_range[1].isoformat()])
        
        # Filtro por status
        if status_filter != "Todos":
            status_map = {"Rascunho": "draft", "Publicado": "published", "Arquivado": "archived"}
            query += " AND mr.status = ?"
            params.append(status_map[status_filter])
        
        query += " ORDER BY mr.created_at DESC"
        
        return db_manager.fetch_all(query, params)
    except:
        return []

def delete_meeting_report(report_id):
    """Exclui um relatório de reunião"""
    try:
        query = "DELETE FROM meeting_reports WHERE id = ?"
        db_manager.execute_query(query, (report_id,))
        return True
    except Exception as e:
        st.error(f"Erro ao excluir relatório: {e}")
        return False