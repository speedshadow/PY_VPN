#!/bin/bash
# ==============================================================================
#   Script de Gestão para o Projeto PY_VPN (Versão Production-Ready)
# ==============================================================================
#   Autor: Cascade AI
#   Descrição: Unifica operações de gestão (instalação, backup, restauro)
#              para um ambiente Docker, seguindo as melhores práticas.
# ==============================================================================

set -e
set -o pipefail

# --- Cores e Variáveis Globais ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR=$(pwd)
FRONTEND_DIR="$PROJECT_DIR/theme/static_src" # Caminho para os recursos de front-end
DB_SERVICE_NAME="db"
WEB_SERVICE_NAME="web"

# --- Verificações Iniciais ---
if [ ! -f "./docker-compose.yml" ]; then
    echo -e "${RED}ERRO: Este script deve ser executado a partir do diretório raiz do projeto.${NC}"
    exit 1
fi

# --- Funções de Lógica ---

# 1. SETUP DE NOVO SERVIDOR (DESTRUTIVO)
setup_new_server() {
    local mode=$1
    echo -e "${YELLOW}AVISO: Esta operação é DESTRUTIVA e irá apagar todos os contentores e volumes existentes.${NC}"
    read -p "Tem a certeza que deseja continuar? (escreva 'sim' para confirmar): " CONFIRMATION
    if [ "$CONFIRMATION" != "sim" ]; then echo "Operação cancelada."; exit 0; fi

    echo -e "${GREEN}---> Iniciando a Configuração de um Novo Servidor...${NC}"
    if [ "$EUID" -ne 0 ]; then
      echo -e "${RED}Esta opção precisa de permissões de root. Por favor, execute com 'sudo ./manage.sh'.${NC}"
      exit 1
    fi

    echo -e "${BLUE}A instalar dependências do sistema (git, curl, openssl)...${NC}"
    apt-get update > /dev/null
    apt-get install -y git curl openssl > /dev/null

    if ! command -v docker &> /dev/null; then
        echo -e "${BLUE}A instalar Docker...${NC}"
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh > /dev/null
        rm get-docker.sh
    fi

    # Garante que o serviço Docker está a correr
    if ! docker info > /dev/null 2>&1; then
        echo -e "${YELLOW}O serviço Docker não está a correr. A iniciar...${NC}"
        systemctl start docker
        systemctl enable docker > /dev/null 2>&1
        sleep 5 # Espera um momento para o serviço arrancar
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${BLUE}A instalar Docker Compose...${NC}"
        curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi

    # A instalação do Node.js e do npm foi removida. O Dockerfile é agora o único responsável pelo ambiente de construção.

    echo -e "${BLUE}A remover instalações Docker anteriores (se existirem)...${NC}"
    docker-compose down -v --remove-orphans > /dev/null 2>&1 || true

    read -p "Qual é o seu domínio (ex: site.com) ou endereço IP? " HOST_NAME
    if [ -z "$HOST_NAME" ]; then echo -e "${RED}Input inválido.${NC}"; exit 1; fi

    echo -e "${BLUE}A gerar ficheiro .env com chaves seguras...${NC}"
    SECRET_KEY=$(openssl rand -hex 32)
    POSTGRES_DB="py_vpn_master_db"
    POSTGRES_USER="py_vpn_master_user"
    POSTGRES_PASSWORD=$(openssl rand -hex 32)
    cat > .env << EOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$HOST_NAME,localhost,127.0.0.1
POSTGRES_DB=$POSTGRES_DB
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
ENABLE_HTTPS=false
EOF

    if [[ "$HOST_NAME" =~ [a-zA-Z] ]]; then
        echo -e "${GREEN}---> Nome de domínio detetado. A preparar para configurar HTTPS...${NC}"
        read -p "Qual o seu e-mail para notificações da Let's Encrypt? (pode ser um email falso para o teste): " EMAIL
        if [ -z "$EMAIL" ]; then echo -e "${RED}Email inválido.${NC}"; exit 1; fi

        echo -e "${BLUE}A copiar o template Nginx para HTTP (para o desafio Certbot)...${NC}"
        cp ./nginx/nginx.http.conf ./nginx/nginx.conf
        sed -i "s/YOUR_DOMAIN_OR_IP/$HOST_NAME/g" ./nginx/nginx.conf

        echo -e "${BLUE}A iniciar Nginx e Certbot para obter o certificado...${NC}"
        docker-compose up -d --no-deps nginx certbot

        local cert_exit_code=1 # Default to failure

        if [ "$mode" == "staging" ]; then
            echo
            echo "******************************************************"
            echo "*** MODO DE TESTE: A SIMULAR criação de certificado ***"
            echo "******************************************************"
            echo
            echo -e "${BLUE}A criar diretórios e ficheiros de certificado falsos dentro do contentor...${NC}"
            docker-compose exec certbot mkdir -p /etc/letsencrypt/live/$HOST_NAME

            docker-compose exec certbot touch /etc/letsencrypt/options-ssl-nginx.conf
            docker-compose exec certbot touch /etc/letsencrypt/live/$HOST_NAME/fullchain.pem
            docker-compose exec certbot touch /etc/letsencrypt/live/$HOST_NAME/privkey.pem
            cert_exit_code=$?
            if [ $cert_exit_code -eq 0 ]; then
                echo -e "${GREEN}Simulação de certificado concluída com sucesso.${NC}"
            fi
        else # production mode
            echo -e "${BLUE}A solicitar o certificado SSL (PRODUÇÃO)...${NC}"
            docker-compose run --rm --entrypoint "\
              certbot certonly --webroot -w /var/www/certbot \
                --email $EMAIL --domain $HOST_NAME \
                --rsa-key-size 4096 \
                --agree-tos \
                --force-renewal \
                --non-interactive" certbot
            cert_exit_code=$?
        fi

        if [ $cert_exit_code -eq 0 ]; then
            echo -e "${GREEN}Certificado SSL obtido (ou simulado)! A reconfigurar Nginx para HTTPS...${NC}"
            cp ./nginx/nginx.https.conf ./nginx/nginx.conf
            sed -i "s/YOUR_DOMAIN_OR_IP/$HOST_NAME/g" ./nginx/nginx.conf
            echo -e "${BLUE}A atualizar .env com ENABLE_HTTPS=true...${NC}"
            sed -i 's/ENABLE_HTTPS=false/ENABLE_HTTPS=true/' .env
        else
            echo -e "${RED}Falha ao obter/simular certificado SSL. A continuar com HTTP.${NC}"
        fi
    else
        echo -e "${YELLOW}---> Endereço IP detetado. A configurar Nginx para HTTP...${NC}"
        cp ./nginx/nginx.http.conf ./nginx/nginx.conf
        sed -i "s/YOUR_DOMAIN_OR_IP/$HOST_NAME/g" ./nginx/nginx.conf
    fi

    echo -e "${GREEN}---> A construir e a iniciar todos os contentores...${NC}"
    docker-compose build --no-cache && docker-compose up -d

    echo -e "${BLUE}A aguardar que a base de dados esteja pronta...${NC}"
    until docker-compose exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" "$DB_SERVICE_NAME" psql -h "$DB_SERVICE_NAME" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
      >&2 echo "Postgres is unavailable - sleeping"
      sleep 1
    done

    echo -e "${BLUE}A executar migrações da base de dados...${NC}"
    docker-compose exec -T "$WEB_SERVICE_NAME" python manage.py migrate --noinput

    # Os passos de construção de front-end e a recolha de estáticos foram removidos.
    # O Dockerfile agora lida com toda a construção de assets e o 'collectstatic'.

    echo -e "${GREEN}---> Instalação concluída! O seu site está disponível em http://$HOST_NAME (ou https://$HOST_NAME).${NC}"
    echo -e "${YELLOW}Para criar um superuser, execute: 'sudo docker-compose exec $WEB_SERVICE_NAME python manage.py createsuperuser'${NC}"
}

