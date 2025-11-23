# backend/app/routers/chat.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import Message, User, RoomMember
from app.services.broker import publish_message
from app.core.security import settings
from jose import jwt, JWTError

router = APIRouter(tags=["Chat"])

# Función auxiliar para validar token en WebSocket (los WS no usan headers HTTP estandar)
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
            # Iteramos sobre una copia para evitar errores si alguien se desconecta durante el loop
            for connection in self.active_connections[room_id][:]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Manejo básico de error de socket muerto
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
            "created_at": msg.created_at.isoformat()
        })
    return history

# --- WebSocket ---

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    room_id: int, 
    token: str = Query(...), # Token viene en la URL ?token=...
    db: Session = Depends(get_db)
):
    # 1. Validar Usuario
    user = await get_user_from_token(token, db)
    if not user:
        await websocket.close(code=4003) # Forbidden
        return

    # 2. Validar Membresía (Seguridad)
    member = db.query(RoomMember).filter_by(room_id=room_id, user_id=user.id).first()
    if not member:
        await websocket.close(code=4003, reason="Not a member of this room")
        return

    await manager.connect(websocket, room_id)
    
    # Notificar entrada (Opcional según requisitos)
    join_msg = {"type": "system", "content": f"{user.username} joined", "user": "System"}
    await manager.broadcast(join_msg, room_id)

    try:
        while True:
            data = await websocket.receive_text()
            
            # Construir payload completo
            message_payload = {
                "room_id": room_id,
                "user_id": user.id,      # Importante para persistencia
                "username": user.username, # Importante para UI inmediata
                "content": data,
                "created_at": str(datetime.now()) # Timestamp temporal para UI
            }
            
            # 1. Enviar a clientes conectados (Latencia < 850ms)
            await manager.broadcast(message_payload, room_id)
            
            # 2. Enviar a RabbitMQ (Durabilidad)
            publish_message(message_payload)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast({"type": "system", "content": f"{user.username} left"}, room_id)