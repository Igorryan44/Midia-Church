# 🎵 Mídia Church - Sistema de Gerenciamento de Igreja

<div align="center">

![Mídia Church](https://img.shields.io/badge/Mídia%20Church-v2.0.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red?style=for-the-badge&logo=streamlit)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-orange?style=for-the-badge&logo=postgresql)

**Sistema completo de gerenciamento para igrejas com foco em mídia e comunicação**

[🚀 Instalação](#-instalação) • [📖 Documentação](#-documentação) • [🎯 Funcionalidades](#-funcionalidades) • [🔧 Configuração](#-configuração)

</div>

---

## 📋 Sobre o Projeto

O **Mídia Church** é um sistema completo de gerenciamento desenvolvido especificamente para igrejas, com foco especial em gestão de mídia, comunicação e administração de membros. O sistema oferece uma interface moderna e intuitiva para facilitar o dia a dia da administração eclesiástica.

### 🎯 Objetivo

Centralizar e simplificar a gestão de:
- 👥 **Membros e usuários**
- 📅 **Eventos e programações**
- 📊 **Presença e frequência**
- 🎬 **Conteúdo multimídia**
- 💬 **Comunicação interna**
- 🤖 **Assistente IA integrado**
- 📈 **Relatórios e analytics**

---

## ✨ Funcionalidades Principais

### 🏠 Dashboard Inteligente
- 📊 Visão geral de estatísticas em tempo real
- 📈 Gráficos de crescimento e engajamento
- 📊 **Estatísticas de Conteúdo Multimídia**
  - Distribuição por tipo de arquivo
  - Uploads recentes (últimos 7 dias)
  - Tamanho total de arquivos
  - Contadores por categoria
- 🔔 Notificações e alertas importantes
- 📱 Interface responsiva para todos os dispositivos

### 👥 Gestão de Membros
- ✅ Cadastro completo de membros
- 🔐 Sistema de autenticação seguro
- 👤 Perfis personalizados por função
- 📞 Informações de contato centralizadas
- 📊 Relatórios de crescimento de membros

### 📅 Gerenciamento de Eventos
- 🗓️ Calendário interativo
- ⏰ Agendamento de cultos e reuniões
- 📋 Lista de presença digital
- 📊 Relatórios de frequência
- ✅ **Sistema de Validação Avançado**
  - Validação de datas e horários
  - Verificação de conflitos
  - Campos obrigatórios
- 📈 Gráficos de eventos por tipo

### 🎬 Centro de Mídia
- 📸 Upload e organização de fotos
- 🎥 Gerenciamento de vídeos
- 🎵 Biblioteca de áudios
- 📱 Galeria responsiva
- 🏷️ **Sistema de Tags e Categorização**
- 📊 **Estatísticas de Conteúdo**
  - Análise por tipo de arquivo
  - Histórico de uploads
  - Gestão de espaço
- 🔍 Busca avançada por metadados

### 💬 Sistema de Comunicação
- 📧 Envio de emails em massa
- 💬 Mensagens internas
- 📢 Avisos e comunicados
- 📱 Notificações push
- 📱 **Integração WhatsApp**
  - Envio de mensagens
  - Grupos automatizados
  - Templates personalizados

### 🤖 Assistente IA
- 💡 Sugestões inteligentes
- 📝 Geração de conteúdo
- 🔍 Busca avançada
- 📊 Análises preditivas
- 📖 **Integração com Bíblia**
  - Múltiplas versões
  - Busca por versículos
  - Sugestões contextuais

### 🛡️ Segurança e Auditoria
- 🔒 Autenticação robusta
- 📝 Logs de segurança detalhados
- 🔐 Controle de acesso por função
- 🛡️ Proteção de dados
- 📊 **Monitoramento em Tempo Real**
  - Tentativas de login
  - Ações administrativas
  - Alertas de segurança

---

## 🚀 Instalação

### Pré-requisitos

- **Python 3.8+**
- **Git**
- **Conta no Supabase** (para produção)

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/midia-church.git
cd midia-church
```

### 2. Configuração do Ambiente

#### Windows
```bash
# Execute o script de configuração
setup.bat
```

#### Linux/macOS
```bash
# Execute o script de configuração
chmod +x setup.sh
./setup.sh
```

#### Manual
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configuração das Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
# Configure suas credenciais do Supabase no arquivo .env
```

### 4. Executar a Aplicação

```bash
# Iniciar o servidor
streamlit run app/main.py

# Ou usar o script de execução
python run.py
```

A aplicação estará disponível em: `http://localhost:8501`

---

## 🔧 Configuração

### Variáveis de Ambiente

```env
# Configurações do Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_chave_publica
SUPABASE_SERVICE_KEY=sua_chave_servico

# Banco de dados
DATABASE_URL=postgresql://postgres:senha@host:5432/database

# Email (opcional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_app

# Configurações da aplicação
SECRET_KEY=sua_chave_secreta_aqui
DEBUG=false
```

### Credenciais Padrão

- **Usuário:** `admin`
- **Senha:** `admin123`

> ⚠️ **Importante:** Altere as credenciais padrão após o primeiro login!

---

## 📖 Documentação

### Estrutura do Projeto

```
mídia-church/
├── app/                    # Código principal da aplicação
│   ├── components/         # Componentes reutilizáveis
│   │   ├── sidebar.py     # Barra lateral
│   │   ├── ui_enhanced.py # Interface aprimorada
│   │   └── widgets.py     # Widgets customizados
│   ├── config/            # Configurações
│   │   ├── settings.py    # Configurações gerais
│   │   ├── timezone.py    # Configurações de fuso horário
│   │   └── whatsapp_config.py # Configurações WhatsApp
│   ├── data/              # Dados e estruturas
│   │   ├── bible_data/    # Dados bíblicos
│   │   ├── bible_loader.py # Carregador de bíblia
│   │   └── sample_verses.py # Versículos de exemplo
│   ├── database/          # Modelos e conexões
│   │   ├── connection.py  # Conexão principal
│   │   ├── models.py      # Modelos de dados
│   │   ├── supabase_connection.py # Conexão Supabase
│   │   └── *.sql         # Scripts SQL
│   ├── modules/           # Módulos funcionais
│   │   ├── dashboard.py   # Dashboard principal
│   │   ├── ai_assistant.py # Assistente IA
│   │   ├── content_management.py # Gestão de conteúdo
│   │   ├── communication.py # Sistema de comunicação
│   │   ├── attendance.py  # Controle de presença
│   │   ├── bible.py       # Módulo bíblico
│   │   └── whatsapp.py    # Integração WhatsApp
│   ├── pages/             # Páginas específicas
│   │   ├── security.py    # Página de segurança
│   │   ├── monitoring.py  # Monitoramento
│   │   ├── backup.py      # Sistema de backup
│   │   └── notifications.py # Notificações
│   ├── utils/             # Utilitários
│   │   ├── auth.py        # Autenticação
│   │   ├── validation.py  # Validação de dados
│   │   ├── email_service.py # Serviço de email
│   │   ├── security_enhanced.py # Segurança avançada
│   │   ├── backup_system.py # Sistema de backup
│   │   └── monitoring.py  # Monitoramento
│   └── main.py           # Arquivo principal
├── data/                  # Dados locais
│   ├── uploads/          # Arquivos enviados
│   └── *.db             # Bancos de dados locais
├── static/               # Arquivos estáticos
├── uploads/              # Uploads de usuários
├── backups/              # Backups automáticos
├── logs/                 # Logs do sistema
├── .streamlit/           # Configurações Streamlit
├── requirements.txt      # Dependências Python
├── .env.example         # Exemplo de configuração
├── .gitignore           # Arquivos ignorados pelo Git
├── Dockerfile           # Configuração Docker
├── docker-compose.yml   # Orquestração Docker
├── run.py               # Script de execução
└── README.md            # Este arquivo
```

### Guias Disponíveis

- 📋 [Guia de Migração](GUIA_MIGRACAO.md) - Migração para Supabase
- 🎨 [Guia de Cores](COLORS.md) - Paleta de cores do sistema
- 🗑️ [Arquivos Removidos](ARQUIVOS_REMOVIDOS.md) - Histórico de limpeza

### Funcionalidades Recentes

#### 🆕 Dashboard Aprimorado
- **Estatísticas de Conteúdo Multimídia**: Visualização completa de uploads, tipos de arquivo e uso de espaço
- **Gráficos Interativos**: Distribuição de conteúdo por tipo com tradução para português
- **Métricas em Tempo Real**: Contadores de uploads recentes e estatísticas detalhadas

#### 🆕 Sistema de Validação
- **Validação Avançada de Eventos**: Verificação de datas, horários e conflitos
- **Campos Obrigatórios**: Validação robusta de formulários
- **Feedback Visual**: Mensagens de erro claras e intuitivas

#### 🆕 Centro de Mídia Completo
- **Gestão de Conteúdo**: Upload, categorização e organização de arquivos
- **Sistema de Tags**: Organização avançada por categorias e tags
- **Análise de Uso**: Estatísticas detalhadas de armazenamento e tipos de arquivo

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.8+** - Linguagem principal
- **Streamlit** - Framework web
- **SQLAlchemy** - ORM para banco de dados
- **PostgreSQL** - Banco de dados (via Supabase)
- **Supabase** - Backend as a Service

### Frontend
- **Streamlit** - Interface web
- **HTML/CSS** - Customizações
- **JavaScript** - Interatividade
- **Bootstrap** - Framework CSS

### Integrações
- **OpenAI API** - Assistente IA
- **SMTP** - Envio de emails
- **Supabase Storage** - Armazenamento de arquivos

---

## 🔄 Migração e Deploy

### Migração para Supabase

1. Configure suas credenciais no `.env`
2. Execute o script de migração:
   ```bash
   python migrate_to_supabase.py
   ```
3. Verifique as tabelas no painel do Supabase

### Deploy em Produção

#### Streamlit Cloud
1. Conecte seu repositório GitHub
2. Configure as variáveis de ambiente
3. Deploy automático

#### Docker (Opcional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app/main.py"]
```

---

## 🤝 Contribuição

### Como Contribuir

1. **Fork** o projeto
2. Crie uma **branch** para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. **Commit** suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. **Push** para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um **Pull Request**

### Padrões de Código

- Siga o **PEP 8** para Python
- Use **type hints** quando possível
- Documente funções complexas
- Escreva testes para novas funcionalidades

---

## 📊 Status do Projeto

- ✅ **Sistema de autenticação** - Completo
- ✅ **Dashboard principal** - Completo
  - ✅ Estatísticas em tempo real
  - ✅ Gráficos de conteúdo por tipo
  - ✅ Métricas de uploads recentes
  - ✅ Análise de espaço utilizado
- ✅ **Gestão de membros** - Completo
- ✅ **Gerenciamento de eventos** - Completo
  - ✅ Sistema de validação avançado
  - ✅ Verificação de conflitos
  - ✅ Relatórios de frequência
- ✅ **Centro de mídia** - Completo
  - ✅ Upload de múltiplos formatos
  - ✅ Sistema de tags e categorização
  - ✅ Estatísticas detalhadas
  - ✅ Busca avançada
- ✅ **Sistema de comunicação** - Completo
  - ✅ Integração WhatsApp
  - ✅ Templates personalizados
  - ✅ Envio em massa
- ✅ **Assistente IA** - Completo
  - ✅ Integração com múltiplas versões da Bíblia
  - ✅ Sugestões contextuais
  - ✅ Análises preditivas
- ✅ **Migração Supabase** - Completo
- ✅ **Sistema de segurança** - Completo
  - ✅ Logs detalhados
  - ✅ Monitoramento em tempo real
  - ✅ Alertas de segurança
- ✅ **Sistema de backup** - Completo
- 🔄 **Testes automatizados** - Em desenvolvimento
- 🔄 **API REST** - Planejado
- 🔄 **App mobile** - Planejado

---

## 🐛 Suporte e Issues

### Reportar Problemas

1. Verifique se o problema já foi reportado
2. Use o template de issue apropriado
3. Inclua informações detalhadas:
   - Versão do Python
   - Sistema operacional
   - Logs de erro
   - Passos para reproduzir

### Suporte

- 📧 **Email:** suporte@midiacurch.com
- 💬 **Discord:** [Servidor da Comunidade](#)
- 📖 **Wiki:** [Documentação Completa](#)

---

## 📄 Licença

Este projeto está sob licença proprietária. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 🙏 Agradecimentos

- **Equipe de desenvolvimento** - Pela dedicação ao projeto
- **Comunidade Streamlit** - Pelo framework incrível
- **Supabase** - Pela infraestrutura robusta
- **Igrejas parceiras** - Pelo feedback valioso

---

<div align="center">

**Desenvolvido com ❤️ para a comunidade cristã**

[⬆ Voltar ao topo](#-mídia-church---sistema-de-gerenciamento-de-igreja)

</div>