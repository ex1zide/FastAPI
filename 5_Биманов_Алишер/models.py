from sqlmodel import Field, SQLModel
from typing import Optional
from pydantic import BaseModel


class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    hash_password: str = Field(nullable=False)

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str

class UserLogin(BaseModel):
    username: str
    password: str