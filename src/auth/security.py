from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from jwt.exceptions import PyJWTError
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer, HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from src.db_depends import get_session
from src.config import settings
from src.auth.models import User
from src.auth.schemas import CreateUser
from src.auth.models import RefreshToken


ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Invalid authentication credentials',
    headers={'WWW-Authenticate': 'Bearer'}
)


async def authenticate_user(
        db: Annotated[AsyncSession, Depends(get_session)],
        username: str,
        password: str
) -> User:
    """
    Проверяет имя пользователя и пароль, возвращает пользователя, если всё ок.
    """
    user = await db.scalar(select(User).where(User.username == username))
    if not user or not bcrypt_context.verify(password, user.hashed_password) or not user.is_active:
        raise HTTPException (
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
            headers={'WWW-Authenticate': 'Bearer'}
        )
    return user


def create_token(
    username: str,
    user_id: int,
    expires_delta: timedelta,
    token_type: str = None
) -> str:
    """
    Универсальная функция создания access/refresh токена.
    """
    payload = {
        'sub': username,
        'id': user_id,
        'exp': int((datetime.now(timezone.utc) + expires_delta).timestamp()),
        'token_type': token_type,
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(username: str, user_id: int, expires_delta: timedelta) -> str:
    """Создание access токена."""
    return create_token(username, user_id, expires_delta, token_type='access')


def create_refresh_token(username: str, user_id: int, expires_delta: timedelta) -> str:
    """Создание refresh токена."""
    return create_token(username, user_id, expires_delta, token_type='refresh')


def verify_access_token(token: str) -> dict:
    """
    Проверяет access токен. Возвращает данные пользователя.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get('token_type') != 'access':
            raise CREDENTIALS_EXCEPTION
        username = payload.get('sub')
        user_id = payload.get('id')
        expire = payload.get('exp')

        if not username or not user_id or not expire:
            raise CREDENTIALS_EXCEPTION

        if expire < datetime.now(timezone.utc).timestamp():
            raise CREDENTIALS_EXCEPTION

        return {'username': username, 'id': user_id}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Access token expired!',
            headers={'WWW-Authenticate': 'Bearer'}
        )

    except jwt.PyJWTError:
        raise CREDENTIALS_EXCEPTION


async def verify_refresh_token(refresh_token: str, db: AsyncSession) -> dict:
    """
    Проверяет refresh токен, возвращает словарь с username и id, если всё ок.
    """
    try:
        payload = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get('token_type') != 'refresh':
            raise CREDENTIALS_EXCEPTION

        if payload.get('sub') is None or payload.get('id') is None:
            raise CREDENTIALS_EXCEPTION

        expire = payload.get('exp')
        if expire is None or expire < datetime.now(timezone.utc).timestamp():
            raise CREDENTIALS_EXCEPTION

        db_token = await db.scalar(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.is_revoked == False
            )
        )

        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Refresh token not found or revoked'
            )
        expires_at = db_token.expires_at
        if not expires_at.tzinfo:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            db_token.is_revoked = True
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Refresh token expired in database'
            )

        return {
            'username': payload['sub'],
            'id': payload['id']
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Refresh token expired!'
        )

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid refresh token'
        )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_session)
) -> User:
    """
    Получает пользователя по access токену, используется как Depends.
    """
    payload = verify_access_token(token)
    user = await db.scalar(select(User).where(User.id == payload['id']))
    if not user or not user.is_active:
        raise CREDENTIALS_EXCEPTION
    return user
