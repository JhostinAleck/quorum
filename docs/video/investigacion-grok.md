# Investigación con Grok: cómo se produce un video con Claude, Higgsfield y ElevenLabs

Consulta hecha el 14 de noviembre de 2026 con el CLI de Grok (`~/.grok/bin/grok --prompt-file <archivo> --output-format plain`), en modo de una sola pregunta y desde una carpeta vacía fuera del repositorio. La pregunta es genérica: no lleva nombres de personas, del equipo ni del proyecto.

Notas sobre este archivo:

- La respuesta va tal como la devolvió Grok, con un solo cambio mecánico: las rayas largas se sustituyeron por un guion corto (`-`), porque en este repositorio no se usan. No se cambió ninguna palabra, cifra ni enlace.
- Los enlaces y las citas son los que dio Grok. No se abrieron uno por uno, así que hay que tratarlos como "según Grok" hasta que alguien los verifique. Las inferencias de Grok están marcadas por él mismo como tales.
- El primer párrafo junta los mensajes de progreso que el CLI imprime antes de la respuesta.

## Pregunta

```text
Busca en X (Twitter) publicaciones recientes (últimos 6 meses, prioriza las más recientes) sobre el flujo de trabajo para producir videos explicativos o de producto de 1 a 3 minutos combinando tres herramientas: Claude (guion, storyboard, prompts, edición por código, por ejemplo con Remotion o ffmpeg), Higgsfield (generación de video e imagen) y ElevenLabs (voz en off). Usa tu herramienta de búsqueda en X; si hace falta complementa con búsqueda web.

Quiero saber, con el detalle práctico que den las publicaciones:
1. Qué pasos siguen y en qué orden (guion, voz, storyboard, imágenes, video, montaje).
2. Qué prompts usan en cada herramienta (ejemplos textuales si los hay) y en qué idioma funcionan mejor los prompts de Higgsfield.
3. Qué duración usan por plano generado y cuántos planos para un video de 2 minutos.
4. Cómo sincronizan la voz con el video (primero la voz y luego el corte, marcas de tiempo, subtítulos).
5. Cómo mantienen consistencia visual entre planos (imagen de referencia, línea de estilo fija, semilla, modelo).
6. Qué ajustes de ElevenLabs recomiendan para narración en español (modelo, estabilidad, similitud, velocidad) y qué tipo de voz.
7. Qué errores evitar.
8. Cómo montan capturas o grabaciones reales de un producto de software junto con planos generados.
9. Cuánto tarda y cuánto cuesta aproximadamente (créditos, planes) si alguna publicación lo dice.

Reglas para tu respuesta: responde en español; cita cada afirmación con la publicación de la que sale (autor con su @ y enlace directo a la publicación, y fecha si la ves); distingue con claridad lo que dice una publicación de lo que es inferencia tuya; si no encuentras publicaciones sobre algún punto, dilo en vez de rellenar. No escribas ni modifiques archivos: solo responde con texto.
```

## Respuesta cruda de Grok

Voy a buscar en X publicaciones recientes sobre el flujo Claude + Higgsfield + ElevenLabs y, si hace falta, complementar con la web. Empiezo por combinaciones de las tres herramientas y por cada paso del flujo.Encontré varios flujos concretos. Ahora saco los hilos y artículos con más detalle práctico (prompts, orden, voz, consistencia) y busco los puntos que aún faltan.Hay buen material de flujo y prompts. Sigo con duración de planos, idioma de Higgsfield, ajustes de ElevenLabs en español, coste y cómo mezclan capturas reales.Me faltan el idioma de los prompts de Higgsfield, ajustes concretos de ElevenLabs en español y cómo mezclan capturas de software. Voy a esas fuentes y a un par de artículos largos.La skill oficial de Higgsfield responde varios puntos clave. Voy a extraer el pipeline, el idioma de prompts y los números de bloques.No encontré un único hilo que documente de punta a punta un video de 1–3 minutos con las tres herramientas juntas y capturas de un producto de software. Lo que sí hay, y es reciente, son dos familias de flujo: la skill oficial de Higgsfield orquestada por Claude (bloques de 10 s, voz primero, estilo fijo), y pipelines “Claude Code + ElevenLabs + ffmpeg/Remotion” donde Higgsfield entra como generador de planos o de fotos.

