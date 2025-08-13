-- Esquema para relatórios de reuniões
-- Adiciona tabela para armazenar relatórios de reuniões com formatação Markdown

-- Tabela de relatórios de reuniões
CREATE TABLE IF NOT EXISTS meeting_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL, -- Conteúdo em Markdown
    summary TEXT, -- Resumo executivo
    participants TEXT, -- Lista de participantes (JSON)
    decisions TEXT, -- Decisões tomadas
    action_items TEXT, -- Itens de ação (JSON)
    next_steps TEXT, -- Próximos passos
    attachments TEXT, -- Anexos (JSON com URLs/paths)
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER,
    updated_at DATETIME,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    version INTEGER DEFAULT 1,
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

-- Tabela para templates de relatórios
CREATE TABLE IF NOT EXISTS report_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    template_content TEXT NOT NULL, -- Template em Markdown
    event_type TEXT, -- Tipo de evento para o qual o template é adequado
    is_default BOOLEAN DEFAULT FALSE,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Índices para otimização
CREATE INDEX IF NOT EXISTS idx_meeting_reports_event ON meeting_reports(event_id);
CREATE INDEX IF NOT EXISTS idx_meeting_reports_created_by ON meeting_reports(created_by);
CREATE INDEX IF NOT EXISTS idx_meeting_reports_status ON meeting_reports(status);
CREATE INDEX IF NOT EXISTS idx_meeting_reports_created_at ON meeting_reports(created_at);
CREATE INDEX IF NOT EXISTS idx_report_templates_event_type ON report_templates(event_type);
CREATE INDEX IF NOT EXISTS idx_report_templates_is_active ON report_templates(is_active);

-- Inserir templates padrão
INSERT OR IGNORE INTO report_templates (name, description, template_content, event_type, is_default, created_by) VALUES 
('Relatório de Culto', 'Template padrão para relatórios de cultos', 
'# Relatório de Culto - {{title}}

## Informações Gerais
- **Data:** {{date}}
- **Horário:** {{time}}
- **Local:** {{location}}
- **Responsável:** {{leader}}

## Participação
- **Total de Participantes:** 
- **Novos Visitantes:** 
- **Membros Presentes:** 

## Programação
### Louvor e Adoração
- **Equipe de Louvor:** 
- **Músicas Ministradas:**
  - 
  - 
  - 

### Pregação
- **Pregador:** 
- **Tema/Texto:** 
- **Pontos Principais:**
  - 
  - 
  - 

## Decisões e Anúncios
- 
- 

## Observações
- 

## Próximos Passos
- 
- 

---
*Relatório gerado em {{generated_date}}*', 'Culto', TRUE, 1),

('Relatório de Reunião', 'Template padrão para reuniões administrativas',
'# Relatório de Reunião - {{title}}

## Informações da Reunião
- **Data:** {{date}}
- **Horário:** {{time}}
- **Local:** {{location}}
- **Facilitador:** {{leader}}

## Participantes
{{participants}}

## Pauta
1. 
2. 
3. 

## Discussões e Decisões

### Item 1
**Discussão:**
- 

**Decisão:**
- 

### Item 2
**Discussão:**
- 

**Decisão:**
- 

## Itens de Ação
| Ação | Responsável | Prazo | Status |
|------|-------------|-------|--------|
|      |             |       |        |
|      |             |       |        |

## Próxima Reunião
- **Data:** 
- **Pauta Prévia:** 

## Observações
- 

---
*Relatório gerado em {{generated_date}}*', 'Reunião', TRUE, 1),

('Relatório de Evento Especial', 'Template para eventos especiais e celebrações',
'# Relatório de Evento - {{title}}

## Detalhes do Evento
- **Data:** {{date}}
- **Horário:** {{time}}
- **Local:** {{location}}
- **Organizador:** {{leader}}

## Participação
- **Total de Participantes:** 
- **Convidados Especiais:** 
- **Equipe de Apoio:** 

## Programação Realizada
### Abertura
- 

### Atividades Principais
- 
- 
- 

### Encerramento
- 

## Resultados Alcançados
- 
- 

## Feedback dos Participantes
### Pontos Positivos
- 
- 

### Pontos de Melhoria
- 
- 

## Recursos Utilizados
- **Financeiro:** 
- **Material:** 
- **Humano:** 

## Lições Aprendidas
- 
- 

## Recomendações para Próximos Eventos
- 
- 

---
*Relatório gerado em {{generated_date}}*', 'Evento Especial', TRUE, 1);