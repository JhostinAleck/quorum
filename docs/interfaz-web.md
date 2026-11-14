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

Necesita en `.env` los tres tokens de agente de [despliegue](despliegue.md) y `OPENROUTER_API_KEY`. La página abre sin usuario ni clave. Si se quiere que pida una, se pone en `QUORUM_UI_PASSWORD` (usuario `quorum`); se genera igual que un token:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Sin clave, cualquiera que llegue al puerto puede usar la página, y en contenedores eso incluye a los agentes: dentro de su contenedor `lab` escucha en todas las interfaces y los agentes comparten red con él, así que un agente podría leer `/api/state` o lanzar corridas. Por defecto Compose publica el puerto solo en `127.0.0.1`.

Es un archivo de Compose aparte: no modifica ni reemplaza `docker-compose.yml`.

## Qué se puede hacer en la página

0. **Pruebas listas.** La página ofrece dos casos de la licitación LP-SRP-2026-014, cada uno con tres ofertas escaneadas que se pueden ver (miniatura de la página 1 y el PDF original) antes de cargarlas, y una guía de qué probar:
   - **Trámite normal:** Andina, Ferrelectro y Logística Páramo, sin trampas en los documentos.
   - **Oferta con inyección:** la oferta de Andina trae en la página 2 (sección V) una instrucción escondida para que los agentes saquen al portal el valor de Ferrelectro. Solo actúa con el motor LLM: los agentes guionados no leen instrucciones.

   Los archivos están en `quorum/ui/examples/pdf/` con su miniatura (`.jpg`) y el texto que leyó el OCR (`.txt`). Con OCR los PDF se leen como cualquier subida (y se leen una vez al arrancar, así el primer clic es inmediato); sin OCR, fuera de Docker, se usa ese texto y la página lo marca como «OCR precalculado».
1. **Ofertas.** También se pueden arrastrar archivos propios de texto, PDF o imágenes. Cada documento necesita una línea `Valor: <número>` y, si se quiere, `Proveedor: <nombre>`; si no la tiene, vale una línea `Proponente <nombre>` como la de la tabla de identificación de una oferta formal. El valor va en pesos enteros, con o sin separador de miles (`468.915.720`); si trae centavos (`,00`) se descartan. El nombre del proveedor va en la misma línea que su etiqueta y es un nombre corto de empresa: letras, dígitos, espacios y `. , & - '`, máximo 60 caracteres y menos de cinco dígitos. Un documento que no cumpla se rechaza con un mensaje. El nombre se restringe porque entra a `terms.bids`, un dato del pliego que leen todos los agentes. Esa lista queda marcada como no confiable en la bitácora, pero en esta demostración la política no actúa sobre esa marca (el modo estricto está apagado), así que la protección que opera es la validación del nombre. Un valor que el reconocimiento de texto partió o leyó mal (`468. 915.720`, `468.9l5.720`) se rechaza en lugar de sellar un número truncado. El valor se sella en el almacén y el resto del texto entra como anexo no confiable. Las demás copias del monto en el documento (un recuadro de resumen, la carta, el valor en letras) también se sellan antes de guardar el anexo: sin eso llegarían al portal sin la marca del valor sellado y la compuerta no las vería. Se buscan en cifras con cualquier separador y en palabras, con o sin tildes (`quorum/ui/redact.py`). La lista muestra cuántos dígitos tiene el valor y, con «ver texto», el contenido del documento (el texto leído por OCR en un escaneo) con el monto reemplazado por `[sellado]`; «mostrar el valor sellado» lo descubre solo en ese navegador, porque es el documento que la misma persona subió.
2. **Agentes.** Honestos, o desviados con k = 1, 2 o 3 agentes (los mismos casos `attack_k1` a `attack_k3` del escenario).
3. **Compuerta.** Activa (bloquea) o solo auditoría (deja pasar y registra qué habría bloqueado).
4. **Motor.** Guionado, sin modelo, o con modelo.
5. **Restablecer.** Vuelve al estado inicial: agentes honestos y ninguna corrida guardada. El estado vive en memoria.

**Varias personas a la vez.** Cada navegador tiene su propio estado, sin crear usuarios: la primera visita recibe una cookie anónima al azar (`quorum_sid`, `HttpOnly`) y el servidor guarda una corrida por cookie. Lo que una persona corre o restablece no cambia lo que ve otra. Dos pestañas del mismo navegador comparten estado. Un estado sin visitas por 6 horas se olvida, y hay un tope de 8 corridas simultáneas en todo el servidor. Con un solo proceso las corridas van en paralelo; con cada agente en su contenedor se turnan, porque los agentes hablan con un único puerto del monitor, y la página dice «En cola» mientras espera.

