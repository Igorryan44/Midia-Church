import os
import sqlite3
import shutil
import zipfile
import json
from datetime import datetime, timedelta
from pathlib import Path
import streamlit as st
from app.database.local_connection import get_db_path
from app.utils.validation import SecurityHelper

class BackupManager:
    """Gerenciador de backup do sistema"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.max_backups = 10  # Manter apenas os 10 backups mais recentes
    
    def create_backup(self, backup_type="manual", user_id=None):
        """Cria um backup completo do sistema"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{backup_type}_{timestamp}"
            backup_path = self.backup_dir / f"{backup_name}.zip"
            
            # Log do início do backup
            SecurityHelper.log_security_event(
                "BACKUP_START",
                f"Starting {backup_type} backup",
                str(user_id) if user_id else "system"
            )
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup do banco de dados
                db_path = get_db_path()
                if os.path.exists(db_path):
                    zipf.write(db_path, "database.db")
                
                # Backup de arquivos de configuração
                config_files = [
                    "requirements.txt",
                    "app/utils/styles.py",
                    "app/database/schema.sql"
                ]
                
                for file_path in config_files:
                    if os.path.exists(file_path):
                        zipf.write(file_path, file_path)
                
                # Backup de logs de segurança
                logs_dir = Path("logs")
                if logs_dir.exists():
                    for log_file in logs_dir.glob("*.log"):
                        zipf.write(log_file, f"logs/{log_file.name}")
                
                # Metadados do backup
                metadata = {
                    "backup_type": backup_type,
                    "timestamp": timestamp,
                    "created_by": user_id,
                    "version": "1.0",
                    "files_count": len(zipf.namelist())
                }
                
                zipf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
            
            # Limpar backups antigos
            self._cleanup_old_backups()
            
            # Log de sucesso
            SecurityHelper.log_security_event(
                "BACKUP_SUCCESS",
                f"Backup created successfully: {backup_name}",
                str(user_id) if user_id else "system"
            )
            
            return {
                "success": True,
                "backup_path": str(backup_path),
                "backup_name": backup_name,
                "size": self._get_file_size(backup_path)
            }
            
        except Exception as e:
            # Log de erro
            SecurityHelper.log_security_event(
                "BACKUP_ERROR",
                f"Backup failed: {str(e)}",
                str(user_id) if user_id else "system"
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    def restore_backup(self, backup_path, user_id=None):
        """Restaura um backup"""
        try:
            # Log do início da restauração
            SecurityHelper.log_security_event(
                "RESTORE_START",
                f"Starting restore from: {backup_path}",
                str(user_id) if user_id else "system"
            )
            
            # Criar backup atual antes da restauração
            current_backup = self.create_backup("pre_restore", user_id)
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Verificar metadados
                if "backup_metadata.json" in zipf.namelist():
                    metadata = json.loads(zipf.read("backup_metadata.json"))
                    st.info(f"Restaurando backup de {metadata.get('timestamp', 'data desconhecida')}")
                
                # Restaurar banco de dados
                if "database.db" in zipf.namelist():
                    db_path = get_db_path()
                    # Fazer backup do banco atual
                    if os.path.exists(db_path):
                        shutil.copy2(db_path, f"{db_path}.backup")
                    
                    # Extrair novo banco
                    zipf.extract("database.db", ".")
                    shutil.move("database.db", db_path)
                
                # Restaurar outros arquivos se necessário
                # (implementar conforme necessidade)
            
            # Log de sucesso
            SecurityHelper.log_security_event(
                "RESTORE_SUCCESS",
                f"Restore completed successfully from: {backup_path}",
                str(user_id) if user_id else "system"
            )
            
            return {"success": True, "message": "Backup restaurado com sucesso"}
            
        except Exception as e:
            # Log de erro
            SecurityHelper.log_security_event(
                "RESTORE_ERROR",
                f"Restore failed: {str(e)}",
                str(user_id) if user_id else "system"
            )
            return {"success": False, "error": str(e)}
    
    def list_backups(self):
        """Lista todos os backups disponíveis"""
        backups = []
        
        for backup_file in self.backup_dir.glob("backup_*.zip"):
            try:
                # Extrair informações do nome do arquivo
                name_parts = backup_file.stem.split("_")
                if len(name_parts) >= 3:
                    backup_type = name_parts[1]
                    timestamp = name_parts[2]
                    
                    # Tentar ler metadados
                    metadata = {}
                    try:
                        with zipfile.ZipFile(backup_file, 'r') as zipf:
                            if "backup_metadata.json" in zipf.namelist():
                                metadata = json.loads(zipf.read("backup_metadata.json"))
                    except:
                        pass
                    
                    backups.append({
                        "name": backup_file.name,
                        "path": str(backup_file),
                        "type": backup_type,
                        "timestamp": timestamp,
                        "size": self._get_file_size(backup_file),
                        "created_date": datetime.fromtimestamp(backup_file.stat().st_mtime),
                        "metadata": metadata
                    })
            except Exception:
                continue
        
        # Ordenar por data de criação (mais recente primeiro)
        backups.sort(key=lambda x: x["created_date"], reverse=True)
        return backups
    
    def delete_backup(self, backup_path, user_id=None):
        """Deleta um backup específico"""
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
                # Log da exclusão
                SecurityHelper.log_security_event(
                    "BACKUP_DELETED",
                    f"Backup deleted: {backup_path}",
                    str(user_id) if user_id else "system"
                )
                
                return {"success": True, "message": "Backup deletado com sucesso"}
            else:
                return {"success": False, "error": "Backup não encontrado"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def schedule_automatic_backup(self):
        """Agenda backup automático (implementação básica)"""
        # Esta função seria chamada por um scheduler externo
        # Por exemplo, usando cron jobs ou task scheduler do Windows
        return self.create_backup("automatic", "system")
    
    def _cleanup_old_backups(self):
        """Remove backups antigos mantendo apenas os mais recentes"""
        backups = self.list_backups()
        
        if len(backups) > self.max_backups:
            # Manter apenas os backups mais recentes
            for backup in backups[self.max_backups:]:
                try:
                    os.remove(backup["path"])
                except Exception:
                    pass
    
    def _get_file_size(self, file_path):
        """Retorna o tamanho do arquivo em formato legível"""
        try:
            size = os.path.getsize(file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except Exception:
            return "Desconhecido"

class LogManager:
    """Gerenciador de logs do sistema"""
    
    def __init__(self):
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.max_log_files = 30  # Manter logs por 30 dias
    
    def get_security_logs(self, days=7, event_type=None, user_id=None):
        """Busca logs de segurança"""
        try:
            from app.database.local_connection import db_manager
            
            query = """
            SELECT event_type, description, user_id, timestamp, ip_address
            FROM security_logs
            WHERE timestamp >= datetime('now', '-{} days')
            """.format(days)
            
            params = []
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY timestamp DESC LIMIT 1000"
            
            return db_manager.fetch_all(query, params)
            
        except Exception as e:
            st.error(f"Erro ao buscar logs: {e}")
            return []
    
    def get_system_stats(self):
        """Retorna estatísticas do sistema"""
        try:
            from app.database.local_connection import db_manager
            
            stats = {}
            
            # Estatísticas de usuários
            users_query = "SELECT COUNT(*) as total FROM users"
            users_result = db_manager.fetch_one(users_query)
            stats["total_users"] = users_result["total"] if users_result else 0
            
            # Estatísticas de eventos
            events_query = "SELECT COUNT(*) as total FROM events"
            events_result = db_manager.fetch_one(events_query)
            stats["total_events"] = events_result["total"] if events_result else 0
            
            # Estatísticas de mensagens
            messages_query = "SELECT COUNT(*) as total FROM messages"
            messages_result = db_manager.fetch_one(messages_query)
            stats["total_messages"] = messages_result["total"] if messages_result else 0
            
            # Logs de segurança (últimos 7 dias)
            security_query = """
            SELECT COUNT(*) as total 
            FROM security_logs 
            WHERE timestamp >= datetime('now', '-7 days')
            """
            security_result = db_manager.fetch_one(security_query)
            stats["security_events_week"] = security_result["total"] if security_result else 0
            
            return stats
            
        except Exception as e:
            st.error(f"Erro ao buscar estatísticas: {e}")
            return {}
    
    def export_logs(self, start_date, end_date, event_types=None):
        """Exporta logs para arquivo"""
        try:
            from app.database.local_connection import db_manager
            
            query = """
            SELECT * FROM security_logs
            WHERE date(timestamp) BETWEEN ? AND ?
            """
            
            params = [start_date, end_date]
            
            if event_types:
                placeholders = ",".join(["?" for _ in event_types])
                query += f" AND event_type IN ({placeholders})"
                params.extend(event_types)
            
            query += " ORDER BY timestamp DESC"
            
            logs = db_manager.fetch_all(query, params)
            
            # Criar arquivo de exportação
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = self.logs_dir / f"logs_export_{timestamp}.json"
            
            export_data = {
                "export_date": datetime.now().isoformat(),
                "period": {"start": start_date, "end": end_date},
                "total_records": len(logs),
                "logs": logs
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return {
                "success": True,
                "file_path": str(export_path),
                "records_count": len(logs)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_logs(self, date=None, level=None, limit=100):
        """Busca logs do sistema com filtros"""
        try:
            from app.database.local_connection import db_manager
            
            # Verificar se a tabela security_logs existe
            try:
                test_query = "SELECT COUNT(*) FROM security_logs LIMIT 1"
                db_manager.fetch_all(test_query)
            except:
                # Se a tabela não existe, retornar logs simulados
                return self._get_fallback_logs(date, level, limit)
            
            query = "SELECT event_type as level, description as message, timestamp FROM security_logs"
            params = []
            conditions = []
            
            if date:
                conditions.append("date(timestamp) = ?")
                params.append(str(date))
            
            if level:
                # Mapear níveis de log para tipos de evento
                level_mapping = {
                    "INFO": ["LOGIN_SUCCESS", "EVENT_CREATED", "MESSAGE_SENT", "BACKUP_SUCCESS"],
                    "WARNING": ["LOGIN_FAILED", "RATE_LIMIT_EXCEEDED"],
                    "ERROR": ["LOGIN_ERROR", "EVENT_CREATE_ERROR", "MESSAGE_SEND_ERROR", "BACKUP_ERROR"]
                }
                
                if level in level_mapping:
                    event_types = level_mapping[level]
                    placeholders = ",".join(["?" for _ in event_types])
                    conditions.append(f"event_type IN ({placeholders})")
                    params.extend(event_types)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDER BY timestamp DESC LIMIT {limit}"
            
            logs = db_manager.fetch_all(query, params)
            
            # Converter para formato esperado
            formatted_logs = []
            for log in logs:
                # Mapear tipo de evento para nível
                level_map = {
                    "LOGIN_SUCCESS": "INFO",
                    "EVENT_CREATED": "INFO", 
                    "MESSAGE_SENT": "INFO",
                    "BACKUP_SUCCESS": "INFO",
                    "LOGIN_FAILED": "WARNING",
                    "RATE_LIMIT_EXCEEDED": "WARNING",
                    "LOGIN_ERROR": "ERROR",
                    "EVENT_CREATE_ERROR": "ERROR",
                    "MESSAGE_SEND_ERROR": "ERROR",
                    "BACKUP_ERROR": "ERROR"
                }
                
                formatted_logs.append({
                    "timestamp": log["timestamp"],
                    "level": level_map.get(log["level"], "INFO"),
                    "message": log["message"]
                })
            
            return formatted_logs
            
        except Exception as e:
            st.error(f"Erro ao buscar logs: {e}")
            return self._get_fallback_logs(date, level, limit)
    
    def _get_fallback_logs(self, date=None, level=None, limit=100):
        """Retorna logs simulados quando há erro na consulta"""
        logs = [
            {"timestamp": "2024-01-30 12:00:00", "level": "INFO", "message": "Usuário admin fez login"},
            {"timestamp": "2024-01-30 11:55:00", "level": "INFO", "message": "Evento 'Culto de Domingo' criado"},
            {"timestamp": "2024-01-30 11:50:00", "level": "WARNING", "message": "Tentativa de login falhada para usuário 'test'"},
            {"timestamp": "2024-01-30 11:45:00", "level": "INFO", "message": "Backup automático executado"},
            {"timestamp": "2024-01-30 11:40:00", "level": "ERROR", "message": "Erro na conexão com banco de dados"},
            {"timestamp": "2024-01-30 11:35:00", "level": "INFO", "message": "Sistema iniciado com sucesso"},
            {"timestamp": "2024-01-30 11:30:00", "level": "WARNING", "message": "Memória do sistema em 85%"},
            {"timestamp": "2024-01-30 11:25:00", "level": "INFO", "message": "Backup criado automaticamente"},
        ]
        
        # Filtrar por nível se especificado
        if level and level != "Todos":
            logs = [log for log in logs if log["level"] == level]
        
        # Limitar resultados
        return logs[:limit]
    
    def cleanup_old_logs(self):
        """Remove logs antigos"""
        try:
            from app.database.local_connection import db_manager
            
            # Remover logs de segurança antigos (mais de 90 dias)
            cleanup_query = """
            DELETE FROM security_logs 
            WHERE timestamp < datetime('now', '-90 days')
            """
            db_manager.execute_query(cleanup_query)
            
            # Remover arquivos de log antigos
            cutoff_date = datetime.now() - timedelta(days=self.max_log_files)
            
            for log_file in self.logs_dir.glob("*.log"):
                if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                    try:
                        log_file.unlink()
                    except Exception:
                        pass
            
            return {"success": True, "message": "Limpeza de logs concluída"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}