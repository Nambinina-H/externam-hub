import { cookies } from "next/headers";

const ACCESS_COOKIE = "access_token";
const REFRESH_COOKIE = "refresh_token";
const isProd = process.env.NODE_ENV === "production";

const ACCESS_MAX_AGE = 60 * 15; // 15 min
const REFRESH_MAX_AGE = 60 * 60 * 24 * 7; // 7 jours

export async function setAuthCookies(accessToken: string, refreshToken: string) {
  const store = await cookies();
  const base = { httpOnly: true, secure: isProd, sameSite: "lax" as const, path: "/" };
  store.set(ACCESS_COOKIE, accessToken, { ...base, maxAge: ACCESS_MAX_AGE });
  store.set(REFRESH_COOKIE, refreshToken, { ...base, maxAge: REFRESH_MAX_AGE });
}

export async function clearAuthCookies() {
  const store = await cookies();
  store.delete(ACCESS_COOKIE);
  store.delete(REFRESH_COOKIE);
}

export async function getAccessToken() {
  return (await cookies()).get(ACCESS_COOKIE)?.value;
}

export async function getRefreshToken() {
  return (await cookies()).get(REFRESH_COOKIE)?.value;
}
