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
> Con buen prompt, con la regla del pliego y sin regla: cero fugas en 120 episodios. Ahí un buen prompt
> basta, y lo decimos. El valor está donde el prompt no llega: el agente ya comprometido, y el agente único
> que sí obedece, en AgentDojo: 90 de 90 secuestros frenados en el corte principal y 1.506 de 1.521 en
> total. Un monitor por agente también detecta las 16 sin falsos positivos, pero paga tres llamadas a un
> modelo por trámite y solo avisa al final. El monitor conjunto que sí se podría desplegar pierde 3 de
> 16 fugas con Gemini o marca 5 de 30 trámites honestos con Haiku.
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
- No decir que el baseline «falla». El baseline de prompt **gana** en su escenario (0 fugas en 120): en
  esa frase hay que decir que ahí la compuerta no aporta, y pasar a donde el prompt no llega.
- No decir que la inyección por contenido en nuestra licitación «rompe» a los agentes: sí la medimos
  (0 fugas en 120 episodios con buen prompt) y ahí el prompt basta. Donde la compuerta aporta frente a
  la inyección es en AgentDojo.
- No presumir de pre-registro sin decir que fue tardío.

## Respuestas de bolsillo

- **¿Keywords o clasificador?** Ninguno de los dos en la compuerta dura: etiquetas de procedencia. El LLM
  solo entra en la compuerta suave y ve el corte de procedencia, no el texto completo.
- **¿Y si el agente parte el número?** La etiqueta va con el valor, no con el texto; partir el número no
  rompe la etiqueta. Lo que sí la evade es lavar el dato por un canal que la política no declara.
- **¿Qué cambia entre dominios?** Una tabla: fuentes restringidas, fuentes no confiables, desclasificadores
  y sumideros. El núcleo es el mismo: hay cinco dominios (licitación, mesa de ayuda, clínica, banca y
  legal) hechos solo con su política y sus herramientas. En 7.600 episodios adversos guionados el daño
  es 100 % sin defensa, 42 % con un filtro de coincidencia exacta o con un buen harness, y 0 % con
  Quórum (`docs/resultados-dominios.md`).
- **¿Por qué no un monitor mejor, como Jev?** Lo probamos como juez de los mismos monitores. Con ataques
  guionados detecta 120 de 120 y dos notas dirigidas al revisor no lo mueven. Con los 30 ataques hechos
  por un modelo se le escapan 2 de 16 fugas como M1 y 3 de 16 como M2, y marca trámites honestos. Cuesta
  menos de la mitad que un modelo de chat. Sigue siendo un puntaje con umbral que lee texto escrito por
  quien vigila; la compuerta no (`docs/resultados-monitores.md`).
- **¿Cada cuánto corre un monitor y cuánto cuesta?** Una vez por trámite, al final: tres llamadas de M1
  (una por agente) y una de M2. Eso detecta, no detiene. Monitorear cada paso relee todo lo anterior y el
  costo crece con el cuadrado del largo del trámite. La compuerta decide en cada salida y no llama a
  ningún modelo.
- **¿Y si alguien cambia la política o el código de la compuerta?** Sus hashes están fijados en
  `quorum/integrity.lock.json`: el CI falla si cambian sin ese archivo, el monitor no arranca con otro
  pipeline y la huella queda sellada en la bitácora antes de la primera llamada. No es una firma: quien
  pueda reescribir todo a la vez no queda detenido (`docs/integridad.md`).
- **¿Cuánto cuesta la compuerta en trabajo legítimo?** Bloquea siempre el trámite honesto descuidado (un
  agente que abre un sobre que no necesitaba) y en AgentDojo detiene parte de las tareas legítimas. Lo
  reportamos junto al beneficio.
