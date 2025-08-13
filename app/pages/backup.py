import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import shutil
import sqlite3
import zipfile
import json
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from app.utils.auth import get_current_user, is_admin, require_admin
from app.database.local_connection import db_manager

def show_backup_page():
    """Página principal de gerenciamento de backups"""
    
    # Verificar autenticação e permissões
    if not require_admin():
        return
    
    st.title("💾 Gerenciamento de Backups")
    st.markdown("### 🔒 Sistema Completo de Backup e Recuperação")
    st.markdown("---")
    
    # Tabs para diferentes seções
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", 
        "🔄 Criar Backup", 
        "📂 Gerenciar Backups", 
        "🔄 Restaurar",
        "⚙️ Configurações"
    ])
    
    with tab1:
        show_backup_dashboard()
    
    with tab2:
        show_create_backup()
    
    with tab3:
        show_manage_backups()
    
    with tab4:
        show_restore_backup()
    
    with tab5:
        show_backup_settings()

def show_backup_dashboard():
    """Dashboard de estatísticas de backup"""
    st.header("📊 Dashboard de Backups")
    
    # Obter estatísticas
    stats = get_backup_statistics()
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📦 Total de Backups",
            stats.get('total_backups', 0),
            help="Número total de backups armazenados"
        )
    
    with col2:
        total_size_mb = stats.get('total_size_mb', 0)
        st.metric(
            "💽 Espaço Utilizado",
            f"{total_size_mb:.1f} MB",
            help="Espaço total ocupado pelos backups"
        )
    
    with col3:
        oldest = stats.get('oldest_backup')
        if oldest:
            days_old = (datetime.now() - oldest).days
            st.metric(
                "📅 Backup Mais Antigo",
                f"{days_old} dias",
                help=f"Data: {oldest.strftime('%d/%m/%Y')}"
            )
        else:
            st.metric("📅 Backup Mais Antigo", "N/A")
    
    with col4:
        newest = stats.get('newest_backup')
        if newest:
            hours_ago = (datetime.now() - newest).total_seconds() / 3600
            if hours_ago < 24:
                time_str = f"{int(hours_ago)}h atrás"
            else:
                time_str = f"{int(hours_ago/24)}d atrás"
            st.metric(
                "🕒 Último Backup",
                time_str,
                help=f"Data: {newest.strftime('%d/%m/%Y %H:%M')}"
            )
        else:
            st.metric("🕒 Último Backup", "N/A")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        show_backup_types_chart(stats)
    
    with col2:
        show_backup_timeline()
    
    # Alertas e recomendações
    show_backup_alerts(stats)

