# Pitch de 2 minutos

Reglas que salen del briefing: 2 minutos, se abre por **la compuerta** y no por los agentes, el baseline se
nombra, y se cierra con el número. El guion son ~325 palabras: a 165–175 por minuto da 1:55.
Si al ensayar pasa de 2:00, se corta la segunda frase del bloque de 0:15 (la del monitor por agente).

## Guion

> **(0:00) Somos Quórum:** una compuerta determinista que impide que un dato sellado salga publicado,
> aunque el ataque se reparta entre tres agentes y el dato vaya disfrazado.
>
> **(0:15) El caso** es una licitación con tres agentes —radica, evalúa, publica—. Uno o varios están
> comprometidos y quieren sacar el precio de un competidor. Si lo reparten, cada paso parece rutina y un
> monitor por agente no ve nada raro.
>
> **(0:35) Nuestra idea no es otro monitor.** Cada dato lleva la etiqueta de sus fuentes y lo que un agente
> escribe hereda esa etiqueta. En la publicación, si lo que sale arrastra un sobre sin autorización, no
> sale: no lee el texto, no se la convence escribiendo.
>
> **(0:55) Son 90 episodios:** 60 honestos y 30 ataques con uno, dos y tres agentes. Sin defensa, el ataque
> funciona en 16 de 30. Llegó a un agente en 23 de los 30 y salió en 16: no impide leerlo, impide
> publicarlo. Bloquea las 16 fugas y 0 de 60 honestos, sin llamar a ningún modelo. El
> baseline, un LLM por agente con buen prompt, también detecta las 16, pero deja 5 de 30 falsos positivos y
> paga una llamada por episodio. La compuerta aporta cero falsos positivos, cero llamadas y una garantía
> que no depende del texto.
>
> **(1:35) Y no solo con nuestros ataques:** 7.127 trazas públicas de AgentDojo, con la política congelada
> antes. Frena 90 de 90 secuestros en el corte principal y 1.506 de 1.521, rompiendo 3 de 19 tareas limpias.
>
> **(1:45) Lo que no funcionó:** juntar las tres trayectorias en un monitor no mejoró a leer cada agente.
> Lo reportamos y sale de la configuración.
>
> **(1:52) Límites:** atacante fijo y 30 ataques, son cotas; el vector por contenido lo medimos fuera, no
> aquí.
>
> **(1:57) Cierre:** 16 de 16 fugas bloqueadas, 0 de 60 trámites honestos, 0 llamadas.

## Versión de 30 segundos (si cortan el tiempo)

> Quórum es una compuerta determinista en la publicación: cada dato lleva su procedencia y, si lo que sale
> arrastra un sobre sellado sin autorización, no sale. Sobre 90 episodios bloquea las 16 fugas de nuestro
> ataque repartido y 0 de 60 trámites honestos, sin llamar a ningún modelo; y sobre 7.127 trazas públicas
> de AgentDojo frena 1.506 de 1.521 secuestros.

## Qué no decir

- No abrir con «tenemos tres agentes». El mentor: «tú me hablas de agentes y la compuerta no la mencionaste».
- No decir que el baseline «falla»: detecta las 16; lo que no da es 0 falsos positivos ni 0 llamadas.
- No decir que medimos inyección por contenido en nuestra licitación: no la medimos ahí, la medimos fuera.
- No presumir de pre-registro sin decir que fue tardío.

## Respuestas de bolsillo

- **¿Keywords o clasificador?** Ninguno de los dos en la compuerta dura: etiquetas de procedencia. El LLM
  solo entra en la compuerta suave y ve el corte de procedencia, no el texto completo.
- **¿Y si el agente parte el número?** La etiqueta va con el valor, no con el texto; partir el número no
  rompe la etiqueta. Lo que sí la evade es lavar el dato por un canal que la política no declara.
- **¿Qué cambia entre dominios?** Una tabla: fuentes restringidas, fuentes no confiables, desclasificadores
  y sumideros. El núcleo es el mismo; el segundo escenario (mesa de ayuda de salud) lo prueba.
