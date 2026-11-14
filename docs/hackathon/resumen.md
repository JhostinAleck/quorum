# Resumen para el formulario de entrega

Quórum es una compuerta determinista que se pone delante de cualquier pipeline de agentes. No le pregunta
a un modelo si algo es peligroso: sigue de dónde viene cada dato. Cada lectura deja una etiqueta (secreto,
no confiable) que se propaga a lo que el agente escribe, y una política escrita por quien opera el sistema
dice qué puede salir por cada sumidero. Lo que la viola, la compuerta lo detiene.

En una licitación pública sintética con tres agentes, cuando uno, dos o los
tres se coluden para filtrar el valor de una oferta sellada, sin defensa se filtró en 16 de 30 ataques; la
compuerta bloqueó las 16 fugas y ninguno de los 60 episodios honestos. Para no evaluarnos solo con
ataques propios, reprodujimos 7127 trazas de AgentDojo (banca), un benchmark externo de inyección
de prompt, con la política congelada antes de verlas: en el corte principal los ataques que llegan a una
acción crítica bajan de 90 de 144 a 0, y 16 de 25 tareas limpias siguen funcionando, frente a 1 de 144 y
9 de 25 del detector DeBERTa.

Límites: la compuerta es correcta por construcción dentro de su política; su valor está en no depender de
un modelo. Su costo depende del agente: si un agente honesto abre ofertas por una inyección, como
gpt-4o-mini, frena publicaciones correctas (50 de 120). Y con los puntajes publicados, un oferente rival
deduce el monto sellado con un error de 0,04 %.
