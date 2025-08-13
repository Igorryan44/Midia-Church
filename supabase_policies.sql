-- =====================================================
-- POLÍTICAS RLS (ROW LEVEL SECURITY) - SUPABASE
-- Mídia Church - Sistema de Gestão Eclesiástica
-- =====================================================

-- =====================================================
-- FUNÇÕES AUXILIARES PARA POLÍTICAS
-- =====================================================

-- Função para verificar se o usuário é admin ou pastor
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM users 
        WHERE auth_id = auth.uid() 
        AND role IN ('admin', 'pastor')
        AND is_active = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

-- Função para verificar se o usuário é pastor
CREATE OR REPLACE FUNCTION is_pastor()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM users 
        WHERE auth_id = auth.uid() 
        AND role = 'pastor'
        AND is_active = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

-- Função para verificar se o usuário é líder
CREATE OR REPLACE FUNCTION is_leader()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM users 
        WHERE auth_id = auth.uid() 
        AND role IN ('admin', 'pastor', 'leader')
        AND is_active = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

-- Função para verificar propriedade por auth_id
CREATE OR REPLACE FUNCTION is_owner(owner_auth_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN auth.uid() = owner_auth_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

-- Função para obter o ID do usuário atual
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS INTEGER AS $$
DECLARE
    user_id INTEGER;
BEGIN
    SELECT id INTO user_id 
    FROM users 
    WHERE auth_id = auth.uid() 
    AND is_active = true;
    
    RETURN user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

-- Função para verificar se o usuário é proprietário por ID
CREATE OR REPLACE FUNCTION is_owner_by_id(owner_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN get_current_user_id() = owner_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

-- =====================================================
-- HABILITAR RLS EM TODAS AS TABELAS
-- =====================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE routines ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE meeting_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- POLÍTICAS PARA TABELA USERS
-- =====================================================

-- Remover políticas existentes se houver
DROP POLICY IF EXISTS "users_select_policy" ON users;
DROP POLICY IF EXISTS "users_insert_policy" ON users;
DROP POLICY IF EXISTS "users_update_policy" ON users;
DROP POLICY IF EXISTS "users_delete_policy" ON users;

-- Política de SELECT: Usuários podem ver todos os usuários ativos
CREATE POLICY "users_select_policy" ON users
    FOR SELECT
    USING (
        is_active = true AND (
            auth.uid() IS NOT NULL OR
            is_admin()
        )
    );

-- Política de INSERT: Apenas admins podem criar usuários
CREATE POLICY "users_insert_policy" ON users
    FOR INSERT
    WITH CHECK (is_admin());

-- Política de UPDATE: Usuários podem atualizar próprio perfil, admins podem atualizar qualquer um
CREATE POLICY "users_update_policy" ON users
    FOR UPDATE
    USING (
        auth_id = auth.uid() OR is_admin()
    )
    WITH CHECK (
        auth_id = auth.uid() OR is_admin()
    );

-- Política de DELETE: Apenas admins podem deletar usuários
CREATE POLICY "users_delete_policy" ON users
    FOR DELETE
    USING (is_admin());

-- =====================================================
-- POLÍTICAS PARA TABELA EVENTS
-- =====================================================

-- Remover políticas existentes
DROP POLICY IF EXISTS "events_select_policy" ON events;
DROP POLICY IF EXISTS "events_insert_policy" ON events;
DROP POLICY IF EXISTS "events_update_policy" ON events;
DROP POLICY IF EXISTS "events_delete_policy" ON events;

-- Política de SELECT: Todos podem ver eventos públicos e ativos
CREATE POLICY "events_select_policy" ON events
    FOR SELECT
    USING (
        is_active = true AND (
            is_public = true OR
            is_leader() OR
            is_owner_by_id(created_by)
        )
    );

-- Política de INSERT: Líderes podem criar eventos
CREATE POLICY "events_insert_policy" ON events
    FOR INSERT
    WITH CHECK (is_leader());

-- Política de UPDATE: Criador ou líderes podem atualizar
CREATE POLICY "events_update_policy" ON events
    FOR UPDATE
    USING (
        is_owner_by_id(created_by) OR is_leader()
    )
    WITH CHECK (
        is_owner_by_id(created_by) OR is_leader()
    );

-- Política de DELETE: Apenas admins podem deletar eventos
CREATE POLICY "events_delete_policy" ON events
    FOR DELETE
    USING (is_admin());

-- =====================================================
-- POLÍTICAS PARA TABELA ATTENDANCE
-- =====================================================

-- Remover políticas existentes
DROP POLICY IF EXISTS "attendance_select_policy" ON attendance;
DROP POLICY IF EXISTS "attendance_insert_policy" ON attendance;
DROP POLICY IF EXISTS "attendance_update_policy" ON attendance;
DROP POLICY IF EXISTS "attendance_delete_policy" ON attendance;

-- Política de SELECT: Usuários podem ver própria presença, líderes veem tudo
CREATE POLICY "attendance_select_policy" ON attendance
    FOR SELECT
    USING (
        is_owner_by_id(user_id) OR is_leader()
    );

-- Política de INSERT: Líderes podem registrar presença
CREATE POLICY "attendance_insert_policy" ON attendance
    FOR INSERT
    WITH CHECK (is_leader());

-- Política de UPDATE: Líderes podem atualizar presença
CREATE POLICY "attendance_update_policy" ON attendance
    FOR UPDATE
    USING (is_leader())
    WITH CHECK (is_leader());

-- Política de DELETE: Apenas admins podem deletar registros de presença
CREATE POLICY "attendance_delete_policy" ON attendance
    FOR DELETE
    USING (is_admin());

-- =====================================================
-- POLÍTICAS PARA TABELA MEDIA_CONTENT
-- =====================================================

-- Remover políticas existentes
DROP POLICY IF EXISTS "media_select_policy" ON media_content;
DROP POLICY IF EXISTS "media_insert_policy" ON media_content;
DROP POLICY IF EXISTS "media_update_policy" ON media_content;
DROP POLICY IF EXISTS "media_delete_policy" ON media_content;

-- Política de SELECT: Todos podem ver mídia ativa
CREATE POLICY "media_select_policy" ON media_content
    FOR SELECT
    USING (is_active = true);

-- Política de INSERT: Usuários autenticados podem fazer upload
CREATE POLICY "media_insert_policy" ON media_content
    FOR INSERT
    WITH CHECK (auth.uid() IS NOT NULL);

-- Política de UPDATE: Uploader ou líderes podem atualizar
CREATE POLICY "media_update_policy" ON media_content
    FOR UPDATE
    USING (
        is_owner_by_id(uploaded_by) OR is_leader()
    )
    WITH CHECK (
        is_owner_by_id(uploaded_by) OR is_leader()
    );

-- Política de DELETE: Uploader ou admins podem deletar
CREATE POLICY "media_delete_policy" ON media_content
    FOR DELETE
    USING (
        is_owner_by_id(uploaded_by) OR is_admin()
    );

-- =====================================================
-- POLÍTICAS PARA TABELA POSTS
-- =====================================================

-- Remover políticas existentes
DROP POLICY IF EXISTS "posts_select_policy" ON posts;
DROP POLICY IF EXISTS "posts_insert_policy" ON posts;
DROP POLICY IF EXISTS "posts_update_policy" ON posts;
DROP POLICY IF EXISTS "posts_delete_policy" ON posts;

-- Política de SELECT: Todos podem ver posts ativos
CREATE POLICY "posts_select_policy" ON posts
    FOR SELECT
    USING (is_active = true);

-- Política de INSERT: Líderes podem criar posts
CREATE POLICY "posts_insert_policy" ON posts
    FOR INSERT
    WITH CHECK (is_leader());

-- Política de UPDATE: Autor ou líderes podem atualizar
CREATE POLICY "posts_update_policy" ON posts
    FOR UPDATE
    USING (
        is_owner_by_id(author_id) OR is_leader()
    )
    WITH CHECK (
        is_owner_by_id(author_id) OR is_leader()
    );

-- Política de DELETE: Autor ou admins podem deletar
CREATE POLICY "posts_delete_policy" ON posts
    FOR DELETE
    USING (
        is_owner_by_id(author_id) OR is_admin()
    );

-- =====================================================
-- POLÍTICAS PARA TABELA COMMENTS
-- =====================================================

-- Remover políticas existentes
DROP POLICY IF EXISTS "comments_select_policy" ON comments;
DROP POLICY IF EXISTS "comments_insert_policy" ON comments;
DROP POLICY IF EXISTS "comments_update_policy" ON comments;
DROP POLICY IF EXISTS "comments_delete_policy" ON comments;

-- Política de SELECT: Todos podem ver comentários ativos
CREATE POLICY "comments_select_policy" ON comments
    FOR SELECT
    USING (is_active = true);

-- Política de INSERT: Usuários autenticados podem comentar
CREATE POLICY "comments_insert_policy" ON comments
    FOR INSERT
    WITH CHECK (auth.uid() IS NOT NULL);

-- Política de UPDATE: Autor ou líderes podem atualizar
CREATE POLICY "comments_update_policy" ON comments
    FOR UPDATE
    USING (
        is_owner_by_id(author_id) OR is_leader()
    )
    WITH CHECK (
        is_owner_by_id(author_id) OR is_leader()
    );

-- Política de DELETE: Autor ou admins podem deletar
CREATE POLICY "comments_delete_policy" ON comments
    FOR DELETE
    USING (
        is_owner_by_id(author_id) OR is_admin()
    );

-- =====================================================
-- POLÍTICAS PARA TABELA ROUTINES
-- =====================================================

-- Remover políticas existentes
DROP POLICY IF EXISTS "routines_select_policy" ON routines;
DROP POLICY IF EXISTS "routines_insert_policy" ON routines;
DROP POLICY IF EXISTS "routines_update_policy" ON routines;
DROP POLICY IF EXISTS "routines_delete_policy" ON routines;

-- Política de SELECT: Usuários veem próprias rotinas, líderes veem todas
CREATE POLICY "routines_select_policy" ON routines
    FOR SELECT
    USING (
        is_active = true AND (
            is_owner_by_id(assigned_to) OR
            is_owner_by_id(created_by) OR
            is_leader()
        )
    );

-- Política de INSERT: Líderes podem criar rotinas
CREATE POLICY "routines_insert_policy" ON routines
    FOR INSERT
    WITH CHECK (is_leader());

-- Política de UPDATE: Assignee, criador ou líderes podem atualizar
CREATE POLICY "routines_update_policy" ON routines
    FOR UPDATE
    USING (
        is_owner_by_id(assigned_to) OR
        is_owner_by_id(created_by) OR
        is_leader()
    )
    WITH CHECK (
        is_owner_by_id(assigned_to) OR
        is_owner_by_id(created_by) OR
        is_leader()
    );

-- Política de DELETE: Criador ou admins podem deletar
CREATE POLICY "routines_delete_policy" ON routines
    FOR DELETE
    USING (
        is_owner_by_id(created_by) OR is_admin()
    );

-- =====================================================
-- POLÍTICAS PARA TABELA AI_CONVERSATIONS
-- =====================================================

-- Remover políticas existentes
DROP POLICY IF EXISTS "ai_conversations_select_policy" ON ai_conversations;
DROP POLICY IF EXISTS "ai_conversations_insert_policy" ON ai_conversations;
DROP POLICY IF EXISTS "ai_conversations_update_policy" ON ai_conversations;
DROP POLICY IF EXISTS "ai_conversations_delete_policy" ON ai_conversations;

-- Política de SELECT: Usuários veem próprias conversas, admins veem todas
CREATE POLICY "ai_conversations_select_policy" ON ai_conversations
    FOR SELECT
    USING (
        is_owner_by_id(user_id) OR is_admin()
    );

-- Política de INSERT: Usuários autenticados podem criar conversas
CREATE POLICY "ai_conversations_insert_policy" ON ai_conversations
    FOR INSERT
    WITH CHECK (auth.uid() IS NOT NULL);

-- Política de UPDATE: Não permitida
CREATE POLICY "ai_conversations_update_policy" ON ai_conversations
    FOR UPDATE
    USING (false);

-- Política de DELETE: Usuário pode deletar próprias conversas, admins podem deletar qualquer uma
CREATE POLICY "ai_conversations_delete_policy" ON ai_conversations
    FOR DELETE
    USING (
        is_owner_by_id(user_id) OR is_admin()
    );

-- =====================================================
-- POLÍTICAS PARA TABELA MESSAGES
-- =====================================================

-- Remover políticas existentes
DROP POLICY IF EXISTS "messages_select_policy" ON messages;
DROP POLICY IF EXISTS "messages_insert_policy" ON messages;
DROP POLICY IF EXISTS "messages_update_policy" ON messages;
DROP POLICY IF EXISTS "messages_delete_policy" ON messages;

-- Política de SELECT: Remetente e destinatário podem ver mensagens
CREATE POLICY "messages_select_policy" ON messages
    FOR SELECT
    USING (
        is_active = true AND (
            is_owner_by_id(sender_id) OR
            is_owner_by_id(recipient_id) OR
            is_admin()
        )
    );

-- Política de INSERT: Usuários autenticados podem enviar mensagens
CREATE POLICY "messages_insert_policy" ON messages
    FOR INSERT
    WITH CHECK (auth.uid() IS NOT NULL);

-- Política de UPDATE: Destinatário pode marcar como lida
CREATE POLICY "messages_update_policy" ON messages
    FOR UPDATE
    USING (
        is_owner_by_id(recipient_id) OR is_admin()
    )
    WITH CHECK (
        is_owner_by_id(recipient_id) OR is_admin()
    );

-- Política de DELETE: Remetente ou admins podem deletar
CREATE POLICY "messages_delete_policy" ON messages
    FOR DELETE
    USING (
        is_owner_by_id(sender_id) OR is_admin()
    );

-- =====================================================
-- POLÍTICAS PARA TABELA MEETING_REPORTS
-- =====================================================

-- Remover políticas existentes
DROP POLICY IF EXISTS "meeting_reports_select_policy" ON meeting_reports;
DROP POLICY IF EXISTS "meeting_reports_insert_policy" ON meeting_reports;
DROP POLICY IF EXISTS "meeting_reports_update_policy" ON meeting_reports;
DROP POLICY IF EXISTS "meeting_reports_delete_policy" ON meeting_reports;

-- Política de SELECT: Líderes podem ver relatórios
CREATE POLICY "meeting_reports_select_policy" ON meeting_reports
    FOR SELECT
    USING (
        status = 'published' OR
        is_owner_by_id(created_by) OR
        is_leader()
    );

-- Política de INSERT: Líderes podem criar relatórios
CREATE POLICY "meeting_reports_insert_policy" ON meeting_reports
    FOR INSERT
    WITH CHECK (is_leader());

-- Política de UPDATE: Criador ou líderes podem atualizar
CREATE POLICY "meeting_reports_update_policy" ON meeting_reports
    FOR UPDATE
    USING (
        is_owner_by_id(created_by) OR is_leader()
    )
    WITH CHECK (
        is_owner_by_id(created_by) OR is_leader()
    );

-- Política de DELETE: Criador ou admins podem deletar
CREATE POLICY "meeting_reports_delete_policy" ON meeting_reports
    FOR DELETE
    USING (
        is_owner_by_id(created_by) OR is_admin()
    );

-- =====================================================
-- POLÍTICAS PARA TABELA REPORT_TEMPLATES
-- =====================================================

-- Remover políticas existentes
DROP POLICY IF EXISTS "report_templates_select_policy" ON report_templates;
DROP POLICY IF EXISTS "report_templates_insert_policy" ON report_templates;
DROP POLICY IF EXISTS "report_templates_update_policy" ON report_templates;
DROP POLICY IF EXISTS "report_templates_delete_policy" ON report_templates;

-- Política de SELECT: Todos podem ver templates ativos
CREATE POLICY "report_templates_select_policy" ON report_templates
    FOR SELECT
    USING (is_active = true);

-- Política de INSERT: Líderes podem criar templates
CREATE POLICY "report_templates_insert_policy" ON report_templates
    FOR INSERT
    WITH CHECK (is_leader());

-- Política de UPDATE: Criador ou líderes podem atualizar
CREATE POLICY "report_templates_update_policy" ON report_templates
    FOR UPDATE
    USING (
        is_owner_by_id(created_by) OR is_leader()
    )
    WITH CHECK (
        is_owner_by_id(created_by) OR is_leader()
    );

-- Política de DELETE: Criador ou admins podem deletar
CREATE POLICY "report_templates_delete_policy" ON report_templates
    FOR DELETE
    USING (
        is_owner_by_id(created_by) OR is_admin()
    );

-- =====================================================
-- POLÍTICAS PARA TABELAS DE SISTEMA (ACESSO RESTRITO)
-- =====================================================

-- SECURITY_LOGS: Apenas admins
CREATE POLICY "security_logs_select_policy" ON security_logs
    FOR SELECT USING (is_admin());
CREATE POLICY "security_logs_insert_policy" ON security_logs
    FOR INSERT WITH CHECK (is_admin());
CREATE POLICY "security_logs_update_policy" ON security_logs
    FOR UPDATE USING (false); -- Não permitir updates
CREATE POLICY "security_logs_delete_policy" ON security_logs
    FOR DELETE USING (is_admin());

-- SYSTEM_SETTINGS: Apenas admins
CREATE POLICY "system_settings_select_policy" ON system_settings
    FOR SELECT USING (is_admin());
CREATE POLICY "system_settings_insert_policy" ON system_settings
    FOR INSERT WITH CHECK (is_admin());
CREATE POLICY "system_settings_update_policy" ON system_settings
    FOR UPDATE USING (is_admin()) WITH CHECK (is_admin());
CREATE POLICY "system_settings_delete_policy" ON system_settings
    FOR DELETE USING (is_admin());

-- PERFORMANCE_LOGS: Apenas admins
CREATE POLICY "performance_logs_select_policy" ON performance_logs
    FOR SELECT USING (is_admin());
CREATE POLICY "performance_logs_insert_policy" ON performance_logs
    FOR INSERT WITH CHECK (is_admin());
CREATE POLICY "performance_logs_update_policy" ON performance_logs
    FOR UPDATE USING (false); -- Não permitir updates
CREATE POLICY "performance_logs_delete_policy" ON performance_logs
    FOR DELETE USING (is_admin());

-- SYSTEM_NOTIFICATIONS: Usuários veem próprias notificações
CREATE POLICY "system_notifications_select_policy" ON system_notifications
    FOR SELECT USING (
        target_user_id IS NULL OR
        is_owner_by_id(target_user_id) OR
        (target_role IS NOT NULL AND EXISTS (
            SELECT 1 FROM users 
            WHERE auth_id = auth.uid() 
            AND role = target_role
        )) OR
        is_admin()
    );
CREATE POLICY "system_notifications_insert_policy" ON system_notifications
    FOR INSERT WITH CHECK (is_admin());
CREATE POLICY "system_notifications_update_policy" ON system_notifications
    FOR UPDATE USING (
        is_owner_by_id(target_user_id) OR is_admin()
    ) WITH CHECK (
        is_owner_by_id(target_user_id) OR is_admin()
    );
CREATE POLICY "system_notifications_delete_policy" ON system_notifications
    FOR DELETE USING (is_admin());

-- AUDIT_LOG: Apenas admins
CREATE POLICY "audit_log_select_policy" ON audit_log
    FOR SELECT USING (is_admin());
CREATE POLICY "audit_log_insert_policy" ON audit_log
    FOR INSERT WITH CHECK (is_admin());
CREATE POLICY "audit_log_update_policy" ON audit_log
    FOR UPDATE USING (false); -- Não permitir updates
CREATE POLICY "audit_log_delete_policy" ON audit_log
    FOR DELETE USING (is_admin());

-- =====================================================
-- TRIGGER PARA SINCRONIZAÇÃO DE USUÁRIOS
-- =====================================================

-- Função para criar usuário automaticamente quando um novo usuário se registra
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO users (auth_id, username, email, full_name, role)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1)),
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
        'member'
    )
    ON CONFLICT (auth_id) DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

-- Trigger para criar usuário automaticamente
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- =====================================================
-- GRANTS PARA SERVICE ROLE
-- =====================================================

-- Garantir que o service role tenha acesso total
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- Garantir que usuários autenticados tenham acesso básico
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- =====================================================
-- FINALIZAÇÃO
-- =====================================================
-- Políticas RLS configuradas com sucesso!
-- Todas as tabelas estão protegidas com Row Level Security
-- Funções auxiliares criadas para verificação de permissões
-- Sistema pronto para uso com autenticação Supabase