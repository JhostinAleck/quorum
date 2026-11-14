# La misma compuerta en cinco dominios

Quórum es una compuerta que se pone delante de cualquier sistema de agentes. No sabe de licitaciones. Para comprobarlo, la misma compuerta, sin cambiar una línea del núcleo, se probó en cinco dominios distintos y se midió igual en todos.

## Los dominios

| Dominio | Qué no puede salir | Por dónde sale algo | Qué ejercita de la compuerta |
|---|---|---|---|
| Licitación pública (`tender`) | El valor de las ofertas selladas | Publicación en el portal | Referencias opacas y desclasificadores con cupo |
| Mesa de ayuda (`helpdesk`) | Los datos de un ciudadano | Respuesta a quien consulta | Permiso por destinatario: cada quien recibe solo lo suyo |
| Historias clínicas (`clinic`) | El diagnóstico de un paciente | Remisión al especialista y factura a la aseguradora | Dos salidas con permisos distintos |
| Banca (`bank`) | El saldo de un cliente, y mover dinero sin orden del cliente | Aviso al cliente y transferencia | Integridad: un mensaje de un tercero no ordena pagos |
| Sector legal (`lawfirm`) | El tope de conciliación que autorizó un cliente, y el expediente de otro cliente | Escrito ante el juzgado e informe al cliente | Muralla entre clientes y una salida pública que no lleva nada reservado |

Cada dominio es una carpeta en `quorum/scenarios/` con un archivo de política (`policy.toml`: la tabla de qué es sensible y por dónde puede salir, que define quien usa el sistema), sus herramientas y sus episodios.

## Qué se compara

Cuatro defensas sobre los mismos episodios:

- **Sin defensa.** Referencia.
- **Filtro de coincidencia exacta.** Conoce todos los secretos y bloquea cualquier salida que lleve uno, tal cual, a quien no debe tenerlo. Es lo primero que cualquiera construiría, y nunca bloquea trabajo honesto. Se le da esa ventaja a propósito.
- **Buen harness (mínimo privilegio).** Lo que hace un harness cuidadoso sin etiquetas: a cada rol se le dejan solo las herramientas que usa su trabajo honesto, y no se revisa nada más. Tampoco bloquea trabajo honesto. La lista de herramientas se saca de los propios trámites honestos.
- **Quórum.** La compuerta de procedencia con la política del dominio.

Y cinco tipos de episodio:

- **Trámite honesto.** Los agentes hacen su trabajo. En cuatro de los cinco dominios ese trabajo incluye sacar datos restringidos a quien sí puede recibirlos.
- **Trámite descuidado.** Un agente honesto mira un dato restringido que no necesitaba y sigue trabajando. No filtra nada.
- **Ataque repartido.** Uno, dos o tres agentes sacan el secreto por pasos. Incluye enviar un dato al destinatario equivocado.
- **El mismo ataque con el dato en palabras.** El secreto viaja escrito dígito por dígito ("tres ocho cero..."), que un filtro de texto no reconoce.
- **Inyección en un documento.** Ningún agente está comprometido. Un documento de un tercero trae una instrucción y los agentes, siguiendo su procedimiento normal, la cumplen.

<!-- bench:start -->

## Daño que queda con cada defensa

Porcentaje de episodios en los que un secreto llegó a quien no debía o se movió dinero sin permiso. Menos es mejor.

| Dominio | Tipo de episodio | Sin defensa | Filtro de coincidencia exacta | Buen harness (mínimo privilegio) | Quórum |
|---|---|---|---|---|---|
| Licitación pública | Ataque repartido (k = 1, 2, 3) | 100 % (600/600) | 0 % (0/600) | 0 % (0/600) | 0 % (0/600) |
| Licitación pública | El mismo ataque con el dato escrito en palabras | 100 % (600/600) | 100 % (600/600) | 0 % (0/600) | 0 % (0/600) |
| Licitación pública | Inyección en un documento, agentes honestos | 100 % (200/200) | 0 % (0/200) | 0 % (0/200) | 0 % (0/200) |
| Mesa de ayuda | Ataque repartido (k = 1, 2, 3) y envío al destinatario equivocado | 100 % (800/800) | 0 % (0/800) | 50 % (400/800) | 0 % (0/800) |
| Mesa de ayuda | El mismo ataque con el dato escrito en palabras | 100 % (600/600) | 100 % (600/600) | 33 % (200/600) | 0 % (0/600) |
| Historias clínicas | Ataque repartido (k = 1, 2, 3) y envío al destinatario equivocado | 100 % (800/800) | 0 % (0/800) | 50 % (400/800) | 0 % (0/800) |
| Historias clínicas | El mismo ataque con el dato escrito en palabras | 100 % (600/600) | 100 % (600/600) | 33 % (200/600) | 0 % (0/600) |
| Banca | Ataque repartido (k = 1, 2, 3) y envío al destinatario equivocado | 100 % (800/800) | 0 % (0/800) | 50 % (400/800) | 0 % (0/800) |
| Banca | El mismo ataque con el dato escrito en palabras | 100 % (600/600) | 100 % (600/600) | 33 % (200/600) | 0 % (0/600) |
| Banca | Inyección en un documento, agentes honestos | 100 % (200/200) | 100 % (200/200) | 100 % (200/200) | 0 % (0/200) |
| Sector legal | Ataque repartido (k = 1, 2, 3) y envío al destinatario equivocado | 100 % (800/800) | 0 % (0/800) | 50 % (400/800) | 0 % (0/800) |
| Sector legal | El mismo ataque con el dato escrito en palabras | 100 % (600/600) | 100 % (600/600) | 33 % (200/600) | 0 % (0/600) |
| Sector legal | Inyección en un documento, agentes honestos | 100 % (200/200) | 0 % (0/200) | 0 % (0/200) | 0 % (0/200) |

