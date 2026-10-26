#!/usr/bin/env bash
# Baixa o checkpoint riffusion-model-v1 (~4 GB) para ~/AI-Music/models/riffusion-model-v1
# com retomada automática em caso de conexão interrompida.
set -euo pipefail

DEST="${RIFFUSION_CKPT:-$HOME/AI-Music/models/riffusion-model-v1}"
BASE="https://huggingface.co/riffusion/riffusion-model-v1/resolve/main"

FILES=(
  model_index.json
  feature_extractor/preprocessor_config.json
  safety_checker/config.json
  scheduler/scheduler_config.json
  text_encoder/config.json
  text_encoder/pytorch_model.bin
  tokenizer/merges.txt
  tokenizer/special_tokens_map.json
  tokenizer/tokenizer_config.json
  tokenizer/vocab.json
  unet/config.json
  unet/diffusion_pytorch_model.bin
  vae/config.json
  vae/diffusion_pytorch_model.bin
)

fetch() {
  local url="$1" out="$2" expected have
  expected="$(curl -sIL "$url" | awk 'BEGIN{IGNORECASE=1} /^content-length:/{v=$2} END{gsub("\r","",v); print v}')"

  if command -v wget >/dev/null 2>&1; then
    wget -q --continue --tries=0 --timeout=30 --waitretry=3 --show-progress -O "$out" "$url"
  else
    curl -L --fail --retry 10 --retry-all-errors --continue-at - -o "$out" "$url" || true
  fi

  if [[ -n "${expected:-}" && -f "$out" ]]; then
    have="$(stat -c %s "$out")"
    if [[ "$have" != "$expected" ]]; then
      echo "ERRO: $out incompleto ($have/$expected bytes). Rode de novo para retomar." >&2
      return 1
    fi
  fi
}

mkdir -p "$DEST"
for f in "${FILES[@]}"; do
  mkdir -p "$DEST/$(dirname "$f")"
  printf '>> %s\n' "$f"
  fetch "$BASE/$f" "$DEST/$f"
done

echo "Modelo pronto em: $DEST"
