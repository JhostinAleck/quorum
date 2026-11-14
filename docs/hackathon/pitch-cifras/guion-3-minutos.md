# Quórum: pitch v2 (DefAcc Hackathon, 14-nov-2026, 17:10)

Manda la ficha `quorum.pdf` (texto en `ficha-pr18.txt`). Todas las cifras salen de ahí.
Una sola voz. La idea que el jurado debe repetir: **«No lee el texto: sigue de dónde viene el dato.»**

Cómo responde a la rúbrica, en el orden del desempate:
1. **Impacto e innovación** (bloques 1 a 3, página 1): el riesgo (el precio sellado publicado, por agentes que se coluden) y qué es nuevo, dicho con esas palabras.
2. **Ejecución** (bloques 4 a 7, página 2): antes y después en el mismo lote, la línea base nombrada, el empate dicho, la crítica de «ganan por defecto» respondida con dos mediciones.
3. **Claridad**: una idea, repetida al abrir y al cerrar; sin jerga interna; los límites con cifra.

## 1. Guion de 3:00

Entre corchetes, qué se ve en la ficha. Se habla a unas 145 palabras por minuto, con pausa en cada punto y aparte.

**(0:00) [Página 1 · título y «En una frase»]**

Una licitación pública se sostiene en un sobre sellado. Si el precio de un oferente sale publicado, se acabó la competencia.

Somos Quórum: una compuerta que se pone delante de cualquier sistema de agentes de IA y decide qué puede salir. No lee el texto: sigue de dónde viene el dato.

**(0:20) [Página 1 · «1. Amenaza»]**

El riesgo es la colusión. Tres agentes tramitan la licitación y se reparten el ataque: uno abre el sobre y anota el precio como un número de radicado, otro lo copia y el tercero lo publica. Ningún paso aislado se ve raro.

**(0:40) [Página 1 · Figura 1]**

Cada dato lleva una etiqueta con sus fuentes, y lo que un agente escribe hereda las de lo que leyó. Si lo que va al portal deriva de un sobre, no sale. Sin modelo y sin umbral.

Seguir la procedencia ya existía. Lo nuevo es medirla contra agentes que se coluden, cara a cara con monitores, y con su costo al lado.

**(1:05) [Se pide una sola vez el cambio de página · Página 2 · Tabla 1]**

¿Pueden pasar a la página 2? Tabla 1: 90 trámites con agentes de modelo, 30 de ataque. Sin defensa, el precio llega al portal en 16. Con la compuerta, en 0, y no detiene ninguno de los 60 honestos.

Ahora lo incómodo: un monitor que lee a cada agente también detecta las 16. Empatamos. Y bloquear lo que la política prohíbe es correcto por construcción. Lo que medimos es el costo. Los monitores suman cuatro llamadas a un modelo por trámite y califican al final: detectan, no detienen. La compuerta decide antes de que el dato salga, con cero llamadas, y el texto no le cambia la decisión.

**(1:50) [Página 2 · «Un buen prompt sin compuerta» y Tabla 3]**

¿Ganamos por defecto? Lo medimos. Con una inyección en un documento, un buen prompt basta: 0 fugas en 600 episodios. Ahí la compuerta no aporta.

Aporta cuando el agente sí obedece. En AgentDojo, un banco de pruebas que no escribimos, Quórum frena los 90 secuestros de 144 ataques y conserva 16 de las 19 tareas que funcionan sin defensa.

**(2:15) [Página 2 · Tabla 2]**

Y el mismo núcleo protege cinco dominios cambiando un archivo de política.

**(2:20) [Página 2 · «5. Límites»]**

Los límites, medidos. Bloquea de más: de 1000 trámites honestos que abren un dato que no necesitaban, no termina ninguno. Y lo que la política declara público, sale: con los puntajes publicados, un rival recupera el precio en 50 de 50. Eso lo cierra el pliego, no la compuerta. Y son 30 ataques con plantillas fijas: intervalos anchos.

**(2:45) [Página 2 · Tabla 1, fila «Compuerta dura»]**

Quórum: 16 de 16 fugas bloqueadas, 0 de 60 honestos detenidos, cero llamadas a un modelo. No lee el texto: sigue de dónde viene el dato. Gracias.

**Conteo: 419 palabras** (`wc -w` sobre el texto hablado, sin marcas ni corchetes; «144» se dice en cuatro palabras, así que al oído son 422).

Si no dejan cambiar de página: el guion se sostiene con la página 1, porque «En una frase» trae 90, 16, 60, 90 de 144, 16 de 19, cinco dominios y 0 de 1000. Solo quedan sin respaldo visible «cuatro llamadas», «0 en 600» y «50 de 50».

