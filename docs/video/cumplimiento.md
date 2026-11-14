# Cumplimiento de los requisitos del hackathon

## Qué se pide del video

**No hay requisito de video.** Ni la página oficial ni la guía del día lo mencionan. Lo que se pide es un pitch presencial con la ficha técnica proyectada. Se asumió un video de 2 minutos que sirve también como pitch.

Citas textuales y de dónde salen:

| Tema | Cita | Fuente |
|---|---|---|
| Video | La página no menciona ningún video (comprobado al leerla el 14 de noviembre) | `https://www.aisafetycolombia.org/defacchackathon` |
| Pitch | "Desde las 5:10 p. m. cada equipo presenta un pitch de 3 minutos, en el orden del sorteo. Después, el jurado puede hacer unas pocas preguntas cortas." | Guía del día de la página oficial (`/defacchackathon/guia`) |
| Pitch | "No tienen que preparar diapositivas. Presentan su ficha técnica de 2 páginas, que proyectamos en pantalla." | Guía del día |
| Pitch, versión del briefing | "frente al pitch, que son 2 minutos y tienes que exponerlo, punto" | `docs/hackathon/briefing-2026-11-14-notas.md:23` |
| Discrepancia | "la página oficial dice 3 minutos con la ficha proyectada; el mentor dijo 2. Confirmar con la organización." | `docs/mentoria-2026-11-14.md:97` |
| Idioma | "Idioma: Español" | Página oficial |
| Entrega | "La ficha técnica en PDF, de máximo 2 páginas y 10 MB: amenaza, defensa, cómo la evaluaron, resultados, límites y riesgo de uso dual." y "El enlace al repositorio (GitHub o Colab) o a la demo." | Guía del día |
| Criterio 1 | "Impacto potencial e innovación: ¿Ataca un riesgo real de IA con una idea nueva? ¿Le da ventaja a quien defiende?" | Guía del día |
| Criterio 2 | "Calidad de ejecución: ¿Funciona y lo pusieron a prueba? ¿Los resultados respaldan lo que dicen?" | Guía del día |
| Criterio 3 | "Presentación y claridad: ¿Un jurado entiende en 2 minutos qué hicieron y qué encontraron?" | Guía del día |
| Regla | "No ataques, escanees ni pruebes sistemas reales de terceros sin permiso escrito. Es delito (Ley 1273 de 2009). Trabaja con benchmarks, laboratorios o datos sintéticos." | Guía del día |
| Regla | "No publiques exploits funcionales ni malware." | Guía del día |
| Regla | "Usa datos públicos anonimizados o sintéticos. Nada de voces, rostros ni correos de personas reales." | Guía del día |
| Regla | "Cita todo el código, los datos y lo que generaste con IA." | Guía del día |
| Regla | "Un proyecto que sobre todo facilita ataques, sin mitigación, no puede ganar premio." | Guía del día |
| Límites | "documentar con honestidad dónde falla la defensa y verificar que el trabajo no facilite usos ofensivos" | Página oficial |
| Consejo del mentor | "tú me hablas de agentes y la compuerta no la mencionaste": abrir por la compuerta y cerrar con el número | `docs/mentoria-2026-11-14.md:87-93` |

## Dónde cumple el video cada requisito

| Requisito | Dónde lo cumple (escena y segundo) |
|---|---|
| Se entiende en 2 minutos qué hicieron y qué encontraron | Dura 1:58,5. Qué hicieron: escenas 1 a 5 (0:00 a 0:53). Qué encontraron: escenas 6 a 9 (0:53 a 1:52) |
| Español | Voz, subtítulos y textos en español |
| El vector de riesgo, definido con precisión | Escena 2 (0:10 a 0:23): el ataque repartido entre tres agentes de una licitación |
| El mecanismo defensivo | Escena 3 (0:23 a 0:36): etiquetas de procedencia y compuerta. Escena 1 abre por la compuerta, como pidió el mentor |
| Funciona | Escenas 4 y 5 (0:36 a 0:53): capturas reales de un trámite honesto que se publica y de un ataque bloqueado |
| Lo pusieron a prueba, con línea base | Escena 6 (0:53 a 1:09): 90 trámites, 16 de 30 fugas sin defensa, 16 de 16 bloqueadas, 0 de 60 honestos. Escena 7 (1:09 a 1:21): frente al monitor LLM por agente. Escena 8 (1:21 a 1:36): cinco dominios frente a filtro exacto y mínimo privilegio, y AgentDojo |
| Los resultados respaldan lo que dicen | Cada cifra lleva su denominador en pantalla y su fuente en `guion.md` |
| Límites dichos con honestidad | Escena 9 (1:36 a 1:52): bloquea de más, frena trabajo legítimo y no cierra lo que la licitación publica. Escena 6: pie sobre intervalos anchos. Escena 7: se dice que el monitor también detecta |
| Nada contra sistemas reales; datos sintéticos | Escena 4 lo dice en voz ("con datos sintéticos"); las capturas llevan el rótulo; cierre (1:52): "Datos sintéticos. No se atacó ni escaneó ningún sistema real." |
| Sin exploits ni instrucciones de ataque | El video muestra el ataque como diagrama y su bloqueo; no enseña cómo construirlo |
| Sin voces, rostros ni correos de personas reales | No hay rostros ni correos. La voz se sintetiza con una voz de catálogo que su dueño licencia a ElevenLabs: ver la nota de abajo |
| Citar lo generado con IA | Cierre (1:52 a 1:58): declaración en pantalla. Los planos generados llevan el rótulo "Plano generado con IA · Higgsfield" mientras se ven |
| Enlace al repositorio | Cierre: `github.com/JhostinAleck/quorum` |

## Declaración de herramientas de IA usadas en el video

| Herramienta | Para qué | Detalle |
|---|---|---|
| Claude Code (Anthropic) | Guion, storyboard, animación en código (`animacion/`), capturas automatizadas de la interfaz, montaje con ffmpeg y estos documentos | Con supervisión del equipo |
| ElevenLabs | Voz de la narración | Voz de biblioteca "Camila ES - Melete", modelo `eleven_v4`, stability 0.5, similarity 0.75, style 0, speed 1.2; las tomas se ajustaron un 5 % de velocidad con ffmpeg |
| Higgsfield | Tres planos de fondo: apertura (g1, 8 s), el caso (g2, 5 s) y cierre (g3, 6 s) | Modelo Seedance 2.5 (`seedance_2_5`), texto a video, 720p, sin audio. Prompts en `storyboard.md` |
| Grok (xAI) | Investigación en X del flujo de producción | Pregunta genérica, sin datos del equipo: `investigacion-grok.md` |
| agy | Revisión del video completo, con imagen y audio | `revision-agy.md` |
| ffmpeg, Chrome sin cabeza y puppeteer-core | Render y montaje | No son IA; se citan como código de terceros |

Nota sobre la voz: es una voz del catálogo de ElevenLabs de categoría "professional", es decir, la voz de una persona real que la licencia a ElevenLabs para que otros la usen. No es un clon hecho por el equipo ni la voz de un integrante. La regla del hackathon dice "Nada de voces, rostros ni correos de personas reales". La lectura del equipo es que la regla se refiere a datos de terceros usados sin permiso y que una voz licenciada para este uso no entra ahí; es una lectura, no algo que la organización haya confirmado. Si se prefiere no dejar la duda, `montar.sh` monta el mismo video con la voz de sistema de macOS cuando `voz/` está vacía.

Lo que no es IA en el video: las capturas son de la interfaz real en modo guionado; todas las cifras salen de los archivos del repositorio y no de un modelo.
