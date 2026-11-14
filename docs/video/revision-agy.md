# Revisión del video con agy

`agy` vio el video completo, con imagen y audio, las dos veces (él mismo lo dice en el punto 1 de cada revisión). No hizo falta pasarle fotogramas sueltos. Se le pasó el MP4 en una carpeta vacía con `agy --print "<pregunta>"`, sin datos del equipo en la pregunta.

Las respuestas van tal como las devolvió, con un solo cambio mecánico: las rayas largas se sustituyeron por un guion corto.

## Qué se corrigió y qué no

### Primera revisión (borrador de láminas fijas con la voz de macOS)

| Observación de agy | Qué se hizo |
|---|---|
| "0 de 1000" bajo "Bloquea de más" se lee al revés de lo que dice la voz | Cierto. Ahora dice "1000 de 1000 trámites honestos descuidados quedan detenidos" |
| En el cierre, "0 de 60 trámites honestos" sin "bloqueados" | Cierto. Corregido |
| "0 de 30" del monitor frente a "0 de 60" de la compuerta, sin explicar | Cierto que confunde; la cifra es correcta. Se añadió el pie: los umbrales se calibran con la mitad de los honestos y los falsos positivos se miden en los otros 30 |
| No se entiende por qué el rival recupera el monto | Cierto. La tarjeta ahora dice que el pliego publica los puntajes, que la fórmula es conocida y que la compuerta no lo impide |
| Jerga: "M1", "M2 sin oráculo", "buen harness", "k" | Cierto. Se quitaron; ahora "Monitor LLM por agente" y "Mínimo privilegio por rol" |
| Capturas cortadas, letra pequeña y poco tiempo | Cierto. Se rehicieron las capturas por bloques, más grandes, con la cámara moviéndose sobre la página |
| La voz y el cambio de lámina no coincidían en 0:17 y 0:37 | Cierto. Ahora cada animación arranca en la marca de tiempo de su frase |
| "No tiene umbral" en pantalla sin que la voz lo diga | Cierto. Se quitó |
| Notas al pie pequeñas y con poco contraste | Cierto. Más grandes y más claras; se quitaron las cifras que la voz no nombraba |
| Errata "agents" en la portada | Falso: la lámina decía "agentes". No se cambió nada |
| La voz de macOS pronunciaba mal "AgentDojo" | Cierto. La voz final es la de ElevenLabs, que lo pronuncia bien |

### Segunda revisión (video animado con voz de ElevenLabs y planos de Higgsfield)

| Observación de agy | Qué se hizo |
|---|---|
| El recuadro de la política tapaba las etiquetas bajo Evaluador y Publicador (0:29 a 0:34) | Cierto. Se bajó el recuadro |
| Los rótulos flotantes tapaban partes de la captura (0:41 a 0:46) | Cierto. Los rótulos pasaron a la franja de arriba, fuera de la captura |
| No se alcanzaba a ver resaltado el Publicador | Cierto. Evaluador y Publicador se resaltan antes y duran más |
| La nota de AgentDojo ("los 15 que escapan") salía tarde y con poco contraste | Cierto. Sale antes y en un gris más claro |
| "IA" suena pegado en 0:08 | Cierto. La escena 1 ahora dice "inteligencia artificial" |
| "El corte principal" no se entiende | Cierto. Ahora dice "la prueba principal" |
| Los rótulos de las capturas llegaban cuando la voz ya había terminado | Cierto. Se adelantaron |
| Líneas cortadas en los bordes al desplazar la captura | Cierto, y se queda así: es el desplazamiento de una página real |
| La interfaz mezcla inglés ("Saved.", "BLOCKED by policy") con español | Cierto, y se queda así: es la interfaz real; cambiarla es tocar el código del producto |
| "Radicar" puede no entenderse fuera de Colombia | Se deja: la tarjeta dice "Registra las ofertas" |
| El intervalo de confianza pasa rápido | Se deja como pie: quitarlo haría sonar el 16 de 16 más fuerte de lo que es |

Después de estas correcciones se cambió también el cierre: decía "sin voces ni rostros de personas reales" y ahora dice "sin rostros ni datos de personas reales; la voz es sintética, de catálogo", que es lo exacto.

### Tercera pasada (video ya corregido)

