
## Prerequisites
- Python 3.11+
- Node.js 20+
- MongoDB (local or Atlas free tier)

---

## 1. MongoDB

**macOS**
```bash
brew install mongodb-community
brew services start mongodb-community
```

**Ubuntu / Debian**
```bash
sudo apt install -y mongodb
sudo systemctl start mongodb
```

**Windows**
Download the installer from https://www.mongodb.com/try/download/community

**Or use MongoDB Atlas (free, no install)**
1. Sign up at https://cloud.mongodb.com
2. Create a free M0 cluster
3. Copy the connection string and set it as `MONGODB_URI` in `.env`

---

## 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` — minimum required:
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=finguard_db
ANTHROPIC_API_KEY=sk-ant-your-key-here
SECRET_KEY=any-random-32-char-string
```

---

## 3. Backend

```bash
cd backend
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### Seed database
```bash
python ../scripts/seed_db.py
```

### (Optional) Train ML models
```bash
python ../scripts/train_models.py
# Takes ~2-3 minutes; models saved to backend/ml_models/
# If skipped, the system uses heuristic fallback scoring
```

### Start the API server
```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

## 4. Frontend

Open a new terminal:

```bash
cd frontend
npm install
```

Create `.env.local`:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ANTHROPIC_API_KEY=sk-ant-your-key-here
```

```bash
npm run dev
```

Dashboard at: http://localhost:5173

---

## 5. Both running?

| Service    | URL                              |
|------------|----------------------------------|
| Dashboard  | http://localhost:5173            |
| API docs   | http://localhost:8000/docs       |
| WebSocket  | ws://localhost:8000/ws/transactions |

---

## Redis (optional)

Redis is used for alert pub/sub caching. Not required for core functionality in dev.

**macOS:** `brew install redis && brew services start redis`  
**Ubuntu:** `sudo apt install redis-server && sudo systemctl start redis`  
**Windows:** https://github.com/microsoftarchive/redis/releases

If you skip Redis, comment out Redis lines in `backend/app/core/events.py`.