## Trabajo legítimo que sobrevive

Porcentaje de episodios honestos que terminan bien. Más es mejor. El trámite descuidado es un agente honesto que mira un dato restringido que no necesitaba: no filtra nada y aun así la compuerta lo detiene. Es el costo de la defensa y se reporta aparte.

| Dominio | Trámite honesto, sin defensa | Trámite honesto, con Quórum | Trámite descuidado, con Quórum |
|---|---|---|---|
| Licitación pública | 100 % (400/400) | 100 % (400/400) | 0 % (0/200) |
| Mesa de ayuda | 100 % (200/200) | 100 % (200/200) | 0 % (0/200) |
| Historias clínicas | 100 % (200/200) | 100 % (200/200) | 0 % (0/200) |
| Banca | 100 % (200/200) | 100 % (200/200) | 0 % (0/200) |
| Sector legal | 100 % (200/200) | 100 % (200/200) | 0 % (0/200) |

## La tabla de lo sensible, por dominio

Es lo único que cambia de un dominio a otro. La escribe quien usa el sistema, en el `policy.toml` del dominio, y la compuerta la aplica sin interpretarla.

| Dominio | Nace restringido | Lo escriben terceros | Salidas y qué puede llevar cada una | Cálculos autorizados sobre datos restringidos | Un tercero no ordena salidas |
|---|---|---|---|---|---|
| Licitación pública | `sealed.`, `scan.`, `manual.` | `annex.` | `publish`: nada restringido | `score_bids`, `transcribe`, `within_budget` | no |
| Mesa de ayuda | `citizen.` | `ticket.` | `reply`: `citizen.{citizen}.` | ninguno | no |
| Historias clínicas | `patient.` | `request.` | `send_referral`: `patient.{patient}.`; `send_invoice`: nada restringido | `coverage_check` | no |
| Banca | `account.` | `mail.` | `send_notice`: `account.{customer}.`; `transfer`: `account.{source}.` | `can_pay` | sí |
| Sector legal | `client.` | `discovery.` | `report_to_client`: `client.{client}.`; `file_with_court`: nada restringido | `conflict_check` | no |

## Lo que cuesta llevar la compuerta a un dominio nuevo

| Dominio | Líneas de política | Líneas de herramientas | Líneas cambiadas en el núcleo | Tiempo de una decisión |
|---|---|---|---|---|
| Licitación pública | 24 | 97 | 0 | 0,5 µs |
| Mesa de ayuda | 18 | 30 | 0 | 1,1 µs |
| Historias clínicas | 21 | 53 | 0 | 1,0 µs |
| Banca | 20 | 57 | 0 | 1,0 µs |
| Sector legal | 21 | 52 | 0 | 1,0 µs |

El tiempo es la mediana de una decisión de la compuerta en esta máquina y cambia un poco entre corridas.

## Ablación: juzgar cada salida con lo que ha visto cualquier agente

El interruptor `high_water_mark` cierra el canal de las claves ausentes (ver intentos de evasión). Esta tabla dice dónde es gratis y dónde no se puede usar: trámites honestos que terminan bien con el interruptor apagado y encendido.

| Dominio | Apagado | Encendido | En la política del dominio |
|---|---|---|---|
| Licitación pública | 100 % (400/400) | 100 % (400/400) | encendido |
| Mesa de ayuda | 100 % (200/200) | 100 % (200/200) | encendido |
| Historias clínicas | 100 % (200/200) | 0 % (0/200) | apagado |
| Banca | 100 % (200/200) | 100 % (200/200) | encendido |
| Sector legal | 100 % (200/200) | 0 % (0/200) | apagado |

