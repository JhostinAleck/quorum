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
| openai (cliente de Python) | Llamadas a un proveedor compatible con OpenAI (OpenRouter) desde el bucle de agente. Opcional |
| Docker y Docker Compose | Despliegue del monitor y de cada agente en contenedores. Imagen base `python:3.12-slim` |

## Modelos

Se completa durante el sprint con el identificador exacto de cada modelo, el proveedor y la fecha de uso.

| Rol | Modelo | Proveedor |
|---|---|---|
| Agentes (corridas sueltas de la interfaz web) | `openai/gpt-6-luna` | OpenRouter, 14 de noviembre de 2026 |
| Monitores M1 y M2 del experimento principal (Frente 3) | por definir | |
| Monitores M1 y M2 del experimento de persuasión (`quorum/monitor_bench.py`) | `openai/gpt-6-luna` | OpenRouter, 14 de noviembre de 2026 |
| Redacción de fragmentos de ataque | por definir | |

## Asistencia de IA en el desarrollo

| Herramienta | Qué hizo |
|---|---|
| Claude Code (Anthropic) | Documentos técnicos, diagramas, núcleo (etiquetas, política, compuerta, monitor), escenarios guionados, adaptadores, protocolo HTTP, despliegue en contenedores, prompts base y tests |
| Grok (xAI) | Búsqueda de literatura y contexto previo al diseño |

Se agregan filas a medida que otros agentes aportan código.
