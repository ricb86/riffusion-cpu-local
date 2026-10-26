#!/usr/bin/env bash
#
# setup.sh — instala o Riffusion Local (CPU) em Python 3.12, sem sudo.
#
# O que faz:
#   1. Encontra (ou cria) um Python 3.12;
#   2. Garante compilador C/C++ + pkg-config + OpenSSL (conda-forge se faltar);
#   3. Instala Rust (rustup) se necessário — tokenizers/safetensors compilam do zero;
#   4. Cria a venv .venv e instala as versões fixadas em requirements-cpu.txt;
#   5. Baixa o modelo (~4 GB) para ~/AI-Music/models/riffusion-model-v1.
#
# Uso:
#   ./setup.sh                 # instalação completa
#   SKIP_MODEL=1 ./setup.sh    # sem baixar o modelo
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

VENV="$REPO_DIR/.venv"
PYENV="$REPO_DIR/.python"
TOOLCHAIN_BIN="$REPO_DIR/.toolchain/bin"
MODEL_DIR="${RIFFUSION_CKPT:-$HOME/AI-Music/models/riffusion-model-v1}"

say()  { printf '\n\033[1;33m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m    %s\033[0m\n' "$*"; }
die()  { printf '\n\033[1;31mERRO: %s\033[0m\n' "$*" >&2; exit 1; }

find_conda() {
  if command -v conda >/dev/null 2>&1; then command -v conda; return 0; fi
  local c
  for c in \
    "$HOME/pinokio/bin/miniforge/bin/conda" \
    "$HOME/miniforge3/bin/conda" \
    "$HOME/mambaforge/bin/conda" \
    "$HOME/miniconda3/bin/conda" \
    "$HOME/anaconda3/bin/conda"; do
    if [[ -x "$c" ]]; then echo "$c"; return 0; fi
  done
  return 1
}

find_python312() {
  local p
  for p in python3.12 python3; do
    if command -v "$p" >/dev/null 2>&1 &&
       "$p" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)' 2>/dev/null; then
      command -v "$p"; return 0
    fi
  done
  return 1
}

version_ge() {  # version_ge A B  ->  A >= B
  printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# ----------------------------------------------------------------------------
say "1/6 Python 3.12"

CONDA="$(find_conda || true)"

if PY="$(find_python312)"; then
  ok "usando $PY ($("$PY" -c 'import platform; print(platform.python_version())'))"
else
  [[ -n "$CONDA" ]] || die "Python 3.12 não encontrado e conda indisponível.
Instale Python 3.12 (ex.: sudo apt install python3.12 python3.12-venv) ou o Miniforge e rode de novo."
  say "criando ambiente Python 3.12 em .python (conda)"
  "$CONDA" create -y -p "$PYENV" python=3.12 >/dev/null
  PY="$PYENV/bin/python3.12"
  ok "criado: $PY"
fi

# ----------------------------------------------------------------------------
say "2/6 Compilador C/C++, pkg-config e OpenSSL"

need=0
for tool in cc c++ ar pkg-config; do
  command -v "$tool" >/dev/null 2>&1 || need=1
done
pkg-config --exists openssl 2>/dev/null || need=1

if (( need )); then
  [[ -n "$CONDA" ]] || die "Faltam cc/c++/ar/pkg-config ou headers do OpenSSL.
Sem sudo, instale o Miniforge e rode de novo (o script instala o toolchain via conda-forge)."

  if [[ ! -d "$PYENV" ]]; then
    say "criando ambiente de toolchain em .python"
    "$CONDA" create -y -p "$PYENV" >/dev/null
  fi

  say "instalando gcc/g++/binutils/pkg-config/openssl via conda-forge"
  "$CONDA" install -y -p "$PYENV" -c conda-forge \
    gcc_linux-64 gxx_linux-64 binutils_linux-64 pkg-config openssl >/dev/null

  mkdir -p "$TOOLCHAIN_BIN"
  for t in cc gcc c++ g++ ar as ld nm ranlib strip; do
    src="$PYENV/bin/x86_64-conda-linux-gnu-$t"
    [[ -e "$src" ]] && ln -sf "$src" "$TOOLCHAIN_BIN/$t"
  done
  export PATH="$TOOLCHAIN_BIN:$PATH"
  export PKG_CONFIG_PATH="$PYENV/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
  export OPENSSL_DIR="$PYENV"
  ok "toolchain em $TOOLCHAIN_BIN"
else
  ok "toolchain do sistema OK ($(cc --version | head -1))"
fi

# ----------------------------------------------------------------------------
say "3/6 Rust"

export PATH="$TOOLCHAIN_BIN:$HOME/.cargo/bin:$PATH"
if [[ -f "$HOME/.cargo/env" ]]; then . "$HOME/.cargo/env"; fi

if command -v rustc >/dev/null 2>&1 && version_ge "$(rustc --version | awk '{print $2}')" 1.80; then
  ok "rustc $(rustc --version | awk '{print $2}')"
else
  say "instalando Rust stable via rustup (~/.cargo)"
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs |
    sh -s -- -y --profile minimal --default-toolchain stable
  . "$HOME/.cargo/env"
  ok "rustc $(rustc --version | awk '{print $2}')"
fi

# tokenizers 0.13.3 usa um cast que virou lint deny-by-default em Rust novo
export RUSTFLAGS="-A invalid_reference_casting"

# ----------------------------------------------------------------------------
say "4/6 Ambiente Python (.venv)"

[[ -d "$VENV" ]] || "$PY" -m venv "$VENV"
PIP="$VENV/bin/python -m pip"
$PIP install --quiet --upgrade pip
$PIP install --quiet "setuptools==75.8.0" wheel

say "instalando dependências (compila tokenizers/safetensors — leva ~15-30 min)"
$PIP install --no-cache-dir \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  -r requirements-cpu.txt

say "instalando o pacote riffusion (editável)"
$PIP install --no-deps -e .

ok "dependências instaladas"

# ----------------------------------------------------------------------------
say "5/6 Verificação"

"$VENV/bin/python" - <<'PY'
import numpy, torch, transformers, diffusers, streamlit
from riffusion.riffusion_pipeline import RiffusionPipeline  # noqa: F401
print(f"    torch {torch.__version__} | numpy {numpy.__version__} | "
      f"transformers {transformers.__version__} | diffusers {diffusers.__version__} | "
      f"streamlit {streamlit.__version__}")
print("    imports do Riffusion OK")
PY

# ----------------------------------------------------------------------------
say "6/6 Modelo riffusion-model-v1 (~4 GB)"

if [[ "${SKIP_MODEL:-0}" == "1" ]]; then
  ok "pulado (SKIP_MODEL=1). Rode ./download_model.sh quando quiser."
elif [[ -s "$MODEL_DIR/unet/diffusion_pytorch_model.bin" ]]; then
  ok "já existe em $MODEL_DIR"
else
  RIFFUSION_CKPT="$MODEL_DIR" ./download_model.sh
fi

printf '\n\033[1;32mPronto!\033[0m  Inicie com: ./run.sh\n\n'
