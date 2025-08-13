-- =====================================================
-- SCRIPT DE CONFIGURAÇÃO INICIAL DO SUPABASE
-- Mídia Church - Sistema de Gestão Eclesiástica
-- =====================================================

-- Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- TABELA DE USUÁRIOS
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    auth_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'member' CHECK (role IN ('admin', 'pastor', 'leader', 'member')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Campos de segurança
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked_until TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret TEXT
);

-- Índices para otimização
CREATE INDEX IF NOT EXISTS idx_users_auth_id ON users(auth_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- =====================================================
-- TABELA DE EVENTOS
-- =====================================================
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    event_type VARCHAR(50) NOT NULL,
    start_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    end_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(200),
    max_attendees INTEGER DEFAULT 0,
    requires_registration BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE
);

-- Índices para eventos
CREATE INDEX IF NOT EXISTS idx_events_start_datetime ON events(start_datetime);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created_by ON events(created_by);
CREATE INDEX IF NOT EXISTS idx_events_active ON events(is_active);

-- =====================================================
-- TABELA DE PRESENÇA
-- =====================================================
CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    present BOOLEAN DEFAULT FALSE,
    check_in_time TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(event_id, user_id)
);

-- Índices para presença
CREATE INDEX IF NOT EXISTS idx_attendance_event ON attendance(event_id);
CREATE INDEX IF NOT EXISTS idx_attendance_user ON attendance(user_id);
CREATE INDEX IF NOT EXISTS idx_attendance_present ON attendance(present);

-- =====================================================
-- TABELA DE CONTEÚDO DE MÍDIA
-- =====================================================
CREATE TABLE IF NOT EXISTS media_content (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    tags TEXT,
    uploaded_by INTEGER REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    file_size BIGINT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Índices para mídia
CREATE INDEX IF NOT EXISTS idx_media_type ON media_content(file_type);
CREATE INDEX IF NOT EXISTS idx_media_category ON media_content(category);
CREATE INDEX IF NOT EXISTS idx_media_uploaded_by ON media_content(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_media_active ON media_content(is_active);

-- =====================================================
-- TABELA DE POSTS
-- =====================================================
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    post_type VARCHAR(50) DEFAULT 'announcement',
    author_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_pinned BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Índices para posts
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author_id);
CREATE INDEX IF NOT EXISTS idx_posts_type ON posts(post_type);
CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at);
CREATE INDEX IF NOT EXISTS idx_posts_pinned ON posts(is_pinned);

-- =====================================================
-- TABELA DE COMENTÁRIOS
-- =====================================================
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Índices para comentários
CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_author ON comments(author_id);
CREATE INDEX IF NOT EXISTS idx_comments_created ON comments(created_at);

-- =====================================================
-- TABELA DE ROTINAS
-- =====================================================
CREATE TABLE IF NOT EXISTS routines (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    frequency VARCHAR(50) NOT NULL,
    assigned_to INTEGER REFERENCES users(id),
    due_date DATE,
    completed BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Índices para rotinas
CREATE INDEX IF NOT EXISTS idx_routines_assigned ON routines(assigned_to);
CREATE INDEX IF NOT EXISTS idx_routines_created_by ON routines(created_by);
CREATE INDEX IF NOT EXISTS idx_routines_due_date ON routines(due_date);
CREATE INDEX IF NOT EXISTS idx_routines_completed ON routines(completed);

-- =====================================================
-- TABELA DE CONVERSAS IA
-- =====================================================
CREATE TABLE IF NOT EXISTS ai_conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para conversas IA
CREATE INDEX IF NOT EXISTS idx_ai_conversations_user ON ai_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_conversations_created ON ai_conversations(created_at);

-- =====================================================
-- TABELA DE LOGS DE SEGURANÇA
-- =====================================================
CREATE TABLE IF NOT EXISTS security_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    user_id VARCHAR(50),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para logs de segurança
CREATE INDEX IF NOT EXISTS idx_security_logs_type ON security_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_security_logs_user ON security_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_security_logs_timestamp ON security_logs(timestamp);

-- =====================================================
-- TABELA DE CONFIGURAÇÕES DO SISTEMA
-- =====================================================
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para configurações
CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(setting_key);

-- =====================================================
-- TABELA DE MENSAGENS
-- =====================================================
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(id),
    recipient_id INTEGER REFERENCES users(id),
    subject VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'notification',
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Índices para mensagens
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id);
CREATE INDEX IF NOT EXISTS idx_messages_sent ON messages(sent_at);
CREATE INDEX IF NOT EXISTS idx_messages_read ON messages(read_at);

-- =====================================================
-- TABELA DE RELATÓRIOS DE REUNIÃO
-- =====================================================
CREATE TABLE IF NOT EXISTS meeting_reports (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id),
    title VARCHAR(200) NOT NULL,
    content TEXT,
    summary TEXT,
    participants JSONB,
    decisions TEXT,
    action_items JSONB,
    next_steps TEXT,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para relatórios
