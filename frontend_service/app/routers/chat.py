from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, HTTPException
import httpx
import websockets
from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["Chat"])

# ============================
# HISTORIAL DE MENSAJES (PROXY HTTP)
# ============================
@router.get("/messages/{other_user_id}")
async def get_chat_history_proxy(request: Request, other_user_id: str):
    token = request.cookies.get("access_token")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    async with httpx.AsyncClient() as client:
        try:
            # Backend: /chat/messages/{other_user_id}
            url = f"{settings.BACKEND_URL}/chat/messages/{other_user_id}"
            resp = await client.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                return resp.json()
            else:
                return []
        except Exception as e:
            print(f"Error fetching chat messages: {e}")
            return []


# ============================
# WEBSOCKET PROXY
# ============================
@router.websocket("/ws/{other_user_id}")
async def websocket_proxy(websocket: WebSocket, other_user_id: str):
    await websocket.accept()
    
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=4003) # Forbidden
        return

    # Construir URL del backend pero cambiando http/https por ws/wss
    backend_ws_url = settings.BACKEND_URL.replace("http://", "ws://").replace("https://", "wss://")
    backend_ws_url = f"{backend_ws_url}/chat/ws/{other_user_id}?token={token}"

    try:
        async with websockets.connect(backend_ws_url) as backend_ws:
            # Loop bidireccional
            async def forward_to_backend():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await backend_ws.send(data)
                except Exception:
                    pass

            async def forward_to_frontend():
                try:
                    while True:
                        data = await backend_ws.recv()
                        await websocket.send_text(data)
                except Exception:
                    pass
            
            import asyncio
            # Correr ambas tareas en paralelo hasta que alguna falle/cierre
            done, pending = await asyncio.wait(
                [forward_to_backend(), forward_to_frontend()],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in pending:
                task.cancel()
                
    except Exception as e:
        print(f"WebSocket Proxy Error: {e}")
        try:
            await websocket.close()
        except:
            pass
