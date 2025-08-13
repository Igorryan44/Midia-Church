import streamlit as st
import json
import requests
from datetime import datetime, timedelta
from app.database.local_connection import db_manager
from app.utils.auth import get_current_user
from app.utils.whatsapp_api_service import whatsapp_api_service
import os
import re
import random

# Configuração da API Groq
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Usar instância global do serviço WhatsApp

def render_ai_assistant():
    """Renderiza o módulo do assistente IA"""
    
    st.title("🤖 Assistente IA")
    
    # Verificar se a API key está configurada
    if not GROQ_API_KEY:
        st.error("⚠️ API Key do Groq não configurada. Configure a variável GROQ_API_KEY no arquivo .env")
        return
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Chat", 
        "📱 Mensagens WhatsApp", 
        "🎯 Templates IA", 
        "📚 Base de Conhecimento", 
        "📊 Histórico"
    ])
    
    with tab1:
        render_chat_interface()
    
    with tab2:
        render_whatsapp_ai_integration()
    
    with tab3:
        render_ai_templates()
    
    with tab4:
        render_knowledge_base()
    
    with tab5:
        render_conversation_history()

def render_chat_interface():
    """Renderiza a interface de chat com o assistente IA"""
    
    st.subheader("💬 Converse com o Assistente")
    
    # Inicializar histórico da conversa na sessão
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Container para o histórico de mensagens
    chat_container = st.container()
    
    with chat_container:
        # Exibir histórico de mensagens
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])
    
    # Input para nova mensagem
    user_input = st.chat_input("Digite sua pergunta...")
    
    if user_input:
        # Adicionar mensagem do usuário ao histórico
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Exibir mensagem do usuário
        with st.chat_message("user"):
            st.write(user_input)
        
        # Gerar resposta do assistente
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                response = generate_ai_response(user_input, st.session_state.chat_history)
                st.write(response)
        
        # Adicionar resposta do assistente ao histórico
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Salvar conversa no banco de dados
        save_conversation(user_input, response)
        
        # Rerun para atualizar a interface
        st.rerun()
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Limpar Chat"):
            st.session_state.chat_history = []
            st.rerun()
    
    with col2:
        if st.button("💾 Salvar Conversa"):
            if st.session_state.chat_history:
                save_full_conversation(st.session_state.chat_history)
                st.success("Conversa salva com sucesso!")
    
    with col3:
        if st.button("📋 Sugestões"):
            show_quick_suggestions()

def render_knowledge_base():
    """Renderiza a base de conhecimento do assistente"""
    
    st.subheader("📚 Base de Conhecimento")
    
    # Informações sobre a igreja que o assistente pode usar
    st.markdown("""
    ### 🏛️ Informações da Igreja
    
    O assistente IA tem acesso às seguintes informações para ajudar você:
    
    #### 📅 **Eventos e Calendário**
    - Próximos cultos e eventos
    - Horários de funcionamento
    - Programação especial
    
    #### 👥 **Membros e Presença**
    - Estatísticas de frequência
    - Informações de contato (quando autorizado)
    - Grupos e ministérios
    
    #### 📱 **Comunicação**
    - Anúncios recentes
    - Notícias da igreja
    - Avisos importantes
    
    #### 🎵 **Conteúdo e Mídia**
    - Sermões gravados
    - Músicas e hinos
    - Material de estudo
    """)
    
    st.divider()
    
    # Perguntas frequentes
    st.subheader("❓ Perguntas Frequentes")
    
    faqs = [
        {
            "pergunta": "Quais são os horários dos cultos?",
            "resposta": "Os cultos acontecem aos domingos às 9h e 19h, e às quartas-feiras às 20h."
        },
        {
            "pergunta": "Como posso me tornar membro da igreja?",
            "resposta": "Para se tornar membro, participe do curso de novos membros que acontece mensalmente."
        },
        {
            "pergunta": "Onde posso encontrar os sermões gravados?",
            "resposta": "Os sermões estão disponíveis na seção de Gerenciamento de Conteúdo do sistema."
        },
        {
            "pergunta": "Como faço para participar de um ministério?",
            "resposta": "Entre em contato com a liderança através do sistema de comunicação interna."
        }
    ]
    
    for faq in faqs:
        with st.expander(f"❓ {faq['pergunta']}"):
            st.write(faq['resposta'])
            if st.button(f"💬 Perguntar ao IA", key=f"faq_{faq['pergunta'][:20]}"):
                # Adicionar pergunta ao chat
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = []
                
                st.session_state.chat_history.append({"role": "user", "content": faq['pergunta']})
                response = generate_ai_response(faq['pergunta'], st.session_state.chat_history)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                
                st.success("Pergunta adicionada ao chat!")

def render_conversation_history():
    """Renderiza o histórico de conversas"""
    
    st.subheader("📊 Histórico de Conversas")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        date_filter = st.date_input("Filtrar por data")
    
    with col2:
        search_term = st.text_input("🔍 Buscar nas conversas")
    
    # Buscar conversas
    conversations = get_conversation_history(date_filter, search_term)
    
    if conversations:
        # Estatísticas
        st.markdown("### 📈 Estatísticas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💬 Total de Conversas", len(conversations))
        
        with col2:
            total_messages = sum(len(conv['messages']) for conv in conversations if conv['messages'])
            st.metric("📝 Total de Mensagens", total_messages)
        
        with col3:
            avg_messages = total_messages / len(conversations) if conversations else 0
            st.metric("📊 Média por Conversa", f"{avg_messages:.1f}")
        
        st.divider()
        
        # Lista de conversas
        for conv in conversations:
            with st.expander(f"💬 Conversa de {conv['created_at']} - {conv['user_question'][:50]}..."):
                st.markdown(f"**👤 Usuário:** {conv['user_question']}")
                st.markdown(f"**🤖 Assistente:** {conv['ai_response']}")
                st.caption(f"📅 {conv['created_at']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Repetir Pergunta", key=f"repeat_{conv['id']}"):
                        # Adicionar ao chat atual
                        if "chat_history" not in st.session_state:
                            st.session_state.chat_history = []
                        
                        st.session_state.chat_history.append({"role": "user", "content": conv['user_question']})
                        response = generate_ai_response(conv['user_question'], st.session_state.chat_history)
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        
                        st.success("Pergunta adicionada ao chat atual!")
                
                with col2:
                    if st.button("🗑️ Excluir", key=f"delete_{conv['id']}"):
                        delete_conversation(conv['id'])
                        st.success("Conversa excluída!")
                        st.rerun()
    else:
        st.info("Nenhuma conversa encontrada.")

