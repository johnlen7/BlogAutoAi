FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY pyproject.toml uv.lock ./

# Instalar uv e dependências Python
RUN pip install uv
RUN uv sync --frozen

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p logs uploads

# Tornar scripts executáveis
RUN chmod +x automation_daemon.py run_automation.py

# Expor porta
EXPOSE 5000

# Comando padrão
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "main:app"]