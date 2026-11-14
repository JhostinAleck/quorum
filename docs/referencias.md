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

**Diferencia con FIDES y CaMeL:** ambos protegen a un agente. Quórum conserva la etiqueta cuando el dato pasa de un agente a otro a través de servicios compartidos, y mide el resultado contra un ataque repartido.

Antes de la entrega, cada cita que aparezca en la ficha técnica se verifica abriendo la fuente.

## Software

| Paquete | Uso |
|---|---|
| inspect-ai | Orquestación de episodios, scorers, trazas |
| pytest, hypothesis | Tests de la compuerta |
| numpy, matplotlib | Bootstrap y figura |
| @mermaid-js/mermaid-cli | Diagramas |

## Modelos

Se completa durante el sprint con el identificador exacto de cada modelo, el proveedor y la fecha de uso.

| Rol | Modelo | Proveedor |
|---|---|---|
| Agentes | por definir | |
| Monitores M1 y M2 | por definir | |
| Redacción de fragmentos de ataque | por definir | |

## Asistencia de IA en el desarrollo

| Herramienta | Qué hizo |
|---|---|
| Claude Code (Anthropic) | Documentos técnicos, diagramas, esqueleto del repo, compuerta y tests |
| Grok (xAI) | Búsqueda de literatura y contexto previo al diseño |

Se agregan filas a medida que otros agentes aportan código.
