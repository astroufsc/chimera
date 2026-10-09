// The WS envelope protocol, mirroring the msgspec structs in
// src/chimera/controllers/ws/protocol.py. Keep the two in sync by hand —
// the shapes are small and stable.

export const PROTOCOL_VERSION = 1;

export interface AuthInfo {
  scheme: string;
  token: string;
}

// client -> server

export interface HelloMessage {
  type: "hello";
  protocol: number;
  auth?: AuthInfo | null;
}

export interface CallMessage {
  type: "call";
  id: string;
  path: string;
  method: string;
  args?: unknown[];
  kwargs?: Record<string, unknown>;
  timeout?: number | null;
}

export interface SubscribeMessage {
  type: "subscribe";
  id: string;
  path: string;
  event: string;
}

export interface UnsubscribeMessage {
  type: "unsubscribe";
  id: string;
  path: string;
  event: string;
}

export interface ListMessage {
  type: "list";
  id: string;
}

export interface DescribeMessage {
  type: "describe";
  id: string;
  path: string;
}

export interface SchemaMessage {
  type: "schema";
  id: string;
}

export interface PingMessage {
  type: "ping";
  id: string;
}

export type ClientMessage =
  | HelloMessage
  | CallMessage
  | SubscribeMessage
  | UnsubscribeMessage
  | ListMessage
  | DescribeMessage
  | SchemaMessage
  | PingMessage;

// server -> client

export interface WelcomeMessage {
  type: "welcome";
  protocol: number;
  server: Record<string, string>;
  auth: string;
}

export interface ResultMessage {
  type: "result";
  id: string;
  value: unknown;
}

export interface ErrorMessage {
  type: "error";
  id: string | null;
  code: string;
  message: string;
  details?: unknown;
}

export interface EventMessage {
  type: "event";
  path: string;
  event: string;
  args: unknown[];
  kwargs: Record<string, unknown>;
  ts: number;
}

export interface PongMessage {
  type: "pong";
  id: string;
}

export type ServerMessage =
  | WelcomeMessage
  | ResultMessage
  | ErrorMessage
  | EventMessage
  | PongMessage;

// payloads of list/describe results

export interface ObjectInfo {
  path: string;
  class: string;
  bases: string[];
  state: string | null;
  config: Record<string, unknown>;
}

export interface TypeDescriptor {
  kind: string;
  enum?: string;
  items?: TypeDescriptor[];
  item?: TypeDescriptor;
  value?: TypeDescriptor;
  options?: TypeDescriptor[];
}

export interface ParamSchema {
  name: string;
  type: TypeDescriptor;
  default?: unknown;
  variadic?: "positional" | "keyword";
}

export interface MethodSchema {
  doc: string | null;
  params: ParamSchema[];
  returns: TypeDescriptor;
}

export interface EventSchema {
  doc: string | null;
  params: ParamSchema[];
}

export interface ConfigEntrySchema {
  type: TypeDescriptor;
  default: unknown;
  choices?: unknown[];
  range?: unknown[];
}

export interface ObjectDescription extends ObjectInfo {
  interfaces: string[];
  methods: Record<string, MethodSchema>;
  events: Record<string, EventSchema>;
  config_schema: Record<string, ConfigEntrySchema>;
  enums: Record<string, string[]>;
}
