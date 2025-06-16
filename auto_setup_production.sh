#!/bin/bash

# ==============================================================================
#   Script de Implantação Automatizada para Django em Servidor de Produção
#   Versão Robusta e Segura v2.1
# ==============================================================================
#   Autor: Cascade AI
#   Descrição: Este script, executado com sudo, automatiza a implantação de
#              um projeto Django. Ele é autossuficiente e segue as melhores
#              práticas de segurança.
#
#   Funcionalidades:
#              - Cria um utilizador de sistema dedicado para a aplicação.
#              - Clona o projeto para /var/www/, o local padrão.
#              - Configura dependências, PostgreSQL, Gunicorn e Nginx.
#              - Gere permissões de ficheiros de forma segura.
#              - Opcionalmente, configura HTTPS com Certbot.
#
#   Uso: Copie este script para a sua VPS, dê-lhe permissão de execução
#        (chmod +x auto_setup_production.sh) e execute com sudo
#        (sudo ./auto_setup_production.sh).
# ==============================================================================

set -e # Termina o script imediatamente se um comando falhar.

# --- Configuração Global ---
APP_USER="django_user"
APP_GROUP="www-data" # Usar www-data como grupo principal simplifica permissões com Nginx
PROJECT_NAME="PY_VPN_MASTER"
PROJECT_BASE_DIR="/var/www"
PROJECT_DIR="$PROJECT_BASE_DIR/$PROJECT_NAME"
GIT_REPO_URL="https://github.com/speedshadow/PY_VPN.git"
GIT_BRANCH="master"
PROJECT_NAME_SLUG=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_]//g')
GUNICORN_SERVICE_NAME="gunicorn_${PROJECT_NAME_SLUG}"
# Colocar o socket no diretório do projeto com permissões corretas é mais simples e seguro
# do que usar /run/gunicorn quando não se usa o RuntimeDirectory do systemd.
GUNICORN_SOCKET_FILE="$PROJECT_DIR/gunicorn.sock"

# --- Cores para o Output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# --- Verificação Inicial ---
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}ERRO: Este script precisa ser executado com 'sudo'.${NC}"
    exit 1
fi

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  Iniciando a Implantação Segura e Automatizada do Django...${NC}"
echo -e "${GREEN}======================================================================${NC}"

# --- Pedir Informações Essenciais ---
read -p "Qual o seu nome de domínio principal (ex: meudominio.com) [Deixe em branco se não tiver um agora]? " DOMAIN_NAME
ADMIN_EMAIL=""
if [[ ! -z "$DOMAIN_NAME" ]]; then
    while [[ -z "$ADMIN_EMAIL" ]]; do
        read -p "Qual o seu email (para registo do Certbot/Let's Encrypt)? " ADMIN_EMAIL
    done
fi

# --- 1. Configuração do Sistema e Utilizador ---
echo -e "\n${YELLOW}--- Etapa 1/10: Configurando utilizador do sistema e permissões... ---${NC}"
if ! id -u $APP_USER > /dev/null 2>&1; then
    # Cria o utilizador sem home dir, sem login shell, e adiciona-o ao grupo www-data
    useradd --system --no-create-home --shell /bin/false --group $APP_GROUP $APP_USER
    echo -e "   - Utilizador de sistema '$APP_USER' criado e adicionado ao grupo '$APP_GROUP'."
else
    echo -e "   - Utilizador de sistema '$APP_USER' já existe. Garantindo que está no grupo '$APP_GROUP'."
    usermod -a -G $APP_GROUP $APP_USER
fi
echo -e "${GREEN}   OK!${NC}"

# --- 2. Instalar Dependências do Sistema --- 
echo -e "\n${YELLOW}--- Etapa 2/10: Instalando dependências do sistema... ---${NC}"
apt-get update
apt-get install -y git python3-venv python3-pip nginx curl postgresql postgresql-contrib libpq-dev build-essential certbot python3-certbot-nginx
echo -e "${GREEN}   OK!${NC}"

# --- 3. Clonar ou Atualizar Repositório ---
echo -e "\n${YELLOW}--- Etapa 3/10: Configurando diretório do projeto em $PROJECT_DIR... ---${NC}"
mkdir -p $PROJECT_DIR
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "   - Repositório existente encontrado. A fazer pull das últimas alterações..."
    cd $PROJECT_DIR
    git pull origin $GIT_BRANCH
    cd - > /dev/null # Volta ao diretório anterior sem imprimir
else
    echo "   - Clonando novo repositório..."
    git clone -b $GIT_BRANCH $GIT_REPO_URL $PROJECT_DIR
fi
# Define o dono e o grupo para todo o projeto
chown -R $APP_USER:$APP_GROUP $PROJECT_DIR
# Garante que o grupo tem permissões de escrita (necessário para o socket, por exemplo)
chmod -R 775 $PROJECT_DIR
echo -e "${GREEN}   OK!${NC}"

