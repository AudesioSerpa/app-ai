#!/usr/bin/env bash
# Renderiza o episódio em partes (retoma de onde parou se o servidor reiniciar) e junta no final.
# Uso: ./render_partes.sh [--cta]
set -euo pipefail
cd "$(dirname "$0")"
BROWSER="${BROWSER:-/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell}"
PROPS='{"showCta":false}'; OUT="out/episodio-01.mp4"
if [[ "${1:-}" == "--cta" ]]; then PROPS='{"showCta":true}'; OUT="out/episodio-01-cta.mp4"; fi
TOTAL=$(python3 -c "import json,math;t=json.load(open('src/timeline.json'));print(math.ceil(t['total']*t['fps']))")
CHUNK=6000
mkdir -p out/partes
npx remotion bundle src/index.ts --out-dir=out/bundle --log=error >/dev/null
: > out/partes/lista.txt
for ((s=0; s<TOTAL; s+=CHUNK)); do
  e=$((s+CHUNK-1)); ((e>=TOTAL)) && e=$((TOTAL-1))
  p=$(printf "out/partes/p%05d.mp4" $s)
  echo "file '$(basename $p)'" >> out/partes/lista.txt
  [[ -f $p ]] && continue
  npx remotion render out/bundle Episodio01 "$p.tmp.mp4" --props="$PROPS" --frames=$s-$e --muted \
    --browser-executable="$BROWSER" --codec=h264 --crf=18 --concurrency=4 --log=error
  mv "$p.tmp.mp4" "$p"; echo "parte $s-$e ok"
done
# junta o vídeo e coloca a narração (áudio gerado direto dos blocos, como no Remotion)
python3 scripts/mix_audio.py out/partes/audio.m4a
ffmpeg -v error -y -f concat -safe 0 -i out/partes/lista.txt -i out/partes/audio.m4a -map 0:v -map 1:a -c copy -movflags +faststart "$OUT"
echo "Pronto: $OUT"
