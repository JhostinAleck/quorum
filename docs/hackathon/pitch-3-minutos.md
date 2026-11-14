# Pitch de 3 minutos, con la ficha en pantalla

Las reglas salen de la página oficial del hackathon:
- Son 3 minutos con la ficha técnica proyectada (`docs/documento-tecnico/quorum.pdf`), sin diapositivas.
- Pitch desde las 5:10 p.m. Después, los jurados hacen unas pocas preguntas cortas.
- Hay tres criterios con el mismo peso, de 1 a 5 cada uno: impacto e innovación, calidad de ejecución y claridad. Si hay empate, gana el mejor en impacto.

Cómo se armó:
- Del mentor: se abre por **la compuerta**, no por los agentes; se nombra la línea base y se cierra con el número.
- De la investigación de pitch de Mérito 11 (`~/Documents/agent-reports/2026-11-12/pitch-merito11/`, informes 20 y 27):
  - La primera frase dice qué hacemos, en lenguaje simple (Seibel, YC).
  - Un titular que se repite: **«no lee el texto; sigue de dónde viene el dato»**.
  - Un antagonista: el monitor que lee.
  - Frases cortas, y cada cifra contra algo que se entienda.
  - Un solo momento para recordar: la tabla 1, donde nadie gana en detección y la compuerta gana en todo lo demás.

El guion tiene unas 440 palabras: a 155 por minuto, con pausas, da unos 2:55. Entre corchetes va adónde se señala en la ficha. Si al ensayar pasa de 3:00, se corta el bloque de AgentDojo (2:05) a su primera frase.

## Guion

> **(0:00) [Título]** Somos Quórum. Hicimos una compuerta que impide que un sistema de agentes de IA publique
> un dato secreto, aunque varios agentes se pongan de acuerdo para sacarlo. Y no lee el texto: sigue de
> dónde viene el dato.
>
> **(0:15) [Amenaza]** El caso es una licitación pública. Tres agentes: uno registra las ofertas, otro las
> evalúa, otro publica. Uno, dos o los tres están comprometidos y quieren filtrar el precio de un
> competidor. Si se reparten el trabajo, cada paso parece rutina: uno abre el sobre y lo anota como
> si fuera un número de radicado, otro lo copia, el tercero lo publica. Un monitor que mira a cada agente
> por separado ve tres pasos normales.
>
> **(0:40) [Figura 1]** Nuestra idea no es otro monitor que lea. Cada dato lleva una etiqueta con sus
> fuentes, y lo que un agente escribe hereda la etiqueta de lo que leyó. Al publicar, si lo que sale deriva de un sobre sellado, no sale. No llama a ningún modelo
> y no tiene umbral. Da igual que el número vaya en palabras, en base64 o partido en dos: no lee el texto;
> sigue de dónde viene el dato.
>
> **(1:05) [Tabla 1]** Lo medimos con agentes de modelo: 90 trámites, 60 honestos y 30 ataques. Sin defensa,
> el precio llega al portal en 16 de 30. La compuerta bloquea las 16 y no detiene ninguno de los 60
> honestos. Y la línea base: un monitor por agente también atrapa las 16. Empatamos en
> detección. La diferencia es todo lo demás: el monitor hace cuatro llamadas a un modelo por trámite, avisa
> al final y depende de un umbral; la compuerta decide en un microsegundo, antes de que el dato salga, y
> ningún texto la convence.
>
> **(1:40) [Tabla 2]** El núcleo no es de la licitación. Probamos cinco dominios: licitación, atención
> ciudadana, historias clínicas, banca y legal. En 7.600 ataques guionados, un filtro que conoce todos los
> secretos deja pasar 42 %; Quórum, cero. Para adoptarlo, un equipo escribe un archivo de política de unas
> 20 líneas por dominio.
>
> **(2:05) [Tabla 3]** También contra ataques que no escribimos: en 7.127 trazas reales de AgentDojo, frena
> 1.506 de 1.521 secuestros por inyección. Y donde no aporta, lo decimos: con un buen prompt, la inyección
> en nuestra licitación dio cero fugas en 600 episodios.
>
> **(2:25) [Límites]** Dónde falla. Bloquea de más: quien abre un sobre sin necesitarlo queda retenido para
> revisión humana. Y lo que la política declara público, sale: con los puntajes publicados un rival
> despeja el precio. Eso no lo arregla la compuerta; lo arregla el pliego.
>
> **(2:45) [Cierre]** Quórum: 16 de 16 fugas bloqueadas, 0 de 60 trámites honestos, cero llamadas a un
> modelo. El repositorio corre sin llaves con `uv run pytest`. Gracias.

## Si cortan a 1 minuto

