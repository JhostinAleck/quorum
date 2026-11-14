# Guion del video de Quórum

Duración: 1:58,5 (118,5 s), por debajo de los 2:00 que nos pusimos como tope. El hackathon no pide video (ver `cumplimiento.md`); se asume un video de 2 minutos que sirve también como pitch.

Voz: ElevenLabs, voz Camila ES, modelo `eleven_v4`. Los tiempos de cada frase los devuelve ElevenLabs y están en `tiempos.tsv`; la animación se cuelga de esas marcas. Son 266 palabras: a 150 palabras por minuto serían 1:46, y con las pausas entre escenas y la tarjeta de cierre el video queda en 1:58,5.

Qué es cada plano: **generado** (Higgsfield), **animación** (hecha en código, `animacion/index.html`), **captura** (la interfaz real, modo guionado).

## Escenas

| # | Tiempo | Voz (texto exacto) | Lo que se ve | Tipo |
|---|---|---|---|---|
| 1 | 0:00,0 a 0:10,4 | Quórum es una compuerta determinista: impide que un dato sellado salga publicado, aunque el ataque se reparta entre varios agentes de inteligencia artificial. | Un sobre sellado avanza por un riel hacia una compuerta que se cierra y se enciende en rojo. Encima, el nombre, "Una compuerta determinista de procedencia" y la frase "Un dato sellado no sale publicado, aunque el ataque se reparta entre varios agentes". | Generado (g1) con texto montado encima |
| 2 | 0:10,4 a 0:23,3 | El caso: tres agentes tramitan una licitación pública con ofertas selladas. Uno radica, otro evalúa y otro publica. Si el ataque se reparte, ningún paso se ve raro. | Primera frase: un sobre sellado pasa por tres mesas iguales. Segunda: aparecen Radicador, Evaluador, Publicador y el Portal público. Tercera: una ficha roja "valor sellado" salta de agente en agente y bajo cada uno aparece lo que hace ("Abre un sobre y anota el valor", "Lo copia a su resultado", "Lo publica"); el portal queda en rojo. | Generado (g2) y luego animación |
| 3 | 0:23,3 a 0:35,5 | Cada dato lleva la etiqueta de sus fuentes, y lo que un agente escribe la hereda. En cada salida, la compuerta compara etiquetas: no lee texto ni llama a ningún modelo. | La etiqueta `{sealed.bid-2}` aparece en el sobre y luego bajo cada agente. Entra la compuerta antes del portal, compara "Etiqueta de la salida" con la política `publish = [ ]` y se cierra: "bloqueada". Dos rótulos: "No lee el texto", "No llama a ningún modelo". | Animación |
| 4 | 0:35,5 a 0:43,1 | Así se ve funcionando, con datos sintéticos. En un trámite honesto, la adjudicación se publica. | La interfaz real: ofertas cargadas y configuración; la cámara baja al resultado y se resaltan "Compuerta: permite" y el texto publicado en el portal. El rótulo de arriba pasa a "Trámite honesto: la compuerta permite y la adjudicación sale al portal". | Captura |
| 5 | 0:43,1 a 0:53,4 | Con los tres agentes desviados, el valor sellado pasa de uno a otro. La compuerta bloquea la salida: no se publica nada. | La interfaz real con los tres agentes en "modificado": se resalta `open_bid` del Radicador y el contexto restringido; la cámara sube y se resalta la misma etiqueta en el Evaluador y el Publicador; baja al resultado: "Compuerta: BLOQUEA", "(no se publicó nada)" y el sello BLOQUEADO. El rótulo de arriba cuenta cada paso. | Captura |
| 6 | 0:53,4 a 1:09,5 | Lo medimos en noventa trámites con agentes de modelo. Sin defensa, el valor se fugó en dieciséis de treinta ataques. La compuerta bloqueó las dieciséis fugas y dejó pasar los sesenta trámites honestos, sin llamar a un modelo. | 60 puntos (trámites honestos) y 30 puntos (ataques, en tres filas: repartidos entre 1, 2 y 3 agentes). Se encienden en rojo 16 ataques y el contador llega a "16 de 30". Luego esos 16 pasan a verde ("16 de 16 fugas bloqueadas"), los 60 honestos a verde ("0 de 60 bloqueados") y aparece "0 llamadas a un modelo". Pie: intervalos anchos. | Animación |
| 7 | 1:09,5 a 1:21,4 | Un monitor por agente también las detecta, sin falsos positivos. Pero gasta tres llamadas a un modelo por trámite y califica al final: detecta, no detiene. | Tabla que se llena con la voz. Monitor LLM por agente: 16 de 16, 0 de 30*, 3 llamadas, "al final: detecta". Compuerta de Quórum: 16 de 16, 0 de 60, 0 llamadas, "en cada salida: detiene". Pie: por qué 30 y no 60. | Animación |
| 8 | 1:21,4 a 1:36,2 | En cinco dominios, con agentes que siguen un guion, dejó en cero el daño en siete mil seiscientos episodios adversos. Y en trazas públicas de AgentDojo frenó mil quinientos seis de mil quinientos veintiún secuestros. | Izquierda: los cinco dominios y cuatro barras de episodios con daño (sin defensa 7600, filtro de coincidencia exacta 3200, mínimo privilegio por rol 3200, Quórum 0). Derecha: AgentDojo, contador hasta 1506 "de 1521 secuestros frenados". | Animación |
| 9 | 1:36,2 a 1:51,8 | Tiene costos. Bloquea siempre al agente honesto que abre un sobre que no necesitaba. En AgentDojo detiene parte de las tareas legítimas. Y un rival externo puede recuperar el monto con los puntajes que la licitación publica. | Tres tarjetas que entran con cada frase: "1000 de 1000 trámites honestos descuidados quedan detenidos", "75 de 411 tareas limpias de AgentDojo quedan detenidas" (y que en el corte principal conserva 16 de las 19), "50 de 50 veces un rival externo recupera el monto sellado" (el pliego publica los puntajes y la compuerta no lo impide). | Animación |
| 10 | 1:51,8 a 1:58,5 | El código, los datos y los límites están en el repositorio. | Sobre el plano de la compuerta cerrada: `github.com/JhostinAleck/quorum`, "16 de 16 fugas bloqueadas · 0 de 60 trámites honestos bloqueados · 0 llamadas a un modelo", y la declaración de datos sintéticos y de uso de IA. | Generado (g3) con texto montado encima |

