# Pitch de 3 minutos, con la ficha en pantalla

Las reglas salen de la página oficial del hackathon:
- Son 3 minutos con la ficha técnica proyectada (`docs/documento-tecnico/quorum.pdf`), sin diapositivas.
- Pitch desde las 5:10 p.m. Después, los jurados hacen unas pocas preguntas cortas.
- Hay tres criterios con el mismo peso, de 1 a 5 cada uno: impacto e innovación, calidad de ejecución y claridad. Si hay empate, gana el mejor en impacto.

Cómo se armó:
- Del mentor: se abre por **la compuerta**, no por los agentes; se nombra la línea base y se cierra con el número.
- De la investigación de pitch de Mérito 11 (`~/Documents/agent-reports/2026-11-12/pitch-merito11/`, informes 20 y 27):
  - La primera frase dice qué hacemos, en lenguaje simple (Seibel, YC).
  - Un titular que se repite: **«no lee el texto; sigue de dónde viene el dato»**.
  - Un antagonista: el monitor que lee.
  - Frases cortas, y cada cifra contra algo que se entienda.
  - Un solo momento para recordar: la tabla 1, donde nadie gana en detección y la compuerta gana en todo lo demás.

El guion tiene unas 440 palabras: a 155 por minuto, con pausas, da unos 2:55. Entre corchetes va adónde se señala en la ficha. Si al ensayar pasa de 3:00, se corta el bloque de AgentDojo (2:05) a su primera frase.

## Guion

> **(0:00) [Título]** Somos Quórum. Hicimos una compuerta que impide que un sistema de agentes de IA publique
> un dato secreto, aunque varios agentes se pongan de acuerdo para sacarlo. Y no lee el texto: sigue de
> dónde viene el dato.
>
> **(0:15) [Amenaza]** El caso es una licitación pública. Tres agentes: uno registra las ofertas, otro las
> evalúa, otro publica. Uno, dos o los tres están comprometidos y quieren filtrar el precio de un
> competidor. Si se reparten el trabajo, cada paso parece rutina: uno abre el sobre y lo anota como
> si fuera un número de radicado, otro lo copia, el tercero lo publica. Cada paso, visto por separado,
> parece normal. Makins y otros lo midieron este año: repartir el ataque le baja la sospecha al
> monitor por agente.
>
> **(0:40) [Figura 1]** Nuestra idea no es otro monitor que lea. Cada dato lleva una etiqueta con sus
> fuentes, y lo que un agente escribe hereda la etiqueta de lo que leyó. Al publicar, si lo que sale deriva de un sobre sellado, no sale. No llama a ningún modelo
> y no tiene umbral. Da igual cómo disfracen el número: no lee el texto; sigue de dónde viene el dato.
>
> **(1:05) [Tabla 1]** Lo medimos con agentes de modelo: 90 trámites, 60 honestos y 30 ataques. Sin defensa,
> el precio llega al portal en 16 de 30. La compuerta bloquea las 16 y no detiene ninguno de los 60
> honestos. Y la línea base: un monitor por agente también atrapa las 16. Empatamos en
> detección. La diferencia es todo lo demás: los monitores suman cuatro llamadas a un modelo por trámite, avisa
> al final y depende de un umbral; la compuerta decide en un microsegundo, antes de que el dato salga, y
> ningún texto la convence.
>
> **(1:40) [Tabla 2]** El núcleo no es de la licitación. Probamos cinco dominios, de historias clínicas a
> banca. En 7.600 ataques guionados, un filtro que conoce todos los
> secretos deja pasar 42 %; Quórum, cero. Para adoptarlo, un equipo escribe un archivo de política de unas
> 20 líneas por dominio.
>
> **(2:05) [Tabla 3]** También contra ataques que no escribimos: en 7.127 trazas de AgentDojo, un banco público de inyección, frena
> 1.506 de 1.521 secuestros por inyección. Y donde no aporta, lo decimos: con un buen prompt, la inyección
> en nuestra licitación dio cero fugas en 600 episodios.
>
> **(2:25) [Límites]** Dónde falla. Bloquea de más: quien abre un sobre sin necesitarlo queda retenido para
> revisión humana. Y lo que la política declara público, sale: con los puntajes publicados un rival
> despeja el precio. Eso no lo arregla la compuerta; lo arregla el pliego. Y el uso dual: los ataques son
> plantillas simples, contra nuestro propio arnés y con datos sintéticos.
>
> **(2:45) [Cierre]** Quórum: 16 de 16 fugas bloqueadas, 0 de 60 trámites honestos, cero llamadas a un
> modelo. El repositorio corre sin llaves con `uv run pytest`. Gracias.

