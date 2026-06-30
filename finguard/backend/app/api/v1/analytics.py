"""Analytics & Dashboard Stats API"""
from fastapi import APIRouter
from app.db.client import get_db
from app.schemas.schemas import DashboardStats
from app.models.alert import Alert

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats():
    db = get_db()

    pipeline = [
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "flagged": {"$sum": {"$cond": ["$is_flagged", 1, 0]}},
            "high_risk": {"$sum": {"$cond": [{"$eq": ["$risk_level", "high"]}, 1, 0]}},
            "loops": {"$sum": {"$cond": ["$is_loop", 1, 0]}},
            "volume": {"$sum": "$amount"},
            "avg_risk": {"$avg": "$risk_score"},
        }}
    ]
    result = await db["transactions"].aggregate(pipeline).to_list(1)
    unresolved_alerts = await Alert.find({"resolved": False}).count()

    if not result:
        return DashboardStats(
            total_transactions=0, flagged_count=0, high_risk_count=0,
            suspicious_chains=0, total_volume_usd=0.0, avg_risk_score=0.0,
            alerts_unresolved=unresolved_alerts,
        )
    r = result[0]
    return DashboardStats(
        total_transactions=r["total"],
        flagged_count=r["flagged"],
        high_risk_count=r["high_risk"],
        suspicious_chains=r["loops"],
        total_volume_usd=round(r["volume"], 2),
        avg_risk_score=round(r["avg_risk"], 4),
        alerts_unresolved=unresolved_alerts,
    )
