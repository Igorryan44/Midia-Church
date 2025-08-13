"""
Sistema de Monitoramento e Analytics Melhorado
Implementa métricas detalhadas, alertas e dashboards de performance
"""

import logging
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import streamlit as st
from collections import defaultdict, deque
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class Alert:
    """Estrutura de alerta"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Metric:
    """Estrutura de métrica"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}

class MetricsCollector:
    """Coletor de métricas do sistema"""
    
    def __init__(self):
        self.metrics = defaultdict(deque)
        self.max_history = 1000  # Máximo de pontos por métrica
        self.collection_interval = 30  # segundos
        self.collecting = False
        self._lock = threading.Lock()
    
    def start_collection(self):
        """Inicia coleta automática de métricas"""
        if self.collecting:
            return
        
        self.collecting = True
        
        def collect_system_metrics():
            while self.collecting:
                try:
                    self._collect_system_metrics()
                    time.sleep(self.collection_interval)
                except Exception as e:
                    logger.error(f"Erro na coleta de métricas: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=collect_system_metrics, daemon=True)
        thread.start()
        logger.info("Coleta de métricas iniciada")
    
    def stop_collection(self):
        """Para coleta de métricas"""
        self.collecting = False
        logger.info("Coleta de métricas parada")
    
    def _collect_system_metrics(self):
        """Coleta métricas do sistema"""
        now = datetime.now()
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        self.add_metric("system.cpu.usage", cpu_percent, MetricType.GAUGE, now)
        
        # Memória
        memory = psutil.virtual_memory()
        self.add_metric("system.memory.usage", memory.percent, MetricType.GAUGE, now)
        self.add_metric("system.memory.available", memory.available / (1024**3), MetricType.GAUGE, now)
        
        # Disco (compatível com Windows e Linux)
        try:
            import os
            if os.name == 'nt':  # Windows
                disk = psutil.disk_usage('C:')
            else:  # Linux/Unix
                disk = psutil.disk_usage('/')
            self.add_metric("system.disk.usage", disk.percent, MetricType.GAUGE, now)
            self.add_metric("system.disk.free", disk.free / (1024**3), MetricType.GAUGE, now)
        except Exception as e:
            logger.warning(f"Erro ao coletar métricas de disco: {e}")
        
        # Rede
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                self.add_metric("system.network.bytes_sent", net_io.bytes_sent, MetricType.COUNTER, now)
                self.add_metric("system.network.bytes_recv", net_io.bytes_recv, MetricType.COUNTER, now)
        except Exception as e:
            logger.warning(f"Erro ao coletar métricas de rede: {e}")
        
        # Processos
        process_count = len(psutil.pids())
        self.add_metric("system.processes.count", process_count, MetricType.GAUGE, now)
    
    def add_metric(self, name: str, value: float, metric_type: MetricType, 
                   timestamp: Optional[datetime] = None, tags: Optional[Dict[str, str]] = None):
        """Adiciona métrica"""
        if timestamp is None:
            timestamp = datetime.now()
        
        metric = Metric(name, metric_type, value, timestamp, tags)
        
        with self._lock:
            self.metrics[name].append(metric)
            
            # Limitar histórico
            if len(self.metrics[name]) > self.max_history:
                self.metrics[name].popleft()
    
    def get_metric_history(self, name: str, hours: int = 24) -> List[Metric]:
        """Obtém histórico de métrica"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            return [
                metric for metric in self.metrics[name]
                if metric.timestamp >= cutoff
            ]
    
    def get_latest_metrics(self) -> Dict[str, Metric]:
        """Obtém últimas métricas"""
        latest = {}
        
        with self._lock:
            for name, metric_deque in self.metrics.items():
                if metric_deque:
                    latest[name] = metric_deque[-1]
        
        return latest
    
    def get_metric_summary(self, name: str, hours: int = 24) -> Dict[str, float]:
        """Obtém resumo estatístico de métrica"""
        history = self.get_metric_history(name, hours)
        
        if not history:
            return {}
        
        values = [m.value for m in history]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'current': values[-1] if values else 0
        }

class AlertManager:
    """Gerenciador de alertas"""
    
    def __init__(self):
        self.alerts = []
        self.rules = []
        self.max_alerts = 500
        self._lock = threading.Lock()
    
    def add_alert_rule(self, name: str, condition: Callable[[Dict[str, Metric]], bool],
                      level: AlertLevel, title: str, message: str):
        """Adiciona regra de alerta"""
        rule = {
            'name': name,
            'condition': condition,
            'level': level,
            'title': title,
            'message': message,
            'last_triggered': None
        }
        
        self.rules.append(rule)
        logger.info(f"Regra de alerta adicionada: {name}")
    
    def check_alerts(self, metrics: Dict[str, Metric]):
        """Verifica regras de alerta"""
        for rule in self.rules:
            try:
                if rule['condition'](metrics):
                    # Evitar spam de alertas (cooldown de 5 minutos)
                    if (rule['last_triggered'] and 
                        datetime.now() - rule['last_triggered'] < timedelta(minutes=5)):
                        continue
                    
                    alert = Alert(
                        id=f"alert_{int(time.time() * 1000)}",
                        level=rule['level'],
                        title=rule['title'],
                        message=rule['message'],
                        timestamp=datetime.now(),
                        source=rule['name']
                    )
                    
                    self.add_alert(alert)
                    rule['last_triggered'] = datetime.now()
                    
            except Exception as e:
                logger.error(f"Erro ao verificar regra {rule['name']}: {e}")
    
    def add_alert(self, alert: Alert):
        """Adiciona alerta"""
        with self._lock:
            self.alerts.append(alert)
            
            # Limitar número de alertas
            if len(self.alerts) > self.max_alerts:
                self.alerts.pop(0)
        
        logger.warning(f"Alerta gerado: {alert.title}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Obtém alertas ativos (não resolvidos)"""
        with self._lock:
            return [alert for alert in self.alerts if not alert.resolved]
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Obtém alertas recentes"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            return [
                alert for alert in self.alerts
                if alert.timestamp >= cutoff
            ]
    
    def resolve_alert(self, alert_id: str):
        """Resolve alerta"""
        with self._lock:
            for alert in self.alerts:
                if alert.id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    logger.info(f"Alerta resolvido: {alert_id}")
                    break

