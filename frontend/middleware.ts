import { NextResponse, type NextRequest } from "next/server";

/**
 * Lightweight edge middleware. Auth is enforced client-side via Zustand
 * (token lives in localStorage). This file remains for security headers
 * and easy future role-based redirects from Set-Cookie sessions.
 */
export function middleware(_req: NextRequest) {
  const res = NextResponse.next();
  res.headers.set("X-Frame-Options", "DENY");
  res.headers.set("X-Content-Type-Options", "nosniff");
  res.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  return res;
}

export const config = { matcher: ["/((?!_next|favicon.ico|api/health).*)"] };
