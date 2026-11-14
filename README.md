# Quórum

**Una compuerta determinista de procedencia que detiene fugas de datos repartidas entre varios agentes de IA, aunque cada agente por separado parezca inocente.**

Proyecto del Defensive Acceleration Hackathon (AI Safety Colombia x IEEE CS Uniandes, 14 de noviembre de 2026). Track 6: riesgos multiagente, con cruce a control de IA y seguridad de agentes.

> Estado: en construcción durante el sprint. Los resultados se agregan a `docs/resultados.md` cuando existan. Nada en este repo afirma un número que no salga de los logs.

## El problema en una frase

Cuando una acción dañina se reparte entre varios agentes, un monitor que revisa a cada agente por separado ve tres pasos normales y ninguna alarma. El daño solo existe en el conjunto.

## La defensa

Cada dato lleva una etiqueta con su origen y su nivel de confidencialidad. La etiqueta viaja con el dato entre agentes a través de los servicios compartidos, y lo que un agente escribe hereda las etiquetas de todo lo que leyó. Antes de cualquier salida al exterior, una función pura (sin modelo de lenguaje) revisa las etiquetas y bloquea lo que no debe salir.

La compuerta no lee prosa, no puntúa sospecha y no se puede persuadir.

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

Tres brazos sobre los mismos episodios (honestos, ataque monolítico, ataque repartido):

1. **M1**: monitor LLM por agente (línea base).
2. **M2**: monitor LLM que ve las tres trayectorias juntas.
3. **Quórum**: compuerta de procedencia.

Métricas pre-registradas en [`metrics.yaml`](metrics.yaml): detección a 5 % de falsos positivos, tasa de fuga del canario, utilidad en episodios honestos y bloqueos de más. Intervalos de confianza al 95 % por bootstrap sobre episodios.

## Documentos

- [Arquitectura](docs/arquitectura.md)
- [Modelo de amenaza](docs/modelo-de-amenaza.md)
- [Plan de evaluación](docs/plan-de-evaluacion.md)
- [Límites, riesgo dual y uso responsable](docs/uso-responsable.md)
- [Referencias y atribución](docs/referencias.md)

## Cómo correrlo

```bash
uv sync
uv run pytest        # 20 tests de etiquetas, compuerta y laboratorio, sin modelos ni costo
```

Los episodios guionados de `quorum/lab/guiones.py` recorren los cuatro casos (honesto, honesto con oferta escaneada, ataque monolítico y ataque repartido) sin llamar a ningún modelo. Las tareas de Inspect AI con agentes LLM están en construcción en `quorum/eval/`.

Las corridas con modelos reales usan una key de OpenRouter en `.env` (ver `.env.example`).

## Reglas que cumple este repo

- Todo corre dentro de un proceso local. No hay red, ni sistemas de terceros, ni datos de personas reales.
- Los proveedores, valores y documentos son sintéticos.
- No se publican instrucciones de ataque reutilizables fuera del laboratorio. Se publican tasas, trazas con canarios sintéticos y la defensa.

## Licencia

MIT. Ver [LICENSE](LICENSE).
