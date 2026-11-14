# Verificación de integridad

La compuerta vale lo que valgan la política que recibe y el código que la ejecuta. Quien pueda editar `policy.toml`, las herramientas de un escenario o el núcleo puede apagar la defensa sin tocar a ningún agente: basta quitar un prefijo de `restricted`, subir un cupo o convertir un desclasificador en una herramienta normal. Este módulo (`quorum/integrity.py`) hace que un cambio así se note.

## Qué se calcula

Cuatro hashes SHA-256 y uno que los resume:

| Hash | Qué cubre | Qué no lo cambia |
|---|---|---|
| `policy` | Lo que la política significa: prefijos restringidos y no confiables, sumideros y sus fuentes, desclasificadores, autorizaciones, cupos, `strict_mode`, `high_water_mark` y los roles con sus herramientas y permisos | Comentarios, espacios y orden del archivo |
| `tools` | La interfaz de cada herramienta que algún rol puede llamar: nombre, tipo (normal, sumidero, desclasificador), descripción, parámetros y justificación | El orden en que se declaran |
| `kernel` | Todos los archivos del camino de confianza: `quorum/domain`, `quorum/application`, `quorum/infrastructure`, los puntos de arranque (`bootstrap.py`, `launch.py`, `__init__.py`), el servicio que convierte un token en un rol (`adapters/http_server.py`, `http_client.py`, `functions.py`) y este mismo módulo | Finales de línea, cachés |
| `scenario` | Todos los archivos `.py` y `.toml` del paquete del escenario: donde se define el pipeline (política, herramientas, caso, prompts) | Finales de línea, cachés |
| `pipeline` | El hash de los cuatro anteriores. Es el que se compara y se publica | |

## Dónde se comprueba

1. **En la revisión.** `quorum/integrity.lock.json` fija los hashes del núcleo y de los cinco escenarios. Un test (`tests/test_integrity.py`) falla si el código y el archivo no coinciden, así que el CI no pasa con una política cambiada a escondidas: el cambio tiene que venir con el archivo de huellas en el mismo PR, a la vista de quien revisa.
2. **Al arrancar.** El servicio del monitor compara antes de atender. Si la política, las herramientas o el código no son los fijados, no arranca y dice qué cambió. La imagen de Docker tampoco se construye. El operador puede además pasarle el hash que aprobó, desde fuera del repositorio, con `QUORUM_EXPECT_PIPELINE`.
3. **En la bitácora.** Antes de que actúe ningún agente, el monitor sella la huella en la bitácora, una sola vez. La bitácora está encadenada con hashes, así que cada decisión queda ligada a la política y al código que la tomó: no se puede cambiar la huella después sin romper la cadena.
4. **En el reporte.** `python -m quorum.launch report` no le cree al monitor: devuelve error si lo que el monitor declara no es lo que selló, o si lo sellado no es el pipeline aprobado (el de `QUORUM_EXPECT_PIPELINE` si el operador lo dio, y si no el del archivo de huellas de quien corre el reporte).

## Lo que no está en ningún archivo

Tres cosas cambian lo que hace la compuerta sin tocar código ni política: si bloquea o solo audita (`--audit`), qué reglas aplica y si hay un aprobador conectado. Ningún hash de archivos las ve, así que el sello las lleva aparte (`runtime`): el reporte muestra `enforce_sealed`, y una bitácora de un monitor en modo auditoría dice que no bloqueaba, aunque su pipeline sea el aprobado.

## Archivos plantados

Python importa un enlace simbólico o un módulo compilado sin mirar el código fuente que aquí se resume. Por eso, si dentro del núcleo o de un escenario aparece un enlace o un archivo compilado (`.pyc`, `.so`, `.pyd`) fuera de `__pycache__`, el cálculo falla y el monitor no arranca.

## Cómo se usa

```bash
uv run python -m quorum.integrity            # comprueba; sale con error si algo cambió
uv run python -m quorum.integrity --show     # imprime los hashes actuales
uv run python -m quorum.integrity --write    # acepta el código actual: reescribe el archivo de huellas
```

Si un cambio a la política o al núcleo es intencional, se corre `--write` y se sube `quorum/integrity.lock.json` en el mismo commit. Para arrancar el monitor con código sin fijar, a propósito: `python -m quorum.launch monitor --unpinned` (el reporte lo marca con `"pinned": false`).

Desde código:

```python
from quorum import integrity

found = integrity.seal(case.quorum, "tender", expected=hash_aprobado)   # antes de abrir sesiones
integrity.verify_log(case.quorum, "tender")     # la bitácora está íntegra y la selló este mismo pipeline
integrity.sealed(eventos)                       # la huella sellada en una bitácora exportada
```

## Qué se probó

- Nueve formas de debilitar la política (quitar un prefijo restringido, dejar que un sumidero acepte una fuente restringida, autorizar una fuente, subir o quitar un cupo, apagar la marea alta, cambiar `strict_mode`, dar a un rol más lecturas u otra herramienta) cambian el hash. Reordenar el archivo no lo cambia.
- Convertir un desclasificador en herramienta normal cambia el hash de las herramientas.
- Un byte distinto en un archivo del escenario, o un archivo nuevo, cambia el hash del escenario.
- Una bitácora cuya huella se editó deja de verificar. Una huella no se puede sellar después de la primera llamada ni dos veces.
- El sello de un monitor en modo auditoría dice que no bloquea; si después se cambia el modo, la bitácora deja de verificar.
- Un paquete compilado, un módulo `.so` o un enlace plantados junto al código se rechazan.
- Quince formas de debilitar la política en total, incluidas las de prefijos no confiables, desclasificadores y permisos de escritura.
- El monitor no arranca si el operador esperaba otro pipeline, y el reporte de un episodio real trae la huella fijada.

## Qué no hace

- **No es una firma.** Quien pueda reescribir a la vez el código, el archivo de huellas y el hash esperado no queda detenido. Para eso el hash contra el que compara un auditor tiene que vivir donde esa persona no pueda escribir (otro repositorio, un registro firmado).
- **No cubre lo que está fuera del paquete**: el intérprete, las dependencias ni la imagen base.
- **Confía en la caché de bytecode.** Un `.pyc` falsificado dentro de `__pycache__` se importaría en lugar del código. La imagen de Docker no lleva caché; en una máquina de desarrollo sí la hay.
- **No cubre el resto de adaptadores ni la interfaz web**, que no están en el camino del servicio del monitor.
- **No dice si una política es buena**, solo que es la que se aprobó.
- **Los bancos de métricas y la interfaz web no sellan la bitácora**; solo lo hace el servicio del monitor. Cualquiera puede hacerlo con `integrity.seal`.
