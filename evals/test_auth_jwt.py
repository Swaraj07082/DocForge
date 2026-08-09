"""Offline + live checks for the Next.js → FastAPI JWT contract."""

from __future__ import annotations

import os
import sys
import time
import urllib.error
import urllib.request

import jwt
from dotenv import load_dotenv

load_dotenv()

ISS = "docforge-web"
AUD = "docforge-api"
ALG = "HS256"
API = os.getenv("DOCFORGE_API_URL", "http://127.0.0.1:8000")


def mint(secret: str, *, exp_seconds: int = 300, sub: str = "test-user") -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": sub,
            "email": "test@example.com",
            "name": "Test User",
            "iss": ISS,
            "aud": AUD,
            "iat": now,
            "exp": now + exp_seconds,
        },
        secret,
        algorithm=ALG,
    )


def request(
    path: str,
    *,
    method: str = "GET",
    token: str | None = None,
    body: bytes | None = None,
) -> tuple[int, str]:
    headers: dict[str, str] = {}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        f"{API.rstrip('/')}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        return 0, str(exc.reason)


def main() -> int:
    secret = os.getenv("AUTH_SECRET")
    if not secret:
        print("FAIL: AUTH_SECRET not set in environment / .env")
        return 1

    token = mint(secret)
    payload = jwt.decode(
        token,
        secret,
        algorithms=[ALG],
        audience=AUD,
        issuer=ISS,
    )
    assert payload["sub"] == "test-user"
    print("OK  offline mint + verify")

    expired = mint(secret, exp_seconds=-10)
    try:
        jwt.decode(expired, secret, algorithms=[ALG], audience=AUD, issuer=ISS)
        print("FAIL: expired token should not verify")
        return 1
    except jwt.ExpiredSignatureError:
        print("OK  expired token rejected offline")

    code, body = request("/me", token=None)
    if code == 0:
        print(f"SKIP live API ({body}) — start FastAPI to test HTTP layer")
        return 0

    if code not in (401, 403):
        print(f"FAIL: expected 401 without token, got {code}: {body[:200]}")
        return 1
    print(f"OK  live /me without token -> {code}")

    bad_code, _ = request("/me", token="not.a.jwt")
    if bad_code != 401:
        print(f"FAIL: expected 401 for bad token, got {bad_code}")
        return 1
    print(f"OK  live /me bad token -> {bad_code}")

    good_code, good_body = request("/me", token=token)
    if good_code != 200:
        print(f"FAIL: valid token rejected: {good_code} {good_body[:200]}")
        return 1
    if "test-user" not in good_body:
        print(f"FAIL: unexpected /me body: {good_body[:200]}")
        return 1
    print(f"OK  live /me valid token -> {good_code} {good_body}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
