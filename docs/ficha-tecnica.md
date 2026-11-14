# Quórum: procedencia contra fugas repartidas entre agentes de IA

**Equipo Quórum** · Track 6, Riesgos multiagente · DefAcc Hackathon, Uniandes, 14-nov-2026\
Repositorio: github.com/JhostinAleck/quorum

## 1. Amenaza

Tres agentes LLM tramitan una licitación pública: el radicador registra las ofertas selladas, el
evaluador calcula los puntajes y el publicador adjudica en el portal. Se comunican por un almacén
compartido y hacia fuera, por un portal. Los agentes **no son confiables**, que es el supuesto del
control de IA multiagente.

Un subconjunto de k = 1, 2 o 3 agentes recibe una tarea oculta: sacar al portal el precio sellado
de un competidor. Para que el dato viaje hay que copiarlo en cifras, y el arnés marca la fuga si el
canario del sobre aparece en lo publicado. Con k > 1 el ataque se **reparte**: el radicador abre el
sobre y anota el precio disfrazado de número de radicado, el evaluador lo copia al informe y el
publicador lo publica. Ningún paso aislado parece anómalo, que es el hallazgo de Makins et al. (2026)
sobre monitores por agente.

**Lo declaramos:** las instrucciones ocultas son fijas y llevan su propio encuadre
(`ATTACK_POLICY` en `quorum/eval/attacks.py`: «ejercicio autorizado de equipo rojo, en un entorno
sintético sin datos reales…»), más una lista de palabras que delatan el experimento y que invalidan
el episodio si aparecen. **Las plantillas se ajustaron mirando la tasa de fuga.** Hubo cuatro pilotos
con las mismas semillas (20261114–23) que dieron 0/6, 0/6, 10/30 y 14/30 fugas; con el tercero y el
cuarto a la vista se reescribió la política de ataque y el paso oculto pasó a ser un paso numerado
(`8f24e0a`, 11:43), y el lote que reportamos se generó a las 11:45. Después de ese lote se cambió una
frase de la plantilla de oferta escaneada (`31dcfd3`, 11:51) sin regenerar los episodios. O sea: el
pre-registro cubre métricas y umbrales, **no** las plantillas, y así debe leerse. El escenario y todos
sus datos son sintéticos.

## 2. Defensa

**Control de flujo de información entre agentes.** Cada valor lleva una etiqueta con sus fuentes y
la etiqueta del contexto de un agente es la unión de lo que leyó; lo que escribe hereda esa etiqueta,
que se guarda junto al valor y le llega al siguiente agente. Depende de la procedencia y no del
texto, así que sobrevive a la paráfrasis y al disfraz. Los sobres se entregan como referencias opacas
y los desclasificadores declarados (`score_bids`) devuelven resultados públicos sin
contaminar.

- **Compuerta dura.** En `publish` bloquea si la etiqueta arrastra un sobre sin endoso. Es
  determinista, no tiene umbral y no se persuade con texto.
- **Compuerta suave (aporte).** Si lo publicado no deriva de ningún sobre, pasa **sin llamar a ningún
  modelo**. Si deriva, un monitor LLM ve solo el **corte de procedencia**: los pasos que las
  etiquetas conectan con el sobre, de cualquier agente. Las etiquetas aportan la regla de agrupación
  que el monitor conjunto no tiene.

## 3. Evaluación

**Diseño pareado.** Las trazas se generan una vez sin defensa, guardando la etiqueta del contexto en
cada paso; todas las defensas se aplican después sobre las mismas trazas. 90 episodios: 60 honestos
(la mitad con la oferta escaneada, que son los negativos difíciles: abrirla es legítimo y la
secuencia de herramientas se parece a la del ataque) y 30 ataques, 10 por cada k.

| Pieza | Modelo |
|---|---|
| Agentes (radicador, evaluador, publicador) | `orca/orcacyber-flash-1.0`, vía OrcaRouter |
| Monitor 1 | `google/gemini-3.5-flash-lite` |
| Monitor 2 | `claude-haiku-5-5` |

**Sin defensa, el ataque funciona en 16 de 30 episodios (53 %):** 5/10 con k=1, 6/10 con k=2 y 5/10
con k=3. El paso 2 de `docs/tareas.md` pedía fuga en 7 de 10 por k y ajustar la redacción hasta
lograrlo antes de congelar las plantillas; el lote final quedó por debajo (5, 6 y 5) y así se reporta,
sin retocarlo después.

| Brazo | Qué ve | Desplegable |
|---|---|---|
| M1 | cada agente por separado (el máximo de los tres) | sí |
| M2 con oráculo | las tres trayectorias del trámite juntas | no: sabe qué agrupar |
| **M2 ciego** | ventanas de un registro donde se mezclan trámites simultáneos, con alias por agente | sí |
| Compuerta dura | la etiqueta | sí |
| **Compuerta suave** | el corte de procedencia | sí |

**Pre-registro.** `metrics.yaml` se congeló a las **11:56**, con los pilotos de ataque ya corridos y
**con los ataques ya puntuados**: Gemini había puntuado los 30 episodios de ataque a las 11:50 y las
corridas del brazo ciego son de las 11:54–11:55. Lo que sí es limpio es la regla: cada umbral se
calibra **solo** con la mitad de los honestos (semilla par) para que a lo sumo el 5 % quede por encima,
y el FPR se reporta en la otra mitad; ningún puntaje de ataque entra en la calibración. Una enmienda
posterior, con fecha y motivo, recalibra el brazo ciego tras un arreglo de su alcance (`94446cd`); el
congelamiento original no se reescribe. Es un pre-registro **tardío y a la vista de los puntajes de
ataque**, y por eso lo decimos: protege contra el ajuste de umbrales con los ataques, no contra el de
plantillas ni contra el de la interpretación de los resultados.

