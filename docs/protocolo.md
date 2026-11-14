# Protocolo del monitor por red

El monitor puede correr como un servicio aparte, y cada agente en su propio contenedor. Los agentes ya no comparten proceso con el almacén ni con la bitácora: solo pueden hablar con el monitor por este protocolo. Es un adaptador más (`quorum/adapters/`); el dominio y la aplicación no cambian.

Versión 1. JSON sobre HTTP, UTF-8. Solo biblioteca estándar en el servidor y en el cliente.

## Identidad

Cada petición lleva `Authorization: Bearer <token>`.

- Un **token de agente** identifica a un agente (`principal`). Su rol es el que la política le asigna a ese nombre. El agente no elige su identidad ni su rol: salen del token.
- Un **token de administración** es del operador o del arnés del experimento. Sirve para leer el estado, no para llamar herramientas.

Los tokens se comparan en tiempo constante. El servidor nunca los escribe en la bitácora ni en los errores.

## Rutas

| Método y ruta | Quién | Respuesta |
|---|---|---|
| `GET /health` | cualquiera, sin token | `{"ok": true}` |
| `GET /v1/tools` | agente | `{"ok": true, "principal": "...", "role": "...", "tools": [{"name", "description", "parameters"}]}` |
| `POST /v1/call` | agente | ver abajo |
| `GET /v1/admin/state` | administración | ver abajo |

### `POST /v1/call`

Cuerpo: `{"tool": "open_bid", "arguments": {"ref": "bid-2"}}`. `arguments` es opcional y por defecto es `{}`.

Toda petición bien formada y autenticada responde 200 con una de estas tres formas:

```json
{"ok": true, "result": 487311902, "text": "487311902"}
{"ok": true, "blocked": {"tool": "publish", "policy": "P1", "reason": "..."}, "text": "BLOCKED by policy P1: ..."}
{"ok": false, "error": {"type": "PermissionDenied", "message": "..."}, "text": "ERROR: ..."}
```

- `result` es el valor que devolvió la herramienta, tal cual en JSON.
- `text` es lo que debe leer un modelo de lenguaje. Es exactamente lo que devuelve `quorum.adapters.functions.execute`.
- `error.type` es el nombre de la clase de error del dominio: `PermissionDenied`, `QuotaExceeded`, `InvalidArguments`, `UnknownTool`, `ToolError`. Cualquier otro fallo inesperado se informa como `QuorumError`.

### `GET /v1/admin/state`

```json
{
  "ok": true,
  "trajectories": {"registrar": [{"tool": "...", "args": {}, "result": "..."}]},
  "emissions": [{"sink": "publish", "principal": "publisher", "arguments": {}}],
  "blocks": [],
  "audit_log": [],
  "audit_log_valid": true,
  "extra": {}
}
```

`extra` lo llena quien arranca el servidor (por ejemplo, la calificación del episodio: fuga, utilidad, bloqueo).

## Errores del protocolo

Con cuerpo `{"ok": false, "error": {"type": "...", "message": "..."}}`:

| Código | `type` | Cuándo |
|---|---|---|
| 400 | `BadRequest` | JSON inválido, cuerpo que no es un objeto, falta `tool`, `arguments` no es un objeto |
| 401 | `Unauthorized` | falta el token o no se reconoce |
| 403 | `Forbidden` | un token de agente en una ruta de administración, o al revés |
| 404 | `NotFound` | ruta desconocida |
| 405 | `MethodNotAllowed` | método no admitido en esa ruta |
| 413 | `PayloadTooLarge` | cuerpo de más de 1 MiB |

## API en Python

Servidor, en `quorum/adapters/http_server.py`:

```python
class MonitorServer:
    def __init__(self, quorum: Quorum, tokens: Mapping[str, str], *, admin_token: str | None = None,
                 host: str = "127.0.0.1", port: int = 0,
                 extra_state: Callable[[], Mapping[str, Any]] | None = None) -> None: ...
    # tokens: {token: principal}. La sesión de cada principal se abre la primera vez que se usa su token.
    url: str                      # "http://127.0.0.1:54321"
    def start(self) -> None       # hilo en segundo plano
    def serve_forever(self) -> None
    def stop(self) -> None
    # también funciona como gestor de contexto: with MonitorServer(...) as server: ...
```

Cliente, en `quorum/adapters/http_client.py`:

```python
class RemoteSession:
    def __init__(self, base_url: str, token: str, *, timeout: float = 30.0) -> None: ...
    principal: str
    role: str
    def tool_specs(self) -> list[dict]                      # igual que functions.tool_specs
    def execute(self, name: str, arguments: Mapping | None = None) -> str    # el campo "text"; nunca lanza
    def call(self, name: str, /, *args, **kwargs) -> Any    # el campo "result", un Blocked, o lanza el error del dominio
    # azúcar: remote.open_bid("bid-2") equivale a remote.call("open_bid", "bid-2")

class RemoteAdmin:
    def __init__(self, base_url: str, admin_token: str, *, timeout: float = 30.0) -> None: ...
    def state(self) -> dict
```

`RemoteSession` se comporta como una `Session` local para todo lo que usan los agentes, así que el mismo código de agente funciona en un proceso o repartido en contenedores.

## Lo que este protocolo no cubre

- **Cifrado.** Es HTTP sin TLS, pensado para una red interna de contenedores. En un despliegue real va detrás de TLS o de una malla de servicios.
- **Rotación y caducidad de tokens.** Los tokens se fijan al arrancar.
- **Límite de peticiones.** Los cupos por herramienta de la política siguen aplicando; no hay un límite general por agente.
