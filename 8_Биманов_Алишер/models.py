from sqlmodel import Field, SQLModel
from typing import Optional
from pydantic import BaseModel


class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    hash_password: str = Field(nullable=False)
    role: str = Field(default="user", nullable=False)  

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    role: str
class UserLogin(BaseModel):
    username: str
    password: str
    
    
class Note(SQLModel, table=True):
    __tablename__ = "notes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False)
    content: str = Field(nullable=False)
    owner_id: int = Field(foreign_key="users.id", nullable=False)

class NoteCreate(BaseModel):
    title: str
    content: str
    
class NoteOut(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class NoteDelete(BaseModel):
    id: int
    owner_id: int
    
class Token(BaseModel):
    access_token: str
    token_type: str