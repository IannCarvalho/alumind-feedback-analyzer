# FeedLens

[![CI](https://github.com/IannCarvalho/feedlens/actions/workflows/ci.yml/badge.svg)](https://github.com/IannCarvalho/feedlens/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

Uma lente sobre o feedback dos seus usuários: análise automática de feedback com Inteligência Artificial, usando Python, Flask e LLMs.

## Sobre o Projeto

O FeedLens recebe feedbacks de usuários, classifica-os por sentimento, detecta spam e identifica as funcionalidades mais pedidas — e disponibiliza tudo em um dashboard web e em um resumo semanal por e-mail. Ele resolve o gargalo de analisar manualmente feedbacks que chegam de muitos canais (atendimento, comunidades, redes sociais).

A aplicação é responsável por:

1. **Classificação de feedback** por sentimento (POSITIVO, NEGATIVO, INCONCLUSIVO)
2. **Identificação de funcionalidades solicitadas** nos feedbacks
3. **Detecção de spam** nos feedbacks
4. **Dashboard web** com estatísticas e visualizações
5. **Resumo semanal** enviado por e-mail aos stakeholders

## Estrutura do Projeto

```
feedlens/
├── app/                           # Diretório principal da aplicação
│   ├── __init__.py                # Inicialização da aplicação Flask (app factory)
│   ├── config.py                  # Configurações da aplicação
│   ├── models/                    # Modelos de dados
│   │   └── feedback.py            # Modelos Feedback e RequestedFeature
│   ├── routes/                    # Rotas da aplicação
│   │   ├── api.py                 # Endpoints da API REST
│   │   └── web.py                 # Rotas da interface web
│   ├── services/                  # Serviços da aplicação
│   │   ├── email_service.py       # Envio de e-mails (resumo semanal)
│   │   ├── feedback_analyzer.py   # Análise de feedback com LLM
│   │   ├── feedback_service.py    # Gerenciamento de feedbacks
│   │   └── statistics_service.py  # Cálculo de estatísticas
│   └── templates/                 # Templates HTML
│       ├── base.html              # Template base
│       ├── dashboard.html         # Dashboard principal
│       ├── feedback_detail.html   # Detalhes de um feedback
│       └── feedback_list.html     # Lista de feedbacks
├── migrations/                    # Migrações de banco de dados (Alembic)
├── .env-example                   # Exemplo de variáveis de ambiente
├── .gitignore                     # Arquivos ignorados pelo Git
├── README.md                      # Este arquivo
├── requirements.txt               # Dependências do projeto
├── run.py                         # Ponto de entrada da aplicação
└── test_email.py                  # Script para testar o envio de e-mail
```

## Tecnologias Utilizadas

- **Backend:**
  - Python 3.10+
  - Flask (framework web)
  - SQLAlchemy & Flask-SQLAlchemy (ORM)
  - Flask-Migrate (migrações de banco de dados)
  - APScheduler (agendamento de tarefas)

- **Banco de Dados:**
  - PostgreSQL (recomendado)
  - SQLite (alternativa para desenvolvimento)

- **Inteligência Artificial:**
  - OpenAI API (GPT-4o-mini por padrão)
  - LangChain (integração com LLMs)

- **Frontend:**
  - HTML, CSS, JavaScript
  - Bootstrap 5 (framework CSS)
  - Chart.js (visualização de dados)
  - Font Awesome (ícones)

- **Envio de E-mail:**
  - SMTP (via `smtplib` do Python)

- **Ambiente:**
  - python-dotenv (gerenciamento de variáveis de ambiente)

## Configuração do Ambiente

### Pré-requisitos

- Python 3.10 ou superior
- PostgreSQL ou outro banco de dados SQL (ou SQLite para desenvolvimento)
- Chave de API da OpenAI

### Instalação

1. Clone o repositório:
```bash
git clone https://github.com/IannCarvalho/feedlens.git
cd feedlens
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv

# No Windows
venv\Scripts\activate

# No Linux/macOS
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Crie um arquivo `.env` baseado no `.env-example`:
```bash
cp .env-example .env
```

5. Edite o arquivo `.env` com suas credenciais:
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=sua_chave_secreta
DASHBOARD_PASSWORD=senha_de_acesso_ao_painel
DATABASE_URL=postgresql://usuario:senha@localhost/feedlens
OPENAI_API_KEY=sua_chave_api_openai
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=30
OPENAI_MAX_RETRIES=2
EMAIL_HOST=smtp.exemplo.com
EMAIL_PORT=587
EMAIL_USER=seu_email@exemplo.com
EMAIL_PASSWORD=sua_senha_email
EMAIL_USE_TLS=true
EMAIL_RECIPIENTS=stakeholder1@exemplo.com,stakeholder2@exemplo.com
```

6. Crie as tabelas aplicando as migrations versionadas (`migrations/versions/`):
```bash
flask db upgrade
```

   **Já tem um banco criado antes das migrations versionadas** (por `flask db migrate` ou `db.create_all()`)? Marque-o como estando no baseline e só então atualize, para não tentar recriar as tabelas:
```bash
flask db stamp 0001
flask db upgrade
```

   Ao mudar um modelo, gere a revisão com `flask db migrate -m "descrição"`, **revise o arquivo gerado** e commite-o. O CI roda `flask db check` num Postgres e falha se os modelos e as migrations divergirem.

### Executando a Aplicação

Para iniciar a aplicação em modo de desenvolvimento:

```bash
flask run
```

A aplicação estará disponível em `http://localhost:5000`.

> **Nota de segurança:** por padrão, em desenvolvimento, o servidor roda com `debug=True` e faz bind em `0.0.0.0`. Em produção, use um servidor WSGI (ex: `gunicorn`), desligue o debug e defina `FLASK_ENV=production`.

### Autenticação do Dashboard

As rotas web do painel (`/`, `/dashboard`, `/feedbacks`, `/feedback/<id>`) são protegidas por uma **senha única compartilhada**, definida em `DASHBOARD_PASSWORD`. Ao acessar sem sessão, o usuário é levado à tela de login (`/login`); a sessão fica num cookie assinado pela `SECRET_KEY`.

- **Com `DASHBOARD_PASSWORD` definida:** o painel exige login e exibe um botão "Sair".
- **Sem `DASHBOARD_PASSWORD` (vazia):** o painel fica aberto, sem login — conveniente em desenvolvimento. Em produção sem senha, um aviso é registrado no log.

Proteções do login e da sessão:

- **`SECRET_KEY` forte em produção:** o app recusa subir com placeholder ou chave com menos de 32 caracteres, já que quem conhece a chave assina um cookie "autenticado" sem saber a senha. Gere uma localmente com `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
- **Força-bruta:** o `POST /login` é limitado por IP (`RATELIMIT_LOGIN`, padrão `10 per minute`).
- **Sessão com validade:** o login expira após `SESSION_LIFETIME_HOURS` (padrão 12h).
- **Cookie:** `HttpOnly`, `SameSite=Lax` e `Secure` (padrão em produção; `SESSION_COOKIE_SECURE=false` só para HTTP local).
- **Redirect pós-login:** o parâmetro `next` só aceita caminhos locais (`//host`, `/\host` e esquemas externos são descartados).

A API (`/api/...`) **não** é afetada por essa autenticação: ela tem seu próprio contrato de ingestão de feedbacks.

### Executando com Docker

O projeto inclui um `Dockerfile` (gunicorn servindo `wsgi:app`) e um `docker-compose.yml` que sobe a aplicação junto de um PostgreSQL.

O compose exige uma `SECRET_KEY` aleatória (32+ caracteres) e falha logo no `up` sem ela; defina-a no `.env` ou no shell (ex.: `$env:SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(48))"` no PowerShell). Como ele serve HTTP em `localhost`, o compose desliga o cookie `Secure` por padrão (`SESSION_COOKIE_SECURE=false`).

```bash
# A OPENAI_API_KEY e obrigatoria em producao (FLASK_ENV=production)
export OPENAI_API_KEY=sua-chave   # no Windows: $env:OPENAI_API_KEY="sua-chave"
docker compose up --build
```

A aplicação sobe em `http://localhost:5000` e o Postgres em `localhost:5432`. As variáveis de ambiente têm defaults no compose; sobrescreva via `.env` ou pelo shell.

Na primeira execução, crie as tabelas no banco (o container `web` compartilha o código):

```bash
docker compose exec web flask db upgrade
```

## Endpoints da API

### Enviar Feedback

**Endpoint:** `POST /api/feedbacks`

**Descrição:** Recebe e analisa um feedback, classificando-o por sentimento, detectando spam e identificando funcionalidades solicitadas.

**Corpo da Requisição:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "feedback": "Gosto muito do app! Só queria uma forma mais fácil de editar o meu perfil dentro da minha conta."
}
```

**Resposta de Sucesso (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sentiment": "POSITIVO",
  "is_spam": false,
  "requested_features": [
    {
      "code": "EDITAR_PERFIL",
      "reason": "O usuário gostaria de realizar a edição do próprio perfil"
    }
  ]
}
```

**Rate limiting:** este endpoint público é limitado (padrão `30 per minute` por IP) via [Flask-Limiter](https://flask-limiter.readthedocs.io/). Ao exceder o limite a resposta é `429 Too Many Requests` com corpo JSON. Configurável por `RATELIMIT_INGEST`, `RATELIMIT_ENABLED` e `RATELIMIT_STORAGE_URI` (use `redis://...` em produção com múltiplos workers; o default `memory://` serve a um único processo). Os endpoints `GET` não são limitados.

**CORS:** as rotas `/api/*` têm CORS habilitado (via [Flask-CORS](https://flask-cors.readthedocs.io/)) para consumo por um frontend/cliente de outra origem. As origens permitidas são configuráveis por `CORS_ORIGINS` (lista separada por vírgula; default `*`). As rotas web do dashboard não expõem CORS.

**Validação:** o corpo precisa ser um objeto JSON com `id` (UUID) e `feedback` (texto não vazio, até `MAX_FEEDBACK_CHARS` caracteres, padrão `5000`); qualquer violação responde `400` com corpo JSON. Corpos acima de `MAX_CONTENT_LENGTH` (padrão 1 MB) recebem `413`, e um `id` já existente recebe `409`, inclusive quando duas requisições com o mesmo id chegam ao mesmo tempo.

### Listar Feedbacks

**Endpoint:** `GET /api/feedbacks`

**Descrição:** Lista os feedbacks analisados (spam excluído), do mais recente para o mais antigo, com paginação.

**Parâmetros de query:**
- `page` — número da página (padrão `1`)
- `per_page` — itens por página (padrão `20`, máximo `100`)
- `sentiment` — filtro opcional (`POSITIVO`, `NEGATIVO` ou `INCONCLUSIVO`)

**Resposta de Sucesso (200 OK):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "feedback": "Gosto muito do app!",
      "sentiment": "POSITIVO",
      "is_spam": false,
      "created_at": "2025-10-15T00:00:00+00:00",
      "requested_features": []
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "pages": 1,
    "has_next": false,
    "has_prev": false
  },
  "sentiment": null
}
```

### Consultar um Feedback

**Endpoint:** `GET /api/feedbacks/<id>`

**Descrição:** Retorna um feedback específico pelo seu UUID. Responde `400` para um id malformado e `404` quando não existe.

### Health Check

**Endpoint:** `GET /health`

**Descrição:** Probe de liveness/readiness para orquestradores (Docker, Render). Sem autenticação e sem rate-limit. Valida a conexão com o banco:
- `200 OK` → `{"status": "ok", "database": "ok"}`
- `503 Service Unavailable` → `{"status": "degraded", "database": "error"}` quando o banco está inacessível

O `docker-compose.yml` usa este endpoint no `healthcheck` do serviço `web`.

## Interface Web

### Dashboard (`/` ou `/dashboard`)

O dashboard principal exibe:
- Contagem total de feedbacks
- Porcentagem de feedbacks positivos e negativos
- Gráficos de distribuição de sentimento
- Lista das funcionalidades mais solicitadas
- Feedbacks recentes

### Lista de Feedbacks (`/feedbacks`)

Página com a lista completa de feedbacks, incluindo:
- Filtros por sentimento
- Paginação
- Links para visualizar detalhes de cada feedback

### Detalhes de Feedback (`/feedback/{id}`)

Página com detalhes completos de um feedback específico:
- Texto original do feedback
- Classificação de sentimento
- Status de spam
- Funcionalidades identificadas

## Funcionalidade de E-mail

A aplicação envia automaticamente um resumo semanal dos feedbacks para os stakeholders configurados. O e-mail inclui:
- Estatísticas de feedbacks da semana
- Porcentagem de feedbacks positivos e negativos
- Principais funcionalidades solicitadas

O envio é agendado via APScheduler. O texto do resumo é gerado por LLM, com fallback para um template estático quando a geração falha ou não há chave configurada.

### Agendamento do resumo

O resumo sai toda segunda-feira às 8h (fuso `SCHEDULER_TIMEZONE`, padrão `America/Sao_Paulo`) e exige **um único agendador por deploy**, senão cada processo envia o seu e-mail:

- **Processo único** (padrão do container: 1 worker do gunicorn com threads, via `gunicorn.conf.py`): `SCHEDULER_ENABLED=true` no próprio app. O `docker-compose.yml` já liga.
- **Vários workers ou réplicas:** `SCHEDULER_ENABLED=false` no web e um processo dedicado com `python -m app.scheduling`.
- **Sob demanda ou por cron externo** (ex.: Render Cron Job): `flask send-weekly-summary` (no container: `docker compose exec web flask --app wsgi send-weekly-summary`).

O SMTP usa STARTTLS com certificado verificado e `EMAIL_TIMEOUT` (padrão 30s). `APP_BASE_URL` define o link do painel no e-mail. Sem configuração de e-mail o app sobe normalmente (inclusive em produção) e só registra um aviso.

## Considerações de Desenvolvimento

### Padrões Arquiteturais

- **Arquitetura em Camadas:** separação de responsabilidades
  - Routes: controladores de requisições e respostas
  - Services: lógica de negócio e operações complexas
  - Models: estrutura de dados e persistência

- **Injeção de Dependência:** serviços são instanciados e injetados onde necessário

- **Padrão Repository:** abstração do acesso ao banco de dados através dos serviços

### Integração com IA

- A análise de feedbacks usa a API da OpenAI através do LangChain
- O prompt de análise identifica:
  - Sentimento (POSITIVO, NEGATIVO, INCONCLUSIVO)
  - Detecção de spam
  - Funcionalidades solicitadas

## Possíveis Melhorias

Já entregues: autenticação por senha no dashboard, suite de testes (pytest), CI (GitHub Actions), dockerização e resumo de e-mail gerado por LLM.

Próximos passos possíveis:

1. **UI/UX:** mais filtros, ordenação, responsividade e exportação de relatórios (PDF/CSV)
2. **Escalabilidade:** cache para consultas frequentes e fila de processamento para análises
3. **Rate-limiting:** proteção do endpoint público de ingestão contra abuso
4. **Monitoramento:** integração com logging/observabilidade e métricas de desempenho
5. **Frontend:** evoluir para um frontend desacoplado baseado em componentes (ex: React)

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
