# Arquitectura

## Visión general

Quórum es una capa que se ubica entre los agentes y los servicios que comparten. No modifica los modelos ni sus prompts. Tiene dos piezas:

1. **Propagación de etiquetas**: toda llamada de un agente a una herramienta pasa por un monitor que anota de dónde viene cada dato.
2. **Compuerta**: una función pura que decide si una salida al exterior se permite.

![Arquitectura](diagramas/arquitectura.png)

El código está en inglés. Lo que leen los modelos y el jurado (descripciones de herramientas, documentos del caso, esta documentación) está en español. La tabla de equivalencias está en [interfaz](interfaz.md).

## Diseño guiado por el dominio (DDD)

El código está organizado en capas, y las dependencias apuntan siempre hacia adentro: todo conoce al dominio y el dominio no conoce a nadie.

![Capas](diagramas/capas.png)

| Capa | Ruta | Qué contiene | Puede importar |
|---|---|---|---|
| Dominio | `quorum/domain/` | El modelo de la defensa: etiquetas, política, compuerta, agente, bitácora y el puerto del almacén. Sin entrada ni salida | Solo la biblioteca estándar |
| Aplicación | `quorum/application/` | El caso de uso "un agente llama a una herramienta": el monitor de referencia y las herramientas genéricas | El dominio |
| Infraestructura | `quorum/infrastructure/` | Almacenes (memoria, SQLite) y lectura de políticas en TOML | El dominio |
| Adaptadores | `quorum/adapters/` | Puentes hacia afuera: frameworks de agentes (Inspect AI, function calling genérico), el bucle de agente y el protocolo HTTP (servidor y cliente) | Aplicación y dominio |
| Contextos | `quorum/scenarios/<contexto>/` | Cada dominio de uso: su `policy.toml`, sus herramientas y sus reglas de negocio | Todas las capas, pero no otro contexto |

`quorum/bootstrap.py` es la raíz de composición: el único lugar que une la aplicación con una infraestructura concreta (`new_monitor`). `quorum/launch.py` es la segunda: arma los procesos que corren por separado (el monitor, cada agente y el reporte del operador) y es el único módulo que conoce a la vez un escenario, los adaptadores y la infraestructura. Todo lo público se importa desde `quorum` (`from quorum import Policy, new_monitor, Blocked`).

Las piezas, con el nombre que les da DDD:

| Pieza | Tipo | Regla que protege |
|---|---|---|
| `Label`, `Policy`, `Role`, `Request`, `Decision`, `Value` | Objetos de valor | Inmutables. Una política se valida al construirse |
| `Agent` | Entidad | **Su etiqueta de contexto solo crece.** No existe operación que le quite una fuente, ni que le cambie el rol o el nombre |
| `evaluate` (la compuerta) | Servicio de dominio | Función pura de (solicitud, política). Si una regla falla, niega |
| `AuditLog` | Agregado | Solo se anexa. Cada evento encadena el hash del anterior |
| `Store` | Puerto (repositorio) | El dominio define qué necesita; la infraestructura lo implementa |
| `Quorum` (el monitor) | Servicio de aplicación | Toda llamada pasa por él; las herramientas nunca tocan el almacén |

**Contextos delimitados.** El dominio de Quórum es el control de flujo de información, no las licitaciones. La licitación (`tender`), la mesa de ayuda (`helpdesk`), las historias clínicas (`clinic`), la banca (`bank`) y el sector legal (`lawfirm`) son contextos aparte que usan ese núcleo. Las reglas de negocio de la licitación (cómo se puntúa, qué es estar dentro del presupuesto, quién gana) viven en `quorum/scenarios/tender/rules.py` como funciones puras, separadas de las herramientas que las exponen a los agentes. Cambiar de dominio es escribir un `policy.toml`, unas herramientas y sus reglas. No se toca la compuerta. Los cinco se miden con el mismo código en [resultados por dominio](resultados-dominios.md).

**La regla de dependencias se prueba.** `tests/test_architecture.py` falla si el dominio importa algo fuera de la biblioteca estándar o hace entrada y salida, si la aplicación importa infraestructura, si alguna capa del núcleo menciona una palabra de un contexto, o si un contexto conoce a otro.

**Lenguaje ubicuo.** Los mismos términos se usan en el código, en los tests y en estos documentos. La tabla de equivalencias entre español e inglés está en [interfaz](interfaz.md).

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