# A função copy_vendor_assets foi removida, pois esta lógica agora pertence ao Dockerfile.

# 2. FAZER BACKUP (APENAS DADOS)
backup_system() {
    echo -e "${GREEN}---> Iniciando Backup de Dados (Base de Dados e Media)...${NC}"
    if [ "$EUID" -ne 0 ]; then
      echo -e "${RED}Esta opção precisa de permissões de root. Por favor, execute com 'sudo ./manage.sh'.${NC}"
      exit 1
    fi

    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    else
        echo -e "${RED}ERRO: Ficheiro .env não encontrado. Não é possível fazer backup.${NC}"
        exit 1
    fi

    BACKUP_DIR="$PROJECT_DIR/backups"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
    BACKUP_FILE="$BACKUP_DIR/data-backup-$TIMESTAMP.tar.gz"
    TMP_BACKUP_DIR="/tmp/pyvpn_backup_$TIMESTAMP"
    mkdir -p "$TMP_BACKUP_DIR/db" "$TMP_BACKUP_DIR/media"

    echo -e "${BLUE}A fazer dump da base de dados...${NC}"
    docker-compose exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" "$DB_SERVICE_NAME" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$TMP_BACKUP_DIR/db/dump.sql"

    echo -e "${BLUE}A copiar ficheiros de media do volume...${NC}"
    docker run --rm --volumes-from "$(docker-compose ps -q $WEB_SERVICE_NAME)" -v "$TMP_BACKUP_DIR/media:/backup" alpine sh -c 'cp -a /app/media/. /backup/'

    echo -e "${BLUE}A criar o ficheiro de backup '$BACKUP_FILE'...${NC}"
    tar -czf "$BACKUP_FILE" -C "$TMP_BACKUP_DIR" .

    rm -rf "$TMP_BACKUP_DIR"

    if [ ! -s "$BACKUP_FILE" ]; then
        echo -e "${RED}ERRO: Falha ao criar o ficheiro de backup ou o ficheiro está vazio.${NC}"; exit 1;
    fi

    echo -e "${GREEN}Backup de dados criado com sucesso em: $BACKUP_FILE${NC}"
    echo -e "${BLUE}A limpar backups com mais de 30 dias...${NC}"
    find "$BACKUP_DIR" -type f -name 'data-backup-*.tar.gz' -mtime +30 -exec rm {} \;
}

