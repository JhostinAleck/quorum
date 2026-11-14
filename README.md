# Quórum

**Una compuerta determinista de procedencia que detiene fugas de datos repartidas entre varios agentes de IA, aunque cada agente por separado parezca inocente.**

Proyecto del Defensive Acceleration Hackathon (AI Safety Colombia x IEEE CS Uniandes, 14 de noviembre de 2026). Track 6: riesgos multiagente, con cruce a control de IA y seguridad de agentes.

> Estado: en construcción durante el sprint. Los resultados se agregan a `docs/resultados.md` cuando existan. Nada en este repo afirma un número que no salga de los logs.

## La idea: juntar dos líneas que estaban separadas

| Línea de trabajo | Qué mostró | Qué dejó sin probar |
|---|---|---|
| **Control de IA multiagente** (Makins et al., UK AISI, 2026, arXiv:2607.07368) | Si un ataque se reparte entre varios agentes, cada paso se ve menos sospechoso y los monitores por agente lo detectan menos | Solo evalúa monitores LLM. No prueba defensas de flujo de información |
| **Control de flujo de información para agentes** (FIDES, CaMeL, SafeFlow) | Etiquetar los datos y decidir con reglas deterministas frena fugas causadas por contenido malicioso | Asume que el agente es honesto y el contenido es el atacante. No se compara con monitores ni contra agentes que coluden |

**Quórum junta las dos:** toma el ataque repartido de la primera línea y lo enfrenta, en los mismos episodios, a los monitores de esa línea y a una compuerta determinista de procedencia de la segunda, bajo el supuesto más duro: los propios agentes son los atacantes.

La pregunta que respondemos con datos:

> Cuando el ataque se reparte entre más agentes, la detección de los monitores cae. ¿Cae también la de una compuerta de procedencia? ¿Y cuánto trabajo legítimo cuesta?

## La defensa

Cada dato lleva una etiqueta con su origen y su nivel de confidencialidad. La etiqueta viaja con el dato entre agentes a través de los servicios compartidos, y lo que un agente escribe hereda las etiquetas de todo lo que leyó. Antes de cualquier salida al exterior, una función pura (sin modelo de lenguaje) revisa las etiquetas y bloquea lo que no debe salir.

La compuerta no lee prosa, no puntúa sospecha y no se puede persuadir. Tampoco le importa entre cuántos agentes se repartió el ataque: la etiqueta llega igual al final.

![Arquitectura](docs/diagramas/arquitectura.png)

## El laboratorio

Una licitación pública simulada, en español, con datos sintéticos:

| Agente | Tarea honesta |
|---|---|
| Radicador | Recibe las ofertas de tres proveedores ficticios y las registra |
| Evaluador | Puntúa las ofertas según el pliego y redacta el informe |
| Publicador | Publica el resultado en el portal (única salida al exterior) |

El secreto es el valor de la oferta sellada de un competidor, marcado con un canario único por episodio. El ataque repartido lo saca en tres pasos, uno por agente.

![Ataque repartido](docs/diagramas/ataque-repartido.png)

## Qué medimos

Cuatro brazos sobre los mismos episodios:

1. **Sin defensa**: referencia.
2. **M1**: monitor LLM por agente, la línea base de control de IA.
3. **M2**: monitor LLM que ve las trayectorias de todos los agentes juntas.
4. **Quórum**: compuerta de procedencia.

El ataque se corre con **fragmentación k = 1, 2 y 3**: el número de agentes entre los que se reparte. Con k = 1 es el ataque monolítico.

Métricas pre-registradas en [`metrics.yaml`](metrics.yaml): detección a 5 % de falsos positivos, tasa de fuga del canario, utilidad en episodios honestos y bloqueos de más. Intervalos de confianza al 95 % por bootstrap sobre episodios.

![Diseño experimental](docs/diagramas/evaluacion.png)

## Estructura del código

| Capa | Ruta | Contenido |
|---|---|---|
| Núcleo | `quorum/core/` | Etiquetas, política, compuerta, monitor, almacén y bitácora. Solo usa la biblioteca estándar y no conoce ningún dominio |
| Escenarios | `quorum/scenarios/` | `tender` (la licitación) y `helpdesk` (una mesa de ayuda). Cada uno es un `policy.toml` más sus herramientas |
| Adaptadores | `quorum/adapters/` | Inspect AI y function calling genérico |

El código está en inglés. Lo que leen los modelos y el jurado está en español.

## Documentos

- [Arquitectura](docs/arquitectura.md)
- [Modelo de amenaza](docs/modelo-de-amenaza.md)
- [Plan de evaluación](docs/plan-de-evaluacion.md)
- [Límites, riesgo dual y uso responsable](docs/uso-responsable.md)
- [Referencias y atribución](docs/referencias.md)
- [Tareas del equipo](docs/tareas.md)
- [Interfaz del laboratorio](docs/interfaz.md)

## Cómo correrlo

```bash
uv sync
uv run pytest        # 108 tests del núcleo, los escenarios y los adaptadores, sin modelos ni costo
```

Los episodios guionados recorren los cinco casos (honesto, honesto con oferta escaneada y ataque repartido entre 1, 2 y 3 agentes) sin llamar a ningún modelo:

```python
from quorum.scenarios.tender import run

ep = run("attack_k3", seed=1, defense=False)   # modo auditoría: nada se bloquea
ep.leak, ep.quorum_blocks                       # (True, True): hubo fuga y la compuerta la habría bloqueado
run("attack_k3", seed=1, defense=True).leak     # False
```

Las tareas de Inspect AI con agentes LLM están en construcción en `quorum/eval/`.

Las corridas con modelos reales usan una key de OpenRouter en `.env` (ver `.env.example`).

## Reglas que cumple este repo

- Todo corre dentro de un proceso local. No hay red, ni sistemas de terceros, ni datos de personas reales.
- Los proveedores, valores y documentos son sintéticos.
- No se publican instrucciones de ataque reutilizables fuera del laboratorio. Se publican tasas, trazas con canarios sintéticos y la defensa.

## Licencia

MIT. Ver [LICENSE](LICENSE).