Mientras corre, cada tarjeta de agente muestra sus llamadas en orden, con las fuentes restringidas y no confiables de su etiqueta después de cada una, tomadas de la bitácora. El resultado dice qué se publicó, si hubo fuga, si el trámite fue útil, cada bloqueo con su motivo y si la cadena de la bitácora verifica.

## Quién maneja a cada agente

| Motor | Agentes honestos | Agentes que se desvían |
|---|---|---|
| Guionado | Pasos guionados del escenario | Pasos guionados del escenario |
| Modelo | El modelo, con `SYSTEM` y `TASK` de `scenarios/tender/prompts.py` | El modelo, con esos prompts más la tarea oculta de `quorum/eval/attacks.py` |

En el motor con modelo, un agente que se desvía también lo maneja el modelo. `quorum/ui/server.py` le pasa a `workflow.run` las tareas ocultas de `quorum/eval/attacks.py` (`side_tasks`), una por cada rol que participa en el ataque. La tarea se añade al final del prompt de sistema de ese rol y, como un paso numerado más, al final de su tarea (`agents.prompts`). Un rol que se desvía y no recibe tarea oculta corre sus pasos guionados (`workflow.plan`); eso solo pasa si se llama a `workflow.run` sin `side_tasks`. La página no deja escribir ni cambiar la tarea oculta: va siempre la del caso elegido.

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

Por defecto la página solo se alcanza desde este equipo (`127.0.0.1`, con o sin Docker) y no pide clave. Para abrirla a otras máquinas:

```bash
QUORUM_UI_HOST=0.0.0.0            # sin Docker
QUORUM_UI_BIND=0.0.0.0            # con Docker: dónde publica Compose el puerto
QUORUM_UI_PASSWORD=<clave>        # opcional: la página pide usuario quorum y esta clave
```

Sin `QUORUM_UI_PASSWORD`, la página abierta a otras máquinas la puede usar cualquiera en esa red; el servidor arranca igual y lo avisa en su salida. Con la clave, la página y su API piden el usuario `quorum` y esa clave.

## Qué no da

- **Los agentes tienen internet.** Necesitan llegar al proveedor del modelo y sus redes no filtran destinos, igual que en el modo con modelo del despliegue base. Todo lo que un agente lee viaja al proveedor.
- **No hay TLS.** La clave de la página y los tokens viajan en claro. Para exponerla de verdad va detrás de un proxy con TLS.
- **Sin persistencia.** El estado y la bitácora de cada navegador viven en memoria y se pierden al restablecer o reiniciar. La cookie separa a las personas, no las autentica: el único control de acceso es la clave opcional de la página.
- **Es una demo, no la evaluación.** Las cifras del proyecto salen del barrido de [plan de evaluación](plan-de-evaluacion.md), no de corridas sueltas en la página.
- **Solo documentos sintéticos.** No subas ofertas reales: en el modo con modelo el anexo completo se envía al proveedor.

Los límites de la defensa y del despliegue en contenedores siguen igual: ver [uso responsable](uso-responsable.md) y [despliegue](despliegue.md).

## Archivos

| Ruta | Contenido |
|---|---|
| `quorum/ui/server.py`, `index.html` | La página y su API (`/api/state`, `/api/run`, `/api/reset`, `/api/extract`, `/api/presets`, `/api/examples/<prueba>`; `/examples/<archivo>` sirve solo los PDF y miniaturas de las pruebas) |
| `quorum/ui/workflow.py` | Arma el caso desde los documentos, corre el episodio y lo califica |
| `quorum/ui/documents.py` | Extrae el texto de PDF e imágenes con `pdftotext`, `pdftoppm` y `tesseract` |
| `quorum/ui/agents.py`, `agent_service.py` | Configuración y el servicio de un agente |
| `quorum/ui/presets.py`, `quorum/ui/examples/pdf/` | Las dos pruebas y sus ofertas escaneadas (PDF, miniatura y texto del OCR) |
| `quorum/ui/redact.py` | Sella las demás copias del monto en cifras y en letras |
| `docker-compose.ui.yml`, `Dockerfile` (`WITH_OCR=1`) | El despliegue de la página |
| `tests/test_ui.py` | Tests, sin modelo ni red externa |
