# Briefing del hackathon, 14-nov-2026 — notas enhanced

**Origen:** transcripción automática de Granola de la reunión «Criterios de evaluación y cronograma para
competencia de proyectos IA» (raw completo en `07-briefing-granola-raw-completo.md`). Estas notas son la
lectura en limpio de ese audio: se corrige puntuación y se ordena por tema, sin agregar nada que no esté
dicho. Donde el audio es ambiguo se marca. Los nombres y cifras que el audio oye mal van con `[?]`.

**Cómo leerlas:** lo del principio es la organización hablando al auditorio; lo del final es la tutoría
sobre nuestro proyecto, con dos mentores distintos. La transcripción no trae etiquetas de hablante: la
atribución es inferida por contexto.

---

## 1. Cronograma del día

| Hora | Qué |
|---|---|
| 10:00 | visita al local para los pitches. «A las 10, por favor, porque a las 2 vamos a dar el orden de los pitches» |
| 14:00 | se publica el orden de los pitches |
| **17:00** | **entrega de la ficha**. «A las 5 en punto es la hora de entrega… muy, muy juiciosos con esa hora» |
| 17:15 | empiezan las presentaciones |

- El pitch es de **2 minutos** («frente al pitch, que son 2 minutos y tienes que exponerlo, punto»).
- Si no se entrega a tiempo «no tienen espacio para las fichas» y no se puede competir por los premios.

## 2. Formato del entregable

- **Ficha de 2 páginas** para «los partners de la empresa técnica, **2 partners máximo**», que se basan
  en la presentación; después va la presentación final.
- «El jurado entiende los miedos [hallazgos] que hicieron y lo que encontraron.»
- Hay **dos jurados internacionales**: conviene escribir la ficha para alguien de fuera del país y del
  contexto colombiano, y elegir el problema pensando en eso.
- Sobre si la ficha puede llevar gráficas: «presentas un paper… presentas todas sus páginas como de
  gráficas y de cosas». O sea, figuras y tablas son aceptables. Para dudas de formato de presentación,
  la persona sugerida es **José**.

## 3. Criterios de evaluación

1. **Impacto potencial e innovación.** «¿Su proyecto ataca un riesgo real con IA y es una idea nueva o
   no?»
2. **Calidad de la ejecución.** «¿Funciona? Y le pusieron a prueba. Los resultados que tienen realmente
   respaldan sus afirmaciones.»
3. **Claridad, presentación.** Que el jurado entienda qué se hizo y qué se encontró.

## 4. Línea roja y ética

- «Proyectos que estén enfocados en la ofensa no van, no pueden ser considerados para los premios, y
  tampoco pueden ser publicados.»
- «Nada de acá ni escaneando, que eso es un delito»; nada de exploits funcionales ni malware.
- «Tienen que ser muy, muy honestos con ustedes mismos de dónde fallan y cómo podría su herramienta ser
  abusada.» La honestidad sobre los límites es criterio explícito, no cortesía.

## 5. Recursos y reglas de participación

- Libertad total de modelos: locales, o claves de Gemini, OpenAI o Anthropic. La organización no da
  proveedor ni crédito.
- Se entregan entornos de prueba con base de datos vectorial y controladores.
- **Oracle Academy**: solo para cuentas UNIANDES; se recomienda que en cada equipo haya al menos una
  persona con cuenta institucional. Sugieren **Google AI Studio** con claves gratuitas de Gemini.
- Los premios: tres ganadores. Los montos del audio son ilegibles (`[?]`), no se usan.

## 6. La tutoría sobre nuestro proyecto

### 6.1 Lo que quedó claro y gustó

- El mentor entendió la idea al final: «fue al final cuando ya le entendí todo, porque ustedes dijeron un
  proceso de licitaciones y tenemos 3 agentes».
- Le interesó el contraste **monitores probabilísticos vs. compuerta determinística** («eso estaría
  interesante porque básicamente sí reduce ese problema»).
- Validó medir con y sin defensa sobre el mismo conjunto: «tenemos este dataset en el sistema sin ningún
  safeguard, ¿qué pasa? Si le metemos este safeguard, ¿cómo mejoras?».
- Su analogía: la compuerta «es como lo mismo que el CI en el código… es un CI básicamente». La dijo en
  la mesa y el mentor la confirmó.

### 6.2 Las tres objeciones

