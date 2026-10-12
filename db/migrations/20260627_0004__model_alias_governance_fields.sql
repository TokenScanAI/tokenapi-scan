-- 治理字段迁移 M2 · model_alias 加五件套(method/fetched_at/evidence_ref) + 生命周期
-- Pillar 3 实施 · 2026-06-27
-- 现状:已有 source/verified_at/evidence(JSON-in-string,Layer 1 决策项 1 待拍)/confidence
-- 决策:evidence 列保留并行(决策项 1 拍板前不 DROP),新增 evidence_ref 规范列
-- 行数:1370 行 → 全量回填为 legacy

-- 五件套补齐(已有 source/verified_at)
ALTER TABLE model_alias ADD COLUMN method        TEXT;
ALTER TABLE model_alias ADD COLUMN fetched_at    TEXT;
ALTER TABLE model_alias ADD COLUMN evidence_ref  TEXT;

-- 生命周期
ALTER TABLE model_alias ADD COLUMN status        TEXT NOT NULL DEFAULT 'raw';
ALTER TABLE model_alias ADD COLUMN status_since  TEXT;
ALTER TABLE model_alias ADD COLUMN status_reason TEXT;

-- 扩展
ALTER TABLE model_alias ADD COLUMN updated_at    TEXT;

CREATE INDEX IF NOT EXISTS idx_model_alias_status     ON model_alias(status);
CREATE INDEX IF NOT EXISTS idx_model_alias_fetched    ON model_alias(fetched_at);
CREATE INDEX IF NOT EXISTS idx_model_alias_updated    ON model_alias(updated_at);

-- 历史 1370 行回填
-- 已 verified_at IS NOT NULL 的,status='verified'(B 级标杆已有验证)
-- 否则 status='legacy_unverified'
UPDATE model_alias
SET method         = COALESCE(method, CASE
                          WHEN source LIKE '%llm%' THEN 'llm_inferred'
                          WHEN source LIKE '%api%' THEN 'api_listed'
                          ELSE 'curate_legacy' END),
    fetched_at     = COALESCE(fetched_at, verified_at, '2026-06-19T00:00:00Z'),
    evidence_ref   = COALESCE(evidence_ref, NULL),
    status         = CASE
                       WHEN status='raw' AND verified_at IS NOT NULL THEN 'verified'
                       WHEN status='raw' THEN 'legacy_unverified'
                       ELSE status END,
    status_since   = COALESCE(status_since, verified_at, '2026-06-27T00:00:00Z'),
    status_reason  = COALESCE(status_reason,
                       CASE WHEN verified_at IS NOT NULL
                            THEN 'pre-governance verified; evidence_ref backfill pending'
                            ELSE 'pre-governance bulk import; needs evidence backfill' END),
    updated_at     = COALESCE(updated_at, verified_at, '2026-06-27T00:00:00Z')
WHERE method IS NULL;
