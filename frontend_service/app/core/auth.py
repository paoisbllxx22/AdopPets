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
        # En frontend, si no hay token, redirigimos a login o lanzamos 401
        # Para simplificar dependencias de redirección, lanzamos 401 y el router maneja
        raise HTTPException(status_code=401, detail="Token no encontrado")

    # 2) URL segura
    base = settings.AUTH_SERVICE_URL.rstrip("/")
    url = f"{base}/auth/me"

    # 3) Validar token con Auth Service
    try:
        resp = await _client.get(
            url,
            headers={"Authorization": f"Bearer {token}"}
        )
    except Exception as e:
        print(f"Error conectando con Auth Service: {e}")
        raise HTTPException(status_code=503, detail="Auth service no disponible")

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    data = resp.json()
    user_id = data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    return user_id
