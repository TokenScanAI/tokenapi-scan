-- 治理字段迁移 · model_canonical 加五件套
-- Pillar 3 实施起点 · 2026-06-26
-- 关联:DATA_GOVERNANCE_FRAMEWORK.md / DATA_VERIFICATION_STANDARD.md
-- 原因:model_canonical(1260 行)是最稀缺字典型资产,但治理等级 D,任何改动不可审计

-- 五件套
ALTER TABLE model_canonical ADD COLUMN source        TEXT;
ALTER TABLE model_canonical ADD COLUMN method        TEXT;
ALTER TABLE model_canonical ADD COLUMN fetched_at    TEXT;
ALTER TABLE model_canonical ADD COLUMN verified_at   TEXT;
ALTER TABLE model_canonical ADD COLUMN evidence_ref  TEXT;

-- 生命周期(Pillar 6 启动 · model_canonical 是第一张装备状态机的表)
ALTER TABLE model_canonical ADD COLUMN status        TEXT NOT NULL DEFAULT 'raw';
ALTER TABLE model_canonical ADD COLUMN status_since  TEXT;
ALTER TABLE model_canonical ADD COLUMN status_reason TEXT;

-- 治理时间戳(扩展信号)
ALTER TABLE model_canonical ADD COLUMN updated_at    TEXT;

-- 索引
CREATE INDEX IF NOT EXISTS idx_model_canonical_status ON model_canonical(status);
CREATE INDEX IF NOT EXISTS idx_model_canonical_source ON model_canonical(source);
CREATE INDEX IF NOT EXISTS idx_model_canonical_verified ON model_canonical(verified_at);

-- 历史数据回填(已有 1260 行无证据,标记为 legacy)
-- legacy 等级 ≠ 入产,后续要走 Gate-CURATE 再升级
UPDATE model_canonical
SET source         = COALESCE(source, 'legacy_pre_governance'),
    method         = COALESCE(method, 'manual_curate'),
    fetched_at     = COALESCE(fetched_at, '2026-06-19T00:00:00Z'),
    verified_at    = COALESCE(verified_at, NULL),
    evidence_ref   = COALESCE(evidence_ref, NULL),
    status         = COALESCE(status, 'legacy_unverified'),
    status_since   = COALESCE(status_since, '2026-06-26T00:00:00Z'),
    status_reason  = COALESCE(status_reason, 'pre-governance bulk import; needs evidence backfill'),
    updated_at     = COALESCE(updated_at, '2026-06-26T00:00:00Z')
WHERE source IS NULL;
