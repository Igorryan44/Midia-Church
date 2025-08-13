"""
Inicialização do banco de dados
"""
import sqlite3
import os
from pathlib import Path
import bcrypt

def init_database():
    """Inicializa o banco de dados com as tabelas básicas"""
    try:
        # Caminho para o banco de dados
        db_path = Path("data/church_media.db")
        
        # Criar diretório se não existir
        db_path.parent.mkdir(exist_ok=True)
        
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Criar tabelas básicas
        cursor.executescript("""
        -- Tabela de usuários
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'leader', 'member')),
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            failed_login_attempts INTEGER DEFAULT 0,
            account_locked_until DATETIME,
            password_changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            two_factor_enabled BOOLEAN DEFAULT FALSE,
            two_factor_secret TEXT
        );

        -- Tabela de eventos
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            event_type TEXT NOT NULL CHECK (event_type IN ('culto', 'reuniao', 'evento_especial', 'ensaio', 'outro')),
            date DATE NOT NULL,
            time TIME NOT NULL,
            location TEXT,
            created_by INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER,
            updated_at DATETIME,
            version INTEGER DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id)
        );

        -- Tabela de mensagens
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            recipient_id INTEGER,
            recipient_group TEXT,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            read_at DATETIME,
            delivered_at DATETIME,
            delivery_status TEXT DEFAULT 'pending' CHECK (delivery_status IN ('pending', 'sent', 'delivered', 'failed')),
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (recipient_id) REFERENCES users(id)
        );

        -- Tabela de presença
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('present', 'absent', 'late')),
            notes TEXT,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            recorded_by INTEGER,
            FOREIGN KEY (event_id) REFERENCES events(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (recorded_by) REFERENCES users(id),
            UNIQUE(event_id, user_id)
        );

        -- Tabela de logs de segurança
        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT NOT NULL,
            description TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Índices para otimização
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);
        CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
        CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
        CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id);
        CREATE INDEX IF NOT EXISTS idx_attendance_event ON attendance(event_id);
        CREATE INDEX IF NOT EXISTS idx_attendance_user ON attendance(user_id);
        CREATE INDEX IF NOT EXISTS idx_security_logs_timestamp ON security_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_security_logs_user ON security_logs(user_id);
        """)
        
        # Verificar se já existe um usuário admin
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            # Criar usuário admin padrão
            password = "admin123"
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            """, ("admin", "admin@church.com", password_hash, "Administrador", "admin"))
            
            print("👤 Usuário administrador criado:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   ⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
        
        conn.commit()
        conn.close()
        
        print("✅ Banco de dados inicializado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        return False

if __name__ == "__main__":
    init_database()