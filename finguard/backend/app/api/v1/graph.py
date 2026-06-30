"""
Graph endpoints — account linkage graph for the canvas visualiser.
"""
from fastapi import APIRouter
from app.schemas.schemas import GraphResponse, GraphNode, GraphEdge
from app.models.account import Account
from app.db.client import get_db

router = APIRouter()


@router.get("/", response_model=GraphResponse)
async def get_account_graph():
    """
    Build account linkage graph from transaction history.
    Returns nodes (accounts) and edges (transaction flows) for the D3/Canvas renderer.
    """
    db = get_db()

    # Aggregate edges from transactions
    pipeline = [
        {"$group": {
            "_id": {"from": "$from_account_id", "to": "$to_account_id"},
            "count": {"$sum": 1},
            "total_volume": {"$sum": "$amount"},
            "max_risk": {"$max": "$risk_score"},
            "has_loop": {"$max": {"$cond": ["$is_loop", 1, 0]}},
            "has_flagged": {"$max": {"$cond": ["$is_flagged", 1, 0]}},
        }},
        {"$limit": 500}
    ]
    raw_edges = await db["transactions"].aggregate(pipeline).to_list(500)

    # Collect unique account IDs
    account_ids = set()
    for e in raw_edges:
        account_ids.add(e["_id"]["from"])
        account_ids.add(e["_id"]["to"])

    # Fetch account docs
    accounts = await Account.find({"account_id": {"$in": list(account_ids)}}).to_list()
    acc_map = {a.account_id: a for a in accounts}

    # Risk score per account node (max across outgoing transactions)
    risk_pipe = [
        {"$match": {"from_account_id": {"$in": list(account_ids)}}},
        {"$group": {
            "_id": "$from_account_id",
            "max_risk": {"$max": "$risk_score"},
            "tx_count": {"$sum": 1},
            "flagged": {"$max": {"$cond": ["$is_flagged", 1, 0]}},
        }}
    ]
    risk_data = {r["_id"]: r for r in await db["transactions"].aggregate(risk_pipe).to_list(500)}

    nodes = []
    for acc_id in account_ids:
        acc = acc_map.get(acc_id)
        r = risk_data.get(acc_id, {})
        nodes.append(GraphNode(
            id=acc_id,
            label=acc.name if acc else acc_id,
            country=acc.country if acc else "??",
            entity_type=acc.entity_type if acc else "unknown",
            risk_score=r.get("max_risk", 0.0),
            tx_count=r.get("tx_count", 0),
            is_flagged=bool(r.get("flagged", 0)),
            is_frozen=acc.is_frozen if acc else False,
        ))

    edges = [
        GraphEdge(
            source=e["_id"]["from"],
            target=e["_id"]["to"],
            count=e["count"],
            total_volume=e["total_volume"],
            is_suspicious=e["max_risk"] > 0.5 or bool(e["has_flagged"]),
            is_loop=bool(e["has_loop"]),
        )
        for e in raw_edges
    ]

    return GraphResponse(nodes=nodes, edges=edges)
