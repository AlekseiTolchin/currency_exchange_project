from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .db import async_session_maker

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