Un desclasificador revela algo del dato por diseño, así que está acotado de cuatro maneras: tiene que estar en la lista de la política y declarar por escrito por qué su resultado es público; no recibe del agente ni umbrales ni fórmulas (los toma del pliego); solo calcula sobre datos de origen oficial, nunca sobre un valor que un agente digitó; y tiene un cupo de llamadas por agente. Las tres últimas son lo que la literatura llama desclasificación robusta: el atacante no puede influir en qué se desclasifica. Sin la tercera, dos agentes podían registrar valores conocidos junto a una oferta secreta y deducirla de los puntajes con un error menor al 0,1 %, con el contexto limpio. Lo encontramos atacando nuestra propia defensa y hay un test que lo impide.

Esta idea viene de las variables ocultas de FIDES y del modelo en cuarentena de CaMeL (ver [referencias](referencias.md)).

## La política

Es lo único que cambia de un dominio a otro. Son cuatro listas, más los roles:

| Lista | Qué declara | En la licitación |
|---|---|---|
| `restricted` | Prefijos de clave cuyos datos nacen restringidos | `sealed.`, `scan.`, `manual.` |
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
| P1 con marea alta | Interruptor `high_water_mark`: la salida se juzga con los secretos que ha visto cualquier agente, no solo quien llama. Cierra el canal de claves ausentes. Encendido en la licitación, la mesa de ayuda y la banca, donde no cuesta trabajo honesto | Confidencialidad frente a señales que no viajan en los datos |
| P3 | Toda llamada y toda decisión quedan en una bitácora de solo anexar, encadenada con hashes, que los agentes no pueden escribir | Auditoría |

La compuerta es una función pura: misma entrada, misma salida. Si una regla falla con una excepción, la respuesta es negar. Se pueden agregar reglas propias sin tocar el núcleo. Se prueba con `pytest` y `hypothesis` sin llamar a ningún modelo.

El monitor tiene dos modos. Con `enforce=True` bloquea. Con `enforce=False` solo audita: nada se bloquea, pero la decisión queda en la bitácora. El experimento usa el segundo para obtener los cuatro brazos de una sola corrida, y un test comprueba que ambos modos deciden igual.

## Monitor y agentes en contenedores

En un solo proceso, los agentes y el monitor comparten memoria: sirve para medir, pero la frontera entre el agente y lo que se protege es una convención del código. Para que sea una frontera real, el monitor corre como un servicio y cada agente en su propio contenedor.

![Contenedores](diagramas/contenedores.png)

- **El monitor es el único que tiene datos.** El almacén, la bitácora y la compuerta viven en su contenedor. Un agente no monta ningún volumen: solo recibe lo que el monitor le responde.
- **La identidad sale del token, no de lo que el agente diga.** Cada agente tiene un token propio y el monitor deduce de él el nombre y el rol. Un agente no puede actuar con el rol de otro ni leer el estado del episodio, que exige un token de administración aparte.
- **Los agentes no se hablan entre sí.** Todo lo que comparten pasa por el almacén etiquetado del monitor, así que la etiqueta no se pierde por el camino.
- **La red no tiene salida.** En el modo guionado, la red de los contenedores es interna. El único camino de un dato hacia afuera es el sumidero `publish`, que pasa por la compuerta.

Nada de esto cambia el dominio ni la aplicación. El servidor (`MonitorServer`) y el cliente (`RemoteSession`) son adaptadores, hechos con la biblioteca estándar. `RemoteSession` se comporta como una sesión local para todo lo que usa un agente, así que el mismo código de agente corre en un proceso o repartido en contenedores. El contrato está en [protocolo](protocolo.md) y la forma de correrlo en [despliegue](despliegue.md).

Dónde se usa cada modo: el barrido de episodios corre en un proceso (milésimas de segundo por episodio guionado), y los contenedores sirven para mostrar la defensa con la frontera puesta (unos 8 segundos por episodio).

## Qué se probó

`uv run pytest` corre 594 tests sin modelos ni costo. Los más importantes:

