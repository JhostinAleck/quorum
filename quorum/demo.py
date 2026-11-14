"""Demo en vivo: un episodio paso a paso, con la etiqueta de cada agente y la decisión de la compuerta.

  uv run python -m quorum.demo ataque 3 4    # ataque repartido k=3, generación L4
  uv run python -m quorum.demo honesto
  uv run python -m quorum.demo escaneada     # el costo conocido: bloqueo de más
"""
from __future__ import annotations

import sys

from .lab.scenarios import correr


def main():
    tipo = sys.argv[1] if len(sys.argv) > 1 else "ataque"
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    L = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    tipo = {"escaneada": "honesto_escaneada"}.get(tipo, tipo)
    e = correr(tipo, semilla=7, k=k if tipo == "ataque" else None, L=L if tipo == "ataque" else None,
               gemelo=1.0)
    print(f"\n=== {tipo}" + (f" · k={k} · L{L}" if tipo == "ataque" else "") + " ===")
    print(f"valor sellado de Ferrelectro (canario): {e.canario}\n")
    for agente, pasos in e.trayectorias.items():
        print(f"── {agente}")
        for p in pasos:
            args = {a: v for a, v in p.items() if a not in ("herramienta", "resultado", "permitido", "politica", "razon", "salio")}
            res = f"  → {str(p['resultado'])[:90]}" if p.get("resultado") is not None else ""
            mark = " 🔴" if p["herramienta"] == "abrir" else ""
            print(f"   {p['herramienta']}({', '.join(f'{a}={str(v)[:110]!s}' for a, v in args.items())}){res}{mark}")
    print("\n── portal (sin defensa)")
    for t in e.portal:
        print("   " + t)
    print(f"\n¿el dato es recuperable de lo publicado? {'SÍ' if e.fuga_real else 'no'}"
          f"   ·   ¿aparece literal? {'sí' if e.fuga_literal else 'NO'}")
    print(f"Quórum: {'BLOQUEA ⛔  ' + e.compuerta_razon if e.compuerta_bloquea else 'permite ✅'}\n")


if __name__ == "__main__":
    main()