# 3. RESTAURAR BACKUP (APENAS DADOS)
restore_system() {
    echo -e "${GREEN}---> Iniciando Restauro de Dados...${NC}"
    if [ "$EUID" -ne 0 ]; then
      echo -e "${RED}Esta opção precisa de permissões de root. Por favor, execute com 'sudo ./manage.sh'.${NC}"
      exit 1
    fi

    if [ ! -f .env ]; then
        echo -e "${RED}ERRO: Ficheiro .env não encontrado. Não é possível restaurar.${NC}"
        exit 1
    fi
    export $(grep -v '^#' .env | xargs)

    BACKUP_FILE=""
    TEMP_DOWNLOAD_FILE=""

    echo -e "${BLUE}Escolha a fonte do backup:${NC}"
    echo "  1) Restaurar de um backup local (da pasta 'backups/')"
    echo "  2) Restaurar de um URL"
    read -p "Opção [1-2]: " choice

    case "$choice" in
        1)
            BACKUP_DIR="$PROJECT_DIR/backups"
            if [ ! -d "$BACKUP_DIR" ] || [ -z "$(find "$BACKUP_DIR" -maxdepth 1 -name '*.tar.gz' -print -quit)" ]; then
                echo -e "${RED}Nenhum backup local encontrado em '$BACKUP_DIR'.${NC}"
                return 1
            fi
            echo -e "${BLUE}Backups locais disponíveis:${NC}"
            mapfile -t backups < <(find "$BACKUP_DIR" -maxdepth 1 -name '*.tar.gz' | sort -r)
            i=0
            for b in "${backups[@]}"; do
                echo "  $((++i))) $(basename "$b")"
            done
            read -p "Escolha o backup para restaurar [1-$i]: " backup_choice
            if [[ ! "$backup_choice" =~ ^[0-9]+$ ]] || [ "$backup_choice" -lt 1 ] || [ "$backup_choice" -gt $i ]; then
                echo -e "${RED}Seleção inválida.${NC}"
                return 1
            fi
            BACKUP_FILE="${backups[$((backup_choice-1))]}"
            ;;
        2)
            read -p "Insira o URL do ficheiro de backup (.tar.gz): " URL
            if [[ ! "$URL" =~ ^https?://.*\.tar\.gz$ ]]; then
                echo -e "${RED}URL inválido. Deve ser um link direto para um ficheiro .tar.gz.${NC}"
                return 1
            fi
            TEMP_DOWNLOAD_FILE=$(mktemp --suffix=.tar.gz)
            echo -e "${BLUE}A descarregar backup de $URL...${NC}"
            if ! curl -L -o "$TEMP_DOWNLOAD_FILE" "$URL"; then
                echo -e "${RED}Falha ao descarregar o ficheiro.${NC}"
                rm -f "$TEMP_DOWNLOAD_FILE"
                return 1
            fi
            BACKUP_FILE="$TEMP_DOWNLOAD_FILE"
            ;;
        *)
            echo -e "${RED}Opção inválida.${NC}"
            return 1
            ;;
    esac

    if [ ! -f "$BACKUP_FILE" ]; then echo -e "${RED}ERRO: Ficheiro de backup não foi definido corretamente.${NC}"; exit 1; fi

    echo -e "${YELLOW}AVISO: Este processo é DESTRUTIVO e irá apagar os dados atuais da BD e media.${NC}"
    read -p "Tem a certeza? (escreva 'sim' para confirmar): " CONFIRMATION
    if [ "$CONFIRMATION" != "sim" ]; then echo "Restauro cancelado."; rm -f "$TEMP_DOWNLOAD_FILE"; exit 0; fi

    RESTORE_DIR=$(mktemp -d)
    echo -e "${BLUE}A extrair backup para diretório temporário...${NC}"
    tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"

    echo -e "${BLUE}A parar serviços e a remover volumes de dados...${NC}"
    docker-compose down -v

    echo -e "${BLUE}A recriar e a iniciar todos os serviços com volumes vazios...${NC}"
    docker-compose build --no-cache && docker-compose up -d

    echo -e "${BLUE}A aguardar que a base de dados esteja pronta...${NC}"
    until docker-compose exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" "$DB_SERVICE_NAME" psql -h "$DB_SERVICE_NAME" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
      >&2 echo "Postgres is unavailable - sleeping"
      sleep 1
    done

    echo -e "${BLUE}A restaurar a base de dados...${NC}"
    cat "$RESTORE_DIR/db/dump.sql" | docker-compose exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" "$DB_SERVICE_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

    echo -e "${BLUE}A restaurar ficheiros de media...${NC}"
    docker run --rm --volumes-from "$(docker-compose ps -q $WEB_SERVICE_NAME)" -v "$RESTORE_DIR/media:/backup" alpine sh -c 'cp -a /backup/. /app/media/'

    rm -rf "$RESTORE_DIR"
    rm -f "$TEMP_DOWNLOAD_FILE" # Limpa o ficheiro descarregado se existir
    echo -e "${GREEN}Restauro de dados concluído com sucesso!${NC}"
}

