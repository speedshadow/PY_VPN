#!/bin/bash
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
read -p "Qual o seu nome de domínio principal (ex: meudominio.com) [Deixe em branco se não tiver um agora]? " DOMAIN_NAME
ADMIN_EMAIL=""
if [[ ! -z "$DOMAIN_NAME" ]]; then
    while [[ -z "$ADMIN_EMAIL" ]]; do
        read -p "Qual o seu email (para registo do Certbot/Let's Encrypt)? " ADMIN_EMAIL
    done
fi

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
if [[ ! -z "$DOMAIN_NAME" ]]; then
    ALLOWED_HOSTS_VALUE="$DOMAIN_NAME,www.$DOMAIN_NAME,$VPS_PRIMARY_IP,localhost,127.0.0.1"
else
    ALLOWED_HOSTS_VALUE="$VPS_PRIMARY_IP,localhost,127.0.0.1"
fi

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
NGINX_SERVER_NAME_LINE="server_name $VPS_PRIMARY_IP;"
if [[ ! -z "$DOMAIN_NAME" ]]; then
    NGINX_SERVER_NAME_LINE="server_name $DOMAIN_NAME www.$DOMAIN_NAME $VPS_PRIMARY_IP;"
fi

sudo -u root bash -c "cat > $NGINX_CONFIG_FILE <<EOF
server {
    listen 80;
    $NGINX_SERVER_NAME_LINE

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

if [[ ! -z "$DOMAIN_NAME" ]]; then
    echo -e "\n${GREEN}>>> Configurando HTTPS com Certbot para $DOMAIN_NAME...${NC}"
    # Pode ser necessário parar o nginx temporariamente se o certbot tiver problemas com a porta 80 já em uso pelo nginx standalone
    # systemctl stop nginx
    # sleep 2
    certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME -m $ADMIN_EMAIL --agree-tos --non-interactive --redirect
    # systemctl start nginx # Se parou antes
    systemctl reload nginx # Recarrega Nginx para aplicar as alterações do Certbot

    echo -e "\n${GREEN}===========================================================${NC}"
    echo -e "${GREEN}  🎉 Implantação COMPLETA Automatizada Concluída! 🎉  ${NC}"
    echo -e "${GREEN}===========================================================${NC}"
    echo -e "Seu site deve estar acessível em: ${YELLOW}https://$DOMAIN_NAME${NC} e ${YELLOW}https://www.$DOMAIN_NAME${NC}"
    echo -e "\n${YELLOW}O Certbot configurou a renovação automática do certificado SSL.${NC}"
    echo -e "${YELLOW}Teste a renovação com: sudo certbot renew --dry-run${NC}"
else
    echo -e "\n${GREEN}===========================================================${NC}"
    echo -e "${GREEN}  🎉 Implantação HTTP Automatizada Concluída! 🎉  ${NC}"
    echo -e "${GREEN}===========================================================${NC}"
    echo -e "${YELLOW}Nenhum domínio foi fornecido. O Certbot (HTTPS) foi ignorado.${NC}"
    echo -e "Seu site deve estar acessível em: ${YELLOW}http://$VPS_PRIMARY_IP${NC}"
    echo -e "${YELLOW}Se desejar adicionar um domínio e HTTPS mais tarde, precisará de configurar o Nginx e o Certbot manualmente.${NC}"
fi

# Desativar ambiente virtual
deactivate

echo -e "\nVerifique os logs se algo não funcionar:"
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