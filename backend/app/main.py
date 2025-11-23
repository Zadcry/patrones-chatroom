# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.routers import chat, auth, rooms

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Realtime Chat App")

# --- CORRECCIÓN CORS ---
origins = [
    "http://localhost:3000",      # Frontend en Docker (puerto mapeado)
    "http://localhost:5173",      # Frontend en desarrollo local (Vite default)
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # <--- CAMBIO: Lista explícita en lugar de ["*"]
    allow_credentials=True,       # Necesario para enviar Headers de Auth
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------

app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"status": "System Operational", "service": "Chat Backend"}