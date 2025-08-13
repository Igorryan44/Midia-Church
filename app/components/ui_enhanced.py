"""
Componentes de UI Melhorados para Mídia Church
Inclui loading states, progress bars e feedback visual
"""

import streamlit as st
import time
from typing import Optional, Dict, Any, List, Callable
from contextlib import contextmanager
import threading

class LoadingManager:
    """Gerenciador de estados de loading"""
    
    @staticmethod
    @contextmanager
    def loading_spinner(message: str = "Carregando...", success_message: Optional[str] = None):
        """Context manager para spinner de loading"""
        placeholder = st.empty()
        
        with placeholder.container():
            col1, col2 = st.columns([1, 10])
            with col1:
                st.markdown("🔄")
            with col2:
                st.markdown(f"**{message}**")
        
        try:
            yield
            if success_message:
                placeholder.success(f"✅ {success_message}")
                time.sleep(1)
                placeholder.empty()
            else:
                placeholder.empty()
        except Exception as e:
            placeholder.error(f"❌ Erro: {str(e)}")
            time.sleep(2)
            placeholder.empty()
            raise
    
    @staticmethod
    def progress_bar(steps: List[str], current_step: int = 0) -> Any:
        """Cria barra de progresso com etapas"""
        progress_container = st.container()
        
        with progress_container:
            # Barra de progresso
            progress = current_step / len(steps) if steps else 0
            st.progress(progress)
            
            # Etapas
            cols = st.columns(len(steps))
            for i, (col, step) in enumerate(zip(cols, steps)):
                with col:
                    if i < current_step:
                        st.markdown(f"✅ {step}")
                    elif i == current_step:
                        st.markdown(f"🔄 **{step}**")
                    else:
                        st.markdown(f"⏳ {step}")
        
        return progress_container
    
    @staticmethod
    def async_operation(func: Callable, *args, **kwargs):
        """Executa operação assíncrona com feedback"""
        if 'async_operations' not in st.session_state:
            st.session_state.async_operations = {}
        
        operation_id = f"{func.__name__}_{time.time()}"
        
        # Placeholder para status
        status_placeholder = st.empty()
        
        def run_operation():
            try:
                st.session_state.async_operations[operation_id] = {
                    'status': 'running',
                    'result': None,
                    'error': None
                }
                
                result = func(*args, **kwargs)
                
                st.session_state.async_operations[operation_id] = {
                    'status': 'completed',
                    'result': result,
                    'error': None
                }
            except Exception as e:
                st.session_state.async_operations[operation_id] = {
                    'status': 'error',
                    'result': None,
                    'error': str(e)
                }
        
        # Iniciar thread
        thread = threading.Thread(target=run_operation)
        thread.start()
        
        # Mostrar status
        with status_placeholder.container():
            st.info("🔄 Processando...")
        
        return operation_id, status_placeholder

class NotificationManager:
    """Gerenciador de notificações e alertas"""
    
    @staticmethod
    def show_toast(message: str, type: str = "info", duration: int = 3):
        """Mostra notificação toast"""
        if 'toasts' not in st.session_state:
            st.session_state.toasts = []
        
        toast = {
            'message': message,
            'type': type,
            'timestamp': time.time(),
            'duration': duration
        }
        
        st.session_state.toasts.append(toast)
        
        # Auto-remover após duração
        def remove_toast():
            time.sleep(duration)
            if toast in st.session_state.toasts:
                st.session_state.toasts.remove(toast)
        
        threading.Thread(target=remove_toast).start()
    
    @staticmethod
    def render_toasts():
        """Renderiza todas as notificações toast ativas"""
        if 'toasts' not in st.session_state:
            return
        
        current_time = time.time()
        active_toasts = [
            toast for toast in st.session_state.toasts
            if current_time - toast['timestamp'] < toast['duration']
        ]
        
        # Atualizar lista
        st.session_state.toasts = active_toasts
        
        # Renderizar toasts
        for toast in active_toasts:
            if toast['type'] == 'success':
                st.success(toast['message'])
            elif toast['type'] == 'error':
                st.error(toast['message'])
            elif toast['type'] == 'warning':
                st.warning(toast['message'])
            else:
                st.info(toast['message'])
    
    @staticmethod
    def confirm_dialog(title: str, message: str, confirm_text: str = "Confirmar", 
                      cancel_text: str = "Cancelar") -> Optional[bool]:
        """Mostra diálogo de confirmação"""
        if f'confirm_dialog_{title}' not in st.session_state:
            st.session_state[f'confirm_dialog_{title}'] = None
        
        with st.expander(f"⚠️ {title}", expanded=True):
            st.markdown(message)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(confirm_text, key=f"confirm_{title}", type="primary"):
                    st.session_state[f'confirm_dialog_{title}'] = True
                    st.rerun()
            
            with col2:
                if st.button(cancel_text, key=f"cancel_{title}"):
                    st.session_state[f'confirm_dialog_{title}'] = False
                    st.rerun()
        
        result = st.session_state[f'confirm_dialog_{title}']
        if result is not None:
            # Limpar estado após uso
            del st.session_state[f'confirm_dialog_{title}']
        
        return result