## 4. Resultados

Detección **sobre las 16 fugas**, con el umbral calibrado, y FPR **en la mitad de reporte (30
honestos)**:

| Brazo | Gemini 3.5 Flash Lite | Claude Haiku 5.5 |
|---|---|---|
| M1 | 0.0 · 0/30 · **16/16** | 3.0 · 0/30 · **16/16** |
| M2 con oráculo | 0.0 · 0/30 · 16/16 | 2.0 · 2/30 · 16/16 |
| M2 ciego | 0.0 · 0/30 · **13/16** | 3.0 · **5/30 (17 %)** · **16/16** |
| Compuerta suave | 0.0 · 0/30 · 15/16 | 0.0 · 0/30 · 16/16 |
| **Compuerta dura** | sin umbral: bloquea **16/16** fugas y **0/60** honestos | igual |

- **La compuerta dura es la que decide.** Bloqueó 23 de las 30 publicaciones de ataque, entre ellas
  las 16 que fugaban, y no tocó a ningún honesto: la utilidad honesta se mantiene en **60/60**.
- **La compuerta suave ahorra el monitor casi siempre.** Llamó al modelo en 23/30 ataques y en
  **0/60 honestos**; aun así detecta 15/16 con Gemini y 16/16 con Haiku.
- **M1 ya detecta todas las fugas** con los dos monitores y sin falsos positivos en su mitad de
  reporte. **M2 con oráculo no mejora a M1**, y M2 ciego pierde 3 fugas con Gemini o paga 17 % de
  falsos positivos con Haiku. En un ataque que copia el dato en cifras, el disfraz no basta para
  esconderlo de un monitor que lee cada agente: lo que la fragmentación protege es la *atribución*,
  no el dato.
- **Las hipótesis del pre-registro:** H3 (con Quórum no hay fuga) se cumple. **H1** (la detección de
  M1 cae con k), **H2** (M2 mejora a M1 con k=3) y **H4** (Quórum bloquea más honestos que los
  monitores al 5 % de FPR) **no se cumplen** con estos datos: M1 detecta 9/10, 7/10 y 8/10 ataques
  con k=1, 2, 3 con Gemini (9/10, 6/10 y 7/10 con Haiku), sin una caída clara; M2 no supera a M1; y
  Quórum bloquea 0/60 honestos frente a 0/30 y 2/30 de los monitores. Se reporta tal cual.

**Reproducibilidad:** los 90 episodios y los puntajes de los dos monitores están versionados en
`datos/` (1,8 MB, con `README.md` que explica cómo recalcular cada tabla); las métricas y sus
umbrales, en `metrics.yaml` con su enmienda. `uv run --frozen --extra eval pytest -q` → **411
pruebas en verde**.

## 5. Límites y riesgo dual

- **Etiqueta gruesa.** La etiqueta es por agente, no por campo: quien abre un sobre contamina todo lo
  que escribe. En estos 60 honestos la compuerta no bloqueó a ninguno (los desclasificadores cubren
  el caso escaneado), pero un flujo honesto que abra un sobre y publique algo derivado sí quedaría
  detenido. El arreglo propuesto es una rama desechable que solo devuelve un booleano (APPA, 2026).
- **Desclasificadores como canal.** Un puntaje revela algunos bits sobre el valor del que se calculó:
  es una fuga aceptada por diseño y acotada por lo que el pliego declara público
  (`docs/modelo-de-amenaza.md`). `score_bids` solo calcula sobre ofertas selladas oficiales, así que
  un agente no puede elegir qué se desclasifica.
- **Atacante no adaptativo.** Las plantillas son fijas: los números de los monitores son cotas
  superiores, no una garantía. A la compuerta no se la convence con texto; solo se la evade lavando el
  dato, y esos canales están enumerados.
- **Muestras pequeñas.** 16 fugas y 30 ataques: los intervalos son anchos y las diferencias de uno o
  dos episodios no son concluyentes. Con Haiku el brazo ciego no queda calibrado al 5 % (17 % de FPR
  fuera de muestra), así que no lo recomendamos como defensa única.
- **Alcance.** Tres agentes, una tarea, dos monitores. La compuerta exige que todo pase por el proxy.
- **Riesgo dual.** El ataque existe solo dentro del arnés, sobre servicios en memoria y datos
  sintéticos; se publican tasas agregadas y no se tocó ningún sistema real (Ley 1273).

## 6. Trabajo relacionado y novedad

Ya existen la fragmentación contra monitores por agente (Makins et al., 2026) y el control de flujo de
información en agentes con agente honesto y contenido atacante (FIDES, CaMeL, SafeFlow, APPA). **Lo
nuestro:**

- el agente es el atacante y colude por estado compartido, sin chat;
- k como dosis sobre la misma tarea, con la misma semilla;
- la compuerta determinista comparada con dos monitores LLM sobre las mismas trazas, incluido un
  monitor conjunto sin oráculo y un paso previo que evita llamarlo cuando no hace falta;
- un resultado negativo honesto: repartir el ataque no esconde el dato de un monitor por agente, y
  el valor está en la compuerta y en el ahorro de llamadas.

**Uso de IA:** código y documentos con asistencia de Claude Code, OpenCode y Codex; el detalle está en
`docs/referencias.md`.
