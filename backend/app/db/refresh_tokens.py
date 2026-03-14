from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.exceptions.DBException import (
    RefreshNotFound,
    RefreshExpired,
    RefreshInactive,
    RefreshRevoked
)
from app.db.models import RefreshToken, User
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from app.Config import settings
from typing import Literal


def generate_refresh_token_value() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_refresh(
    user: User,
    db: AsyncSession,
) -> str:
    raw_refresh = generate_refresh_token_value()
    refresh_hash = hash_refresh_token(raw_refresh)

    refresh = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        status="active",
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(refresh)
    await db.flush()
    return raw_refresh


async def get_refresh(
    raw_refresh: str,
    db: AsyncSession,
) -> RefreshToken:
    refresh_hash = hash_refresh_token(raw_refresh)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == refresh_hash)
    result = await db.execute(stmt)
    refresh = result.scalar_one_or_none()
    if refresh is None:
        raise RefreshNotFound(f"Refresh token {raw_refresh} not found")
    return refresh


async def validate_refresh(
    raw_refresh: str,
    db: AsyncSession,
) -> RefreshToken:
    refresh = await get_refresh(raw_refresh=raw_refresh, db=db)

    now = datetime.now(timezone.utc)

    if refresh.status != "active":
        raise RefreshInactive(f"Refresh token {raw_refresh} is inactive")
    if refresh.revoked_at is not None:
        raise RefreshRevoked(f"Refresh token {raw_refresh} is revoked")

    expires_at = refresh.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        raise RefreshExpired(f"Refresh token {raw_refresh} is expired")

    return refresh


async def rotate_refresh_token(
    raw_refresh: str,
    user: User,
    db: AsyncSession,
) -> str:
    old_refresh = await validate_refresh(raw_refresh=raw_refresh, db=db)

    old_refresh.status = "rotated"
    old_refresh.used_at = datetime.now(timezone.utc)

    new_raw_refresh = await create_refresh(user=user, db=db)
    new_refresh = await get_refresh(raw_refresh=new_raw_refresh, db=db)

    old_refresh.replaced_by_token_id = new_refresh.id
    return new_raw_refresh


async def revoke_refresh_token(
    raw_refresh: str,
    reason: Literal["logout", "banned", "other"],
    db: AsyncSession,
) -> None:
    refresh = await get_refresh(raw_refresh=raw_refresh, db=db)
    refresh.status = "revoked"
    refresh.revoked_at = datetime.now(timezone.utc)
    refresh.revoke_reason = reason
    await db.flush()
