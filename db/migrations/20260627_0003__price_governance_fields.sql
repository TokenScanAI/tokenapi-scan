-- 治理字段迁移 M1 · price 加五件套(method/verified_at/evidence_ref) + 生命周期 + updated_at
-- Pillar 3 实施 · 2026-06-27 (M0 = model_canonical 0002 模板)
-- 现状:price 已有 source + fetched_at, 缺 method/verified_at/evidence_ref
-- 行数:3807 行 → 全量回填为 legacy_pre_governance / status='legacy_unverified'

-- 五件套补齐(已有 source/fetched_at)
ALTER TABLE price ADD COLUMN method        TEXT;
ALTER TABLE price ADD COLUMN verified_at   TEXT;
ALTER TABLE price ADD COLUMN evidence_ref  TEXT;

-- 生命周期(Pillar 6 状态机)
ALTER TABLE price ADD COLUMN status        TEXT NOT NULL DEFAULT 'raw';
ALTER TABLE price ADD COLUMN status_since  TEXT;
ALTER TABLE price ADD COLUMN status_reason TEXT;

-- 扩展信号
ALTER TABLE price ADD COLUMN updated_at    TEXT;

-- 索引
CREATE INDEX IF NOT EXISTS idx_price_status     ON price(status);
CREATE INDEX IF NOT EXISTS idx_price_verified   ON price(verified_at);
CREATE INDEX IF NOT EXISTS idx_price_updated    ON price(updated_at);

-- 历史 3807 行回填(无证据,标 legacy_unverified)
UPDATE price
SET method         = COALESCE(method, 'scrape_legacy'),
    verified_at    = COALESCE(verified_at, NULL),
    evidence_ref   = COALESCE(evidence_ref, NULL),
    status         = CASE WHEN status='raw' THEN 'legacy_unverified' ELSE status END,
    status_since   = COALESCE(status_since, '2026-06-27T00:00:00Z'),
    status_reason  = COALESCE(status_reason, 'pre-governance bulk import; needs evidence backfill'),
    updated_at     = COALESCE(updated_at, '2026-06-27T00:00:00Z')
WHERE method IS NULL;
