# chimera WebSocket gateway

Exposes the chimera bus (RPC + pub/sub) to web pages over WebSocket, with a
generated TypeScript client. The SvelteKit demo app living in
`src/chimera/web/` is its first consumer.

## Running

**As a controller (recommended)** — add to your `chimera.config`:

```yaml
controller:
  - type: WsGateway
    name: ws
    ws_host: 0.0.0.0
    ws_port: 7667
```

The gateway shares the server's bus: calls and events are delivered
in-process.

**Standalone** — `chimera-ws` joins a running server as a bus peer:

```
chimera-ws --config ~/.chimera/chimera.config     # or -H <host> -P <port>
```

Note the bus is symmetric: the server dials back to the gateway, so
`--bus-host` (auto-detected by default) must be reachable from the server.

There is no authentication in v1 — run it on a trusted network. The `hello`
handshake carries a reserved `auth` field so tokens can be added without
breaking clients.

## Protocol

JSON text frames, tagged by `"type"`. The client MUST send `hello` first:

```jsonc
→ {"type": "hello", "protocol": 1, "auth": null}
← {"type": "welcome", "protocol": 1, "server": {"chimera": "0.2"}, "auth": "none"}
```

Wrong first message → `error` + close `4002`; unsupported version → close
`4001` (`4003` is reserved for auth failures).

Requests carry a client-chosen correlation `id` (string), answered by exactly
one `result` or `error`:

```jsonc
→ {"type": "call", "id": "c1", "path": "/Telescope/0", "method": "slew_to_ra_dec",
   "args": [10.5, -30.2], "kwargs": {}, "timeout": null}
← {"type": "result", "id": "c1", "value": null}

→ {"type": "list", "id": "c2"}          // objects: [{path, class, bases, state, config}]
→ {"type": "describe", "id": "c3", "path": "/Telescope/0"}
                                        // + interfaces, methods, events,
                                        //   config_schema, enums (schema ∪ MRO)
→ {"type": "schema", "id": "c4"}        // the full static interface schema
→ {"type": "ping", "id": "c5"}          // ← {"type": "pong", "id": "c5"}
```

Errors: `{"type": "error", "id": "c1", "code": "...", "message": "..."}` with
codes `not_found` (bus 404), `busy` (bus 503, lane full), `remote_error`
(bus 500, message carries the remote traceback), `timeout` (only the wait was
abandoned — the operation may still complete; there is no cancellation, call
the instrument's abort method instead), `unavailable`, `bad_request`,
`protocol_error`.

Events are subscribed per (path, event) and pushed server-to-client; the
subscribe result echoes the canonical path used in event frames:

```jsonc
→ {"type": "subscribe", "id": "c6", "path": "/Telescope/0", "event": "slew_complete"}
← {"type": "result", "id": "c6", "value": {"path": "/FakeTelescope/fake",
                                           "event": "slew_complete"}}
← {"type": "event", "path": "/FakeTelescope/fake", "event": "slew_complete",
   "args": [10.5, -30.2, "OK"], "kwargs": {}, "ts": 1785000000000}
```

Long-running calls (slews, exposures) simply stay pending — subscribe to the
instrument's events for progress. Slow consumers have events dropped (never
results) once the per-connection outbox fills.

## Code layout

| file | role |
|---|---|
| `protocol.py` | WS envelope structs (msgspec tagged union) |
| `gateway.py` | `GatewayCore`: asyncio WS server on a thread, executor bridge to the Bus |
| `session.py` | per-connection dispatch, outbox writer, cleanup |
| `broker.py` | refcounted (publisher, event) → bus subscription fan-out |
| `introspect.py` | list/describe from `manager.get_status()` + schema |
| `codegen.py` | schema extraction + TypeScript emission |
| `schema.json` | generated interface schema (checked in) |
| `controller.py` / `standalone.py` | the two deployment shells |
| `ts/` | the `chimera-ws-client` TypeScript package |

## Codegen

Interface signatures are read statically from `chimera.interfaces` (python
type annotations) and written to `schema.json` plus
`ts/src/generated/{enums,interfaces,schema}.ts`:

```
chimera-ws-codegen           # regenerate after changing interfaces
chimera-ws-codegen --check   # CI freshness check (also a pytest)
```

## TypeScript client

```ts
import { ChimeraClient, type TelescopeSlew } from "chimera-ws-client";

const client = new ChimeraClient("ws://observatory:7667");
await client.connect();               // auto-reconnects, re-subscribes

const tel = client.get<TelescopeSlew>("/Telescope/0");
await tel.slew_to_ra_dec(10.5, -30.2);           // typed, Promise-based

client.on("/Telescope/0", "slew_complete", (ra, dec, status) => { ... });
```

Build/test: `cd ts && npm ci && npm run build && npm test`.

## Tests

`uv run pytest tests/chimera/controllers/ws/` — protocol round-trips, codegen
freshness, gateway integration (calls, events, refcounting, cleanup), both
shells, and a slow FakeTelescope slew end-to-end.
