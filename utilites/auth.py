"""JWT auth for FastAPI — verifies short-lived tokens minted by the Next.js BFF."""

from __future__ import annotations

import os
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=True)

ISS = "docforge-web"
AUD = "docforge-api"
ALG = "HS256"


def _secret() -> str:
    secret = os.getenv("AUTH_SECRET")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AUTH_SECRET is not configured on the API",
        )
    return secret


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict[str, Any]:
    """Decode and validate the Bearer JWT from the Next.js BFF."""
    try:
        payload = jwt.decode(
            creds.credentials,
            _secret(),
            algorithms=[ALG],
            audience=AUD,
            issuer=ISS,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    if not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )
    return payload
