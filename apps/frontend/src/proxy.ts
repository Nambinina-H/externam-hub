import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

/**
 * Garde d'authentification basée sur le cookie HttpOnly `access_token`.
 * (Convention Next 16 : fichier `proxy.ts`, remplace l'ancien `middleware.ts`.)
 * - `/dashboard/*` sans cookie → redirection vers la page de login.
 * - `/auth/*` avec cookie → redirection vers le dashboard (déjà connecté).
 */
export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const hasToken = req.cookies.has("access_token");

  if (pathname.startsWith("/dashboard") && !hasToken) {
    const url = req.nextUrl.clone();
    url.pathname = "/auth/login";
    return NextResponse.redirect(url);
  }

  if (pathname.startsWith("/auth") && hasToken) {
    const url = req.nextUrl.clone();
    url.pathname = "/dashboard";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/auth/:path*"],
};
