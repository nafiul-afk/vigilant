"""
Vigilant — Password Hashing
Uses passlib with bcrypt for secure password storage.
"""

import bcrypt
from passlib.context import CryptContext

# Passlib 1.7.x expects `bcrypt.__about__.__version__`, which was removed in
# newer bcrypt releases. Populate it when missing so hashing stays quiet.
if not hasattr(bcrypt, "__about__"):
    class _BcryptAbout:
        __version__ = getattr(bcrypt, "__version__", "unknown")

    bcrypt.__about__ = _BcryptAbout()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)
