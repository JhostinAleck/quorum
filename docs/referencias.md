# Referencias y atribución

## Trabajos en los que se basa

| Trabajo | Qué tomamos |
|---|---|
| Costa et al., *Securing AI Agents with Information-Flow Control* (FIDES), Microsoft, 2025. arXiv:2505.23643 | Etiquetas de confidencialidad e integridad en el contexto del agente, política determinista en cada llamada, variables ocultas |
| Debenedetti et al., *Defeating Prompt Injections by Design* (CaMeL), Google DeepMind, 2025. arXiv:2503.18813 | Separar flujo de control de datos no confiables, modelo en cuarentena |
| Debenedetti et al., *AgentDojo*, 2024. arXiv:2406.13352 | Medir seguridad y utilidad en los mismos episodios |
| Greenblatt et al., *AI Control: Improving Safety Despite Intentional Subversion*, 2023. arXiv:2312.06942 | Supuesto de agentes no confiables, monitores como línea base, calibración por falsos positivos |
| Hammond et al., *Multi-Agent Risks from Advanced AI*, 2025. arXiv:2502.14143 | Marco de riesgos que solo aparecen en el conjunto |
| Urcuqui, *AgentBreak* (github.com/urcuqui/AgentBreak) | Controles deterministas fuera del modelo, ataques convertidos en tests de regresión |
| UK AI Security Institute, *Inspect AI* (inspect.aisi.org.uk) | Framework de evaluación |

## Trabajo relacionado más cercano

| Trabajo | Relación con Quórum |
|---|---|
| Makins, Angelini, Shams y Phuong, *Multi-Agent AI Control: Distributed Attacks Hamper Per-Instance Monitors*, UK AISI y MATS, 2026. arXiv:2607.07368 | Formaliza el ataque repartido y muestra que repartirlo baja la sospecha de cada agente ante un monitor. Evalúa monitores, no seguimiento de procedencia. Es el problema que tomamos como punto de partida |
| Dai et al., *SafeFlow: Semantic Information-Flow Control for Blocking Malicious Propagation in Multi-Agent Systems*, 2026. arXiv:2607.25255 | Propaga etiquetas entre agentes y valida el flujo antes de acciones irreversibles. Parte de las etiquetas iniciales las asigna un clasificador LLM, su modelo de amenaza es contenido malicioso y no agentes no confiables, y no se compara con monitores de control |
| *APPA: Recoverable Information-Flow Control for Real-World LLM Agents*, 2026. arXiv:2607.24625 | Aborda el bloqueo de más del taint monótono, el mismo costo que medimos aquí |

**Qué aporta Quórum.** Llevar etiquetas de procedencia entre agentes no es una idea nueva. Lo que este proyecto aporta es:

1. Medir una compuerta determinista de procedencia contra el ataque repartido, cara a cara con monitores por agente y de composición, bajo el supuesto de que los propios agentes son los atacantes.
2. Reportar el costo en trabajo legítimo bloqueado junto al beneficio.
3. Un laboratorio abierto, pequeño y en español, con un escenario de contratación pública.

Antes de la entrega, cada cita que aparezca en la ficha técnica se verifica abriendo la fuente.

## Software

| Paquete | Uso |
|---|---|
| inspect-ai | Orquestación de episodios, scorers, trazas |
| pytest, hypothesis | Tests de la compuerta |
| numpy, matplotlib | Bootstrap y figura |
| @mermaid-js/mermaid-cli | Diagramas |
| agentdojo 0.1.35 (opcional, solo para `quorum/agentdojo_bench.py`) | Tareas, herramientas y ataques del banco de pruebas AgentDojo, repetidos sin modelo |
| openai (cliente de Python) | Llamadas a un proveedor compatible con OpenAI (OpenRouter) desde el bucle de agente. Opcional |
| Docker y Docker Compose | Despliegue del monitor y de cada agente en contenedores. Imagen base `python:3.12-slim` |

## Modelos

Todos se usaron el 14 de noviembre de 2026. El identificador es el que queda registrado en `datos/`.

| Rol | Modelo | Proveedor | Dónde consta |
|---|---|---|---|
| Agentes de la licitación (ataques, honestos y línea base principal) | `orca/orcacyber-flash-1.0` | OrcaRouter | `datos/pilot_orca_v4.jsonl`, `pilot_honest_extra.jsonl`, `baseline_v1.jsonl` |
| Monitores M1, M2, M2 sin oráculo y compuerta suave | `google/gemini-3.5-flash-lite` | OpenRouter | `datos/monitor_*` (sin sufijo y `_ciegofix`) |
| Los mismos monitores, segunda familia | `claude-haiku-5-5` | Anthropic | `datos/monitor_*_haiku55*` |
| Línea base de buen prompt con otros agentes | `openai/gpt-4o-mini`, `meta-llama/llama-3.1-8b-instruct`, `meta/muse-ember` (solo prueba corta) | OpenRouter | `datos/baseline_*` |
| Línea base de buen prompt con otros agentes | `openai/gpt-6-luna`, `xiaomi/mimo-v2.6-flash` | OrcaRouter | `datos/baseline_gpt6luna.jsonl`, `baseline_mimoflash.jsonl` |
| Monitores M1 y M2 del experimento de persuasión (`quorum/monitor_bench.py`) | `openai/gpt-6-luna` | OpenRouter | `datos/monitores-persuasion.jsonl` |
| Agentes con prompts honestos y carta inyectada (`quorum/llm_bench.py`) | `openai/gpt-6-luna` | OpenRouter | `datos/agentes-inyeccion.jsonl` |
| Agentes de la interfaz web (por defecto) | `openai/gpt-6-luna` | OpenRouter | `quorum/ui/agents.py` |
| Prueba de modelos para la demo (un episodio por caso, no se reporta como cifra) | `deepseek/deepseek-v4-flash`, `qwen/qwen3.7-flash`, `mistralai/mistral-small-3.2-24b-instruct`, `z-ai/glm-5.3-flash` | OpenRouter | descripción del PR del Frente 3 |
| Trazas externas de AgentDojo (no las generamos: se reproducen) | `gpt-4o-2024-05-13` y las demás configuraciones del benchmark | ETH Zürich (ethz-spylab/agentdojo, commit `089ed468`) | `quorum/eval/agentdojo/RESULTADOS.md` |
| Redacción de los fragmentos de ataque | Ningún modelo: las plantillas se escribieron a mano con Claude Code y están en `quorum/eval/attacks.py` | | |

## Asistencia de IA en el desarrollo

| Herramienta | Qué hizo |
|---|---|
| Claude Code (Anthropic) | Documentos técnicos, diagramas, núcleo (etiquetas, política, compuerta, monitor), escenarios guionados, adaptadores, protocolo HTTP, despliegue en contenedores, prompts base y tests |
| Grok (xAI) | Búsqueda de literatura y contexto previo al diseño |
| Claude Code (Anthropic, Claude Opus 5.5) | Frente 3: ataques, monitores, piloto, `metrics.yaml`, análisis con intervalos de confianza, reproducción de AgentDojo, línea base, ablación, intentos de romper la compuerta, conexión de los ataques a la interfaz, notas de la mentoría y tests |
| OpenCode | Frente 3: ficha técnica, `metrics.yaml` (enmiendas), `datos/README.md` y revisión de cifras |

Los agentes de desarrollo trabajaron con supervisión del equipo; cada cifra se recalcula desde `datos/` con `quorum/eval/analysis.py`.
