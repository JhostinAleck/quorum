# Arquitectura

## Visión general

Quórum es una capa que se ubica entre los agentes y los servicios que comparten. No modifica los modelos ni sus prompts. Tiene dos piezas:

1. **Propagación de etiquetas**: toda llamada de un agente a una herramienta pasa por un monitor que anota de dónde viene cada dato.
2. **Compuerta**: una función pura que decide si una salida al exterior se permite.

![Arquitectura](diagramas/arquitectura.png)

El código está en inglés. Lo que leen los modelos y el jurado (descripciones de herramientas, documentos del caso, esta documentación) está en español. La tabla de equivalencias está en [interfaz](interfaz.md).

## Tres capas

| Capa | Ruta | Qué contiene | De qué depende |
|---|---|---|---|
| Núcleo | `quorum/core/` | Etiquetas, política, compuerta, monitor, almacén y bitácora | Solo de la biblioteca estándar de Python |
| Escenarios | `quorum/scenarios/<dominio>/` | Un `policy.toml`, las herramientas del dominio y el generador de casos | Del núcleo |
| Adaptadores | `quorum/adapters/` | Puentes hacia frameworks de agentes (Inspect AI, function calling genérico) | Del núcleo y del framework |

El núcleo no conoce licitaciones, ni modelos de lenguaje, ni Inspect. Un test (`tests/test_architecture.py`) falla si el núcleo importa algo fuera de la biblioteca estándar o menciona una palabra de algún dominio. Para comprobar que la separación es real hay un segundo escenario, una mesa de ayuda (`quorum/scenarios/helpdesk/`), que usa el mismo núcleo sin cambiarle una línea.

**Cambiar de dominio es escribir un `policy.toml` y unas herramientas.** No se toca la compuerta.

## Etiquetas

Cada valor guardado lleva una etiqueta (`Label`) con dos conjuntos de fuentes:

| Campo | Significado |
|---|---|
| `secrets` | Fuentes restringidas de las que se derivó el dato. Si está vacío, el dato es público |
| `untrusted` | Fuentes escritas por terceros de las que se derivó. Si está vacío, el dato es confiable |

Una fuente es la clave original del dato, por ejemplo `sealed.bid-2`. Las etiquetas se combinan con unión de conjuntos (`join`): nunca se pierde una fuente. La operación es asociativa, conmutativa e idempotente, y eso se verifica con tests de propiedades.

![Propagación de etiquetas](diagramas/etiquetas.png)

## Reglas de propagación

1. **Lectura**: cuando un agente lee un valor, la etiqueta de su contexto pasa a ser la unión de la que tenía y la del valor leído.
2. **Escritura**: todo lo que un agente escribe hereda la etiqueta de su contexto en ese momento.
3. **La etiqueta depende del contexto, no del texto.** Si un agente lee un dato restringido y luego escribe un resumen con otras palabras, el resumen sigue restringido. Esto cierra el "lavado" por paráfrasis, que es la debilidad de las defensas que comparan cadenas.
4. **Entre agentes**: la etiqueta se guarda junto al valor en el almacén compartido. El siguiente agente que lo lea la hereda. La etiqueta no se reinicia al cambiar de agente, ni al delegar en un subagente.

Las herramientas no pueden saltarse estas reglas: nunca tocan el almacén directamente. Reciben un objeto `Call` que es la única puerta al almacén y que anota la etiqueta de todo lo que se lee.

## Referencias opacas y desclasificadores

Si todo el que toca un dato restringido quedara contaminado, el sistema bloquearía casi todo el trabajo legítimo. Para evitarlo, los datos sellados se entregan como **referencias opacas**: el agente recibe un identificador (`bid-2`), no el valor.

- Un agente puede pasar la referencia a otra herramienta sin contaminarse.
- Si un agente necesita ver el valor llama a `open_bid(ref)`. En ese momento su contexto queda restringido.
- Las funciones deterministas declaradas como **desclasificadores** reciben referencias y devuelven resultados públicos: `score_bids(refs)` devuelve puntajes, `within_budget(ref)` devuelve sí o no, `transcribe(doc)` sella una oferta escaneada y devuelve solo la referencia.

Un desclasificador revela algo del dato por diseño, así que está acotado de tres maneras: tiene que estar en la lista de la política y declarar por escrito por qué su resultado es público; no recibe del agente ni umbrales ni fórmulas (los toma del pliego), para que no sirva de oráculo; y tiene un cupo de llamadas por agente.

Esta idea viene de las variables ocultas de FIDES y del modelo en cuarentena de CaMeL (ver [referencias](referencias.md)).

## La política

Es lo único que cambia de un dominio a otro. Son cuatro listas, más los roles:

| Lista | Qué declara | En la licitación |
|---|---|---|
| `restricted` | Prefijos de clave cuyos datos nacen restringidos | `sealed.`, `scan.` |
| `untrusted` | Prefijos de clave que escriben terceros | `annex.` |
| `sinks` | Herramientas que sacan datos del sistema y qué fuentes restringidas admite cada una | `publish` no admite ninguna |
| `declassifiers` | Herramientas autorizadas a devolver un resultado público | `score_bids`, `within_budget`, `transcribe` |

Cada rol declara qué herramientas puede usar y qué prefijos puede leer y escribir. Un campo mal escrito en el archivo detiene el arranque: un error de tipeo no puede debilitar la política en silencio. Tampoco arranca si la política declara un sumidero o un desclasificador que no existe como herramienta, o al revés.

Un sumidero puede admitir fuentes según su destinatario. En la mesa de ayuda, `reply = ["citizen.{citizen}."]` deja salir los datos de una persona solo en la respuesta dirigida a esa misma persona.

## La compuerta

```
evaluate(request, policy) -> Decision(allow, policy, reason)
```

`request` es la llamada a un sumidero: quién llama, con qué rol, a qué herramienta, con qué argumentos y con qué etiqueta de contexto.

| Id | Regla | Motivo |
|---|---|---|
| P1 | Una salida se bloquea si el contexto de quien llama deriva de alguna fuente restringida que ese sumidero no admite y que el usuario no endosó | Confidencialidad en la salida |
| P2 | Modo estricto, opcional: si el contexto deriva de fuentes no confiables, la salida exige una aprobación humana que se obtiene fuera de los agentes. Desactivada en el experimento principal | Integridad: un documento entrante no decide acciones |
| P3 | Toda llamada y toda decisión quedan en una bitácora de solo anexar, encadenada con hashes, que los agentes no pueden escribir | Auditoría |

La compuerta es una función pura: misma entrada, misma salida. Si una regla falla con una excepción, la respuesta es negar. Se pueden agregar reglas propias sin tocar el núcleo. Se prueba con `pytest` y `hypothesis` sin llamar a ningún modelo.

El monitor tiene dos modos. Con `enforce=True` bloquea. Con `enforce=False` solo audita: nada se bloquea, pero la decisión queda en la bitácora. El experimento usa el segundo para obtener los cuatro brazos de una sola corrida, y un test comprueba que ambos modos deciden igual.

## Qué se probó

`uv run pytest` corre 108 tests sin modelos ni costo. Los más importantes:

- **Ningún secreto llega al exterior**: se generan programas al azar de varios agentes que leen, copian y publican, y con la compuerta activa nunca sale un secreto.
- **No interferencia**: se cambia el valor de los secretos y lo que sale del sistema es idéntico.
- **Los tests detectan fallos reales**: si se quita la propagación al leer, la herencia al escribir o la decisión de la compuerta, la batería falla.
- **Los dos escenarios** de punta a punta, con almacén en memoria y con SQLite.

## Por qué no un monitor LLM

Un monitor LLM puntúa sospecha a partir de texto. Tiene tres problemas en este escenario:

- Si ve a un agente a la vez, cada fragmento del ataque parece trabajo normal.
- Si ve todo junto, cuesta más y sigue dependiendo de que reconozca el patrón.
- En ambos casos el texto que lee lo escribe el agente vigilado, que puede intentar convencerlo.

La compuerta decide con etiquetas que los agentes no controlan. Los monitores M1 y M2 se implementan igual, como líneas base, para medir la diferencia.

## Flujo del ataque y de la defensa

![Ataque repartido](diagramas/ataque-repartido.png)

## Componentes del código

| Ruta | Contenido |
|---|---|
| `quorum/core/labels.py` | Etiquetas y operación `join` |
| `quorum/core/policy.py` | Política, roles y reglas P1 y P2 de la compuerta |
| `quorum/core/engine.py` | El monitor: sesiones, permisos, cupos, propagación y registro |
| `quorum/core/tools.py` | Declaración de herramientas y su JSON Schema |
| `quorum/core/store.py` | Almacén etiquetado (memoria y SQLite) |
| `quorum/core/audit_log.py` | Bitácora encadenada con hashes |
| `quorum/core/base.py` | Herramientas genéricas: `read`, `write` y mensajes directos |
| `quorum/adapters/` | Inspect AI y function calling genérico |
| `quorum/scenarios/tender/` | La licitación: política, herramientas, casos y episodios guionados |
| `quorum/scenarios/helpdesk/` | La mesa de ayuda, segundo dominio |
| `quorum/eval/` | Agentes con modelo, ataques, monitores M1 y M2 y tareas de Inspect AI (en construcción) |
| `analysis/` | Bootstrap y figura principal (en construcción) |