def render_whatsapp_ai_integration():
    """Renderiza a integração de IA com WhatsApp"""
    
    st.subheader("📱 Geração de Mensagens WhatsApp com IA")
    
    # Verificar conexão WhatsApp
    status_info = whatsapp_api_service.get_connection_status()
    
    if not status_info["connected"]:
        st.warning("⚠️ WhatsApp não está conectado. Conecte-se primeiro na aba WhatsApp.")
        if st.button("🔗 Ir para WhatsApp"):
            st.switch_page("WhatsApp")
        return
    
    st.success("✅ WhatsApp conectado - Pronto para enviar mensagens!")
    
    # Seleção do tipo de mensagem
    message_type = st.selectbox(
        "🎯 Tipo de Mensagem:",
        [
            "Convite para Evento",
            "Mensagem de Boas-vindas",
            "Lembrete de Culto",
            "Aniversário",
            "Oração/Intercessão",
            "Anúncio Geral",
            "Mensagem Personalizada"
        ]
    )
    
    # Configurações específicas por tipo
    if message_type == "Convite para Evento":
        render_event_invitation_generator()
    elif message_type == "Mensagem de Boas-vindas":
        render_welcome_message_generator()
    elif message_type == "Lembrete de Culto":
        render_service_reminder_generator()
    elif message_type == "Aniversário":
        render_birthday_message_generator()
    elif message_type == "Oração/Intercessão":
        render_prayer_message_generator()
    elif message_type == "Anúncio Geral":
        render_general_announcement_generator()
    else:
        render_custom_message_generator()

def render_ai_templates():
    """Renderiza os templates de IA"""
    
    st.subheader("🎯 Templates de IA para Mensagens")
    
    # Gerenciar templates
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📝 Templates Disponíveis")
        
        # Buscar templates existentes
        templates = get_ai_templates()
        
        if templates:
            for template in templates:
                with st.expander(f"📋 {template['name']} - {template['category']}"):
                    st.markdown(f"**Descrição:** {template['description']}")
                    st.code(template['template_text'], language="text")
                    
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        if st.button("✏️ Editar", key=f"edit_{template['id']}"):
                            st.session_state[f"editing_template_{template['id']}"] = True
                    
                    with col_b:
                        if st.button("🚀 Usar", key=f"use_{template['id']}"):
                            st.session_state["selected_template"] = template
                            st.success("Template selecionado!")
                    
                    with col_c:
                        if st.button("🗑️ Excluir", key=f"delete_{template['id']}"):
                            delete_ai_template(template['id'])
                            st.success("Template excluído!")
                            st.rerun()
        else:
            st.info("Nenhum template encontrado. Crie seu primeiro template!")
    
    with col2:
        st.markdown("### ➕ Criar Novo Template")
        
        with st.form("new_template_form"):
            template_name = st.text_input("Nome do Template:")
            template_category = st.selectbox(
                "Categoria:",
                ["Eventos", "Boas-vindas", "Lembretes", "Aniversários", "Orações", "Anúncios", "Outros"]
            )
            template_description = st.text_area("Descrição:", height=100)
            template_text = st.text_area(
                "Template (use {variavel} para campos dinâmicos):",
                height=200,
                placeholder="Exemplo: Olá {nome}, você está convidado para {evento} no dia {data}..."
            )
            
            if st.form_submit_button("💾 Salvar Template"):
                if template_name and template_text:
                    save_ai_template(template_name, template_category, template_description, template_text)
                    st.success("Template salvo com sucesso!")
                    st.rerun()
                else:
                    st.error("Preencha pelo menos o nome e o texto do template!")

def render_event_invitation_generator():
    """Gera convites para eventos usando IA"""
    
    st.markdown("### 🎉 Gerador de Convites para Eventos")
    
    # Buscar eventos próximos
    events = get_upcoming_events()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if events:
            event_options = {f"{e['title']} - {e['start_datetime']}": e for e in events}
            selected_event_key = st.selectbox("Selecionar Evento:", list(event_options.keys()))
            selected_event = event_options[selected_event_key]
        else:
            st.info("Nenhum evento próximo encontrado.")
            selected_event = None
        
        tone = st.selectbox(
            "Tom da Mensagem:",
            ["Formal", "Amigável", "Entusiasmado", "Carinhoso", "Solene"]
        )
        
        include_details = st.checkbox("Incluir detalhes do evento", value=True)
        include_contact = st.checkbox("Incluir informações de contato", value=True)
    
    with col2:
        if selected_event:
            st.markdown("**Preview do Evento:**")
            st.write(f"**Título:** {selected_event['title']}")
            st.write(f"**Data:** {selected_event['start_datetime']}")
            st.write(f"**Local:** {selected_event.get('location', 'A definir')}")
            st.write(f"**Descrição:** {selected_event.get('description', 'Sem descrição')}")
    
    if st.button("🤖 Gerar Convite com IA") and selected_event:
        with st.spinner("Gerando convite personalizado..."):
            invitation = generate_event_invitation_ai(selected_event, tone, include_details, include_contact)
            
            st.markdown("### 📝 Convite Gerado:")
            st.text_area("Mensagem:", value=invitation, height=200, key="generated_invitation")
            
            # Opções de envio
            st.markdown("### 📤 Enviar Convite")
            
            # Seleção de contatos
            contacts = whatsapp_service.get_contacts()
            if contacts:
                contact_options = {f"{c['name']} ({c['phone']})": c for c in contacts}
                selected_contacts = st.multiselect(
                    "Selecionar Contatos:",
                    options=list(contact_options.keys())
                )
                
                if st.button("📱 Enviar via WhatsApp") and selected_contacts:
                    send_ai_generated_messages(invitation, selected_contacts, contact_options)