# 4. VER .ENV
view_env() {
    echo -e "${BLUE}--- Conteúdo do seu ficheiro .env ---${NC}"
    if [ -f ".env" ]; then
        cat .env
    else
        echo -e "${YELLOW}Ficheiro .env não encontrado. Execute a instalação primeiro.${NC}"
    fi
    echo -e "${BLUE}------------------------------------${NC}"
}

# 5. VER E PREPARAR DOWNLOAD DE BACKUPS
view_and_prepare_download() {
    echo -e "${GREEN}---> Listar e Preparar Download de Backups...${NC}"
    if [ "$EUID" -ne 0 ]; then
      echo -e "${RED}Esta opção precisa de permissões de root. Por favor, execute com 'sudo ./manage.sh'.${NC}"
      exit 1
    fi

    BACKUP_DIR="$PROJECT_DIR/backups"
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR)" ]; then
        echo -e "${YELLOW}Nenhum backup encontrado em $BACKUP_DIR${NC}"
        exit 0
    fi

    echo -e "${BLUE}Backups disponíveis:${NC}"
    mapfile -t backups < <(find "$BACKUP_DIR" -name 'data-backup-*.tar.gz' | sort -r)
    
    i=0
    for backup in "${backups[@]}"; do
        echo "  $((i+1))) $(basename "$backup")"
        i=$((i+1))
    done

    read -p "Escolha o número do backup que deseja descarregar (ou 0 para sair): " choice

    if [[ ! "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 0 ] || [ "$choice" -gt "${#backups[@]}" ]; then
        echo -e "${RED}Opção inválida.${NC}"
        exit 1
    fi

    if [ "$choice" -eq 0 ]; then
        echo "Operação cancelada."
        exit 0
    fi

    selected_backup="${backups[$((choice-1))]}"
    REMOTE_USER=$(logname)
    REMOTE_HOST=$(hostname -I | awk '{print $1}')

    echo -e "${YELLOW}------------------------------------------------------------------${NC}"
    echo -e "${GREEN}Para descarregar o ficheiro, copie e cole o seguinte comando no terminal do SEU COMPUTADOR LOCAL:${NC}"
    echo -e "\n  scp ${REMOTE_USER}@${REMOTE_HOST}:${selected_backup} .\n"
    echo -e "${YELLOW}------------------------------------------------------------------${NC}"
}

# 6. ATUALIZAR APLICAÇÃO (SEM DESTRUIR DADOS)
update_application() {
    echo -e "${GREEN}---> A iniciar a atualização da aplicação...${NC}"
    
    echo -e "${BLUE}A descarregar as últimas alterações do Git...${NC}"
    if ! git pull; then
        echo -e "${RED}Falha ao executar 'git pull'. Por favor, resolva os conflitos ou problemas e tente novamente.${NC}"
        exit 1
    fi

    echo -e "${BLUE}A reconstruir a imagem da aplicação web...${NC}"
    if ! docker-compose build --no-cache web; then
        echo -e "${RED}Falha ao construir a imagem Docker. Verifique o Dockerfile e os logs.${NC}"
        exit 1
    fi

    echo -e "${BLUE}A reiniciar os serviços com o novo código...${NC}"
    if ! docker-compose up -d --force-recreate; then
        echo -e "${RED}Falha ao reiniciar os contentores.${NC}"
        exit 1
    fi

    echo -e "${GREEN}---> Atualização concluída com sucesso!${NC}"
}

# 7. RENOVAR CERTIFICADOS SSL MANUALMENTE
renew_ssl_certs() {
    echo -e "${GREEN}---> A tentar renovar os certificados SSL manualmente...${NC}"
    # Verifica se o contentor do certbot está a correr. ps -q devolve um ID se estiver 'Up'.
    if [ -z "$(docker-compose ps -q certbot)" ]; then
        echo -e "${YELLOW}AVISO: O contentor do Certbot não está a correr. A renovação só funciona se o sistema estiver instalado com HTTPS.${NC}"
        return 1
    fi
    docker-compose exec certbot certbot renew
    echo -e "${GREEN}---> Tentativa de renovação concluída.${NC}"
}

# --- Menu Principal ---
show_menu() {
    clear
    echo "================================================="
    echo "     Gestor de Projeto Docker - PY_VPN"
    echo "================================================="
    echo "Opções:"
    echo "1) Instalar/Atualizar Sistema (Produção)"
    echo "2) Instalar/Atualizar Sistema (Teste Staging)"
    echo "3) Fazer Backup do Sistema"
    echo "4) Restaurar Sistema a partir de um Backup"
    echo "5) Ver ficheiro de ambiente (.env)"
    echo "6) Ver e Preparar Download de Backups"
    echo "7) Atualizar Aplicação (Recomendado)"
    echo "8) Renovar Certificados SSL Manualmente"
    echo "9) Sair"
    echo "-------------------------------------------------"
}

# --- Loop Principal de Execução ---
while true; do
    show_menu
    read -p "Escolha uma opção [1-9]: " choice
    case "$choice" in
        1) setup_new_server "production" ;;
        2) setup_new_server "staging" ;;
        3) backup_system ;;
        4) restore_system ;;
        5) view_env ;;
        6) view_and_prepare_download ;;
        7) update_application ;;
        8) renew_ssl_certs ;;
        9) echo "A sair."; exit 0 ;;
        *) echo -e "${RED}Opção inválida. Tente novamente.${NC}"; sleep 2 ;;
    esac
    
    echo
    read -p "Pressione Enter para continuar..."
done
