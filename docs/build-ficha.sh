#!/usr/bin/env bash
# Compila la ficha de dos páginas (docs/ficha-tecnica.md -> docs/ficha-tecnica.pdf).
# Carta, márgenes 1,5 cm, cuerpo 9,5 pt, interlineado de párrafo corto: el texto entra justo en dos páginas.
# Si se agrega texto, el PDF sale de tres: recortar antes de subir el tamaño de letra.
set -euo pipefail
cd "$(dirname "$0")/.."

header=$(mktemp -d)/header.tex
cat > "$header" <<'TEX'
\usepackage[fontsize=9.5pt]{scrextend}
\usepackage{enumitem}
\setlist[itemize]{topsep=1pt,itemsep=0pt,parsep=0pt,leftmargin=1.2em}
\usepackage{titlesec}
\titlespacing*{\section}{0pt}{6pt}{3pt}
TEX

pandoc docs/ficha-tecnica.md -o docs/ficha-tecnica.pdf \
  --pdf-engine=tectonic \
  -V geometry:margin=1.45cm \
  -V papersize=letter \
  -V colorlinks=true \
  -V parskip=3pt \
  -H "$header"

pages=$(pdfinfo docs/ficha-tecnica.pdf | awk '/^Pages:/ {print $2}')
echo "docs/ficha-tecnica.pdf -> ${pages} páginas"
[ "$pages" -le 2 ] || { echo "ERROR: la ficha pasa de dos páginas" >&2; exit 1; }
