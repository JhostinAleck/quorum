# Arquitectura

## Visión general

Quórum es una capa que se ubica entre los agentes y los servicios que comparten. No modifica los modelos ni sus prompts. Tiene dos piezas:

1. **Propagación de etiquetas**: cada lectura y escritura pasa por un proxy que anota de dónde viene cada dato.
2. **Compuerta**: una función pura que decide si una salida al exterior se permite.

![Arquitectura](diagramas/arquitectura.png)

Todo el laboratorio vive en un solo proceso de Python. Los servicios son objetos en memoria. No hay red.

## Etiquetas

Cada valor almacenado lleva una etiqueta con tres campos:

| Campo | Valores | Significado |
|---|---|---|
| `conf` | `PUBLICO` < `RESTRINGIDO` | Quién puede verlo fuera del sistema |
| `integ` | `CONFIABLE` > `NO_CONFIABLE` | Si su contenido pudo ser escrito por un tercero |
| `fuentes` | conjunto de identificadores | De qué objetos se derivó |

Las etiquetas se combinan con una operación de unión (`join`): la confidencialidad sube al máximo, la integridad baja al mínimo y las fuentes se unen. La operación es asociativa, conmutativa e idempotente, lo que se verifica con tests de propiedades.

![Propagación de etiquetas](diagramas/etiquetas.png)

## Reglas de propagación

1. **Lectura**: cuando un agente lee un valor, la etiqueta de su contexto pasa a ser la unión de la que tenía y la del valor leído.
2. **Escritura**: todo lo que un agente escribe hereda la etiqueta de su contexto en ese momento.
3. **La etiqueta depende del contexto, no del texto.** Si un agente lee un dato restringido y luego escribe un resumen con otras palabras, el resumen sigue restringido. Esto cierra el "lavado" por paráfrasis, que es la debilidad de las defensas que comparan cadenas.
4. **Entre agentes**: la etiqueta se guarda junto al valor en el servicio compartido. El siguiente agente que lo lea la hereda. La etiqueta no se reinicia al cambiar de agente.

## Referencias opacas

Si todo el que toca un dato restringido quedara contaminado, el sistema bloquearía casi todo el trabajo legítimo. Para evitarlo, los datos sellados se entregan como **referencias opacas**: el agente recibe un identificador (`ref:oferta-2`), no el valor.

- Un agente puede pasar la referencia a otra herramienta sin contaminarse.
- Si un agente necesita ver el valor llama a `abrir(ref)`. En ese momento su contexto queda `RESTRINGIDO`.
- Las funciones deterministas declaradas como **desclasificadores** reciben referencias y devuelven resultados públicos. Ejemplos: `calcular_puntajes(refs)` devuelve puntajes, `validar_tope(ref)` devuelve sí o no. La lista de desclasificadores es parte de la política y se revisa por humanos.

Esta idea viene de las variables ocultas de FIDES y del modelo en cuarentena de CaMeL (ver [referencias](referencias.md)).

## La compuerta

```
permitido(llamada, etiqueta_contexto, etiquetas_argumentos, endosos) -> PERMITIR | BLOQUEAR(razón)
```

Políticas iniciales:

| Id | Regla | Motivo |
|---|---|---|
| P1 | `publicar()` se bloquea si el contexto o algún argumento es `RESTRINGIDO` y no hay endoso explícito del usuario para esas fuentes | Confidencialidad en la salida |
| P2 | Modo estricto, opcional: si el contexto es `NO_CONFIABLE`, `publicar()` exige aprobación humana. Desactivada en el experimento principal | Integridad: un documento entrante no decide acciones |
| P3 | Toda decisión queda en una bitácora que los agentes no pueden escribir | Auditoría |

La compuerta es una función pura: misma entrada, misma salida. Se prueba con `pytest` y `hypothesis` sin llamar a ningún modelo.

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
| `quorum/defense/labels.py` | Etiquetas y operación `join` |
| `quorum/defense/gate.py` | Políticas P1 a P3 |
| `quorum/lab/services.py` | Registro, evaluación y portal, con etiquetas por valor |
| `quorum/lab/agents.py` | Los tres roles y sus herramientas |
| `quorum/lab/scenarios.py` | Generador de episodios y canarios |
| `quorum/defense/monitors.py` | Monitores M1 y M2 |
| `quorum/eval/task.py` | Tareas de Inspect AI, una por brazo |
| `quorum/eval/scorers.py` | Fuga, utilidad y sospecha |
| `analysis/` | Bootstrap y figura principal |