Se le pasó el video corregido para confirmar los arreglos, pero `agy` agotó su tiempo límite de 7 minutos sin devolver respuesta. Los arreglos de la segunda revisión se comprobaron mirando fotogramas del video final en los segundos 33, 41, 44, 47, 52, 94, 109 y 117: el recuadro de la política ya no tapa las etiquetas, los rótulos están fuera de la captura, Evaluador y Publicador quedan resaltados, el contador llega a 1506 mientras la voz lo dice y el cierre trae el texto nuevo. Lo que no se pudo volver a comprobar con oído ajeno es la frase rehecha de la escena 1 ("inteligencia artificial"); conviene escucharla una vez.

## Primera revisión, respuesta de agy

### 1. Qué pude hacer (con honestidad)
Pude abrir y analizar el archivo `video.mp4` **completo (de `00:00` a `01:56`) tanto con su pista de audio íntegra como con su secuencia completa de imagen** (a razón de un fotograma por segundo, cubriendo las 13 láminas y capturas de pantalla de principio a fin).

---

### 2. ¿Se entiende sin contexto previo? ¿Qué parte no se entiende?
**La tesis central sí se entiende sin contexto previo:** queda claro el caso de uso (una licitación pública con tres agentes: Radicador, Evaluador y Publicador), el riesgo (si un ataque se reparte entre varios agentes, ningún paso individual parece malicioso y el valor sellado se filtra) y el funcionamiento de Quórum (etiquetado determinista de procedencia o *taint tracking*, donde cada salida hereda las etiquetas de lo que el agente leyó y una compuerta bloquea según una política sin llamar a ningún LLM).

**Lo que NO se entiende sin contexto previo:**
1. **La fuga matemática a través de los puntajes (`01:33–01:49`, 3.ª tarjeta: *"No cierra lo que se publica: 50 de 50 veces un rival externo recupera el monto con los puntajes publicados"*):** Para un jurado que no conoce el proyecto, esto resulta desconcertante. Nunca se explicó cómo se calculan los puntajes (presumiblemente con una fórmula proporcional al precio ofertado) ni **por qué los puntajes pudieron publicarse sin heredar la etiqueta `sealed.bid-2`** si el Evaluador tuvo que leer las ofertas selladas para calcularlos. Parece contradecir la regla de `00:22` (*"lo que escribe un agente hereda las etiquetas de lo que leyó"*), porque falta aclarar que el puntaje es un dato agregado cuya publicación sí está autorizada por la política (desclasificación parcial) y que eso abre un canal lateral.
2. **La diferencia entre «modo guionado / agentes con guion» y «agentes de modelo» (`00:35–00:51`, `00:52`, `01:19`):** En la demostración se ve un cartel fijo que dice `MODO GUIONADO`, luego en `00:52` se pasa a `90 trámites con agentes de modelo` y en `01:19` a `agentes con guion`. Un jurado externo no sabe de entrada si la interfaz mostrada ejecuta agentes reales o una reproducción pregrabada/simulada, ni por qué se separan ambas evaluaciones.
3. **Jerga interna no explicada en pantalla:**
   - **`M1` y `M2 sin oráculo` (`01:07–01:18`):** En la nota al pie se menciona `M2 sin oráculo` frente a `M1` sin definir qué es el "oráculo" en este experimento ni qué diferencia a M1 de M2.
   - **`Buen harness: 3200 de 7600` (`01:19–01:32`):** No se explica qué defensas incluye ese "buen harness" ni por qué falla exactamente en la misma proporción que el filtro de coincidencia exacta (`3200 de 7600`).
   - **`k = 1, 2, 3` (`00:18`, `00:35`, `00:42`):** En `00:42` el subtítulo dice `Tres agentes desviados (k = 3)`, pero el significado de `k` solo apareció en una nota al pie diminuta en `00:18`.

---

### 3. ¿La voz y la imagen van sincronizadas?
En términos generales, cada lámina coincide con su bloque de narración, pero hay cuatro desajustes concretos:

- **`00:17 – 00:18`:** La narración empieza a decir *"Si el ataque se reparte..."* en el segundo `00:17`, cuando en pantalla todavía está la lámina 2 (*"EL CASO: Tres agentes tramitan..."*). La lámina 3 (*"EL ATAQUE REPARTIDO"*) recién entra en `00:18`.
- **`00:30 – 00:34`:** En la lámina 4 (*"La etiqueta viaja con el dato"*), la fila inferior muestra tres cajas grandes: `No lee el texto`, `No llama a ningún modelo` y `No tiene umbral`. La voz menciona las dos primeras, pero ignora por completo `No tiene umbral`, dejando al jurado preguntándose a qué umbral se refiere.
- **`00:37 – 00:38`:** La voz arranca la frase *"En un trámite honesto..."* en `00:37` mientras sigue en pantalla la captura inicial vacía de la interfaz (lámina 5); el cambio a la captura con el resultado del trámite honesto ocurre recién en `00:38`.
- **`01:34 – 01:40`:** Mientras la voz dice *"Bloquea siempre el trámite honesto descuidado"*, la vista se dirige a la primera tarjeta que tiene en gigante un **`0 de 1000`**, generando un choque inmediato entre lo que se oye ("siempre" = 100 %) y el cero gigante que se ve en pantalla (ver punto 7).

