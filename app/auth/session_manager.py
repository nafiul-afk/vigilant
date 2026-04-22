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


def create_session(response: Response, user_id: str) -> None:
    """Write a signed session cookie containing the user_id."""
    token = _serializer.dumps({"uid": user_id})
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=settings.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,  # set True in production behind HTTPS
    )


def get_current_user_id(request: Request) -> Optional[str]:
    """Extract and verify the user_id from the session cookie."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        data = _serializer.loads(token, max_age=settings.SESSION_MAX_AGE)
        return data.get("uid")
    except BadSignature:
        return None


def destroy_session(response: Response) -> None:
    """Delete the session cookie."""
    response.delete_cookie(SESSION_COOKIE)
