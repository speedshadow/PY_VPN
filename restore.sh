#!/bin/bash

# 'set -e' faz com que o script termine imediatamente se um comando falhar.
set -e

# --- Validação de Input ---
if [ "$#" -ne 1 ]; then
    echo "Uso: $0 /caminho/para/o/backup-ficheiro.tar.gz"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Erro: O ficheiro de backup '$BACKUP_FILE' não foi encontrado."
    exit 1
fi

# --- Confirmação do Utilizador (Medida de Segurança) ---
echo "ATENÇÃO: Este processo é DESTRUTIVO."
echo "Ele irá parar a aplicação, apagar a base de dados e os ficheiros de media atuais, e substituí-los pelo conteúdo do backup."
read -p "Tem a certeza que deseja continuar? (escreva 'sim' para confirmar): " CONFIRMATION

if [ "$CONFIRMATION" != "sim" ]; then
    echo "Restauro cancelado pelo utilizador."
    exit 0
fi

# --- Lógica de Restauro ---
echo "A iniciar o processo de restauro..."

# Navega para o diretório do projeto
cd "$(dirname "$0")"

# Cria um diretório de restauro temporário
RESTORE_DIR=$(mktemp -d)

# 1. Extrair o ficheiro de backup
echo "A extrair o ficheiro de backup para um diretório temporário..."
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"
DB_DUMP_FILE=$(find "$RESTORE_DIR" -name 'db_dump-*.sql' -type f -print -quit)

if [ -z "$DB_DUMP_FILE" ]; then
    echo "Erro: Não foi possível encontrar o ficheiro de dump .sql no arquivo de backup."
    rm -rf "$RESTORE_DIR"
    exit 1
fi

# 2. Parar os serviços e remover os volumes antigos para garantir um estado limpo
echo "A parar os serviços e a remover os volumes de dados antigos..."
docker compose down -v

# 3. Iniciar a base de dados para que o volume seja recriado
echo "A iniciar o serviço da base de dados..."
docker compose up -d db

echo "A aguardar que a base de dados esteja pronta..."
sleep 15

# 4. Restaurar a base de dados a partir do dump
echo "A restaurar a base de dados..."
cat "$DB_DUMP_FILE" | docker compose exec -T db psql -U py_vpn_master_user -d py_vpn_master_db

# 5. Restaurar os ficheiros de media
# O docker compose up recriou o volume de media. Agora copiamos os ficheiros.
echo "A restaurar os ficheiros de media..."
# O tar extrai para um diretório 'media_volume' ou similar, ou diretamente. Vamos ser flexíveis.
MEDIA_SOURCE_DIR=$RESTORE_DIR
if [ -d "$RESTORE_DIR/media_volume" ]; then
    MEDIA_SOURCE_DIR="$RESTORE_DIR/media_volume"
fi
docker compose cp "$MEDIA_SOURCE_DIR/." web:/app/media/
# Garante que as permissões estão corretas dentro do contentor
docker compose exec web chown -R django-user:django-user /app/media

# 6. Iniciar todos os outros serviços
echo "A iniciar todos os serviços da aplicação..."
docker compose up -d --remove-orphans

# 7. Limpeza
echo "A limpar ficheiros temporários..."
rm -rf "$RESTORE_DIR"

echo "\nProcesso de restauro concluído com sucesso!"
