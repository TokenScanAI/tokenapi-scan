-- 治理字段迁移 M3 · detection 加五件套(method/fetched_at/verified_at/evidence_ref)
-- Pillar 3 实施 · 2026-06-27
-- 现状:已有 source + detected_at(=语义 fetched_at) + is_legacy 列
-- 设计:不重命名 detected_at,而是新加 fetched_at(规范字段)双列并行,后续脚本写入端可统一
--      verified_at 对于探测的语义 = 二次复核时间(同一目标 24h 内复测验证)
-- 行数:7503 行 → 全量回填:已 is_legacy=1 标 legacy_unverified,其余按 source 推 method

-- 五件套规范字段补齐(detected_at 不动)
ALTER TABLE detection ADD COLUMN method        TEXT;
ALTER TABLE detection ADD COLUMN fetched_at    TEXT;
ALTER TABLE detection ADD COLUMN verified_at   TEXT;
ALTER TABLE detection ADD COLUMN evidence_ref  TEXT;

-- 生命周期
ALTER TABLE detection ADD COLUMN status        TEXT NOT NULL DEFAULT 'raw';
ALTER TABLE detection ADD COLUMN status_since  TEXT;
ALTER TABLE detection ADD COLUMN status_reason TEXT;

-- 扩展
ALTER TABLE detection ADD COLUMN updated_at    TEXT;

CREATE INDEX IF NOT EXISTS idx_detection_status     ON detection(status);
CREATE INDEX IF NOT EXISTS idx_detection_method     ON detection(method);
CREATE INDEX IF NOT EXISTS idx_detection_verified   ON detection(verified_at);

-- 7503 行回填
UPDATE detection
SET method         = COALESCE(method, CASE
                          WHEN source LIKE '%relay_detector%' THEN 'relay_probe'
                          WHEN source LIKE '%manual%' THEN 'manual_check'
                          ELSE 'auto_probe_legacy' END),
    fetched_at     = COALESCE(fetched_at, detected_at),
    verified_at    = COALESCE(verified_at, NULL),
    evidence_ref   = COALESCE(evidence_ref, NULL),
    status         = CASE
                       WHEN status='raw' AND is_legacy=1 THEN 'legacy_unverified'
                       WHEN status='raw' AND success=1 THEN 'probe_ok'
                       WHEN status='raw' AND success=0 THEN 'probe_failed'
                       ELSE status END,
    status_since   = COALESCE(status_since, detected_at, '2026-06-27T00:00:00Z'),
    status_reason  = COALESCE(status_reason,
                       CASE WHEN is_legacy=1
                            THEN 'pre-governance probe; needs evidence_ref backfill'
                            ELSE 'auto-classified from success flag' END),
    updated_at     = COALESCE(updated_at, detected_at, '2026-06-27T00:00:00Z')
WHERE method IS NULL;
