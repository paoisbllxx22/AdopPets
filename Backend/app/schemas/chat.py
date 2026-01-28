#schemas/chat.py
from pydantic import BaseModel
from datetime import datetime

class ChatMessageResponse(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    content: str
    timestamp: datetime
