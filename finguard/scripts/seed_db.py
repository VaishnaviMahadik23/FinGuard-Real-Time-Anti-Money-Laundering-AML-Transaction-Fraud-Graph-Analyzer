"""
scripts/seed_db.py
Seeds MongoDB with 12 realistic accounts and 500 synthetic transactions,
including injected AML patterns (smurfing, layering, loops).
"""
import asyncio
import random
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorClient

import sys, os
# Always resolve to backend/ regardless of where script is called from
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings

ACCOUNTS = [
    {"account_id": "ACC-001", "name": "GreenLeaf Trading LLC", "country": "US", "entity_type": "corporate"},
    {"account_id": "ACC-002", "name": "Dmitri Volkov",         "country": "RU", "entity_type": "individual"},
    {"account_id": "ACC-003", "name": "Nexus Holdings",         "country": "PAN","entity_type": "shell"},
    {"account_id": "ACC-004", "name": "Sarah Chen",             "country": "SG", "entity_type": "individual"},
    {"account_id": "ACC-005", "name": "Atlantic Ventures",      "country": "UK", "entity_type": "corporate"},
    {"account_id": "ACC-006", "name": "Ali Hassan",             "country": "AE", "entity_type": "individual"},
    {"account_id": "ACC-007", "name": "Phantom LLC",            "country": "BVI","entity_type": "shell"},
    {"account_id": "ACC-008", "name": "Nordic Capital",         "country": "NO", "entity_type": "corporate"},
    {"account_id": "ACC-009", "name": "Carlos Mendez",          "country": "MX", "entity_type": "individual"},
    {"account_id": "ACC-010", "name": "Apex Global",            "country": "HK", "entity_type": "corporate"},
    {"account_id": "ACC-011", "name": "Sunrise Fund",           "country": "KY", "entity_type": "shell"},
    {"account_id": "ACC-012", "name": "Elena Petrov",           "country": "UA", "entity_type": "individual"},
]

TX_TYPES = ["WIRE", "ACH", "CRYPTO", "SWIFT", "INTERNAL", "CASH"]


def random_amount(pattern=None):
    if pattern == "smurfing":
        return round(random.uniform(8500, 9999), 2)
    if pattern == "layering":
        return round(random.uniform(50000, 500000), 2)
    return round(random.uniform(100, 150000), 2)


async def seed():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]

    print("Clearing existing data...")
    await db["accounts"].drop()
    await db["transactions"].drop()

    print(f"Inserting {len(ACCOUNTS)} accounts...")
    await db["accounts"].insert_many(ACCOUNTS)

    print("Generating 500 transactions...")
    txs = []
    now = datetime.utcnow()

    for i in range(500):
        src = random.choice(ACCOUNTS)
        dst = random.choice([a for a in ACCOUNTS if a["account_id"] != src["account_id"]])

        roll = random.random()
        pattern = None
        if roll < 0.05:
            pattern = "smurfing"
        elif roll < 0.10:
            pattern = "layering"
            dst = next((a for a in ACCOUNTS if a["entity_type"] == "shell"), dst)
        elif roll < 0.15:
            pattern = "loop"

        amount = random_amount(pattern)
        ts = now - timedelta(hours=random.uniform(0, 48))

        # Simple risk heuristic for seed data
        risk = 0.1
        if src["country"] in ("BVI", "PAN", "KY", "RU"):
            risk += 0.3
        if src["entity_type"] == "shell" or dst["entity_type"] == "shell":
            risk += 0.3
        if amount > 100000:
            risk += 0.2
        if pattern:
            risk += 0.2
        risk = min(risk + random.uniform(-0.05, 0.1), 0.99)

        txs.append({
            "tx_id": f"TX{str(i+1).zfill(6)}",
            "from_account_id": src["account_id"],
            "to_account_id": dst["account_id"],
            "amount": amount,
            "currency": "USD",
            "tx_type": random.choice(TX_TYPES),
            "timestamp": ts,
            "risk_score": round(risk, 4),
            "risk_level": "high" if risk > 0.65 else "medium" if risk > 0.35 else "low",
            "is_flagged": risk > 0.65 or pattern in ("loop",),
            "is_loop": pattern == "loop",
            "pattern": pattern,
            "isolation_forest_score": round(risk * 0.9, 4),
            "autoencoder_error": round(risk * 0.42, 4),
        })

    await db["transactions"].insert_many(txs)
    flagged = sum(1 for t in txs if t["is_flagged"])
    print(f"✓ Seeded {len(txs)} transactions ({flagged} flagged)")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