1. **Hablamos de agentes y no de la compuerta.** «No es tanto a los agentes, sino es más la compuerta.
   Esto es como para probarlo.» Y después: «tú me hablas de agentes y la compuerta no la mencionaste al
   final… Es bueno decir muy concretamente qué están haciendo».
2. **El baseline de un solo LLM con buen prompt.** «Un sistema donde solo está un modelo de lenguaje…
   con un buen prompt optimizado… tiene un rendimiento del 70 %… y con nuestro sistema multiagentes tiene
   un 85 %… ustedes están aportando 15 % ahí, pero ¿qué puede llegar a pasar? Que ustedes estén aportando
   0 %.» Corolario: «si yo llevo un modelo de lenguaje, un prompt, y alcanza el mismo nivel de rendimiento
   de ustedes, pues ustedes no se imaginan absolutamente nada».
3. **«Están inventando una solución a un problema que ustedes inventaron.»** Si el único escenario es un
   sistema que corrompimos a propósito, «básicamente estás diciendo: yo gano por defecto»; el sistema «se
   está construyendo para un caso muy particular». Pide que se muestre «al menos en un caso, en una
   cantidad de casos, se pueda saltar todo», es decir, un ataque que no hayamos puesto nosotros.

Sobre los dos caminos de ataque lo dijo explícito: uno es **prompt injection** por el contenido y el otro
es que **el modelo ya esté comprometido**; y anotó que si el compromiso es del `system prompt`, «la
compuerta no puede bloquear, pero claro, ahí hay un problema». Nosotros solo cubrimos el segundo.

### 6.3 Lo que pidió

- **Métrica diseñada primero y específica**: «uno debería inicialmente diseñar una métrica muy adecuada»;
  «con métricas específicas, por ejemplo, qué fue lo que se filtró». Su ejemplo de dato sensible: «el
  precio de los demás solicitantes».
- **Ablación y disposición a descartar**: si una pieza no mejora, «la pueden sacar de su sistema» y decir
  «qué partes del sistema en específico sí necesitamos».
- **Probar a romper la compuerta**: «qué tanto se puede llegar a usar tal compuerta… intentar romperlas».
- **Una política declarativa por caso de uso**: «una tabla verdadera por cada uso… estos elementos en
  específico… no pueden salir de la página», definiendo «qué tipo de información es sensible, cómo se
  mueve el proceso, qué debería especialmente tenerle mucho cuidado en la monitorización».
- **Un escenario realista**: «hacer que realmente tenga un escenario realístico».
- **Un cierre con resultado**: «¿cómo cerrar? No, normalmente era como un resultado».

## 7. Qué nos toca corregir

Detalle y redacción exacta en `06-raw-mentor-notas-y-correcciones.md`. En orden de riesgo:

| Prio | Corrección | Estado |
|---|---|---|
| P0 | Abrir el pitch por la compuerta, no por los tres agentes; cerrar con el número | guion listo (06 §4) |
| P0 | Nombrar el baseline (un LLM por agente con buen prompt) y decir el delta **sin inflarlo**: empata en detección (16/16); lo que aporta la compuerta es 0 falsos positivos, 0 llamadas y no ser persuadible por texto | ficha §3–§4 ya lo dice |
| P0 | Un caso de ataque que **no** hayamos puesto nosotros (instrucción por contenido, p. ej. la oferta escaneada), o declararlo como límite | límite declarado; medirlo, pendiente |
| P1 | Presentar M2 como **ablación**: no mejoró a M1 y por eso sale de la configuración recomendada | ficha lo reporta; falta decirlo así en el pitch |
| P1 | «Agnóstico» con letra pequeña: dos escenarios, monitores medidos en uno | ficha §3 |
| P1 | La política por caso de uso ya existe (`policy.toml`, sinks por destinatario): nombrarla | falta en el pitch |
| P1 | El símil del CI, una línea, para los partners no técnicos | falta en la ficha |
| P2 | «¿Keywords o clasificador?»: ni uno ni otro en la compuerta dura; etiquetas de procedencia | ficha §2 |
| P2 | Prior art en una línea | ficha §6 |
| P2 | No presumir de pre-registro sin explicar en la misma frase que el congelamiento fue tardío | ficha §1 |

## 8. Cierre de la reunión

«Vamos por buen camino, pero nos toca meter hartas cosas.» Y un aviso operativo: ya se podía pasar a
recoger algo en el piso 5 para presentar.
