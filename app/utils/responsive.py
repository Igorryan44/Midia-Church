import streamlit as st

def get_responsive_css():
    """Retorna CSS para responsividade aprimorada"""
    
    return """
    <style>
    /* Responsividade Geral */
    @media (max-width: 768px) {
        /* Mobile */
        .main-header h1 {
            font-size: 1.5rem !important;
            text-align: center;
        }
        
        .metric-card {
            margin-bottom: 1rem;
        }
        
        .stColumns > div {
            padding: 0 0.25rem !important;
        }
        
        .sidebar .sidebar-content {
            padding: 1rem 0.5rem;
        }
        
        /* Formulários em mobile */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {
            font-size: 16px !important; /* Evita zoom no iOS */
        }
        
        /* Tabelas responsivas */
        .dataframe {
            font-size: 0.8rem;
        }
        
        /* Botões em mobile */
        .stButton > button {
            width: 100% !important;
            margin-bottom: 0.5rem;
        }
        
        /* Calendar responsivo */
        .fc-toolbar {
            flex-direction: column !important;
        }
        
        .fc-toolbar-chunk {
            margin: 0.25rem 0 !important;
        }
    }
    
    @media (max-width: 480px) {
        /* Mobile pequeno */
        .main-header h1 {
            font-size: 1.2rem !important;
        }
        
        .metric-card {
            padding: 0.75rem !important;
        }
        
        .metric-card h3 {
            font-size: 1rem !important;
        }
        
        .metric-value {
            font-size: 1.5rem !important;
        }
        
        /* Sidebar compacta */
        .sidebar .sidebar-content {
            padding: 0.5rem 0.25rem;
        }
        
        .sidebar-stats {
            padding: 0.5rem !important;
        }
        
        .stat-item {
            padding: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
    }
    
    @media (min-width: 769px) and (max-width: 1024px) {
        /* Tablet */
        .main-header h1 {
            font-size: 2rem;
        }
        
        .stColumns > div {
            padding: 0 0.5rem !important;
        }
    }
    
    @media (min-width: 1025px) {
        /* Desktop */
        .main-header h1 {
            font-size: 2.5rem;
        }
        
        .stColumns > div {
            padding: 0 0.75rem !important;
        }
    }
    
    /* Container responsivo para gráficos */
    .chart-container {
        width: 100%;
        overflow-x: auto;
    }
    
    /* Tabelas responsivas */
    .responsive-table {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }
    
    .responsive-table table {
        min-width: 600px;
    }
    
    /* Cards responsivos */
    .responsive-card {
        width: 100%;
        margin-bottom: 1rem;
        box-sizing: border-box;
    }
    
    @media (min-width: 768px) {
        .responsive-card {
            width: calc(50% - 0.5rem);
            display: inline-block;
            vertical-align: top;
            margin-right: 1rem;
        }
    }
    
    @media (min-width: 1024px) {
        .responsive-card {
            width: calc(33.333% - 0.67rem);
        }
    }
    
    /* Navegação responsiva */
    .nav-responsive {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    
    .nav-responsive .nav-item {
        flex: 1;
        min-width: 120px;
        text-align: center;
    }
    
    @media (max-width: 768px) {
        .nav-responsive .nav-item {
            min-width: 100%;
        }
    }
    
    /* Imagens responsivas */
    .responsive-image {
        max-width: 100%;
        height: auto;
        display: block;
    }
    
    /* Texto responsivo */
    .responsive-text {
        font-size: clamp(0.875rem, 2.5vw, 1.125rem);
        line-height: 1.6;
    }
    
    /* Espaçamento responsivo */
    .responsive-spacing {
        padding: clamp(1rem, 4vw, 2rem);
        margin: clamp(0.5rem, 2vw, 1rem) 0;
    }
    
    /* Grid responsivo */
    .responsive-grid {
        display: grid;
        gap: 1rem;
        grid-template-columns: 1fr;
    }
    
    @media (min-width: 768px) {
        .responsive-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    @media (min-width: 1024px) {
        .responsive-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    
    @media (min-width: 1200px) {
        .responsive-grid {
            grid-template-columns: repeat(4, 1fr);
        }
    }
    
    /* Flexbox responsivo */
    .responsive-flex {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
    }
    
    .responsive-flex > * {
        flex: 1;
        min-width: 250px;
    }
    
    @media (max-width: 768px) {
        .responsive-flex {
            flex-direction: column;
        }
        
        .responsive-flex > * {
            min-width: 100%;
        }
    }
    
    /* Ocultar elementos em mobile */
    @media (max-width: 768px) {
        .hide-mobile {
            display: none !important;
        }
    }
    
    /* Mostrar apenas em mobile */
    .show-mobile {
        display: none !important;
    }
    
    @media (max-width: 768px) {
        .show-mobile {
            display: block !important;
        }
    }
    
    /* Ajustes para telas muito pequenas */
    @media (max-width: 320px) {
        .main-header h1 {
            font-size: 1rem !important;
        }
        
        .metric-card {
            padding: 0.5rem !important;
        }
        
        .stButton > button {
            font-size: 0.8rem !important;
            padding: 0.5rem !important;
        }
    }
    
    /* Ajustes para telas muito grandes */
    @media (min-width: 1920px) {
        .main-container {
            max-width: 1600px;
            margin: 0 auto;
        }
    }
    
    /* Melhorias de acessibilidade */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
    
    /* Alto contraste */
    @media (prefers-contrast: high) {
        .metric-card,
        .sidebar-stats,
        .stat-item {
            border: 2px solid var(--dark-color) !important;
        }
    }
    
    /* Modo escuro */
    @media (prefers-color-scheme: dark) {
        :root {
            --light-color: #1E293B;
            --light-secondary: #334155;
            --dark-color: #F8FAFC;
            --dark-secondary: #E2E8F0;
        }
    }
    </style>
    """

