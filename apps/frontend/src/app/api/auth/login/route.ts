import { NextRequest, NextResponse } from "next/server";

import { api, ApiError } from "@/lib/api";
import { setAuthCookies } from "@/lib/auth";

interface TokenResponse {
  access_token: string;
  refresh_token: string;
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  try {
    const data = await api<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    });
    await setAuthCookies(data.access_token, data.refresh_token);
    return NextResponse.json({ success: true });
  } catch (e) {
    const status = e instanceof ApiError ? e.status : 500;
    return NextResponse.json({ error: (e as Error).message }, { status });
  }
}
