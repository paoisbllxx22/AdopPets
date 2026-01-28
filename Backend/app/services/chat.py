#services/chat.py
from datetime import datetime
from typing import List, Dict, Any
from app.db.init_db import db

async def build_room_id(user_a: str, user_b: str) -> str:
    # Siempre el mismo orden, para que el mismo par de usuarios tenga el mismo room_id
    return "_".join(sorted([user_a, user_b]))


async def save_message(sender_id: str, receiver_id: str, content: str) -> Dict[str, Any]:
    room_id = await build_room_id(sender_id, receiver_id)

    doc = {
        "room_id": room_id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "content": content,
        "timestamp": datetime.utcnow(),
    }

    result = await db.messages.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return doc


async def get_conversation(user_id: str, other_user_id: str) -> List[Dict[str, Any]]:
    room_id = await build_room_id(user_id, other_user_id)

    cursor = db.messages.find({"room_id": room_id}).sort("timestamp", 1)

    messages: List[Dict[str, Any]] = []
    async for m in cursor:
        messages.append(
            {
                "id": str(m["_id"]),
                "sender_id": m["sender_id"],
                "receiver_id": m["receiver_id"],
                "content": m["content"],
                "timestamp": m["timestamp"],
            }
        )
    return messages
