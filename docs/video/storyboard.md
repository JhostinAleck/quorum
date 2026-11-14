# Storyboard

Formato: 1920x1080, 30 fotogramas por segundo, 1:58,5. Todo lleva subtítulos y una barra de avance.

Tres tipos de plano:

- **Generado**: video de Higgsfield (modelo Seedance 2.5, texto a video, 720p, 16:9, sin audio), usado como fondo con el texto montado encima en el montaje. Lleva en pantalla el rótulo "Plano generado con IA · Higgsfield".
- **Animación**: diagramas y cifras animados en código (`animacion/index.html`), sincronizados con las marcas de tiempo de la voz.
- **Captura**: la interfaz real de Quórum corriendo en 127.0.0.1 en modo guionado (sin modelo, sin key), con las tres ofertas sintéticas de ejemplo. Los recuadros y rótulos de color se añaden en el montaje; lo demás es la página tal cual.

## Línea de estilo común de los planos generados

Va al final de cada prompt, sin cambios, para que los tres planos se vean iguales:

```text
Minimal 3D motion-design animation, dark navy studio background, soft volumetric blue rim light, matte paper and brushed metal materials, shallow depth of field, clean composition, cinematic, slow and calm. No people, no faces, no hands, no text, no letters, no numbers, no logos, no flags, no emblems, no watermark.
```

Los prompts van en inglés: es lo que pide la skill oficial de Higgsfield según la investigación ("Write all image/video prompts in English. Only narration uses the selected language"). Las publicaciones recomiendan además una imagen de estilo única adjunta a cada clip; aquí no se usó porque con solo tres planos y la misma línea de estilo la consistencia salió bien a la primera, y ahorraba un paso.

## Planos

| Plano | Tiempo | Escena | Tipo | Qué se ve | Movimiento |
|---|---|---|---|---|---|
| P1 | 0:00,0 a 0:10,4 | 1 | Generado g1 (8 s, reproducido al 77 % de velocidad) | Un sobre sellado avanza por un riel azul hacia una compuerta; las barras se cierran y se encienden en rojo | Acercamiento lento de la cámara (viene del plano) |
| P2 | 0:10,4 a 0:16,1 | 2 | Generado g2 (5 s) | Un sobre sellado pasa por tres mesas iguales unidas por un riel | Travelling lateral de izquierda a derecha |
| P3 | 0:16,1 a 0:23,3 | 2 | Animación | Radicador, Evaluador, Publicador y Portal; la ficha "valor sellado" salta de uno a otro | Entradas con desplazamiento corto; la ficha salta en arco |
| P4 | 0:23,3 a 0:35,5 | 3 | Animación | La etiqueta `{sealed.bid-2}` se hereda; la compuerta compara con la política y se cierra | Las barras de la compuerta se juntan y pasan a rojo |
| P5 | 0:35,5 a 0:39,0 | 4 | Captura | Ofertas cargadas y configuración | Fija |
| P6 | 0:39,0 a 0:43,1 | 4 | Captura | Resultado del trámite honesto; recuadros verdes en "Compuerta: permite" y en el portal | Desplazamiento vertical de la página hasta el resultado |
| P7 | 0:43,1 a 0:45,5 | 5 | Captura | Radicador desviado: `open_bid` y contexto restringido resaltados | Fija |
| P8 | 0:45,5 a 0:48,3 | 5 | Captura | Evaluador y Publicador con la misma etiqueta resaltada | Desplazamiento vertical hacia arriba |
| P9 | 0:48,3 a 0:53,4 | 5 | Captura | Resultado: "Compuerta: BLOQUEA", "(no se publicó nada)", sello BLOQUEADO | Desplazamiento vertical hasta el resultado; el sello entra con escala |
| P10 | 0:53,4 a 1:09,5 | 6 | Animación | 60 y 30 puntos; 16 en rojo; luego bloqueados; contadores | Los puntos entran escalonados; el contador sube |
| P11 | 1:09,5 a 1:21,4 | 7 | Animación | Tabla monitor por agente frente a compuerta | Las celdas entran cuando la voz las nombra |
| P12 | 1:21,4 a 1:36,2 | 8 | Animación | Cinco dominios con barras; AgentDojo con contador | Las barras crecen; el contador sube hasta 1506 |
| P13 | 1:36,2 a 1:51,8 | 9 | Animación | Tres tarjetas de costos y límites | Cada tarjeta entra con su frase |
| P14 | 1:51,8 a 1:58,5 | 10 | Generado g3 (6 s) con texto encima | Compuerta cerrada en rojo y el sobre delante; encima la dirección del repositorio, que se escribe letra a letra | Alejamiento muy lento (viene del plano) |

## Prompts exactos de Higgsfield

Cada uno termina con la línea de estilo común.

**g1, apertura (8 s)**

```text
A single sealed white paper envelope with a red wax seal glides slowly along a thin glowing blue rail toward a narrow metal gate. As the envelope arrives, two slim vertical gate bars slide shut in front of it and glow soft red; the envelope stops gently before the gate. Camera: slow push-in from a three-quarter angle.
```

**g2, el caso (5 s)**

```text
Three identical small matte-white desks stand in a row, connected by a thin glowing blue rail. A sealed white paper envelope with a red wax seal slides calmly along the rail from the first desk to the second and then to the third; each handoff looks smooth and ordinary. Camera: slow lateral tracking shot from left to right.
```

**g3, cierre (6 s)**

```text
A closed metal gate with slim vertical bars glowing soft red. A sealed white paper envelope with a red wax seal rests in front of the gate on a thin glowing blue rail; beyond the gate the rail is empty and calm. Camera: very slow pull-back, subtle floating dust particles.
```

Los tres planos no muestran personas, logos, banderas ni entidades reales. El sello de lacre de g3 trae un relieve abstracto que puso el modelo; no es el emblema de nadie y queda oscurecido bajo el texto.
