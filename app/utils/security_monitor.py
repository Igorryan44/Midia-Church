import streamlit as st
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.database.local_connection import db_manager

class SecurityMonitor:
    """Sistema avançado de monitoramento de segurança"""
    
    @staticmethod
    def create_security_tables():
        """Cria tabelas para monitoramento de segurança"""
        try:
            # Tabela de logs de segurança
            security_logs_query = """
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                user_id TEXT NULL,
                username TEXT NULL,
                ip_address TEXT NULL,
                user_agent TEXT NULL,
                event_data TEXT NULL,
                severity TEXT DEFAULT 'INFO',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT NULL
            )
            """
            db_manager.execute_query(security_logs_query)
            
            # Tabela de tentativas de login
            login_attempts_query = """
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                ip_address TEXT NULL,
                success INTEGER DEFAULT 0,
                failure_reason TEXT NULL,
                user_agent TEXT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
            db_manager.execute_query(login_attempts_query)
            
            # Tabela de sessões ativas
            active_sessions_query = """
            CREATE TABLE IF NOT EXISTS active_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL UNIQUE,
                ip_address TEXT NULL,
                user_agent TEXT NULL,
                last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
            db_manager.execute_query(active_sessions_query)
            
            # Índices para performance (com tratamento de erro)
            try:
                db_manager.execute_query("CREATE INDEX IF NOT EXISTS idx_security_logs_event_type ON security_logs(event_type)")
                db_manager.execute_query("CREATE INDEX IF NOT EXISTS idx_security_logs_user_id ON security_logs(user_id)")
                db_manager.execute_query("CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username)")
                db_manager.execute_query("CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address)")
                db_manager.execute_query("CREATE INDEX IF NOT EXISTS idx_active_sessions_user_id ON active_sessions(user_id)")
            except Exception as idx_error:
                # Ignorar erros de índices para não interromper a aplicação
                pass
            
            return True
        except Exception as e:
            st.error(f"Erro ao criar tabelas de segurança: {str(e)}")
            return False
    
    @staticmethod
    def log_security_event(event_type: str, description: str, severity: str = "INFO", 
                          user_id: str = None, additional_data: Dict = None):
        """Registra evento de segurança"""
        try:
            # Obter dados do usuário atual da sessão
            current_user = st.session_state.get('user', {})
            if not user_id and current_user:
                user_id = current_user.get('id')
            
            username = current_user.get('username') if current_user else None
            
            # Obter informações da sessão (simulado)
            ip_address = st.session_state.get('client_ip', 'unknown')
            user_agent = st.session_state.get('user_agent', 'unknown')
            session_id = st.session_state.get('session_id', 'unknown')
            
            event_data = {
                'description': description,
                'timestamp': datetime.now().isoformat(),
                'additional_data': additional_data or {}
            }
            
            query = """
            INSERT INTO security_logs 
            (event_type, user_id, username, ip_address, user_agent, event_data, severity, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            db_manager.execute_query(query, (
                event_type, user_id, username, ip_address, 
                user_agent, json.dumps(event_data), severity, session_id
            ))
            
            return True
        except Exception as e:
            # Não mostrar erro para não interromper fluxo
            return False
    
    @staticmethod
    def log_login_attempt(username: str, success: bool, failure_reason: str = None):
        """Registra tentativa de login"""
        try:
            ip_address = st.session_state.get('client_ip', 'unknown')
            user_agent = st.session_state.get('user_agent', 'unknown')
            
            query = """
            INSERT INTO login_attempts (username, ip_address, success, failure_reason, user_agent)
            VALUES (?, ?, ?, ?, ?)
            """
            
            db_manager.execute_query(query, (username, ip_address, int(success), failure_reason, user_agent))
            
            # Log de segurança correspondente
            event_type = "LOGIN_SUCCESS" if success else "LOGIN_FAILED"
            severity = "INFO" if success else "WARNING"
            description = f"Login {'bem-sucedido' if success else 'falhado'} para usuário: {username}"
            
            if failure_reason:
                description += f" - Motivo: {failure_reason}"
            
            SecurityMonitor.log_security_event(event_type, description, severity)
            
            return True
        except Exception as e:
            return False
    
    @staticmethod
    def check_suspicious_activity(username: str, time_window_minutes: int = 15) -> Dict:
        """Verifica atividade suspeita"""
        try:
            # Verificar múltiplas tentativas de login falhadas
            since_time = (datetime.now() - timedelta(minutes=time_window_minutes)).isoformat()
            
            failed_attempts_query = """
            SELECT COUNT(*) as count, ip_address
            FROM login_attempts 
            WHERE username = ? AND success = 0 AND created_at > ?
            GROUP BY ip_address
            """
            
            failed_attempts = db_manager.fetch_all(failed_attempts_query, (username, since_time))
            
            suspicious_indicators = {
                'multiple_failed_logins': False,
                'different_ips': False,
                'risk_level': 'LOW',
                'details': []
            }
            
            if failed_attempts:
                total_failures = sum(attempt['count'] for attempt in failed_attempts)
                unique_ips = len(failed_attempts)
                
                if total_failures >= 5:
                    suspicious_indicators['multiple_failed_logins'] = True
                    suspicious_indicators['risk_level'] = 'HIGH'
                    suspicious_indicators['details'].append(f"{total_failures} tentativas falhadas em {time_window_minutes} minutos")
                
                if unique_ips >= 3:
                    suspicious_indicators['different_ips'] = True
                    suspicious_indicators['risk_level'] = 'HIGH'
                    suspicious_indicators['details'].append(f"Tentativas de {unique_ips} IPs diferentes")
                
                elif total_failures >= 3:
                    suspicious_indicators['risk_level'] = 'MEDIUM'
            
            return suspicious_indicators
            
        except Exception as e:
            return {'error': str(e), 'risk_level': 'UNKNOWN'}
    
    @staticmethod
    def get_security_dashboard_data() -> Dict:
        """Obtém dados para dashboard de segurança"""
        try:
            # Últimas 24 horas
            since_24h = (datetime.now() - timedelta(hours=24)).isoformat()
            
            # Total de eventos por tipo
            events_query = """
            SELECT event_type, COUNT(*) as count, severity
            FROM security_logs 
            WHERE created_at > ?
            GROUP BY event_type, severity
            ORDER BY count DESC
            """
            events_data = db_manager.fetch_all(events_query, (since_24h,))
            
            # Tentativas de login
            login_stats_query = """
            SELECT 
                COUNT(*) as total_attempts,
                SUM(success) as successful_logins,
                COUNT(*) - SUM(success) as failed_attempts
            FROM login_attempts 
            WHERE created_at > ?
            """
            login_stats = db_manager.fetch_all(login_stats_query, (since_24h,))
            
            # Usuários mais ativos
            active_users_query = """
            SELECT username, COUNT(*) as activity_count
            FROM security_logs 
            WHERE created_at > ? AND username IS NOT NULL
            GROUP BY username
            ORDER BY activity_count DESC
            LIMIT 10
            """
            active_users = db_manager.fetch_all(active_users_query, (since_24h,))
            
            # IPs suspeitos
            suspicious_ips_query = """
            SELECT ip_address, COUNT(*) as failed_count
            FROM login_attempts 
            WHERE created_at > ? AND success = 0
            GROUP BY ip_address
            HAVING failed_count >= 3
            ORDER BY failed_count DESC
            """
            suspicious_ips = db_manager.fetch_all(suspicious_ips_query, (since_24h,))
            
            return {
                'events': events_data or [],
                'login_stats': login_stats[0] if login_stats else {},
                'active_users': active_users or [],
                'suspicious_ips': suspicious_ips or [],
                'period': '24 horas'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def render_security_dashboard():
        """Renderiza dashboard de segurança"""
        st.header("🛡️ Dashboard de Segurança")
        
        # Verificar se usuário é admin
        current_user = get_current_user()
        if not current_user or current_user.get('role') != 'admin':
            st.error("🚫 Acesso restrito a administradores")
            return
        
        # Obter dados
        data = SecurityMonitor.get_security_dashboard_data()
        
        if 'error' in data:
            st.error(f"Erro ao carregar dados: {data['error']}")
            return
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        login_stats = data.get('login_stats', {})
        
        with col1:
            st.metric(
                "Total de Tentativas",
                login_stats.get('total_attempts', 0),
                help="Tentativas de login nas últimas 24h"
            )
        
        with col2:
            st.metric(
                "Logins Bem-sucedidos",
                login_stats.get('successful_logins', 0),
                help="Logins realizados com sucesso"
            )
        
        with col3:
            st.metric(
                "Tentativas Falhadas",
                login_stats.get('failed_attempts', 0),
                help="Tentativas de login que falharam"
            )
        
        with col4:
            success_rate = 0
            if login_stats.get('total_attempts', 0) > 0:
                success_rate = (login_stats.get('successful_logins', 0) / login_stats.get('total_attempts', 1)) * 100
            st.metric(
                "Taxa de Sucesso",
                f"{success_rate:.1f}%",
                help="Porcentagem de logins bem-sucedidos"
            )
        
        # Gráficos e tabelas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Eventos de Segurança")
            events = data.get('events', [])
            if events:
                import pandas as pd
                df_events = pd.DataFrame(events)
                st.dataframe(df_events, use_container_width=True)
            else:
                st.info("Nenhum evento registrado nas últimas 24h")
        
        with col2:
            st.subheader("👥 Usuários Mais Ativos")
            active_users = data.get('active_users', [])
            if active_users:
                import pandas as pd
                df_users = pd.DataFrame(active_users)
                st.dataframe(df_users, use_container_width=True)
            else:
                st.info("Nenhuma atividade registrada")
        
        # IPs suspeitos
        st.subheader("🚨 IPs Suspeitos")
        suspicious_ips = data.get('suspicious_ips', [])
        if suspicious_ips:
            import pandas as pd
            df_ips = pd.DataFrame(suspicious_ips)
            st.dataframe(df_ips, use_container_width=True)
            
            if len(suspicious_ips) > 0:
                st.warning(f"⚠️ {len(suspicious_ips)} IP(s) com atividade suspeita detectada!")
        else:
            st.success("✅ Nenhuma atividade suspeita detectada")
        
        # Ações de segurança
        st.subheader("🔧 Ações de Segurança")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🧹 Limpar Logs Antigos", help="Remove logs com mais de 30 dias"):
                SecurityMonitor.cleanup_old_logs()
                st.success("Logs antigos removidos!")
                st.rerun()
        
        with col2:
            if st.button("📊 Exportar Relatório", help="Gera relatório de segurança"):
                report = SecurityMonitor.generate_security_report()
                st.download_button(
                    "📥 Baixar Relatório",
                    report,
                    file_name=f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col3:
            if st.button("🔄 Atualizar Dados", help="Recarrega os dados do dashboard"):
                st.rerun()
    
    @staticmethod
    def cleanup_old_logs(days: int = 30):
        """Remove logs antigos"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Limpar logs de segurança
            db_manager.execute_query("DELETE FROM security_logs WHERE created_at < ?", (cutoff_date,))
            
            # Limpar tentativas de login antigas
            db_manager.execute_query("DELETE FROM login_attempts WHERE created_at < ?", (cutoff_date,))
            
            return True
        except Exception as e:
            st.error(f"Erro ao limpar logs: {e}")
            return False
    
    @staticmethod
    def generate_security_report() -> str:
        """Gera relatório de segurança em JSON"""
        try:
            data = SecurityMonitor.get_security_dashboard_data()
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'period': data.get('period', '24 horas'),
                'summary': data.get('login_stats', {}),
                'events': data.get('events', []),
                'active_users': data.get('active_users', []),
                'suspicious_ips': data.get('suspicious_ips', []),
                'recommendations': SecurityMonitor.get_security_recommendations(data)
            }
            
            return json.dumps(report, indent=2, ensure_ascii=False)
        except Exception as e:
            return json.dumps({'error': str(e)}, indent=2)
    
    @staticmethod
    def get_security_recommendations(data: Dict) -> List[str]:
        """Gera recomendações de segurança baseadas nos dados"""
        recommendations = []
        
        login_stats = data.get('login_stats', {})
        suspicious_ips = data.get('suspicious_ips', [])
        
        # Verificar taxa de falhas
        if login_stats.get('total_attempts', 0) > 0:
            failure_rate = (login_stats.get('failed_attempts', 0) / login_stats.get('total_attempts', 1)) * 100
            
            if failure_rate > 30:
                recommendations.append("Alta taxa de falhas de login detectada. Considere implementar CAPTCHA.")
            
            if failure_rate > 50:
                recommendations.append("Taxa crítica de falhas. Verifique possíveis ataques de força bruta.")
        
        # Verificar IPs suspeitos
        if len(suspicious_ips) > 0:
            recommendations.append(f"{len(suspicious_ips)} IP(s) suspeito(s) detectado(s). Considere bloqueio temporário.")
        
        if len(suspicious_ips) > 5:
            recommendations.append("Múltiplos IPs suspeitos. Possível ataque coordenado.")
        
        # Recomendações gerais
        if not recommendations:
            recommendations.append("Sistema operando normalmente. Continue monitorando.")
        
        return recommendations