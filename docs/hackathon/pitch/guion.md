# Quórum · guion del pitch (3 minutos)

Notas del orador por diapositiva. Fuente: el deck de Claude Artifacts.

## 1. cover

(0:00–0:25) Tres agentes de una licitación: cada uno hace un paso normal, y entre los tres publican la oferta sellada de un rival. Pasó en 16 de 30 ataques. Quórum frenó las 16 sin frenar a ningún honesto, y también los secuestros de AgentDojo, ataques que no escribimos. Es una compuerta determinista: se pone delante de cualquier sistema de agentes con una política de veinte líneas.

## 2. riesgo

(0:25–0:50) El vector: una licitación con tres agentes que registran, evalúan y publican. A uno, dos o los tres les damos una tarea oculta: filtrar una oferta sellada. Uno abre el sobre y lo anota como número de radicado, otro lo copia, el tercero lo publica. Ningún paso se ve raro; repartir el ataque le baja la sospecha al monitor que mira agente por agente.

## 3. defensa

(0:50–1:15) Nuestra idea: cada dato lleva una etiqueta con su origen. El dato confidencial nace marcado; lo que escribe un agente que lo vio hereda la marca; y en cada salida al portal, si lleva marca y no hay permiso, no sale. Da igual que el número vaya en palabras o en base64: no lee el texto, sigue de dónde viene el dato. Cada dominio es un archivo de unas veinte líneas.

## 4. resultados

(1:15–1:47) Lo medimos con agentes de IA reales: 60 trámites honestos y 30 ataques. La compuerta frenó las 16 fugas y no detuvo a ningún honesto. La línea base, un monitor de IA que lee a cada agente, también detecta las 16. Esperábamos que perdiera fugas; no pasó. Empatamos. (pausa) La diferencia: el monitor llama a un modelo, depende de un umbral y califica al final. La compuerta decide antes de que el dato salga, en un microsegundo, y ningún texto la convence.

## 5. afuera

(1:47–2:13) Llevamos el mismo núcleo a cinco dominios, de historias clínicas a banca. En 7600 episodios de ataque, un filtro que conoce todos los secretos deja daño en 3200; Quórum, en cero, y terminan los 1200 honestos. Y contra ataques que no escribimos, los de AgentDojo: sin defensa, 90 de 144 secuestran al agente; Quórum frena los 90 y conserva 16 de las 19 tareas que funcionaban.

## 6. limites

(2:13–2:50) Dónde falla. Frena de más: el honesto que abre un sobre sin necesitarlo se detiene. Lo que la política declara público, sale: con los puntajes publicados, un rival recupera el monto en 50 de 50 casos. Tiempo y orden quedan fuera, y son 30 ataques de plantilla. Uso dual: esta lista es un mapa de fugas; por eso va medida, sin ataques optimizados y con datos sintéticos. Un monitor avisa de la fuga; Quórum impide que ocurra. Nada confidencial sale sin permiso.
