import uuid

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.tokens import TokenError, decode_access_token

security = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(self, user_id: uuid.UUID, email: str, role: str):
        self.user_id = user_id
        self.email = email
        self.role = role


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser:
    """Extract and validate the current user from the JWT token."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
        email = payload.get("email", "")
        role = payload.get("role", "user")
        return CurrentUser(user_id=user_id, email=email, role=role)
    except TokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except (ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid token payload")


async def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Require admin or superadmin role."""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def require_superadmin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Require superadmin role."""
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return current_user


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
