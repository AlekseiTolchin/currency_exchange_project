from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.auth.models import User
from src.auth.schemas import CreateUser, TokenResponse, RefreshRequest, ReadUser
from src.db_depends import get_session
from src.auth.security import bcrypt_context
from src.auth.models import RefreshToken
from src.auth.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_user
)


auth_router = APIRouter(prefix='/auth', tags=['auth'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')


@auth_router.post('/token', response_model=TokenResponse)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_session)
):
    """Аутентификация и выдача access и refresh токенов."""
    user = await authenticate_user(db, form_data.username, form_data.password)

    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(
        username=user.username,
        user_id=user.id,
        expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=7)
    refresh_token = create_refresh_token(
        username=user.username,
        user_id=user.id,
        expires_delta=refresh_token_expires
    )

    expires_at = datetime.now(timezone.utc) + refresh_token_expires
    db_token = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(db_token)
    await db.commit()

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type':'Bearer'
    }


@auth_router.post('/refresh', response_model=TokenResponse)
async def refresh_access_token(
        body: RefreshRequest,
        db: AsyncSession = Depends(get_session)
):
    """Обновление access и refresh токена (рефреш токен инвалидируется после использования)."""
    info = await verify_refresh_token(body.refresh_token, db)

    old_token = await db.scalar(
        select(RefreshToken).where(
            RefreshToken.token == body.refresh_token,
            RefreshToken.is_revoked == False
        )
    )

    if old_token:
        old_token.is_revoked = True
        await db.commit()

    user = await db.scalar(select(User).where(User.id == info['id']))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    access_token_expires = timedelta(minutes=5)
    access_token = create_access_token(
        username=user.username,
        user_id=user.id,
        expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=7)
    refresh_token = create_refresh_token(
        username=user.username,
        user_id=user.id,
        expires_delta=refresh_token_expires
    )

    expires_at = datetime.now(timezone.utc) + refresh_token_expires
    db_refresh_token = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    await db.commit()

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer'
    }


@auth_router.post('/register', status_code=201)
async def create_user(
    db: Annotated[AsyncSession, Depends(get_session)],
    user: CreateUser
):
    """Регистрация нового пользователя."""
    exist = await db.scalar(select(User).where(
        (User.username == user.username) | (User.email == user.email)
    ))
    if exist:
        raise HTTPException(status_code=400, detail='User already exists')

    db.add(User(
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        email=user.email,
        hashed_password=bcrypt_context.hash(user.password),
    ))
    await db.commit()
    return {'transaction': 'Successful'}


@auth_router.get('/read_current_user', response_model=ReadUser)
async def read_current_user(current_user: Annotated[User, Depends(get_current_user)]):
    """Вернуть текущего пользователя (по access токену)."""
    return current_user
