from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.schemas.tokens import TokenOnly
from app.db.users import authenticate_user, get_user_by_id, create_user
from app.jwts.access_token import create_access_token
from app.db.refresh_tokens import (
    revoke_refresh_token,
    rotate_refresh_token,
    validate_refresh,
    create_refresh,
)
from app.db.DBException import (
    UserNotFound,
    WrongPassword,
    RefreshException,
    UserAlreadyExist,
)
from app.Config import settings
from logging import getLogger


logger = getLogger(settings.api_logger)
INTERNAL_ERROR = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Internal server error",
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOnly)
async def register_for_tokens(
        response: Response,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenOnly:
    try:
        user = await create_user(
            login=form_data.username,
            password=form_data.password,
            db=db,
        )
    except UserAlreadyExist as e:
        logger.error(f"/users/register: User with login {form_data.username} already exist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exist",
        )
    except Exception as e:
        logger.error(f"/users/register: Unknown error with registration {form_data.username}: {str(e)}")
        raise INTERNAL_ERROR

    access_token = create_access_token(user_id=user.id)
    refresh_token = await create_refresh(user=user, db=db)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_secure_cookie,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 60 * 60 * 24,
        path="/auth",
    )

    return TokenOnly(
        access_token=access_token,
        token_type="bearer",
    )


@router.post("/login", response_model=TokenOnly)
async def login_for_tokens(
        response: Response,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenOnly:
    try:
        user = await authenticate_user(
            login=form_data.username,
            password=form_data.password,
            db=db,
        )
    except (UserNotFound, WrongPassword) as e:
        logger.error(f"/auth/login: Login for {form_data.username} failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"/auth/login: Login for {form_data.username} failed (internal error): {str(e)}")
        raise INTERNAL_ERROR

    access_token = create_access_token(user_id=user.id)
    refresh_token = await create_refresh(user=user, db=db)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_secure_cookie,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 60 * 60 * 24,
        path="/auth",
    )

    return TokenOnly(
        access_token=access_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenOnly)
async def refresh_tokens(
        response: Response,
        raw_refresh: Annotated[str | None, Cookie()] = None,
        db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> TokenOnly:
    if raw_refresh is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    try:
        refresh = await validate_refresh(raw_refresh=raw_refresh, db=db)
    except RefreshException as e:
        logger.error(f"/auth/refresh: Refresh token {raw_refresh} failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    try:
        user = await get_user_by_id(user_id=refresh.user_id, db=db)
    except UserNotFound as e:
        logger.error(f"/auth/refresh: User not found for {refresh.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    except Exception as e:
        logger.error(f"/auth/refresh: Internal error for {refresh.user_id}: {str(e)}")
        raise INTERNAL_ERROR

    new_access_token = create_access_token(user_id=user.id)
    try:
        new_refresh_token = await rotate_refresh_token(
            raw_refresh=raw_refresh,
            user=user,
            db=db,
        )
    except Exception as e:
        logger.error(f"/auth/refresh: Refresh error: {str(e)}")
        raise INTERNAL_ERROR

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.is_secure_cookie,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 60 * 60 * 24,
        path="/auth",
    )

    return TokenOnly(
        access_token=new_access_token,
        token_type="bearer",
    )


@router.post("/logout", status_code=204)
async def logout(
        response: Response,
        refresh_token: Annotated[str | None, Cookie()] = None,
        db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> None:
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    try:
        await revoke_refresh_token(
            raw_refresh=refresh_token,
            reason="logout",
            db=db,
        )
    except RefreshException as e:
        logger.error(f"/auth/logout: Refresh token {refresh_token} not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    response.delete_cookie(
        key="refresh_token",
        path="/auth",
    )
