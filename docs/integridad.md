# Verificación de integridad

La compuerta vale lo que valgan la política que recibe y el código que la ejecuta. Quien pueda editar `policy.toml`, las herramientas de un escenario o el núcleo puede apagar la defensa sin tocar a ningún agente: basta quitar un prefijo de `restricted`, subir un cupo o convertir un desclasificador en una herramienta normal. Este módulo (`quorum/integrity.py`) hace que un cambio así se note.

## Qué se calcula

Cuatro hashes SHA-256 y uno que los resume:

| Hash | Qué cubre | Qué no lo cambia |
|---|---|---|
| `policy` | Lo que la política significa: prefijos restringidos y no confiables, sumideros y sus fuentes, desclasificadores, autorizaciones, cupos, `strict_mode`, `high_water_mark` y los roles con sus herramientas y permisos | Comentarios, espacios y orden del archivo |
| `tools` | La interfaz de cada herramienta que algún rol puede llamar: nombre, tipo (normal, sumidero, desclasificador), descripción, parámetros y justificación | El orden en que se declaran |
| `kernel` | Todos los archivos de `quorum/domain`, `quorum/application`, `quorum/infrastructure` y `quorum/bootstrap.py` | Finales de línea, cachés |
| `scenario` | Todos los archivos `.py` y `.toml` del paquete del escenario: donde se define el pipeline (política, herramientas, caso, prompts) | Finales de línea, cachés |
| `pipeline` | El hash de los cuatro anteriores. Es el que se compara y se publica | |

## Dónde se comprueba

1. **En la revisión.** `quorum/integrity.lock.json` fija los hashes del núcleo y de los cinco escenarios. Un test (`tests/test_integrity.py`) falla si el código y el archivo no coinciden, así que el CI no pasa con una política cambiada a escondidas: el cambio tiene que venir con el archivo de huellas en el mismo PR, a la vista de quien revisa.
2. **Al arrancar.** El servicio del monitor compara antes de atender. Si la política, las herramientas o el código no son los fijados, no arranca y dice qué cambió. La imagen de Docker tampoco se construye. El operador puede además pasarle el hash que aprobó, desde fuera del repositorio, con `QUORUM_EXPECT_PIPELINE`.
3. **En la bitácora.** Antes de que actúe ningún agente, el monitor sella la huella en la bitácora. La bitácora está encadenada con hashes, así que cada decisión queda ligada a la política y al código que la tomó: no se puede cambiar la huella después sin romper la cadena. El reporte (`python -m quorum.launch report`) muestra la huella y devuelve error si lo que el monitor declara no es lo que selló.

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
- Una bitácora cuya huella se editó deja de verificar. Una huella no se puede sellar después de la primera llamada.
- El monitor no arranca si el operador esperaba otro pipeline, y el reporte de un episodio real trae la huella fijada.

## Qué no hace

- **No es una firma.** Quien pueda reescribir a la vez el código, el archivo de huellas y el hash esperado no queda detenido. Para eso el hash contra el que compara un auditor tiene que vivir donde esa persona no pueda escribir (otro repositorio, un registro firmado).
- **No cubre lo que está fuera del paquete**: el intérprete, las dependencias ni la imagen base.
- **No dice si una política es buena**, solo que es la que se aprobó.
- **Los bancos de métricas y la interfaz web no sellan la bitácora**; solo lo hace el servicio del monitor. Cualquiera puede hacerlo con `integrity.seal`.
