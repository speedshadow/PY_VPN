#!/bin/bash
# Roda Lighthouse CLI para todas as rotas públicas e salva relatórios HTML
# Uso: ./scripts/lighthouse_audit.sh

set -e

# Endereço do site em produção ou localhost
BASE_URL=${1:-http://localhost}
REPORT_DIR="$(dirname "$0")/../lighthouse_reports"

mkdir -p "$REPORT_DIR"

# Rotas públicas a auditar
ROUTES=(
  "/"
  "/contact/"
  "/faq/"
  "/vpn/"
)

for ROUTE in "${ROUTES[@]}"; do
  SAFE_ROUTE=$(echo "$ROUTE" | sed 's/\//-/g' | sed 's/^-//')
  lighthouse --quiet --chrome-flags="--headless --no-sandbox" \
    "$BASE_URL$ROUTE" \
    --output html \
    --output-path "$REPORT_DIR/lighthouse${SAFE_ROUTE}.html"
done

echo "Relatórios Lighthouse gerados em $REPORT_DIR"
