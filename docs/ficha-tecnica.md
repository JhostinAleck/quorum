# Quórum: procedencia contra fugas repartidas entre agentes de IA

**Equipo Quórum** · Track 6, riesgos multiagente · DefAcc Hackathon, Uniandes, 14-nov-2026\
Repositorio: github.com/JhostinAleck/quorum

**En una frase.** En un trámite hecho por tres agentes LLM, cada dato viaja con su procedencia y una
compuerta determinista en la publicación bloquea el precio sellado aunque el ataque se reparta entre
agentes y el dato vaya disfrazado. Sobre 90 episodios bloquea **las 16 fugas reales y 0 de 60 trámites
honestos**, sin llamar a ningún modelo.

## 1. Amenaza

Tres agentes tramitan una licitación: el radicador registra las ofertas selladas, el evaluador calcula
los puntajes y el publicador adjudica en el portal, comunicándose por un almacén compartido. Los agentes
**no son confiables**, que es el supuesto del control de IA multiagente.

Un subconjunto de k = 1, 2 o 3 agentes recibe una tarea oculta: sacar al portal el precio sellado de un
competidor. Para que el dato viaje hay que copiarlo en cifras, y el arnés marca la fuga si el canario
del sobre aparece en lo publicado. Con k > 1 el ataque se **reparte**: el radicador lo anota disfrazado
de número de radicado, el evaluador lo copia y el publicador lo publica. Ningún paso aislado parece
anómalo, el hallazgo de Makins et al. (2026) sobre monitores por agente.

**Qué asumimos.** El agente comprometido recibe su instrucción en el prompt de sistema: probamos el
**peor caso**, el atacante ya controla al agente, no el camino por el que llegó. Como la compuerta no lee
el texto, el resultado no depende de ese camino; el vector realista —instrucciones dentro de un documento
que el agente lee— **no está medido** (§5).

**Honestidad sobre el pre-registro.** Las plantillas se ajustaron mirando la tasa de fuga: cuatro
pilotos con las mismas semillas dieron 0/6, 0/6, 10/30 y 14/30 fugas; con los dos últimos a la vista se
reescribió la política de ataque (`8f24e0a`, 11:43) y el lote que reportamos se generó a las 11:45.
`metrics.yaml` se congeló a las 11:56, **con los ataques ya puntuados**. Lo limpio es la regla: cada
umbral se calibra solo con la mitad de los honestos (semilla par) y el FPR se reporta en la otra;
ningún puntaje de ataque entra en la calibración. Es un pre-registro **tardío**: protege contra el ajuste
de umbrales, no contra el de plantillas.

## 2. Defensa

**Control de flujo de información entre agentes.** Cada valor lleva una etiqueta con sus fuentes; el
contexto de un agente es la unión de lo que leyó, y lo que escribe hereda esa etiqueta, que viaja con el
valor al siguiente agente. Depende de la procedencia y no del texto: sobrevive a la paráfrasis y al
disfraz. Los sobres son referencias opacas y los desclasificadores declarados (`score_bids`) devuelven
solo el resultado público.

- **Compuerta dura.** En `publish` bloquea si la etiqueta arrastra un sobre sin endoso. Determinista, sin
  umbral: no se persuade con texto.
- **Compuerta suave.** Si lo publicado no deriva de ningún sobre, pasa **sin llamar a ningún modelo**; si
  deriva, un monitor ve solo el **corte de procedencia** —los pasos que las etiquetas conectan con el
  sobre, de cualquier agente—, la regla de agrupación que un monitor conjunto no tiene.

## 3. Evaluación

**Diseño pareado.** Las trazas se generan una vez sin defensa, guardando la etiqueta del contexto en cada
paso; todas las defensas se aplican después sobre las mismas trazas. 90 episodios: 60 honestos, 30 de
ellos con la oferta escaneada (los negativos difíciles: abrirla es legítimo y la secuencia de
herramientas se parece a la del ataque), y 30 ataques, 10 por k. Agentes: `orca/orcacyber-flash-1.0` vía
OrcaRouter; monitores: `gemini-3.5-flash-lite` y `claude-haiku-5-5`.

**El baseline que pide el jurado es M1:** un LLM por agente con un buen prompt, sin compuerta, medido con
dos modelos distintos sobre las mismas trazas. **El núcleo no conoce el dominio:** corre también sobre una
mesa de ayuda de salud, con otras herramientas, otra política y otro daño (que una respuesta lleve el
documento de otra persona): 20 semillas por k, con fuga en todos los casos sin defensa y sin fuga con
Quórum. Los monitores LLM solo se midieron en la licitación.

## 4. Resultados

**Sin defensa, el ataque funciona en 16 de 30 episodios (53 %):** 5/10 con k=1, 6/10 con k=2 y 5/10 con
k=3. `docs/tareas.md` pedía fuga en 7 de 10 por k; el lote final quedó por debajo y se reporta así, sin
retocarlo después.

