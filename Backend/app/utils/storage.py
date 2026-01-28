import os
from fastapi import UploadFile
from app.core.config import settings
from uuid import uuid4

os.makedirs(settings.upload_dir, exist_ok=True)

async def save_upload_file(upload_file: UploadFile) -> str:
    ext = upload_file.filename.split(".")[-1]
    filename = f"{uuid4().hex}.{ext}"
    path = os.path.join(settings.upload_dir, filename)
    with open(path, "wb") as buffer:
        content = await upload_file.read()
        buffer.write(content)
    return filename
