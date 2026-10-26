#!/usr/bin/env bash
# Inicia a interface local do Riffusion (CPU) e abre o navegador.
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -x .venv/bin/python ]]; then
  echo "Ambiente não encontrado. Rode ./setup.sh primeiro." >&2
  exit 1
fi

source .venv/bin/activate

PORT="${RIFFUSION_PORT:-8501}"
URL="http://127.0.0.1:${PORT}"

# Se já houver um servidor rodando nesta porta, apenas abre o navegador.
if curl -s -o /dev/null "${URL}/_stcore/health" 2>/dev/null; then
  echo "Riffusion já está rodando em ${URL}"
  xdg-open "${URL}" >/dev/null 2>&1 || true
  exit 0
fi

echo "Iniciando Riffusion Local em ${URL}"
echo "Pressione Ctrl+C para encerrar."

# Abre o navegador quando o servidor estiver de pé.
(
  for _ in $(seq 1 30); do
    if curl -s -o /dev/null "${URL}/_stcore/health" 2>/dev/null; then
      xdg-open "${URL}" >/dev/null 2>&1 || true
      break
    fi
    sleep 1
  done
) &

exec python -m streamlit run streamlit_app.py \
  --server.address 127.0.0.1 \
  --server.port "${PORT}" \
  --browser.gatherUsageStats false
