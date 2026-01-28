
from fastapi import HTTPException, Cookie, Header, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import PyJWTError
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> str:
    # Esta función ahora valida el token LOCALMENTE, sin llamar a otro servicio.
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido: falta user_id")
        return user_id
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