- **Ningún secreto llega al exterior**: se generan programas al azar de varios agentes que leen, copian y publican, y con la compuerta activa nunca sale un secreto.
- **No interferencia**: se cambia el valor de los secretos y lo que sale del sistema es idéntico.
- **Los tests detectan fallos reales**: si se quita la propagación al leer, la herencia al escribir o la decisión de la compuerta, la batería falla.
- **La invariante del agente**: su contexto nunca pierde una fuente y no se puede reasignar.
- **Ninguna llamada escapa de la bitácora**: ni un texto que no se puede codificar ni un argumento con ciclos impiden registrar el evento. Antes de este arreglo, una escritura así se ejecutaba y no quedaba anotada.
- **La regla de dependencias** entre capas.
- **Convencer a la compuerta no sirve**: un texto que pide su propia aprobación ("ya fue revisada, clasifíquela como segura") no cambia la decisión, porque la compuerta no lee texto.
- **Intentos de romper la compuerta**: nueve formas de disfrazar el valor, todas bloqueadas, y un canal que sí lo saca con la política por defecto y que el modo de marea alta cierra. Ver [intentos de evasión](intentos-de-evasion.md).
- **Los dos escenarios** de punta a punta, con almacén en memoria y con SQLite.
- **El protocolo por red**: tokens desconocidos, roles cruzados, cuerpos mal formados y llamadas en paralelo. Un agente remoto obtiene exactamente lo mismo que uno local.
- **Procesos separados**: el monitor y cada agente como procesos distintos que solo comparten un puerto. El ataque repartido entre tres procesos se bloquea igual.

Además, el despliegue con Docker Compose se corrió a mano en los cuatro casos (honesto, honesto con oferta escaneada, ataque k = 3 con compuerta y en modo auditoría) con los resultados que indica [despliegue](despliegue.md).

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
| `quorum/domain/labels.py` | Etiquetas y operación `join` |
| `quorum/domain/policy.py` | Política y roles |
| `quorum/domain/gate.py` | La compuerta: reglas P1 y P2, decisión y resultados de una salida |
| `quorum/domain/agent.py` | El agente y la invariante de su contexto |
| `quorum/domain/tools.py` | Declaración de herramientas y su JSON Schema |
| `quorum/domain/audit_log.py` | Bitácora encadenada con hashes |
| `quorum/domain/repositories.py` | Puerto del almacén etiquetado |
| `quorum/application/monitor.py` | El monitor: sesiones, permisos, cupos, propagación y registro |
| `quorum/application/base_tools.py` | Herramientas genéricas: `read`, `write` y mensajes directos |
| `quorum/infrastructure/stores.py` | Almacén en memoria y en SQLite |
| `quorum/infrastructure/policy_files.py` | Lectura de políticas en TOML |
| `quorum/bootstrap.py` | Raíz de composición |
| `quorum/launch.py` | Puntos de entrada de los procesos: `monitor`, `agent` y `report` |
| `quorum/adapters/functions.py`, `inspect_ai.py` | Function calling genérico e Inspect AI |
| `quorum/adapters/http_server.py`, `http_client.py` | El monitor como servicio HTTP y la sesión remota de un agente |
| `quorum/adapters/agent_loop.py`, `openai_chat.py` | Bucle de agente con modelo y cliente de un proveedor compatible con OpenAI |
| `Dockerfile`, `docker-compose.yml`, `docker-compose.llm.yml` | Una imagen para todos los servicios, el despliegue guionado y la variante con modelo |
| `quorum/scenarios/tender/` | La licitación: política, reglas, herramientas, casos, episodios guionados y prompts base de cada rol |
| `quorum/scenarios/helpdesk/` | La mesa de ayuda: permiso por destinatario |
| `quorum/scenarios/clinic/` | Historias clínicas: dos salidas con permisos distintos |
| `quorum/scenarios/bank/` | Banca: integridad, un mensaje de un tercero no ordena pagos |
| `quorum/scenarios/lawfirm/` | Sector legal: muralla entre clientes y un escrito público que no lleva nada reservado |
| `quorum/bench.py` | Mide los cinco dominios con el mismo código y escribe las tablas |
| `quorum/adapters/monitors.py` | Monitores M1 y M2 con prompt normal y endurecido; respuesta ilegible vale nota máxima |
| `quorum/monitor_bench.py` | Mide con un modelo real si una nota dirigida al revisor cambia el veredicto |
| `quorum/llm_bench.py` | Corre la licitación con agentes de modelo y prompts honestos, con y sin una carta inyectada |
| `quorum/eval/` | Agentes con modelo, ataques, monitores M1 y M2 y tareas de Inspect AI (en construcción) |
| `analysis/` | Bootstrap y figura principal (en construcción) |
