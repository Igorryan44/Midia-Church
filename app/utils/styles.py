"""
Estilos CSS customizados para a aplicação
"""

def get_custom_css():
    """Retorna CSS customizado para a aplicação"""
    
    return """
    <style>
    /* Importar fontes do Google */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Variáveis CSS - Paleta Moderna */
    :root {
        --primary-color: #4F46E5;      /* Indigo moderno */
        --secondary-color: #7C3AED;    /* Violeta elegante */
        --accent-color: #06B6D4;       /* Cyan vibrante */
        --success-color: #10B981;      /* Verde esmeralda */
        --warning-color: #F59E0B;      /* Âmbar quente */
        --danger-color: #EF4444;       /* Vermelho coral */
        --info-color: #3B82F6;         /* Azul royal */
        --light-color: #F8FAFC;        /* Cinza muito claro */
        --light-secondary: #F1F5F9;    /* Cinza claro secundário */
        --medium-color: #64748B;       /* Cinza médio */
        --dark-color: #1E293B;         /* Azul escuro */
        --dark-secondary: #334155;     /* Azul escuro secundário */
        --border-color: #E2E8F0;       /* Cinza para bordas */
        --border-radius: 12px;
        --border-radius-sm: 8px;
        --border-radius-lg: 16px;
        --box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --box-shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Reset e configurações gerais */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        padding: 2rem;
        border-radius: var(--border-radius);
        margin-bottom: 2rem;
        box-shadow: var(--box-shadow);
        text-align: center;
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 2.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    
    /* Cards de métricas */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
        border-left: 4px solid var(--primary-color);
        transition: var(--transition);
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--box-shadow-lg);
        border-left-color: var(--secondary-color);
    }
    
    .metric-card h3 {
        color: var(--dark-color);
        margin: 0 0 0.5rem 0;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-card .metric-value {
        font-size: 2.25rem;
        font-weight: 700;
        color: var(--primary-color);
        margin: 0;
        line-height: 1;
    }
    
    .metric-card .metric-label {
        color: var(--medium-color);
        font-size: 0.875rem;
        margin: 0.25rem 0 0 0;
        font-weight: 500;
    }
    
    /* Sidebar customizada */
    .sidebar .sidebar-content {
        background: var(--light-color);
        border-radius: var(--border-radius);
        padding: 1rem;
        border: 1px solid var(--border-color);
    }
    
    .sidebar-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        padding: 1.5rem;
        border-radius: var(--border-radius);
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: var(--box-shadow);
    }
    
    .sidebar-header h3 {
        margin: 0;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.125rem;
    }
    
    .sidebar-stats {
        background: white;
        border-radius: var(--border-radius-sm);
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
        box-shadow: var(--box-shadow);
    }
    
    .sidebar-stats h4 {
        color: var(--dark-color);
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0 0 0.75rem 0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .stat-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--border-color);
    }
    
    .stat-item:last-child {
        border-bottom: none;
    }
    
    .stat-label {
        color: var(--medium-color);
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .stat-value {
        color: var(--primary-color);
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    /* Botões customizados */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border: none;
        border-radius: var(--border-radius-sm);
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.875rem;
        transition: var(--transition);
        width: 100%;
        box-shadow: var(--box-shadow);
        letter-spacing: 0.025em;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: var(--box-shadow-lg);
        background: linear-gradient(135deg, var(--secondary-color) 0%, var(--accent-color) 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Botões secundários */
    .stButton.secondary > button {
        background: white;
        color: var(--primary-color);
        border: 2px solid var(--primary-color);
    }
    
    .stButton.secondary > button:hover {
        background: var(--primary-color);
        color: white;
    }
    
    /* Botões de sucesso */
    .stButton.success > button {
        background: var(--success-color);
        color: white;
    }
    
    .stButton.success > button:hover {
        background: #059669;
    }
    
    /* Botões de perigo */
    .stButton.danger > button {
        background: var(--danger-color);
        color: white;
    }
    
    .stButton.danger > button:hover {
        background: #DC2626;
    }
    
    /* Formulários */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    .stTimeInput > div > div > input {
        border-radius: var(--border-radius-sm);
        border: 2px solid var(--border-color);
        transition: var(--transition);
        font-size: 0.875rem;
        padding: 0.75rem;
        background-color: white;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus,
    .stDateInput > div > div > input:focus,
    .stTimeInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        outline: none;
    }
    
    /* Labels dos formulários */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stNumberInput > label,
    .stDateInput > label,
    .stTimeInput > label {
        color: var(--dark-color);
        font-weight: 600;
        font-size: 0.875rem;
        margin-bottom: 0.5rem;
    }
    
    /* Tabelas */
    .dataframe {
        border-radius: var(--border-radius-sm);
        overflow: hidden;
        box-shadow: var(--box-shadow);
        border: 1px solid var(--border-color);
    }
    
    .dataframe thead th {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        font-weight: 600;
        font-size: 0.875rem;
        padding: 1rem 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .dataframe tbody td {
        padding: 0.75rem;
        font-size: 0.875rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: var(--light-color);
    }
    
    .dataframe tbody tr:hover {
        background-color: var(--light-secondary);
        transition: var(--transition);
    }
    
    /* Alertas e mensagens */
    .stAlert {
        border-radius: var(--border-radius-sm);
        border: none;
        box-shadow: var(--box-shadow);
        font-weight: 500;
    }
    
    .stSuccess {
        background-color: #ECFDF5;
        border-left: 4px solid var(--success-color);
        color: #065F46;
    }
    
    .stError {
        background-color: #FEF2F2;
        border-left: 4px solid var(--danger-color);
        color: #991B1B;
    }
    
    .stWarning {
        background-color: #FFFBEB;
        border-left: 4px solid var(--warning-color);
        color: #92400E;
    }
    
    .stInfo {
        background-color: #EFF6FF;
        border-left: 4px solid var(--info-color);
        color: #1E40AF;
    }
    
    /* Gráficos */
    .stPlotlyChart {
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
        background: white;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: var(--light-color);
        padding: 0.5rem;
        border-radius: var(--border-radius-sm);
        border: 1px solid var(--border-color);
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: var(--border-radius-sm);
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.875rem;
        transition: var(--transition);
        border: 1px solid var(--border-color);
        color: var(--medium-color);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--light-secondary);
        color: var(--dark-color);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border-color: var(--primary-color);
        box-shadow: var(--box-shadow);
    }
    
    /* Expansores */
    .streamlit-expanderHeader {
        background-color: var(--light-color);
        border-radius: var(--border-radius-sm);
        font-weight: 600;
        color: var(--dark-color);
        border: 1px solid var(--border-color);
        padding: 1rem;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: var(--light-secondary);
        transition: var(--transition);
    }
    
    .streamlit-expanderContent {
        border-radius: 0 0 var(--border-radius-sm) var(--border-radius-sm);
        box-shadow: var(--box-shadow);
        border: 1px solid var(--border-color);
        border-top: none;
    }
    
    /* Upload de arquivos */
    .stFileUploader {
        border: 2px dashed var(--primary-color);
        border-radius: var(--border-radius);
        padding: 2rem;
        text-align: center;
        transition: var(--transition);
        background-color: rgba(79, 70, 229, 0.02);
    }
    
    .stFileUploader:hover {
        border-color: var(--secondary-color);
        background-color: rgba(79, 70, 229, 0.05);
        transform: translateY(-1px);
    }
    
    /* Progresso */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        border-radius: 4px;
    }
    
    /* Chat messages */
    .chat-message {
        padding: 1.5rem;
        border-radius: var(--border-radius);
        margin-bottom: 1rem;
        box-shadow: var(--box-shadow);
        border: 1px solid var(--border-color);
    }
    
    .chat-message.user {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        margin-left: 2rem;
        border-color: var(--primary-color);
    }
    
    .chat-message.assistant {
        background: white;
        border-left: 4px solid var(--accent-color);
        margin-right: 2rem;
        color: var(--dark-color);
    }
    
    /* Scrollbar customizada */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--light-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-color);
    }
    
    /* Badges e tags */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: var(--border-radius-sm);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-primary {
        background-color: var(--primary-color);
        color: white;
    }
    
    .badge-success {
        background-color: var(--success-color);
        color: white;
    }
    
    .badge-warning {
        background-color: var(--warning-color);
        color: white;
    }
    
    .badge-danger {
        background-color: var(--danger-color);
        color: white;
    }
    
    .badge-info {
        background-color: var(--info-color);
        color: white;
    }
    
    .badge-light {
        background-color: var(--light-secondary);
        color: var(--dark-color);
        border: 1px solid var(--border-color);
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .main-header h1 {
            font-size: 2rem;
        }
        
        .metric-card {
            padding: 1rem;
        }
        
        .chat-message.user {
            margin-left: 0;
        }
        
        .chat-message.assistant {
            margin-right: 0;
        }
    }
    
    /* Animações */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    </style>
    """

def get_login_css():
    """CSS específico para a página de login"""
    
    return """
    <style>
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow-lg);
        border: 1px solid var(--border-color);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-header h2 {
        color: var(--dark-color);
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .login-header p {
        color: var(--medium-color);
        margin: 0;
        font-weight: 500;
    }
    
    .login-form {
        margin-bottom: 1rem;
    }
    
    .login-button {
        width: 100%;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: var(--border-radius-sm);
        font-weight: 600;
        cursor: pointer;
        transition: var(--transition);
        box-shadow: var(--box-shadow);
    }
    
    .login-button:hover {
        transform: translateY(-1px);
        box-shadow: var(--box-shadow-lg);
    }
    </style>
    """