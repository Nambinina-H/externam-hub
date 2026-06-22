import type { AuthUser } from "@externam/shared";

import { clientApi } from "./api";

export async function login(email: string, password: string) {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error((await res.json()).error ?? "Échec de la connexion");
  return res.json();
}

export async function logout() {
  await fetch("/api/auth/logout", { method: "POST" });
}

export async function getMe(): Promise<AuthUser> {
  return clientApi<AuthUser>("/users/me");
}
