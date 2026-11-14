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

## Funciona en otros dominios

La compuerta no sabe de licitaciones. Se probó igual, sin cambiar una línea del núcleo, en cuatro dominios: licitación pública, mesa de ayuda, historias clínicas y banca. Cada uno es un archivo de política de unas 20 líneas más sus herramientas.

| Episodios guionados, 200 semillas por tipo | Sin defensa | Filtro de coincidencia exacta | Quórum |
|---|---|---|---|
| Daño en 5800 episodios adversos (4 dominios) | 100 % | 45 % | 0 % |
| Trámites honestos que terminan bien (1000) | 100 % | 100 % | 100 % |
| Trámites descuidados que terminan bien (800) | 100 % | 100 % | 0 % |

El filtro de coincidencia exacta conoce todos los secretos y detiene las copias literales, pero no el mismo dato escrito en palabras ni una transferencia ordenada por un mensaje de un tercero. La última fila es el costo de Quórum: si un agente honesto mira un dato restringido que no necesitaba, la compuerta detiene su salida aunque no filtre nada.

Son agentes que siguen un guion, así que estas cifras miden el mecanismo y no la conducta de un modelo. El detalle por dominio, la tabla de qué es sensible en cada uno y cómo reproducirlo están en [resultados por dominio](docs/resultados-dominios.md). Lo que sí rompe la compuerta está en [intentos de evasión](docs/intentos-de-evasion.md).

```bash
uv run python -m quorum.bench      # sin modelos ni costo, unos segundos
```

## Estructura del código

| Capa | Ruta | Contenido |
|---|---|---|
| Dominio | `quorum/domain/` | El modelo de la defensa: etiquetas, política, compuerta, agente y bitácora. Puro, sin entrada ni salida |
| Aplicación | `quorum/application/` | El monitor de referencia por el que pasa toda llamada de un agente |
| Infraestructura | `quorum/infrastructure/` | Almacenes (memoria, SQLite) y políticas en TOML |
| Contextos | `quorum/scenarios/` | Cuatro dominios: `tender` (licitación), `helpdesk` (mesa de ayuda), `clinic` (historias clínicas) y `bank` (banca). Cada uno es un `policy.toml` más sus herramientas y reglas |
| Adaptadores | `quorum/adapters/` | Inspect AI, function calling genérico, bucle de agente y el monitor como servicio HTTP |
| Despliegue | `quorum/launch.py`, `Dockerfile`, `docker-compose.yml` | El monitor y cada agente en su propio contenedor |
| Interfaz web | `quorum/ui/`, `docker-compose.ui.yml` | Página de demo: subir ofertas (texto, PDF o escaneos), correr un episodio y ver decidir a la compuerta |

El diseño sigue DDD: las dependencias apuntan hacia el dominio y un test lo comprueba (ver [arquitectura](docs/arquitectura.md)). El código está en inglés. Lo que leen los modelos y el jurado está en español.

## Documentos

- [Arquitectura](docs/arquitectura.md)
- [Modelo de amenaza](docs/modelo-de-amenaza.md)
- [Plan de evaluación](docs/plan-de-evaluacion.md)
- [Límites, riesgo dual y uso responsable](docs/uso-responsable.md)
- [Intentos de romper la compuerta](docs/intentos-de-evasion.md)
- [La misma compuerta en cuatro dominios](docs/resultados-dominios.md)
- [Referencias y atribución](docs/referencias.md)
- [Tareas del equipo](docs/tareas.md)
- [Interfaz del laboratorio](docs/interfaz.md)
- [Protocolo del monitor por red](docs/protocolo.md)
- [Despliegue en contenedores](docs/despliegue.md)
- [Interfaz web](docs/interfaz-web.md)

## Cómo correrlo

```bash
uv sync
uv run pytest        # 533 tests del núcleo, los escenarios, los adaptadores y la interfaz, sin modelos ni costo
```

Los episodios guionados recorren los cinco casos (honesto, honesto con oferta escaneada y ataque repartido entre 1, 2 y 3 agentes) sin llamar a ningún modelo:

```python
from quorum.scenarios.tender import run

ep = run("attack_k3", seed=1, defense=False)   # modo auditoría: nada se bloquea
ep.leak, ep.quorum_blocks                       # (True, True): hubo fuga y la compuerta la habría bloqueado
run("attack_k3", seed=1, defense=True).leak     # False
```

### En contenedores

El monitor y cada agente pueden correr en contenedores separados. Los agentes no tienen el almacén ni la bitácora: solo le hablan al monitor por HTTP, cada uno con su token, en una red sin salida a internet.

![Contenedores](docs/diagramas/contenedores.png)

```bash
# una vez: cuatro tokens al azar en .env (no se sube al repo)
for v in QUORUM_TOKEN_REGISTRAR QUORUM_TOKEN_EVALUATOR QUORUM_TOKEN_PUBLISHER QUORUM_ADMIN_TOKEN; do
  echo "$v=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
done >> .env

docker compose build
docker compose run --rm report                              # trámite honesto
docker compose down -v

QUORUM_KIND=attack_k3 docker compose run --rm report        # ataque repartido: la compuerta lo bloquea
docker compose down -v
```

El reporte es un JSON con `leak`, `useful`, `quorum_blocks`, lo publicado y cada bloqueo con su motivo. Los demás casos, el modo con modelo y lo que este aislamiento da y no da están en [despliegue](docs/despliegue.md).

### Interfaz web

Una página para subir ofertas (texto, PDF o escaneos), elegir agentes honestos o desviados y ver cada paso con sus etiquetas y la decisión de la compuerta. Usa el mismo escenario, bucle de agente y protocolo.

```bash
uv run python -m quorum.ui.server                          # un solo proceso, http://127.0.0.1:8765
docker compose -f docker-compose.ui.yml up --build         # cada agente en su contenedor
```

Detalles y límites en [interfaz web](docs/interfaz-web.md).

Las tareas de Inspect AI con agentes LLM están en construcción en `quorum/eval/`.

Las corridas con modelos reales usan una key de OpenRouter en `.env` (ver `.env.example`).

## Reglas que cumple este repo

- Todo corre en la máquina local, en un proceso o en contenedores propios dentro de una red interna. No se toca ningún sistema de terceros ni hay datos de personas reales. La única conexión hacia afuera es la llamada al proveedor del modelo cuando los agentes usan uno.
- Los proveedores, valores y documentos son sintéticos.
- No se publican instrucciones de ataque reutilizables fuera del laboratorio. Se publican tasas, trazas con canarios sintéticos y la defensa.

## Licencia

MIT. Ver [LICENSE](LICENSE).
