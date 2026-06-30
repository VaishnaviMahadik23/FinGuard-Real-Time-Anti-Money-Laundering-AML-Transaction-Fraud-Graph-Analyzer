"""
Application startup / shutdown handlers.
Initializes DB connections and loads ML models into memory.
"""
from loguru import logger

from app.db.client import init_db, close_db
from app.ml.model_registry import ModelRegistry


async def startup_handler():
    logger.info("Connecting to MongoDB...")
    await init_db()
    logger.info("MongoDB connected ✓")

    logger.info("Loading ML models...")
    await ModelRegistry.load()
    logger.info(f"Models loaded ✓  (IF + AE ensemble ready)")


async def shutdown_handler():
    logger.info("Closing MongoDB connection...")
    await close_db()
