import json, re, sys, pathlib
d = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2])
idx = json.loads((d/'project/deck.json').read_text())
css = (d/'project/deck.css').read_text()
partes, notas = [], []
for sid in idx['order']:
    h = (d/f'project/slides/{sid}.html').read_text()
    m = re.search(r'<aside>(.*?)</aside>', h, re.S)
    notas.append((sid, m.group(1).strip() if m else ''))
    h = re.sub(r'<aside>.*?</aside>', '', h, flags=re.S)
    h = re.sub(r'<x-icon[^>]*></x-icon>', '', h)
    h = re.sub(r'<x-shape kind="arrow-right"[^>]*></x-shape>', '<span class="flechatxt">→</span>', h)
    partes.append(h)
href = idx['faces']['inter']['href']
html = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{idx["title"]}</title>
<link rel="stylesheet" href="{href}"><style>{css}
@page {{ size: 1920px 1080px; margin: 0 }}
html,body {{ margin:0; background:#121417 }}
* {{ box-sizing:border-box }} p,h1,h2,h3 {{ margin:0 }}
section {{ width:1920px; height:1080px; position:relative; overflow:hidden; page-break-after:always; break-after:page }}
.entra {{ animation:none }}
.flechatxt {{ font-size:56px; color:var(--soft); align-self:center }}
.tabla {{ border-collapse:collapse }} .tabla th,.tabla td {{ text-align:left; padding:12px 16px; border-bottom:1px solid #3a414a }}
.tabla th {{ color:var(--soft); font-weight:600 }}
</style></head><body>{"".join(partes)}</body></html>'''
(out/'quorum-pitch.html').write_text(html)
md = ['# Quórum · guion del pitch (3 minutos)', '', 'Notas del orador por diapositiva. Fuente: el deck de Claude Artifacts.', '']
for i,(sid,n) in enumerate(notas,1):
    md += [f'## {i}. {sid}', '', n, '']
(out/'guion.md').write_text('\n'.join(md))
