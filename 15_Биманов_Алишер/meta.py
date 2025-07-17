from datetime import datetime, timedelta, UTC
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import Optional, Annotated
from sqlalchemy.orm import DeclarativeBase
from fastapi import Depends
from sqlmodel import SQLModel
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from settings import settings

CURRENT_DATETIME = datetime.now(UTC)  

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

engine = create_async_engine(settings.database_url, echo=settings.debug)
session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_db():
    async with session_factory() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_db)]

class Base(DeclarativeBase):
    pass

@asynccontextmanager
async def lifespan(app):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield