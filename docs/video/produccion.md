# Cómo se produjo el video (Claude + Higgsfield + ElevenLabs)

> **Versión que quedó en el repositorio:** voz de sistema de macOS (Paulina, es_MX), sintetizada en local con `say`; dura 1:51,2. Los tiempos exactos de cada frase están en `tiempos.tsv`. La primera versión usó una voz del catálogo de ElevenLabs de categoría "professional" (la voz de una persona real que la licencia) y se descartó por la regla "nada de voces, rostros ni correos de personas reales". Lo que este documento dice de ElevenLabs y los tiempos de sus tablas describen esa primera versión (1:58,5); el guion, las cifras, las capturas y los planos son los mismos.

El flujo sale de la investigación con Grok (`investigacion-grok.md`). Las publicaciones se citan como las dio Grok: no se abrieron una por una, así que valen como "según Grok".

## Qué dice la investigación y qué se hizo

| Paso | Qué recomiendan las publicaciones | Qué se hizo aquí |
|---|---|---|
| Orden | Guion, estilo, voz, marcas de tiempo, planos y montaje. La voz va antes que el video (skill oficial de Higgsfield; @facelesslaunchp; @AtamanshaX) | Igual: guion, voz de ElevenLabs con marcas de tiempo, animación colgada de esas marcas |
| Sincronía | Pedir las marcas de tiempo a ElevenLabs y colgar cada plano de las palabras (@sleepclip, @finnardley, @caesarscales); un audio por escena y acortar el texto si no cabe (@gebermudez, @0kncn) | Una toma por escena con el endpoint `with-timestamps`; cada animación arranca en la frase que la nombra (`tiempos.tsv`) |
| No acelerar el audio | Acortar el texto y regenerar; `atempo` fuerte suena mal (@finnardley, @0kncn) | Se acortó el guion (de 297 a 266 palabras) y se subió `speed` a 1.2. Aun así faltaban 3 s y se aplicó un `atempo` de 1.05: es una desviación pequeña de la recomendación y se dice |
| Ajustes de voz | `eleven_v4`, stability 0.5, similarity 0.75, style 0, speed 1.0 a 1.1 (@sleepclip, @finnardley). Ninguna publicación da números pensados para español | `eleven_v4`, 0.5, 0.75, 0, speaker boost, speed 1.2 |
| Prompts de Higgsfield | En inglés; un bloque con escena, movimiento y negativos; nada de voz ni texto dentro del clip (skill oficial de Higgsfield; scriptable.com) | Tres prompts en inglés con una línea de estilo común y negativos (sin personas, texto ni logos); el texto se monta encima |
| Duración por plano | Bloques de 10 s en la skill oficial; planos de menos de 5 s si se cosen (@NabhaniMehdi) | Tres planos de 8, 5 y 6 s como apertura, transición y cierre |
| Consistencia | Una imagen de estilo única adjunta a cada clip y el mismo descriptor de estilo (skill oficial; scriptable.com). Nadie recomienda semilla | Solo el mismo descriptor de estilo; con tres planos bastó |
| Producto real junto a planos generados | No hay un flujo publicado. Lo más cercano: animar la interfaz como página web con `seek(t)`, Chrome sin cabeza para los fotogramas y ffmpeg (@justonedev) | Ese camino: la animación es una página con `seek(t)`, las capturas son de la interfaz real y Chrome sin cabeza saca cada fotograma |
| Errores a evitar | Inventar datos; devolver clips sueltos; meter subtítulos de frases que la voz no dice | Cada cifra tiene su fuente (`guion.md`); se entrega un MP4 montado; en pantalla solo va lo que la voz dice o su denominador |

## Paso a paso para rehacerlo

1. **Guion.** Una escena por archivo en `escenas/eNN.txt`, una frase por línea, números en letras.
2. **Voz.** Con la key en el entorno (no se escribe en ningún archivo del repo):
   `VOZ_VELOCIDAD=1.2 python3 animacion/voz_elevenlabs.py <voice_id> eleven_v4`
   Deja `voz/eNN.mp3` y `voz/eNN.json` (inicio y fin de cada frase). Para regenerar solo una escena se añade su número al final (por ejemplo `08`).
3. **Capturas.** Arrancar la interfaz en local (`python -m quorum.ui.server <puerto>`, escucha en 127.0.0.1 y no pide key en modo guionado), cargar "Ejemplos de texto", correr "Honestos" y "k=3" con "Quórum activa" y capturar. Las de este video están en `capturas/ui/`, con las coordenadas de lo que se resalta en `meta.json`.
4. **Planos generados.** Con el CLI de Higgsfield, consultando antes el costo:
   `higgsfield generate cost seedance_2_5 --prompt "..." --mode t2v --duration 5 --resolution 720p --aspect_ratio 16:9`
   y luego `higgsfield generate create seedance_2_5 ... --generate_audio false --wait`. Los MP4 van en `planos/gN.mp4`, sus fotogramas en `planos/gN/` y la lista en `planos/clips.js`.
5. **Montaje.** `PUPPETEER_DIR=<carpeta con puppeteer-core> VOZ_TEMPO=1.05 VOZ_NOMBRE="ElevenLabs, voz Camila ES, modelo eleven_v4" ./montar.sh quorum-video.mp4`
   Arma la pista de voz y `animacion/timeline.js`, saca los 3554 fotogramas con Chrome sin cabeza y los une con ffmpeg. Se detiene con error si el resultado pasa de 120 s. Sin tomas en `voz/` usa la voz de macOS, y sin `planos/clips.js` usa una apertura animada en código.
6. **Revisión.** Pasarle el MP4 completo a `agy` y corregir lo que sea cierto (`revision-agy.md`).

Para ver la animación sin renderizar: abrir `animacion/index.html?play=1` en Chrome, o `?t=60` para un instante.

## Cuánto tardó y cuánto costó

| Concepto | Este video | Lo que dicen las fuentes |
|---|---|---|
| ElevenLabs | 3508 caracteres en total: una prueba de 137, una pasada completa de 1650, otra de 1563 con el guion recortado y 158 para rehacer la escena 1 | "per character of voice" (@ellypromtstar); alrededor de 1000 créditos por un corto (@caesarscales) |
| Higgsfield | 133 créditos: 56 (8 s), 35 (5 s) y 42 (6 s), a 720p con Seedance 2.5. Los tres salieron a la primera | 30 créditos por clip de 10 s a 720p con otro modelo (scriptable.com); 300 créditos y 6 horas por un video de 2:30 (@Zetetzone) |
| Generación de los planos | Entre 2 y 4 minutos, los tres en paralelo | Un anuncio de 20 s puede llevar de 2 a 3 horas por regeneraciones (@TechneoFest) |
| Render | 2 minutos y 15 segundos para 3554 fotogramas con 8 pestañas en paralelo | 5,5 minutos de render para 8 s de motion design (@AtamanshaX) |
| Animación en código | 0 créditos | "0 credits" para motion design en código (@AtamanshaX) |

## Qué mejoraría con más tiempo

- Una imagen de estilo única para los planos generados y un cuarto plano para la escena de la compuerta.
- Regenerar la voz con el guion recortado otro 4 % para no necesitar el `atempo` de 1.05.
- Grabar la interfaz con el motor de modelo (necesita una key de OpenRouter) además del guionado.