class FormBuilder:
    """Construtor de formulários avançados"""
    
    def __init__(self, form_key: str):
        self.form_key = form_key
        self.fields = {}
        self.validators = {}
        self.errors = {}
    
    def add_field(self, name: str, field_type: str, label: str, 
                  required: bool = False, validator: Optional[Callable] = None, **kwargs):
        """Adiciona campo ao formulário"""
        self.fields[name] = {
            'type': field_type,
            'label': label,
            'required': required,
            'kwargs': kwargs
        }
        
        if validator:
            self.validators[name] = validator
    
    def render(self) -> Dict[str, Any]:
        """Renderiza formulário e retorna valores"""
        values = {}
        
        with st.form(self.form_key):
            for name, config in self.fields.items():
                field_type = config['type']
                label = config['label']
                kwargs = config['kwargs']
                
                # Adicionar indicador de campo obrigatório
                if config['required']:
                    label += " *"
                
                # Renderizar campo baseado no tipo
                if field_type == 'text':
                    values[name] = st.text_input(label, **kwargs)
                elif field_type == 'textarea':
                    values[name] = st.text_area(label, **kwargs)
                elif field_type == 'number':
                    values[name] = st.number_input(label, **kwargs)
                elif field_type == 'date':
                    values[name] = st.date_input(label, **kwargs)
                elif field_type == 'time':
                    values[name] = st.time_input(label, **kwargs)
                elif field_type == 'select':
                    values[name] = st.selectbox(label, **kwargs)
                elif field_type == 'multiselect':
                    values[name] = st.multiselect(label, **kwargs)
                elif field_type == 'checkbox':
                    values[name] = st.checkbox(label, **kwargs)
                elif field_type == 'file':
                    values[name] = st.file_uploader(label, **kwargs)
                
                # Mostrar erro se existir
                if name in self.errors:
                    st.error(self.errors[name])
            
            # Botão de submit
            submitted = st.form_submit_button("Enviar", type="primary")
        
        if submitted:
            # Validar campos
            self.errors = {}
            
            for name, config in self.fields.items():
                value = values.get(name)
                
                # Validar campo obrigatório
                if config['required'] and not value:
                    self.errors[name] = "Este campo é obrigatório"
                
                # Validar com validator customizado
                if name in self.validators and value:
                    try:
                        if not self.validators[name](value):
                            self.errors[name] = "Valor inválido"
                    except Exception as e:
                        self.errors[name] = str(e)
            
            # Se há erros, re-renderizar
            if self.errors:
                st.rerun()
            
            return values if not self.errors else None
        
        return None

class DataTable:
    """Tabela de dados avançada com filtros e ações"""
    
    def __init__(self, data, columns: Optional[List[str]] = None):
        self.data = data
        self.columns = columns or list(data.columns) if hasattr(data, 'columns') else []
    
    def render(self, 
               searchable: bool = True,
               sortable: bool = True,
               actions: Optional[List[Dict[str, Any]]] = None,
               page_size: int = 10) -> Dict[str, Any]:
        """Renderiza tabela com funcionalidades avançadas"""
        
        # Filtros
        if searchable:
            search_term = st.text_input("🔍 Buscar", key=f"search_{id(self.data)}")
            if search_term:
                # Filtrar dados baseado no termo de busca
                mask = self.data.astype(str).apply(
                    lambda x: x.str.contains(search_term, case=False, na=False)
                ).any(axis=1)
                filtered_data = self.data[mask]
            else:
                filtered_data = self.data
        else:
            filtered_data = self.data
        
        # Paginação
        from app.utils.cache_manager import PaginationHelper
        
        paginated_data, current_page, total_pages, total_items = PaginationHelper.paginate_dataframe(
            filtered_data, page_size, f"table_{id(self.data)}"
        )
        
        # Mostrar informações
        st.markdown(f"**Total: {total_items} itens** | Página {current_page} de {total_pages}")
        
        # Renderizar tabela
        if not paginated_data.empty:
            # Adicionar colunas de ação se especificadas
            if actions:
                action_data = paginated_data.copy()
                for i, action in enumerate(actions):
                    action_data[f"action_{i}"] = [
                        f"[{action['label']}]" for _ in range(len(action_data))
                    ]
                
                st.dataframe(action_data, use_container_width=True)
                
                # Processar ações
                selected_rows = st.multiselect(
                    "Selecionar linhas para ação:",
                    options=list(range(len(paginated_data))),
                    format_func=lambda x: f"Linha {x + 1}"
                )
                
                if selected_rows:
                    action_cols = st.columns(len(actions))
                    for i, (col, action) in enumerate(zip(action_cols, actions)):
                        with col:
                            if st.button(action['label'], key=f"action_{i}_{id(self.data)}"):
                                for row_idx in selected_rows:
                                    action['callback'](paginated_data.iloc[row_idx])
                                st.rerun()
            else:
                st.dataframe(paginated_data, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado")
        
        # Controles de paginação
        PaginationHelper.render_pagination_controls(
            current_page, total_pages, f"table_{id(self.data)}"
        )
        
        return {
            'filtered_data': filtered_data,
            'paginated_data': paginated_data,
            'current_page': current_page,
            'total_pages': total_pages,
            'total_items': total_items
        }

# Funções utilitárias para UI
def render_metric_card(title: str, value: str, delta: Optional[str] = None, 
                      delta_color: str = "normal"):
    """Renderiza card de métrica"""
    with st.container():
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <h3 style="margin: 0; color: #666; font-size: 0.9rem;">{title}</h3>
            <h2 style="margin: 0.5rem 0; color: #333;">{value}</h2>
            {f'<p style="margin: 0; color: {"green" if delta_color == "normal" else "red"};">{delta}</p>' if delta else ''}
        </div>
        """, unsafe_allow_html=True)

def render_status_badge(status: str, color_map: Optional[Dict[str, str]] = None):
    """Renderiza badge de status"""
    default_colors = {
        'ativo': 'green',
        'inativo': 'red',
        'pendente': 'orange',
        'concluído': 'blue',
        'cancelado': 'gray'
    }
    
    colors = color_map or default_colors
    color = colors.get(status.lower(), 'gray')
    
    st.markdown(f"""
    <span style="
        background-color: {color};
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
    ">{status}</span>
    """, unsafe_allow_html=True)