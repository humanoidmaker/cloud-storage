import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings


class TokenError(Exception):
    """Raised when token validation fails."""
    pass


def create_access_token(user_id: uuid.UUID, email: str, role: str) -> str:
    """Create a JWT access token with user claims."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Create a JWT refresh token with longer expiry."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises TokenError on any failure."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if "sub" not in payload:
            raise TokenError("Token missing subject claim")
        return payload
    except JWTError as e:
        raise TokenError(f"Invalid token: {str(e)}")


def decode_access_token(token: str) -> dict:
    """Decode an access token and verify it's an access token type."""
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise TokenError("Not an access token")
    return payload


def decode_refresh_token(token: str) -> dict:
    """Decode a refresh token and verify it's a refresh token type."""
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise TokenError("Not a refresh token")
    return payload