---

### 4. ¿Algún texto en pantalla se corta, se sale del cuadro o no se lee?
Sí, hay cortes evidentes en las capturas de la interfaz y textos demasiado pequeños:

- **Textos cortados / mutilados en los bordes:**
  - **`00:38 – 00:41` (Lámina 6, trámite honesto):**
    - **Borde superior:** Las columnas de los agentes están recortadas a mitad de texto. A la izquierda se corta el inicio de `read_annex({"ident":"anexo-2"})` y en la columna central aparece un JSON cortado por la mitad (`Suministros SAS":"bid-1","Ferrelectro del Sur Ltda":"bid-2"...`).
    - **Borde inferior:** Justo encima del zócalo azul (`CAPTURA REAL · MODO GUIONADO`), la línea `Adjudicación esperada: Ferrelectro del Sur Ltda` queda pegada al borde y casi mordida por la barra inferior.
  - **`00:42 – 00:47` (Lámina 7, tres agentes desviados):**
    - **Borde inferior:** El zócalo azul corta abruptamente las tarjetas de los tres agentes. En la columna izquierda (`Radicador`), el texto de la oferta queda cortado a mitad de oración: `...suministro de equipos de cómputo. Cinco`.
  - **`00:48 – 00:51` (Lámina 8, salida bloqueada):**
    - **Borde superior:** Se vuelve a cortar el contenido de las columnas de arriba: a la izquierda asoma `cómputo. Plazo de...` cortado y en el centro `408915720.","key":"evaluation.context"})` truncado a mitad de línea.
- **Textos que no se leen bien por tamaño o contraste:**
  - **`00:35 – 00:51` (Láminas 5 a 8):** Dentro de las capturas de la aplicación web, los textos secundarios (hashes como `prompt honesto fe9729b7aa6`, etiquetas `contexto público / no confiable: 3` y la nota explicativa bajo los botones en `00:35`) son demasiado pequeños para leerse al vuelo.
  - **Notas al pie (`00:10–00:34` y `00:52–01:56`):** Las líneas de fuente y notas metodológicas en la parte inferior izquierda tienen un tamaño muy reducido y un color gris azulado de bajo contraste sobre el fondo oscuro.

---

### 5. ¿El ritmo es bueno? ¿Alguna lámina dura demasiado poco o demasiado?
El ritmo de las láminas conceptuales (`00:00–00:09`, `00:22–00:34`, `00:52–01:06`) es bueno, pero **las capturas de la interfaz y un par de láminas densas duran demasiado poco**:

- **Demasiado cortas:**
  - **`00:35 – 00:37` (Lámina 5, interfaz inicial):** Dura **solo 3 segundos**. Es imposible que un jurado que ve la herramienta por primera vez lea las secciones `1 · OFERTAS`, `2 · CONFIGURACIÓN` y las tres columnas de agentes en 3 segundos.
  - **`00:38 – 00:41` (Lámina 6, resultado honesto):** Dura **4 segundos**. No da tiempo a leer los badges verdes ni el texto publicado en el portal.
  - **`00:48 – 00:51` (Lámina 8, resultado bloqueado):** Dura **4 segundos**. Tiene muchísima información visual (etiquetas rojas, mensaje de bloqueo, resultado vacío y texto tachado con el intento de fuga) para tan poco tiempo.
  - **`00:18 – 00:21` (Lámina 3, "Ningún paso aislado se ve raro"):** Dura **4 segundos** para leer cuatro cajas de flujo más una nota al pie.
- **Demasiado densas para su duración:**
  - **`01:07 – 01:18` (Lámina 10)** y **`01:19 – 01:32` (Lámina 11):** Duran 11 y 13 segundos, tiempo suficiente para leer la tabla o las cifras grandes, pero insuficiente para leer además los párrafos de letra pequeña al pie (como el caso de los 600 episodios de inyección en un anexo o la comparativa entre Gemini y Haiku).

---

