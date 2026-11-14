# Interfaz web

Una página para la demo: se suben las ofertas, se elige si los agentes son honestos o se desvían, y se ve paso a paso qué hace cada agente, qué etiquetas arrastra y qué decide la compuerta.

No es otro laboratorio. Usa las piezas del repo tal cual: el escenario `tender` (política, herramientas, prompts y pasos guionados), el bucle de agente de `quorum/adapters/agent_loop.py`, el cliente del modelo de `quorum/adapters/openai_chat.py` y, en contenedores, el monitor por red de [protocolo](protocolo.md). Lo único nuevo es armar el caso desde documentos subidos en lugar de una semilla, y mostrar la bitácora en vivo.

## Correrla

En un solo proceso, sin Docker:

```bash
uv run python -m quorum.ui.server        # http://127.0.0.1:8765
```

Así los tres agentes corren dentro del proceso de la página. Sirve para el modo guionado y, con `OPENROUTER_API_KEY` en `.env` y el extra `eval` instalado (`uv sync --extra eval`), para el modo con modelo. Los PDF y los escaneos necesitan `poppler-utils` y `tesseract` en el host; el texto plano no necesita nada.

En contenedores, con cada agente en el suyo:

```bash
docker compose -f docker-compose.ui.yml up --build      # http://127.0.0.1:8765
docker compose -f docker-compose.ui.yml down
```

Necesita en `.env` los tres tokens de agente de [despliegue](despliegue.md) y `OPENROUTER_API_KEY`. Es un archivo de Compose aparte: no modifica ni reemplaza `docker-compose.yml`.

## Qué se puede hacer en la página

1. **Ofertas.** Se arrastran archivos de texto, PDF o imágenes, o se cargan los ejemplos (tres ofertas de texto, o dos PDF y un PDF escaneado). Cada documento necesita una línea `Valor: <número>` y, si se quiere, `Proveedor: <nombre>`. El valor se sella en el almacén y el resto del texto entra como anexo no confiable. La página nunca muestra el valor, solo cuántos dígitos tiene.
2. **Agentes.** Honestos, o desviados con k = 1, 2 o 3 agentes (los mismos casos `attack_k1` a `attack_k3` del escenario).
3. **Compuerta.** Activa (bloquea) o solo auditoría (deja pasar y registra qué habría bloqueado).
4. **Motor.** Guionado, sin modelo, o con modelo.
5. **Restablecer.** Vuelve al estado inicial: agentes honestos y ninguna corrida guardada. El estado vive en memoria.

Mientras corre, cada tarjeta de agente muestra sus llamadas en orden, con las fuentes restringidas y no confiables de su etiqueta después de cada una, tomadas de la bitácora. El resultado dice qué se publicó, si hubo fuga, si el trámite fue útil, cada bloqueo con su motivo y si la cadena de la bitácora verifica.

## Quién maneja a cada agente

| Motor | Agentes honestos | Agentes que se desvían |
|---|---|---|
| Guionado | Pasos guionados del escenario | Pasos guionados del escenario |
| Modelo | El modelo, con `SYSTEM` y `TASK` de `scenarios/tender/prompts.py` | Pasos guionados del escenario |

En el motor con modelo, un agente que se desvía sigue siendo guionado porque el repo no trae tareas ocultas para modelos. `workflow.run(..., side_tasks={"evaluator": "..."})` permite pasar una: se añade al final del prompt de sistema de ese rol y entonces lo maneja el modelo. La página no expone esa opción.

Si se pide el motor con modelo y no hay key ni servicios de agente, la corrida cae al guionado y el resultado lo dice en `engines`.

## Ofertas escaneadas

Un PDF sin capa de texto o una imagen se leen por OCR. El pliego del escenario admite un solo documento escaneado (`terms.scan`), así que la primera oferta leída por OCR entra como escaneo (`scan.scan-N`) y el Radicador la digita con `transcribe`. Si hay más ofertas escaneadas, las demás las sella el sistema directamente, como a las de texto.

