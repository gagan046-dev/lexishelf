// Use the computer's LAN address for EXPO_PUBLIC_API_BASE_URL when testing on a physical device.
export const API_BASE_URL = (process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000")
  .replace(/\/$/, "");

let authToken: string | null = null;

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly errorCode?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const actionableMessages: Record<string, string> = {
  GROQ_NOT_CONFIGURED: "AI explanations are not configured on the server.",
  GROQ_UNAVAILABLE: "The explanation service is temporarily unreachable. Try again shortly.",
  GROQ_RATE_LIMITED: "The explanation service is busy. Wait a moment, then try again.",
  GROQ_INVALID_RESPONSE: "The explanation was incomplete. Please try the word again.",
  GROQ_EMPTY_RESPONSE: "The explanation was incomplete. Please try the word again.",
  GROQ_TIMEOUT: "The server is waking up or busy. Please try again in a few seconds.",
  GROQ_REQUEST_FAILED: "The explanation service is temporarily unavailable. Try again shortly.",
  AGENT_NOT_CONFIGURED: "Agent Chat is not configured on the server.",
  AGENT_RUNTIME_UNAVAILABLE: "Agent Chat is temporarily unavailable on the server.",
  AGENT_EXECUTION_FAILED: "The assistant is busy or waking up. Please try again in a few seconds.",
  AGENT_EMPTY_RESPONSE: "The assistant did not return a response. Please try again.",
};

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError && error.errorCode && actionableMessages[error.errorCode]) {
    return actionableMessages[error.errorCode];
  }
  return error instanceof Error ? error.message : fallback;
}

export function setAuthToken(token: string | null) {
  authToken = token;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body?.detail;
    const message = typeof detail === "string"
      ? detail
      : detail?.message ?? body?.message ?? `Request failed (${response.status})`;
    throw new ApiError(message, response.status, detail?.error_code ?? body?.error_code);
  }

  return response.status === 204 ? (undefined as T) : response.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "DELETE", body: body ? JSON.stringify(body) : undefined }),
};
