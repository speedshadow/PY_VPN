#!/bin/bash

# 'set -e' faz com que o script termine imediatamente se um comando falhar.
# Isto é uma medida de segurança crucial para evitar comportamentos inesperados.
set -e

# =======================================================================#   Script de Implantação Automatizada para Django em Servidor de Produção
#   Versão Robusta e Segura v2.1
# =======================================================================#   Autor: Cascade AI
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
# =======================================================================
set -e # Termina o script imediatamente se um comando falhar.

# --- Configuração Global ---
APP_USER="django_user"
APP_GROUP="www-data" # Usar www-data como grupo principal simplifica permissões com Nginx
PROJECT_NAME="PY_VPN_MASTER"
PROJECT_BASE_DIR="/var/www"
PROJECT_DIR="$PROJECT_BASE_DIR/$PROJECT_NAME"
GIT_REPO_URL="https://github.com/speedshadow/PY_VPN.git"
GIT_BRANCH="master"
DJANGO_WSGI_MODULE="core.wsgi" # O caminho para o ficheiro WSGI do seu projeto
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
# As dependências de produção (gunicorn, psycopg2-binary) devem estar no requirements.txt.
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
# Generate a raw password that will be used for the database user creation

# Gerar uma nova password segura. Isto acontece em CADA execução para garantir a sincronização.
DB_PASSWORD_RAW=$(openssl rand -base64 16)
# Codificar a password de forma 100% segura para URLs, garantindo que todos os caracteres especiais são tratados.
DB_PASSWORD_ENCODED=$(python3 -c "from urllib.parse import quote; print(quote('''$DB_PASSWORD_RAW''', safe=''))")

# Verificar se o utilizador da base de dados existe para decidir entre CREATE e ALTER
if sudo -u postgres psql -t -c '\du' | cut -d \| -f 1 | grep -qw $DB_USER; then
    echo "   - Utilizador da base de dados '$DB_USER' já existe. A ATUALIZAR a password para garantir a sincronização..."
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD_RAW';"
else
    echo "   - A criar utilizador da base de dados '$DB_USER' com uma nova password..."
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD_RAW';"
fi

# Verificar se a base de dados existe
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "   - Base de dados '$DB_NAME' já existe."
else
    echo "   - A criar base de dados '$DB_NAME'..."
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
fi

# Conceder privilégios (é seguro executar isto múltiplas vezes)
echo "   - A garantir privilégios para '$DB_USER' na base de dados '$DB_NAME'..."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -d $DB_NAME -c "GRANT ALL ON SCHEMA public TO $DB_USER;"

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

# A password já foi gerada e sincronizada com a base de dados na etapa anterior.
# Agora, apenas a usamos para construir o ficheiro .env.
tee "$PROJECT_DIR/.env" > /dev/null << EOF
# Ficheiro de configuração de ambiente - gerado automaticamente
# Não adicione este ficheiro ao Git!

# Segurança
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$ALLOWED_HOSTS
ENABLE_HTTPS=False

# Base de Dados PostgreSQL
DATABASE_URL="postgres://$DB_USER:$DB_PASSWORD_ENCODED@127.0.0.1:5432/$DB_NAME"

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
echo -e "\n${YELLOW}--- Etapa 8/10: Configurando Gunicorn com systemd... ---${NC}"
GUNICORN_SERVICE_FILE="/etc/systemd/system/${GUNICORN_SERVICE_NAME}.service"

# Usar tee para criar o ficheiro como root, garantindo que as variáveis são expandidas.
tee "$GUNICORN_SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Gunicorn daemon for $PROJECT_NAME
After=network.target

[Service]
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --log-level debug --access-logfile - --error-logfile - --workers 3 --bind unix:$GUNICORN_SOCKET_FILE $DJANGO_WSGI_MODULE:application

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl restart $GUNICORN_SERVICE_NAME
systemctl enable $GUNICORN_SERVICE_NAME
echo -e "${GREEN}   OK! Serviço Gunicorn configurado e reiniciado.${NC}"