class PerformanceMonitor:
    """Monitor de performance da aplicação"""
    
    def __init__(self):
        self.request_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.feature_usage = defaultdict(int)
        self.user_sessions = {}
        self._lock = threading.Lock()
    
    def record_request(self, endpoint: str, duration: float, status_code: int = 200):
        """Registra tempo de requisição"""
        with self._lock:
            self.request_times.append({
                'endpoint': endpoint,
                'duration': duration,
                'status_code': status_code,
                'timestamp': datetime.now()
            })
            
            if status_code >= 400:
                self.error_counts[f"{endpoint}_{status_code}"] += 1
    
    def record_feature_usage(self, feature: str, user_id: Optional[str] = None):
        """Registra uso de funcionalidade"""
        with self._lock:
            self.feature_usage[feature] += 1
            
            if user_id:
                if user_id not in self.user_sessions:
                    self.user_sessions[user_id] = {
                        'start_time': datetime.now(),
                        'last_activity': datetime.now(),
                        'features_used': []
                    }
                
                self.user_sessions[user_id]['last_activity'] = datetime.now()
                self.user_sessions[user_id]['features_used'].append({
                    'feature': feature,
                    'timestamp': datetime.now()
                })
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de performance"""
        with self._lock:
            if not self.request_times:
                return {}
            
            durations = [req['duration'] for req in self.request_times]
            
            return {
                'avg_response_time': sum(durations) / len(durations),
                'max_response_time': max(durations),
                'min_response_time': min(durations),
                'total_requests': len(self.request_times),
                'error_rate': sum(self.error_counts.values()) / len(self.request_times) * 100,
                'active_sessions': len([
                    s for s in self.user_sessions.values()
                    if datetime.now() - s['last_activity'] < timedelta(minutes=30)
                ])
            }
    
    def get_feature_usage_stats(self) -> Dict[str, int]:
        """Obtém estatísticas de uso de funcionalidades"""
        with self._lock:
            return dict(self.feature_usage)

class MonitoringDashboard:
    """Dashboard de monitoramento"""
    
    def __init__(self, metrics_collector: MetricsCollector, 
                 alert_manager: AlertManager, 
                 performance_monitor: PerformanceMonitor):
        self.metrics = metrics_collector
        self.alerts = alert_manager
        self.performance = performance_monitor
    
    def render_system_metrics(self):
        """Renderiza métricas do sistema"""
        st.subheader("📊 Métricas do Sistema")
        
        # Métricas atuais
        latest_metrics = self.metrics.get_latest_metrics()
        
        if latest_metrics:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                cpu_metric = latest_metrics.get('system.cpu.usage')
                if cpu_metric:
                    st.metric("CPU", f"{cpu_metric.value:.1f}%")
            
            with col2:
                memory_metric = latest_metrics.get('system.memory.usage')
                if memory_metric:
                    st.metric("Memória", f"{memory_metric.value:.1f}%")
            
            with col3:
                disk_metric = latest_metrics.get('system.disk.usage')
                if disk_metric:
                    st.metric("Disco", f"{disk_metric.value:.1f}%")
            
            with col4:
                process_metric = latest_metrics.get('system.processes.count')
                if process_metric:
                    st.metric("Processos", f"{int(process_metric.value)}")
        
        # Gráficos históricos
        self._render_metric_charts()
    
    def _render_metric_charts(self):
        """Renderiza gráficos de métricas"""
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU e Memória
            cpu_history = self.metrics.get_metric_history('system.cpu.usage', 2)
            memory_history = self.metrics.get_metric_history('system.memory.usage', 2)
            
            if cpu_history and memory_history:
                fig = go.Figure()
                
                cpu_times = [m.timestamp for m in cpu_history]
                cpu_values = [m.value for m in cpu_history]
                
                memory_times = [m.timestamp for m in memory_history]
                memory_values = [m.value for m in memory_history]
                
                fig.add_trace(go.Scatter(
                    x=cpu_times, y=cpu_values,
                    name='CPU %', line=dict(color='red')
                ))
                
                fig.add_trace(go.Scatter(
                    x=memory_times, y=memory_values,
                    name='Memória %', line=dict(color='blue')
                ))
                
                fig.update_layout(
                    title="CPU e Memória (2h)",
                    xaxis_title="Tempo",
                    yaxis_title="Porcentagem (%)",
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Disco
            disk_history = self.metrics.get_metric_history('system.disk.usage', 2)
            
            if disk_history:
                fig = go.Figure()
                
                times = [m.timestamp for m in disk_history]
                values = [m.value for m in disk_history]
                
                fig.add_trace(go.Scatter(
                    x=times, y=values,
                    name='Disco %', line=dict(color='green')
                ))
                
                fig.update_layout(
                    title="Uso do Disco (2h)",
                    xaxis_title="Tempo",
                    yaxis_title="Porcentagem (%)",
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def render_alerts(self):
        """Renderiza alertas"""
        st.subheader("🚨 Alertas")
        
        active_alerts = self.alerts.get_active_alerts()
        
        if active_alerts:
            for alert in active_alerts[-10:]:  # Últimos 10
                level_colors = {
                    AlertLevel.INFO: "blue",
                    AlertLevel.WARNING: "orange", 
                    AlertLevel.ERROR: "red",
                    AlertLevel.CRITICAL: "darkred"
                }
                
                with st.container():
                    st.markdown(f"""
                    <div style="padding: 10px; border-left: 4px solid {level_colors[alert.level]}; 
                                background-color: rgba(255,255,255,0.1); margin: 5px 0;">
                        <strong>{alert.title}</strong><br>
                        {alert.message}<br>
                        <small>{alert.timestamp.strftime('%d/%m/%Y %H:%M:%S')}</small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.success("Nenhum alerta ativo")
    
    def render_performance(self):
        """Renderiza métricas de performance"""
        st.subheader("⚡ Performance da Aplicação")
        
        stats = self.performance.get_performance_stats()
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Tempo Médio", f"{stats['avg_response_time']:.2f}s")
            
            with col2:
                st.metric("Taxa de Erro", f"{stats['error_rate']:.1f}%")
            
            with col3:
                st.metric("Total Requisições", stats['total_requests'])
            
            with col4:
                st.metric("Sessões Ativas", stats['active_sessions'])
        
        # Uso de funcionalidades
        feature_stats = self.performance.get_feature_usage_stats()
        
        if feature_stats:
            st.subheader("📈 Uso de Funcionalidades")
            
            df = pd.DataFrame(
                list(feature_stats.items()),
                columns=['Funcionalidade', 'Uso']
            ).sort_values('Uso', ascending=False)
            
            fig = px.bar(df.head(10), x='Funcionalidade', y='Uso',
                        title="Top 10 Funcionalidades Mais Usadas")
            fig.update_xaxis(tickangle=45)
            
            st.plotly_chart(fig, use_container_width=True)

