#services/users.py
from app.db.init_db import db
from app.core.security import hash_password, verify_password, create_access_token
from bson import ObjectId


# -----------------------------------------
# Crear usuario
# -----------------------------------------
async def create_user(data, profile_image: str | None = None):
    existing = await db.users.find_one({"email": data.email})
    if existing:
        return None

    hashed = hash_password(data.password)

    new_user = {
        "name": data.name,
        "email": data.email,
        "hashed_password": hashed,
        "profile_image": profile_image
    }

    result = await db.users.insert_one(new_user)
    new_user["id"] = str(result.inserted_id)

    return new_user



# -----------------------------------------
# Login
# -----------------------------------------
async def login_user(data):
    user = await db.users.find_one({"email": data.email})
    if not user:
        return None

    if not verify_password(data.password, user["hashed_password"]):
        return None

    token = create_access_token({"sub": str(user["_id"])})

    return {
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "profile_image": user.get("profile_image")
        }
    }


# -----------------------------------------
# Obtener usuario por ID (para /users/me)
# -----------------------------------------
async def get_user_by_id(user_id: str):
    user = await db.users.find_one({"_id": ObjectId(user_id)})

    if not user:
        return None

    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "profile_image": user.get("profile_image")
    }


# -----------------------------------------
# Guardar imagen de perfil
# -----------------------------------------
async def update_profile_image(user_id: str, image_url: str):
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"profile_image": image_url}}
    )
    return True
