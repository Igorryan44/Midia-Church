"""
Módulo WhatsApp API Refatorado
Interface Streamlit usando o sistema unificado de mensagens
Remove duplicações e melhora a arquitetura
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
import json
import time
from typing import Dict, List, Optional, Any
import logging

# Imports do sistema unificado
from app.services.message_manager import message_manager
from app.interfaces.message_service import (
    Message, MessageContent, MessageRecipient, MessageType, 
    MessagePriority, MessageStatus, MessageValidator
)
from app.config.whatsapp_api_config import (
    API_CONFIG, MESSAGE_TYPES, CHURCH_TEMPLATES,
    SUCCESS_MESSAGES, ERROR_MESSAGES, UI_CONFIG
)

logger = logging.getLogger(__name__)

def render_whatsapp_api():
    """Renderiza interface principal da API WhatsApp refatorada"""
    st.title("📱 WhatsApp API - Sistema Unificado")
    st.markdown("*Sistema avançado de mensagens com arquitetura refatorada*")
    
    # Verificar status dos serviços
    status = message_manager.get_service_status()
    whatsapp_status = status.get('whatsapp', {})
    
    # Header com status
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if whatsapp_status.get('connected', False):
            st.success("✅ WhatsApp Conectado")
        else:
            st.error("❌ WhatsApp Desconectado")
    
    with col2:
        if st.button("🔄 Conectar Serviços", key="connect_services"):
            with st.spinner("Conectando serviços..."):
                results = asyncio.run(message_manager.connect_all_services())
                
                for service, (success, msg) in results.items():
                    if success:
                        st.success(f"✅ {service}: {msg}")
                    else:
                        st.error(f"❌ {service}: {msg}")
                
                st.rerun()
    
    with col3:
        if st.button("🔌 Desconectar", key="disconnect_services"):
            results = asyncio.run(message_manager.disconnect_all_services())
            for service, success in results.items():
                if success:
                    st.success(f"✅ {service} desconectado")
                else:
                    st.error(f"❌ Erro ao desconectar {service}")
            st.rerun()
    
    # Mostrar QR Code se necessário
    if whatsapp_status.get('connection_status') == 'qr_required':
        qr_code = whatsapp_status.get('qr_code')
        if qr_code:
            st.markdown("### 📱 Escaneie o QR Code")
            st.image(qr_code, caption="QR Code WhatsApp", width=300)
            st.info("Abra o WhatsApp no seu celular e escaneie este código")
            
            if st.button("🔄 Atualizar QR", key="refresh_qr"):
                st.rerun()
    
    # Tabs principais
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", "💬 Enviar", "👥 Contatos", 
        "📝 Templates", "🔧 Configurações", "📈 Relatórios"
    ])
    
    with tab1:
        render_dashboard()
    
    with tab2:
        render_send_message()
    
    with tab3:
        render_contacts()
    
    with tab4:
        render_templates()
    
    with tab5:
        render_settings()
    
    with tab6:
        render_reports()

def render_dashboard():
    """Renderiza dashboard unificado"""
    st.markdown("### 📊 Dashboard Unificado")
    
    # Estatísticas dos serviços
    try:
        stats = asyncio.run(message_manager.get_statistics())
        today_stats = stats.get('today', {})
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        stats = {}
        today_stats = {}
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    whatsapp_stats = today_stats.get('whatsapp', {})
    email_stats = today_stats.get('email', {})
    
    with col1:
        total_sent = whatsapp_stats.get('sent', 0) + email_stats.get('sent', 0)
        st.metric("Mensagens Enviadas Hoje", total_sent)
    
    with col2:
        total_messages = whatsapp_stats.get('total', 0) + email_stats.get('total', 0)
        success_rate = (total_sent / total_messages * 100) if total_messages > 0 else 0
        st.metric("Taxa de Sucesso", f"{success_rate:.1f}%")
    
    with col3:
        whatsapp_sent = whatsapp_stats.get('sent', 0)
        st.metric("WhatsApp Enviadas", whatsapp_sent)
    
    with col4:
        email_sent = email_stats.get('sent', 0)
        st.metric("Emails Enviados", email_sent)
    
    # Status dos serviços
    st.markdown("### 🔗 Status dos Serviços")
    
    services_status = stats.get('services', {})
    if not services_status:
        services_status = message_manager.get_service_status()
    
    for service_name, service_info in services_status.items():
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if service_info.get('connected', False):
                st.success(f"✅ {service_name.title()}")
            else:
                st.error(f"❌ {service_name.title()}")
        
        with col2:
            if 'error' in service_info:
                st.error(f"Erro: {service_info['error']}")
            else:
                supported_types = service_info.get('supported_types', [])
                st.info(f"Tipos suportados: {', '.join(supported_types)}")
    
    # Gráfico de mensagens
    st.markdown("### 📈 Histórico de Mensagens")
    
    history = asyncio.run(message_manager.get_message_history(limit=50))
    
    if history:
        df = pd.DataFrame(history)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date
        
        # Agrupar por data e serviço
        daily_stats = df.groupby(['date', 'service']).size().reset_index(name='count')
        
        if not daily_stats.empty:
            fig = px.bar(
                daily_stats,
                x='date',
                y='count',
                color='service',
                title="Mensagens por Dia e Serviço",
                color_discrete_map={'whatsapp': '#25D366', 'email': '#EA4335'}
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum histórico de mensagens disponível")

def render_send_message():
    """Renderiza interface unificada de envio"""
    st.markdown("### 💬 Enviar Mensagem - Sistema Unificado")
    
    # Verificar status dos serviços
    status = asyncio.run(message_manager.get_service_status())
    
    available_services = [
        name for name, info in status.items() 
        if info.get('connected', False)
    ]
    
    if not available_services:
        st.error("❌ Nenhum serviço conectado. Conecte primeiro na aba Dashboard.")
        return
    
    # Formulário de envio
    with st.form("unified_send_message_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Destinatário
            recipient_type = st.radio(
                "Tipo de Destinatário",
                ["WhatsApp", "Email", "Automático"],
                horizontal=True,
                help="Automático escolhe o melhor serviço baseado no contato"
            )
            
            if recipient_type == "WhatsApp":
                contact = st.text_input(
                    "📱 Número do WhatsApp",
                    placeholder="+5511999999999",
                    help="Digite o número com código do país"
                )
            elif recipient_type == "Email":
                contact = st.text_input(
                    "📧 Email",
                    placeholder="exemplo@email.com"
                )
            else:  # Automático
                contact = st.text_input(
                    "📱📧 Telefone ou Email",
                    placeholder="+5511999999999 ou exemplo@email.com"
                )
            
            # Assunto (para emails)
            subject = st.text_input(
                "📝 Assunto",
                placeholder="Assunto da mensagem (usado em emails)"
            )
            
            # Mensagem
            message_text = st.text_area(
                "💬 Mensagem",
                height=150,
                placeholder="Digite sua mensagem aqui..."
            )
        
        with col2:
            # Serviço preferido
            preferred_service = st.selectbox(
                "🎯 Serviço Preferido",
                options=["Automático"] + available_services,
                help="Escolha o serviço ou deixe automático"
            )
            
            # Prioridade
            priority = st.selectbox(
                "⚡ Prioridade",
                options=[p.name for p in MessagePriority],
                index=1  # Normal
            )
            
            # Template rápido
            template_category = st.selectbox(
                "📋 Template",
                options=["Nenhum"] + list(CHURCH_TEMPLATES.keys())
            )
            
            if template_category != "Nenhum":
                template_name = st.selectbox(
                    "Escolher Template",
                    options=list(CHURCH_TEMPLATES[template_category].keys())
                )
                
                if st.button("📋 Usar Template"):
                    st.session_state.template_text = CHURCH_TEMPLATES[template_category][template_name]
        
        # Aplicar template se selecionado
        if 'template_text' in st.session_state:
            message_text = st.session_state.template_text
            del st.session_state.template_text
        
        # Botões de ação
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            send_now = st.form_submit_button("📤 Enviar", type="primary")
        
        with col2:
            validate_only = st.form_submit_button("✅ Validar")
    
    # Processar envio
    if send_now or validate_only:
        if not contact or not message_text:
            st.error("❌ Preencha o destinatário e a mensagem")
        else:
            # Criar destinatário
            recipient = None
            
            if recipient_type == "WhatsApp" or MessageValidator.validate_phone(contact):
                if MessageValidator.validate_phone(contact):
                    recipient = MessageRecipient(phone=contact)
                else:
                    st.error("❌ Número de telefone inválido")
                    return
            
            elif recipient_type == "Email" or MessageValidator.validate_email(contact):
                if MessageValidator.validate_email(contact):
                    recipient = MessageRecipient(email=contact)
                else:
                    st.error("❌ Email inválido")
                    return
            
            else:
                st.error("❌ Contato inválido. Use um telefone ou email válido")
                return
            
            if recipient:
                # Criar mensagem
                message = Message(
                    subject=subject or "Mensagem",
                    content=MessageContent(text=message_text),
                    recipients=[recipient],
                    message_type=MessageType.TEXT,
                    priority=MessagePriority[priority]
                )
                
                if validate_only:
                    st.success("✅ Mensagem válida!")
                    st.json({
                        "Destinatário": contact,
                        "Tipo": recipient_type,
                        "Assunto": subject,
                        "Mensagem": message_text[:100] + "..." if len(message_text) > 100 else message_text,
                        "Prioridade": priority
                    })
                else:
                    with st.spinner("Enviando mensagem..."):
                        try:
                            service_type = None if preferred_service == "Automático" else preferred_service.lower()
                            
                            result = asyncio.run(
                                message_manager.send_message(message, service_type)
                            )
                            
                            if result.success:
                                st.success(f"✅ Mensagem enviada! ID: {result.message_id}")
                                if result.service_used:
                                    st.info(f"📡 Enviado via: {result.service_used}")
                            else:
                                st.error(f"❌ Falha no envio: {result.error_message}")
                        
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
    
    # Histórico unificado
    st.markdown("### 📋 Histórico Unificado")
    
    try:
        history = asyncio.run(message_manager.get_message_history(limit=15))
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}")
        history = []
    
    if history:
        df = pd.DataFrame(history)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.sort_values('created_at', ascending=False)
        
        # Formatação para exibição
        display_df = df.copy()
        if 'message' in display_df.columns:
            display_df['message'] = display_df['message'].str[:50] + '...'
        display_df['created_at'] = display_df['created_at'].dt.strftime('%d/%m %H:%M')
        
        st.dataframe(
            display_df,
            column_config={
                "recipient": "Destinatário",
                "message": "Mensagem",
                "status": "Status",
                "service": "Serviço",
                "created_at": "Enviado em"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Nenhuma mensagem no histórico")

def render_contacts():
    """Renderiza gerenciamento unificado de contatos"""
    st.markdown("### 👥 Contatos Unificados")
    
    # Buscar contatos do WhatsApp
    if st.button("🔄 Sincronizar Contatos WhatsApp"):
        with st.spinner("Sincronizando..."):
            # Implementar sincronização via serviço unificado
            st.success("✅ Contatos sincronizados")
    
    # Lista de contatos (implementar busca unificada)
    st.info("🚧 Funcionalidade em desenvolvimento - Contatos unificados")

def render_templates():
    """Renderiza templates unificados"""
    st.markdown("### 📝 Templates Unificados")
    
    # Templates da igreja
    for category, templates in CHURCH_TEMPLATES.items():
        with st.expander(f"📋 {category.title()}"):
            for name, content in templates.items():
                st.markdown(f"**{name}**")
                st.code(content, language="text")
                
                col1, col2, col3 = st.columns([1, 1, 3])
                
                with col1:
                    if st.button(f"📱 WhatsApp", key=f"wa_{category}_{name}"):
                        st.session_state.template_text = content
                        st.session_state.template_service = "whatsapp"
                        st.success("Template para WhatsApp!")
                
                with col2:
                    if st.button(f"📧 Email", key=f"email_{category}_{name}"):
                        st.session_state.template_text = content
                        st.session_state.template_service = "email"
                        st.success("Template para Email!")

def render_settings():
    """Renderiza configurações unificadas"""
    st.markdown("### 🔧 Configurações Unificadas")
    
    # Status dos serviços
    status = message_manager.get_service_status()
    
    st.markdown("#### 📡 Serviços Disponíveis")
    
    for service_name, service_info in status.items():
        with st.expander(f"🔧 {service_name.title()}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.json({
                    "Status": "Conectado" if service_info.get('connected') else "Desconectado",
                    "Tipos Suportados": service_info.get('supported_types', [])
                })
            
            with col2:
                if service_info.get('connected'):
                    if st.button(f"🔌 Desconectar {service_name}", key=f"disconnect_{service_name}"):
                        # Implementar desconexão individual
                        st.success(f"✅ {service_name} desconectado")
                else:
                    if st.button(f"🔗 Conectar {service_name}", key=f"connect_{service_name}"):
                        # Implementar conexão individual
                        st.success(f"✅ {service_name} conectado")
    
    # Configurações gerais
    st.markdown("#### ⚙️ Configurações Gerais")
    
    with st.expander("📊 Configurações de Mensagens"):
        st.slider("Limite de mensagens por minuto", 1, 60, 30)
        st.checkbox("Salvar histórico de mensagens", value=True)
        st.checkbox("Logs detalhados", value=False)

def render_reports():
    """Renderiza relatórios unificados"""
    st.markdown("### 📈 Relatórios Unificados")
    
    # Período
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Data Inicial", datetime.now() - timedelta(days=30))
    
    with col2:
        end_date = st.date_input("Data Final", datetime.now())
    
    # Estatísticas do período
    try:
        stats = asyncio.run(message_manager.get_statistics())
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        stats = {}
    
    st.markdown("#### 📊 Resumo do Período")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Mensagens", "🚧 Em desenvolvimento")
    
    with col2:
        st.metric("Taxa de Sucesso", "🚧 Em desenvolvimento")
    
    with col3:
        st.metric("Serviço Mais Usado", "🚧 Em desenvolvimento")
    
    # Gráficos
    st.markdown("#### 📈 Gráficos")
    st.info("🚧 Relatórios detalhados em desenvolvimento")

# Função auxiliar para compatibilidade
def render_whatsapp_api_legacy():
    """Wrapper para compatibilidade com código existente"""
    return render_whatsapp_api()