# Pitch de 2 minutos

Reglas que salen del briefing: 2 minutos, se abre por **la compuerta** y no por los agentes, el baseline se
nombra, y se cierra con el número. El guion son ~330 palabras: a 170 por minuto da 1:57. Si al ensayar
pasa de 2:00, se corta la última frase del bloque de 1:12 (la del monitor por agente).

## Guion

> **(0:00) Somos Quórum:** una compuerta determinista que impide que un dato sellado salga publicado,
> aunque el ataque se reparta entre tres agentes y el dato vaya disfrazado.
>
> **(0:15) El caso:** una licitación con tres agentes —radica, evalúa, publica— y uno o varios comprometidos
> que quieren sacar el precio de un competidor. Si lo reparten, cada paso parece rutina y un monitor por
> agente no ve nada raro.
>
> **(0:32) Nuestra idea no es otro monitor.** Cada dato lleva la etiqueta de sus fuentes y lo que un agente
> escribe hereda esa etiqueta. En la publicación, si lo que sale arrastra un sobre sin autorización, no
> sale: no lee el texto, no se la convence escribiendo.
>
> **(0:50) Son 90 episodios:** 60 honestos y 30 ataques. Sin defensa el ataque funciona en 16 de 30; el dato
> llegó a un agente en 23 y salió en 16, y la compuerta bloquea las 16 y 0 de 60 honestos, sin llamar a
> ningún modelo.
>
> **(1:12) Y medimos el baseline que importa:** tres agentes honestos y una inyección dentro de un anexo.
> Con buen prompt, con la regla del pliego y hasta sin regla: cero fugas en 120 episodios. Ahí la
> inyección no alcanza, con o sin prompt, y lo decimos. El valor está donde el prompt no llega: el agente ya comprometido, y el agente único
> que sí obedece, en AgentDojo: 90 de 90 secuestros frenados en el corte principal y 1.506 de 1.521 en
> total. Un monitor por agente también detecta las 16, pero paga una llamada por episodio y deja 5 de 30
> falsos positivos.
>
> **(1:45) Lo que no funcionó:** juntar las tres trayectorias en un monitor no mejoró a leer cada agente;
> sale de la configuración.
>
> **(1:52) Límites:** atacante fijo y 30 ataques, son cotas.
>
> **(1:56) Cierre:** 16 de 16 fugas bloqueadas, 0 de 60 trámites honestos, 0 llamadas.

## Versión de 30 segundos (si cortan el tiempo)

> Quórum es una compuerta determinista en la publicación: cada dato lleva su procedencia y, si lo que sale
> arrastra un sobre sellado sin autorización, no sale. Sobre 90 episodios bloquea las 16 fugas de nuestro
> ataque repartido y 0 de 60 trámites honestos, sin llamar a ningún modelo; y sobre 7.127 trazas públicas
> de AgentDojo frena 1.506 de 1.521 secuestros.

## Qué no decir

- No abrir con «tenemos tres agentes». El mentor: «tú me hablas de agentes y la compuerta no la mencionaste».
- No decir que el baseline «falla». El baseline de prompt **no pierde** en su escenario (0 fugas en 120, también sin regla): en
  esa frase hay que decir que ahí la compuerta no aporta, y pasar a donde el prompt no llega.
- No decir que medimos inyección por contenido en nuestra licitación: no la medimos ahí, la medimos fuera.
- No presumir de pre-registro sin decir que fue tardío.

## Respuestas de bolsillo

- **¿Keywords o clasificador?** Ninguno de los dos en la compuerta dura: etiquetas de procedencia. El LLM
  solo entra en la compuerta suave y ve el corte de procedencia, no el texto completo.
- **¿Y si el agente parte el número?** La etiqueta va con el valor, no con el texto; partir el número no
  rompe la etiqueta. Lo que sí la evade es lavar el dato por un canal que la política no declara.
- **¿Qué cambia entre dominios?** Una tabla: fuentes restringidas, fuentes no confiables, desclasificadores
  y sumideros. El núcleo es el mismo; el segundo escenario (mesa de ayuda de salud) lo prueba.