def render_welcome_message_generator():
    """Gera mensagens de boas-vindas usando IA"""
    
    st.markdown("### 👋 Gerador de Mensagens de Boas-vindas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        visitor_name = st.text_input("Nome do Visitante:")
        visit_context = st.selectbox(
            "Contexto da Visita:",
            ["Primeira visita", "Retornando", "Convidado por membro", "Evento especial"]
        )
        
        message_style = st.selectbox(
            "Estilo da Mensagem:",
            ["Calorosa", "Formal", "Jovem", "Familiar"]
        )
        
        include_next_steps = st.checkbox("Incluir próximos passos", value=True)
        include_contact_info = st.checkbox("Incluir informações de contato", value=True)
    
    with col2:
        st.markdown("**Informações Adicionais:**")
        special_notes = st.text_area(
            "Observações especiais:",
            placeholder="Ex: Veio com a família, interessado em ministério infantil..."
        )
    
    if st.button("🤖 Gerar Mensagem de Boas-vindas"):
        if visitor_name:
            with st.spinner("Gerando mensagem personalizada..."):
                welcome_msg = generate_welcome_message_ai(
                    visitor_name, visit_context, message_style, 
                    include_next_steps, include_contact_info, special_notes
                )
                
                st.markdown("### 📝 Mensagem Gerada:")
                st.text_area("Mensagem:", value=welcome_msg, height=200, key="generated_welcome")
                
                # Opção de envio
                phone_number = st.text_input("Número do WhatsApp:", placeholder="+55 11 99999-9999")
                
                if st.button("📱 Enviar via WhatsApp") and phone_number:
                    success, message = whatsapp_service.send_message_selenium(phone_number, welcome_msg)
                    if success:
                        st.success("✅ Mensagem enviada com sucesso!")
                    else:
                        st.error(f"❌ Erro ao enviar: {message}")
        else:
            st.warning("Por favor, insira o nome do visitante.")

def render_service_reminder_generator():
    """Gera lembretes de culto usando IA"""
    
    st.markdown("### ⛪ Gerador de Lembretes de Culto")
    
    col1, col2 = st.columns(2)
    
    with col1:
        service_type = st.selectbox(
            "Tipo de Culto:",
            ["Domingo Manhã", "Domingo Noite", "Quarta-feira", "Culto Jovem", "Evento Especial"]
        )
        
        reminder_time = st.selectbox(
            "Quando Lembrar:",
            ["1 hora antes", "2 horas antes", "No dia pela manhã", "Dia anterior"]
        )
        
        message_tone = st.selectbox(
            "Tom da Mensagem:",
            ["Motivacional", "Carinhoso", "Informativo", "Urgente"]
        )
    
    with col2:
        include_theme = st.checkbox("Incluir tema do culto", value=True)
        include_special_guest = st.checkbox("Incluir pregador/convidado especial")
        
        if include_theme:
            service_theme = st.text_input("Tema do Culto:")
        
        if include_special_guest:
            special_guest = st.text_input("Pregador/Convidado:")
    
    if st.button("🤖 Gerar Lembrete"):
        with st.spinner("Gerando lembrete personalizado..."):
            reminder = generate_service_reminder_ai(
                service_type, reminder_time, message_tone,
                service_theme if include_theme else None,
                special_guest if include_special_guest else None
            )
            
            st.markdown("### 📝 Lembrete Gerado:")
            st.text_area("Mensagem:", value=reminder, height=200, key="generated_reminder")
            
            # Envio em massa
            st.markdown("### 📤 Envio em Massa")
            
            contacts = whatsapp_service.get_contacts()
            if contacts:
                contact_options = {f"{c['name']} ({c['phone']})": c for c in contacts}
                selected_contacts = st.multiselect(
                    "Selecionar Contatos:",
                    options=list(contact_options.keys())
                )
                
                if st.button("📱 Enviar Lembretes") and selected_contacts:
                    send_ai_generated_messages(reminder, selected_contacts, contact_options)

def render_birthday_message_generator():
    """Gera mensagens de aniversário usando IA"""
    
    st.markdown("### 🎂 Gerador de Mensagens de Aniversário")
    
    col1, col2 = st.columns(2)
    
    with col1:
        birthday_person = st.text_input("Nome do Aniversariante:")
        relationship = st.selectbox(
            "Relacionamento:",
            ["Membro", "Pastor", "Líder", "Visitante", "Criança", "Jovem", "Idoso"]
        )
        
        message_style = st.selectbox(
            "Estilo da Mensagem:",
            ["Alegre", "Carinhosa", "Respeitosa", "Divertida", "Espiritual"]
        )
    
    with col2:
        include_bible_verse = st.checkbox("Incluir versículo bíblico", value=True)
        include_prayer = st.checkbox("Incluir oração")
        
        special_notes = st.text_area(
            "Observações especiais:",
            placeholder="Ex: Aniversário especial, conquistas recentes..."
        )
    
    if st.button("🤖 Gerar Mensagem de Aniversário"):
        if birthday_person:
            with st.spinner("Gerando mensagem personalizada..."):
                birthday_msg = generate_birthday_message_ai(
                    birthday_person, relationship, message_style,
                    include_bible_verse, include_prayer, special_notes
                )
                
                st.markdown("### 📝 Mensagem Gerada:")
                st.text_area("Mensagem:", value=birthday_msg, height=200, key="generated_birthday")
                
                # Opção de envio
                phone_number = st.text_input("Número do WhatsApp:", placeholder="+55 11 99999-9999")
                
                if st.button("📱 Enviar via WhatsApp") and phone_number:
                    success, message = whatsapp_service.send_message_selenium(phone_number, birthday_msg)
                    if success:
                        st.success("✅ Mensagem enviada com sucesso!")
                    else:
                        st.error(f"❌ Erro ao enviar: {message}")
        else:
            st.warning("Por favor, insira o nome do aniversariante.")

def render_prayer_message_generator():
    """Gera mensagens de oração usando IA"""
    
    st.markdown("### 🙏 Gerador de Mensagens de Oração")
    
    col1, col2 = st.columns(2)
    
    with col1:
        prayer_type = st.selectbox(
            "Tipo de Oração:",
            ["Intercessão", "Gratidão", "Pedido", "Cura", "Proteção", "Sabedoria", "Família"]
        )
        
        urgency = st.selectbox(
            "Urgência:",
            ["Normal", "Urgente", "Muito Urgente"]
        )
    
    with col2:
        prayer_request = st.text_area(
            "Pedido de Oração:",
            height=100,
            placeholder="Descreva o motivo da oração..."
        )
        
        include_bible_verse = st.checkbox("Incluir versículo bíblico", value=True)
    
    if st.button("🤖 Gerar Mensagem de Oração"):
        if prayer_request:
            with st.spinner("Gerando mensagem de oração..."):
                prayer_msg = generate_prayer_message_ai(
                    prayer_type, urgency, prayer_request, include_bible_verse
                )
                
                st.markdown("### 📝 Mensagem Gerada:")
                st.text_area("Mensagem:", value=prayer_msg, height=200, key="generated_prayer")
                
                # Envio para grupo de oração
                st.markdown("### 📤 Enviar para Grupo de Oração")
                
                contacts = whatsapp_api_service.get_contacts()
                if contacts:
                    contact_options = {f"{c['name']} ({c['phone']})": c for c in contacts}
                    selected_contacts = st.multiselect(
                        "Selecionar Membros do Grupo de Oração:",
                        options=list(contact_options.keys())
                    )
                    
                    if st.button("📱 Enviar Pedido de Oração") and selected_contacts:
                        send_ai_generated_messages(prayer_msg, selected_contacts, contact_options)
        else:
            st.warning("Por favor, descreva o pedido de oração.")

def render_general_announcement_generator():
    """Gera anúncios gerais usando IA"""
    
    st.markdown("### 📢 Gerador de Anúncios Gerais")
    
    col1, col2 = st.columns(2)
    
    with col1:
        announcement_type = st.selectbox(
            "Tipo de Anúncio:",
            ["Informativo", "Urgente", "Celebração", "Mudança", "Novo Ministério", "Evento"]
        )
        
        target_audience = st.selectbox(
            "Público-alvo:",
            ["Todos os Membros", "Líderes", "Jovens", "Crianças", "Famílias", "Específico"]
        )
    
    with col2:
        announcement_content = st.text_area(
            "Conteúdo do Anúncio:",
            height=150,
            placeholder="Descreva o que precisa ser anunciado..."
        )
        
        include_call_to_action = st.checkbox("Incluir chamada para ação", value=True)
    
    if st.button("🤖 Gerar Anúncio"):
        if announcement_content:
            with st.spinner("Gerando anúncio personalizado..."):
                announcement = generate_announcement_ai(
                    announcement_type, target_audience, announcement_content, include_call_to_action
                )
                
                st.markdown("### 📝 Anúncio Gerado:")
                st.text_area("Mensagem:", value=announcement, height=200, key="generated_announcement")
                
                # Envio em massa
                st.markdown("### 📤 Envio em Massa")
                
                contacts = whatsapp_api_service.get_contacts()
                if contacts:
                    contact_options = {f"{c['name']} ({c['phone']})": c for c in contacts}
                    selected_contacts = st.multiselect(
                        "Selecionar Contatos:",
                        options=list(contact_options.keys())
                    )
                    
                    if st.button("📱 Enviar Anúncio") and selected_contacts:
                        send_ai_generated_messages(announcement, selected_contacts, contact_options)
        else:
            st.warning("Por favor, descreva o conteúdo do anúncio.")

def render_custom_message_generator():
    """Gera mensagens personalizadas usando IA"""
    
    st.markdown("### ✨ Gerador de Mensagens Personalizadas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        message_purpose = st.text_input(
            "Propósito da Mensagem:",
            placeholder="Ex: Convite especial, agradecimento, motivação..."
        )
        
        target_person = st.text_input(
            "Destinatário:",
            placeholder="Nome da pessoa ou grupo"
        )
        
        message_tone = st.selectbox(
            "Tom da Mensagem:",
            ["Formal", "Informal", "Carinhoso", "Motivacional", "Agradecimento", "Convite"]
        )
    
    with col2:
        custom_content = st.text_area(
            "Conteúdo/Contexto:",
            height=150,
            placeholder="Descreva o que você quer comunicar..."
        )
        
        include_bible_reference = st.checkbox("Incluir referência bíblica")
        include_church_signature = st.checkbox("Incluir assinatura da igreja", value=True)
    
    if st.button("🤖 Gerar Mensagem Personalizada"):
        if message_purpose and custom_content:
            with st.spinner("Gerando mensagem personalizada..."):
                custom_msg = generate_custom_message_ai(
                    message_purpose, target_person, message_tone, custom_content,
                    include_bible_reference, include_church_signature
                )
                
                st.markdown("### 📝 Mensagem Gerada:")
                st.text_area("Mensagem:", value=custom_msg, height=200, key="generated_custom")
                
                # Opção de envio
                phone_number = st.text_input("Número do WhatsApp:", placeholder="+55 11 99999-9999")
                
                if st.button("📱 Enviar via WhatsApp") and phone_number:
                    success, message = whatsapp_api_service.send_message(phone_number, custom_msg)
                    if success:
                        st.success("✅ Mensagem enviada com sucesso!")
                    else:
                        st.error(f"❌ Erro ao enviar: {message}")
        else:
            st.warning("Por favor, preencha o propósito e o conteúdo da mensagem.")

def generate_ai_response(user_input, chat_history):
    """Gera resposta usando a API do Groq"""
    
    try:
        if not GROQ_API_KEY:
            return "⚠️ API Key do Groq não configurada. Configure a variável GROQ_API_KEY no arquivo .env"
        
        # Contexto da igreja
        church_context = get_church_context()
        
        # Preparar contexto para a IA
        system_prompt = f"""
        Você é um assistente virtual de uma igreja cristã. Seu papel é ajudar membros e visitantes com informações sobre:
        - Eventos e cultos
        - Ministérios e atividades
        - Dúvidas sobre a fé cristã
        - Orientações pastorais básicas
        
        Contexto atual da igreja:
        - Eventos próximos: {church_context.get('events', 'Nenhum evento próximo')}
        - Anúncios: {church_context.get('announcements', 'Nenhum anúncio')}
        - Estatísticas: {church_context.get('stats', 'Sem estatísticas')}
        
        Responda de forma calorosa, acolhedora e sempre com base bíblica quando apropriado.
        Mantenha as respostas concisas mas informativas.
        """
        
        # Preparar histórico de conversa
        messages = [{"role": "system", "content": system_prompt}]
        
        # Adicionar histórico recente (últimas 5 mensagens)
        for msg in chat_history[-5:]:
            messages.append({"role": "user", "content": msg["message"]})
            messages.append({"role": "assistant", "content": msg["response"]})
        
        # Adicionar mensagem atual
        messages.append({"role": "user", "content": user_input})
        
        # Fazer chamada para a API do Groq
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama3-8b-8192",  # Modelo do Groq
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            return ai_response
        else:
            # Fallback para resposta simulada
            return generate_fallback_response(user_input, church_context)
            
    except Exception as e:
        st.error(f"Erro na API do Groq: {str(e)}")
        return generate_contextual_response(user_input, church_context)

def generate_contextual_response(user_input, context):
    """Gera uma resposta contextual baseada na pergunta do usuário"""
    
    user_input_lower = user_input.lower()
    
    # Respostas sobre horários
    if any(word in user_input_lower for word in ['horário', 'hora', 'quando', 'culto']):
        return """
        📅 **Horários dos Cultos:**
        
        • **Domingos:** 9h00 (Manhã) e 19h00 (Noite)
        • **Quartas-feiras:** 20h00 (Culto de Oração)
        • **Sábados:** 19h30 (Culto Jovem - 1º sábado do mês)
        
        Todos são bem-vindos! 🙏
        """
    
    # Respostas sobre eventos
    elif any(word in user_input_lower for word in ['evento', 'programação', 'atividade']):
        return """
        🎉 **Próximos Eventos:**
        
        Você pode consultar todos os eventos na seção **Planner** do sistema.
        Lá você encontrará:
        • Cultos especiais
        • Conferências
        • Atividades para crianças e jovens
        • Reuniões de ministérios
        
        Para mais detalhes, acesse o calendário! 📅
        """
    
    # Respostas sobre contato
    elif any(word in user_input_lower for word in ['contato', 'telefone', 'endereço', 'localização']):
        return """
        📞 **Informações de Contato:**
        
        Para informações de contato e localização, consulte:
        • A seção de **Comunicação Interna** para anúncios
        • Entre em contato com a liderança através do sistema
        • Consulte os dados na sua área de membro
        
        A liderança está sempre disponível para ajudar! 🤝
        """
    
    # Respostas sobre membros
    elif any(word in user_input_lower for word in ['membro', 'cadastro', 'inscrição']):
        return """
        👥 **Informações sobre Membros:**
        
        Para se tornar membro ou atualizar seus dados:
        • Participe do curso de novos membros
        • Entre em contato com a secretaria
        • Consulte a seção de **Comunicação** para anúncios sobre inscrições
        
        Sua participação é muito importante para nós! ❤️
        """
    
    # Respostas sobre conteúdo
    elif any(word in user_input_lower for word in ['sermão', 'pregação', 'música', 'vídeo', 'áudio']):
        return """
        🎵 **Conteúdo e Mídia:**
        
        Todo o conteúdo está disponível na seção **Gerenciamento de Conteúdo**:
        • Sermões gravados
        • Músicas e hinos
        • Estudos bíblicos
        • Fotos de eventos
        
        Acesse e aproveite todo o material disponível! 📚
        """
    
    # Resposta padrão
    else:
        return """
        Olá! 👋 Sou o assistente IA da igreja e estou aqui para ajudar!
        
        Posso ajudar você com:
        • 📅 Horários e eventos
        • 👥 Informações sobre membros
        • 🎵 Conteúdo e mídia
        • 📞 Contatos e localização
        • 💬 Comunicação interna
        
        Faça sua pergunta e eu farei o meu melhor para ajudar! 🙏
        """

def get_church_context():
    """Busca informações da igreja para contexto do IA"""
    
    try:
        # Próximos eventos
        events_query = """
        SELECT title, event_date, event_type 
        FROM events 
        WHERE event_date >= date('now') 
        AND is_active = 1 
        ORDER BY event_date 
        LIMIT 5
        """
        events = db_manager.fetch_all(events_query)
        
        # Anúncios recentes
        announcements_query = """
        SELECT title, content 
        FROM posts 
        WHERE post_type = 'announcement' 
        AND is_active = 1 
        ORDER BY created_at DESC 
        LIMIT 3
        """
        announcements = db_manager.fetch_all(announcements_query)
        
        # Estatísticas gerais
        stats_query = """
        SELECT 
            (SELECT COUNT(*) FROM users WHERE is_active = 1) as total_members,
            (SELECT COUNT(*) FROM events WHERE event_date >= date('now') AND is_active = 1) as upcoming_events,
            (SELECT COUNT(*) FROM media_content WHERE is_active = 1) as total_content
        """
        stats = db_manager.fetch_all(stats_query)[0]
        
        context = f"""
        INFORMAÇÕES DA IGREJA:
        
        Estatísticas:
        - Total de membros: {stats['total_members']}
        - Próximos eventos: {stats['upcoming_events']}
        - Conteúdo disponível: {stats['total_content']}
        
        Próximos eventos:
        {chr(10).join([f"- {event['title']} ({event.get('event_date', 'Data não disponível')})" for event in events])}
        
        Anúncios recentes:
        {chr(10).join([f"- {ann['title']}" for ann in announcements])}
        """
        
        return context
        
    except:
        return "Informações da igreja não disponíveis no momento."

def save_conversation(user_question, ai_response):
    """Salva a conversa no banco de dados"""
    
    try:
        user_info = get_current_user()
        user_id = get_user_id(user_info['username'])
        
        query = """
        INSERT INTO ai_conversations (user_id, user_question, ai_response)
        VALUES (?, ?, ?)
        """
        params = (user_id, user_question, ai_response)
        db_manager.execute_query(query, params)
        
    except Exception as e:
        st.error(f"Erro ao salvar conversa: {e}")

def save_full_conversation(chat_history):
    """Salva uma conversa completa"""
    
    try:
        user_info = get_current_user()
        user_id = get_user_id(user_info['username'])
        
        # Salvar cada par pergunta-resposta
        for i in range(0, len(chat_history), 2):
            if i + 1 < len(chat_history):
                user_msg = chat_history[i]['content']
                ai_msg = chat_history[i + 1]['content']
                
                query = """
                INSERT INTO ai_conversations (user_id, user_question, ai_response)
                VALUES (?, ?, ?)
                """
                params = (user_id, user_msg, ai_msg)
                db_manager.execute_query(query, params)
        
    except Exception as e:
        st.error(f"Erro ao salvar conversa completa: {e}")

def get_conversation_history(date_filter=None, search_term=None):
    """Busca histórico de conversas"""
    
    try:
        user_info = get_current_user()
        user_id = get_user_id(user_info['username'])
        
        query = """
        SELECT * FROM ai_conversations 
        WHERE user_id = ?
        """
        params = [user_id]
        
        if date_filter:
            query += " AND date(created_at) = ?"
            params.append(str(date_filter))
        
        if search_term:
            query += " AND (user_question LIKE ? OR ai_response LIKE ?)"
            search_param = f"%{search_term}%"
            params.extend([search_param, search_param])
        
        query += " ORDER BY created_at DESC"
        
        conversations = db_manager.fetch_all(query, params)
        
        # Processar para incluir mensagens formatadas
        for conv in conversations:
            conv['messages'] = [
                {"role": "user", "content": conv['user_question']},
                {"role": "assistant", "content": conv['ai_response']}
            ]
        
        return conversations
        
    except:
        return []

def delete_conversation(conversation_id):
    """Exclui uma conversa"""
    
    try:
        query = "DELETE FROM ai_conversations WHERE id = ?"
        db_manager.execute_query(query, (conversation_id,))
        return True
    except:
        return False

def show_quick_suggestions():
    """Mostra sugestões rápidas de perguntas"""
    
    st.markdown("### 💡 Sugestões de Perguntas")
    
    suggestions = [
        "Quais são os horários dos cultos?",
        "Como posso me tornar membro da igreja?",
        "Quais eventos estão programados para este mês?",
        "Onde posso encontrar os sermões gravados?",
        "Como faço para participar de um ministério?",
        "Qual é o contato da igreja?",
        "Como posso fazer uma doação?",
        "Há atividades para crianças?"
    ]
    
    for suggestion in suggestions:
        if st.button(f"💬 {suggestion}", key=f"suggestion_{suggestion[:20]}"):
            # Adicionar sugestão ao chat
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            
            st.session_state.chat_history.append({"role": "user", "content": suggestion})
            response = generate_ai_response(suggestion, st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            st.success("Pergunta adicionada ao chat!")
            st.rerun()

def get_user_id(username):
    """Busca o ID do usuário pelo username"""
    try:
        query = "SELECT id FROM users WHERE username = ?"
        result = db_manager.fetch_all(query, (username,))
        return result[0]['id'] if result else None
    except:
        return None

# Funções auxiliares para geração de IA
def generate_event_invitation_ai(event, tone, include_details, include_contact):
    """Gera convite para evento usando IA"""
    
    # Contexto base
    context = f"""
    Gere um convite para o evento "{event['title']}" que acontecerá em {event['start_datetime']}.
    Tom da mensagem: {tone}
    """
    
    if include_details:
        context += f"\nLocal: {event.get('location', 'A definir')}"
        context += f"\nDescrição: {event.get('description', '')}"
    
    if include_contact:
        context += "\nIncluir informações de contato da igreja para dúvidas."
    
    # Simular resposta da IA (aqui você integraria com a API real)
    invitation = f"""🎉 *Convite Especial* 🎉

Olá! Esperamos você no evento *{event['title']}*!

📅 *Data:* {event['start_datetime']}
📍 *Local:* {event.get('location', 'Igreja - endereço a confirmar')}

{event.get('description', 'Venha participar deste momento especial conosco!')}

Sua presença é muito importante para nós! 

🙏 Deus abençoe!

_Igreja - Contato: (11) 99999-9999_"""
    
    return invitation

def generate_welcome_message_ai(name, context, style, include_next_steps, include_contact, notes):
    """Gera mensagem de boas-vindas usando IA"""
    
    welcome_msg = f"""👋 Olá, {name}!

É uma alegria tê-lo(a) conosco! """
    
    if context == "Primeira visita":
        welcome_msg += "Esperamos que tenha se sentido em casa durante sua primeira visita."
    elif context == "Retornando":
        welcome_msg += "Que bom vê-lo(a) de volta!"
    elif context == "Convidado por membro":
        welcome_msg += "Ficamos felizes que alguém especial o(a) convidou para nos conhecer."
    
    if notes:
        welcome_msg += f"\n\n{notes}"
    
    if include_next_steps:
        welcome_msg += "\n\n📋 *Próximos passos:*\n• Participe de nossos cultos aos domingos\n• Conheça nossos ministérios\n• Faça parte da nossa família"
    
    if include_contact:
        welcome_msg += "\n\n📞 Para mais informações: (11) 99999-9999"
    
    welcome_msg += "\n\n🙏 Deus abençoe sua vida!"
    
    return welcome_msg

def generate_service_reminder_ai(service_type, reminder_time, tone, theme, special_guest):
    """Gera lembrete de culto usando IA"""
    
    reminder = f"⛪ *Lembrete de Culto* ⛪\n\n"
    
    if reminder_time == "1 hora antes":
        reminder += f"Em 1 hora teremos nosso {service_type}! "
    elif reminder_time == "2 horas antes":
        reminder += f"Em 2 horas teremos nosso {service_type}! "
    else:
        reminder += f"Hoje teremos nosso {service_type}! "
    
    if theme:
        reminder += f"\n\n📖 *Tema:* {theme}"
    
    if special_guest:
        reminder += f"\n👤 *Pregador:* {special_guest}"
    
    if tone == "Motivacional":
        reminder += "\n\n🔥 Prepare seu coração para um encontro transformador com Deus!"
    elif tone == "Carinhoso":
        reminder += "\n\n💝 Esperamos você com muito carinho!"
    elif tone == "Urgente":
        reminder += "\n\n⚡ Não perca este momento especial!"
    
    reminder += "\n\n🙏 Nos vemos lá!"
    
    return reminder

def generate_birthday_message_ai(name, relationship, style, include_verse, include_prayer, notes):
    """Gera mensagem de aniversário usando IA"""
    
    birthday_msg = f"🎂 *Feliz Aniversário, {name}!* 🎂\n\n"
    
    if style == "Alegre":
        birthday_msg += "🎉 Hoje é um dia especial para celebrar sua vida! "
    elif style == "Carinhosa":
        birthday_msg += "💝 Com muito carinho, desejamos um dia repleto de alegrias! "
    elif style == "Espiritual":
        birthday_msg += "🙏 Que Deus continue abençoando sua caminhada! "
    
    if relationship == "Pastor":
        birthday_msg += "Obrigado por sua liderança e dedicação."
    elif relationship == "Líder":
        birthday_msg += "Agradecemos por seu serviço e exemplo."
    
    if notes:
        birthday_msg += f"\n\n{notes}"
    
    if include_verse:
        birthday_msg += '\n\n📖 "Porque eu bem sei os pensamentos que tenho a vosso respeito, diz o Senhor; pensamentos de paz e não de mal, para vos dar o fim que esperais." - Jeremias 29:11'
    
    if include_prayer:
        birthday_msg += "\n\n🙏 Que Deus continue derramando bênçãos sobre sua vida!"
    
    birthday_msg += "\n\n🎈 Com amor, Igreja"
    
    return birthday_msg

def generate_prayer_message_ai(prayer_type, urgency, request, include_verse):
    """Gera mensagem de oração usando IA"""
    
    prayer_msg = f"🙏 *Pedido de {prayer_type}* 🙏\n\n"
    
    if urgency == "Urgente":
        prayer_msg += "🚨 *URGENTE* - "
    elif urgency == "Muito Urgente":
        prayer_msg += "🆘 *MUITO URGENTE* - "
    
    prayer_msg += f"Irmãos, vamos nos unir em oração:\n\n{request}"
    
    if include_verse:
        if prayer_type == "Cura":
            prayer_msg += '\n\n📖 "Pela sua ferida fomos sarados." - Isaías 53:5'
        elif prayer_type == "Proteção":
            prayer_msg += '\n\n📖 "O Senhor é o meu pastor, nada me faltará." - Salmos 23:1'
        else:
            prayer_msg += '\n\n📖 "E tudo o que pedirdes em oração, crendo, recebereis." - Mateus 21:22'
    
    prayer_msg += "\n\n🤝 Vamos orar juntos por esta causa!"
    
    return prayer_msg

def generate_announcement_ai(announcement_type, audience, content, include_action):
    """Gera anúncio geral usando IA"""
    
    announcement = f"📢 *{announcement_type.upper()}* 📢\n\n"
    
    if audience != "Todos os Membros":
        announcement += f"*Para: {audience}*\n\n"
    
    announcement += content
    
    if include_action:
        if announcement_type == "Evento":
            announcement += "\n\n✅ Confirme sua presença!"
        elif announcement_type == "Novo Ministério":
            announcement += "\n\n🙋‍♀️ Interessados, procurem a liderança!"
        else:
            announcement += "\n\n📞 Para mais informações, entre em contato conosco."
    
    announcement += "\n\n🙏 Deus abençoe!"
    
    return announcement

def generate_custom_message_ai(purpose, target, tone, content, include_bible, include_signature):
    """Gera mensagem personalizada usando IA"""
    
    message = ""
    
    if target:
        message += f"Olá, {target}!\n\n"
    
    message += content
    
    if include_bible:
        message += '\n\n📖 "Tudo posso naquele que me fortalece." - Filipenses 4:13'
    
    if include_signature:
        message += "\n\n🙏 Com carinho,\nIgreja"
    
    return message

# Funções para gerenciamento de templates
def get_ai_templates():
    """Busca templates de IA do banco de dados"""
    try:
        query = """
        SELECT id, name, category, description, template_text, created_at
        FROM ai_templates
        ORDER BY created_at DESC
        """
        
        results = db_manager.fetch_all(query)
        
        templates = []
        for row in results:
            templates.append({
                'id': row['id'],
                'name': row['name'],
                'category': row['category'],
                'description': row['description'],
                'template_text': row['template_text'],
                'created_at': row['created_at']
            })
        
        return templates
        
    except Exception as e:
        st.error(f"Erro ao buscar templates: {e}")
        return []

def save_ai_template(name, category, description, template_text):
    """Salva template de IA no banco de dados"""
    try:
        query = """
        INSERT INTO ai_templates (name, category, description, template_text, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        """
        
        db_manager.execute_query(query, (name, category, description, template_text))
        return True
        
    except Exception as e:
        st.error(f"Erro ao salvar template: {e}")
        return False

def delete_ai_template(template_id):
    """Exclui template de IA do banco de dados"""
    try:
        query = "DELETE FROM ai_templates WHERE id = ?"
        db_manager.execute_query(query, (template_id,))
        return True
        
    except Exception as e:
        st.error(f"Erro ao excluir template: {e}")
        return False

# Funções auxiliares para dados
def get_upcoming_events():
    """Busca eventos próximos do banco de dados"""
    try:
        query = """
        SELECT id, title, description, start_datetime, location
        FROM events
        WHERE start_datetime >= datetime('now')
        ORDER BY start_datetime ASC
        LIMIT 10
        """
        
        results = db_manager.fetch_all(query)
        
        events = []
        for row in results:
            events.append({
                'id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'start_datetime': row['start_datetime'],
                'location': row['location']
            })
        
        return events
        
    except Exception as e:
        st.error(f"Erro ao buscar eventos: {e}")
        return []

def send_ai_generated_messages(message, selected_contacts, contact_options):
    """Envia mensagens geradas por IA via WhatsApp"""
    import time
    
    success_count = 0
    error_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, contact_key in enumerate(selected_contacts):
        contact = contact_options[contact_key]
        
        status_text.text(f"Enviando para {contact['name']}...")
        
        success, error_msg = whatsapp_api_service.send_message(contact['phone'], message)
        
        if success:
            success_count += 1
        else:
            error_count += 1
            st.error(f"Erro ao enviar para {contact['name']}: {error_msg}")
        
        # Atualizar barra de progresso
        progress_bar.progress((i + 1) / len(selected_contacts))
        
        # Delay entre mensagens para evitar bloqueio
        time.sleep(random.uniform(2, 5))
    
    status_text.text("Envio concluído!")
    
    if success_count > 0:
        st.success(f"✅ {success_count} mensagens enviadas com sucesso!")
    
    if error_count > 0:
        st.error(f"❌ {error_count} mensagens falharam.")

def generate_fallback_response(user_input, church_context):
    """Gera uma resposta de fallback quando a API não está disponível"""
    user_input_lower = user_input.lower()
    
    # Respostas baseadas em palavras-chave
    if any(word in user_input_lower for word in ['evento', 'culto', 'reunião', 'programação']):
        events = church_context.get('events', [])
        if events:
            return f"Temos alguns eventos próximos: {events}. Para mais informações, entre em contato conosco!"
        else:
            return "No momento não temos eventos programados, mas fique atento às nossas redes sociais para novidades!"
    
    elif any(word in user_input_lower for word in ['horário', 'hora', 'quando']):
        return "Nossos cultos principais são aos domingos. Para horários específicos, consulte nossa programação ou entre em contato!"
    
    elif any(word in user_input_lower for word in ['localização', 'endereço', 'onde', 'local']):
        return "Nossa igreja está localizada em um local acolhedor. Entre em contato conosco para obter o endereço completo!"
    
    elif any(word in user_input_lower for word in ['oração', 'orar', 'pray']):
        return "Que bênção poder orar! 'Orai sem cessar' (1 Tessalonicenses 5:17). Como posso ajudá-lo em suas orações?"
    
    elif any(word in user_input_lower for word in ['bíblia', 'versículo', 'palavra']):
        return "A Palavra de Deus é lâmpada para os nossos pés! Como posso ajudá-lo com estudos bíblicos?"
    
    elif any(word in user_input_lower for word in ['batismo', 'batizar']):
        return "O batismo é um passo importante na vida cristã! Entre em contato com nossa liderança para mais informações."
    
    elif any(word in user_input_lower for word in ['dízimo', 'oferta', 'contribuição']):
        return "Deus ama quem dá com alegria! Para informações sobre contribuições, fale com nossa tesouraria."
    
    else:
        # Resposta genérica acolhedora
        responses = [
            "Obrigado por sua mensagem! Nossa equipe está aqui para ajudá-lo. Como posso auxiliá-lo hoje?",
            "Que bênção ter você aqui! Como posso ajudá-lo em sua jornada de fé?",
            "Paz do Senhor! Estou aqui para ajudá-lo. O que gostaria de saber?",
            "Seja bem-vindo(a)! Como posso servi-lo hoje?",
            "Que alegria conversar com você! Em que posso ajudá-lo?"
        ]
        return random.choice(responses)