## Por Zoom

Según la investigación en `~/Documents/agent-reports/2026-11-14/pitch-hackathon/01-como-ganar-pitch-zoom.md`, en lo virtual el reloj
corre desde que aparecemos, y con la pantalla compartida el orador se queda en una miniatura. Lo que más pesa:
la ficha a página completa se ve ilegible en Zoom.

**Roles**
- **Voz:** una sola para los 3 minutos; el equipo entra en las preguntas. Si son dos voces, un solo relevo en
  1:40: se dice el nombre en voz alta y se espera un segundo antes de hablar.
- **Pantalla:** una persona. Comparte **la ventana del PDF**, no el escritorio, y hace zoom a cada tabla cuando
  la voz dice la señal entre corchetes. La página oficial dice que los jurados **leen la ficha** mientras
  hablamos, así que la pantalla tiene que mostrar justo lo que se dice. Son 6 movimientos, ensayados con el
  guion:
  - **0:00, página 1 arriba:** el título y «En una frase».
  - **0:40, página 1:** la Figura 1 ampliada. Se queda ahí durante la amenaza y la defensa.
  - **1:05, página 2, columna izquierda:** la Tabla 1 ampliada.
  - **1:40, página 2, columna izquierda:** la Tabla 2.
  - **2:05, página 2, columna izquierda:** la Tabla 3.
  - **2:25, página 2, columna derecha:** «5. Límites» y «6. Riesgo de uso dual».
  - **2:45, vuelta a la página 1 arriba:** el título, para el cierre.
- **Respaldo:** otra persona, en otra red (datos del celular), con el PDF abierto. Si la pantalla falla más de
  10 segundos, comparte ella. La voz sigue hablando: el guion se entiende sin la pantalla.
- **Reloj y chat:** pega en el chat de Zoom el enlace del repositorio y el del PDF en el segundo 0. Lleva el
  tiempo y, durante las preguntas, le pasa una cifra a quien responde por WhatsApp. Nunca a quien comparte:
  la notificación saldría en pantalla.

**Antes (a más tardar 16:45)**
- Preguntar a los organizadores si los participantes pueden compartir pantalla, y entrar temprano al enlace.
- Renombrarse en Zoom como «Nombre · Quórum».
- Hacer un ensayo cronometrado en un Zoom propio, con la misma persona compartiendo, y 3 preguntas de la lista.
- Quien comparte: «No molestar» activado, Slack, WhatsApp y correo cerrados, el portátil enchufado y, si se
  puede, conexión por cable.
- Quien habla: audífonos con micrófono probados, cuarto silencioso, cámara encendida, cara iluminada y fondo
  simple.

**Durante**
- La pantalla ya está compartida antes de la primera palabra. Nada de «¿se ve?, ¿me escuchan?»: si hace falta,
  se confirma por el chat.
- Todos en silencio menos quien habla. Con la latencia de Zoom no se pisa a nadie: se espera un segundo.
- En las preguntas, quien responde repite la pregunta en voz alta, activa el micrófono, da una frase, una cifra
  y el límite, y lo vuelve a silenciar.

## Si cortan a 1 minuto

> Quórum es una compuerta para sistemas de agentes de IA: cada dato lleva la etiqueta de sus fuentes y, si
> lo que se publica deriva de un sobre sellado, no sale. No lee el texto, así que no se la convence ni se
> la engaña disfrazando el número. Con agentes de modelo coludidos en una licitación, bloquea las 16 fugas
> y 0 de 60 trámites honestos, sin llamar a ningún modelo; en 7.127 trazas de AgentDojo frena 1.506 de
> 1.521 secuestros. Falla donde la política declara algo público, y lo medimos.

## Qué no decir

