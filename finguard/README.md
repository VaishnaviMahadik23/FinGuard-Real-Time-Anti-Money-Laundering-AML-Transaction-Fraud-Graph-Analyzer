# FinGuard — Real-Time AML & Transaction Fraud Graph Analyzer

![FinGuard](https://img.shields.io/badge/FinGuard-AML%20v2.4.1-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?style=flat-square)
![PyTorch](https://img.shields.io/badge/PyTorch-2.2-red?style=flat-square)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green?style=flat-square)

A high-throughput streaming AML system combining **Isolation Forest** + **Autoencoder Neural Networks** with real-time graph-based fraud path detection.

---

## Architecture

```
finguard/
├── backend/                  # FastAPI + asyncio backend
│   ├── app/
│   │   ├── api/              # REST & WebSocket routes
│   │   ├── core/             # Config, security, events
│   │   ├── ml/               # Isolation Forest + Autoencoder models
│   │   ├── db/               # MongoDB async client
│   │   ├── models/           # ODM document models
│   │   └── schemas/          # Pydantic request/response schemas
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Dark-mode compliance dashboard
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Dashboard, Graph, Transactions, AI
│   │   ├── hooks/            # WebSocket, data hooks
│   │   └── utils/            # Risk scoring, graph helpers
│   ├── package.json
│   └── index.html
├── scripts/                  # DB seed, model training scripts
├── tests/                    # pytest + vitest suites
├── docker-compose.yml
└── .env.example
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+

### 1. Clone & configure
```bash
git clone https://github.com/your-org/finguard.git
cd finguard
cp .env.example .env
# Edit .env with your MongoDB URI and secret keys
```

### 2. Start all services
```bash
docker-compose up --build
```

### 3. Seed the database & train models
```bash
docker-compose exec backend python scripts/seed_db.py
docker-compose exec backend python scripts/train_models.py
```

### 4. Access
| Service | URL |
|---------|-----|
| Dashboard | http://localhost:5173 |
| API Docs | http://localhost:8000/docs |
| WebSocket | ws://localhost:8000/ws/transactions |
| MongoDB | mongodb://localhost:27017 |

---

## AI Detection Models

### Isolation Forest
- Trained on 100k+ synthetic transactions
- Contamination factor: 0.08
- Features: amount z-score, velocity, jurisdiction risk, counterparty entropy

### Autoencoder Neural Network (PyTorch)
- 6-layer encoder/decoder: `128 → 64 → 32 → 16 → 32 → 64 → 128`
- Reconstruction error threshold: 0.42
- Trained with Adam optimizer, MSE loss

### Graph Loop Detection
- BFS-based circular path detection on account linkage graph
- MongoDB Atlas Graph Lookup for persistent chain tracing
- Identifies: smurfing, layering, round-tripping patterns

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/transactions/` | Submit transaction for screening |
| `GET` | `/api/v1/transactions/flagged` | Get all flagged transactions |
| `GET` | `/api/v1/graph/accounts` | Account linkage graph data |
| `GET` | `/api/v1/alerts/` | Live alert feed |
| `POST` | `/api/v1/accounts/{id}/freeze` | Freeze account |
| `WS` | `/ws/transactions` | Real-time transaction stream |

---

## Environment Variables

See `.env.example` for all required variables.

---

## License

MIT © 2024 FinGuard