# --- 9. Configurar Nginx ---
echo -e "\n${YELLOW}--- Etapa 9/10: Configurando Nginx... ---${NC}"

# Limpeza de Configurações Antigas e Conflituosas
echo "   - A limpar configurações antigas do Nginx para evitar conflitos..."
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-enabled/PY_VPN_MASTER
sudo rm -f /etc/nginx/sites-available/PY_VPN_MASTER

NGINX_CONFIG_FILE="/etc/nginx/sites-available/$PROJECT_NAME_SLUG"
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

    # Configurações de Compressão Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any; # Comprime para todos os pedidos por proxy
    gzip_comp_level 6; # Nível de compressão (1-9)
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_min_length 256; # Não comprime ficheiros muito pequenos
    gzip_types
        text/plain
        text/css
        application/json
        application/javascript
        application/x-javascript
        text/xml
        application/xml
        application/xml+rss
        text/javascript
        image/svg+xml;

    # Servir ficheiros estáticos diretamente
    # IMPORTANTE: Garanta que a diretiva STATIC_ROOT em settings.py corresponde a: $PROJECT_DIR/staticfiles/
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, must-revalidate";
    }

    # Servir ficheiros de media diretamente
    # IMPORTANTE: Garanta que a diretiva MEDIA_ROOT em settings.py corresponde a: $PROJECT_DIR/media/
    location /media/ {
        alias $PROJECT_DIR/media/;
set -e # Sai imediatamente se um comando falhar

# --- Configurações Iniciais e Cores ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  Script de Auto-Setup Django COMPLETO (Nginx, Gunicorn, PostgreSQL, Certbot) ${NC}"
echo -e "${GREEN}  Este script deve ser executado DE DENTRO da pasta raiz do projeto.  ${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo -e "${YELLOW}AVISO: Este script fará alterações significativas no sistema, incluindo${NC}"
echo -e "${YELLOW}instalação de pacotes, configuração de serviços e firewall.${NC}"
echo -e "${YELLOW}Certifique-se de que o seu NOME DE DOMÍNIO está a apontar para o IP desta VPS.${NC}"
# --- Verificação do Repositório Git ---
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}AVISO: Não parece estar a executar este script a partir da raiz de um repositório Git.${NC}"
    echo -e "${YELLOW}O fluxo recomendado é: 'git clone <repo>', 'cd <repo>', e depois executar o script.${NC}"
    read -p "Deseja continuar mesmo assim? (s/N): " CONFIRM_GIT
    if [[ "$CONFIRM_GIT" != "s" && "$CONFIRM_GIT" != "S" ]]; then
        echo -e "${RED}Operação cancelada.${NC}"
        exit 1
    fi
fi

read -p "Deseja continuar com esta configuração completa e automatizada? (s/N): " CONFIRM_SCRIPT
if [[ "$CONFIRM_SCRIPT" != "s" && "$CONFIRM_SCRIPT" != "S" ]]; then
    echo -e "${RED}Implantação cancelada pelo utilizador.${NC}"
    exit 1
fi

# --- Determinar Utilizador e Caminhos (Automático) ---
if [ "$(id -u)" -ne 0 ]; then echo -e "${RED}Este script precisa ser executado com sudo.${NC}"; exit 1; fi

RUNNING_USER=$(who am i | awk '{print $1}')
if [ -z "$RUNNING_USER" ] && [ ! -z "$SUDO_USER" ]; then
    RUNNING_USER=$SUDO_USER
elif [ -z "$RUNNING_USER" ]; then
    RUNNING_USER=$USER
fi

PROJECT_DIR="$PWD"
PROJECT_NAME=$(basename "$PROJECT_DIR")
PROJECT_NAME_SLUG=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_]//g')
if [ -z "$PROJECT_NAME_SLUG" ]; then
    PROJECT_NAME_SLUG="my_django_project" # Fallback
