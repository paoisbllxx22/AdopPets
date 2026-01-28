#routers/chat.py
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException,
    Query,
)
from jose import jwt, JWTError
from app.core.config import settings
from app.core.auth import get_current_user
from app.schemas.chat import ChatMessageResponse
from app.services.chat import save_message, get_conversation, build_room_id

router = APIRouter(prefix="/chat", tags=["Chat"])


# ------------------------------
# 1) HISTORIAL DE MENSAJES (HTTP)
# ------------------------------
@router.get("/messages/{other_user_id}", response_model=list[ChatMessageResponse])
async def get_chat_messages(
    other_user_id: str,
    user_id: str = Depends(get_current_user),
):
    messages = await get_conversation(user_id, other_user_id)
    return messages


# ------------------------------
# 2) MANEJADOR DE CONEXIONES WS
# ------------------------------
class ConnectionManager:
    def __init__(self):
        # room_id -> lista de websockets
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(room_id, []).append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: str, message: dict):
        for connection in self.active_connections.get(room_id, []):
            await connection.send_json(message)


manager = ConnectionManager()


# ------------------------------
# 3) UTILIDAD PARA DECODIFICAR TOKEN
# ------------------------------
def decode_token(token: str) -> str:
    """Decodifica el JWT y devuelve el user_id (sub)."""
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    user_id: str = payload.get("sub")
    if not user_id:
        raise JWTError("No sub in token")
    return user_id


# ------------------------------
# 4) WEBSOCKET DE CHAT
# ------------------------------
@router.websocket("/ws/{other_user_id}")
async def websocket_chat(
    websocket: WebSocket,
    other_user_id: str,
    token: str | None = Query(default=None),  # opcional: ?token=
):
    # 1) Intentar leer token de query; si no, de cookie
    if not token:
        token = websocket.cookies.get("access_token")

    if not token:
        await websocket.close(code=1008)  # Policy Violation
        return

    # 2) Decodificar user_id
    try:
        user_id = decode_token(token)
    except JWTError:
        await websocket.close(code=1008)
        return

    # 3) Construir room_id
    room_id = await build_room_id(user_id, other_user_id)

    # 4) Conectar
    await manager.connect(room_id, websocket)

    try:
        while True:
            text = await websocket.receive_text()

            # Guardar en BD
            doc = await save_message(user_id, other_user_id, text)

            # Broadcast a todos en el room
            await manager.broadcast(
                room_id,
                {
                    "id": doc["id"],
                    "sender_id": doc["sender_id"],
                    "receiver_id": doc["receiver_id"],
                    "content": doc["content"],
                    "timestamp": doc["timestamp"].isoformat(),
                },
            )

    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
    except Exception:
        manager.disconnect(room_id, websocket)
        await websocket.close()

