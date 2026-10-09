import type { ErrorMessage } from "./protocol.js";

/** Base class for every failure surfaced by the gateway or the client. */
export class ChimeraError extends Error {
  readonly code: string;
  readonly details: unknown;

  constructor(code: string, message: string, details: unknown = null) {
    super(message);
    this.name = new.target.name;
    this.code = code;
    this.details = details;
  }
}

/** The object path (or method) does not exist on the server. */
export class NotFoundError extends ChimeraError {}

/** The object's serialized-method lane is full (bus 503). */
export class BusyError extends ChimeraError {}

/** The call's wait timed out — the remote operation MAY still complete. */
export class TimeoutError extends ChimeraError {}

/** The gateway cannot reach the chimera server, or the connection dropped. */
export class UnavailableError extends ChimeraError {}

/** The remote method raised; message carries the remote traceback text. */
export class RemoteError extends ChimeraError {}

const BY_CODE: Record<string, typeof ChimeraError> = {
  not_found: NotFoundError,
  busy: BusyError,
  timeout: TimeoutError,
  unavailable: UnavailableError,
  remote_error: RemoteError,
};

export function errorFromMessage(frame: ErrorMessage): ChimeraError {
  const cls = BY_CODE[frame.code] ?? ChimeraError;
  return new cls(frame.code, frame.message, frame.details ?? null);
}