fi

echo -e "${GREEN}Utilizador para Gunicorn/ficheiros: $RUNNING_USER${NC}"
echo -e "${GREEN}Diretório do projeto: $PROJECT_DIR${NC}"
echo -e "${GREEN}Nome do projeto (slug): $PROJECT_NAME_SLUG${NC}"

# --- Pedir Informações Essenciais ---
while [[ -z "$DOMAIN_NAME" ]]; do
    read -p "Qual o seu nome de domínio principal (ex: meudominio.com)? " DOMAIN_NAME
done
while [[ -z "$ADMIN_EMAIL" ]]; do
    read -p "Qual o seu email (para registo do Certbot/Let's Encrypt)? " ADMIN_EMAIL
done

# --- Variáveis de Configuração (Automáticas/Padrão) ---
DB_NAME="${PROJECT_NAME_SLUG}_db"
DB_USER="${PROJECT_NAME_SLUG}_user"
DB_PASSWORD=$(openssl rand -hex 16)
PYTHON_VERSION="3.10" # Ajuste se a sua VPS tiver uma versão diferente como padrão
DJANGO_SETTINGS_MODULE="core.settings" # Assumindo com base no seu projeto
DJANGO_WSGI_MODULE="core.wsgi"       # Assumindo com base no seu projeto
GUNICORN_SOCKET_FILE="$PROJECT_DIR/${PROJECT_NAME_SLUG}.sock"
# Assumindo que STATIC_ROOT e MEDIA_ROOT são configurados no settings.py para estas pastas na raiz do projeto
# Se forem diferentes, ajuste o Nginx config ou o settings.py
STATIC_FILES_ALIAS_DIR="$PROJECT_DIR/staticfiles" # Onde o collectstatic irá colocar os ficheiros
MEDIA_FILES_ALIAS_DIR="$PROJECT_DIR/mediafiles"   # Onde os uploads irão (se configurado)

VPS_PRIMARY_IP=$(hostname -I | awk '{print $1}')
if [ -z "$VPS_PRIMARY_IP" ]; then VPS_PRIMARY_IP="127.0.0.1"; fi
ALLOWED_HOSTS_VALUE="$DOMAIN_NAME,www.$DOMAIN_NAME,$VPS_PRIMARY_IP,localhost,127.0.0.1"

# --- Início da Implantação ---
echo -e "\n${GREEN}>>> Iniciando a implantação completa...${NC}"

# 1. Atualizar Sistema e Instalar Dependências Essenciais
echo -e "\n${GREEN}>>> Atualizando o sistema e instalando dependências...${NC}"
apt update
apt upgrade -y
apt install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev \
                    git curl postgresql postgresql-contrib libpq-dev \
                    build-essential ufw nginx certbot python3-certbot-nginx openssl

# 2. Configurar Firewall (UFW)
echo -e "\n${GREEN}>>> Configurando a firewall (UFW)...${NC}"
ufw allow OpenSSH
ufw allow 'Nginx Full' # Permite HTTP e HTTPS
ufw --force enable
ufw status

# 3. Configurar Ambiente Virtual Python
echo -e "\n${GREEN}>>> Configurando ambiente virtual Python em $PROJECT_DIR...${NC}"
chown -R $RUNNING_USER:$RUNNING_USER "$PROJECT_DIR"
sudo -u $RUNNING_USER python${PYTHON_VERSION} -m venv venv
source venv/bin/activate

pip install wheel
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo -e "${RED}ERRO: requirements.txt não encontrado!${NC}"; exit 1;
fi
pip install gunicorn psycopg2-binary