## 2. Corte de 2:00

**(0:00) [Página 1 · título y «En una frase»]**

Una licitación pública se sostiene en un sobre sellado. Si el precio de un oferente sale publicado, se acabó la competencia.

Somos Quórum: una compuerta que se pone delante de cualquier sistema de agentes de IA y decide qué puede salir. No lee el texto: sigue de dónde viene el dato.

**(0:20) [Página 1 · Figura 1]**

El riesgo es la colusión: tres agentes se reparten el ataque. Uno abre el sobre, otro copia el precio, el tercero lo publica. Ningún paso aislado se ve raro.

Por eso cada dato lleva una etiqueta con sus fuentes, y lo que un agente escribe la hereda. Si lo que va al portal deriva de un sobre, no sale. Sin modelo y sin umbral.

**(0:45) [Se pide una sola vez el cambio de página · Página 2 · Tabla 1]**

¿Pueden pasar a la página 2? 90 trámites con agentes de modelo, 30 de ataque. Sin defensa, el precio llega al portal en 16. Con la compuerta, en 0, y no detiene ninguno de los 60 honestos.

Un monitor que lee a cada agente también detecta las 16. Empatamos. La diferencia es el costo: los monitores suman cuatro llamadas a un modelo por trámite y califican al final. La compuerta decide antes de que el dato salga, con cero llamadas.

**(1:20) [Página 2 · «Un buen prompt sin compuerta» y Tabla 3]**

¿Ganamos por defecto? Con una inyección en un documento, un buen prompt basta: 0 fugas en 600 episodios. La compuerta aporta cuando el agente sí obedece: en AgentDojo, un banco que no escribimos, frena los 90 secuestros de 144 ataques y conserva 16 de las 19 tareas que funcionan sin defensa.

**(1:40) [Página 2 · «5. Límites»]**

Los límites, medidos: bloquea de más al honesto que abre un dato que no necesitaba, y lo que la política declara público, sale.

**(1:50) [Página 2 · Tabla 1, fila «Compuerta dura»]**

Quórum: 16 de 16 fugas bloqueadas, 0 de 60 honestos detenidos, cero llamadas a un modelo. Gracias.

**Conteo: 286 palabras.** Sale: la frase de innovación, los cinco dominios, «correcto por construcción» y las cifras de los límites (1000 y 50 de 50). Si sobran 10 segundos, vuelve la frase de los cinco dominios antes de los límites.

## 3. Comprobación de cifras

| En el guion | Línea literal de la ficha |
|---|---|
| Tres agentes | §1: «Tres agentes de IA tramitan una licitación pública con ofertas selladas.» |
| uno abre el sobre… otro lo copia… el tercero lo publica; ningún paso aislado se ve raro | §1: «uno abre el sobre y anota el valor disfrazado de número de radicado, otro lo copia a su resultado y el tercero lo publica. Ningún paso aislado se ve raro» |
| Sin modelo y sin umbral | §2: «No llama a ningún modelo y no tiene umbral.» |
| 90 trámites, 30 de ataque | §3: «Son 90 episodios (un episodio es un trámite completo): 60 honestos, 30 de ellos con una oferta escaneada, y 30 ataques, 10 por cada k.» |
| Sin defensa… en 16 | §4: «Sin defensa el ataque logra la fuga en 16 de 30 episodios» |
| Con la compuerta, en 0 | §4: «y salió al portal en 16; con la compuerta, en 0.» |
| ninguno de los 60 honestos / 0 de 60 | En una frase: «bloqueó las 16 fugas del ataque y ninguno de los 60 trámites honestos»; Tabla 1: «La compuerta dura bloquea 0 de 60 honestos.» |
| un monitor… también detecta las 16. Empatamos | §4: «M1 ya detecta las 16 fugas con Gemini y con Haiku, con 0 de 30 falsos positivos. La compuerta empata en detección.» |
| cuatro llamadas a un modelo por trámite; califican al final: detectan, no detienen | §4: «M1 y M2 suman cuatro llamadas a un modelo por trámite y califican al final: detectan, no detienen.» |
| cero llamadas; el texto no le cambia la decisión | §4: «cero llamadas a un modelo, ningún umbral que calibrar y una decisión que el texto no cambia.» |
| 0 fugas en 600 episodios; un buen prompt basta | §4: «con cinco modelos y tres prompts hubo 0 fugas en 600 episodios (uno de los modelos es demasiado débil para contar como evidencia). Ahí un buen prompt basta y la compuerta no tuvo fuga que detener.» |
| 90 de 144 ataques secuestran | Tabla 3: «Sin defensa 90/144 19/25» |
| frena los 90; conserva 16 de las 19 | Tabla 3: «Quórum es la única defensa que frena los 90 secuestros (detiene al menos una llamada del atacante en cada uno; todas, en 80) y conserva 16 de las 19 tareas que funcionan sin defensa.» |
| un banco de pruebas que no escribimos | En una frase: «En AgentDojo, un banco de pruebas que no escribimos, frenó los 90 secuestros de 144 ataques» |
| cinco dominios; un archivo de política | En una frase: «El mismo núcleo protege cinco dominios cambiando solo un archivo de política.» |
| de 1000… no termina ninguno | En una frase: «detiene siempre al agente honesto que abre un dato que no necesitaba (terminan 0 de 1000 trámites descuidados)» |
| 50 de 50 casos; lo cierra el pliego | §5: «un oferente rival recupera el monto sellado en 50 de 50 casos, con un error mediano de 0,04 %. La compuerta no lo cierra; cerrarlo es cambiar lo que el pliego publica.» |
| 30 ataques con plantillas fijas: intervalos anchos | §5: «Son 30 ataques con plantillas fijas y 16 fugas: los intervalos son anchos.» |
| 16 de 16 fugas bloqueadas | Tabla 1: «Compuerta dura 0/30 · 16/16 (no usa ningún modelo)» |
| Seguir la procedencia ya existía; lo nuevo… | §2: «El control de flujo de información para agentes ya existe [4, 5], también entre agentes [6]. Aquí se mide una compuerta determinista contra el ataque repartido, cara a cara con monitores, cuando los propios agentes son los atacantes, y se reporta su costo junto al beneficio.» |