### 6. ¿Hay errores de español (ortografía, tildes, concordancia) en la voz o en pantalla?
- **En pantalla:**
  1. **`00:00 – 00:09` (Portada, error tipográfico grave):** El subtítulo dice *"Una compuerta determinista de procedencia para sistemas de varios **agents**"*. Está escrito **`agents`** (en inglés / sin la «e») en lugar de **`agentes`**.
  2. **`01:50 – 01:56` (Lámina final, frase incompleta):** Bajo la URL de GitHub dice: `16 de 16 fugas bloqueadas · 0 de 60 trámites honestos · 0 llamadas a un modelo`. Falta la palabra **`bloqueados`** tras *«trámites honestos»* (en la lámina de `00:52` sí ponía *«0 de 60 trámites honestos bloqueados»*). Tal como quedó en el cierre, *"0 de 60 trámites honestos"* parece decir que ningún trámite honesto funcionó.
  3. **`00:48 – 00:51` (Lámina 8, mezcla de idiomas en la UI):** Toda la interfaz está en español salvo la línea del motor que sale en inglés: `Blocked: restricted sources not authorized for this destination: sealed.bid-2`.
- **En la voz:**
  1. **`01:28` y `01:41`:** La voz sintética (Paulina de macOS) lee **`AgentDojo`** con fonética literal española (`/a-xent-dó-xo/`, pronunciando la *g* y la *j* como jota castellana), lo cual suena antinatural y cuesta reconocer al oído.
  2. **`00:00`:** En el primer segundo del video, el ataque de la palabra **"Quórum"** suena ligeramente mordido/atropellado al comenzar la pista de audio.

---

### 7. ¿Alguna cifra en pantalla no cuadra con lo que dice la narración en ese momento?
1. **`01:34 – 01:40` (Lámina 12, tarjeta izquierda «Bloquea de más»):**
   - **Lo que dice la voz:** *"Bloquea **siempre** el trámite honesto descuidado: un agente que abre un sobre que no necesitaba."*
   - **Lo que dice la pantalla:** Título **`Bloquea de más`**, cifra gigante **`0 de 1000`** (*"trámites honestos descuidados terminan..."*).
   - **Discrepancia:** El título de la tarjeta (*"Bloquea de más"*) y la voz (*"Bloquea siempre"*) hablan de cuántos trámites se **bloquean** (1000 de 1000), pero la cifra en pantalla muestra **`0 de 1000`** porque cambió el verbo abajo a cuántos **terminan**. Además rompe la consistencia con las otras dos tarjetas de la misma lámina (`75 de 411` tareas detenidas y `50 de 50` fugas por puntaje), donde el numerador siempre representa el problema o costo.
2. **`01:07 – 01:13` (Lámina 10, tabla comparativa, columna «Honestos marcados»):**
   - **Lo que dice la voz:** *"Un monitor por agente también detecta las 16, sin falsos positivos..."*
   - **Lo que dice la pantalla:** En la columna `Honestos marcados`, el Monitor (M1) muestra **`0 de 30`**, mientras que justo debajo la Compuerta de Quórum muestra **`0 de 60`**.
   - **Discrepancia:** En la lámina anterior (`00:52`) se estableció que el banco de pruebas tiene **60 trámites honestos y 30 ataques**. Que el monitor marque `0 de 30` honestos en lugar de `0 de 60` deja una inconsistencia sin explicar (¿solo se corrió el monitor en la mitad de los casos honestos, o se puso `30` por error pensando en los 30 ataques?).

---

### 8. ¿Qué cambiarías? (De más a menos importante)

1. **Corregir el typo `agents` $\rightarrow$ `agentes` en la portada (`00:00–00:09`) y agregar `bloqueados` en la lámina final (`01:50–01:56`):**
   - En la primera lámina está el error más visible del video (*"sistemas de varios agents"*). En la última, cambiar `0 de 60 trámites honestos` por `0 de 60 trámites honestos bloqueados`.
2. **Unificar el sentido de la cifra en la tarjeta «Bloquea de más» (`01:33–01:49`):**
   - Cambiar **`0 de 1000`** (`trámites honestos descuidados terminan...`) por **`1000 de 1000`** (`trámites honestos descuidados bloqueados: si un agente abre un sobre que no necesitaba, no sale`). Así coincidirá con el título de la tarjeta (*"Bloquea de más"*), con la voz (*"Bloquea siempre..."*) y con el color naranja de alerta de las otras dos tarjetas de esa lámina.
3. **Aclarar en 1 frase por qué el puntaje se publica y permite inferir el monto (`01:33–01:49`):**
   - En la tercera tarjeta de `01:33` (*"No cierra lo que se publica"*), explicar que **la política autoriza publicar los puntajes** (desclasificación deliberada) y que Quórum controla la procedencia de las etiquetas, pero no el flujo de información matemático por canales laterales (*side-channel* cuantitativo). Sin ese matiz, parece un fallo de la propia regla de herencia de etiquetas.
