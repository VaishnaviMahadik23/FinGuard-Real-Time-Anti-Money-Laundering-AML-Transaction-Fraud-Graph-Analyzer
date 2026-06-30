// scripts/mongo-init.js
// Runs once when MongoDB container is first created.
db = db.getSiblingDB('finguard_db');

db.createCollection('accounts');
db.createCollection('transactions');
db.createCollection('alerts');

db.transactions.createIndex({ timestamp: -1 });
db.transactions.createIndex({ risk_score: -1 });
db.transactions.createIndex({ from_account_id: 1, timestamp: -1 });
db.transactions.createIndex({ is_flagged: 1 });

db.alerts.createIndex({ created_at: -1 });
db.alerts.createIndex({ severity: 1, resolved: 1 });

print('FinGuard DB initialised ✓');