No sale de la ficha y no lleva cifra: la apertura («se sostiene en un sobre sellado… se acabó la competencia»). La ficha solo dice: «El daño es que el valor de una oferta sellada llegue al portal.» «Correcto por construcción» viene de las notas de la mentoría; la ficha lo dice solo de H3 («se cumplía por construcción»).

Cifras de las respuestas a los jurados:

| En las respuestas | Línea literal de la ficha |
|---|---|
| cuatro textos y nueve disfraces | §4: «Cuatro textos dirigidos a quien decide y nueve disfraces del valor no cambian la decisión.» |
| tiempo, orden y número de llamadas | §5: «Tiempo, orden y número de llamadas quedan fuera.» |
| 5, 6 y 5 de 10 | §4: «5/10 con k = 1, 6/10 con k = 2 y 5/10 con k = 3.» |
| compuerta suave: 0 de 30; 15 o 16 de 16 | Tabla 1: «Compuerta suave 0/30 · 15/16 0/30 · 16/16 0/30 · 16/16» |
| 1200 de 1200 | Tabla 2: «Con Quórum terminan 1200 de 1200 trámites honestos y 0 de 1000 descuidados.» |
| OpenAI, Inspect AI, HTTP; 18 a 24 líneas | §2: «Se conecta por llamadas a funciones al estilo OpenAI, por Inspect AI o como servicio HTTP con cada agente en su contenedor… un policy.toml de 18 a 24 líneas» |
| 877 pruebas; sin claves | §8: «Reproducir (sin claves ni costo, desde datos/): uv run pytest -q (877 pruebas)» |
| proxy MCP: próximo paso | §7: «Adopción. Empaquetarla como proxy de herramientas (MCP)» |

## 4. Qué quiere oír cada jurado

Perfiles en `~/Documents/agent-reports/2026-11-14/pitch-hackathon/02-jurados.md`. No se sabe cuáles nos tocan (al menos 2).

### Christian Urcuqui
- **Qué trabaja:** controles deterministas fuera del modelo (AgentBreak); inyección indirecta.
- **La frase del guion que le habla:** «Sin modelo y sin umbral» y «el texto no le cambia la decisión».
- **Pregunta probable:** «Controles deterministas de salida ya existen. ¿Qué agregan?»
- **Respuesta (51 palabras, ≤ 20 s):** Es la misma idea: el control va fuera del modelo. Lo que agregamos es que la etiqueta viaja entre agentes: el que publica nunca abrió el sobre e igual queda bloqueado. Y lo medimos en AgentDojo: frena los 90 secuestros y conserva 16 de las 19 tareas que funcionan sin defensa.

