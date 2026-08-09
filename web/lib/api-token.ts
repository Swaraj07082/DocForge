import { SignJWT } from "jose";

const encoder = new TextEncoder();

/** Mint a short-lived HS256 JWT that FastAPI will verify. */
export async function mintApiAccessToken(user: {
  id: string;
  email?: string | null;
  name?: string | null;
}): Promise<string> {
  const secret = process.env.AUTH_SECRET;
  if (!secret) {
    throw new Error("AUTH_SECRET is not set");
  }

  return new SignJWT({
    email: user.email ?? undefined,
    name: user.name ?? undefined,
  })
    .setProtectedHeader({ alg: "HS256", typ: "JWT" })
    .setSubject(user.id)
    .setIssuer("docforge-web")
    .setAudience("docforge-api")
    .setIssuedAt()
    .setExpirationTime("5m")
    .sign(encoder.encode(secret));
}
