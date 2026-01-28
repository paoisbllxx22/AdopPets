#models/pet.py 
from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime

class Pet(Document):
    owner_id: str  # ObjectId as str, or use Link[User] with beanie
    name: str
    age: Optional[int]
    description: Optional[str]
    photos: list[str] = Field(default_factory=list)
    status: str = "available"  # available, adopted, pending
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "pets"
