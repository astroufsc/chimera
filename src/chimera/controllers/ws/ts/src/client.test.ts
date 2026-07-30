import { beforeEach, describe, expect, it } from "vitest";

import { ChimeraClient } from "./client.js";
import { BusyError, NotFoundError, UnavailableError } from "./errors.js";
import type { ClientMessage } from "./protocol.js";

/** A scriptable stand-in for the browser WebSocket. */
class FakeWebSocket {
  static instances: FakeWebSocket[] = [];

  url: string;
  sent: ClientMessage[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }

  send(data: string): void {
    this.sent.push(JSON.parse(data) as ClientMessage);
  }

  close(): void {
    this.onclose?.();
  }

  // test helpers
  serverOpens(): void {
    this.onopen?.();
    const hello = this.sent.at(-1);
    expect(hello?.type).toBe("hello");
    this.receive({ type: "welcome", protocol: 1, server: {}, auth: "none" });
  }

  receive(frame: unknown): void {
    this.onmessage?.({ data: JSON.stringify(frame) });
  }

  drops(): void {
    this.onclose?.();
  }

  lastId(): string {
    const last = this.sent.at(-1) as { id?: string };
    return last.id!;
  }
}

const connect = async () => {
  const client = new ChimeraClient("ws://test", {
    webSocketImpl: FakeWebSocket as unknown as new (url: string) => WebSocket,
    backoffMinMs: 0,
    backoffMaxMs: 0,
  });
  const pending = client.connect();
  const ws = FakeWebSocket.instances.at(-1)!;
  ws.serverOpens();
  await pending;
  return { client, ws };
};

beforeEach(() => {
  FakeWebSocket.instances = [];
});

describe("correlation", () => {
  it("routes interleaved results to the right calls", async () => {
    const { client, ws } = await connect();

    const first = client.call("/Telescope/0", "get_ra");
    const firstId = ws.lastId();
    const second = client.call("/Telescope/0", "get_dec");
    const secondId = ws.lastId();

    // answer out of order
    ws.receive({ type: "result", id: secondId, value: -30.2 });
    ws.receive({ type: "result", id: firstId, value: 10.5 });

    expect(await first).toBe(10.5);
    expect(await second).toBe(-30.2);
  });
});

describe("error mapping", () => {
  it("maps busy and not_found to typed errors", async () => {
    const { client, ws } = await connect();

    const busy = client.call("/Telescope/0", "slew_to_ra_dec", [1, 2]);
    ws.receive({ type: "error", id: ws.lastId(), code: "busy", message: "lane full" });
    await expect(busy).rejects.toBeInstanceOf(BusyError);

    const missing = client.call("/Nope/0", "x");
    ws.receive({
      type: "error",
      id: ws.lastId(),
      code: "not_found",
      message: "no object",
    });
    await expect(missing).rejects.toBeInstanceOf(NotFoundError);
  });

  it("rejects pending calls when the connection drops", async () => {
    const { client, ws } = await connect();
    const stuck = client.call("/Telescope/0", "get_ra");
    ws.drops();
    await expect(stuck).rejects.toBeInstanceOf(UnavailableError);
    client.close();
  });
});

describe("events", () => {
  it("delivers events, including under the resolved canonical path", async () => {
    const { client, ws } = await connect();

    const seen: unknown[][] = [];
    client.on("/Telescope/0", "slew_complete", (...args) => seen.push(args));

    const subscribe = ws.sent.at(-1)!;
    expect(subscribe.type).toBe("subscribe");
    // the gateway echoes the canonical path
    ws.receive({
      type: "result",
      id: ws.lastId(),
      value: { path: "/FakeTelescope/fake", event: "slew_complete" },
    });
    ws.receive({
      type: "event",
      path: "/FakeTelescope/fake",
      event: "slew_complete",
      args: [10.5, -30.2, "OK"],
      kwargs: {},
      ts: 1,
    });

    expect(seen).toEqual([[10.5, -30.2, "OK"]]);
  });

  it("unsubscribes when the last handler is removed", async () => {
    const { client, ws } = await connect();
    const off = client.on("/Telescope/0", "slew_begin", () => {});
    ws.receive({
      type: "result",
      id: ws.lastId(),
      value: { path: "/Telescope/0", event: "slew_begin" },
    });
    off();
    expect(ws.sent.at(-1)!.type).toBe("unsubscribe");
  });
});

describe("reconnect", () => {
  it("re-hellos and re-subscribes active events on a new socket", async () => {
    const { client, ws } = await connect();
    client.on("/Telescope/0", "slew_complete", () => {});
    ws.receive({
      type: "result",
      id: ws.lastId(),
      value: { path: "/Telescope/0", event: "slew_complete" },
    });

    ws.drops();
    // wait for the 0 ms backoff timer to fire
    await new Promise((resolve) => setTimeout(resolve, 1));

    const next = FakeWebSocket.instances.at(-1)!;
    expect(next).not.toBe(ws);
    next.serverOpens();

    const resubscribe = next.sent.at(-1)!;
    expect(resubscribe.type).toBe("subscribe");
    expect(resubscribe).toMatchObject({
      path: "/Telescope/0",
      event: "slew_complete",
    });
    expect(client.status).toBe("open");
    client.close();
  });
});