def show_backup_types_chart(stats):
    """Gráfico de tipos de backup"""
    st.subheader("📈 Tipos de Backup")
    
    backup_types = stats.get('backup_types', {})
    
    if backup_types:
        # Traduzir tipos para português
        type_translation = {
            'full_backup': 'Backup Completo',
            'incremental_backup': 'Backup Incremental',
            'database_only': 'Apenas Banco',
            'files_only': 'Apenas Arquivos',
            'unknown': 'Tipo Desconhecido'
        }
        
        translated_types = {
            type_translation.get(k, k): v 
            for k, v in backup_types.items()
        }
        
        fig = px.pie(
            values=list(translated_types.values()),
            names=list(translated_types.keys()),
            title="Distribuição por Tipo"
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Nenhum backup encontrado para análise")

def show_backup_timeline():
    """Timeline de backups"""
    st.subheader("📅 Timeline de Backups")
    
    backups = list_backups()
    
    if backups:
        # Preparar dados para o gráfico
        df_data = []
        for backup in backups[-10:]:  # Últimos 10 backups
            df_data.append({
                'Data': backup['created_at'].strftime('%d/%m'),
                'Tamanho (MB)': round(backup['size'] / (1024 * 1024), 2),
                'Tipo': backup.get('type', 'unknown')
            })
        
        if df_data:
            df = pd.DataFrame(df_data)
            
            fig = px.bar(
                df,
                x='Data',
                y='Tamanho (MB)',
                color='Tipo',
                title="Tamanho dos Últimos Backups"
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📈 Dados insuficientes para gráfico")
    else:
        st.info("📅 Nenhum backup encontrado")

def show_backup_alerts(stats):
    """Exibe alertas e recomendações"""
    st.subheader("⚠️ Alertas e Recomendações")
    
    alerts = []
    
    # Verificar se há backups
    if stats.get('total_backups', 0) == 0:
        alerts.append({
            'type': 'error',
            'message': 'Nenhum backup encontrado! Crie um backup imediatamente.',
            'action': 'Criar primeiro backup'
        })
    
    # Verificar backup recente
    newest = stats.get('newest_backup')
    if newest:
        days_since_last = (datetime.now() - newest).days
        if days_since_last > 7:
            alerts.append({
                'type': 'warning',
                'message': f'Último backup há {days_since_last} dias. Recomenda-se backup semanal.',
                'action': 'Criar novo backup'
            })
    
    # Verificar espaço em disco
    total_size = stats.get('total_size_mb', 0)
    if total_size > 1000:  # Mais de 1GB
        alerts.append({
            'type': 'info',
            'message': f'Backups ocupando {total_size:.1f} MB. Considere limpeza.',
            'action': 'Gerenciar backups antigos'
        })
    
    # Exibir alertas
    if alerts:
        for alert in alerts:
            if alert['type'] == 'error':
                st.error(f"🚨 {alert['message']}")
            elif alert['type'] == 'warning':
                st.warning(f"⚠️ {alert['message']}")
            else:
                st.info(f"ℹ️ {alert['message']}")
    else:
        st.success("✅ Todos os indicadores de backup estão normais!")

def show_create_backup():
    """Interface para criar novos backups"""
    st.header("🔄 Criar Novo Backup")
    
    with st.form("create_backup_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Configurações do Backup")
            
            backup_type = st.selectbox(
                "Tipo de Backup",
                ["full_backup", "database_only", "files_only"],
                format_func=lambda x: {
                    "full_backup": "🔄 Backup Completo",
                    "database_only": "🗄️ Apenas Banco de Dados",
                    "files_only": "📁 Apenas Arquivos"
                }[x]
            )
            
            include_media = st.checkbox("📸 Incluir arquivos de mídia", value=True)
            include_logs = st.checkbox("📝 Incluir logs do sistema", value=False)
            compress_backup = st.checkbox("🗜️ Comprimir backup", value=True)
        
        with col2:
            st.subheader("📝 Informações Adicionais")
            
            backup_name = st.text_input(
                "Nome do Backup (opcional)",
                placeholder="Ex: backup_pre_atualizacao"
            )
            
            description = st.text_area(
                "Descrição",
                placeholder="Descreva o motivo ou contexto deste backup..."
            )
            
            retention_days = st.number_input(
                "Retenção (dias)",
                min_value=1,
                max_value=365,
                value=30,
                help="Dias para manter este backup antes da exclusão automática"
            )
        
        # Botão de criação
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            create_button = st.form_submit_button(
                "🚀 Criar Backup",
                type="primary",
                use_container_width=True
            )
    
    if create_button:
        with st.spinner("🔄 Criando backup..."):
            try:
                backup_config = {
                    'type': backup_type,
                    'name': backup_name or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'description': description,
                    'include_media': include_media,
                    'include_logs': include_logs,
                    'compress': compress_backup,
                    'retention_days': retention_days
                }
                
                result = create_backup(backup_config)
                
                if result['success']:
                    st.success(f"✅ Backup criado com sucesso!")
                    st.info(f"📁 Arquivo: {result['filename']}")
                    st.info(f"📊 Tamanho: {result['size_mb']:.2f} MB")
                    
                    # Mostrar progresso se disponível
                    if 'progress' in result:
                        st.progress(result['progress'])
                else:
                    st.error(f"❌ Erro ao criar backup: {result['error']}")
                    
            except Exception as e:
                st.error(f"❌ Erro inesperado: {str(e)}")

def show_manage_backups():
    """Interface para gerenciar backups existentes"""
    st.header("📂 Gerenciar Backups Existentes")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_type = st.selectbox(
            "Filtrar por tipo",
            ["Todos", "full_backup", "database_only", "files_only"],
            format_func=lambda x: {
                "Todos": "📋 Todos os tipos",
                "full_backup": "🔄 Backup Completo",
                "database_only": "🗄️ Apenas Banco",
                "files_only": "📁 Apenas Arquivos"
            }.get(x, x)
        )
    
    with col2:
        sort_by = st.selectbox(
            "Ordenar por",
            ["Data (mais recente)", "Data (mais antigo)", "Tamanho (maior)", "Tamanho (menor)"]
        )
    
    with col3:
        if st.button("🔄 Atualizar Lista"):
            st.rerun()
    
    # Listar backups
    backups = list_backups()
    
    if filter_type != "Todos":
        backups = [b for b in backups if b.get('type') == filter_type]
    
    # Aplicar ordenação
    if "Data (mais recente)" in sort_by:
        backups.sort(key=lambda x: x['created_at'], reverse=True)
    elif "Data (mais antigo)" in sort_by:
        backups.sort(key=lambda x: x['created_at'])
    elif "Tamanho (maior)" in sort_by:
        backups.sort(key=lambda x: x['size'], reverse=True)
    elif "Tamanho (menor)" in sort_by:
        backups.sort(key=lambda x: x['size'])
    
    if backups:
        st.subheader(f"📋 {len(backups)} backup(s) encontrado(s)")
        
        # Ações em lote
        with st.expander("🔧 Ações em Lote"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🗑️ Limpar Backups Antigos (>30 dias)"):
                    deleted_count = cleanup_old_backups(30)
                    st.success(f"✅ {deleted_count} backup(s) removido(s)")
                    st.rerun()
            
            with col2:
                if st.button("📊 Verificar Integridade"):
                    verify_all_backups()
            
            with col3:
                if st.button("📤 Exportar Lista"):
                    export_backup_list(backups)
        
        # Lista de backups
        for i, backup in enumerate(backups):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    # Informações do backup
                    type_icon = {
                        'full_backup': '🔄',
                        'database_only': '🗄️',
                        'files_only': '📁'
                    }.get(backup.get('type'), '📦')
                    
                    st.markdown(f"**{type_icon} {backup['name']}**")
                    st.caption(f"📅 {backup['created_at'].strftime('%d/%m/%Y %H:%M')}")
                    st.caption(f"📊 {backup['size'] / (1024*1024):.2f} MB")
                    
                    if backup.get('description'):
                        st.caption(f"📝 {backup['description']}")
                
                with col2:
                    # Status do backup
                    if backup.get('verified', False):
                        st.success("✅ Verificado")
                    else:
                        st.warning("⚠️ Não verificado")
                
                with col3:
                    # Ações
                    if st.button("📥 Restaurar", key=f"restore_{i}"):
                        st.session_state[f'restore_backup_{i}'] = backup
                        st.rerun()
                    
                    if st.button("🔍 Verificar", key=f"verify_{i}"):
                        verify_backup(backup['filename'])
                
                with col4:
                    # Download e exclusão
                    if st.button("📤 Download", key=f"download_{i}"):
                        download_backup(backup['filename'])
                    
                    if st.button("🗑️ Excluir", key=f"delete_{i}"):
                        if delete_backup(backup['filename']):
                            st.success("✅ Backup excluído!")
                            st.rerun()
                
                st.markdown("---")
    else:
        st.info("📭 Nenhum backup encontrado com os filtros aplicados.")

def show_restore_backup():
    """Interface para restaurar backups"""
    st.header("🔄 Restaurar Backup")
    
    # Verificar se há backup selecionado para restauração
    restore_backup_key = None
    for key in st.session_state.keys():
        if key.startswith('restore_backup_'):
            restore_backup_key = key
            break
    
    if restore_backup_key:
        backup = st.session_state[restore_backup_key]
        
        st.warning("⚠️ **ATENÇÃO**: A restauração substituirá os dados atuais!")
        
        with st.container():
            st.subheader(f"📦 Backup Selecionado: {backup['name']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"📅 **Data:** {backup['created_at'].strftime('%d/%m/%Y %H:%M')}")
                st.info(f"📊 **Tamanho:** {backup['size'] / (1024*1024):.2f} MB")
                st.info(f"🔧 **Tipo:** {backup.get('type', 'unknown')}")
            
            with col2:
                if backup.get('description'):
                    st.info(f"📝 **Descrição:** {backup['description']}")
                
                # Opções de restauração
                restore_database = st.checkbox("🗄️ Restaurar banco de dados", value=True)
                restore_files = st.checkbox("📁 Restaurar arquivos", value=True)
                create_backup_before = st.checkbox("💾 Criar backup antes da restauração", value=True)
            
            # Confirmação
            st.markdown("---")
            st.subheader("⚠️ Confirmação de Restauração")
            
            confirmation = st.text_input(
                "Digite 'CONFIRMAR' para prosseguir:",
                placeholder="CONFIRMAR"
            )
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.button("❌ Cancelar", use_container_width=True):
                    del st.session_state[restore_backup_key]
                    st.rerun()
            
            with col2:
                if st.button("🔄 RESTAURAR", type="primary", use_container_width=True):
                    if confirmation == "CONFIRMAR":
                        with st.spinner("🔄 Restaurando backup..."):
                            try:
                                restore_config = {
                                    'backup_file': backup['filename'],
                                    'restore_database': restore_database,
                                    'restore_files': restore_files,
                                    'create_backup_before': create_backup_before
                                }
                                
                                result = restore_backup_file(restore_config)
                                
                                if result['success']:
                                    st.success("✅ Backup restaurado com sucesso!")
                                    if result.get('backup_created'):
                                        st.info(f"💾 Backup de segurança criado: {result['backup_filename']}")
                                    
                                    del st.session_state[restore_backup_key]
                                    st.rerun()
                                else:
                                    st.error(f"❌ Erro na restauração: {result['error']}")
                                    
                            except Exception as e:
                                st.error(f"❌ Erro inesperado: {str(e)}")
                    else:
                        st.error("❌ Digite 'CONFIRMAR' para prosseguir")
    else:
        st.info("📋 Selecione um backup na aba 'Gerenciar Backups' para restaurar.")
        
        # Lista de backups disponíveis para seleção rápida
        st.subheader("📋 Backups Disponíveis")
        backups = list_backups()
        
        if backups:
            for i, backup in enumerate(backups[:5]):  # Mostrar apenas os 5 mais recentes
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    type_icon = {
                        'full_backup': '🔄',
                        'database_only': '🗄️',
                        'files_only': '📁'
                    }.get(backup.get('type'), '📦')
                    
                    st.write(f"{type_icon} **{backup['name']}** - {backup['created_at'].strftime('%d/%m/%Y %H:%M')}")
                
                with col2:
                    if st.button("Selecionar", key=f"select_restore_{i}"):
                        st.session_state[f'restore_backup_{i}'] = backup
                        st.rerun()

def show_backup_settings():
    """Configurações de backup"""
    st.header("⚙️ Configurações de Backup")
    
    # Carregar configurações atuais
    settings = load_backup_settings()
    
    with st.form("backup_settings_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔄 Backup Automático")
            
            auto_backup_enabled = st.checkbox(
                "Habilitar backup automático",
                value=settings.get('auto_backup_enabled', False)
            )
            
            auto_backup_frequency = st.selectbox(
                "Frequência",
                ["daily", "weekly", "monthly"],
                index=["daily", "weekly", "monthly"].index(settings.get('auto_backup_frequency', 'weekly')),
                format_func=lambda x: {
                    "daily": "📅 Diário",
                    "weekly": "📆 Semanal",
                    "monthly": "🗓️ Mensal"
                }[x]
            )
            
            auto_backup_time = st.time_input(
                "Horário do backup automático",
                value=datetime.strptime(settings.get('auto_backup_time', '02:00'), '%H:%M').time()
            )
        
        with col2:
            st.subheader("🗂️ Armazenamento")
            
            backup_location = st.text_input(
                "Diretório de backups",
                value=settings.get('backup_location', './backups')
            )
            
            max_backups = st.number_input(
                "Máximo de backups a manter",
                min_value=1,
                max_value=100,
                value=settings.get('max_backups', 10)
            )
            
            compression_level = st.slider(
                "Nível de compressão",
                min_value=1,
                max_value=9,
                value=settings.get('compression_level', 6),
                help="1 = mais rápido, 9 = menor tamanho"
            )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📧 Notificações")
            
            email_notifications = st.checkbox(
                "Notificar por email",
                value=settings.get('email_notifications', False)
            )
            
            notification_email = st.text_input(
                "Email para notificações",
                value=settings.get('notification_email', '')
            )
        
        with col2:
            st.subheader("🔒 Segurança")
            
            encrypt_backups = st.checkbox(
                "Criptografar backups",
                value=settings.get('encrypt_backups', False)
            )
            
            verify_integrity = st.checkbox(
                "Verificar integridade automaticamente",
                value=settings.get('verify_integrity', True)
            )
        
        # Botão de salvamento
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.form_submit_button("💾 Salvar Configurações", type="primary", use_container_width=True):
                new_settings = {
                    'auto_backup_enabled': auto_backup_enabled,
                    'auto_backup_frequency': auto_backup_frequency,
                    'auto_backup_time': auto_backup_time.strftime('%H:%M'),
                    'backup_location': backup_location,
                    'max_backups': max_backups,
                    'compression_level': compression_level,
                    'email_notifications': email_notifications,
                    'notification_email': notification_email,
                    'encrypt_backups': encrypt_backups,
                    'verify_integrity': verify_integrity
                }
                
                if save_backup_settings(new_settings):
                    st.success("✅ Configurações salvas com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar configurações!")

# Funções auxiliares para o sistema de backup

def get_backup_statistics():
    """Obtém estatísticas dos backups"""
    try:
        backup_dir = Path("./backups")
        if not backup_dir.exists():
            return {'total_backups': 0, 'total_size_mb': 0}
        
        backups = list(backup_dir.glob("*.zip"))
        
        if not backups:
            return {'total_backups': 0, 'total_size_mb': 0}
        
        total_size = sum(backup.stat().st_size for backup in backups)
        
        # Obter datas
        dates = [datetime.fromtimestamp(backup.stat().st_mtime) for backup in backups]
        
        # Contar tipos (baseado no nome do arquivo)
        backup_types = {}
        for backup in backups:
            if 'full' in backup.name:
                backup_types['full_backup'] = backup_types.get('full_backup', 0) + 1
            elif 'database' in backup.name:
                backup_types['database_only'] = backup_types.get('database_only', 0) + 1
            elif 'files' in backup.name:
                backup_types['files_only'] = backup_types.get('files_only', 0) + 1
            else:
                backup_types['unknown'] = backup_types.get('unknown', 0) + 1
        
        return {
            'total_backups': len(backups),
            'total_size_mb': total_size / (1024 * 1024),
            'oldest_backup': min(dates) if dates else None,
            'newest_backup': max(dates) if dates else None,
            'backup_types': backup_types
        }
        
    except Exception as e:
        st.error(f"Erro ao obter estatísticas: {str(e)}")
        return {'total_backups': 0, 'total_size_mb': 0}

def list_backups():
    """Lista todos os backups disponíveis"""
    try:
        backup_dir = Path("./backups")
        if not backup_dir.exists():
            backup_dir.mkdir(parents=True)
            return []
        
        backups = []
        for backup_file in backup_dir.glob("*.zip"):
            stat = backup_file.stat()
            
            # Tentar extrair metadados do nome do arquivo
            name = backup_file.stem
            backup_type = 'unknown'
            
            if 'full' in name:
                backup_type = 'full_backup'
            elif 'database' in name:
                backup_type = 'database_only'
            elif 'files' in name:
                backup_type = 'files_only'
            
            backups.append({
                'filename': backup_file.name,
                'name': name,
                'type': backup_type,
                'size': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_mtime),
                'verified': False  # Implementar verificação real
            })
        
        return backups
        
    except Exception as e:
        st.error(f"Erro ao listar backups: {str(e)}")
        return []

def create_backup(config):
    """Cria um novo backup"""
    try:
        backup_dir = Path("./backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{config['name']}_{timestamp}.zip"
        backup_path = backup_dir / backup_name
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Backup do banco de dados
            if config['type'] in ['full_backup', 'database_only']:
                db_path = Path("church_media.db")
                if db_path.exists():
                    zipf.write(db_path, "database/church_media.db")
            
            # Backup de arquivos
            if config['type'] in ['full_backup', 'files_only']:
                # Adicionar arquivos da aplicação
                app_dir = Path("app")
                if app_dir.exists():
                    for file_path in app_dir.rglob("*"):
                        if file_path.is_file() and not file_path.name.endswith('.pyc'):
                            zipf.write(file_path, f"app/{file_path.relative_to(app_dir)}")
                
                # Incluir mídia se solicitado
                if config.get('include_media', False):
                    media_dir = Path("media")
                    if media_dir.exists():
                        for file_path in media_dir.rglob("*"):
                            if file_path.is_file():
                                zipf.write(file_path, f"media/{file_path.relative_to(media_dir)}")
            
            # Adicionar metadados
            metadata = {
                'created_at': datetime.now().isoformat(),
                'type': config['type'],
                'description': config.get('description', ''),
                'version': '1.0',
                'retention_days': config.get('retention_days', 30)
            }
            
            zipf.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        size_mb = backup_path.stat().st_size / (1024 * 1024)
        
        return {
            'success': True,
            'filename': backup_name,
            'size_mb': size_mb,
            'progress': 100
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def delete_backup(filename):
    """Exclui um backup"""
    try:
        backup_path = Path("./backups") / filename
        if backup_path.exists():
            backup_path.unlink()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao excluir backup: {str(e)}")
        return False

def verify_backup(filename):
    """Verifica a integridade de um backup"""
    try:
        backup_path = Path("./backups") / filename
        
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            # Testar integridade do arquivo ZIP
            bad_files = zipf.testzip()
            
            if bad_files:
                st.error(f"❌ Backup corrompido: {bad_files}")
                return False
            else:
                st.success("✅ Backup íntegro!")
                return True
                
    except Exception as e:
        st.error(f"❌ Erro na verificação: {str(e)}")
        return False

def restore_backup_file(config):
    """Restaura um backup"""
    try:
        # Criar backup de segurança se solicitado
        if config.get('create_backup_before', True):
            safety_backup = create_backup({
                'name': f"safety_backup_before_restore",
                'type': 'full_backup',
                'description': 'Backup de segurança antes da restauração'
            })
        
        backup_path = Path("./backups") / config['backup_file']
        
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            # Restaurar banco de dados
            if config.get('restore_database', True):
                try:
                    zipf.extract("database/church_media.db", ".")
                    # Mover para o local correto
                    shutil.move("database/church_media.db", "church_media.db")
                    os.rmdir("database")
                except KeyError:
                    pass  # Arquivo não existe no backup
            
            # Restaurar arquivos
            if config.get('restore_files', True):
                # Extrair arquivos da aplicação
                for member in zipf.namelist():
                    if member.startswith('app/'):
                        zipf.extract(member, ".")
        
        return {
            'success': True,
            'backup_created': config.get('create_backup_before', True),
            'backup_filename': safety_backup.get('filename') if config.get('create_backup_before', True) else None
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def cleanup_old_backups(days):
    """Remove backups antigos"""
    try:
        backup_dir = Path("./backups")
        if not backup_dir.exists():
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for backup_file in backup_dir.glob("*.zip"):
            if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                backup_file.unlink()
                deleted_count += 1
        
        return deleted_count
        
    except Exception as e:
        st.error(f"Erro na limpeza: {str(e)}")
        return 0

def load_backup_settings():
    """Carrega configurações de backup"""
    try:
        settings_file = Path("backup_settings.json")
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_backup_settings(settings):
    """Salva configurações de backup"""
    try:
        settings_file = Path("backup_settings.json")
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {str(e)}")
        return False

def verify_all_backups():
    """Verifica todos os backups"""
    backups = list_backups()
    verified_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, backup in enumerate(backups):
        status_text.text(f"Verificando {backup['name']}...")
        
        if verify_backup(backup['filename']):
            verified_count += 1
        
        progress_bar.progress((i + 1) / len(backups))
    
    status_text.text(f"✅ Verificação concluída: {verified_count}/{len(backups)} backups íntegros")

def download_backup(filename):
    """Prepara download de backup"""
    try:
        backup_path = Path("./backups") / filename
        if backup_path.exists():
            with open(backup_path, 'rb') as f:
                st.download_button(
                    label="📥 Download",
                    data=f.read(),
                    file_name=filename,
                    mime="application/zip"
                )
    except Exception as e:
        st.error(f"Erro no download: {str(e)}")

def export_backup_list(backups):
    """Exporta lista de backups para CSV"""
    try:
        df = pd.DataFrame([
            {
                'Nome': backup['name'],
                'Tipo': backup['type'],
                'Tamanho (MB)': round(backup['size'] / (1024*1024), 2),
                'Data Criação': backup['created_at'].strftime('%d/%m/%Y %H:%M'),
                'Verificado': 'Sim' if backup.get('verified') else 'Não'
            }
            for backup in backups
        ])
        
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="📊 Baixar Lista (CSV)",
            data=csv,
            file_name=f"lista_backups_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Erro na exportação: {str(e)}")

if __name__ == "__main__":
    show_backup_page()