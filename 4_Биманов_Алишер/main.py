from fastapi import FastAPI, HTTPException, status
from sqlmodel import select, Session, SQLModel
from sqlalchemy import engine, create_engine
from models import User, UserCreate, UserOut, UserLogin
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, UTC

app = FastAPI()

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = "postgresql://alisher:271221@localhost:5432/auth_db"
engine = create_engine(DATABASE_URL)

SECRET_KEY = "1a2b3c4d5e6f7g8h9i0jklmnopqrstuvwx"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: int = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta(minutes=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def hash_password(password: str) -> str:
    return password_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)

def create_db_and_tables():
    engine = create_engine("sqlite:///database.db")
    SQLModel.metadata.create_all(engine)

@app.on_event("startup")
def startup():
    create_db_and_tables()
    
@app.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    with Session(engine) as session:
        existing_user = session.exec(select(User).where(User.username == user.username)).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        
    
        hash_passwordd = hash_password(user.hash_password)
        user.hash_password = hash_passwordd
        new_user = User.from_orm(user)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
    return new_user

@app.post("/login", response_model=UserOut)
def login_user(user: UserLogin):
    with Session(engine) as session:
        
        existing_user = session.exec(select(User).where(User.username == user.username)).first()
        if not existing_user or not verify_password(user.password, existing_user.hash_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        access_token = create_access_token(data={"sub": existing_user.username})
    return {"access_token": access_token, "token_type": "bearer"}   