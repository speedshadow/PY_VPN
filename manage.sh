#!/bin/bash
# ==============================================================================
#   Script Mestre de Gestão para o Projeto PY_VPN
# ==============================================================================
#   Autor: Cascade AI
#   Descrição: Unifica todas as operações de gestão do servidor (instalação,
#              backup, restauro) num único menu interativo.
# ==============================================================================

set -e
set -o pipefail

# --- Cores ---
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Configurações e Variáveis Globais ---
PROJECT_DIR=$(pwd)

# O script assume que está na raiz do projeto. Se não estiver, falha.
if [ ! -f "./docker-compose.yml" ]; then
    echo -e "${RED}ERRO: Este script deve ser executado a partir do diretório raiz do projeto.${NC}"
    exit 1
fi

# --- Funções de Lógica ---

# 1. INSTALAÇÃO E ATUALIZAÇÃO
install_or_update() {
    echo -e "${GREEN}---> Iniciando Instalação/Atualização do Ambiente de Produção...${NC}"
    
    # --- Verificação de Root ---
    if [ "$EUID" -ne 0 ]; then
      echo -e "${YELLOW}Esta opção precisa de permissões de root. Por favor, execute com 'sudo ./manage.sh'.${NC}"
      exit 1
    fi

    echo -e "${YELLOW}A remover instalações anteriores (incluindo dados da BD)...${NC}"
    docker-compose down -v

    # --- Instalação de Dependências ---
    echo -e "${GREEN}---> Atualizando o sistema e instalando dependências...${NC}"
    apt-get update > /dev/null
    apt-get install -y git curl openssl > /dev/null

    echo -e "${GREEN}---> Instalando Docker...${NC}"
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh > /dev/null
        rm get-docker.sh
    else
        echo -e "${YELLOW}Docker já está instalado.${NC}"
    fi

    # --- Recolha de Informação ---
    read -p "Qual é o seu domínio (ex: site.com) ou endereço IP? " HOST_NAME
    if [ -z "$HOST_NAME" ]; then echo -e "${RED}Input inválido.${NC}"; exit 1; fi

    # --- Geração do .env ---
    echo -e "${GREEN}---> Gerando ficheiro .env...${NC}"
    SECRET_KEY=$(openssl rand -hex 32)
    POSTGRES_PASSWORD=$(openssl rand -hex 32)
    cat > .env << EOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$HOST_NAME,localhost,127.0.0.1
POSTGRES_DB=py_vpn_master_db
POSTGRES_USER=py_vpn_master_user
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
ENABLE_HTTPS=False
EOF

    # --- Configuração do Nginx ---
    echo -e "${GREEN}---> Configurando Nginx...${NC}"
    sed -i "s/server_name YOUR_DOMAIN.COM;/server_name $HOST_NAME;/g" "$PROJECT_DIR/nginx/nginx.conf"

    # --- Build e Start dos Contentores ---
    echo -e "${GREEN}---> Construindo e iniciando os contentores Docker...${NC}"
    docker-compose up --build -d

    echo -e "${GREEN}---> Preparando a aplicação Django (migrate & collectstatic)...${NC}"
    sleep 10 # Dar tempo à BD para iniciar
    docker-compose exec -T web python manage.py migrate --noinput
    docker-compose exec -T web python manage.py collectstatic --noinput --clear

    # --- LÓGICA INTELIGENTE PARA HTTPS ---
        if [[ "$HOST_NAME" =~ [a-zA-Z] && "$HOST_NAME" != "localhost" ]]; then
        echo -e "${GREEN}---> Detetado um nome de domínio. A configurar HTTPS com Certbot...${NC}"
        read -p "Qual o seu e-mail para notificações da Let's Encrypt? " EMAIL
        if [ -z "$EMAIL" ]; then echo -e "${RED}Email inválido.${NC}"; exit 1; fi

        docker-compose run --rm --entrypoint "\
          certbot certonly --webroot -w /var/www/certbot \
            --email $EMAIL -d $HOST_NAME --rsa-key-size 4096 \
            --agree-tos --force-renewal --non-interactive" certbot

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Certificado SSL criado! A reconfigurar Nginx para HTTPS...${NC}"
            HTTPS_BLOCK="
server {
    listen 443 ssl http2;
    server_name $HOST_NAME;
    ssl_certificate /etc/letsencrypt/live/$HOST_NAME/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$HOST_NAME/privkey.pem;
    ssl_session_timeout 1d; ssl_session_cache shared:SSL:10m; ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3; ssl_prefer_server_ciphers on;
    location / { proxy_pass http://web:8000; proxy_set_header Host \$host; proxy_set_header X-Real-IP \$remote_addr; proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto \$scheme; }
    location /static/ { alias /app/staticfiles/; }
    location /media/ { alias /app/media/; }
}"
            echo "$HTTPS_BLOCK" >> "$PROJECT_DIR/nginx/nginx.conf"
            sed -i '/listen 80;/,/location \/ {/!b; /location \/ {/c\    location / {\n        return 301 https://\$host\$request_uri;\n    }' "$PROJECT_DIR/nginx/nginx.conf"
            docker-compose up -d --no-deps nginx
            echo -e "${GREEN}HTTPS ativado com sucesso!${NC}"
        else
            echo -e "${RED}Falha ao criar certificado SSL. Verifique se o seu domínio aponta para este IP. HTTPS não foi ativado.${NC}"
        fi
    else
        echo -e "${YELLOW}---> Detetado um endereço IP. A saltar configuração de HTTPS.${NC}"
    fi

    echo -e "${GREEN}---> Instalação concluída! O seu site está disponível em http://$HOST_NAME:8080 (ou https://$HOST_NAME se o domínio foi usado).${NC}"
    echo -e "${YELLOW}Para criar um superuser, execute: 'sudo docker-compose exec web python manage.py createsuperuser'${NC}"
}

# 2. FAZER BACKUP
backup_system() {
    echo -e "${GREEN}---> Iniciando Backup Completo...${NC}"
    BACKUP_DIR="$PROJECT_DIR/backups"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
    BACKUP_FILE="$BACKUP_DIR/backup-$TIMESTAMP.tar.gz"
    DB_SERVICE_NAME="db"
export DB_SERVICE_NAME
    MEDIA_VOLUME_NAME="$(basename "$PROJECT_DIR")_media_volume"

    echo "A fazer dump da base de dados e a arquivá-lo diretamente com o volume de media ($MEDIA_VOLUME_NAME)..."
    echo "Este processo utiliza 'pipes' para contornar problemas de sincronização de ficheiros do Docker."

    # A saída do pg_dumpall é enviada ('piped') diretamente para um contentor temporário.
    # Dentro desse contentor, o dump é guardado num ficheiro temporário e depois arquivado com o tar juntamente com o volume de media.
    # Isto evita completamente a necessidade de guardar o dump no sistema de ficheiros do anfitrião antes de o arquivar.
    # Utiliza-se pg_dump (e não pg_dumpall) porque é a ferramenta correta para uma única BD e não requer superuser.
    docker-compose exec -T "$DB_SERVICE_NAME" pg_dump -U py_vpn_master_user -d py_vpn_master_db | docker run --rm -i \
        -v "$MEDIA_VOLUME_NAME:/media_volume:ro" \
        -w /tmp \
        alpine sh -c 'tee db_dump.sql > /dev/null && tar -czf - /tmp/db_dump.sql -C /media_volume .' > "$BACKUP_FILE"

    # Verifica se o backup foi criado e não está vazio
    if [ ! -s "$BACKUP_FILE" ]; then
        echo -e "${RED}ERRO: Falha ao criar o ficheiro de backup ou o ficheiro está vazio.${NC}"
        exit 1
    fi

    echo -e "${GREEN}Backup criado com sucesso em: $BACKUP_FILE${NC}"

    echo "A limpar backups com mais de 30 dias..."
    find "$BACKUP_DIR" -type f -name 'backup-*.tar.gz' -mtime +30 -exec rm {} \;
}

# 3. RESTAURAR BACKUP
restore_system() {
    echo -e "${GREEN}---> Iniciando Restauro a partir de Backup...${NC}"
    read -p "Por favor, insira o caminho completo para o ficheiro de backup (.tar.gz): " BACKUP_FILE
    if [ ! -f "$BACKUP_FILE" ]; then echo -e "${RED}ERRO: Ficheiro não encontrado.${NC}"; exit 1; fi

    echo -e "${RED}ATENÇÃO: Este processo é DESTRUTIVO e irá apagar os dados atuais.${NC}"
    read -p "Tem a certeza? (escreva 'sim' para confirmar): " CONFIRMATION
    if [ "$CONFIRMATION" != "sim" ]; then echo "Restauro cancelado."; exit 0; fi

    RESTORE_DIR=$(mktemp -d)
    echo "A extrair backup..."
    tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"
    DB_DUMP_FILE="$RESTORE_DIR/tmp/db_dump.sql"
    if [ ! -f "$DB_DUMP_FILE" ]; then echo -e "${RED}ERRO: Ficheiro tmp/db_dump.sql não encontrado no backup.${NC}"; rm -rf "$RESTORE_DIR"; exit 1; fi

    echo "A parar serviços e a apagar volumes..."
    docker-compose down -v

    echo "A recriar e iniciar todos os serviços..."
    # O Docker Compose irá criar o volume 'postgres_data' automaticamente se não existir, conforme definido no docker-compose.yml
    docker-compose up -d --build
    echo "A aguardar que os serviços estejam prontos (especialmente a base de dados)..."
    sleep 15 # Aumentar se necessário, para dar tempo à BD de inicializar completamente

    echo "A restaurar base de dados..."
    # Usando 'db' hardcodado diretamente devido a problemas de escopo de variável com input via pipe.
    cat "$DB_DUMP_FILE" | docker-compose exec -T "db" psql -U py_vpn_master_user -d py_vpn_master_db

    echo "A restaurar ficheiros de media..."
    # O nome do volume de media é derivado do nome do projeto
    MEDIA_VOLUME_NAME="${PROJECT_NAME}_media_volume"
    # Certifica-se de que o diretório de destino existe no volume de media dentro do contentor
    # O comando tar dentro do contentor irá extrair para /app/media/
    # Os ficheiros no backup estão na raiz do que foi copiado do volume de media original.
    # Removido 'z' de '-xzf' porque o fluxo de entrada de 'tar -cf -' não é comprimido com gzip.
    docker-compose exec -T web sh -c "mkdir -p /app/media/ && tar -xf - -C /app/media/" < <(tar -cf - -C "$RESTORE_DIR" --exclude='tmp' .)

    # Os serviços já foram reiniciados anteriormente com 'docker-compose up -d --build'
    # A linha 'docker-compose up -d --remove-orphans' foi removida por ser redundante.
    rm -rf "$RESTORE_DIR"
    echo -e "${GREEN}Restauro concluído com sucesso!${NC}"
}

# 4. VER .ENV
view_env() {
    echo -e "${YELLOW}--- Conteúdo do seu ficheiro .env ---${NC}"
    if [ -f ".env" ]; then
        cat .env
    else
        echo "Ficheiro .env não encontrado. Execute a instalação primeiro."
    fi
    echo -e "${YELLOW}------------------------------------${NC}"
}

# --- Menu Principal ---
clear
echo -e "${GREEN}===== SCRIPT DE GESTÃO PY_VPN =====${NC}"
echo "1. Instalar / Atualizar Ambiente de Produção"
echo "2. Fazer Backup Completo"
echo "3. Restaurar a partir de um Backup"
echo "4. Ver Ficheiro de Configuração (.env)"
echo "5. Sair"
echo "======================================"
read -p "Escolha uma opção [1-5]: " choice

case $choice in
    1) install_or_update ;; 
    2) backup_system ;; 
    3) restore_system ;; 
    4) view_env ;; 
    5) echo "A sair."; exit 0 ;; 
    *) echo -e "${RED}Opção inválida.${NC}"; exit 1 ;; 
esac