4. **Arreglar el recorte de las capturas de interfaz y darles más tiempo o zoom (`00:35–00:51`):**
   - No mostrar la página cortada a mitad de un bloque JSON en el borde superior (`00:38` y `00:48`) ni a mitad de frase en el borde inferior (`00:42`). Hacer un recorte limpio encuadrando solo las 3 tarjetas de agentes en `00:42` y solo el bloque `3 · RESULTADO` (con zoom al 130–150 %) en `00:38` y `00:48`, extendiendo 2–3 segundos esas láminas para que el jurado alcance a leerlas.
5. **Explicar o corregir el `0 de 30` vs. `0 de 60` en la lámina del Monitor LLM (`01:07–01:18`):**
   - Si fue una errata al transcribir el denominador (confundiendo los 30 ataques con los 60 honestos), corregirlo a `0 de 60`. Si realmente solo se evaluaron 30 trámites honestos con el monitor por costo de API, aclararlo brevemente o quitar las dos líneas densas de texto inferior sobre `M2 sin oráculo` y los `600 episodios` que no se mencionan en el audio y distraen de la tabla.
6. **Ajustar la pronunciación de `AgentDojo` en el TTS y los adelantos de audio (`00:17`, `00:37`, `01:28`, `01:41`):**
   - En el guion que se pasa a la voz `Paulina` de macOS, escribir fonéticamente *"Éiyent Dóyo"* (solo en el archivo de texto para síntesis de voz) para evitar que diga `/a-xent-dó-xo/`, dejar 0,2 segundos de silencio al inicio de `00:00` para que no se muerda la palabra *"Quórum"*, y alinear el inicio del audio en `00:18` y `00:38` exactamente con el cambio de lámina.


## Segunda revisión, respuesta de agy

Aquí tienes la revisión completa y estricta de [video.mp4](video.mp4):

### 1. Qué pude hacer (con total honestidad)
**Vi y escuché el video completo de principio a fin (00:00 a 01:57.60), con imagen en movimiento y su pista de audio original completa.** Además, inspeccioné fotogramas clave a resolución nativa (1920×1080) para verificar pixel por pixel contrastes, recortes de texto y superposiciones en la interfaz.

---

### 2. ¿Se entiende sin contexto previo? ¿Qué parte no se entiende?
**Sí, la tesis central se entiende muy bien sin contexto previo.** En los primeros 34 segundos queda claro el problema (fuga de un dato confidencial repartida entre varios agentes para que ningún paso individual parezca sospechoso) y el mecanismo (propagación determinista de etiquetas de procedencia como `{sealed.bid-2}` y bloqueo en la compuerta de salida cuando `publish = []` sin invocar un LLM).

**Partes que no se entienden del todo sin contexto previo:**
- **00:15 y 00:35 (`"Radicador" / "Uno radica"`):** Para un jurado hispanohablante fuera de Colombia (donde *radicar* es el término estándar para registrar/ingresar formalmente documentos en una licitación), el término puede resultar poco familiar, aunque el subtítulo de la tarjeta (*"Registra las ofertas"*) ayuda a deducirlo.
- **00:35 y 01:21 (`"agentes con guion, sin modelo"` vs. `"agentes manejados por un modelo"`):** Para alguien externo no queda del todo claro por qué parte de la demostración y del banco de pruebas usa agentes con guion (*scripted*) si el riesgo real es entre agentes de IA, hasta leer la nota al pie en **01:21–01:34** (*"Sin modelo: mide el mecanismo, no la conducta de un modelo"*).
- **01:08 (`"Son 30 ataques con plantillas fijas: los intervalos son anchos (16 de 16: de 81 a 100 %, al 95 %)"`):** La nota al pie sobre el intervalo de confianza binomial aparece sin explicación oral y pasa rápido.
- **01:41–01:44 (`"En el corte principal conserva 16 de las 19 tareas que funcionan sin defensa"`):** No se explica qué es *"el corte principal"* de AgentDojo ni cómo se relaciona el `16 de 19` con el `75 de 411 tareas limpias detenidas` que encabeza la misma tarjeta.

---