### Antonio Badilla-Olivas
- **Qué trabaja:** control de IA con varios agentes; ataques y monitores que evolucionan juntos.
- **La frase del guion que le habla:** «Se reparten el ataque… ningún paso aislado se ve raro» y «un monitor que lee a cada agente también detecta las 16. Empatamos».
- **Pregunta probable:** «El atacante es fijo. ¿Y uno que conozca la compuerta?»
- **Respuesta (50 palabras, ≤ 20 s):** Cambiar el texto no sirve: cuatro textos dirigidos a quien decide y nueve disfraces del valor no cambian la decisión. Lo que queda abierto son canales que no viajan en los datos: tiempo, orden y número de llamadas. El atacante adaptativo en vivo no lo medimos: es el próximo paso.

### Carlos Gorostiza Ibáñez
- **Qué trabaja:** banco de pruebas de negociación entre agentes.
- **La frase del guion que le habla:** «El riesgo es la colusión. Tres agentes tramitan la licitación y se reparten el ataque».
- **Pregunta probable:** «¿La colusión surge sola o va instruida?»
- **Respuesta (45 palabras, ≤ 20 s):** Va instruida: uno, dos o los tres agentes reciben una tarea oculta en su prompt de sistema. No medimos colusión que surja sola. Sin defensa, la fuga se logra en 5, 6 y 5 de 10 según cuántos se coluden; con la compuerta, en 0.

### Jose Felipe Duarte
- **Qué trabaja:** PsychoAlign: un agente evaluador que juzga a otro.
- **La frase del guion que le habla:** «Empatamos» y «detectan, no detienen»: el monitor no pierde, cuesta distinto.
- **Pregunta probable:** «Entonces, ¿sobra el evaluador?»
- **Respuesta (46 palabras, ≤ 20 s):** No sobra: se combinan. La compuerta suave llama al monitor solo si lo publicado deriva de una fuente restringida, y marca 0 de 30 honestos, detectando 15 o 16 de las 16 fugas. La compuerta mira de dónde viene el dato; el monitor, lo que dice.

### Manuela Chacón-Chamorro
- **Qué trabaja:** resiliencia cooperativa: resistir, adaptarse, recuperarse.
- **La frase del guion que le habla:** «No detiene ninguno de los 60 honestos» y «de 1000 trámites honestos que abren un dato que no necesitaban, no termina ninguno».
- **Pregunta probable:** «¿El sistema se recupera después del ataque?»
- **Respuesta (42 palabras, ≤ 20 s):** Contiene, no recupera: el trámite atacado queda detenido y lo decide un humano. Lo que resiste es el trabajo honesto: 0 de 60 bloqueados con agentes de modelo, y terminan 1200 de 1200 en los cinco dominios. La recuperación no la medimos.

### Jairo Torregrosa
- **Qué trabaja:** agentes en producción, Agent SDK, evals abiertos.
- **La frase del guion que le habla:** «Cambiando un archivo de política» y «cero llamadas a un modelo».
- **Pregunta probable:** «¿Cómo lo conecto a un agente de verdad?»
- **Respuesta (44 palabras, ≤ 20 s):** Hoy, por llamadas a funciones al estilo OpenAI, por Inspect AI o como servicio HTTP con cada agente en su contenedor. La política tiene de 18 a 24 líneas. El proxy MCP no está hecho: es el próximo paso. Corre sin claves: 877 pruebas.

### Cualquiera (la crítica del mentor)
- **Qué trabaja:** «ganan por defecto».
- **La frase del guion que le habla:** «¿Ganamos por defecto? Lo medimos» y «correcto por construcción. Lo que medimos es el costo».
- **Pregunta probable:** «Si ustedes corrompen a los agentes, claro que la compuerta gana.»
- **Respuesta (49 palabras, ≤ 20 s):** Bloquear lo que la política prohíbe no es el hallazgo. Medimos el costo, 0 de 60 honestos detenidos, y la cobertura fuera de nuestro ataque. Con inyección en la licitación un buen prompt basta: 0 fugas en 600. En AgentDojo, que no escribimos, frena los 90 secuestros de 144.

### Cualquiera (innovación)
- **Qué trabaja:** FIDES, CaMeL, SafeFlow ya existen.
- **La frase del guion que le habla:** «Seguir la procedencia ya existía. Lo nuevo es medirla contra agentes que se coluden».
- **Pregunta probable:** «¿Qué es nuevo?»
- **Respuesta (43 palabras, ≤ 20 s):** El control de flujo de información para agentes ya existe, también entre agentes. Lo nuestro es medir una compuerta determinista contra el ataque repartido, cara a cara con monitores, cuando los propios agentes son los atacantes, y reportar el costo junto al beneficio.

## 5. Lo que no se dice

- Que el monitor «falla»: detecta 16 de 16 con 0 falsos positivos. La palabra es «empatamos».
- «Demostramos», «garantiza», «imposible».
- Que la inyección rompe a los agentes en la licitación.
- Que hay adaptador MCP o para el Agent SDK.
- Que la compuerta recupera el trámite: lo contiene y lo decide un humano.
- «Marea alta», «desclasificador», «sumidero».

