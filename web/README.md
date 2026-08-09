# DocForge Web (Auth.js + BFF)

Next.js frontend with **Google OAuth**, **JWT sessions in httpOnly cookies**, and a **BFF proxy** to FastAPI.

## Auth flow

```text
Browser                  Next.js (:3000)                 FastAPI (:8000)
  |                           |                               |
  |  GET /login              |                               |
  |-------------------------->|                               |
  |  Sign in with Google      |                               |
  |-------------------------->|  OAuth code exchange          |
  |                           |------------------------------>| Google
  |  Set-Cookie:              |<------------------------------|
  |  authjs.session-token     |                               |
  |  (httpOnly, JWT/JWE)      |                               |
  |<--------------------------|                               |
  |                           |                               |
  |  POST /api/backend/analyse|                               |
  |  (cookie auto-sent)       |                               |
  |-------------------------->|  auth() reads session         |
  |                           |  mint 5m HS256 JWT            |
  |                           |  Authorization: Bearer …      |
  |                           |------------------------------>|
  |                           |         200 queued            |
  |                           |<------------------------------|
  |<--------------------------|                               |
```

### Why BFF?

Next.js (`:3000`) and FastAPI (`:8000`) are different origins. An httpOnly cookie set by Next.js is **not** sent to FastAPI. So:

1. Browser only talks to Next.js (session cookie stays on `:3000`).
2. Next.js mints a short-lived API JWT (`iss=docforge-web`, `aud=docforge-api`, `exp=5m`).
3. FastAPI verifies that JWT with the shared `AUTH_SECRET`.

## Security practices used

| Practice | Where |
|----------|--------|
| httpOnly session cookie | `auth.ts` cookies |
| `SameSite=Lax` | OAuth-safe CSRF mitigation |
| `Secure` cookies in production | `auth.ts` |
| JWT session strategy | Auth.js `session.strategy: "jwt"` |
| Short session (8h) | `auth.ts` |
| Short API token (5m) | `lib/api-token.ts` |
| `iss` / `aud` / `exp` checks | FastAPI `utilites/auth.py` |
| Middleware route protection | `middleware.ts` |
| No API JWT in localStorage | BFF only |
| Tight CORS on API | `server.py` |

## Google Cloud setup

1. [Google Cloud Console](https://console.cloud.google.com/apis/credentials) → Create OAuth client (Web application).
2. Authorized JavaScript origins: `http://localhost:3000`
3. Authorized redirect URIs: `http://localhost:3000/api/auth/callback/google`
4. Copy Client ID + Client Secret into `web/.env.local`:

```env
AUTH_GOOGLE_ID=...
AUTH_GOOGLE_SECRET=...
```

5. Put the **same** `AUTH_SECRET` in the root `.env` (FastAPI) and `web/.env.local`.

## Run

```powershell
# terminal 1 — API (must have AUTH_SECRET in .env)
docker compose up
# or: uvicorn server:app --reload --port 8000

# terminal 2 — web
cd web
npm run dev
```

Open http://localhost:3000 → redirect to login → Google → analyse UI.

## Test without Google UI

```powershell
# From repo root — verifies FastAPI rejects missing/bad tokens and accepts a valid one
python -m evals.test_auth_jwt
```
