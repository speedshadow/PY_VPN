# ==============================================================================
# FASE DE DESENVOLVIMENTO/PRODUÇÃO
# Esta imagem inclui Node.js e npm para compilar assets (Tailwind CSS)
# diretamente dentro do container, facilitando o desenvolvimento.
# ==============================================================================
FROM python:3.11-slim-bookworm

# Define variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema: Node.js e npm para o Tailwind CSS
RUN apt-get update && \
    apt-get install -y nodejs npm curl --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Cria um utilizador não-root para correr a aplicação por razões de segurança
RUN addgroup --system django-user && adduser --system --ingroup django-user django-user

# Copia os requisitos e instala as dependências Python
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação do diretório de trabalho atual para o contentor
# Nota: Isto será maioritariamente sobrescrito pelo volume no docker-compose.yml
COPY . .

# Muda a posse de todos os ficheiros da aplicação para o utilizador não-root.
# Isto é crucial para permitir que processos como o tailwind build escrevam ficheiros.
RUN chown -R django-user:django-user /app

# Cria os diretórios para media e staticfiles.
# A posse já foi definida pelo comando chown acima, mas garantimos que existem.
RUN mkdir -p /app/staticfiles && \
    mkdir -p /app/media

# Muda para o utilizador não-root
USER django-user

# Expõe a porta que o Gunicorn irá usar
EXPOSE 8000

# Comando para iniciar o Gunicorn
CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "core.wsgi:application"]