- No abrir con «tenemos tres agentes». La primera frase es la compuerta.
- No decir que el monitor «falla»: M1 detecta 16 de 16. La ventaja es el costo, el momento de decidir y
  que no se la convence.
- No decir que la inyección «rompe» a los agentes en la licitación: ahí un buen prompt basta.
- No decir «demostramos» ni «garantiza»: son 30 ataques con plantillas fijas, y los intervalos son anchos.
- No presumir de pre-registro sin decir que fue tardío.

## El guion visto por cada jurado

Perfiles verificados el 14-nov; fuentes en `~/Documents/agent-reports/2026-11-14/pitch-hackathon/02-jurados.md`.
En la apertura dijeron que cada proyecto lo califican al menos 2 jurados, que algunos son internacionales y que
quizá no tengan mucho contexto. Por eso el guion va en lenguaje simple, sin «marea alta» ni «desclasificador».

| Jurado | Qué trabaja | Qué escucha en el guion | Riesgo | Qué hacer |
|---|---|---|---|---|
| **Christian Urcuqui** (investigador de seguridad y científico de datos; profesor) | AgentBreak: un laboratorio donde un documento recuperado le inyecta órdenes a un agente y unos «controles deterministas» (clasificación de datos, salida, aprobación humana) impiden la acción, «aunque el atacante manipule el razonamiento». Cada ataque exitoso se vuelve una prueba de regresión | Es su tesis: «no llama a ningún modelo», «ningún texto la convence». También la cifra de AgentDojo | Que piense «esto ya es AgentBreak» | En las preguntas, reconocerlo: «Es la misma idea que AgentBreak: el control fuera del modelo. Nosotros la llevamos a varios agentes: la etiqueta viaja con el dato, y el que publica nunca abrió el sobre». Los ataques son pruebas en `pytest` |
| **Antonio Badilla-Olivas** (SPAR/CRSS) | Control de IA con varios agentes: ataques y monitores que evolucionan juntos | La colusión repartida, Makins y otros, y M1 como línea base | El atacante es fijo; querrá saber qué hace uno que conoce la compuerta | P1: el canal de la existencia de la clave (6,3 bits), que quedó en 0 con la marea alta. Decir que los canales de tiempo y orden siguen abiertos |
| **Carlos Gorostiza Ibáñez** (SPAR/UANL) | Un banco de pruebas de negociación entre agentes | La licitación como mercado con adversarios | Que pregunte si la colusión surge sola o va instruida, y por los canales encubiertos | La nuestra va **instruida**, con una tarea oculta; no medimos colusión que surja sola. Lo cifrado o escondido en una salida derivada conserva la etiqueta; lo que no viaja en los datos queda fuera |
| **Jose Felipe Duarte** (LRC/UTP) | PsychoAlign (ICML 2026, con Jose Jaramillo): un agente que maximiza utilidad, un Evaluador con marcos morales intercambiables y un Mediador que arbitra | El antagonista del guion es «el monitor que lee», que se parece a su Evaluador | Que lo tome como un ataque a su enfoque | No decir que los monitores «fallan». Decir: «se combinan: la compuerta suave solo llama al monitor cuando lo publicado deriva de un secreto». El costo en capacidad: 16 de 25 tareas limpias en AgentDojo, frente a 19 sin defensa |
| **Manuela Chacón-Chamorro** (Uniandes; doctorado con beca DeepMind) | La resiliencia cooperativa: resistir, adaptarse, recuperarse y transformarse ante disrupciones (Melting Pot, humanos frente a LLM) | La licitación sigue funcionando con agentes comprometidos: 60 de 60 honestos | **La compuerta contiene, no recupera**: el trámite atacado queda retenido para revisión humana | Decirlo así. Lo que sí resiste: terminan 1.200 de 1.200 trámites honestos en los cinco dominios. La recuperación no la medimos |
| **Jairo Torregrosa** (Mercado Libre; Agent SDK, evals abiertos; embajador de la comunidad de Claude; también es mentor) | Agentes en producción y evals | `uv run pytest`, las 20 líneas de política, el microsegundo | Que pregunte cómo se conecta a un agente de verdad | El monitor es un servidor HTTP: los agentes, en sus propios contenedores, llaman a las herramientas a través de él (está desplegado). Un adaptador MCP o para el Agent SDK **no está hecho** |

