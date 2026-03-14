from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.db.models import User
from app.exceptions.DBException import (
    UserAlreadyExist,
    UserNotFound,
    WrongPassword,
)
from app.jwts.hasher import hash_pass, verify_pass


async def create_user(
        login: str,
        password: str,
        db: AsyncSession,
) -> User:
    user = User(login=login, pass_hash=hash_pass(password))
    db.add(user)
    try:
        await db.flush()
    except IntegrityError as e:
        raise UserAlreadyExist(f"User with login {login} already exist")
    return user


def verify_user(
        user: User,
        password: str,
) -> bool:
    return verify_pass(password, user.pass_hash)


async def get_user_by_login(
        login: str,
        db: AsyncSession,
) -> User:
    stmt = select(User).where(User.login == login)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFound(f"User with login {login} is not found")
    return user


async def get_user_by_id(
        user_id: int,
        db: AsyncSession,
) -> User:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFound(f"User with id {user_id} is not found")
    return user


async def authenticate_user(
        login: str,
        password: str,
        db: AsyncSession,
) -> User:
    user = await get_user_by_login(login=login, db=db)
    if not verify_user(user=user, password=password):
        raise WrongPassword(f"Wrong password for user {login}")
    return user


async def update_user_login(
        user: User,
        new_login: str,
        db: AsyncSession,
) -> User:
    user.login = new_login
    try:
        await db.flush()
    except IntegrityError:
        raise UserAlreadyExist(f"User with login {new_login} already exist")
    return user


async def update_user_pass(
        user: User,
        password: str,
        new_password: str,
        db: AsyncSession,
) -> User:
    if not verify_user(user=user, password=password):
        raise WrongPassword(f"Wrong password for user {user.login}")

    user.pass_hash = hash_pass(new_password)
    await db.flush()
    return user


async def delete_user(
        user: User,
        password: str,
        db: AsyncSession,
) -> None:
    if not verify_user(user=user, password=password):
        raise WrongPassword(f"Wrong password for user {user.login}")

    await db.delete(user)
    await db.flush()