### 3. ¿La voz y la imagen van sincronizadas?
En general **van muy bien sincronizadas**, salvo dos pequeños desfases en la sección de capturas de la interfaz:
- **00:40–00:41:** La voz termina de decir *"En un trámite honesto, la adjudicación se publica"* en el segundo **00:40**, y el segundo rótulo verde (`"La adjudicación sale al portal"`) aparece en **00:41**, ya en silencio.
- **00:45–00:46:** La voz termina de decir *"el valor sellado pasa de uno a otro"* alrededor de **00:45.2**, pero el recuadro y el rótulo rojo `"El Evaluador hereda la etiqueta"` recién aparecen en **00:45.5–00:46.8**, cuando la narradora ya está en pausa antes de la siguiente frase.

---

### 4. ¿Algún texto en pantalla se corta, se sale del cuadro o no se lee?
Sí, hay cortes y superposiciones concretas y un texto de bajo contraste:
- **00:29–00:34 (Texto tapado en el diagrama):** El cuadro explicativo (`Etiqueta de la salida {sealed.bid-2} / Política publish = []`) se superpone a las pastillas rojas `{sealed.bid-2}` situadas debajo de las cajas de **Evaluador** y **Publicador**, cortándolas horizontalmente por la mitad.
- **00:35–00:37 (Corte inferior de ventana):** En la parte inferior de la captura de la interfaz, las tres tarjetas (`Radicador`, `Evaluador`, `Publicador`) quedan cortadas justo por debajo de la primera línea de código (`read({"key":"terms.bids"})`).
- **00:38–00:40, 00:42–00:44 y 00:47–00:48 (Cortes por scroll de la captura):** Al hacer scroll dentro de la ventana de la interfaz, las primeras y últimas líneas visibles de las tres columnas quedan rebanadas a mitad de renglón (por ejemplo, en **00:43** arriba a la izquierda se corta a la mitad `"Ocho años de experiencia e..."`; en **00:48** abajo a la izquierda queda cortado por la mitad el resultado numérico `→ 468915720` debajo de `open_bid({"ref":"bid-2"})`).
- **00:41 (Rótulo que tapa etiquetas):** El rótulo flotante verde `"La adjudicación sale al portal"` tapa parcialmente las etiquetas de estado `"Adjudicación correcta publicada"`, `"guionado"` y `"bitácora: 25 eventos · cadena íntegra ✓"`.
- **00:43–00:44 (Rótulo que tapa código):** El rótulo flotante rojo `"El Radicador abre un sobre"` tapa la pastilla `"no confiable: 3"` de la columna izquierda y se monta sobre la columna central (`Evaluador`), tapando parte de `write({"data":"Radicadas tres ofertas...","key":"evaluation.context"})`.
- **00:46 (Rótulo que tapa código):** En la columna central (`Evaluador`), el recuadro rojo de `"contexto restringido: sealed.bid-2"` corta `"Páramo SA":"bid-3"}"` y el rótulo `"El Evaluador hereda la etiqueta"` tapa casi por completo la llamada `score_bids({"refs":["bid-1","bid-2","bid-3"]})`.
- **01:33–01:34 (Bajo contraste):** En la tarjeta derecha (`AgentDojo`), debajo de la barra verde aparece el texto `"En los 15 que escapan, el valor viene del pedido del usuario."` en gris oscuro sobre fondo azul marino oscuro; tiene muy poco contraste y cuesta leerlo.

---

### 5. ¿El ritmo es bueno? ¿Alguna lámina dura demasiado poco o demasiado?
El ritmo general es pausado y fácil de seguir, pero hay tres láminas donde el tiempo en pantalla de ciertos elementos es demasiado corto:
- **00:35–00:37 (3 segundos):** La primera captura de la interfaz tiene mucha densidad visual (configuración, archivos, opciones de agentes y compuerta) y dura apenas 3 segundos antes de hacer scroll.
- **00:45–00:47 (~1.5 segundos):** El segundo resaltado del ataque (`"El Evaluador hereda la etiqueta"`) dura menos de dos segundos en pantalla antes de que la vista vuelva a desplazarse hacia abajo.
- **01:33–01:34 (~1.5 segundos):** La nota explicativa en la tarjeta de AgentDojo (*"En los 15 que escapan, el valor viene del pedido del usuario"*) aparece casi al terminar la lámina y desaparece en el corte del segundo **01:35**, sin dar tiempo a leerla.

---

### 6. ¿Hay errores de español (ortografía, tildes, concordancia) en la voz o en pantalla?
**No hay errores ortográficos ni de concordancia.** El uso de tildes y puntuación es impecable y consistente con las normas de la RAE (incluyendo *«guion»* sin tilde en pantalla en **00:35, 00:38, 00:42, 01:21, 01:52** y *«Quórum»* con tilde en todo el video).
- Como único detalle menor de mezcla de idiomas en la interfaz: en **00:40, 00:43, 00:46 y 00:49**, los registros de los agentes mezclan inglés y español (`→ Saved.`, `→ BLOCKED by policy P1: restricted sources not authorized for this destination: sealed.bid-2`, mientras el resto de la UI está en español).

