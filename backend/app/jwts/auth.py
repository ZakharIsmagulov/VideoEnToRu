from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db import get_db
from app.db.models import User
from app.jwts.access_token import decode_access_token
from app.db.users import get_user_by_id
from app.Config import settings


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=settings.token_url,
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (jwt.InvalidTokenError, ValueError):
        raise credentials_exception

    user = await get_user_by_id(user_id=user_id, db=db)
    return user
