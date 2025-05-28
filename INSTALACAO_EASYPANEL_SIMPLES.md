# 🚀 Instalação BlogAuto AI no EasyPanel - Versão Simplificada

## Opção 1: Deploy Tudo-em-Um (Mais Simples)

### Passo 1: Modificar Dockerfile para tudo-em-um
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    cron \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

# Copiar código
COPY . .

# Criar diretórios
RUN mkdir -p logs uploads

# Configurar supervisor para rodar app + automação
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expor porta
EXPOSE 5000

# Comando principal
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

### Passo 2: Criar arquivo supervisord.conf
```ini
[supervisord]
nodaemon=true

[program:webapp]
command=uv run gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
directory=/app
autostart=true
autorestart=true
stdout_logfile=/app/logs/webapp.log
stderr_logfile=/app/logs/webapp.log

[program:automation]
command=uv run python automation_daemon.py
directory=/app
autostart=true
autorestart=true
stdout_logfile=/app/logs/automation.log
stderr_logfile=/app/logs/automation.log
```

## Opção 2: Apenas App Web (Mais Compatível)

Se o EasyPanel não aceita workers, use apenas a aplicação web com CRON interno:

### Configuração no EasyPanel:

1. **Criar Projeto:** `blogauto-ai`

2. **Adicionar MySQL:**
   - Service Type: MySQL
   - Database: `blogauto`
   - Username: `blogauto`
   - Password: (auto-gerado)

3. **Adicionar App Principal:**
   - Service Type: App
   - Source: GitHub (seu repositório)
   - Build: Dockerfile
   - Port: 5000
   - Dockerfile: Use o Dockerfile simplificado abaixo

### Dockerfile Simplificado:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    cron \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

COPY . .
RUN mkdir -p logs uploads

# Configurar CRON interno
RUN echo "*/15 * * * * cd /app && python run_automation.py >> logs/cron.log 2>&1" | crontab -

EXPOSE 5000

# Iniciar CRON e aplicação
CMD service cron start && uv run gunicorn --bind 0.0.0.0:5000 main:app
```

## Opção 3: Deploy Manual via Docker Compose

Se o EasyPanel tem limitações, você pode usar um VPS simples com Docker:

1. **Conecte-se ao seu VPS**
2. **Clone o repositório:**
   ```bash
   git clone seu-repositorio
   cd blogauto-ai
   ```

3. **Configure o ambiente:**
   ```bash
   cp .env.example .env
   # Edite .env com suas configurações
   ```

4. **Execute:**
   ```bash
   docker-compose up -d
   ```

## Variáveis de Ambiente (Para qualquer opção):

```
SECRET_KEY=sua_chave_secreta
DB_HOST=mysql
DB_USER=blogauto
DB_PASSWORD=senha_do_mysql
DB_NAME=blogauto
OPENAI_API_KEY=sua_chave_openai
ANTHROPIC_API_KEY=sua_chave_anthropic
```

## 🎯 Qual opção você prefere?

1. **Opção 1:** Tudo-em-um com supervisor (mais completo)
2. **Opção 2:** App simples com CRON interno (mais compatível)
3. **Opção 3:** VPS próprio com Docker Compose (mais controle)

Diga qual você quer tentar e eu ajudo com os detalhes específicos!