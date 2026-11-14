#!/usr/bin/env bash
# Compila la ficha técnica de entrega (quorum.tex -> quorum.pdf) con tectonic.
# Requisito del hackathon: PDF de máximo 2 páginas y 10 MB. El script falla si se pasa de
# cualquiera de los dos, si queda una caja desbordada grande o si el fuente trae rayas largas.
set -euo pipefail
cd "$(dirname "$0")"

MAX_PAGES=2
MAX_BYTES=$((10 * 1024 * 1024))
TECTONIC="${TECTONIC:-$(command -v tectonic || echo /opt/homebrew/bin/tectonic)}"

# Rayas largas: ni el carácter ni tres guiones seguidos.
if grep -n -e "—" -e "---" quorum.tex; then
  echo "ERROR: quorum.tex trae rayas largas (ver líneas de arriba)" >&2
  exit 1
fi

log=$(mktemp)
"$TECTONIC" --keep-logs --print quorum.tex >"$log" 2>&1 || { cat "$log" >&2; echo "ERROR: tectonic falló" >&2; exit 1; }

# Cajas desbordadas de más de 2 pt: se listan y cuentan como error.
if grep -E "Overfull \\\\[hv]box \(([2-9]|[0-9]{2,})(\.[0-9]+)?pt too" quorum.log; then
  echo "ERROR: hay cajas desbordadas (Overfull) de más de 2 pt" >&2
  exit 1
fi
rm -f "$log" quorum.log

pages=$(pdfinfo quorum.pdf | awk '/^Pages:/ {print $2}')
bytes=$(wc -c < quorum.pdf | tr -d ' ')
echo "quorum.pdf -> ${pages} páginas, ${bytes} bytes"
[ "$pages" -le "$MAX_PAGES" ] || { echo "ERROR: la ficha pasa de ${MAX_PAGES} páginas" >&2; exit 1; }
[ "$bytes" -le "$MAX_BYTES" ] || { echo "ERROR: el PDF pasa de 10 MB" >&2; exit 1; }
