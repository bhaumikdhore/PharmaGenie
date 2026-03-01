ALTER TABLE medicines
ADD COLUMN IF NOT EXISTS threshold INTEGER DEFAULT 10;

CREATE TABLE IF NOT EXISTS stock_alerts (
    id SERIAL PRIMARY KEY,
    medicine_id INTEGER REFERENCES medicines(id),
    alert_type VARCHAR(50) NOT NULL,
    current_stock INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_stock_alerts_medicine_alert_resolved
ON stock_alerts (medicine_id, alert_type, resolved);

CREATE INDEX IF NOT EXISTS idx_stock_alerts_created_at
ON stock_alerts (created_at DESC);