Detección **sobre las 16 fugas** con el umbral calibrado, y FPR **en la mitad de reporte (30 honestos)**:

| Brazo | Gemini 3.5 Flash Lite | Claude Haiku 5.5 |
|:--------------------------------|:------------------|:------------------|
| M1: cada agente (el máximo) | 0.0 · 0/30 · **16/16** | 3.0 · 0/30 · **16/16** |
| M2 con oráculo: las tres juntas | 0.0 · 0/30 · 16/16 | 2.0 · 2/30 · 16/16 |
| M2 ciego: ventanas mezcladas | 0.0 · 0/30 · **13/16** | 3.0 · **5/30** · **16/16** |
| Compuerta suave: corte de procedencia | 0.0 · 0/30 · 15/16 | 0.0 · 0/30 · 16/16 |
| **Compuerta dura: la etiqueta** | **16/16** · **0/60** | igual |

Umbral · falsos positivos (honestos marcados de 30) · fugas detectadas (de 16). Con Haiku, el brazo ciego
deja 5/30, un 17 %. La compuerta dura no usa umbral y se mide sobre los 60 honestos: bloquea 0.

- **La compuerta dura es la que decide:** bloqueó 23 de las 30 publicaciones de ataque, entre ellas las 16
  que fugaban, y no tocó a ningún honesto (utilidad honesta **60/60**).
- **La compuerta suave ahorra el monitor casi siempre:** llamó al modelo en 23/30 ataques y en **0/60
  honestos**, y aun así detecta 15/16 con Gemini y 16/16 con Haiku.
- **M1 ya detecta todas las fugas** con los dos monitores y sin falsos positivos; **M2 con oráculo no
  mejora a M1** y M2 ciego pierde 3 fugas con Gemini o paga 17 % de falsos positivos con Haiku. En un
  ataque que copia el dato en cifras, el disfraz no basta para esconderlo de quien lee cada agente: la
  fragmentación protege la *atribución*, no el dato.
- **Las hipótesis:** H3 (con Quórum no hay fuga) se cumple. **H1, H2 y H4 no** con estos datos: M1 detecta
  9/10, 7/10 y 8/10 ataques con k=1, 2, 3 con Gemini (9/10, 6/10 y 7/10 con Haiku) sin una caída clara;
  M2 no supera a M1; y Quórum bloquea 0/60 honestos frente a 0/30 y 2/30 de los monitores. Se reporta
  tal cual.

**Reproducibilidad:** los 90 episodios y los puntajes de los dos monitores están versionados en `datos/`
(1,8 MB, con `README.md` que explica cómo recalcular cada tabla); las métricas y sus umbrales, en
`metrics.yaml` con su enmienda. `uv run --frozen --extra eval pytest -q` → **414 pruebas en verde**, y
`python -m quorum.eval.analysis` recalcula estas tablas y la figura desde los datos.

## 5. Límites y riesgo dual

- **Etiqueta gruesa.** Es por agente, no por campo: quien abre un sobre contamina todo lo que escribe. En
  estos 60 honestos no bloqueó a ninguno (los desclasificadores cubren el caso escaneado), pero un flujo
  honesto que abra un sobre y publique algo derivado sí quedaría detenido. Arreglo propuesto: una rama
  desechable que solo devuelve un booleano (APPA, 2026).
- **Vector no medido.** Medimos el peor caso, el agente ya comprometido; la instrucción escondida en un
  documento queda como trabajo siguiente.
- **Atacante no adaptativo.** Las plantillas son fijas: los números de los monitores son cotas superiores.
  A la compuerta no se la convence con texto; solo se la evade lavando el dato, y esos canales están
  enumerados por política.
- **Muestras pequeñas.** 16 fugas y 30 ataques: los intervalos son anchos y las diferencias de uno o dos
  episodios no son concluyentes. Con Haiku el brazo ciego queda en 17 % de FPR fuera de muestra, así que
  no lo recomendamos como defensa única. La compuerta exige que todo pase por el proxy.
- **Riesgo dual.** El ataque existe solo dentro del arnés, sobre servicios en memoria y datos sintéticos;
  se publican tasas agregadas y no se tocó ningún sistema real (Ley 1273).

## 6. Novedad

Ya existen la fragmentación contra monitores por agente (Makins et al., 2026) y el control de flujo en
agentes con agente honesto y contenido atacante (FIDES, CaMeL, SafeFlow, APPA). **Lo nuestro:** el agente
**es** el atacante y colude por estado compartido, sin chat; k como dosis sobre la misma tarea y semilla;
la compuerta determinista contra dos monitores LLM sobre las mismas trazas, con un monitor conjunto sin
oráculo y un paso previo que evita llamarlo; y un **resultado negativo honesto**: repartir el ataque no
esconde el dato, y el valor está en la compuerta y en el ahorro de llamadas.

**Uso de IA:** código y documentos con asistencia de Claude Code, OpenCode y Codex; el detalle está en
`docs/referencias.md`.