> Quórum es una compuerta para sistemas de agentes de IA: cada dato lleva la etiqueta de sus fuentes y, si
> lo que se publica deriva de un sobre sellado, no sale. No lee el texto, así que no se la convence ni se
> la engaña disfrazando el número. Con agentes de modelo coludidos en una licitación, bloquea las 16 fugas
> y 0 de 60 trámites honestos, sin llamar a ningún modelo; en 7.127 trazas de AgentDojo frena 1.506 de
> 1.521 secuestros. Falla donde la política declara algo público, y lo medimos.

## Qué no decir

- No abrir con «tenemos tres agentes». La primera frase es la compuerta.
- No decir que el monitor «falla»: M1 detecta 16 de 16. La ventaja es el costo, el momento de decidir y
  que no se la convence.
- No decir que la inyección «rompe» a los agentes en la licitación: ahí un buen prompt basta.
- No decir «demostramos» ni «garantiza»: son 30 ataques con plantillas fijas, y los intervalos son anchos.
- No presumir de pre-registro sin decir que fue tardío.

## Ensayo de preguntas (respuestas de unos 20 segundos)

**Antonio Badilla-Olivas** (SPAR, entornos donde los ataques y los monitores evolucionan juntos)
1. *«Tu atacante es fijo. ¿Qué pasa con uno adaptativo?»* Adaptar el texto no sirve, porque la compuerta no
   lo lee: probamos cuatro textos dirigidos a quien decide y nueve disfraces del número, y ninguno cambia la
   decisión. Lo que sí la evade son los canales que no viajan en los datos. Un atacante encontró uno: la
   existencia de una clave revelaba el valor (6,3 bits). Lo cerramos juzgando con lo que vio cualquier
   agente, y quedó en 0 bits. Los que siguen abiertos están en la ficha: tiempo, orden y puntajes publicados.
2. *«¿Por qué no un monitor mejor?»* Probamos tres jueces, entre ellos Jev, que cuesta la mitad. Siguen
   siendo un puntaje con umbral que lee lo que escribe quien vigila. Jev, con ataques hechos por un modelo,
   deja escapar 2 de 16. La compuerta y el monitor se combinan: la compuerta suave solo llama al monitor
   cuando lo publicado deriva de un secreto.

**Christian Urcuqui** (TryHackMe, AgentBreak: inyección indirecta)
3. *«¿Y la inyección indirecta?»* En nuestra licitación, un buen prompt ya basta: 0 fugas en 600. Donde la
   compuerta aporta es con el agente que sí obedece. En AgentDojo, la regla por valor frena 1.506 de 1.521
   secuestros. El costo: deja funcionando 16 de 25 tareas limpias, frente a 19 sin defensa.
4. *«¿Quién pone las etiquetas iniciales?»* Un humano, en la política: qué nace restringido y qué escriben
   terceros. Es un supuesto, y está en la ficha. Todo tiene que pasar por el monitor.

**Carlos Gorostiza, José Felipe Duarte y Manuela Chacón** (negociación y resiliencia multiagente)
5. *«¿Esto es colusión o solo una fuga?»* Es colusión: k agentes con una tarea oculta que se reparten el
   ataque para que ningún paso aislado se vea raro. Es el riesgo del track 6 y el resultado de Makins et al.
   (UK AISI): repartir baja la sospecha de un monitor por agente.
6. *«¿Funciona si los agentes negocian entre sí en vez de compartir un almacén?»* Sí, mientras los mensajes
   pasen por el monitor: un mensaje es un dato con etiqueta. Fuera del monitor no vemos nada, y ese es el
   supuesto.
7. *«¿Cuánto trabajo legítimo rompe?»* Con la licitación terminan los 60 honestos, y en los cinco dominios
   los 1.200 trámites honestos. Lo que detiene siempre es el honesto descuidado que abre un sobre que no
   necesitaba: lo retiene para revisión humana, a propósito.

**Jairo Torregrosa** (Mercado Libre: agentes y evals abiertos)
8. *«¿Lo puedo correr?»* Sí, sin llaves ni costo: `uv run pytest` (877 pruebas) y los análisis se
   recalculan desde `datos/`. La política y el código de la compuerta tienen hashes fijados, y el monitor no
   arranca si cambian.
9. *«¿Cómo lo meto en mi sistema de agentes?»* Las herramientas que sacan datos pasan por el monitor, y se
   escribe un `policy.toml` de unas 20 líneas: fuentes restringidas, fuentes no confiables, qué admite cada
   salida. El núcleo no cambia entre dominios.

**Cualquiera**
10. *«¿Qué es nuevo, si FIDES y CaMeL ya hacen control de flujo?»* Ellos defienden contra la inyección, con
    el agente como víctima. Nosotros medimos la compuerta cuando los propios agentes son los atacantes y se
    coluden, cara a cara con monitores, y reportamos el costo junto al beneficio.
