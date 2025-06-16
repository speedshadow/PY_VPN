#!/bin/bash

# 'set -e' faz com que o script termine imediatamente se um comando falhar.
set -e

# ==============================================================================
#   Script de Implantação Automatizada com Docker para Django
#   Versão 1.0
# ==============================================================================
#   Autor: Cascade AI
#   Descrição: Este script, executado com sudo, automatiza a implantação de
#              um projeto Django num ambiente Dockerizado em produção.
#
#   Funcionalidades:
#              - Instala Docker e Docker Compose.
#              - Clona o projeto do Git.
#              - Pede ao utilizador o domínio/IP.
#              - Gera um ficheiro .env com segredos automaticamente.
#              - Configura o Nginx.
#              - Constrói e inicia os contentores com Docker Compose.
#              - Executa migrações da base de dados.
# ==============================================================================

# --- Funções de Ajuda e Cores ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- Verificação de Root ---
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}Por favor, execute este script como root ou com sudo.${NC}"
  exit 1
fi

# --- Instalação de Dependências (Docker e Git) ---
echo -e "${GREEN}---> Atualizando o sistema e instalando dependências...${NC}"
apt-get update
apt-get install -y git curl

# Instala o Docker (usando o script oficial para garantir a versão mais recente)
echo -e "${GREEN}---> Instalando Docker...${NC}"
if ! command -v docker &> /dev/null
then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo -e "${YELLOW}Docker já está instalado. A saltar.${NC}"
fi

# --- Recolha de Informação do Utilizador ---
echo -e "${GREEN}---> A recolher informações de configuração...${NC}"
read -p "Qual é o domínio ou endereço IP do seu servidor? (ex: meusite.com ou 123.45.67.89): " HOST_NAME

if [ -z "$HOST_NAME" ]; then
    echo -e "${YELLOW}O domínio ou IP não pode ser vazio. A sair.${NC}"
    exit 1
fi

# --- Clonar o Projeto ---
PROJECT_DIR="/var/www/PY_VPN_MASTER"
echo -e "${GREEN}---> Clonando o projeto do GitHub para $PROJECT_DIR...${NC}"
if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}O diretório $PROJECT_DIR já existe. A saltar a clonagem.${NC}"
else
    git clone https://github.com/speedshadow/PY_VPN.git "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# --- Geração do Ficheiro .env ---
echo -e "${GREEN}---> Gerando o ficheiro de ambiente .env...${NC}"

# Gerar valores aleatórios para segredos
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)

cat > .env << EOF
# Ficheiro de configuração de ambiente - gerado automaticamente

# Segurança Django
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$HOST_NAME,localhost,127.0.0.1

# Base de Dados PostgreSQL (usado pelo docker-compose)
POSTGRES_DB=py_vpn_master_db
POSTGRES_USER=py_vpn_master_user
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# Configurações de HTTPS (ainda não implementado)
ENABLE_HTTPS=False
EOF

# --- Configuração do Nginx ---
echo -e "${GREEN}---> Configurando o Nginx...${NC}"
# Substitui o 'server_name' no ficheiro de configuração do Nginx
sed -i "s/server_name localhost;/server_name $HOST_NAME;/" ./nginx/nginx.conf

# --- Construir e Iniciar os Contentores ---
echo -e "${GREEN}---> Construindo e iniciando os contentores com Docker Compose...${NC}"
echo -e "${YELLOW}Isto pode demorar vários minutos na primeira vez...${NC}"
docker compose up --build -d

# --- Executar Comandos Finais do Django ---
echo -e "${GREEN}---> A aguardar que a base de dados esteja pronta...${NC}"
sleep 15 # Dá tempo ao contentor da BD para iniciar completamente

echo -e "${GREEN}---> A executar migrações da base de dados...${NC}"
docker compose exec -T web python manage.py migrate --noinput

echo -e "${GREEN}---> A recolher ficheiros estáticos...${NC}"
docker compose exec -T web python manage.py collectstatic --noinput --clear

# --- Conclusão ---
echo -e "\n${GREEN}=======================================================${NC}"
echo -e "${GREEN}  A sua aplicação foi implementada com sucesso!      ${NC}"
echo -e "${GREEN}=======================================================${NC}"
echo -e "\nO seu site deve estar acessível em: ${YELLOW}http://$HOST_NAME${NC}"

echo -e "\nPara criar um superutilizador, execute o seguinte comando:"
echo -e "${YELLOW}  cd $PROJECT_DIR && docker compose exec web python manage.py createsuperuser${NC}"

echo -e "\nComandos úteis do Docker:"
echo -e "  - Ver logs em tempo real: ${YELLOW}cd $PROJECT_DIR && docker compose logs -f${NC}"
echo -e "  - Parar os serviços: ${YELLOW}cd $PROJECT_DIR && docker compose down${NC}"