Abajo va lo que las publicaciones dicen, punto por punto. Cuando infiero, lo marco.

---

## 1. Orden de pasos

Hay tres órdenes publicados, no uno solo.

**A. Skill oficial de Higgsfield (Claude orquesta). Voz antes que el video.**

La skill `higgsfield-video-explainer` (repo de Higgsfield, actualizada el 5 nov 2026) fija este pipeline:

0. Elegir estilo visual  
R. Investigar el tema  
1. Generar **una** imagen de estilo (`style key`)  
2. Escribir N líneas de locución  
3. Escribir N prompts de video  
4. Generar **todas** las tomas de voz  
5. Generar **todos** los clips  
6. Ensamblar el MP4  

Fuente: [skill oficial Higgsfield](https://skillselion.com/skills/higgsfield-ai/skills/higgsfield-video-explainer) y la guía de [scriptable.com, 8 jul 2026](https://scriptable.com/posts/higgsfield/youtube-video-from-script/).

**B. YouTube faceless con Claude + ElevenLabs + Higgsfield. Voz primero, imágenes después.**

[@facelesslaunchp, 14 nov 2026](https://x.com/facelesslaunchp/status/2121612756658909426):

1. investigación de nicho (Claude)  
2. transcripciones de competidores  
3. **guion** (Claude, “un script de 30 minutos de una vez”)  
4. **voz** (ElevenLabs)  
5. transcripción con marcas de tiempo (TurboScribe)  
6. **imágenes de escena** (Higgsfield conectado a Claude Code, “straight from that timestamped voiceover”)  
7. personajes recurrentes (ChatGPT Images + referencia)  
8. miniatura  
9. montaje (CapCut; Claude para stick-figure/slideshow)  
10. metraje real: editor humano  

**C. Anuncio de producto corto (15 s). Brief → video Higgsfield → locución.**

[@humzaakhalid, 26 may 2026](https://x.com/humzaakhalid/status/2059152604442267813): foto de producto → conectar Higgsfield MCP a Claude → brief de 3 escenas + locución → generar el video en Higgsfield → escribir la voz → overlays.

**Otras piezas del mismo stack:**

- [@RaulReyeszumeta, 14 nov 2026](https://x.com/RaulReyeszumeta/status/2121592919748456914): “FFmpeg edits, graphics with code, Higgsfield + ElevenLabs through Super Tools MCP.”
- [@youtubersinn, 13 nov 2026](https://x.com/youtubersinn/status/2121247365910630640): idea/script Claude → voz propia o ElevenLabs → visual Higgsfield/Flow → edit CapCut.
- [@axultan (head of product de Higgsfield), 4 ago 2026](https://x.com/axultan/status/2084650201504260546): skill de “editorial explainer” de hasta 10 minutos con research, generación, voiceover y subtítulos dentro de Claude/ChatGPT.
- [@AtamanshaX, 14 nov 2026](https://x.com/AtamanshaX/status/2121495792338776484): para motion design con Katana, **primero la voz y el mix**, y Katana renderiza el video a esa pista.

**Inferencia mía:** para un explainer de 1–3 min el orden que más se repite es guion → estilo/referencias → voz (entera o por bloque) → timestamps → planos → montaje. El brief de 15 s de Hamza genera el video antes de la voz porque el clip es un solo producto, no un relato de 2 minutos.

---

## 2. Prompts por herramienta e idioma de Higgsfield

### Claude (brief / guion)

[@humzaakhalid, 26 may 2026](https://x.com/humzaakhalid/status/2059152604442267813):

> I am creating a 15-second TikTok product video for [product]. Target audience: [audience]. Tone: [energetic/luxurious/cinematic]. Goal: [awareness/conversion]. Write: video concept in 2 sentences, 3-scene shot sequence, voiceover script under 15 seconds, text overlay plan for each scene.

Y para la locución:

> Write a 15-second voiceover for [product]. Tone: [tone]. Hook in the first 2 seconds. Short, punchy sentences. End with soft CTA: 'Shop now' or 'Try it today.' Max 40 words total.

[@AtamanshaX, 14 nov 2026](https://x.com/AtamanshaX/status/2121495792338776484) (brief de Katana, copiar tal cual):

> /katana Turn the video I attached into a motion-design ad for my [product], using my photos.  
> - Motion design only: kinetic type, shapes, UI cards and camera moves, drawn in code…  
> - No AI video and no AI images. My photos are the only pictures. It should cost 0 credits.  
> - Copy the reference's rhythm and cuts, not its content. [16:9, 8 seconds], keep its soundtrack.  
> - My words: "[Meet KŌRI.]" / "[Ice cold.]" / "[Steel.]" / "[Made to carry.]"

### Higgsfield (prompt de plano)

Plantilla de la skill oficial (inglés, un bloque):

```
Block N
STYLE REFERENCE: Match the attached reference image EXACTLY. <STYLE descriptor>
SCENE: <una acción que coincida con la locución del bloque>
MOTION: <cámara y animación>
AUDIO: <ambiente o música; sin voz ni diálogo>
NEGATIVE: <nada de fotorrealismo, lip-sync, captions, texto, logos, watermark>
```

Ejemplo concreto de [scriptable.com, 8 jul 2026](https://scriptable.com/posts/higgsfield/youtube-video-from-script/):

```
Block 1
STYLE REFERENCE: Match the attached reference image EXACTLY: hand-inked black
marker on off-white paper, solid jet-black fills, thin white scratch highlights,
marker grain, strictly monochrome.
SCENE: An old mapmaker bent over a wide sheet, inking a coastline; the far edge
of the map stays a broad blank margin.
MOTION: Slow push-in toward the empty margin, ink lines settling.
AUDIO: quiet scratch of a nib, soft room tone - no voice.
NEGATIVE: color, gray midtones, photorealism, 3D render, lip-sync, captions,
on-screen text, watermark.
```

Prompt de video de producto (Hamza):

> Using Higgsfield, generate a product video for the image I will upload. Motion: [slow zoom/orbit/floating/cinematic pan]. Style: [luxury/energetic/minimal]. Duration: 15 seconds. Subtle depth of field. Output in 9:16 vertical format.

Prompt largo de UGC en Seedance 2.5 dentro de Higgsfield, en inglés, con minutos marcados: [@mehvishs25, 13 nov 2026](https://x.com/mehvishs25/status/2121090977515671871). Empieza: “Create a finished 30-second realistic social-media UGC advertisement…” y detalla personaje, vestuario, setting, cámara, diálogo por tramo de 0–5 / 5–10 / 10–16 s, y una lista de continuidad (“Keep the same woman throughout…”).

### Idioma de los prompts de Higgsfield

La skill oficial lo dice en una línea dura: **“Write all image/video prompts in English. Only narration uses the selected language.”** ([skill Higgsfield](https://skillselion.com/skills/higgsfield-ai/skills/higgsfield-video-explainer), 5 nov 2026).

Los prompts publicados en X que encontré (Meem, Ciri, Oogie, Johnn, Hamza, Atamansha) están en inglés. Un tutorial de YouTube del flujo Claude + Higgsfield ([“One Sentence → A Full Vox-Style Explainer”](https://www.youtube.com/watch?v=_fNOdvr3Wrc), 30 jul 2026) hace el video en inglés y después: “Now do the same video in Spanish and Portuguese - same clips, just a new voiceover.”

**No encontré ninguna publicación que compare A/B prompts de Higgsfield en español vs inglés y declare un ganador.** Lo que sí está escrito, y es de Higgsfield, es: prompts visuales en inglés; locución en el idioma que elijas.

### ElevenLabs (tags de actuación)

[@AtamanshaX, 14 nov 2026](https://x.com/AtamanshaX/status/2121495792338776484): una sola toma de todo el guion, con acotaciones entre corchetes que **se actúan, no se leen**:

> [low, intense, like an old samurai master] Don't learn After Effects.  
> [explosive kiai shout, full power] EIYAAAAH!!  
> [proud, fierce, quiet] My katana made this.

---

## 3. Duración por plano y cuántos para ~2 minutos

| Fuente | Duración por plano | Para ~2 min |
|---|---|---|
| Skill oficial Higgsfield | **10 s fijos**. `N = minutos × 6` | **12 planos** |
| [scriptable.com](https://scriptable.com/posts/higgsfield/youtube-video-from-script/) | 10 s; locución de 8–9 s (~20–24 palabras) centrada en el bloque | 12 bloques |
| [@NabhaniMehdi, 14 nov 2026](https://x.com/NabhaniMehdi/status/2121542488548610177) | “keep each shot **under 5 seconds**. Stitched short shots look far more epic than one long generation.” | no da el recuento para 2 min |
| [@humzaakhalid](https://x.com/humzaakhalid/status/2059152604442267813) | 3 escenas de **5 s** en un TikTok de 15 s | no escala a 2 min |
| [@johnvirality, 8 jun 2026](https://x.com/johnvirality/status/2063975263206080945) | “full **6-shot** video” (UGC, no 2 min) | - |
| [@AtamanshaX](https://x.com/AtamanshaX/status/2121495792338776484) | motion design: **33 escenas en 45 s**; nota de corrección: “Don't keep the same scene for over 2 seconds.” | ritmo de ~1,4 s/escena, no aplicable 1:1 a video generado |
| [@aidarosgo3, 13 nov 2026](https://x.com/aidarosgo3/status/2121212229571981760) | Cinema Studio 4.0: “**30-second multi-shot** scenes” | - |
| Tutorial YouTube Vox-style | 6 clips de 10 s = 60 s | el de 2 min sería 12 |

Para un video de 2 minutos en el flujo Claude + Higgsfield explainer, **la cifra publicada es 12 planos de 10 s**. [@NabhaniMehdi](https://x.com/NabhaniMehdi/status/2121542488548610177) recomienda cortar por debajo de 5 s si el objetivo es “épico” al coser planos, no un explainer narrado.

**No encontré** un recuento publicado del tipo “para 2 minutos uso 24 planos de 5 s” en el combo Claude + Higgsfield + ElevenLabs.

---

## 4. Cómo sincronizan voz y video

Cuatro técnicas publicadas:

**1. Bloque fijo de 10 s (Higgsfield ensambla).**  
La skill genera N audios y N clips. El ensamblador deja cada bloque en exactamente 10 s: centra tomas cortas con silencio, acelera un poco las que se pasan (sin cambiar el tono), **no estira el video**. Subtítulos opcionales: 0,05 créditos por bloque, fuentes `patrick / caveat / marker / anton`. ([skill](https://skillselion.com/skills/higgsfield-ai/skills/higgsfield-video-explainer); [scriptable.com](https://scriptable.com/posts/higgsfield/youtube-video-from-script/))

**2. Voz primero, luego corte a las marcas de tiempo.**  
[@facelesslaunchp, 14 nov 2026](https://x.com/facelesslaunchp/status/2121612756658909426): ElevenLabs → TurboScribe “so claude code has a timestamp for every line” → Higgsfield genera las imágenes desde esa locución fechada.  
[Talentdu, 24 ago 2026](https://www.talentdu.com/blogs/ai-video-ads-higgsfield-elevenlabs-capcut) (Higgsfield + ElevenLabs + CapCut): “Lay the voice down first, then cut the clips to it; the words set the rhythm.” Locución a ~2–3 palabras por segundo.

**3. Whisper / word timestamps y el video se cuelga de las palabras.**  
[@caesarscales, 9 nov 2026](https://x.com/caesarscales/status/2119851324284240009): Claude pide la API de ElevenLabs → ffmpeg recorta silencios → Whisper anota cada palabra → todo lo demás se temporiza a esas marcas.  
[@gebermudez, 14 nov 2026](https://x.com/gebermudez/status/2121636272632426972): un audio de ElevenLabs **por escena**; Claude mide si la frase cabe; si no cabe, acorta el texto sin cambiar el sentido. Remotion, cada escena es código.  
[@sleepclip, 10 nov 2026](https://x.com/sleepclip/status/2119975673662194100) y [@finnardley, 8 nov 2026](https://x.com/finnardley/status/2119332592814067932): endpoint de timestamps de ElevenLabs; `S('exact words', fn)` arranca el plano 0,08 s antes de esa frase; no acelerar con `atempo` (“it sounds chipmunked”).  
[@0kncn, 11 nov 2026](https://x.com/0kncn/status/2120470513378017789): cada línea de locución empieza 12 frames después del plano y debe terminar 12 frames antes; si se pasa, **acortar el texto y regenerar, no acelerar el audio**.

**4. Lip-sync medido al audio (cine, no explainer).**  
[@sarit69976, 13 nov 2026](https://x.com/sarit69976/status/2121225309336875109): “Lip sync: measure where each line starts and ends in the audio, and build the shot to exactly those bounds.” Voces: ElevenLabs. Planos: Higgsfield entre otros.

---

## 5. Consistencia visual entre planos

Lo que se publica, en este orden de frecuencia:

1. **Una sola imagen de estilo (`style key`) enganchada a todos los clips.** Skill oficial: “Attach the same style-key image to every clip.” [scriptable.com](https://scriptable.com/posts/higgsfield/youtube-video-from-script/): el job id de esa imagen va como referencia en cada generación. Tutorial Vox-style: “Generate ONE style key image first… and attach it to every clip so all six match” ([YouTube, 30 jul 2026](https://www.youtube.com/watch?v=_fNOdvr3Wrc)).
2. **El mismo descriptor STYLE + NEGATIVE en cada prompt.** Skill: repetir “non-photorealistic, illustrated, not a photo, no live-action, no realism”.
3. **Character sheets como fuente, nunca frames del propio film.** [@sarit69976, 13 nov 2026](https://x.com/sarit69976/status/2121225309336875109): “Character sheets are the source, never frames from the film. They go into every generation as reference.” “Lock the first frame of every shot so it joins the previous one without a jump.” “Never patch with masks. Regenerate the shot.”
4. **Una foto héroe y editar encima, no regenerar.** [@PrajwalTomar_, 13 nov 2026](https://x.com/PrajwalTomar_/status/2121218794903552069): “make ONE hero shot, then edit it… Don't keep regenerating... you'll never get the same logo twice.” Brand doc primero; el logo final se sube para empaquetado.
5. **Referencia de personaje + estilo en ChatGPT Images** para recurrentes: [@facelesslaunchp](https://x.com/facelesslaunchp/status/2121612756658909426).
6. **Imagen de referencia + voz de narrador guardadas** para episodios: [@OBAxbt, 10 nov 2026](https://x.com/OBAxbt/status/2120083098893230564) (flujo Zinho + Claude + Higgsfield).
7. **Start/end frames** por plano: [Talentdu](https://www.talentdu.com/blogs/ai-video-ads-higgsfield-elevenlabs-capcut).
8. **Misma descripción de personaje pegada en cada sheet** + devolver el base sheet: [@sleepclip](https://x.com/sleepclip/status/2119975673662194100) / [@finnardley](https://x.com/finnardley/status/2119332592814067932).

**No encontré publicaciones que recomienden semilla (seed) numérica para Higgsfield.** La palanca que sí nombran es la imagen de referencia + el mismo texto de estilo.

---

## 6. ElevenLabs en español: modelo, estabilidad, similitud, velocidad, tipo de voz

**No encontré ninguna publicación de los últimos 6 meses que dé números de stability / similarity / speed pensados específicamente para narración en español** en este flujo. Lo que hay son ajustes de narración en general, y consejos de doblaje al español.

**Ajustes publicados (no etiquetados como “para español”):**

| Autor | Modelo | Stability | Similarity | Style | Speed | Voz |
|---|---|---|---|---|---|---|
| [@AtamanshaX, 14 nov 2026](https://x.com/AtamanshaX/status/2121495792338776484) | Eleven **v4** | **0.4** | - | - | - | library “Ryu - Characters”; **una sola toma** de todo el guion |
| [@sleepclip](https://x.com/sleepclip/status/2119975673662194100) / [@finnardley](https://x.com/finnardley/status/2119332592814067932) | **eleven_v4** | **0.5** | **0.75** | **0** | **1.0–1.1** (el speed de la voz, no `atempo`) | “deep warm US documentary”; speaker boost; timestamps |
| [@MethodByVid, 13 nov 2026](https://x.com/MethodByVid/status/2121381202561278374) | **Multilingual v2** | - | - | - | forzar el guion traducido a **65–72 palabras / 28 s** | la misma voz inglesa hablando alemán/noruego/holandés |
| [@0kncn, 11 nov 2026](https://x.com/0kncn/status/2120470513378017789) | **v4** | - | - | - | **no acelerar**; acortar texto | “calm, low, documentary male”; audicionar varias voces en la línea 1 |
| [@facelesslaunchp](https://x.com/facelesslaunchp/status/2121612756658909426) | - | **“leave the settings alone”** | | | | voz cercana a la del competidor |

**Español, lo que sí se dice:**

- [@EvanCarmichael, 13 nov 2026](https://x.com/EvanCarmichael/status/2121370671196627154): “ElevenLabs is the best one for voice cloning and it's really good for Spanish.” Recomienda clonar tu propia voz y un segundo canal con el texto en pantalla también en español.
- Tutorial de doblaje ([YouTube, 5 nov 2026](https://www.youtube.com/watch?v=JJwFMPrc3wM)): en el prompt de traducción hay que **declarar el género de quien habla**, porque el español marca género y el modelo cae en masculino. Corregir la tabla de palabras **antes** de generar audio.
- Tutorial Vox-style Claude + Higgsfield: versión en español = **mismos clips, locución nueva** ([YouTube, 30 jul 2026](https://www.youtube.com/watch?v=_fNOdvr3Wrc)).
- La skill de Higgsfield usa **Seed Audio propio**, no ElevenLabs, y deja elegir idioma de narración (inglés por defecto).

**Inferencia mía, no citada:** el 0.5 / 0.75 / style 0 de los prompts de explainer en código es el paquete más repetido para narración documental; el 0.4 de Atamansha es para una voz de personaje con gritos. Nadie lo midió en castellano en las publicaciones que vi.

---

## 7. Errores a evitar

De las mismas publicaciones:

- **Saltar el brief.** Hamza: “Skip it, and your video is random.”
- **Meter voz dentro del clip de Higgsfield.** Skill: “Keep all spoken words out of video generation… no dialogue, lip-sync, or baked narration.” El audio del plano es ambiente.
- **Un plano largo en vez de varios cortos.** [@NabhaniMehdi](https://x.com/NabhaniMehdi/status/2121542488548610177); Talentdu: “One shot per generation.”
- **Regenerar el héroe/logo cada vez.** [@PrajwalTomar_](https://x.com/PrajwalTomar_/status/2121218794903552069): no vas a recuperar el mismo logo.
- **Parchear con máscaras.** [@sarit69976](https://x.com/sarit69976/status/2121225309336875109): regenerar el plano.
- **Usar frames del propio video como referencia de personaje.** Misma fuente: las character sheets son la fuente.
- **Acelerar la locución para que quepa.** [@finnardley](https://x.com/finnardley/status/2119332592814067932), [@0kncn](https://x.com/0kncn/status/2120470513378017789): suena a ardilla; acortar el texto.
- **Frases cortas con punto en ElevenLabs.** [@caesarscales](https://x.com/caesarscales/status/2119851324284240009): el punto resetea la voz y deja un hueco; unir con comas.
- **Recortar por timestamps de Whisper dentro de una palabra.** Caesar: recortar solo silencio, con un pequeño margen.
- **Quemar subtítulos en inglés si luego pones otra pista de audio.** [@MethodByVid](https://x.com/MethodByVid/status/2121381202561278374): en pantalla solo cifras, años, marcas; la frase la lleva la voz.
- **Traducir al español sin marcar género.** [Tutorial de doblaje](https://www.youtube.com/watch?v=JJwFMPrc3wM).
- **Foto sucia de producto.** Hamza: “Clean photo in = clean video out.”
- **Katana yendo a “AI footage” (créditos) cuando querías motion design.** [@AtamanshaX](https://x.com/AtamanshaX/status/2121495792338776484): no uses video de gente filmada como referencia; di “No generation. Motion design in code only, 0 credits.”
- **Manos, etiqueta del producto que cambia, hold estático.** [@TechneoFest, 13 nov 2026](https://x.com/TechneoFest/status/2121246972313301350): un anuncio de 20 s puede llevar 2–3 h por “one weird hand, a changing product label.”
- **Inventar datos en un explainer.** Skill Higgsfield: investigar antes; no inventar citas, fechas ni números.
- **Devolver clips sueltos** en vez de ensamblar. Skill: “Returning loose clips is a failure.”

---

## 8. Capturas / grabaciones reales de un producto de software + planos generados

**No encontré un flujo publicado, con prompts y orden, que mezcle screencasts de un SaaS con planos de Higgsfield.** Las prácticas más cercanas:

- [@justonedev, 8 nov 2026](https://x.com/justonedev/status/2119397119190499659): explainer de producto **sin grabar la pantalla**. La UI es una página web con `seek(t)`, Chrome headless para los frames, ffmpeg para el sonido, ElevenLabs para la voz. Write-up: [dev.to](https://dev.to/justonedev/how-to-create-a-cool-looking-explainer-video-for-anything-in-5-minutes-519p).
- [@facelesslaunchp](https://x.com/facelesslaunchp/status/2121612756658909426): Higgsfield para imágenes de escena; **el metraje real lo monta un editor humano** con el video del competidor como brief.
- [@ugc_sarahd, 14 nov 2026](https://x.com/ugc_sarahd/status/2121638992131117252): Claude hace motion graphics; “Now it’s just **screen recording inserts** from here adding my humanness.” No menciona Higgsfield.
- [@JamesonCamp, 14 nov 2026](https://x.com/JamesonCamp/status/2121636926574960865): “all image choices, motion graphics, **screen recording**, edits, and coloring are all 100% done by Claude.” Tampoco Higgsfield.
- [@AtamanshaX](https://x.com/AtamanshaX/status/2121495792338776484): fotos reales del producto (hasta 5) como **únicas imágenes**; Katana dibuja tipo, UI cards y cámara en código alrededor. Eso sirve para packshots, no para un flujo de app.
- Talentdu: en CapCut, “B-roll where a shot feels static” después de poner la voz.

**Inferencia mía:** el hueco está vacío en X. El patrón que se deja ver es: locución + planos Higgsfield (o motion code) como B-roll, y las capturas del software se insertan en el editor (CapCut / Claude+ffmpeg) cortadas a las mismas marcas de tiempo. Nadie publicó el prompt de ese corte.

---

## 9. Tiempo y coste

Cifras que sí aparecen:

| Qué | Cuánto | Quién / cuándo |
|---|---|---|
| Clip Higgsfield 10 s, `gemini_omni` 720p | **30 créditos** | [scriptable.com, jul 2026](https://scriptable.com/posts/higgsfield/youtube-video-from-script/) |
| Toma Seed Audio (voz Higgsfield) | **0,4 créditos** | misma guía |
| Video de 30 s (3 bloques) | ~**90 créditos** de clips + ~1,2 de voz + 1 style key. Ensamblaje gratis. Subtítulos 0,05/bloque | misma guía. Dice: un video de 2 min son **12 bloques**, no 3 |
| Explainer Vox-style 60 s, 6 clips, + versiones ES/PT | **200 créditos** | [YouTube, 30 jul 2026](https://www.youtube.com/watch?v=_fNOdvr3Wrc) |
| Video de **2:30** en Higgsfield | **300 créditos**, **6 horas** (lo más largo: el guion) | [@Zetetzone, 14 nov 2026](https://x.com/Zetetzone/status/2121612726640185761) |
| Tests de AI footage Katana | **218 y 385 créditos** | [@AtamanshaX, 14 nov 2026](https://x.com/AtamanshaX/status/2121495792338776484) |
| Mismo anuncio en motion design (código) | **0 créditos**; 8 s / 5,5 min de render; **41 min** mensaje→MP4 | Atamansha |
| Identidad de marca (imágenes) | **24 créditos** Higgsfield | [@PrajwalTomar_](https://x.com/PrajwalTomar_/status/2121218794903552069) |
| Plan Higgsfield | **850 € / 2 años, 8.000 créditos al mes** | [@OseilleTV, 14 nov 2026](https://x.com/OseilleTV/status/2121642231022981392) |
| 10 s 720p, precio de lista Higgsfield vs Sume | **4,62 $ vs 2,31 $** | [@Aria_Nawi, 12 nov 2026](https://x.com/Aria_Nawi/status/2120896948660056085) |
| Anuncio de 20 s | **2–3 horas** por regeneraciones | [@TechneoFest, 13 nov 2026](https://x.com/TechneoFest/status/2121246972313301350) |
| 15–25 videos UGC al día | **3–4 horas** (ads de 6 planos, no 2 min) | [@johnvirality, 8 jun 2026](https://x.com/johnvirality/status/2063975263206080945) |
| Explainer en código, 1 min / 3 min | ~12 imágenes **~0,50 $** / ~25 imágenes | [@sleepclip](https://x.com/sleepclip/status/2119975673662194100) |
| ElevenLabs | “per character of voice”; “cheap plans” y créditos gratis | [@ellypromtstar, 12 nov 2026](https://x.com/ellypromtstar/status/2120757745737506843); [@Devon8zzh, 14 nov 2026](https://x.com/Devon8zzh/status/2121667355004793011) |
| VO ElevenLabs de un short | **~1.000 créditos** (Short) o **0,10 $** vía Calliope | [@caesarscales](https://x.com/caesarscales/status/2119554953018773795); [@seergioo_gil, 8 nov 2026](https://x.com/seergioo_gil/status/2119239985576779874) |
| Render Remotion local | **~18 s** por versión de 32 s | [@gebermudez](https://x.com/gebermudez/status/2121636272632426972) |

**Inferencia mía a partir de la tarifa de scriptable, no una publicación:** 12 clips × 30 = 360 créditos de video + ~5 de voz Higgsfield para 2 minutos, **si no hay reintentos**. Zetet gastó 300 en 2:30 “using as few credits as possible”, así que el rango real de 2 min está alrededor de 300–400 créditos si el primer render sale, y sube con cada plano malo (Atamansha: 218–385 ya en tests de footage).

---

## Cómo encaja el combo que pediste

Las tres herramientas aparecen juntas en X, pero **casi nunca como un tutorial de producto de software de 1–3 min**. El mapa real es:

- **Claude** escribe guion, storyboard, prompts, y a menudo monta con Remotion/ffmpeg/CapCut ([@RaulReyeszumeta](https://x.com/RaulReyeszumeta/status/2121592919748456914), [@gebermudez](https://x.com/gebermudez/status/2121636272632426972), [@caesarscales](https://x.com/caesarscales/status/2119851324284240009)).
- **Higgsfield** genera imagen/video, o (skill oficial) el explainer entero con su propia voz Seed Audio.
- **ElevenLabs** entra cuando el autor quiere una voz de librería/clon, no la de Higgsfield ([@facelesslaunchp](https://x.com/facelesslaunchp/status/2121612756658909426), [@AtamanshaX](https://x.com/AtamanshaX/status/2121495792338776484), [@quietwolfz, 14 nov 2026](https://x.com/quietwolfz/status/2121672158569230687), [@ReStructureAI, 13 nov 2026](https://x.com/ReStructureAI/status/2121292792072896843)).

Si tu caso es un explainer de 2 minutos de un producto de software, lo más cercano a un procedimiento publicado es: skill de Higgsfield con **12 bloques de 10 s, prompts en inglés, locución en español, style key única, voz primero**; y las capturas reales de la app **no están documentadas en ese skill** (está pensado para explainers no fotorrealistas). Para meter UI real, las pistas sueltas son CapCut/Claude cortando a la pista de ElevenLabs, o saltarse Higgsfield y animar la UI en código como [@justonedev](https://x.com/justonedev/status/2119397119190499659).