Todo el video lleva subtítulos con la frase que se está diciendo y una barra de avance.

## Cada cifra y de dónde sale

Las líneas son las de los archivos el 14 de noviembre a las 15:30. `quorum.tex` se estaba editando ese día, así que su numeración puede haberse corrido; las otras fuentes son estables.

| Cifra (escena) | Fuente |
|---|---|
| 90 trámites: 60 honestos y 30 ataques, 10 por cada reparto (6) | `docs/ficha-tecnica.md:51-52`; `metrics.yaml:121-122` y `:142` |
| Fuga en 16 de 30 ataques sin defensa; 5, 6 y 5 según el reparto (6) | `docs/ficha-tecnica.md:73`; `metrics.yaml:145`; `docs/documento-tecnico/quorum.tex:179` |
| 16 de 16 fugas bloqueadas, 0 de 60 honestos bloqueados, sin llamar a un modelo (6, 7, 10) | `docs/ficha-tecnica.md:8-9`, `:84-87` y `:93` (utilidad honesta 60/60); `metrics.yaml:173-174` |
| Intervalo del 95 % de 16 de 16: de 81 a 100 % (6, en pantalla) | `docs/documento-tecnico/quorum.tex:196` |
| Monitor por agente: 16 de 16 fugas y 0 de 30 honestos marcados (7) | `docs/ficha-tecnica.md:80` y `:95`; `metrics.yaml:87` y `:124` |
| Los falsos positivos del monitor se miden en la mitad de los honestos (7, pie) | `docs/ficha-tecnica.md:31` y `:76`; `metrics.yaml:78` |
| El monitor por agente hace tres llamadas por trámite y califica al final (7) | `docs/resultados-monitores.md:217-218` |
| Cinco dominios; daño en 7600 de 7600 sin defensa, 3200 con filtro exacto, 3200 con mínimo privilegio, 0 con Quórum (8) | `docs/resultados-dominios.md:119`; `README.md:65` y `:69` |
| AgentDojo: 1506 de 1521 secuestros frenados (8) | `quorum/eval/agentdojo/RESULTADOS.md:43`; `docs/ficha-tecnica.md:114` |
| 1000 de 1000 trámites descuidados detenidos, es decir, terminan 0 de 1000 (9) | `docs/resultados-dominios.md:119` y `:141`; `README.md:71` |
| AgentDojo: 75 de 411 tareas limpias detenidas (9) | `quorum/eval/agentdojo/RESULTADOS.md:43` |
| AgentDojo, corte principal: conserva 16 de las 19 tareas que funcionan sin defensa (9, en pantalla) | `quorum/eval/agentdojo/RESULTADOS.md:24` y `:26`; `docs/documento-tecnico/quorum.tex:241` |
| Un rival externo recupera el monto en 50 de 50 casos (9) | `docs/intentos-de-evasion.md:89`; `docs/documento-tecnico/quorum.tex:254` |
| Política `publish = [ ]`: el portal no admite fuentes restringidas (3, en pantalla) | `quorum/scenarios/tender/policy.toml`, sección `[sinks]` |
| Lo que muestran las capturas (25 y 29 eventos de bitácora, puntajes 91,5, 100 y 87, el valor 468915720) | Salida real de la interfaz en modo guionado con las ofertas de ejemplo; no se dicen en la voz |

## Lo que el video deja fuera a propósito

- **Las dos mediciones de AgentDojo no se mezclan.** El video solo usa la de trazas grabadas de banca (`quorum/eval/agentdojo/RESULTADOS.md`). La repetición sin modelo de las cuatro suites (`docs/resultados-agentdojo.md`) no aparece.
- **Jev no aparece.** Se midió después de congelar `metrics.yaml`; si se menciona en las preguntas, hay que decirlo así.
- **El "5 de 30" no es del monitor por agente.** Es del monitor conjunto sin oráculo con Haiku. El monitor por agente tiene 0 de 30, que es lo que dice el video.
- **La inyección en la licitación sí se midió** (0 fugas en 600 episodios con buen prompt, `docs/ficha-tecnica.md:62`). No cabe en dos minutos y el video no afirma lo contrario.
- **"Agnóstica al modelo, al framework y al dominio"**, que el documento técnico ahora destaca, queda representada solo por la escena 8 (cinco dominios y un banco de pruebas ajeno). No hubo espacio para decirlo con esas palabras sin pasar de 2:00.
