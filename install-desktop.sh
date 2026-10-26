#!/usr/bin/env bash
# Cria o atalho "Riffusion Local" no menu de aplicativos e na Área de Trabalho.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS_DIR="$HOME/.local/share/applications"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
[[ -n "$DESKTOP_DIR" ]] || DESKTOP_DIR="$HOME/Desktop"

mkdir -p "$APPS_DIR"

write_entry() {
  local target="$1"
  cat > "$target" <<EOF
[Desktop Entry]
Type=Application
Name=Riffusion Local
Comment=Gerar música com IA localmente (CPU, sem internet)
Exec=$REPO_DIR/run.sh
Path=$REPO_DIR
Icon=audio-x-generic
Terminal=true
Categories=AudioVideo;Audio;Player;
Keywords=music;ia;ai;riffusion;diffusion;
EOF
  chmod +x "$target"
  gio set "$target" metadata::trusted true 2>/dev/null || true
}

write_entry "$APPS_DIR/riffusion-local.desktop"
echo "Atalho criado em: $APPS_DIR/riffusion-local.desktop"

if [[ -d "$DESKTOP_DIR" ]]; then
  write_entry "$DESKTOP_DIR/riffusion-local.desktop"
  echo "Atalho criado em: $DESKTOP_DIR/riffusion-local.desktop"
fi

update-desktop-database "$APPS_DIR" 2>/dev/null || true
echo "Pronto. Procure por 'Riffusion Local' no menu de aplicativos."