CREATE INDEX IF NOT EXISTS idx_meeting_reports_event ON meeting_reports(event_id);
CREATE INDEX IF NOT EXISTS idx_meeting_reports_status ON meeting_reports(status);
CREATE INDEX IF NOT EXISTS idx_meeting_reports_created_by ON meeting_reports(created_by);

-- =====================================================
-- TABELA DE TEMPLATES DE RELATÓRIO
-- =====================================================
CREATE TABLE IF NOT EXISTS report_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Índices para templates
CREATE INDEX IF NOT EXISTS idx_report_templates_created_by ON report_templates(created_by);
CREATE INDEX IF NOT EXISTS idx_report_templates_active ON report_templates(is_active);

-- =====================================================
-- TABELAS DE MONITORAMENTO E AUDITORIA
-- =====================================================

-- Tabela de logs de performance
CREATE TABLE IF NOT EXISTS performance_logs (
    id SERIAL PRIMARY KEY,
    function_name VARCHAR(200) NOT NULL,
    execution_time REAL NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('SUCCESS', 'ERROR')),
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_performance_logs_timestamp ON performance_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_logs_function ON performance_logs(function_name);
CREATE INDEX IF NOT EXISTS idx_performance_logs_status ON performance_logs(status);

-- Tabela de notificações do sistema
CREATE TABLE IF NOT EXISTS system_notifications (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(20) NOT NULL CHECK (notification_type IN ('info', 'warning', 'error', 'success')),
    target_user_id INTEGER REFERENCES users(id),
    target_role VARCHAR(20),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Índices para notificações
CREATE INDEX IF NOT EXISTS idx_notifications_user ON system_notifications(target_user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_role ON system_notifications(target_role);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON system_notifications(created_at);

-- Tabela de auditoria
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    user_id INTEGER REFERENCES users(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Índices para auditoria
CREATE INDEX IF NOT EXISTS idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);

-- =====================================================
-- TRIGGERS PARA UPDATED_AT
-- =====================================================

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

-- Triggers para tabelas com updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_posts_updated_at BEFORE UPDATE ON posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_routines_updated_at BEFORE UPDATE ON routines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meeting_reports_updated_at BEFORE UPDATE ON meeting_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- INSERIR CONFIGURAÇÕES PADRÃO
-- =====================================================
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
('backup_retention_days', '30', 'Número de dias para manter backups'),
('log_retention_days', '90', 'Número de dias para manter logs de segurança'),
('performance_log_retention_days', '30', 'Número de dias para manter logs de performance'),
('max_login_attempts', '5', 'Número máximo de tentativas de login'),
('login_attempt_window_minutes', '15', 'Janela de tempo para tentativas de login (minutos)'),
('session_timeout_hours', '24', 'Tempo limite da sessão (horas)'),
('enable_performance_monitoring', 'true', 'Habilitar monitoramento de performance'),
('enable_security_logging', 'true', 'Habilitar logs de segurança'),
('maintenance_mode', 'false', 'Modo de manutenção'),
('system_name', 'Mídia Church', 'Nome do sistema'),
('system_version', '2.0.0', 'Versão do sistema')
ON CONFLICT (setting_key) DO NOTHING;

-- =====================================================
-- COMENTÁRIOS PARA DOCUMENTAÇÃO
-- =====================================================
COMMENT ON TABLE users IS 'Tabela de usuários do sistema';
COMMENT ON TABLE events IS 'Tabela de eventos da igreja';
COMMENT ON TABLE attendance IS 'Tabela de controle de presença';
COMMENT ON TABLE media_content IS 'Tabela de conteúdo de mídia';
COMMENT ON TABLE posts IS 'Tabela de posts e anúncios';
COMMENT ON TABLE comments IS 'Tabela de comentários dos posts';
COMMENT ON TABLE routines IS 'Tabela de rotinas e tarefas';
COMMENT ON TABLE ai_conversations IS 'Tabela de conversas com IA';
COMMENT ON TABLE security_logs IS 'Tabela de logs de segurança';
COMMENT ON TABLE system_settings IS 'Tabela de configurações do sistema';
COMMENT ON TABLE messages IS 'Tabela de mensagens entre usuários';
COMMENT ON TABLE meeting_reports IS 'Tabela de relatórios de reunião';
COMMENT ON TABLE report_templates IS 'Tabela de templates de relatório';
COMMENT ON TABLE performance_logs IS 'Tabela de logs de performance';
COMMENT ON TABLE system_notifications IS 'Tabela de notificações do sistema';
COMMENT ON TABLE audit_log IS 'Tabela de auditoria de alterações';

-- =====================================================
-- FINALIZAÇÃO
-- =====================================================
-- Script executado com sucesso!
-- Próximo passo: Execute o arquivo supabase_policies.sql