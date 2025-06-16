#!/bin/bash
# Script para ativar HTTPS com Certbot num ambiente Docker

# --- Verificações Iniciais ---
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script precisa ser executado como root. Por favor, use 'sudo'."
  exit 1
fi

PROJECT_DIR="/var/www/PY_VPN_MASTER"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERRO: O diretório do projeto $PROJECT_DIR não foi encontrado."
    echo "Certifique-se de que executou o 'setup_docker_production.sh' primeiro."
    exit 1
fi

cd "$PROJECT_DIR" || exit

# --- Obter as informações do utilizador ---
read -p "Por favor, insira o seu nome de domínio (ex: seusite.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo "O nome de domínio não pode ser vazio."
    exit 1
fi

read -p "Por favor, insira o seu e-mail (usado para notificações da Let's Encrypt): " EMAIL
if [ -z "$EMAIL" ]; then
    echo "O e-mail não pode ser vazio."
    exit 1
fi

echo "A preparar o Nginx para o domínio $DOMAIN..."
# Atualiza o server_name no nginx.conf
sed -i "s/server_name YOUR_DOMAIN.COM;/server_name $DOMAIN;/g" "$PROJECT_DIR/nginx/nginx.conf"

echo "A reiniciar o Nginx para aplicar o novo server_name..."
docker compose up -d --no-deps nginx

echo "A solicitar um certificado SSL para $DOMAIN..."

# --- Executar o Certbot para obter o certificado ---
docker compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email $EMAIL \
    -d $DOMAIN \
    --rsa-key-size 4096 \
    --agree-tos \
    --force-renewal \
    --non-interactive" certbot

# --- Verificar se o certificado foi criado ---
if [ $? -ne 0 ]; then
    echo "ERRO: A criação do certificado SSL falhou."
    echo "Por favor, verifique os logs acima. Garanta que o seu domínio ($DOMAIN) está a apontar para o IP deste servidor."
    # Reverter o server_name
    sed -i "s/server_name $DOMAIN;/server_name YOUR_DOMAIN.COM;/g" "$PROJECT_DIR/nginx/nginx.conf"
    exit 1
fi

echo "Certificado SSL criado com sucesso!"

# --- Preparar a configuração HTTPS final para o Nginx ---
NGINX_CONF_PATH="$PROJECT_DIR/nginx/nginx.conf"
HTTPS_BLOCK="
server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Configurações de segurança recomendadas
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;

    client_max_body_size 100M;

    location /static/ { alias /app/staticfiles/; }
    location /media/ { alias /app/media/; }

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}"

# Adicionar o bloco HTTPS ao final do ficheiro
echo "$HTTPS_BLOCK" >> "$NGINX_CONF_PATH"

# Modificar o bloco HTTP (porta 80) para apenas redirecionar
sed -i '/location \/ {/,/}/c\    location / {\n        return 301 https://\$host\$request_uri;\n    }' "$NGINX_CONF_PATH"

echo "A reiniciar o Nginx para aplicar as configurações HTTPS..."
docker compose up -d --no-deps nginx

echo "---"
echo "HTTPS ativado com sucesso para https://$DOMAIN!"
echo "O seu site está agora seguro. A renovação automática será gerida pelo serviço do Certbot."
echo "---"
# Script para ativar HTTPS com Certbot num ambiente Docker

