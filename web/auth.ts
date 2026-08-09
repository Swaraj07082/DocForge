import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

/**
 * Auth.js (NextAuth v5) — Google OAuth + JWT sessions in httpOnly cookies.
 *
 * The browser only ever sees Auth.js's encrypted session cookie.
 * Short-lived API JWTs for FastAPI are minted server-side in the BFF proxy.
 */
export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Google({
      clientId: process.env.AUTH_GOOGLE_ID,
      clientSecret: process.env.AUTH_GOOGLE_SECRET,
      authorization: {
        params: {
          prompt: "consent",
          access_type: "offline",
          response_type: "code",
        },
      },
    }),
  ],
  session: {
    strategy: "jwt",
    maxAge: 60 * 60 * 8, // 8 hours
    updateAge: 60 * 30, // refresh session cookie at most every 30 min
  },
  pages: {
    signIn: "/login",
    error: "/login",
  },
  cookies: {
    sessionToken: {
      name:
        process.env.NODE_ENV === "production"
          ? "__Secure-authjs.session-token"
          : "authjs.session-token",
      options: {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        secure: process.env.NODE_ENV === "production",
      },
    },
  },
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account && profile) {
        token.sub = profile.sub ?? token.sub;
        token.email = profile.email ?? token.email;
        token.name = profile.name ?? token.name;
        token.picture =
          typeof profile.picture === "string" ? profile.picture : token.picture;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.sub ?? "";
        session.user.email = token.email ?? session.user.email;
        session.user.name = token.name ?? session.user.name;
        session.user.image =
          typeof token.picture === "string"
            ? token.picture
            : session.user.image;
      }
      return session;
    },
    authorized({ auth: session }) {
      return !!session?.user;
    },
  },
  trustHost: true,
});
