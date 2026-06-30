"""
FinGuard AML — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from loguru import logger

from app.core.config import settings
from app.core.events import startup_handler, shutdown_handler
from app.api.v1.router import api_router
from app.api.websocket import ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: DB connections, ML model loading."""
    await startup_handler()
    logger.info("FinGuard AML system online ✓")
    yield
    await shutdown_handler()
    logger.info("FinGuard AML system shutdown complete")


app = FastAPI(
    title="FinGuard AML API",
    description="Real-time Anti-Money Laundering & Transaction Fraud Graph Analyzer",
    version="2.4.1",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(ws_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "finguard-aml", "version": "2.4.1"}
