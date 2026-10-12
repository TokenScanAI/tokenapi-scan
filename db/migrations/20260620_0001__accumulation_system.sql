-- 数据积累体系 migration  2026-06-20
-- 目的:把"一次性盘点"升级为"自己跑、自己攒"的活体系
-- 三张积累载体:authority_map(模型权威映射) / framework_registry(价格框架端点谱) / model_alias 加证据字段

-- ============================================================
-- 1. authority_map —— 官方发布阵地(HF/魔搭)权威映射积累表
--    每条 = 一个从官方源校对出来的"权威事实",可重复校验、可追溯
-- ============================================================
CREATE TABLE IF NOT EXISTS authority_map (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  alias         TEXT NOT NULL,            -- 中转站/源里出现的原始模型名
  canonical_id  TEXT,                     -- 归一到的标准 id(对齐 model_canonical)
  authority     TEXT NOT NULL,            -- 权威源: huggingface / modelscope / vendor_doc / relay_site_doc
  authority_ref TEXT,                     -- 证据链接:HF repo / 魔搭 repo / 厂商文档 / 中转站说明页 URL
  base_model    TEXT,                     -- HF base_model 标签声明的上游(客观证据)
  relation      TEXT,                     -- base / finetune / quant / alias / variant / independent
  vendor        TEXT,                     -- 官方厂商
  confidence    TEXT NOT NULL DEFAULT 'medium',  -- high(官方tag) / medium(前缀规则) / low(待人工)
  verified_at   TEXT,                     -- 最近一次真实校对时间
  note          TEXT,
  UNIQUE(alias, authority)
);
CREATE INDEX IF NOT EXISTS idx_authority_alias ON authority_map(alias);
CREATE INDEX IF NOT EXISTS idx_authority_canonical ON authority_map(canonical_id);
CREATE INDEX IF NOT EXISTS idx_authority_conf ON authority_map(confidence);

-- ============================================================
-- 2. framework_registry —— 中转站开源框架指纹 + 公开端点谱积累表
--    每条 = 一个站点的框架识别结果 + 可拿源数据的公开端点 + 最近探测状态
-- ============================================================
CREATE TABLE IF NOT EXISTS framework_registry (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  domain          TEXT NOT NULL UNIQUE,   -- 站点域名
  framework       TEXT,                   -- new-api / one-api / veloera / done-hub / shell-api / unknown
  framework_evidence TEXT,                -- 识别依据:window.__APP_CONFIG__ / 页脚 / 端点形态
  price_endpoint  TEXT,                   -- 可拿价格的公开端点(如 /api/pricing)
  endpoint_status TEXT,                   -- open(公开可取) / auth(需登录) / empty(端点在但空) / dead(无)
  models_count    INTEGER DEFAULT 0,      -- 最近探测拿到的模型数
  quota_type_note TEXT,                   -- 计费形态:token/per-call 混合说明
  last_probed_at  TEXT,
  recoverable     INTEGER DEFAULT 0,      -- 1=可入库源 0=暂不可
  note            TEXT
);
CREATE INDEX IF NOT EXISTS idx_fw_recoverable ON framework_registry(recoverable);
CREATE INDEX IF NOT EXISTS idx_fw_framework ON framework_registry(framework);

-- ============================================================
-- 3. model_alias 补证据字段 —— 解决"93% 未验证"
--    SQLite 不支持 IF NOT EXISTS 加列,迁移脚本里用 PRAGMA 防重复
-- ============================================================
-- ALTER 由 python 迁移器条件执行(见 apply_migration.py),此处仅注释期望末态:
--   ALTER TABLE model_alias ADD COLUMN confidence TEXT DEFAULT 'low';
--   ALTER TABLE model_alias ADD COLUMN evidence TEXT;
--   ALTER TABLE model_alias ADD COLUMN verified_at TEXT;
