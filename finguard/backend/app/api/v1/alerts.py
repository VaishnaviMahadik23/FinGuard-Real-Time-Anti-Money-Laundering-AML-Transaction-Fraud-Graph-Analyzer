"""Alerts API"""
from fastapi import APIRouter, Query
from app.models.alert import Alert
from app.schemas.schemas import AlertResponse

router = APIRouter()


@router.get("/", response_model=list[AlertResponse])
async def list_alerts(
    resolved: bool | None = None,
    severity: str | None = None,
    limit: int = Query(50, le=200),
):
    query = {}
    if resolved is not None:
        query["resolved"] = resolved
    if severity:
        query["severity"] = severity
    return await Alert.find(query).sort("-created_at").limit(limit).to_list()


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, resolved_by: str = "compliance_officer"):
    from datetime import datetime
    alert = await Alert.find_one({"alert_id": alert_id})
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(404, "Alert not found")
    alert.resolved = True
    alert.resolved_by = resolved_by
    alert.resolved_at = datetime.utcnow()
    await alert.save()
    return {"status": "resolved", "alert_id": alert_id}