# 3. Configurar Ambiente Virtual Python
echo -e "\n${GREEN}>>> Configurando ambiente virtual Python em $PROJECT_DIR...${NC}"
chown -R $APP_USER:$APP_GROUP "$PROJECT_DIR"
su -s /bin/bash $APP_USER <<EOF
set -e
python3 -m venv $PROJECT_DIR/venv
source $PROJECT_DIR/venv/bin/activate
pip install --upgrade pip
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    pip install -r $PROJECT_DIR/requirements.txt
else
    echo "AVISO: Ficheiro requirements.txt não encontrado. A saltar a instalação de dependências."
fi
pip install gunicorn psycopg2-binary
deactivate
EOF

# 4. (Opcional) Compilar Assets de Frontend (Ex: Tailwind CSS via npm)
if [ -f "$PROJECT_DIR/package.json" ]; then
    echo -e "\n${GREEN}>>> package.json encontrado. Tentando instalar Node.js e compilar assets...${NC}"
    if ! command -v npm &> /dev/null; then
        echo "   - Node.js/npm não encontrado. Instalando..."
        # O script da nodesource já executa apt-get update
        curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - &>/dev/null
        apt-get install -y nodejs &>/dev/null
    fi
    
    echo "   - Instalando dependências com 'npm install'..."
    su -s /bin/bash $APP_USER <<EOF
set -e
export HOME="$PROJECT_DIR"
cd "$PROJECT_DIR"
npm install
EOF

    echo "   - Compilando assets..."
    su -s /bin/bash $APP_USER <<EOF
set -e
export HOME="$PROJECT_DIR"
cd "$PROJECT_DIR"
# Procura por um script de build comum
if grep -q '"build:css"' "package.json"; then
    npm run build:css
elif grep -q '"build"' "package.json"; then
    npm run build
else
    echo "AVISO: Nenhum script 'build' ou 'build:css' encontrado em package.json."
fi
EOF
    echo -e "${GREEN}   OK! Assets de frontend processados.${NC}"
fi

# --- 5. Configurar Base de Dados PostgreSQL ---
echo -e "\n${YELLOW}--- Etapa 5/10: Configurando a base de dados PostgreSQL... ---${NC}"
DB_USER="${PROJECT_NAME_SLUG}_user"
DB_NAME="${PROJECT_NAME_SLUG}_db"
# Gera uma password segura se ainda não tiver sido gerada
DB_PASSWORD=$(openssl rand -base64 32)

# Usar sudo -u postgres para executar comandos psql
# A sintaxe 'psql -c' é mais limpa e o '|| true' evita que o script pare se o user/db já existir
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" || echo "   - Base de dados '$DB_NAME' já existe."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || echo "   - Utilizador '$DB_USER' já existe."
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
echo -e "${GREEN}   OK!${NC}"

# --- 6. Criar Ficheiro de Ambiente .env ---
echo -e "\n${YELLOW}--- Etapa 6/10: Criando o ficheiro de ambiente .env... ---${NC}"
SECRET_KEY=$(openssl rand -hex 40)
VPS_PRIMARY_IP=$(hostname -I | awk '{print $1}')
if [[ ! -z "$DOMAIN_NAME" ]]; then
    ALLOWED_HOSTS="$DOMAIN_NAME,www.$DOMAIN_NAME,$VPS_PRIMARY_IP,localhost"
else
    ALLOWED_HOSTS="$VPS_PRIMARY_IP,localhost"
fi

# Usar tee para criar o ficheiro como root e depois chown para o utilizador correto
tee "$PROJECT_DIR/.env" > /dev/null << EOF
# Ficheiro de configuração de ambiente - gerado automaticamente
# Não adicione este ficheiro ao Git!

# Segurança
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$ALLOWED_HOSTS

# Base de Dados PostgreSQL
DATABASE_URL=postgres://$DB_USER:$DB_PASSWORD@127.0.0.1:5432/$DB_NAME

# Outras configurações (se necessário)
# EMAIL_HOST_USER=
# EMAIL_HOST_PASSWORD=
EOF

chown $APP_USER:$APP_GROUP "$PROJECT_DIR/.env"
chmod 660 "$PROJECT_DIR/.env" # Apenas dono e grupo podem ler/escrever
echo -e "${GREEN}   OK!${NC}"

# --- 7. Executar Comandos de Gestão do Django ---
echo -e "\n${YELLOW}--- Etapa 7/10: Executando collectstatic e migrate... ---${NC}"
# Executa os comandos como o utilizador da aplicação
su -s /bin/bash $APP_USER <<EOF
set -e
source $PROJECT_DIR/venv/bin/activate
# O manage.py está na raiz do projeto clonado
python $PROJECT_DIR/manage.py collectstatic --noinput
python $PROJECT_DIR/manage.py migrate --noinput
deactivate
EOF
echo -e "${GREEN}   OK!${NC}"

