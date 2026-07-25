import type { ApiErrorShape } from "./types";

/**
 * Typed fetch wrapper. Calls are same-origin /api/* — Next.js rewrites forward
 * them to FastAPI (and in prod a proxy attaches the API key server-side).
 */
export class ApiError extends Error {
  code: string;
  status: number;
  detail?: unknown;
  constructor(status: number, code: string, message: string, detail?: unknown) {
    super(message);
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
  } catch {
    throw new ApiError(0, "network", "Can't reach the server. Check your connection.");
  }
  const text = await res.text();

  // The API normally returns JSON, but a 5xx from the proxy/infra layer (e.g. a
  // plain "Internal Server Error") or an empty body would make JSON.parse throw
  // an opaque "Unexpected token" error. Parse defensively and fall back to the
  // raw text / status so the UI shows a readable message instead.
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      if (!res.ok) {
        throw new ApiError(res.status, "server_error", text.trim().slice(0, 200) || res.statusText);
      }
      throw new ApiError(res.status, "bad_response", "The server returned an unexpected response.");
    }
  }

  if (!res.ok) {
    const err = (body as ApiErrorShape)?.error;
    throw new ApiError(res.status, err?.code || "error", err?.message || res.statusText, err?.detail);
  }
  return body as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(data) }),
  patch: <T>(path: string, data: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(data) }),
  put: <T>(path: string, data: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(data) }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
