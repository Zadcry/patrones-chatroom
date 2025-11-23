# backend/app/routers/rooms.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import Room, RoomMember, User
from app.schemas.schemas import RoomCreate, RoomResponse, RoomJoin
from app.core.security import get_current_user, get_password_hash, verify_password

router = APIRouter(prefix="/rooms", tags=["Rooms"])

@router.post("/", response_model=RoomResponse)
def create_room(
    room: RoomCreate, 
    db: Session = Depends(get_db), 
    username: str = Depends(get_current_user)
):
    # Obtener ID del usuario creador
    user = db.query(User).filter(User.username == username).first()
    
    # Validar unicidad nombre sala
    if db.query(Room).filter(Room.name == room.name).first():
        raise HTTPException(status_code=400, detail="Room name already exists")

    # Hash del password si la sala es privada
    room_pwd_hash = None
    if room.is_private:
        if not room.password:
            raise HTTPException(status_code=400, detail="Private rooms require a password")
        room_pwd_hash = get_password_hash(room.password)

    new_room = Room(name=room.name, is_private=room.is_private, password_hash=room_pwd_hash, created_by=user.id)
    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    # Agregar al creador como miembro admin automáticamente
    member = RoomMember(room_id=new_room.id, user_id=user.id, role="admin")
    db.add(member)
    db.commit()

    return new_room

@router.get("/", response_model=List[RoomResponse])
def list_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()

@router.post("/{room_id}/join")
def join_room(
    room_id: int, 
    join_data: RoomJoin, 
    db: Session = Depends(get_db), 
    username: str = Depends(get_current_user)
):
    user = db.query(User).filter(User.username == username).first()
    room = db.query(Room).filter(Room.id == room_id).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Verificar si ya es miembro
    if db.query(RoomMember).filter_by(room_id=room_id, user_id=user.id).first():
        return {"message": "Already joined"}

    # Verificar password si es privada
    if room.is_private:
        if not join_data.password or not verify_password(join_data.password, room.password_hash):
            raise HTTPException(status_code=403, detail="Invalid room password")

    new_member = RoomMember(room_id=room_id, user_id=user.id)
    db.add(new_member)
    db.commit()
    
    return {"message": f"Joined room {room.name}"}