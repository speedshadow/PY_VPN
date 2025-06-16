#!/bin/bash

# 'set -e' faz com que o script termine imediatamente se um comando falhar.
set -e

# --- Configurações ---
# Diretório onde os backups serão guardados (fora da pasta do projeto)
BACKUP_DIR="/var/backups/py_vpn_backups"
# Nome do projeto (usado para os nomes dos contentores/volumes do Docker)
PROJECT_NAME="PY_VPN_MASTER"
# Número de dias para manter os backups
RETENTION_DAYS=30

# --- Lógica do Script ---

echo "A iniciar o processo de backup..."

# Garante que o diretório de backups existe
mkdir -p "$BACKUP_DIR"

# Define o nome do ficheiro de backup com a data e hora
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/backup-$TIMESTAMP.tar.gz"
DB_DUMP_FILE="db_dump-$TIMESTAMP.sql"

# Navega para o diretório do projeto para usar o docker-compose.yml
# Usa o diretório onde o script está localizado
cd "$(dirname "$0")"

# 1. Fazer o dump da base de dados PostgreSQL
echo "A fazer o dump da base de dados..."
docker compose exec -T db pg_dumpall -U py_vpn_master_user > "$DB_DUMP_FILE"
echo "Dump da base de dados criado: $DB_DUMP_FILE"

# 2. Arquivar o dump da BD e a pasta de media
# O docker-compose cria volumes com o nome do projeto como prefixo.
MEDIA_VOLUME_NAME="$(basename $(pwd))_media_volume"

echo "A arquivar o dump da BD e o volume de media ($MEDIA_VOLUME_NAME)..."
# Usamos um contentor temporário para aceder ao volume e criar o tarball
docker run --rm -v "$MEDIA_VOLUME_NAME":/media_volume:ro -v "$(pwd)":/backup_source alpine tar -czf - -C /backup_source "$DB_DUMP_FILE" -C /media_volume . > "$BACKUP_FILE"

# 3. Limpar o ficheiro de dump temporário
rm "$DB_DUMP_FILE"

echo "Arquivo de backup criado com sucesso: $BACKUP_FILE"

# 4. Limpar backups antigos
echo "A limpar backups com mais de $RETENTION_DAYS dias..."
find "$BACKUP_DIR" -type f -name 'backup-*.tar.gz' -mtime +$RETENTION_DAYS -exec rm {} \;

echo "Processo de backup concluído!"
