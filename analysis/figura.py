"""Figuras en SVG (sin dependencias) a partir de resultados/.

  fig_principal.svg     detección a 5 % FPR contra fragmentación k (banda IC 95 %) + utilidad honesta por brazo
  fig_generaciones.svg  detección contra generación del atacante L0..L4
  fig_escena.svg        un ataque k=3 que M1 dejó pasar: tres nodos en verde, el dato cruza; al lado, la arista bloqueada

  uv run python -m analysis.figura [resultados]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

INK, GRIS, ROJO, VERDE = "#1f2328", "#9aa0a6", "#c0392b", "#2e8b57"
F = "font-family='Inter,Segoe UI,Arial,sans-serif'"
COLORES = {"dlp_digitos": "#7f8a99", "m1": "#e67e22", "m2": "#8e44ad", "quorum": "#2f6fdf"}
NOMBRES = {"dlp_digitos": "DLP (dígitos)", "m1": "M1 por agente", "m2": "M2 composición", "quorum": "Quórum"}


def _txt(x, y, s, size=12, color=INK, anchor="start", weight="400"):
    return f"<text x='{x}' y='{y}' font-size='{size}' fill='{color}' text-anchor='{anchor}' font-weight='{weight}' {F}>{s}</text>"


def _ejes(L, T, W, H, etiquetas_x, titulo):
    s = [_txt(L, 26, titulo, 16, weight="700")]
    for v in (0, .25, .5, .75, 1):
        y = T + H * (1 - v)
        s.append(f"<line x1='{L}' y1='{y}' x2='{L + W}' y2='{y}' stroke='#eceff1'/>")
        s.append(_txt(L - 8, y + 4, f"{int(v * 100)}%", 11, GRIS, "end"))
    n = len(etiquetas_x)
    for i, e in enumerate(etiquetas_x):
        s.append(_txt(L + i * W / (n - 1), T + H + 20, e, 12, anchor="middle"))
    return s


def _lineas(m, clave, xs, L, T, W, H, bandas=True):
    s = []
    n = len(xs)
    X = lambda i: L + i * W / (n - 1)
    Y = lambda v: T + H * (1 - v)
    for b, c in COLORES.items():
        serie = [m[b][clave][str(x)] for x in xs]
        if bandas:
            arriba = [(X(i), Y(p["ic95"][1])) for i, p in enumerate(serie)]
            abajo = [(X(i), Y(p["ic95"][0])) for i, p in enumerate(serie)][::-1]
            s.append(f"<polygon points='{' '.join(f'{a},{b_}' for a, b_ in arriba + abajo)}' fill='{c}' opacity='0.12'/>")
        pts = [(X(i), Y(p["valor"])) for i, p in enumerate(serie)]
        s.append(f"<polyline fill='none' stroke='{c}' stroke-width='3' points='{' '.join(f'{a},{b_}' for a, b_ in pts)}'/>")
        s += [f"<circle cx='{a}' cy='{b_}' r='4' fill='{c}'/>" for a, b_ in pts]
    return s


def principal(m, meta, out: Path):
    w, h, L, T, W, H = 980, 400, 60, 50, 480, 270
    s = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'><rect width='{w}' height='{h}' fill='white'/>"]
    s += _ejes(L, T, W, H, ["k=1", "k=2", "k=3"], "Detección a 5 % FPR según en cuántos agentes se reparte el ataque")
    s += _lineas(m, "deteccion_por_k", [1, 2, 3], L, T, W, H)
    # utilidad honesta
    bx, bw = 640, 300
    s.append(_txt(bx, T - 8, "Utilidad honesta", 13, weight="700"))
    for i, (b, c) in enumerate(COLORES.items()):
        u = m[b]["utilidad_honesta"]
        y = T + 10 + i * 52
        s.append(_txt(bx, y + 4, NOMBRES[b], 12))
        s.append(f"<rect x='{bx}' y='{y + 10}' width='{bw}' height='14' fill='#f1f3f4'/>")
        s.append(f"<rect x='{bx}' y='{y + 10}' width='{bw * u['valor']:.1f}' height='14' fill='{c}'/>")
        s.append(_txt(bx + bw + 6, y + 22, f"{100 * u['valor']:.0f}%", 12))
    nota = ("⚠ backend heurístico: NO son resultados" if meta["backend"] == "heuristico"
            else f"monitores: {meta['backend']}")
    s.append(_txt(L, h - 14, f"Bandas: IC 95 % bootstrap. Utilidad = honestos publicados y no bloqueados. {nota}", 11, GRIS))
    s.append("</svg>")
    out.write_text("".join(s), encoding="utf-8")


def generaciones(m, meta, out: Path):
    w, h, L, T, W, H = 820, 380, 60, 50, 520, 260
    s = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'><rect width='{w}' height='{h}' fill='white'/>"]
    s += _ejes(L, T, W, H, [f"L{i}" for i in range(5)], "Detección según la generación del atacante")
    s += _lineas(m, "deteccion_por_L", list(range(5)), L, T, W, H, bandas=False)
    for i, (b, c) in enumerate(COLORES.items()):
        s.append(f"<rect x='{L + W + 20}' y='{T + 10 + i * 22}' width='14' height='4' fill='{c}'/>")
        s.append(_txt(L + W + 40, T + 16 + i * 22, NOMBRES[b], 12))
    s.append(_txt(L, h - 14, "L0 literal · L1 formato de pesos · L2 radicado invertido · L3 +persuasión · L4 palabras +persuasión", 11, GRIS))
    s.append("</svg>")
    out.write_text("".join(s), encoding="utf-8")


def _panel(sospechas: dict, bloqueada: bool):
    xs = {"radicador": 170, "evaluador": 320, "publicador": 470}
    y = 90
    s = [f"<rect x='20' y='{y - 25}' width='80' height='50' rx='8' fill='#f6f8fa' stroke='{GRIS}'/>", _txt(60, y + 5, "oferta sellada", 10, anchor="middle")]
    for a, x in xs.items():
        v = sospechas.get(a, 0)
        c = VERDE if v < 5 else ROJO
        s.append(f"<circle cx='{x}' cy='{y}' r='42' fill='white' stroke='{c}' stroke-width='3'/>")
        s.append(_txt(x, y - 2, a, 12, anchor="middle", weight="600"))
        s.append(_txt(x, y + 16, f"sospecha {v:.0f}/10", 11, c, "middle"))
    s.append(f"<rect x='560' y='{y - 25}' width='70' height='50' rx='8' fill='#f6f8fa' stroke='{GRIS}'/>" + _txt(595, y + 5, "portal", 11, anchor="middle"))
    for x1, x2 in ((100, 128), (212, 278), (362, 428)):
        s.append(f"<line x1='{x1}' y1='{y}' x2='{x2}' y2='{y}' stroke='{ROJO}' stroke-width='3'/>")
        s.append(_txt((x1 + x2) / 2, y - 10, "RESTRINGIDO", 9, ROJO, "middle"))
    if bloqueada:
        s.append(f"<line x1='512' y1='{y}' x2='558' y2='{y}' stroke='{GRIS}' stroke-width='3' stroke-dasharray='5 4'/>")
        s.append(f"<g stroke='{ROJO}' stroke-width='4'><line x1='526' y1='{y - 9}' x2='544' y2='{y + 9}'/><line x1='526' y1='{y + 9}' x2='544' y2='{y - 9}'/></g>")
    else:
        s.append(f"<line x1='512' y1='{y}' x2='558' y2='{y}' stroke='{ROJO}' stroke-width='3'/>" + _txt(535, y - 10, "dato", 9, ROJO, "middle"))
    return "".join(s)


def escena(filas, m, out: Path):
    t = m["m1"]["umbral"]
    cands = [f for f in filas if f["tipo"] == "ataque" and f["k"] == 3 and f["fuga_real"]]
    pasadas = [f for f in cands if f["puntajes"]["m1"] < t] or cands
    f = max(pasadas, key=lambda f: (f["L"], -f["puntajes"]["m1"]))
    w, h = 1300, 220
    s = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'><rect width='{w}' height='{h}' fill='white'/>",
         _txt(20, 26, "Monitor por agente: los tres en verde y el dato llega al portal", 15, weight="700"),
         f"<g transform='translate(0,30)'>{_panel(f['m1_por_agente'], False)}</g>",
         _txt(670, 26, "Quórum: la etiqueta viaja con el dato y la última arista se bloquea", 15, weight="700"),
         f"<g transform='translate(650,30)'>{_panel(f['m1_por_agente'], True)}</g>",
         _txt(20, h - 12, f"Episodio {f['eid']} · k=3 · generación L{f['L']} · umbral M1 = {t}", 11, GRIS), "</svg>"]
    out.write_text("".join(s), encoding="utf-8")
    return f["eid"]


def main(carpeta="resultados"):
    r = Path(carpeta)
    datos = json.loads((r / "metricas.json").read_text(encoding="utf-8"))
    filas = [json.loads(l) for l in (r / "puntajes.jsonl").read_text(encoding="utf-8").splitlines()]
    m = datos["metricas"]
    principal(m, datos, r / "fig_principal.svg")
    generaciones(m, datos, r / "fig_generaciones.svg")
    eid = escena(filas, m, r / "fig_escena.svg")
    print(f"figuras en {r}/ (escena: {eid})")


if __name__ == "__main__":
    main(*sys.argv[1:])
