import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import CurrentUser, get_client_ip, get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.activity_service import ActivityService
from app.utils.hashing import hash_password, verify_password
from app.utils.tokens import TokenError, create_access_token, create_refresh_token, decode_refresh_token
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=UserResponse)
async def register(body: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.REGISTRATION_ENABLED:
        raise HTTPException(status_code=403, detail="Registration is disabled")

    # Check duplicate email
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Validate password strength
    if len(body.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

    user = User(
        id=uuid.uuid4(),
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        role="user",
        storage_quota=settings.DEFAULT_STORAGE_QUOTA_BYTES,
    )
    db.add(user)
    await db.flush()

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=user.id, action="register", ip_address=get_client_ip(request)
    )

    return user


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access_token = create_access_token(user.id, user.email, user.role)
    refresh_token = create_refresh_token(user.id)

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=user.id, action="login", ip_address=get_client_ip(request)
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_refresh_token(body.refresh_token)
        user_id = uuid.UUID(payload["sub"])
    except TokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access_token = create_access_token(user.id, user.email, user.role)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=current_user.user_id, action="logout", ip_address=get_client_ip(request)
    )
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.password_hash = hash_password(body.new_password)
    await db.flush()

    activity_svc = ActivityService(db)
    await activity_svc.log_activity(
        user_id=user.id, action="password_change", ip_address=get_client_ip(request)
    )

    return {"message": "Password changed successfully"}
