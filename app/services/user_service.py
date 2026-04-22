"""
Vigilant — User Service
All user-related business logic lives here, never in the routes.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.hashing import hash_password, verify_password
from app.models.user import User


def create_user(db: Session, email: str, username: str, password: str) -> User:
    """Register a new user with a hashed password."""
    user = User(
        email=email.lower().strip(),
        username=username.strip(),
        hashed_password=hash_password(password),
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Validate credentials. Returns the User on success, None on failure."""
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user or not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Fetch a user by primary key."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Fetch a user by email address."""
    return db.query(User).filter(User.email == email.lower().strip()).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Fetch a user by username."""
    return db.query(User).filter(User.username == username.strip()).first()


def get_or_create_oauth_user(
    db: Session,
    email: str,
    username: str,
    provider: str,
    avatar_url: Optional[str] = None,
) -> User:
    """Find or create a user from an OAuth provider."""
    user = get_user_by_email(db, email)
    if user:
        return user
    user = User(
        email=email.lower().strip(),
        username=username,
        is_oauth_user=True,
        oauth_provider=provider,
        avatar_url=avatar_url,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
