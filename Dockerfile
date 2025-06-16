# ==============================================================================
# FASE 1: Builder - Compilar os recursos estáticos (CSS)
# ==============================================================================
# Usamos uma imagem que já inclui Python e Node.js para a fase de compilação.
FROM python:3.11-slim-bookworm as builder

# Define o diretório de trabalho
WORKDIR /app

# Instala o Node.js e o npm
# A imagem python:3.11-slim não tem node, então instalamos.
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Copia os ficheiros de dependências do frontend
COPY package.json package-lock.json* ./

# Instala as dependências do frontend
RUN npm install

# Copia o resto do código da aplicação
COPY . .

# Compila o CSS do Tailwind
RUN npm run build:css

# ==============================================================================
# FASE 2: Final - A imagem de produção final
# ==============================================================================
# Começamos com uma imagem Python "slim" para manter o tamanho final pequeno.
FROM python:3.11-slim-bookworm

# Define variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Define o diretório de trabalho
WORKDIR /app

# Cria um utilizador não-root para correr a aplicação por razões de segurança
RUN addgroup --system django-user && adduser --system --ingroup django-user django-user

# Copia os requisitos e instala as dependências Python
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copia o código da aplicação do diretório de trabalho atual para o contentor
COPY . .

# Copia os ficheiros estáticos compilados da fase 'builder'
# O --chown garante que o novo utilizador tem permissão sobre estes ficheiros
COPY --from=builder --chown=django-user:django-user /app/theme/static/css/dist/styles.css ./theme/static/css/dist/styles.css

# Cria os diretórios para media e staticfiles e define as permissões
# Estes diretórios serão montados como volumes, mas criá-los aqui garante
# que as permissões estão corretas.
RUN mkdir -p /app/staticfiles && \
    mkdir -p /app/media && \
    chown -R django-user:django-user /app/staticfiles && \
    chown -R django-user:django-user /app/media

# Muda para o utilizador não-root
USER django-user

# Expõe a porta que o Gunicorn irá usar
EXPOSE 8000

# Comando para iniciar o Gunicorn
# O ficheiro de entrada do Gunicorn (core.wsgi) será referenciado aqui.
CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "core.wsgi:application"]
