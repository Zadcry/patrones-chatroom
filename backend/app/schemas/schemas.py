# backend/app/schemas/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- Auth & Users ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Rooms ---
class RoomCreate(BaseModel):
    name: str
    is_private: bool = False
    password: Optional[str] = None

class RoomJoin(BaseModel):
    password: Optional[str] = None

class RoomResponse(BaseModel):
    id: int
    name: str
    is_private: bool
    created_by: int
    class Config:
        orm_mode = True

# --- Messages ---
class MessageResponse(BaseModel):
    id: int
    content: str
    user_id: Optional[int]
    username: str
    created_at: datetime
    class Config:
        orm_mode = True