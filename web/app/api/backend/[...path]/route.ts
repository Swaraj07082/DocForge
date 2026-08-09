import { proxyToBackend } from "@/lib/backend";

type RouteContext = { params: Promise<{ path: string[] }> };

async function handle(req: Request, context: RouteContext) {
  const { path } = await context.params;
  const target = path.join("/");
  const url = new URL(req.url);
  const qs = url.searchParams.toString();
  const fullPath = qs ? `${target}?${qs}` : target;

  const init: RequestInit = {
    method: req.method,
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  return proxyToBackend(fullPath, init);
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