**Si en la sala dicen «2 minutos»** (el mentor lo mencionó en la apertura): el bloque de AgentDojo se queda en su
primera frase y los límites en «Bloquea de más, y lo que la política declara público, sale».

## Ensayo de preguntas (respuestas de unos 20 segundos)

**Antonio Badilla-Olivas** (SPAR, entornos donde los ataques y los monitores evolucionan juntos)
1. *«Tu atacante es fijo. ¿Qué pasa con uno adaptativo?»* Adaptar el texto no sirve, porque la compuerta no
   lo lee: probamos cuatro textos dirigidos a quien decide y nueve disfraces del número, y ninguno cambia la
   decisión. Lo que sí la evade son los canales que no viajan en los datos. Un atacante encontró uno: la
   existencia de una clave revelaba el valor (6,3 bits). Lo cerramos juzgando con lo que vio cualquier
   agente, y quedó en 0 bits. Los que siguen abiertos están en la ficha: tiempo, orden y puntajes publicados.
2. *«¿Por qué no un monitor mejor?»* Probamos tres jueces, entre ellos Jev, que cuesta menos de la mitad. Siguen
   siendo un puntaje con umbral que lee lo que escribe quien vigila. Jev, con ataques hechos por un modelo,
   deja escapar 2 de 16. La compuerta y el monitor se combinan: la compuerta suave solo llama al monitor
   cuando lo publicado deriva de un secreto.

**Christian Urcuqui** (TryHackMe, AgentBreak: inyección indirecta)
3. *«¿Y la inyección indirecta?»* En nuestra licitación, un buen prompt ya basta: 0 fugas en 600. Donde la
   compuerta aporta es con el agente que sí obedece. En AgentDojo, la regla por valor frena 1.506 de 1.521
   secuestros. El costo: deja funcionando 16 de 25 tareas limpias, frente a 19 sin defensa.
4. *«¿Quién pone las etiquetas iniciales?»* Un humano, en la política: qué nace restringido y qué escriben
   terceros. Es un supuesto, y está en la ficha. Todo tiene que pasar por el monitor.

**Carlos Gorostiza, José Felipe Duarte y Manuela Chacón** (negociación y resiliencia multiagente)
5. *«¿Esto es colusión o solo una fuga?»* Es colusión: k agentes con una tarea oculta que se reparten el
   ataque para que ningún paso aislado se vea raro. Es el riesgo del track 6 y el resultado de Makins et al.
   (arXiv 2607.07368): repartir baja la sospecha de un monitor por agente.
6. *«¿Funciona si los agentes negocian entre sí en vez de compartir un almacén?»* Sí, mientras los mensajes
   pasen por el monitor: un mensaje es un dato con etiqueta. Fuera del monitor no vemos nada, y ese es el
   supuesto.
7. *«¿Cuánto trabajo legítimo rompe?»* Con la licitación terminan los 60 honestos, y en los cinco dominios
   los 1.200 trámites honestos. Lo que detiene siempre es el honesto descuidado que abre un sobre que no
   necesitaba: lo retiene para revisión humana, a propósito.

**Jairo Torregrosa** (Mercado Libre: agentes y evals abiertos)
8. *«¿Lo puedo correr?»* Sí, sin llaves ni costo: `uv run pytest` (880 pruebas) y los análisis se
   recalculan desde `datos/`. La política y el código de la compuerta tienen hashes fijados, y el monitor no
   arranca si cambian.
9. *«¿Cómo lo meto en mi sistema de agentes?»* Las herramientas que sacan datos pasan por el monitor, y se
   escribe un `policy.toml` de unas 20 líneas: fuentes restringidas, fuentes no confiables, qué admite cada
   salida. El núcleo no cambia entre dominios.

**Cualquiera**
10. *«¿Qué es nuevo, si FIDES y CaMeL ya hacen control de flujo?»* Ellos defienden contra la inyección, con
    el agente como víctima. Nosotros medimos la compuerta cuando los propios agentes son los atacantes y se
    coluden, cara a cara con monitores, y reportamos el costo junto al beneficio.
