# chimera web

A SvelteKit + Tailwind web UI for chimera, talking to the WebSocket gateway
(`src/chimera/controllers/ws/`). Three views:

- **Objects** — every object on the server, grouped by class, with state chips
- **Object detail** (`/object/<Class>/<name>`) — works for *any* interface:
  live config (click a value to edit), event subscriptions with a live log,
  and auto-generated invoke forms for every method
- **Telescope** (`/telescope`) — a handcrafted panel: RA/Dec + Alt/Az readout
  (1 Hz poll + live events), slew/abort, park, tracking and cover controls,
  capability-gated by what the telescope implements

## Development

Run a chimera server with the gateway controller (see
`../controllers/ws/README.md`), then:

```sh
cd src/chimera/controllers/ws/ts && npm ci && npm run build   # once
cd src/chimera/web && npm ci
npm run dev -- --open
```

The app connects to `ws://<page host>:7667` by default; point it elsewhere
with `VITE_CHIMERA_WS=ws://observatory:7667 npm run dev`.

## Production

```sh
npm run build     # static SPA in build/, serve with any file server
```

There is no auth in v1 — serve it only on a trusted network.
