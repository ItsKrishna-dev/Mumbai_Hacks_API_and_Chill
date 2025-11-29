from motor.motor_asyncio import AsyncIOMotorClient
from .settings import settings

# MongoDB client initialized once per process
client = AsyncIOMotorClient(settings.MONGODB_URL)

# Application database
db = client["SwasthAI"]


async def get_database():
    """Return the default application database."""
    return db


async def close_database():
    """Close the MongoDB client connection."""
    client.close()