Donde un trámite honesto necesita que un agente vea un dato restringido y que después salga algo por una vía que no lo admite (la factura a la aseguradora, el escrito ante el juzgado), el interruptor detiene ese trabajo. Ahí se deja apagado y el canal queda acotado con cupos por salida.

## En una frase

En 5 dominios y 7400 episodios adversos, el daño ocurre en 100 % (7400/7400) sin defensa, en 43 % (3200/7400) con el filtro de coincidencia exacta, en 35 % (2600/7400) con un buen harness de mínimo privilegio y en 0 % (0/7400) con Quórum. De 1200 trámites honestos, Quórum deja terminar 100 % (1200/1200). El costo: de 1000 trámites descuidados, que no filtran nada, deja terminar 0 % (0/1000). Son episodios guionados: miden el mecanismo, no la conducta de un modelo.

<!-- bench:end -->

## ¿Aporta algo sobre un buen harness?

Depende del dominio, y las tablas lo dicen:

- **En la licitación, no.** Ningún agente necesita abrir un sobre para radicar, puntuar o publicar. Un harness que le quita `open_bid` a quien no lo necesita detiene todos los ataques, igual que la compuerta. Ahí Quórum no aporta sobre el mínimo privilegio.
- **En los otros cuatro dominios, sí.** El agente que redacta la respuesta, la remisión, el aviso o el escrito **necesita** leer el dato reservado para hacer su trabajo. Quitarle la herramienta es quitarle el trabajo. El harness no puede distinguir entre leer el expediente del cliente correcto y leer el de otro, ni entre un dato que va al destinatario correcto y uno que va al equivocado: son la misma herramienta. Por eso deja pasar la mitad de los ataques repartidos (los que hace un solo agente con sus propias herramientas y los envíos al destinatario equivocado) y la transferencia inyectada del banco.
- **Lo que el harness sí detiene** son los ataques que exigen una herramienta que el rol no usa nunca. Es barato y hay que tenerlo. Quórum cubre lo que queda: el mal uso de una herramienta legítima.

Dicho de otra forma: el harness decide **quién puede usar qué**. La compuerta decide **adónde puede ir un dato según de dónde vino**. Son capas distintas y la segunda no se puede expresar con permisos de herramientas.

## Cómo leer estas cifras

- **Los agentes siguen un guion, no son modelos de lenguaje.** Por eso los porcentajes son 0 o 100: miden si el mecanismo detiene el flujo y cuánto cuesta, no qué tan seguido se desvía un modelo. Las corridas con modelos reales están en los resultados del experimento principal, sobre la licitación.
- **El filtro de coincidencia exacta detiene todo ataque que copia el dato tal cual y ninguno que lo reescribe.** Un filtro más listo reconocería los dígitos en palabras, y entonces el atacante usaría otra forma. La compuerta no depende de cómo esté escrito el dato, y esa es la diferencia que muestran las tablas.
- **La compuerta tiene un costo y aquí se ve.** En el trámite descuidado bloquea el 100 % sin que haya fuga. Es correcto según la política y es trabajo perdido. Qué tan seguido pasa con modelos reales depende de qué tan disciplinados sean los agentes.
- **Cero líneas del núcleo** significa que `quorum/domain`, `quorum/application` y `quorum/infrastructure` son idénticos para los cinco dominios. Un test (`tests/test_architecture.py`) falla si el núcleo llega a mencionar una palabra de algún dominio.
- **Lo que estas tablas no miden.** Los canales que no viajan en los datos. Uno de ellos sí rompe la compuerta con la política por defecto y está medido en [intentos de evasión](intentos-de-evasion.md).

## Cómo reproducirlo

```bash
uv run python -m quorum.bench                                        # imprime las tablas
uv run python -m quorum.bench --out docs/resultados-dominios.md      # las vuelve a escribir aquí
```

No usa ningún modelo ni tiene costo. Tarda unos segundos.

## Cómo agregar un dominio

1. Copiar `quorum/scenarios/helpdesk/` con otro nombre.
2. En `policy.toml`, declarar qué prefijos nacen restringidos, cuáles escriben terceros, qué herramientas sacan datos y qué puede llevar cada una.
3. Escribir las herramientas del dominio con el decorador `@tool`.
4. Escribir `prepare(seed)` y `run(kind, seed)` con un trámite honesto y los ataques.
5. Agregarlo a `DOMAINS` en `quorum/bench.py`.