# --- 8. Configurar Gunicorn com systemd ---
echo -e "\n${GREEN}>>> Configurando Gunicorn com systemd...${NC}"
GUNICORN_SERVICE_FILE="/etc/systemd/system/gunicorn_${PROJECT_NAME_SLUG}.service"
sudo -u root bash -c "cat > $GUNICORN_SERVICE_FILE <<EOF
[Unit]
Description=gunicorn daemon for $PROJECT_NAME
After=network.target

[Service]
# O Gunicorn irá correr como root, mas pertencer ao grupo www-data
# para que o Nginx possa comunicar com o socket.
User=root
Group=www-data

# O systemd irá criar e gerir o diretório /run/gunicorn para nós com as permissões corretas.
RuntimeDirectory=gunicorn

WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --access-logfile - \\
    --workers 3 \\
    --bind unix:$GUNICORN_SOCKET_FILE \\
    $DJANGO_WSGI_MODULE:application

[Install]
WantedBy=multi-user.target
EOF"
systemctl daemon-reload
systemctl enable --now $GUNICORN_SERVICE_NAME
echo -e "${GREEN}   OK! Serviço Gunicorn configurado e ativado.${NC}"

# --- 9. Configurar Nginx ---
echo -e "\n${YELLOW}--- Etapa 9/10: Configurando Nginx... ---${NC}"
NGINX_CONFIG_FILE="/etc/nginx/sites-available/${PROJECT_NAME_SLUG}"
VPS_PRIMARY_IP=$(hostname -I | awk '{print $1}')

if [[ ! -z "$DOMAIN_NAME" ]]; then
    SERVER_NAME_LINE="server_name $DOMAIN_NAME www.$DOMAIN_NAME;"
else
    SERVER_NAME_LINE="server_name $VPS_PRIMARY_IP;"
fi

# Usar tee para criar o ficheiro como root
tee "$NGINX_CONFIG_FILE" > /dev/null <<EOF
server {
    listen 80;
    $SERVER_NAME_LINE

    client_max_body_size 100M;

    # O Django trata do favicon.ico, mas isto evita logs desnecessários
    location = /favicon.ico { access_log off; log_not_found off; }

    # Servir ficheiros estáticos diretamente
    # STATIC_ROOT no settings.py deve ser BASE_DIR / 'staticfiles'
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, must-revalidate";
    }

    # Servir ficheiros de media diretamente
    # MEDIA_ROOT no settings.py deve ser BASE_DIR / 'mediafiles'
    location /media/ {
        alias $PROJECT_DIR/mediafiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$GUNICORN_SOCKET_FILE;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Ativar o site e remover o default
if [ ! -L "/etc/nginx/sites-enabled/${PROJECT_NAME_SLUG}" ]; then
    ln -s "$NGINX_CONFIG_FILE" "/etc/nginx/sites-enabled/"
fi
rm -f /etc/nginx/sites-enabled/default

# Testar e reiniciar Nginx
nginx -t
systemctl restart nginx
echo -e "${GREEN}   OK! Nginx configurado e reiniciado.${NC}"

# --- 10. Configurar Firewall e HTTPS (Opcional) ---
echo -e "\n${YELLOW}--- Etapa 10/10: Configurando Firewall e HTTPS... ---${NC}"
ufw allow 'Nginx Full'
ufw allow 'OpenSSH'
ufw --force enable

if [[ ! -z "$DOMAIN_NAME" && ! -z "$ADMIN_EMAIL" ]]; then
    echo "   - Configurando HTTPS com Certbot para $DOMAIN_NAME..."
    certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --email $ADMIN_EMAIL --agree-tos --non-interactive --redirect
    echo -e "${GREEN}   OK! HTTPS configurado.${NC}"
else
    echo "   - A saltar configuração HTTPS (domínio ou email não fornecido)."
fi
echo -e "${GREEN}   OK! Firewall ativada.${NC}"

# --- Fim da Implantação ---
echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}  IMPLANTAÇÃO CONCLUÍDA!                                            ${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo -e "${YELLOW}  O seu site deve estar acessível em:                                 ${NC}"
if [[ ! -z "$DOMAIN_NAME" ]]; then
    echo -e "${YELLOW}  https://$DOMAIN_NAME                                                 ${NC}"
else
    echo -e "${YELLOW}  http://$VPS_PRIMARY_IP                                                ${NC}"
fi
echo -e "\n${YELLOW}  Próximos Passos Recomendados:                                     ${NC}"
echo -e "${YELLOW}  1. Crie um superutilizador Django (se ainda não tiver um):          ${NC}"
echo -e "${YELLOW}     sudo -u $APP_USER bash -c 'source $PROJECT_DIR/venv/bin/activate && python $PROJECT_DIR/manage.py createsuperuser'${NC}"
echo -e "${YELLOW}  2. Verifique os logs se algo não funcionar:                         ${NC}"
echo -e "${YELLOW}     journalctl -u $GUNICORN_SERVICE_NAME -f                          ${NC}"
echo -e "${YELLOW}     tail -f /var/log/nginx/error.log                                 ${NC}"
echo -e "\n"

exit 0