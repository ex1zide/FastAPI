from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from .models import User, UserCreate, UserLogin, UserOut, NoteOut, NoteCreate, NoteUpdate, NoteDelete, Token
from .main import get_session, hash_password, verify_password, create_access_token, get_current_user, required_role


router = APIRouter(tags=["API"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.username == user.username)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, password=hashed_password, role="user")
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return UserOut(id=db_user.id, username=db_user.username)

@router.post("/login", response_model=Token)
def login(user: UserLogin, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.username == user.username)).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": db_user.username})
    return Token(access_token=access_token, token_type="bearer")

@router.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserOut(id=current_user.id, username=current_user.username)

@router.get("/admin", response_model=UserOut, dependencies=[Depends(required_role("admin"))])
async def read_admin(current_user: User = Depends(get_current_user)):
    return UserOut(id=current_user.id, username=current_user.username)

#CRUD

@router.get("/notes", response_model=list[NoteOut])
async def read_notes(session: Session = Depends(get_session), skip: int = 0, limit: int = 100, search: str = None):
    query = select(NoteOut).offset(skip).limit(limit)
    if search:
        query = query.where(NoteOut.title.contains(search) | NoteOut.content.contains(search))
    notes = await session.exec(query).all()
    return notes

@router.post("/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(note: NoteCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_note = NoteOut(**note.dict(), owner_id=current_user.id)
    await session.add(db_note)
    await session.commit()
    await session.refresh(db_note)
    return db_note

@router.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(note_id: int, note: NoteUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_note = await session.exec(select(NoteOut).where(NoteOut.id == note_id, NoteOut.owner_id == current_user.id)).first()
    if not db_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    
    for key, value in note.dict(exclude_unset=True).items():
        setattr(db_note, key, value)

    await session.add(db_note)
    await session.commit()
    await session.refresh(db_note)
    return db_note

@router.delete("/notes/{note_id}", response_model=NoteDelete)
async def delete_note(note_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_note = await session.exec(select(NoteOut).where(NoteOut.id == note_id, NoteOut.owner_id == current_user.id)).first()
    if not db_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    
    await session.delete(db_note)
    await session.commit()
    return NoteDelete(id=note_id, owner_id=current_user.id, message="Note deleted successfully")