class MonitoringSystem:
    """Sistema completo de monitoramento"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.performance_monitor = PerformanceMonitor()
        self.dashboard = MonitoringDashboard(
            self.metrics_collector,
            self.alert_manager, 
            self.performance_monitor
        )
        
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """Configura alertas padrão"""
        
        # CPU alto
        self.alert_manager.add_alert_rule(
            "high_cpu",
            lambda m: m.get('system.cpu.usage', Metric('', MetricType.GAUGE, 0, datetime.now())).value > 80,
            AlertLevel.WARNING,
            "CPU Alto",
            "Uso de CPU acima de 80%"
        )
        
        # Memória alta
        self.alert_manager.add_alert_rule(
            "high_memory",
            lambda m: m.get('system.memory.usage', Metric('', MetricType.GAUGE, 0, datetime.now())).value > 85,
            AlertLevel.WARNING,
            "Memória Alta",
            "Uso de memória acima de 85%"
        )
        
        # Disco cheio
        self.alert_manager.add_alert_rule(
            "disk_full",
            lambda m: m.get('system.disk.usage', Metric('', MetricType.GAUGE, 0, datetime.now())).value > 90,
            AlertLevel.ERROR,
            "Disco Cheio",
            "Uso de disco acima de 90%"
        )
    
    def start(self):
        """Inicia sistema de monitoramento"""
        self.metrics_collector.start_collection()
        
        # Thread para verificar alertas
        def check_alerts_loop():
            while self.metrics_collector.collecting:
                try:
                    latest_metrics = self.metrics_collector.get_latest_metrics()
                    self.alert_manager.check_alerts(latest_metrics)
                    time.sleep(60)  # Verificar a cada minuto
                except Exception as e:
                    logger.error(f"Erro na verificação de alertas: {e}")
                    time.sleep(10)
        
        thread = threading.Thread(target=check_alerts_loop, daemon=True)
        thread.start()
        
        logger.info("Sistema de monitoramento iniciado")
    
    def stop(self):
        """Para sistema de monitoramento"""
        self.metrics_collector.stop_collection()
        logger.info("Sistema de monitoramento parado")

# Função para criar instância global
def get_monitoring_system():
    """Obtém instância do sistema de monitoramento"""
    if 'monitoring_system' not in st.session_state:
        st.session_state.monitoring_system = MonitoringSystem()
        st.session_state.monitoring_system.start()
    
    return st.session_state.monitoring_system