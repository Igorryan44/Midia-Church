# Guia de Dependências - Mídia Church

Este documento explica os diferentes arquivos de dependências do projeto e como utilizá-los.

## Arquivos de Dependências

### 1. `requirements.txt` (Principal)
**Uso:** Instalação completa do projeto com pip
```bash
pip install -r requirements.txt
```

**Conteúdo:** Todas as dependências necessárias para executar o projeto, organizadas por categoria:
- Core Framework (Streamlit)
- Data Processing (Pandas, NumPy)
- Database (SQLAlchemy, Supabase, PostgreSQL)
- Authentication & Security
- Visualization (Plotly)
- System & Performance
- Environment & Configuration
- HTTP & API
- Phone & Communication
- File Processing
- QR Code & Automation
- Email
- Development & Testing (opcional)
- Utilities

### 2. `requirements_supabase.txt` (Específico)
**Uso:** Instalação mínima para funcionalidades do Supabase
```bash
pip install -r requirements_supabase.txt
```

**Conteúdo:** Dependências mínimas necessárias para:
- Conexão com Supabase
- Migração de dados
- Operações básicas de banco de dados
- Ferramentas de desenvolvimento

### 3. `pyproject.toml` (Poetry)
**Uso:** Gerenciamento de dependências com Poetry
```bash
poetry install
```

**Conteúdo:** Configuração completa do projeto incluindo:
- Metadados do projeto
- Dependências de produção
- Dependências de desenvolvimento
- Scripts de execução
- Configurações de build

### 4. `package.json` (Node.js)
**Uso:** Dependências JavaScript para WhatsApp API
```bash
npm install
```

**Conteúdo:** Dependências Node.js para:
- WhatsApp Web.js
- Servidor Express
- Utilitários JavaScript

## Instalação Recomendada

### Opção 1: Usando pip (Recomendado)
```bash
# Instalar todas as dependências
pip install -r requirements.txt

# Instalar dependências Node.js para WhatsApp
npm install
```

### Opção 2: Usando Poetry
```bash
# Instalar dependências Python
poetry install

# Instalar dependências Node.js
npm install
```

### Opção 3: Apenas Supabase
```bash
# Para desenvolvimento focado em Supabase
pip install -r requirements_supabase.txt
```

## Dependências por Categoria

### Core Framework
- **streamlit**: Interface web principal
- **streamlit-calendar**: Componente de calendário

### Data Processing
- **pandas**: Manipulação de dados
- **numpy**: Computação numérica

### Database
- **sqlalchemy**: ORM para banco de dados
- **psycopg2-binary**: Driver PostgreSQL
- **supabase**: Cliente Supabase
- **alembic**: Migrações de banco

### Authentication & Security
- **bcrypt**: Hash de senhas
- **bleach**: Sanitização de HTML

### Visualization
- **plotly**: Gráficos interativos

### System & Performance
- **psutil**: Monitoramento do sistema

### Environment & Configuration
- **python-dotenv**: Variáveis de ambiente
- **pytz**: Fusos horários

### HTTP & API
- **requests**: Cliente HTTP

### Phone & Communication
- **phonenumbers**: Validação de telefones

### File Processing
- **openpyxl**: Arquivos Excel
- **reportlab**: Geração de PDFs
- **pillow**: Processamento de imagens

### QR Code & Automation
- **qrcode**: Geração de QR codes
- **pywhatkit**: Automação WhatsApp
- **selenium**: Automação web
- **webdriver-manager**: Gerenciamento de drivers

### Email
- **email-validator**: Validação de emails

### Development & Testing
- **pytest**: Framework de testes
- **pytest-asyncio**: Testes assíncronos
- **black**: Formatação de código
- **flake8**: Linting
- **mypy**: Verificação de tipos

### Utilities
- **tqdm**: Barras de progresso
- **click**: Interface de linha de comando
- **postgrest**: Cliente PostgREST

## Versões Mínimas

Todas as dependências usam versões mínimas (>=) para garantir compatibilidade e permitir atualizações de segurança automáticas.

## Atualizações

Para atualizar as dependências:

```bash
# Com pip
pip install --upgrade -r requirements.txt

# Com poetry
poetry update

# Node.js
npm update
```

## Problemas Comuns

### 1. Erro de instalação do psycopg2
```bash
# No Windows, use a versão binary
pip install psycopg2-binary
```

### 2. Erro de instalação do numpy
```bash
# Instalar dependências do sistema primeiro
pip install --upgrade pip setuptools wheel
pip install numpy
```

### 3. Problemas com Selenium
```bash
# Instalar webdriver-manager para gerenciamento automático
pip install webdriver-manager
```

## Suporte

Para problemas com dependências, verifique:
1. Versão do Python (>= 3.9)
2. Versão do pip (>= 21.0)
3. Versão do Node.js (>= 16.0) para WhatsApp API
4. Logs de instalação para erros específicos