from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from meta import get_db, SessionDep
from models import Note, NoteCreate, NoteOut, NoteUpdate, User, require_owner, get_current_user
from redis_cache import redis_cache

router = APIRouter(
    prefix="/notes",
    tags=["notes"]
)

@router.post("/", response_model=NoteOut)
async def create_note(note: NoteCreate, session: SessionDep, current_user: User = Depends(get_current_user)):
    new_note = Note(title=note.title, content=note.content, owner_id=current_user.id)
    session.add(new_note)
    await session.commit()
    await session.refresh(new_note)
    
    # Инвалидация кеша при создании заметки
    await redis_cache.invalidate_by_prefix("notes")
    
    return new_note

@router.get("/", response_model=list[NoteOut])
@redis_cache.cache(key_prefix="notes", ttl=300, ignore_args=["session"], serializer="json")
async def read_notes(session: SessionDep, skip: int = 0, limit: int = 100, search: str = ""):
    query = select(Note).offset(skip).limit(limit)
    if search:
        query = query.where(Note.title.ilike(f"%{search}%") | Note.content.ilike(f"%{search}%"))
    result = await session.execute(query)
    notes = result.scalars().all()
    return notes


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(note_id: int, session: SessionDep, current_user: User = Depends(get_current_user)):
    stmt = select(Note).where(Note.id == note_id, Note.owner_id == current_user.id)
    result = await session.execute(stmt)
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found or access denied")
    return note

@router.put("/{note_id}", response_model=NoteOut)
async def update_note(note_id: int, note: NoteUpdate, session: SessionDep, current_user: User = Depends(get_current_user)):
    stmt = select(Note).where(Note.id == note_id, Note.owner_id == current_user.id)
    result = await session.execute(stmt)
    db_note = result.scalars().first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found or access denied")
    if note.title is not None:
        db_note.title = note.title
    if note.content is not None:
        db_note.content = note.content
    session.add(db_note)
    await session.commit()
    await session.refresh(db_note)
    
    # Инвалидация кеша при обновлении заметки
    await redis_cache.invalidate_by_prefix("notes")
    
    return db_note

@router.delete("/{note_id}")
async def delete_note(note_id: int, session: SessionDep, current_user: User = Depends(get_current_user)):
    stmt = select(Note).where(Note.id == note_id, Note.owner_id == current_user.id)
    result = await session.execute(stmt)
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found or access denied")
    await session.delete(note)
    await session.commit()
    
    # Инвалидация кеша при удалении заметки
    await redis_cache.invalidate_by_prefix("notes")
    
    return {"detail": "Note deleted"}