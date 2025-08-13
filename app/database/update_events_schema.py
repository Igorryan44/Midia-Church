#!/usr/bin/env python3
"""
Script para atualizar o schema da tabela events com novos campos
"""

import sqlite3
import os

def update_events_schema():
    """Adiciona novos campos à tabela events se não existirem"""
    
    # Caminho do banco de dados
    db_path = 'data/church_media.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar quais colunas já existem
        cursor.execute("PRAGMA table_info(events)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Lista de novos campos para adicionar
        new_fields = [
            ("max_attendees", "INTEGER DEFAULT 0"),
            ("requires_registration", "BOOLEAN DEFAULT FALSE"),
            ("is_public", "BOOLEAN DEFAULT TRUE"),
            ("start_datetime", "TEXT"),
            ("end_datetime", "TEXT")
        ]
        
        # Adicionar campos que não existem
        for field_name, field_definition in new_fields:
            if field_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE events ADD COLUMN {field_name} {field_definition}")
                    print(f"✅ Campo '{field_name}' adicionado com sucesso")
                except sqlite3.Error as e:
                    print(f"⚠️ Erro ao adicionar campo '{field_name}': {e}")
        
        # Verificar se as colunas date e time existem para migração
        if 'date' in existing_columns and 'time' in existing_columns:
            # Atualizar campos start_datetime e end_datetime se estiverem vazios
            cursor.execute("""
                UPDATE events 
                SET start_datetime = date || 'T' || time || ':00'
                WHERE start_datetime IS NULL OR start_datetime = ''
            """)
            
            cursor.execute("""
                UPDATE events 
                SET end_datetime = date || 'T' || CASE 
                    WHEN time IS NOT NULL THEN 
                        printf('%02d:%02d:00', 
                            (CAST(substr(time, 1, 2) AS INTEGER) + 2) % 24,
                            CAST(substr(time, 4, 2) AS INTEGER)
                        )
                    ELSE '12:00:00'
                END
                WHERE end_datetime IS NULL OR end_datetime = ''
            """)
            print("✅ Campos de data/hora migrados com sucesso")
        else:
            print("ℹ️ Campos date/time não encontrados - schema já atualizado")
        
        conn.commit()
        conn.close()
        
        print("✅ Schema da tabela events atualizado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar schema: {e}")
        return False

if __name__ == "__main__":
    update_events_schema()