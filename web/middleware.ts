export { auth as middleware } from "@/auth";

export const config = {
  matcher: [
    /*
     * Protect everything except:
     * - login page
     * - Auth.js routes
     * - static assets
     */
    "/((?!login|api/auth|_next/static|_next/image|favicon.ico).*)",
  ],
};
