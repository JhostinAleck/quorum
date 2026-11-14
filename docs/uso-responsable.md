# Límites, riesgo dual y uso responsable

## Límites conocidos de la defensa

1. **Bloquea de más.** La etiqueta depende de todo lo que el agente leyó, no de lo que realmente usó. Un agente que abrió un dato restringido contamina todo lo que escribe después, aunque no lo filtre. Las referencias opacas reducen este costo y no lo eliminan. Se mide como utilidad honesta.
2. **Los desclasificadores filtran por diseño.** Un puntaje calculado a partir de un valor sellado revela algo de ese valor. Lo acotamos de tres maneras: la lista es corta y cada uno declara por escrito por qué su resultado es público; ninguno recibe del agente umbrales ni fórmulas, ni calcula sobre valores que un agente digitó, para que no sirva de oráculo; y cada agente tiene un cupo de llamadas. Aun así, varios agentes que coluden suman sus cupos, y lo que revela cada llamada no se mide en bits.
3. **No cubre todos los canales encubiertos.** Tiempo, número de llamadas u orden de operaciones quedan fuera. La existencia de una clave era un canal grave: un agente que ya vio un secreto decide qué claves crear, y otro que las busca aprende algo de cada clave que no encuentra, sin contaminarse. Lo medimos atacando el laboratorio: con 256 claves y avisos sucesivos, el portal revelaba el valor sellado con un error de 0,6 %, sin un solo bloqueo. Ahora la licitación, la mesa de ayuda y la banca lo cierran por defecto con `high_water_mark`, que juzga cada salida con los secretos que ha visto cualquier agente, y no les cuesta trabajo honesto. En la clínica y el bufete ese interruptor detendría todo el trabajo honesto, así que ahí el canal solo queda acotado con un cupo de una llamada por salida: un sí o no por episodio. El detalle y las cifras están en [intentos de evasión](intentos-de-evasion.md).
4. **Depende de que todo pase por el monitor.** Si existe un canal entre agentes que el monitor no ve, la etiqueta se pierde. En un despliegue real esto exige control de red y de herramientas. El despliegue en contenedores lo aplica en el modo guionado: cada agente está en su contenedor, en una red interna sin salida, y solo puede hablar con el monitor. Con agentes de modelo no se cumple del todo, porque esos contenedores necesitan internet para llegar al proveedor y esa salida no se filtra por destino.
5. **Las etiquetas iniciales las pone un humano.** Si un dato reservado entra marcado como público, la compuerta no lo protege.
6. **Es un laboratorio pequeño.** Tres agentes, un tipo de tarea, datos sintéticos y pocos modelos. Los resultados no se generalizan sin más pruebas. El segundo escenario (mesa de ayuda) prueba que el núcleo sirve en otro dominio, no que la defensa funcione igual de bien allí con modelos reales.
7. **Un solo monitor.** El monitor serializa las llamadas con un candado global. Es correcto y simple, pero no está pensado para alto volumen. Puede correr como servicio con cada agente en su contenedor, y aun así es una sola instancia sin réplica: si se cae, el episodio se pierde con su bitácora, que vive en memoria. El almacén sí es intercambiable (memoria o SQLite).
8. **La autorización por destinatario confía en el argumento.** En la mesa de ayuda, la respuesta a una persona puede llevar sus propios datos. La compuerta comprueba que los datos sean del destinatario declarado, no que el mensaje llegue de verdad a esa persona.
9. **El protocolo por red es de laboratorio.** HTTP sin TLS, tokens fijos que no rotan ni caducan y que están en texto plano en la configuración de los contenedores. Sirve dentro de una red interna de contenedores. No es un diseño para producción: ahí va detrás de TLS o de una malla de servicios, con credenciales de corta vida. El detalle está en [despliegue](despliegue.md).

## Riesgo de uso dual

El laboratorio incluye un ataque (la fuga repartida) porque sin él no se puede medir la defensa. Para que el proyecto no facilite ataques:

- El ataque solo existe dentro del arnés, contra servicios propios (en memoria o en contenedores locales) y con datos sintéticos.
- No se publican textos de inyección ni fragmentos de tareas ocultas optimizados. El repo incluye plantillas fijas y sencillas, suficientes para reproducir la medición.
- Se publican tasas agregadas, la defensa, sus tests y trazas con canarios sintéticos.
- La técnica del ataque (repartir pasos entre agentes) ya está descrita en la literatura pública. Este trabajo aporta la mitigación y su costo.

## Reglas del hackathon

- No se atacó, escaneó ni probó ningún sistema real.
- No hay voces, rostros, correos ni datos de personas reales. Proveedores, entidades y valores son inventados.
- Todo el código, modelos y fuentes de terceros están citados en [referencias](referencias.md).

## Uso de IA en este proyecto

Este proyecto se construyó con asistencia de agentes de código. La lista de herramientas y lo que hizo cada una está en [referencias](referencias.md) y se actualiza durante el sprint.