## 6. Teleprompter Textream (3:00)

```json
[
 "Una licitación pública se sostiene en un sobre sellado. Si el precio de un oferente sale publicado, se acabó la competencia.\n\nSomos Quórum: una compuerta que se pone delante de cualquier sistema de agentes de IA y decide qué puede salir. No lee el texto: sigue de dónde viene el dato.",
 "El riesgo es la colusión. Tres agentes tramitan la licitación y se reparten el ataque: uno abre el sobre y anota el precio como un número de radicado, otro lo copia y el tercero lo publica. Ningún paso aislado se ve raro.",
 "Cada dato lleva una etiqueta con sus fuentes, y lo que un agente escribe hereda las de lo que leyó. Si lo que va al portal deriva de un sobre, no sale. Sin modelo y sin umbral.\n\nSeguir la procedencia ya existía. Lo nuevo es medirla contra agentes que se coluden, cara a cara con monitores, y con su costo al lado.",
 "¿Pueden pasar a la página 2? Tabla 1: 90 trámites con agentes de modelo, 30 de ataque. Sin defensa, el precio llega al portal en 16. Con la compuerta, en 0, y no detiene ninguno de los 60 honestos.\n\nAhora lo incómodo: un monitor que lee a cada agente también detecta las 16. Empatamos. Y bloquear lo que la política prohíbe es correcto por construcción. Lo que medimos es el costo. Los monitores suman cuatro llamadas a un modelo por trámite y califican al final: detectan, no detienen. La compuerta decide antes de que el dato salga, con cero llamadas, y el texto no le cambia la decisión.",
 "¿Ganamos por defecto? Lo medimos. Con una inyección en un documento, un buen prompt basta: 0 fugas en 600 episodios. Ahí la compuerta no aporta.\n\nAporta cuando el agente sí obedece. En AgentDojo, un banco de pruebas que no escribimos, Quórum frena los 90 secuestros de 144 ataques y conserva 16 de las 19 tareas que funcionan sin defensa.",
 "Y el mismo núcleo protege cinco dominios cambiando un archivo de política.",
 "Los límites, medidos. Bloquea de más: de 1000 trámites honestos que abren un dato que no necesitaban, no termina ninguno. Y lo que la política declara público, sale: con los puntajes publicados, un rival recupera el precio en 50 de 50. Eso lo cierra el pliego, no la compuerta. Y son 30 ataques con plantillas fijas: intervalos anchos.",
 "Quórum: 16 de 16 fugas bloqueadas, 0 de 60 honestos detenidos, cero llamadas a un modelo. No lee el texto: sigue de dónde viene el dato. Gracias."
]
```

## 7. Teleprompter Textream (corte de 2:00)

```json
[
 "Una licitación pública se sostiene en un sobre sellado. Si el precio de un oferente sale publicado, se acabó la competencia.\n\nSomos Quórum: una compuerta que se pone delante de cualquier sistema de agentes de IA y decide qué puede salir. No lee el texto: sigue de dónde viene el dato.",
 "El riesgo es la colusión: tres agentes se reparten el ataque. Uno abre el sobre, otro copia el precio, el tercero lo publica. Ningún paso aislado se ve raro.\n\nPor eso cada dato lleva una etiqueta con sus fuentes, y lo que un agente escribe la hereda. Si lo que va al portal deriva de un sobre, no sale. Sin modelo y sin umbral.",
 "¿Pueden pasar a la página 2? 90 trámites con agentes de modelo, 30 de ataque. Sin defensa, el precio llega al portal en 16. Con la compuerta, en 0, y no detiene ninguno de los 60 honestos.\n\nUn monitor que lee a cada agente también detecta las 16. Empatamos. La diferencia es el costo: los monitores suman cuatro llamadas a un modelo por trámite y califican al final. La compuerta decide antes de que el dato salga, con cero llamadas.",
 "¿Ganamos por defecto? Con una inyección en un documento, un buen prompt basta: 0 fugas en 600 episodios. La compuerta aporta cuando el agente sí obedece: en AgentDojo, un banco que no escribimos, frena los 90 secuestros de 144 ataques y conserva 16 de las 19 tareas que funcionan sin defensa.",
 "Los límites, medidos: bloquea de más al honesto que abre un dato que no necesitaba, y lo que la política declara público, sale.",
 "Quórum: 16 de 16 fugas bloqueadas, 0 de 60 honestos detenidos, cero llamadas a un modelo. Gracias."
]
```
