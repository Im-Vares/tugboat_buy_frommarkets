-- Схема aportals_project
BEGIN;
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  telegram_id BIGINT NOT NULL UNIQUE,
  username TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS filters (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  collection TEXT NOT NULL,
  model TEXT,
  backdrop TEXT,
  max_price NUMERIC(18,6) NOT NULL CHECK (max_price > 0),
  quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_filters_active ON filters(active);
CREATE INDEX IF NOT EXISTS idx_filters_user   ON filters(user_id);
CREATE INDEX IF NOT EXISTS idx_filters_combo  ON filters(collection, model, backdrop);
CREATE TABLE IF NOT EXISTS pending_gifts (
  gift_id TEXT PRIMARY KEY,
  tg_id TEXT,
  filter_id BIGINT NOT NULL REFERENCES filters(id) ON DELETE CASCADE,
  price NUMERIC(18,6) NOT NULL,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pending_status ON pending_gifts(status);
CREATE TABLE IF NOT EXISTS logs (
  id BIGSERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  action TEXT NOT NULL,
  gift_id TEXT,
  filter_id BIGINT,
  user_id BIGINT,
  price NUMERIC(18,6),
  result TEXT,
  details TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_logs_created ON logs(created_at DESC);
COMMIT;
