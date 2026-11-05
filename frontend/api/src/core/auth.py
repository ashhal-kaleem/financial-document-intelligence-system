import os
import time
import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import httpx
from fastapi import Depends, Request
from src.core.config import get_settings
from src.core.errors import FDISException

_UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
_CACHE_TTL_SECONDS = 60
_token_cache: Dict[str, Tuple[float, "AuthUser"]] = {}


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: Optional[str] = None


class UnauthorizedError(FDISException):
    def __init__(self, detail: str = "Sign in to use this endpoint."):
        super().__init__(title="Unauthorized", detail=detail, status_code=401, code="unauthorized")


async def _verify_with_supabase(token: str) -> Optional[AuthUser]:
    """Ask Supabase Auth who owns this access token. Returns None if invalid."""
    settings = get_settings()
    api_key = settings.SUPABASE_ANON_KEY or settings.SUPABASE_SERVICE_ROLE_KEY
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(
                f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
                headers={"apikey": api_key, "Authorization": f"Bearer {token}"},
            )
    except httpx.HTTPError:
        return None
    if res.status_code != 200:
        return None
    data = res.json()
    if not data.get("id"):
        return None
    user_id = str(data["id"])
    if not _UUID_RE.fullmatch(user_id):
        return None
    return AuthUser(id=user_id, email=data.get("email"))


def auth_bypass_enabled() -> bool:
    """Fail closed: the dev bypass needs AUTH_REQUIRED=false AND DEBUG=true AND no hosting-platform env."""
    s = get_settings()
    if s.AUTH_REQUIRED or not s.DEBUG:
        return False
    return not any(os.environ.get(v) for v in ("RENDER", "VERCEL", "VERCEL_ENV", "FLY_APP_NAME", "K_SERVICE"))


LOCAL_DEV_USER = AuthUser(id="00000000-0000-0000-0000-000000000000", email="dev@localhost")


async def get_current_user(request: Request) -> AuthUser:
    if auth_bypass_enabled():
        return LOCAL_DEV_USER
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise UnauthorizedError()
    token = token.strip()

    now = time.monotonic()
    cached = _token_cache.get(token)
    if cached and cached[0] > now:
        return cached[1]

    user = await _verify_with_supabase(token)
    if user is None:
        raise UnauthorizedError("Invalid or expired session.")
    if len(_token_cache) > 1000:
        _token_cache.clear()
    _token_cache[token] = (now + _CACHE_TTL_SECONDS, user)
    return user