def apply_responsive_layout():
    """Aplica layout responsivo à página atual"""
    
    # Detectar tipo de dispositivo
    device_type = detect_device_type()
    
    # Aplicar CSS responsivo
    st.markdown(get_responsive_css(), unsafe_allow_html=True)
    
    # Configurar colunas baseado no dispositivo
    if device_type == "mobile":
        return {"columns": 1, "spacing": "small"}
    elif device_type == "tablet":
        return {"columns": 2, "spacing": "medium"}
    else:
        return {"columns": 3, "spacing": "large"}

def detect_device_type():
    """Detecta o tipo de dispositivo (aproximado)"""
    
    # Streamlit não tem acesso direto ao user agent,
    # então usamos uma abordagem baseada em JavaScript
    device_detection_js = """
    <script>
    function detectDevice() {
        const width = window.innerWidth;
        if (width <= 768) {
            return 'mobile';
        } else if (width <= 1024) {
            return 'tablet';
        } else {
            return 'desktop';
        }
    }
    
    // Armazenar no sessionStorage
    sessionStorage.setItem('deviceType', detectDevice());
    
    // Listener para mudanças de tamanho
    window.addEventListener('resize', function() {
        sessionStorage.setItem('deviceType', detectDevice());
    });
    </script>
    """
    
    st.markdown(device_detection_js, unsafe_allow_html=True)
    
    # Retorno padrão (será sobrescrito pelo JavaScript)
    return "desktop"

def create_responsive_columns(num_columns: int = None):
    """Cria colunas responsivas baseadas no dispositivo"""
    
    if num_columns is None:
        # Auto-detectar baseado no conteúdo da tela
        try:
            # Usar JavaScript para detectar largura (aproximado)
            num_columns = 3  # Padrão desktop
        except:
            num_columns = 3
    
    # Ajustar para mobile
    if num_columns > 2:
        mobile_columns = 1
        tablet_columns = 2
        desktop_columns = num_columns
    else:
        mobile_columns = 1
        tablet_columns = num_columns
        desktop_columns = num_columns
    
    return st.columns(desktop_columns)

def responsive_metric_cards(metrics: list):
    """Cria cards de métricas responsivos"""
    
    # Detectar número de colunas baseado na quantidade de métricas
    if len(metrics) <= 2:
        cols = st.columns(len(metrics))
    elif len(metrics) <= 4:
        cols = st.columns(min(4, len(metrics)))
    else:
        # Para muitas métricas, usar grid responsivo
        cols = st.columns(4)
    
    for i, metric in enumerate(metrics):
        col_index = i % len(cols)
        with cols[col_index]:
            st.metric(
                label=metric.get("label", ""),
                value=metric.get("value", ""),
                delta=metric.get("delta", None)
            )

def responsive_dataframe(df, height: int = None):
    """Exibe dataframe responsivo"""
    
    # Configurações responsivas para tabelas
    config = {
        "use_container_width": True,
        "hide_index": True
    }
    
    if height:
        config["height"] = height
    
    # Wrapper responsivo
    st.markdown('<div class="responsive-table">', unsafe_allow_html=True)
    st.dataframe(df, **config)
    st.markdown('</div>', unsafe_allow_html=True)

def responsive_chart(chart_func, *args, **kwargs):
    """Wrapper para gráficos responsivos"""
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    chart_func(*args, **kwargs)
    st.markdown('</div>', unsafe_allow_html=True)

def mobile_friendly_form(form_key: str):
    """Cria formulário otimizado para mobile"""
    
    # CSS específico para formulários mobile
    mobile_form_css = """
    <style>
    .mobile-form input, .mobile-form textarea, .mobile-form select {
        font-size: 16px !important;
        padding: 12px !important;
        border-radius: 8px !important;
    }
    
    .mobile-form .stButton > button {
        width: 100% !important;
        padding: 12px !important;
        font-size: 16px !important;
        margin-top: 1rem !important;
    }
    </style>
    """
    
    st.markdown(mobile_form_css, unsafe_allow_html=True)
    
    # Container com classe mobile-form
    st.markdown('<div class="mobile-form">', unsafe_allow_html=True)
    
    return st.form(form_key)

def responsive_sidebar():
    """Configura sidebar responsiva"""
    
    # CSS para sidebar responsiva
    sidebar_css = """
    <style>
    @media (max-width: 768px) {
        .css-1d391kg {
            width: 100% !important;
            margin-left: 0 !important;
        }
        
        .css-1lcbmhc {
            width: 100% !important;
            margin-left: 0 !important;
        }
    }
    </style>
    """
    
    st.markdown(sidebar_css, unsafe_allow_html=True)