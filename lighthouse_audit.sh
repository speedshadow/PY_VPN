#!/bin/bash
# Script para rodar Lighthouse automaticamente em várias rotas do site local

# Lista de rotas para auditar
ROUTES=( "/" "/vpn/" "/blog/" "/faq/" "/contact/" "/dashboard/" )

# Garante que a pasta de relatórios existe
REPORT_DIR="lighthouse_reports"
mkdir -p "$REPORT_DIR"

# Checa se lighthouse está instalado
if ! command -v lighthouse &> /dev/null; then
    echo "[ERRO] O Lighthouse CLI não está instalado. Rode: npm install -g lighthouse"
    exit 1
fi

for ROUTE in "${ROUTES[@]}"; do
    # Substitui / por - para nome do arquivo
    SAFE_ROUTE=$(echo "$ROUTE" | sed 's/\//-/g')
    [ "$SAFE_ROUTE" = "-" ] && SAFE_ROUTE="root"
    OUTFILE="$REPORT_DIR/lighthouse${SAFE_ROUTE}.html"
    echo "[INFO] Auditando: http://localhost:8080$ROUTE -> $OUTFILE"
    lighthouse "http://localhost:8080$ROUTE" --output html --output-path "$OUTFILE" --chrome-flags="--headless"
done

echo "[OK] Relatórios gerados em $REPORT_DIR/"
