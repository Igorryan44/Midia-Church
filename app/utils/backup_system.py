import streamlit as st
import json
import sqlite3
import zipfile
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from app.database.local_connection import db_manager
from app.utils.auth import get_current_user

class BackupSystem:
    """Sistema de backup e recuperação de dados"""
    
    BACKUP_DIR = "backups"
    
    @staticmethod
    def ensure_backup_directory():
        """Garante que o diretório de backup existe"""
        backup_path = Path(BackupSystem.BACKUP_DIR)
        backup_path.mkdir(exist_ok=True)
        return backup_path
    
    @staticmethod
    def create_full_backup(include_logs: bool = False) -> Dict:
        """Cria backup completo do sistema"""
        try:
            backup_path = BackupSystem.ensure_backup_directory()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_completo_{timestamp}.zip"
            backup_filepath = backup_path / backup_filename
            
            # Tabelas para backup
            tables_to_backup = [
                'users',
                'user_preferences', 
                'notifications',
                'notification_settings',
                'password_recovery_tokens',
                'user_sessions'
            ]
            
            if include_logs:
                tables_to_backup.extend([
                    'security_logs',
                    'login_attempts',
                    'active_sessions'
                ])
            
            backup_data = {
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'type': 'full_backup',
                    'include_logs': include_logs,
                    'tables': tables_to_backup
                },
                'data': {}
            }
            
            # Exportar dados de cada tabela
            for table in tables_to_backup:
                try:
                    data = db_manager.fetch_all(f"SELECT * FROM {table}")
                    backup_data['data'][table] = data or []
                except Exception as e:
                    st.warning(f"Aviso: Não foi possível fazer backup da tabela {table}: {e}")
                    backup_data['data'][table] = []
            
            # Criar arquivo ZIP
            with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Adicionar dados JSON
                json_data = json.dumps(backup_data, indent=2, ensure_ascii=False, default=str)
                zipf.writestr('backup_data.json', json_data)
                
                # Adicionar arquivos de configuração se existirem
                config_files = [
                    'app/config.py',
                    'requirements.txt',
                    '.streamlit/config.toml'
                ]
                
                for config_file in config_files:
                    if os.path.exists(config_file):
                        zipf.write(config_file, f"config/{os.path.basename(config_file)}")
            
            return {
                'success': True,
                'filename': backup_filename,
                'filepath': str(backup_filepath),
                'size': os.path.getsize(backup_filepath),
                'tables_count': len(tables_to_backup),
                'records_count': sum(len(data) for data in backup_data['data'].values())
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_incremental_backup(since_date: datetime = None) -> Dict:
        """Cria backup incremental (apenas dados modificados)"""
        try:
            if not since_date:
                since_date = datetime.now() - timedelta(days=1)
            
            backup_path = BackupSystem.ensure_backup_directory()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_incremental_{timestamp}.zip"
            backup_filepath = backup_path / backup_filename
            
            since_str = since_date.isoformat()
            
            # Tabelas com timestamps para backup incremental
            incremental_tables = {
                'users': 'created_at',
                'notifications': 'created_at',
                'security_logs': 'created_at',
                'login_attempts': 'created_at'
            }
            
            backup_data = {
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'type': 'incremental_backup',
                    'since_date': since_str,
                    'tables': list(incremental_tables.keys())
                },
                'data': {}
            }
            
            total_records = 0
            
            # Exportar dados modificados
            for table, timestamp_column in incremental_tables.items():
                try:
                    query = f"SELECT * FROM {table} WHERE {timestamp_column} > ?"
                    data = db_manager.fetch_all(query, (since_str,))
                    backup_data['data'][table] = data or []
                    total_records += len(data or [])
                except Exception as e:
                    st.warning(f"Aviso: Não foi possível fazer backup incremental da tabela {table}: {e}")
                    backup_data['data'][table] = []
            
            # Criar arquivo ZIP apenas se houver dados
            if total_records > 0:
                with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    json_data = json.dumps(backup_data, indent=2, ensure_ascii=False, default=str)
                    zipf.writestr('incremental_data.json', json_data)
                
                return {
                    'success': True,
                    'filename': backup_filename,
                    'filepath': str(backup_filepath),
                    'size': os.path.getsize(backup_filepath),
                    'records_count': total_records,
                    'since_date': since_str
                }
            else:
                return {
                    'success': True,
                    'message': 'Nenhum dado novo para backup incremental',
                    'records_count': 0
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def list_backups() -> List[Dict]:
        """Lista todos os backups disponíveis"""
        try:
            backup_path = BackupSystem.ensure_backup_directory()
            backups = []
            
            for backup_file in backup_path.glob("*.zip"):
                try:
                    stat = backup_file.stat()
                    
                    # Tentar extrair metadados do backup
                    metadata = BackupSystem.get_backup_metadata(str(backup_file))
                    
                    backup_info = {
                        'filename': backup_file.name,
                        'filepath': str(backup_file),
                        'size': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_ctime),
                        'modified_at': datetime.fromtimestamp(stat.st_mtime),
                        'metadata': metadata
                    }
                    
                    backups.append(backup_info)
                    
                except Exception as e:
                    st.warning(f"Erro ao processar backup {backup_file.name}: {e}")
            
            # Ordenar por data de criação (mais recente primeiro)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return backups
            
        except Exception as e:
            st.error(f"Erro ao listar backups: {e}")
            return []
    
    @staticmethod
    def get_backup_metadata(backup_filepath: str) -> Dict:
        """Obtém metadados de um arquivo de backup"""
        try:
            with zipfile.ZipFile(backup_filepath, 'r') as zipf:
                # Tentar ler metadados do backup_data.json
                if 'backup_data.json' in zipf.namelist():
                    with zipf.open('backup_data.json') as f:
                        data = json.load(f)
                        return data.get('metadata', {})
                
                # Tentar ler metadados do incremental_data.json
                elif 'incremental_data.json' in zipf.namelist():
                    with zipf.open('incremental_data.json') as f:
                        data = json.load(f)
                        return data.get('metadata', {})
                
                return {}
                
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def restore_backup(backup_filepath: str, restore_options: Dict = None) -> Dict:
        """Restaura dados de um backup"""
        try:
            if not os.path.exists(backup_filepath):
                return {'success': False, 'error': 'Arquivo de backup não encontrado'}
            
            restore_options = restore_options or {}
            
            with zipfile.ZipFile(backup_filepath, 'r') as zipf:
                # Determinar tipo de backup
                if 'backup_data.json' in zipf.namelist():
                    data_file = 'backup_data.json'
                elif 'incremental_data.json' in zipf.namelist():
                    data_file = 'incremental_data.json'
                else:
                    return {'success': False, 'error': 'Formato de backup inválido'}
                
                # Ler dados do backup
                with zipf.open(data_file) as f:
                    backup_data = json.load(f)
                
                metadata = backup_data.get('metadata', {})
                data = backup_data.get('data', {})
                
                # Confirmar restauração
                if not restore_options.get('confirmed', False):
                    return {
                        'success': False,
                        'requires_confirmation': True,
                        'metadata': metadata,
                        'tables': list(data.keys()),
                        'total_records': sum(len(table_data) for table_data in data.values())
                    }
                
                # Executar restauração
                restored_tables = []
                errors = []
                
                for table_name, table_data in data.items():
                    try:
                        if restore_options.get('tables') and table_name not in restore_options['tables']:
                            continue
                        
                        # Backup da tabela atual (se solicitado)
                        if restore_options.get('backup_current', True):
                            BackupSystem._backup_table_before_restore(table_name)
                        
                        # Restaurar dados
                        if restore_options.get('mode', 'replace') == 'replace':
                            # Limpar tabela e inserir dados
                            db_manager.execute_query(f"DELETE FROM {table_name}")
                            
                        # Inserir dados do backup
                        if table_data:
                            BackupSystem._insert_backup_data(table_name, table_data)
                        
                        restored_tables.append(table_name)
                        
                    except Exception as e:
                        errors.append(f"Erro ao restaurar tabela {table_name}: {str(e)}")
                
                return {
                    'success': len(errors) == 0,
                    'restored_tables': restored_tables,
                    'errors': errors,
                    'metadata': metadata
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _backup_table_before_restore(table_name: str):
        """Faz backup de uma tabela antes da restauração"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"pre_restore_{table_name}_{timestamp}.json"
            backup_path = BackupSystem.ensure_backup_directory() / "pre_restore"
            backup_path.mkdir(exist_ok=True)
            
            data = db_manager.fetch_all(f"SELECT * FROM {table_name}")
            
            with open(backup_path / backup_filename, 'w', encoding='utf-8') as f:
                json.dump(data or [], f, indent=2, ensure_ascii=False, default=str)
                
        except Exception as e:
            st.warning(f"Não foi possível fazer backup da tabela {table_name} antes da restauração: {e}")
    
    @staticmethod
    def _insert_backup_data(table_name: str, data: List[Dict]):
        """Insere dados do backup em uma tabela"""
        if not data:
            return
        
        # Obter colunas da primeira linha
        columns = list(data[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        columns_str = ', '.join(columns)
        
        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        for row in data:
            values = [row.get(col) for col in columns]
            db_manager.execute_query(query, values)
    
    @staticmethod
    def delete_backup(backup_filepath: str) -> bool:
        """Deleta um arquivo de backup"""
        try:
            if os.path.exists(backup_filepath):
                os.remove(backup_filepath)
                return True
            return False
        except Exception as e:
            st.error(f"Erro ao deletar backup: {e}")
            return False
    
    @staticmethod
    def cleanup_old_backups(days: int = 30) -> Dict:
        """Remove backups antigos"""
        try:
            backup_path = BackupSystem.ensure_backup_directory()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            deleted_files = []
            errors = []
            
            for backup_file in backup_path.glob("*.zip"):
                try:
                    file_date = datetime.fromtimestamp(backup_file.stat().st_ctime)
                    
                    if file_date < cutoff_date:
                        backup_file.unlink()
                        deleted_files.append(backup_file.name)
                        
                except Exception as e:
                    errors.append(f"Erro ao deletar {backup_file.name}: {str(e)}")
            
            return {
                'success': len(errors) == 0,
                'deleted_files': deleted_files,
                'errors': errors,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_backup_statistics() -> Dict:
        """Obtém estatísticas dos backups"""
        try:
            backups = BackupSystem.list_backups()
            
            if not backups:
                return {
                    'total_backups': 0,
                    'total_size': 0,
                    'oldest_backup': None,
                    'newest_backup': None,
                    'backup_types': {}
                }
            
            total_size = sum(backup['size'] for backup in backups)
            backup_types = {}
            
            for backup in backups:
                backup_type = backup.get('metadata', {}).get('type', 'unknown')
                backup_types[backup_type] = backup_types.get(backup_type, 0) + 1
            
            return {
                'total_backups': len(backups),
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'oldest_backup': min(backups, key=lambda x: x['created_at'])['created_at'],
                'newest_backup': max(backups, key=lambda x: x['created_at'])['created_at'],
                'backup_types': backup_types
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def schedule_automatic_backup(frequency: str = 'daily') -> bool:
        """Configura backup automático (placeholder para implementação futura)"""
        # Esta função seria implementada com um sistema de agendamento
        # como APScheduler ou similar
        try:
            # Salvar configuração de backup automático
            config = {
                'enabled': True,
                'frequency': frequency,
                'last_backup': datetime.now().isoformat(),
                'next_backup': (datetime.now() + timedelta(days=1)).isoformat()
            }
            
            # Em uma implementação real, isso seria salvo no banco de dados
            # ou arquivo de configuração
            
            return True
            
        except Exception as e:
            st.error(f"Erro ao configurar backup automático: {e}")
            return False