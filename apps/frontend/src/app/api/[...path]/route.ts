import { type NextRequest, NextResponse } from "next/server";

import { API_URL } from "@/lib/api";
import { getAccessToken, getRefreshToken, setAuthCookies } from "@/lib/auth";

/**
 * Proxy générique : /api/<path> -> <API_URL>/api/<path>
 * - Injecte le cookie access_token en Bearer
 * - Sur 401, tente un refresh puis rejoue la requête
 *
 * Les routes explicites /api/auth/* (login, logout) priment sur ce catch-all.
 */

async function refreshAccess(): Promise<string | null> {
  const refreshToken = await getRefreshToken();
  if (!refreshToken) return null;

  const res = await fetch(`${API_URL}/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) return null;

  const data = await res.json();
  await setAuthCookies(data.access_token, data.refresh_token);
  return data.access_token as string;
}

async function forward(req: NextRequest, path: string[]) {
  const url = `${API_URL}/api/${path.join("/")}${req.nextUrl.search}`;
  const hasBody = req.method !== "GET" && req.method !== "HEAD";
  const body = hasBody ? await req.text() : undefined;

  const doFetch = (token?: string) =>
    fetch(url, {
      method: req.method,
      headers: {
        "Content-Type": req.headers.get("content-type") ?? "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body,
    });

  const token = await getAccessToken();
  let res = await doFetch(token);

  if (res.status === 401) {
    const refreshed = await refreshAccess();
    if (refreshed) res = await doFetch(refreshed);
  }

  const data = await res.text();
  return new NextResponse(data, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("content-type") ?? "application/json" },
  });
}

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  return forward(req, (await ctx.params).path);
}

export async function POST(req: NextRequest, ctx: Ctx) {
  return forward(req, (await ctx.params).path);
}

export async function PUT(req: NextRequest, ctx: Ctx) {
  return forward(req, (await ctx.params).path);
}

export async function PATCH(req: NextRequest, ctx: Ctx) {
  return forward(req, (await ctx.params).path);
}

export async function DELETE(req: NextRequest, ctx: Ctx) {
  return forward(req, (await ctx.params).path);
}
