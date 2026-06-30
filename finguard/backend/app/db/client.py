"""
Async MongoDB client — Motor + Beanie ODM initialisation.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from loguru import logger

from app.core.config import settings
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.alert import Alert

_client: AsyncIOMotorClient | None = None


async def init_db():
    global _client
    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = _client[settings.MONGODB_DB_NAME]
    await init_beanie(
        database=db,
        document_models=[Transaction, Account, Alert],
    )
    logger.info(f"Beanie ODM initialised on '{settings.MONGODB_DB_NAME}'")


async def close_db():
    global _client
    if _client:
        _client.close()
        _client = None


def get_db():
    """Return raw Motor database (for aggregation pipelines)."""
    if _client is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _client[settings.MONGODB_DB_NAME]