---

### 7. ¿Alguna cifra en pantalla no cuadra con lo que dice la narración en ese momento?
Todas las cifras principales coinciden con la voz. Las únicas dos diferencias (menores y justificadas, pero perceptibles) son:
- **00:54:** La pantalla titula `"90 trámites, con agentes manejados por un modelo"` y muestra al instante el desglose `"60 trámites honestos"` y `"30 ataques, repartidos entre 1, 2 y 3 agentes"`, mientras la voz en ese segundo dice únicamente *"Lo medimos en noventa trámites con agentes de modelo"* (recién menciona los 30 ataques en **00:58** y los 60 honestos en **01:03**).
- **01:11–01:12:** La voz dice *"Un monitor por agente también las detecta, sin falsos positivos"*, mientras en la tabla aparece `"0 de 30*"` (con asterisco) en la columna `"Honestos marcados"`. Aunque `0 de 30` equivale a cero falsos positivos, el cambio de denominador respecto a los `60` trámites honestos (que la fila inferior muestra como `0 de 60` en **01:19**) obliga a leer la nota al pie para entender por qué son 30 y no 60.

---

### 8. ¿Qué cambiarías? (De más a menos importante)
1. **Corregir la superposición en el diagrama de la idea clave (00:29–00:34):** Mover más abajo el recuadro de `"Etiqueta de la salida / Política publish = []"` o ocultar las etiquetas `{sealed.bid-2}` inferiores de Evaluador y Publicador cuando se abre ese panel, para que no queden cortadas por la mitad.
2. **Reubicar los rótulos flotantes en las capturas de interfaz (00:41, 00:43–00:46):** Ponerles una flecha o colocarlos en un margen limpio para que `"El Radicador abre un sobre"` y `"El Evaluador hereda la etiqueta"` no tapen las llamadas `score_bids` ni la columna contigua, y que `"La adjudicación sale al portal"` (**00:41**) no tape los badges de resultado.
3. **Añadir un tercer resaltado para el Publicador en 00:46–00:47:** La voz dice *"Con los tres agentes desviados, el valor sellado pasa de uno a otro"*, pero solo se resaltan el Radicador (**00:43**) y el Evaluador (**00:46**); falta un breve recuadro en la tercera columna (`Publicador`) o extender medio segundo cada paso para que se vea la cadena de tres completa.
4. **Subir el contraste y la duración de la nota en AgentDojo (01:30–01:34):** Hacer que la frase *"En los 15 que escapan, el valor viene del pedido del usuario"* aparezca desde **01:30** junto con la tarjeta y en un gris mucho más claro (`#CBD5E1` o blanco), porque en **01:33–01:34** apenas se ve y dura 1.5 segundos.
5. **Ajustar la pronunciación de la sigla «IA» en el cierre (00:08):** En el segundo **00:08**, la voz sintética pronuncia `"IA"` casi como un diptongo o sílaba unida (*"i-a"* muy rápido), en lugar de deletrear con claridad *"i-a"* o decir *"inteligencia artificial"*.

---

### 9. Sobre la voz sintética
- **¿Suena natural o apurada?:** Suena **muy natural, clara y con excelente dicción y ritmo** (no suena apurada en ningún tramo; las pausas entre secciones están muy bien medidas).
- **¿Se entiende cada cifra?:** Sí, absolutamente todas las cifras (`90`, `16 de 30`, `60`, `7600`, `1506 de 1521`) se entienden con total nitidez.
- **¿Cómo pronuncia `"AgentDojo"`, `"Quórum"` y `"IA"`?:**
  - **`"Quórum"` (00:00):** Lo pronuncia perfectamente en español (`"Cuórum"`, con acento en la *o*).
  - **`"AgentDojo"` (01:30 y 01:41):** Lo pronuncia con fonética inglesa natural (`"Éiyent Dóyo"` / `/ˈeɪdʒənt ˈdoʊdʒoʊ/`), muy claro en ambas ocasiones.
  - **`"IA"` (00:08):** Es el único punto flojo de la locución; al final de *"varios agentes de IA"* (**00:08.5**), une las dos vocales rápido (`"de i-a"` / `"ya"` con un leve corte glotal entre la *i* y la *a*), lo que suena un poco robótico comparado con el resto de la frase.
