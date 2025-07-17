from fastapi import FastAPI, HTTPException, status
from sqlmodel import select, Session, SQLModel
from sqlalchemy import engine, create_engine
from models import User, UserCreate, UserOut, UserLogin

app = FastAPI()

DATABASE_URL = "postgresql://alisher:271221@localhost:5432/auth_db"
engine = create_engine(DATABASE_URL)

def create_db_and_tables():
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
        
        new_user = User.from_orm(user)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
    return new_user

@app.post("/login", response_model=UserOut)
def login_user(user: UserLogin):
    with Session(engine) as session:
        existing_user = session.exec(select(User).where(User.username == user.username)).first()
        if not existing_user or existing_user.password != user.password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
    return existing_user