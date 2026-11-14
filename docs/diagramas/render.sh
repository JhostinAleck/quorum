#!/bin/sh
# Exporta los .mmd a PNG. Uso: PUPPETEER_CFG=ruta/a/puppeteer.json ./render.sh
cd "$(dirname "$0")"
for f in *.mmd; do
  npx -y @mermaid-js/mermaid-cli@11.4.2 -i "$f" -o "${f%.mmd}.png" -b white -s 3 -w 1400 ${PUPPETEER_CFG:+-p "$PUPPETEER_CFG"}
done
