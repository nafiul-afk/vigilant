"""
Vigilant — Session Management
Signed-cookie session backend using itsdangerous.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.core.config import get_settings

settings = get_settings()

_serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

SESSION_COOKIE = "vigilant_session"


def _dump_signed(payload: dict) -> str:
    return _serializer.dumps(payload)


def _load_signed(token: str, max_age: int) -> Optional[dict]:
    try:
        return _serializer.loads(token, max_age=max_age)
    except BadSignature:
        return None


def create_session(response: Response, user_id: str) -> None:
    """Write a signed session cookie containing the user_id."""
    token = _dump_signed({"uid": user_id})
    is_secure = settings.BASE_URL.startswith("https")
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=settings.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=is_secure,
    )


def get_current_user_id(request: Request) -> Optional[str]:
    """Extract and verify the user_id from the session cookie."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    data = _load_signed(token, max_age=settings.SESSION_MAX_AGE)
    if not data:
        return None
    return data.get("uid")


def destroy_session(response: Response) -> None:
    """Delete the session cookie."""
    response.delete_cookie(SESSION_COOKIE)


def set_signed_cookie(
    response: Response,
    key: str,
    payload: dict,
    max_age: int,
) -> None:
    """Set an additional signed cookie for short-lived flows like OAuth state."""
    is_secure = settings.BASE_URL.startswith("https")
    response.set_cookie(
        key=key,
        value=_dump_signed(payload),
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=is_secure,
    )


def get_signed_cookie(request: Request, key: str, max_age: int) -> Optional[dict]:
    """Read and verify a signed cookie payload."""
    token = request.cookies.get(key)
    if not token:
        return None
    return _load_signed(token, max_age=max_age)


def delete_cookie(response: Response, key: str) -> None:
    """Delete a named cookie."""
    response.delete_cookie(key)
