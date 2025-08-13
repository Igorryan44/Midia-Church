"""
Módulo de inicialização dos módulos da aplicação
"""

from .dashboard import render_dashboard
from .planner import render_planner
from .scheduling import render_scheduling
from .content_management import render_content_management
from .attendance import render_attendance
from .communication import render_communication
# WhatsApp antigo removido - usando apenas whatsapp_api
from .ai_assistant import render_ai_assistant

__all__ = [
    'render_dashboard',
    'render_planner',
    'render_scheduling',
    'render_content_management',
    'render_attendance',
    'render_communication',
    'render_whatsapp_module',
    'render_ai_assistant'
]