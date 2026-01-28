#services/password_reset.py
import random
from datetime import datetime, timedelta
from app.db.init_db import db

def generate_code():
    return str(random.randint(100000, 999999))

async def create_reset_code(email: str):
    code = generate_code()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    await db.password_resets.insert_one({
        "email": email,
        "code": code,
        "expires_at": expires_at,
        "used": False
    })

    return code
