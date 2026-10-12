-- TokenAPI Scan 标准化数据库 v1
-- 创建时间：2026-06-19
-- 设计原则：DB 是新增层，不替换原 JSON；所有 ID 用 provider_id 统一
-- 启用 WAL 提升并发读写
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ==========================================
-- 1. 站点档案
-- ==========================================
CREATE TABLE IF NOT EXISTS provider (
  provider_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  endpoint TEXT,
  homepage TEXT,
  category TEXT,
  region TEXT,
  is_official_baseline INTEGER DEFAULT 0,
  network_status TEXT DEFAULT 'unknown',
  service_status TEXT DEFAULT 'active',
  schema_version INTEGER DEFAULT 1,
  added_at TEXT,
  updated_at TEXT,
  raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_provider_status ON provider(service_status);
CREATE INDEX IF NOT EXISTS idx_provider_region ON provider(region);
CREATE INDEX IF NOT EXISTS idx_provider_category ON provider(category);

-- ==========================================
-- 2. 模型规范
-- ==========================================
CREATE TABLE IF NOT EXISTS model_canonical (
  canonical_id TEXT PRIMARY KEY,
  family TEXT NOT NULL,
  variant TEXT,
  vendor TEXT,
  is_thinking INTEGER DEFAULT 0,
  is_vision INTEGER DEFAULT 0,
  is_audio INTEGER DEFAULT 0,
  release_date TEXT,
  is_active INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_model_family ON model_canonical(family);
CREATE INDEX IF NOT EXISTS idx_model_vendor ON model_canonical(vendor);

CREATE TABLE IF NOT EXISTS model_alias (
  alias TEXT PRIMARY KEY,
  canonical_id TEXT REFERENCES model_canonical(canonical_id),
  source TEXT
);

CREATE INDEX IF NOT EXISTS idx_alias_canonical ON model_alias(canonical_id);

-- ==========================================
-- 3. 价格
-- ==========================================
CREATE TABLE IF NOT EXISTS price (
  provider_id TEXT REFERENCES provider(provider_id),
  canonical_id TEXT,
  raw_model_id TEXT,
  input_price_usd_per_1m REAL,
  output_price_usd_per_1m REAL,
  cached_price_usd_per_1m REAL,
  audio_input_price_usd_per_1m REAL,
  audio_output_price_usd_per_1m REAL,
  currency TEXT DEFAULT 'USD',
  source TEXT,
  fetched_at TEXT,
  PRIMARY KEY (provider_id, canonical_id, raw_model_id)
);

CREATE INDEX IF NOT EXISTS idx_price_canonical ON price(canonical_id);
CREATE INDEX IF NOT EXISTS idx_price_provider ON price(provider_id);
CREATE INDEX IF NOT EXISTS idx_price_fetched ON price(fetched_at);

-- ==========================================
-- 4. 检测记录
-- ==========================================
CREATE TABLE IF NOT EXISTS detection (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider_id TEXT REFERENCES provider(provider_id),
  level TEXT NOT NULL,
  protocol TEXT,
  brand TEXT,
  model_id TEXT,
  success INTEGER NOT NULL,
  duration_ms INTEGER,
  error_kind TEXT,
  error_msg TEXT,
  http_status INTEGER,
  source TEXT,
  detected_at TEXT NOT NULL,
  via_proxy INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_detection_provider_time ON detection(provider_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_detection_level ON detection(level);
CREATE INDEX IF NOT EXISTS idx_detection_brand ON detection(brand);
CREATE INDEX IF NOT EXISTS idx_detection_success ON detection(success);

-- ==========================================
-- 5. 健康快照
-- ==========================================
CREATE TABLE IF NOT EXISTS health_snapshot (
  snapshot_date TEXT PRIMARY KEY,
  total_providers INTEGER,
  active_count INTEGER,
  pass_count INTEGER,
  pass_rate REAL,
  avg_duration_ms INTEGER,
  raw_json TEXT
);

-- ==========================================
-- 6. 站点支持的模型
-- ==========================================
CREATE TABLE IF NOT EXISTS provider_model_support (
  provider_id TEXT REFERENCES provider(provider_id),
  canonical_id TEXT REFERENCES model_canonical(canonical_id),
  raw_model_id TEXT,
  source TEXT,
  probed_at TEXT,
  is_active INTEGER DEFAULT 1,
  PRIMARY KEY (provider_id, canonical_id)
);

CREATE INDEX IF NOT EXISTS idx_pms_canonical ON provider_model_support(canonical_id);

-- ==========================================
-- 7. 通知
-- ==========================================
CREATE TABLE IF NOT EXISTS notification (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT,
  payload TEXT,
  status TEXT DEFAULT 'pending',
  created_at TEXT,
  sent_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_notif_status ON notification(status);

-- ==========================================
-- 8. 排行榜快照
-- ==========================================
CREATE TABLE IF NOT EXISTS ranking_snapshot (
  snapshot_id TEXT PRIMARY KEY,
  generated_at TEXT,
  scoring_method TEXT,
  top_n_count INTEGER,
  raw_json TEXT
);

-- ==========================================
-- 9. SEO 报告索引
-- ==========================================
CREATE TABLE IF NOT EXISTS seo_report (
  report_date TEXT PRIMARY KEY,
  kind TEXT,
  file_path TEXT,
  summary TEXT
);

-- ==========================================
-- 10. ETL 运行日志
-- ==========================================
CREATE TABLE IF NOT EXISTS normalize_run (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ran_at TEXT NOT NULL,
  source_file TEXT,
  table_name TEXT,
  rows_in INTEGER,
  rows_out INTEGER,
  rows_skipped INTEGER,
  errors TEXT
);

-- ==========================================
-- View: 现用聚合（替代前端从 JSON 多次拉）
-- ==========================================
CREATE VIEW IF NOT EXISTS v_provider_health_7d AS
SELECT
  p.provider_id,
  p.name,
  p.category,
  p.region,
  p.service_status,
  p.network_status,
  COUNT(d.id) AS total_detections,
  SUM(d.success) AS pass_count,
  ROUND(SUM(d.success) * 100.0 / COUNT(d.id), 1) AS pass_rate,
  AVG(d.duration_ms) AS avg_duration_ms,
  MIN(d.duration_ms) AS min_duration_ms,
  MAX(d.duration_ms) AS max_duration_ms
FROM provider p
LEFT JOIN detection d ON p.provider_id = d.provider_id
  AND d.detected_at >= datetime('now', '-7 days')
GROUP BY p.provider_id;

CREATE VIEW IF NOT EXISTS v_price_canonical AS
SELECT
  p.canonical_id,
  m.family,
  m.vendor,
  COUNT(DISTINCT p.provider_id) AS provider_count,
  MIN(p.input_price_usd_per_1m) AS min_input,
  MAX(p.input_price_usd_per_1m) AS max_input,
  MIN(p.output_price_usd_per_1m) AS min_output,
  MAX(p.output_price_usd_per_1m) AS max_output,
  AVG(p.input_price_usd_per_1m) AS avg_input,
  AVG(p.output_price_usd_per_1m) AS avg_output
FROM price p
LEFT JOIN model_canonical m ON p.canonical_id = m.canonical_id
WHERE p.input_price_usd_per_1m IS NOT NULL
GROUP BY p.canonical_id;
