#schemas/post.py
from pydantic import BaseModel, HttpUrl
from typing import Optional

class PostCreate(BaseModel):
    title: str        # nombre de la mascota
    description: str  # descripción general
    details: Optional[str] = None
    image_url: Optional[str] = None   # ruta de imagen subida
    user_id: str      # ID del usuario dueño

class PostUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    details: Optional[str]
    image_url: Optional[str]

class PostResponse(BaseModel):
    id: str
    title: str
    description: str
    details: Optional[str]
    image_url: Optional[str]
    user_id: str
