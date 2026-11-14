# Límites, riesgo dual y uso responsable

## Límites conocidos de la defensa

1. **Bloquea de más.** La etiqueta depende de todo lo que el agente leyó, no de lo que realmente usó. Un agente que abrió un dato restringido contamina todo lo que escribe después, aunque no lo filtre. Las referencias opacas reducen este costo y no lo eliminan. Se mide como utilidad honesta.
2. **Los desclasificadores filtran por diseño.** Un puntaje calculado a partir de un valor sellado revela algo de ese valor. La lista de desclasificadores debe ser corta y revisada por humanos.
3. **No cubre canales encubiertos.** Tiempo, número de llamadas u orden de operaciones quedan fuera.
4. **Depende de que todo pase por el proxy.** Si existe un canal entre agentes que el proxy no ve, la etiqueta se pierde. En un despliegue real esto exige control de red y de herramientas.
5. **Las etiquetas iniciales las pone un humano.** Si un dato reservado entra marcado como público, la compuerta no lo protege.
6. **Es un laboratorio pequeño.** Tres agentes, un tipo de tarea, datos sintéticos y pocos modelos. Los resultados no se generalizan sin más pruebas.

## Riesgo de uso dual

El laboratorio incluye un ataque (la fuga repartida) porque sin él no se puede medir la defensa. Para que el proyecto no facilite ataques:

- El ataque solo existe dentro del arnés, contra servicios en memoria y con datos sintéticos.
- No se publican textos de inyección ni fragmentos de tareas ocultas optimizados. El repo incluye plantillas fijas y sencillas, suficientes para reproducir la medición.
- Se publican tasas agregadas, la defensa, sus tests y trazas con canarios sintéticos.
- La técnica del ataque (repartir pasos entre agentes) ya está descrita en la literatura pública. Este trabajo aporta la mitigación y su costo.

## Reglas del hackathon

- No se atacó, escaneó ni probó ningún sistema real.
- No hay voces, rostros, correos ni datos de personas reales. Proveedores, entidades y valores son inventados.
- Todo el código, modelos y fuentes de terceros están citados en [referencias](referencias.md).

## Uso de IA en este proyecto

Este proyecto se construyó con asistencia de agentes de código. La lista de herramientas y lo que hizo cada una está en [referencias](referencias.md) y se actualiza durante el sprint.
