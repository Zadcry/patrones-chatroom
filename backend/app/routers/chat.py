from datetime import datetime
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import Message, User, RoomMember 
from app.services.broker import publish_message
from app.core.security import settings
from jose import jwt, JWTError

router = APIRouter(tags=["Chat"])

async def get_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = db.query(User).filter(User.username == username).first()
        return user
    except JWTError:
        return None

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)

    async def broadcast(self, message: dict, room_id: int):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id][:]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

# --- Endpoints REST ---

@router.get("/rooms/{room_id}/messages")
def get_history(room_id: int, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    # Join con User para obtener el nombre del usuario
    results = db.query(Message, User.username)\
                .join(User, Message.user_id == User.id)\
                .filter(Message.room_id == room_id)\
                .order_by(Message.created_at.desc())\
                .offset(offset).limit(limit).all()
    
    # Formatear respuesta
    history = []
    for msg, uname in results:
        history.append({
            "id": msg.id,
            "content": msg.content,
            "user_id": msg.user_id,
            "username": uname,
            "created_at": msg.created_at.isoformat() if msg.created_at else str(datetime.now())
        })
    return history

# --- WebSocket ---

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    room_id: int, 
    token: str = Query(...), 
    db: Session = Depends(get_db)
):
    # 1. Validar Usuario
    user = await get_user_from_token(token, db)
    if not user:
        # Código 4003 no es estándar en todos los navegadores, usamos 1008 (Policy Violation) o cerramos simple
        await websocket.close(code=1008, reason="Invalid Token") 
        return

    # 2. Validar Membresía (Seguridad)
    # Si RoomMember no estaba importado, aquí explotaba el backend
    member = db.query(RoomMember).filter_by(room_id=room_id, user_id=user.id).first()
    if not member:
        await websocket.close(code=1008, reason="Not a member")
        return

    await manager.connect(websocket, room_id)
    
    # Notificar entrada
    # Usamos str(datetime.now()) para evitar problemas de serialización JSON
    join_msg = {
        "type": "system", 
        "content": f"{user.username} joined", 
        "username": "System",
        "created_at": str(datetime.now()) 
    }
    await manager.broadcast(join_msg, room_id)

    try:
        while True:
            data = await websocket.receive_text()
            
            message_payload = {
                "room_id": room_id,
                "user_id": user.id,
                "username": user.username,
                "content": data,
                "created_at": str(datetime.now()) # <--- Aquí explotaba si faltaba importar datetime
            }
            
            # 1. Enviar a clientes conectados
            await manager.broadcast(message_payload, room_id)
            
            # 2. Enviar a RabbitMQ (Durabilidad) en un hilo aparte para no bloquear
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, publish_message, message_payload)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        leave_msg = {
            "type": "system", 
            "content": f"{user.username} left", 
            "username": "System",
            "created_at": str(datetime.now())
        }
        await manager.broadcast(leave_msg, room_id)