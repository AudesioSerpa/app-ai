#!/usr/bin/env bash
# Renderiza o episódio completo em Full HD (1920x1080), MP4 H.264.
# Uso: ./render.sh            (sem chamadas de curtir/inscrever na imagem)
#      ./render.sh --cta      (com chamadas discretas)
set -euo pipefail
cd "$(dirname "$0")"
BROWSER="${BROWSER:-/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell}"
PROPS='{"showCta":false}'
OUT="out/episodio-01.mp4"
if [[ "${1:-}" == "--cta" ]]; then PROPS='{"showCta":true}'; OUT="out/episodio-01-cta.mp4"; fi
npx remotion render src/index.ts Episodio01 "$OUT" \
  --props="$PROPS" \
  --browser-executable="$BROWSER" \
  --codec=h264 --crf=18 --audio-bitrate=192k \
  --concurrency=4 --log=info
echo "Pronto: $OUT"
