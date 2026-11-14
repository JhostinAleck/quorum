#!/bin/bash
# Build the Quórum video: narration track + timeline, frames rendered by headless Chrome, mux with ffmpeg.
#
#   PUPPETEER_DIR=<folder with node_modules/puppeteer-core> docs/video/montar.sh [output.mp4]
#
# Voice: takes in voz/eNN.mp3 (see animacion/voz_elevenlabs.py) are used when present; otherwise the
# macOS voice in $VOZ. Generated shots in planos/ are used when planos/clips.js lists them.
# No key is read here: voz_elevenlabs.py takes ELEVENLABS_API_KEY from the environment.
set -euo pipefail
cd "$(dirname "$0")"
OUT="${1:-quorum-video.mp4}"
FFMPEG="${FFMPEG:-/opt/homebrew/bin/ffmpeg}"
FFPROBE="${FFPROBE:-/opt/homebrew/bin/ffprobe}"
WORK="${WORK:-$(mktemp -d)}"
: "${PUPPETEER_DIR:?set PUPPETEER_DIR to a folder that has node_modules/puppeteer-core}"

python3 animacion/build_timeline.py "$WORK"
rm -rf "$WORK/frames"
node animacion/render.js "$PUPPETEER_DIR" "$WORK/frames" "${WORKERS:-8}"
"$FFMPEG" -nostdin -v error -y -framerate 30 -i "$WORK/frames/f_%05d.jpg" -i "$WORK/audio.wav" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
real="$("$FFPROBE" -v error -show_entries format=duration -of csv=p=0 "$OUT")"
echo "written: $OUT (${real}s)"
awk "BEGIN { exit !($real > 120) }" && { echo "ERROR: longer than 120 s" >&2; exit 1; }
exit 0
