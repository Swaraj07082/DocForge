import { auth } from "@/auth";
import { mintApiAccessToken } from "@/lib/api-token";

const API_BASE = process.env.DOCFORGE_API_URL ?? "http://127.0.0.1:8000";

export async function proxyToBackend(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const session = await auth();
  if (!session?.user?.id) {
    return Response.json({ detail: "Unauthorized" }, { status: 401 });
  }

  const token = await mintApiAccessToken({
    id: session.user.id,
    email: session.user.email,
    name: session.user.name,
  });

  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const url = `${API_BASE.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
  const upstream = await fetch(url, {
    ...init,
    headers,
    cache: "no-store",
  });

  const body = await upstream.arrayBuffer();
  return new Response(body, {
    status: upstream.status,
    headers: {
      "Content-Type":
        upstream.headers.get("Content-Type") ?? "application/json",
    },
  });
}
