FROM python:3.11-slim

# Evita .pyc e deixa o log sair sem buffer (bom para containers)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências de sistema para o psycopg2-binary em runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Instala as dependências primeiro para aproveitar o cache de camadas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante da aplicação
COPY . .

EXPOSE 5000

# gunicorn servindo a app factory via wsgi:app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "wsgi:app"]
