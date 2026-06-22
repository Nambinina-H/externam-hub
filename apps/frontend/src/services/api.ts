/**
 * Client API côté navigateur.
 * Passe par les routes proxy Next.js (/api/*) qui injectent le cookie d'accès
 * et gèrent le refresh automatique sur 401.
 */

export class ClientApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ClientApiError";
  }
}

export async function clientApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    throw new ClientApiError(res.status, data?.detail ?? data?.error ?? res.statusText);
  }
  return data as T;
}
