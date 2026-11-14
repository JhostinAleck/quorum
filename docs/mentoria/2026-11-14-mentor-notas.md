# Mentoría del 14-nov-2026: notas para el equipo Quórum

Fuente: [2026-11-14-mentor-RAW.md](2026-11-14-mentor-RAW.md), la transcripción de Granola sin editar.
Granola no separa las voces, así que la atribución al mentor es una interpretación. Estado del
proyecto según la rama `frente-3-ataques` (commit `2e327d8`) y `origin/main` a las 12:40.

## Lo que dijo el mentor, en 9 puntos

1. **No se entendió qué es el producto hasta el final.** Lo captó con el ejemplo de la Coca-Cola.
   Lo presentamos como «3 agentes que hacen una licitación», cuando el producto es **la compuerta**.
   Los agentes solo son el banco de pruebas. El pitch debe abrir con la compuerta y cerrar con un
   resultado concreto («nuestra solución es N veces mejor que…»).
2. **Comparar contra una línea base: un LLM con un buen prompt.** Si un solo modelo bien instruido
   llega al mismo nivel, Quórum aporta 0 %. Hay que mostrar la diferencia con un número.
3. **Diseñar bien las métricas.** Hay que dejar pasar lo legítimo y bloquear lo malo. Un sistema
   que bloquea todo es tan malo como uno que no bloquea nada, así que la utilidad cuenta tanto como
   la detección.
4. **Crítica central: «yo gano por defecto».** Si suponemos de entrada un *system prompt* ya
   corrupto, construimos «una solución a un problema que ustedes inventaron». La compuerta tiene que:
   - funcionar como algo **externo e independiente del pipeline**;
   - valer también para un sistema estándar, no solo para uno corrompido a propósito;
   - probarse en un **escenario realista**, con inyección de prompt y no solo con un prompt
     comprometido.
5. **Intentar romper la compuerta.** Hay que forzar el sistema a fallar, para que la afirmación de
   robustez tenga respaldo.
6. **Ablación.** Hay que decir qué partes sirven y cuáles no, y quitar las que no aportan. Decir «lo
   intentamos y no dio nada» suma, no resta.
7. **Métricas específicas de fuga.** Hay que reportar qué se filtró: el precio de otros oferentes u
   otro dato.
8. **El mismo dataset sin la salvaguarda y con ella.** La comparación central es antes contra
   después.
9. **Agnóstico implica más dominios.** Por ejemplo salud o historias clínicas, con una tabla por caso
   de qué es sensible y qué no puede salir. Le pareció bien que esa tabla la defina el usuario.

**Logística:**
- Dijo que el pitch dura **2 minutos**, mientras que `docs/tareas.md` dice 3; hay que confirmarlo.
- El formato del documento no lo sabía (dijo que un paper serviría) y quedó en preguntarlo.

Recordatorio de los criterios de los organizadores, de la misma grabación:
- impacto e innovación;
- calidad de ejecución: «los resultados realmente respaldan sus afirmaciones»;
- claridad.

También pidieron una ficha de **2 páginas**, entrega a las **5:00 pm** y honestidad sobre los fallos
y los posibles abusos.

## Qué nos toca corregir

Prioridad: **A** antes de la entrega, **B** si da el tiempo, **C** basta con decirlo en la ficha.

