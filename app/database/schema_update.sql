-- Atualização do esquema do banco de dados
-- Adiciona tabelas para monitoramento de performance e logs

-- Tabela para logs de performance
CREATE TABLE IF NOT EXISTS performance_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    function_name TEXT NOT NULL,
    execution_time REAL NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('SUCCESS', 'ERROR')),
    error_message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices para otimizar consultas de performance
CREATE INDEX IF NOT EXISTS idx_performance_logs_timestamp ON performance_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_logs_function ON performance_logs(function_name);
CREATE INDEX IF NOT EXISTS idx_performance_logs_status ON performance_logs(status);

-- Tabela para configurações do sistema
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    updated_by INTEGER,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

-- Inserir configurações padrão
INSERT OR IGNORE INTO system_settings (setting_key, setting_value, description) VALUES
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
('system_version', '2.0.0', 'Versão do sistema');

-- Tabela para notificações do sistema
CREATE TABLE IF NOT EXISTS system_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT NOT NULL CHECK (notification_type IN ('info', 'warning', 'error', 'success')),
    target_user_id INTEGER,
    target_role TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    FOREIGN KEY (target_user_id) REFERENCES users(id)
);

-- Índices para notificações
CREATE INDEX IF NOT EXISTS idx_notifications_user ON system_notifications(target_user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_role ON system_notifications(target_role);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON system_notifications(created_at);

-- Tabela para auditoria de alterações
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values TEXT, -- JSON com valores antigos
    new_values TEXT, -- JSON com valores novos
    user_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Índices para auditoria
CREATE INDEX IF NOT EXISTS idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);

-- Atualizar tabela de usuários para incluir campos de segurança
ALTER TABLE users ADD COLUMN last_login DATETIME;
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN account_locked_until DATETIME;
ALTER TABLE users ADD COLUMN password_changed_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN two_factor_secret TEXT;

-- Atualizar tabela de eventos para incluir campos de auditoria
ALTER TABLE events ADD COLUMN updated_by INTEGER;
ALTER TABLE events ADD COLUMN updated_at DATETIME;
ALTER TABLE events ADD COLUMN version INTEGER DEFAULT 1;

-- Adicionar foreign key para updated_by (se não existir)
-- CREATE INDEX IF NOT EXISTS idx_events_updated_by ON events(updated_by);

-- Atualizar tabela de mensagens para incluir campos de rastreamento
ALTER TABLE messages ADD COLUMN read_at DATETIME;
ALTER TABLE messages ADD COLUMN delivered_at DATETIME;
ALTER TABLE messages ADD COLUMN delivery_status TEXT DEFAULT 'pending' CHECK (delivery_status IN ('pending', 'sent', 'delivered', 'failed'));

-- Criar view para estatísticas do sistema
CREATE VIEW IF NOT EXISTS system_stats AS
SELECT 
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM users WHERE created_at >= date('now', '-30 days')) as new_users_month,
    (SELECT COUNT(*) FROM events) as total_events,
    (SELECT COUNT(*) FROM events WHERE date >= date('now')) as upcoming_events,
    (SELECT COUNT(*) FROM messages) as total_messages,
    (SELECT COUNT(*) FROM messages WHERE sent_at >= date('now', '-7 days')) as messages_week,
    (SELECT COUNT(*) FROM security_logs WHERE timestamp >= datetime('now', '-24 hours')) as security_events_day,
    (SELECT COUNT(*) FROM performance_logs WHERE timestamp >= datetime('now', '-24 hours')) as performance_logs_day;

-- Criar view para relatório de performance
CREATE VIEW IF NOT EXISTS performance_report AS
SELECT 
    function_name,
    COUNT(*) as call_count,
    AVG(execution_time) as avg_execution_time,
    MIN(execution_time) as min_execution_time,
    MAX(execution_time) as max_execution_time,
    SUM(CASE WHEN status = 'ERROR' THEN 1 ELSE 0 END) as error_count,
    (SUM(CASE WHEN status = 'ERROR' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as error_rate
FROM performance_logs 
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY function_name
ORDER BY avg_execution_time DESC;

-- Trigger para auditoria automática na tabela users
CREATE TRIGGER IF NOT EXISTS audit_users_update
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, user_id, timestamp)
    VALUES (
        'users',
        NEW.id,
        'UPDATE',
        json_object(
            'username', OLD.username,
            'email', OLD.email,
            'full_name', OLD.full_name,
            'role', OLD.role,
            'is_active', OLD.is_active
        ),
        json_object(
            'username', NEW.username,
            'email', NEW.email,
            'full_name', NEW.full_name,
            'role', NEW.role,
            'is_active', NEW.is_active
        ),
        NEW.id,
        CURRENT_TIMESTAMP
    );
END;

-- Trigger para auditoria automática na tabela events
CREATE TRIGGER IF NOT EXISTS audit_events_insert
AFTER INSERT ON events
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, new_values, user_id, timestamp)
    VALUES (
        'events',
        NEW.id,
        'INSERT',
        json_object(
            'title', NEW.title,
            'description', NEW.description,
            'event_type', NEW.event_type,
            'date', NEW.date,
            'time', NEW.time
        ),
        NEW.created_by,
        CURRENT_TIMESTAMP
    );
END;

CREATE TRIGGER IF NOT EXISTS audit_events_update
AFTER UPDATE ON events
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, user_id, timestamp)
    VALUES (
        'events',
        NEW.id,
        'UPDATE',
        json_object(
            'title', OLD.title,
            'description', OLD.description,
            'event_type', OLD.event_type,
            'date', OLD.date,
            'time', OLD.time
        ),
        json_object(
            'title', NEW.title,
            'description', NEW.description,
            'event_type', NEW.event_type,
            'date', NEW.date,
            'time', NEW.time
        ),
        NEW.updated_by,
        CURRENT_TIMESTAMP
    );
END;

CREATE TRIGGER IF NOT EXISTS audit_events_delete
AFTER DELETE ON events
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_values, timestamp)
    VALUES (
        'events',
        OLD.id,
        'DELETE',
        json_object(
            'title', OLD.title,
            'description', OLD.description,
            'event_type', OLD.event_type,
            'date', OLD.date,
            'time', OLD.time
        ),
        CURRENT_TIMESTAMP
    );
END;