- **¿Alguna otra palabra que se oiga mal o cortada?:** Ninguna palabra se oye cortada. Solo en **01:21**, al decir *"que siguen un guion"*, hace un hiato muy marcado (`"gui-ón"`), aunque totalmente comprensible.

---

### 10. Sobre los tres planos generados con IA (apertura 00:00–00:09, inicio del caso 00:09–00:14 y cierre 01:51–01:57)
- **¿Se ve algún texto, logo, persona o algo raro?:**
  - No aparecen personas, manos ni textos alucinados.
  - En los tres planos el protagonista es un sobre con un sello de lacre rojo. En el sello de lacre (**00:00–00:09** y especialmente en el primer plano de **01:51–01:57**) se distingue un relieve geométrico rectangular dentro de un círculo (parecido a una hebilla o dos columnas dentro del lacre), pero sin letras ni logotipos reales.
  - Como detalle visual menor de generación por IA: en el primer plano (**00:00–00:09**), el sobre levita o avanza sobre un haz de luz vertical azul que pasa a través de él, y en el segundo plano (**00:09–00:14**), el sobre se desliza solo sobre un riel luminoso azul que atraviesa tres atriles/escritorios blancos. Ambos se ven limpios y estéticos.
- **¿El texto montado encima se lee bien?:** **Sí, se lee perfectamente en los tres planos.** Los fondos son oscuros y tienen buen viñeteado/oscurecimiento, por lo que los textos blancos y celestes (incluida la URL del repositorio y el bloque de créditos de **01:52–01:57** y el aviso `"Plano generado con IA · Higgsfield"` arriba a la derecha) tienen excelente legibilidad.

---

### 11. Sobre las capturas de la interfaz (segundos 34 a 52)
- **¿Los recuadros y rótulos resaltan lo que la voz dice en ese momento?:**
  - **00:39–00:41:** Sí. Cuando la voz dice *"En un trámite honesto, la adjudicación se publica"*, se resalta primero en verde `"Compuerta: permite ✓"` con el rótulo `"La compuerta permite"` (**00:40**) y luego el cuadro negro del portal externo con `"La adjudicación sale al portal"` (**00:41**).
  - **00:42–00:47:** Parcialmente. La voz dice *"Con los tres agentes desviados, el valor sellado pasa de uno a otro"*. Se resalta el paso 1 en la columna del Radicador (`open_bid({"ref":"bid-2"})` con el rótulo `"El Radicador abre un sobre"`, **00:43–00:44**) y el paso 2 en la columna del Evaluador (`contexto restringido: sealed.bid-2` con el rótulo `"El Evaluador hereda la etiqueta"`, **00:46**), pero **no se resalta nada en la tercera columna (`Publicador`)**, a pesar de que el texto dice que son tres agentes y que pasa de uno a otro.
  - **00:48–00:52:** Sí. Cuando la voz dice *"La compuerta bloquea la salida: no se publica nada"*, se encuadra `"Compuerta: BLOQUEA ⛔"` con el rótulo `"La compuerta bloquea"` (**00:48**), luego se encuadra en rojo `"(no se publicó nada)"` (**00:49**) y aparece el sello `"BLOQUEADO"` sobre el intento tachado (**00:51**).
- **¿Algo queda tapado o cortado?:**
  - **Tapado por rótulos:**
    - En **00:41**, el rótulo `"La adjudicación sale al portal"` tapa las pastillas `"Adjudicación correcta publicada"`, `"guionado"` y parte de `"bitácora: 25 eventos · cadena íntegra ✓"`.
    - En **00:43–00:44**, el rótulo `"El Radicador abre un sobre"` tapa `"no confiable: 3"` en la columna izquierda y el inicio del bloque `write(...)` en la columna central.
    - En **00:46**, el rótulo `"El Evaluador hereda la etiqueta"` tapa `score_bids({"refs":["bid-1","bid-2","bid-3"]})` en la columna central, y el borde superior de su recuadro rojo pisa la línea `"Páramo SA":"bid-3"}"`.
  - **Cortado por los bordes de la captura:**
    - En **00:35–00:37**, la parte inferior de las tres tarjetas de agentes queda cortada tras la primera línea `read(...)`.
    - En **00:40–00:41** y **00:48–00:52**, cuando la vista baja a `"3 · RESULTADO"`, las columnas del Evaluador y Publicador quedan vacías en blanco arriba y la columna del Radicador muestra solo el final de su último `write(...)`.
    - En **00:42–00:44** y **00:47–00:48**, los bordes superior e inferior de las columnas cortan líneas de texto a mitad de altura durante el scroll.

