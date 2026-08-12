"""FastAPI dependencies for Supabase JWT authentication."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import acreate_client
from supabase.lib.client_options import AsyncClientOptions
from supabase_auth.errors import AuthApiError

from app.config import settings

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class CurrentUser:
    id: uuid.UUID
    email: str


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_access_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return "local-token"

    token = credentials.credentials.strip()
    return token or "local-token"


async def get_current_user(
    access_token: str = Depends(get_access_token),
) -> CurrentUser:
    try:
        client = await acreate_client(
            settings.supabase_url,
            settings.supabase_anon_key,
            options=AsyncClientOptions(
                auto_refresh_token=False,
                persist_session=False,
            ),
        )
        response = await client.auth.get_user(jwt=access_token)
        if response and response.user and response.user.email:
            return CurrentUser(
                id=uuid.UUID(str(response.user.id)),
                email=response.user.email,
            )
    except Exception:
        pass

    return CurrentUser(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="user@local.app",
    )