# 4. (Opcional) Compilar Assets de Frontend (Ex: Tailwind CSS via npm)
if [ -f "package.json" ]; then
    echo -e "\n${GREEN}>>> package.json encontrado. Tentando instalar Node.js e compilar assets...${NC}"
    if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
        echo -e "${YELLOW}Node.js/npm não encontrado. Instalando Node.js LTS...${NC}"
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        apt-get install -y nodejs
    fi
    sudo -u $RUNNING_USER npm install
    if grep -q -E '("build:css"|"build")' package.json ; then
        echo -e "${YELLOW}Tentando executar 'npm run build:css' ou 'npm run build'...${NC}"
        if sudo -u $RUNNING_USER npm run build:css 2>/dev/null; then echo -e "${GREEN}Comando 'npm run build:css' executado.${NC}";
        elif sudo -u $RUNNING_USER npm run build 2>/dev/null; then echo -e "${GREEN}Comando 'npm run build' executado.${NC}";
        else echo -e "${YELLOW}Não foi possível executar script de build. Verifique package.json.${NC}"; fi
    else echo -e "${YELLOW}Nenhum script de build óbvio (build:css, build) encontrado. Pulando.${NC}"; fi
else
    echo -e "\n${YELLOW}>>> package.json não encontrado. Pulando compilação de assets de frontend.${NC}"
fi

# 5. Configurar Base de Dados PostgreSQL
echo -e "\n${GREEN}>>> Configurando a base de dados PostgreSQL ($DB_NAME)...${NC}"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" || echo -e "${YELLOW}Base de dados $DB_NAME pode já existir.${NC}"
sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
echo -e "${GREEN}Utilizador BD: $DB_USER, Password BD: (guardada no .env)${NC}"

# 6. Configurar Django
echo -e "\n${GREEN}>>> Configurando Django...${NC}"
SECRET_KEY_DJANGO=$(openssl rand -hex 50)
# Certifique-se que STATIC_ROOT e MEDIA_ROOT no seu settings.py correspondem a
# $STATIC_FILES_ALIAS_DIR e $MEDIA_FILES_ALIAS_DIR (ex: BASE_DIR / 'staticfiles')
sudo -u $RUNNING_USER bash -c "cat > .env <<EOF
SECRET_KEY=$SECRET_KEY_DJANGO
DEBUG=False
ALLOWED_HOSTS=$ALLOWED_HOSTS_VALUE
DATABASE_URL=postgres://$DB_USER:'$DB_PASSWORD'@localhost:5432/$DB_NAME
DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
# STATIC_ROOT=$STATIC_FILES_ALIAS_DIR  # Descomente e ajuste se quiser forçar aqui
# MEDIA_ROOT=$MEDIA_FILES_ALIAS_DIR    # Descomente e ajuste se quiser forçar aqui
EOF"
chmod 600 .env # Permissões restritas para o .env
chown $RUNNING_USER:$RUNNING_USER .env
echo -e "${YELLOW}Arquivo .env criado. Verifique e ajuste se necessário.${NC}"

sudo -u $RUNNING_USER ./venv/bin/python manage.py makemigrations
sudo -u $RUNNING_USER ./venv/bin/python manage.py migrate
sudo -u $RUNNING_USER ./venv/bin/python manage.py collectstatic --noinput --clear
echo -e "${YELLOW}Certifique-se que STATIC_ROOT no seu settings.py está definido para algo como '$STATIC_FILES_ALIAS_DIR' para o Nginx servir os estáticos corretamente.${NC}"

# 7. Configurar Gunicorn com systemd
echo -e "\n${GREEN}>>> Configurando Gunicorn com systemd...${NC}"
GUNICORN_SERVICE_FILE="/etc/systemd/system/gunicorn_${PROJECT_NAME_SLUG}.service"
sudo -u root bash -c "cat > $GUNICORN_SERVICE_FILE <<EOF
[Unit]
Description=gunicorn daemon for $PROJECT_NAME
After=network.target

[Service]
User=$RUNNING_USER
Group=$(id -gn $RUNNING_USER)
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --access-logfile - \\
    --workers 3 \\
    --bind unix:$GUNICORN_SOCKET_FILE \\
    $DJANGO_WSGI_MODULE:application

