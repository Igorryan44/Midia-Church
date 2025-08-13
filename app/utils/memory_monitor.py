
import psutil
import gc
import threading
import time
from datetime import datetime

class MemoryMonitor:
    def __init__(self, threshold_mb=500):
        self.threshold_mb = threshold_mb
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Inicia monitoramento de memória"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Para monitoramento de memória"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_loop(self):
        """Loop de monitoramento"""
        while self.monitoring:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                if memory_mb > self.threshold_mb:
                    print(f"⚠️ Alto uso de memória: {memory_mb:.1f}MB")
                    gc.collect()  # Forçar limpeza
                
                time.sleep(30)  # Verificar a cada 30 segundos
            except Exception:
                break
    
    def get_memory_usage(self):
        """Retorna uso atual de memória"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0

# Instância global do monitor
memory_monitor = MemoryMonitor()