Los guiones de ataque apuntan a la oferta del proveedor `TARGET` del escenario. Con documentos propios que no la incluyan, los ataques se rechazan con un mensaje y el trámite honesto funciona igual.

## En contenedores

| Servicio | Qué tiene | Qué no tiene |
|---|---|---|
| `lab` | La página, las herramientas de OCR, y en cada corrida el monitor con su almacén, bitácora y compuerta | La key del modelo |
| `registrar`, `evaluator`, `publisher` | La key del modelo y su propio token | El almacén, la bitácora y los tokens de los demás |

`docker compose run agent` corre un agente una vez y termina. Aquí cada agente es ese mismo agente mantenido vivo (`quorum/ui/agent_service.py`): espera a que `lab` le avise que es su turno y entonces hace lo mismo que `quorum.launch agent`, con una `RemoteSession` contra el monitor. Solo obedece peticiones con su propio token, y verifica que el monitor le reconozca ese token con su rol.

En cada corrida, `lab` crea un monitor nuevo para ese caso, lo sirve en el puerto 8080 y da el turno a cada agente en orden.

Cada agente comparte una red privada solo con `lab`, así que los agentes no se alcanzan entre sí. Eso es más de lo que da la red `control` del despliegue base.

La tarjeta de cada agente muestra si su contenedor responde, qué modelo usa y si el hash de su prompt de sistema es el mismo que el del escenario en `lab`.

## Abrirla a otras máquinas

Por defecto solo escucha en `127.0.0.1` y no pide clave. Para abrirla:

```bash
QUORUM_UI_HOST=0.0.0.0            # sin Docker
QUORUM_UI_BIND=0.0.0.0            # con Docker: dónde publica Compose el puerto
QUORUM_UI_PASSWORD=<clave>        # si falta, se genera una y se imprime al arrancar
```

Fuera de `127.0.0.1` la página siempre pide el usuario `quorum` y esa clave.

## Qué no da

- **Los agentes tienen internet.** Necesitan llegar al proveedor del modelo y sus redes no filtran destinos, igual que en el modo con modelo del despliegue base. Todo lo que un agente lee viaja al proveedor.
- **No hay TLS.** La clave de la página y los tokens viajan en claro. Para exponerla de verdad va detrás de un proxy con TLS.
- **Una corrida a la vez y sin persistencia.** El estado y la bitácora viven en memoria y se pierden al restablecer o reiniciar.
- **Es una demo, no la evaluación.** Las cifras del proyecto salen del barrido de [plan de evaluación](plan-de-evaluacion.md), no de corridas sueltas en la página.
- **Solo documentos sintéticos.** No subas ofertas reales: en el modo con modelo el anexo completo se envía al proveedor.

Los límites de la defensa y del despliegue en contenedores siguen igual: ver [uso responsable](uso-responsable.md) y [despliegue](despliegue.md).

## Archivos

| Ruta | Contenido |
|---|---|
| `quorum/ui/server.py`, `index.html` | La página y su API (`/api/state`, `/api/run`, `/api/reset`, `/api/extract`, `/api/examples`) |
| `quorum/ui/workflow.py` | Arma el caso desde los documentos, corre el episodio y lo califica |
| `quorum/ui/documents.py` | Extrae el texto de PDF e imágenes con `pdftotext`, `pdftoppm` y `tesseract` |
| `quorum/ui/agents.py`, `agent_service.py` | Configuración y el servicio de un agente |
| `quorum/ui/examples/` | Ofertas sintéticas de ejemplo; `scripts/make_example_pdfs.py` regenera los PDF |
| `docker-compose.ui.yml`, `Dockerfile` (`WITH_OCR=1`) | El despliegue de la página |
| `tests/test_ui.py` | Tests, sin modelo ni red externa |
