#core/auth.py
from fastapi import HTTPException, Cookie, Header
import httpx
from app.core.config import settings

# Cliente reutilizable (mejor performance)
_client = httpx.AsyncClient(timeout=10)

async def get_current_user(
    access_token: str | None = Cookie(None),
    authorization: str | None = Header(None),
) -> str:
    # 1) Obtener token desde cookie o Authorization: Bearer
    token = access_token
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(status_code=401, detail="Token no encontrado")

    # 2) URL segura (por si AUTH_SERVICE_URL termina con /)
    base = settings.AUTH_SERVICE_URL.rstrip("/")
    url = f"{base}/auth/me"

    # 3) Validar token con Auth Service
    try:
        resp = await _client.get(
            url,
            headers={"Authorization": f"Bearer {token}"}
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Auth service no disponible")

    if resp.status_code != 200:
        # (debug útil si algo falla)
        # print("AUTH /me:", resp.status_code, resp.text)
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    data = resp.json()
    user_id = data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    return user_id
