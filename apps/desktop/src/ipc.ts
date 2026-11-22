import { invoke } from "@tauri-apps/api/core";

export interface WorkspaceStatusRequest {
  schemaVersion: 1;
  commandId: "workspace.status";
  correlationId: string;
  workspaceScope: "local";
  payload: Record<string, never>;
}

export interface WorkspaceStatusReply {
  schemaVersion: 1;
  commandId: "workspace.status";
  correlationId: string;
  status: "ok";
  workspaceState: "not_configured";
  writable: false;
}

export class TransportError extends Error {
  constructor(readonly code: "ZYN-IPC-CLIENT" | "ZYN-IPC-TIMEOUT" | "ZYN-IPC-RESPONSE") {
    super(code);
    this.name = "TransportError";
  }
}

function checkReply(value: unknown, correlationId: string): WorkspaceStatusReply {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new TransportError("ZYN-IPC-RESPONSE");
  }
  const v = value as Record<string, unknown>;
  const keys = Object.keys(v);
  if (keys.length !== 6 ||
      v.schemaVersion !== 1 || v.commandId !== "workspace.status" ||
      v.correlationId !== correlationId || v.status !== "ok" ||
      v.workspaceState !== "not_configured" || v.writable !== false) {
    throw new TransportError("ZYN-IPC-RESPONSE");
  }
  return value as WorkspaceStatusReply;
}

export async function probeWorkspaceStatus(timeoutMs = 4000): Promise<WorkspaceStatusReply> {
  const correlationId = globalThis.crypto?.randomUUID?.();
  if (!correlationId) throw new TransportError("ZYN-IPC-CLIENT");
  const request: WorkspaceStatusRequest = {
    schemaVersion: 1,
    commandId: "workspace.status",
    correlationId,
    workspaceScope: "local",
    payload: {},
  };
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    const result: unknown = await Promise.race([
      invoke<unknown>("workspace_handshake", { request }),
      new Promise<never>((_, reject) => {
        timer = setTimeout(() => reject(new TransportError("ZYN-IPC-TIMEOUT")), timeoutMs);
      }),
    ]);
    return checkReply(result, correlationId);
  } finally {
    if (timer !== undefined) clearTimeout(timer);
  }
}
