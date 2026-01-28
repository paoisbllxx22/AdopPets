#db/init_db
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Crea el cliente de Mongo
client = AsyncIOMotorClient(settings.MONGO_URL)

# Como en tu URI ya pusiste el nombre de la base (adoppets_db),
# esto devuelve directamente esa base
db = client.get_default_database()
