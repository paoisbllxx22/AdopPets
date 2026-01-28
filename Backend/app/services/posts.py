# app/services/posts.py

from app.db.init_db import db
from bson import ObjectId
import requests


# ---------------------------------------
# Helper para convertir ObjectId -> string
# ---------------------------------------
def fix_post(post):
    """
    Convierte ObjectId a string y elimina el campo '_id'
    """
    if not post:
        return None

    post["id"] = str(post["_id"])
    del post["_id"]

    # Si user_id también es ObjectId, convertirlo
    if isinstance(post.get("user_id"), ObjectId):
        post["user_id"] = str(post["user_id"])

    return post


# ---------------------------------------
# Crear post
# ---------------------------------------
async def create_post(data):
    result = await db.posts.insert_one(data)
    data["id"] = str(result.inserted_id)

    # Si guardaste user_id como ObjectId en Mongo, arréglalo
    if isinstance(data.get("user_id"), ObjectId):
        data["user_id"] = str(data["user_id"])

    return data


# ---------------------------------------
# Obtener post por ID
# ---------------------------------------
async def get_post_by_id(post_id: str):
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        return None

    post["id"] = str(post["_id"])
    del post["_id"]              # ✅ obligatorio

    return post



# ---------------------------------------
# Feed general
# ---------------------------------------
async def get_posts_feed():
    cursor = db.posts.find().sort("_id", -1)  # más recientes primero
    posts = []

    async for post in cursor:
        user = None

        if post.get("user_id"):
            user = await db.users.find_one(
                {"_id": ObjectId(post["user_id"])}
            )

        posts.append({
            "id": str(post["_id"]),
            "title": post.get("title"),
            "description": post.get("description"),
            "details": post.get("details"),
            "image_url": post.get("image_url"),
            "user_id": post.get("user_id"),

            # 👇 INFO DEL USUARIO
            "user_name": user.get("name") if user else "Usuario",
            "user_profile_image": user.get("profile_image") if user else None
        })

    return posts





# ---------------------------------------
# Posts de un usuario
# ---------------------------------------
async def get_user_posts(user_id: str):
    cursor = db.posts.find({})
    posts = []

    async for post in cursor:
        # ✅ cualquier forma que venga user_id
        if str(post.get("user_id")) == str(user_id):
            post = fix_post(post)
            posts.append(post)

    return posts




# ---------------------------------------
# Actualizar post
# ---------------------------------------
async def update_post(post_id: str, data, user_id: str):
    """
    data viene como diccionario (NO Pydantic)
    así que lo dejamos tal cual.
    """

    # Limpiar campos None
    update_data = {k: v for k, v in data.items() if v is not None}

    updated = await db.posts.update_one(
        {"_id": ObjectId(post_id), "user_id": user_id},
        {"$set": update_data}
    )

    return updated.modified_count > 0


# ---------------------------------------
# Eliminar post
# ---------------------------------------
async def delete_post(post_id: str, user_id: str):
    deleted = await db.posts.delete_one(
        {"_id": ObjectId(post_id), "user_id": user_id}
    )
    return deleted.deleted_count > 0
