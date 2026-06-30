"""
API v1 route aggregator.
"""
from fastapi import APIRouter

from app.api.v1 import transactions, accounts, alerts, graph, analytics

api_router = APIRouter()

api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(accounts.router,     prefix="/accounts",     tags=["Accounts"])
api_router.include_router(alerts.router,       prefix="/alerts",       tags=["Alerts"])
api_router.include_router(graph.router,        prefix="/graph",        tags=["Graph"])
api_router.include_router(analytics.router,    prefix="/analytics",    tags=["Analytics"])