| # | Crítica | Dónde estamos | Qué hacer | Prio |
|---|---|---|---|---|
| 1 | El pitch habla de agentes y no de la compuerta (pt. 1) | El README y la ficha ya hablan de la compuerta. El pitch no está escrito. | Primera frase: «Quórum es una compuerta determinista que se pone delante de cualquier pipeline de agentes». Cierre con una cifra (ver #6). Medir que dure 2 minutos. | A |
| 2 | «Ganan por defecto»: el ataque supone agentes ya corruptos (pt. 4) | Cierto para el escenario de licitación: los ataques son tareas ocultas en el prompt de 1, 2 o 3 agentes. La compuerta dura bloquea 16/16 fugas **por construcción**, porque la política marca `sealed.*` como restringido. | (a) Correr la compuerta sobre **AgentDojo**, un benchmark externo de inyección de prompt con trazas que no hicimos nosotros, con la política congelada antes de ver resultados. Piloto: banca. (b) En la ficha, decir claramente que la compuerta dura es correcta por construcción y que lo que se mide es su costo en utilidad y su cobertura. | A |
| 3 | Falta la línea base «LLM con buen prompt» (pt. 2 y 8) | Hay un brazo sin defensa (fuga 16/30) y cuatro monitores LLM: M1, M2, M2 ciego y la compuerta suave. Ese es justamente el «LLM que clasifica». **No hay** brazo de agentes con un prompt de seguridad fuerte y sin compuerta. | Agregar ese brazo B0: mismo lote, el prompt de cada agente con instrucciones explícitas de no filtrar montos. Si no da el tiempo, presentar los monitores LLM como esa línea base, que es defendible. | A/B |
| 4 | Utilidad y falsos positivos (pt. 3) | Ya se mide. Compuerta dura: 0/60 honestos bloqueados, utilidad 60/60. Monitores con Haiku 5.5: M2 tiene 2/30 falsos positivos y M2 ciego 5/30. | Ponerlo junto a la detección en la figura y la tabla (ya está en `docs/figura-deteccion.png`). Reportar el intervalo de confianza: con 30 casos, 0/30 equivale a ≤ ~10 % con 95 %. | A |
| 5 | Romper la compuerta (pt. 5) | Hay un oráculo de Jhostin (`fc50888`). No hay ataques adaptativos contra la compuerta misma, como parafrasear el monto, partirlo en pedazos o codificarlo. | Una tabla corta de intentos de evasión y su resultado, aunque sean 5 casos a mano. Lo honesto: la compuerta sigue la procedencia, no el texto, así que una paráfrasis derivada de `sealed.*` también queda marcada. Hay que probarlo y no solo afirmarlo. | B |
| 6 | Ablación (pt. 6) | Ya existe y hay que decirla. M2, con la vista global, **no supera** a M1 por agente (16/16 los dos con Gemini). La compuerta suave ahorra llamadas: solo llama al modelo en 23/30 ataques y 0/60 honestos. | Un párrafo en la ficha: «qué parte sirvió y qué parte no». | C |
| 7 | Métrica de qué se filtró (pt. 7) | La fuga solo cuenta el **canario literal**, el monto exacto del oferente objetivo. No mide fugas semánticas («entre 400 y 450 millones», «más alta que…»). | Decirlo como límite en la ficha. Si da el tiempo, sumar un detector de rango o paráfrasis sobre lo publicado. | C/B |
| 8 | Agnóstico implica más dominios (pt. 9) | Existe un escenario `helpdesk`, pero **no está evaluado**. La política es un `policy.toml` por dominio: es la «tabla por caso» que pidió. | AgentDojo cuenta como segundo y tercer dominio (banca, slack, workspace o viajes). Mostrar en la ficha un `policy.toml` corto como «la tabla de lo sensible». | B |
| 9 | Ficha y logística | La ficha ya tiene **2 páginas** (`88a3f0c`, 12:48, en la rama `frente-3-ataques`). Falta verificar su contenido y que incluya la figura. No sabemos el formato. Tampoco la hora exacta: el mentor dice 5:00, `tareas.md` dice 16:00 y otra fuente dice que se congela a las 15:30. | Alguien pregunta a los organizadores el formato del documento, la duración del pitch y la hora límite. Entretanto, ficha de 2 páginas con el diagrama y la figura. | A |

## Lo que ya tenemos y responde al mentor

- **Antes y después en el mismo lote:** 90 episodios (60 honestos y 30 ataques). Sin defensa fugan
  16/30 (5, 6 y 5 de 10 por k). La compuerta dura bloquea 16/16 fugas y 0/60 honestos.
- **Monitores LLM como comparación:** con Gemini 3.5 Flash Lite, M1 y M2 detectan 16/16 y M2 ciego
  13/16, todos con 0/30 falsos positivos. Con Haiku 5.5, M2 y M2 ciego pagan en falsos positivos
  (2/30 y 5/30).
- **Calibración honesta:** el umbral sale de los honestos con semilla par y el FPR se reporta en la
  mitad impar. Los ataques nunca entran a la calibración.
- **Reproducible:** `uv run --extra eval python -m quorum.eval.analysis --figure docs/figura-deteccion.png`
  recalcula todas las cifras desde `datos/`.

## Límites que conviene decir antes de que los digan

- Hay un solo escenario evaluado (licitación) y 30 ataques: los intervalos son anchos.
- Las plantillas de ataque se ajustaron después de 4 pilotos, con las mismas semillas.
- `metrics.yaml` se congeló cuando ya se habían visto puntajes de ataque. Los umbrales salen solo de
  honestos, pero el congelamiento no fue a ciegas.
- La fuga se mide con el canario literal.
- La compuerta dura es correcta por construcción dentro de su política. Su valor está en que no
  depende de un modelo y en lo que cuesta en utilidad, que aquí fue nada; no está en que «detecte
  mejor».