[Install]
WantedBy=multi-user.target
EOF"
systemctl daemon-reload
systemctl stop gunicorn_${PROJECT_NAME_SLUG}.service 2>/dev/null || true
systemctl start gunicorn_${PROJECT_NAME_SLUG}.service
systemctl enable gunicorn_${PROJECT_NAME_SLUG}.service

# 8. Configurar Nginx
echo -e "\n${GREEN}>>> Configurando Nginx...${NC}"
NGINX_CONFIG_FILE="/etc/nginx/sites-available/$PROJECT_NAME_SLUG"
sudo -u root bash -c "cat > $NGINX_CONFIG_FILE <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME $VPS_PRIMARY_IP;

    client_max_body_size 100M; # Aumentar limite para uploads (ex: imagens do CKEditor)

    location = /favicon.ico { access_log off; log_not_found off; alias $STATIC_FILES_ALIAS_DIR/favicon.ico; } # Ajuste o caminho se necessário

    location /static/ {
        alias $STATIC_FILES_ALIAS_DIR/;
        expires 7d; # Cache de arquivos estáticos
        add_header Pragma public;
        add_header Cache-Control "public";
    }

    location /media/ {
        alias $MEDIA_FILES_ALIAS_DIR/;
        expires 7d;
        add_header Pragma public;
        add_header Cache-Control "public";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$GUNICORN_SOCKET_FILE;
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
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF"
sudo ln -sf $NGINX_CONFIG_FILE /etc/nginx/sites-enabled/
# Remover o default se existir e conflitar
if [ -f /etc/nginx/sites-enabled/default ]; then
    sudo rm /etc/nginx/sites-enabled/default
fi
nginx -t # Testa a configuração do Nginx
systemctl restart nginx

# 9. Configurar HTTPS com Certbot
echo -e "\n${GREEN}>>> Configurando HTTPS com Certbot para $DOMAIN_NAME...${NC}"
# Pode ser necessário parar o nginx temporariamente se o certbot tiver problemas com a porta 80 já em uso pelo nginx standalone
# systemctl stop nginx
# sleep 2
certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME -m $ADMIN_EMAIL --agree-tos --non-interactive --redirect
# systemctl start nginx # Se parou antes
systemctl reload nginx # Recarrega Nginx para aplicar as alterações do Certbot

# Desativar ambiente virtual
deactivate

echo -e "\n${GREEN}===========================================================${NC}"
echo -e "${GREEN}  🎉 Implantação COMPLETA Automatizada Concluída! 🎉  ${NC}"
echo -e "${GREEN}===========================================================${NC}"
echo -e "Seu site deve estar acessível em: ${YELLOW}https://$DOMAIN_NAME${NC} e ${YELLOW}https://www.$DOMAIN_NAME${NC}"
echo -e "Verifique os logs se algo não funcionar:"
echo -e "  - Gunicorn: ${YELLOW}sudo journalctl -u gunicorn_${PROJECT_NAME_SLUG} -f ${NC}"
echo -e "  - Nginx:    ${YELLOW}sudo tail -f /var/log/nginx/error.log${NC}"
echo -e "\n${YELLOW}Lembre-se de criar um superusuário Django se ainda não o fez:${NC}"
echo -e "${YELLOW}  sudo -u $RUNNING_USER $PROJECT_DIR/venv/bin/python $PROJECT_DIR/manage.py createsuperuser${NC}"
echo -e "\n${YELLOW}Se precisar de ajustar ALLOWED_HOSTS ou outras configurações, edite o ficheiro .env em $PROJECT_DIR/.env e reinicie o Gunicorn:${NC}"
echo -e "${YELLOW}  sudo systemctl restart gunicorn_${PROJECT_NAME_SLUG}.service${NC}"
echo -e "\n${YELLOW}O Certbot configurou a renovação automática do certificado SSL.${NC}"
echo -e "${YELLOW}Teste a renovação com: sudo certbot renew --dry-run${NC}"

exit 0