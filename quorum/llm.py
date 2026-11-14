"""Cliente mínimo de chat (API compatible con OpenAI), sin dependencias.

Variables: OPENROUTER_API_KEY u OPENAI_API_KEY; OPENAI_BASE_URL (por defecto OpenRouter).
El modelo «simulado» no usa red: sirve para probar todo de punta a punta sin costo.
Caché en disco (logs/cache) para que repetir una corrida no vuelva a cobrar.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CACHE = RAIZ / "logs" / "cache"


def llamar(modelo: str, mensajes: list[dict], temperatura: float = 0.0, max_tokens: int = 500, muestra: int = 0) -> str:
    firma = json.dumps([modelo, mensajes, temperatura, max_tokens, muestra], sort_keys=True)
    clave = hashlib.sha256(firma.encode()).hexdigest()
    archivo = CACHE / f"{clave}.json"
    if archivo.exists():
        return json.loads(archivo.read_text())["texto"]
    # Con OPENAI_BASE_URL propio va solo OPENAI_API_KEY: nunca se manda la llave de OpenRouter a otro proveedor.
    if os.environ.get("OPENAI_BASE_URL"):
        base, llave = os.environ["OPENAI_BASE_URL"].rstrip("/"), os.environ.get("OPENAI_API_KEY")
    else:
        base, llave = "https://openrouter.ai/api/v1", os.environ.get("OPENROUTER_API_KEY")
    if not llave:
        raise RuntimeError("falta la llave: OPENROUTER_API_KEY, u OPENAI_API_KEY junto con OPENAI_BASE_URL")
    pedido = {"model": modelo, "messages": mensajes, "max_tokens": max_tokens}
    if not modelo.startswith("claude"):          # los Claude recientes rechazan `temperature` (400)
        pedido["temperature"] = temperatura
    else:                                        # y razonan antes de responder: con 500 tokens la respuesta sale vacía
        pedido["max_tokens"] = max(max_tokens, 4000)
    cuerpo = json.dumps(pedido).encode()
    error = None
    for intento in range(5):
        try:
            # Groq y otros detrás de Cloudflare responden 403 al agente «Python-urllib»: User-Agent propio
            cabeceras = {"Authorization": f"Bearer {llave}", "Content-Type": "application/json",
                         "User-Agent": "quorum-eval/0.1"}
            req = urllib.request.Request(base + "/chat/completions", data=cuerpo, headers=cabeceras)
            with urllib.request.urlopen(req, timeout=120) as r:
                texto = json.loads(r.read())["choices"][0]["message"]["content"] or ""
            CACHE.mkdir(parents=True, exist_ok=True)
            archivo.write_text(json.dumps({"modelo": modelo, "texto": texto}, ensure_ascii=False))
            return texto
        except (urllib.error.URLError, KeyError, IndexError, TimeoutError, json.JSONDecodeError) as e:
            error = e
            espera = 2 ** intento
            if isinstance(e, urllib.error.HTTPError) and e.code == 429:   # límite de ritmo: esperar lo que pida
                try:
                    espera = max(espera, float(e.headers.get("retry-after") or 0) + 1, 10.0)
                except ValueError:
                    espera = max(espera, 10.0)
            time.sleep(min(espera, 90))
    raise RuntimeError(f"el modelo {modelo} no respondió tras 5 intentos: {error}")
