"""Spanish texts for the generic tools, shared by the Spanish-language scenarios."""
from ..core import read as _read
from ..core import write as _write

read = _read.localized("Lee un dato del espacio compartido.",
                       {"key": "Clave del dato, por ejemplo 'registry.notes'."})
write = _write.localized("Guarda un dato en el espacio compartido para que otros agentes lo lean.",
                         {"key": "Clave bajo la que se guarda.", "data": "Contenido a guardar."})
