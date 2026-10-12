# DATA_LINEAGE.md — 数据 Provenance 与血缘溯源标准

> **Pillar 3 落地细则。** 任意一行数据,能在 3 步内查出"哪个采集器 + 什么 URL/API + 什么时候 + 用什么方法 + 当时原始响应"。
> **状态:** v0.1 (草案,2026-06-26) — Sprint 1 之前为 P0-P1 推进期。
> **对标:** OpenLineage 0.x facet 模型 (RunEvent / DatasetEvent / JobEvent)。

---

## 0. 写这份文档的原因

DATA_GOVERNANCE_FRAMEWORK.md §4 Pillar 3 给了"五件套"列(source / method / fetched_at / verified_at / evidence_ref),但是:

1. 当前实测落地不一致 — `price.source/fetched_at` 已有,`detection.source/detected_at` 已有,`model_alias.source/verified_at/evidence` 已有(但是 `evidence` 现存值是 JSON-in-string,不是 sha256 引用),其它表(`ranking_snapshot` / `health_snapshot` / `notification` / `detection.duration_ms` 等)**没有统一 Provenance 列**。
2. 每个表的"应该加哪几列、列里写什么值"没有写死,Agent 抓取脚本各写各的。
3. raw_snapshot 落盘机制只在 ranking_snapshot.raw_json / health_snapshot.raw_json 这种"整段塞 JSON"形式存在,**没有按 sha256 引用 + 90 天 TTL 的标准存储路径**。

本文档把这三件事 **写死**:统一的五件套列 + 取值字典 + 落盘路径 + 引用规则 + 三档优先级。

---

## 1. 五件套列规范(Provenance Quintuple)

每个写入 SoR (System of Record) 的数据表,**必须**含下列 5 列(或在视图层等价提供):

| 列名 | 类型 | 必填 | 含义 | 取值字典 |
|---|---|---|---|---|
| `source` | TEXT | 是 | 数据从**哪里**来 | 见 §1.1 |
| `method` | TEXT | 是 | 数据**怎么**来 | 见 §1.2 |
| `fetched_at` | TEXT (RFC3339 UTC) | 是 | 抓取的瞬间 | `2026-06-26T15:34:22Z` |
| `verified_at` | TEXT (RFC3339 UTC) | 否 | 二次验证通过的瞬间(没二次验证就 NULL) | 同上 |
| `evidence_ref` | TEXT | 否 | 原始响应快照引用 | 见 §2 |

> **不要**用 JSON-blob 把这 5 个值塞在 `raw_json` 列里 — 必须是独立列,因为查询/索引/SLO 报表全靠它。

### 1.1 source 字典(必填,枚举集中)

| source 取值 | 含义 | 示例使用表 |
|---|---|---|
| `openrouter` | OpenRouter 价格 API | `price` |
| `litellm` | LiteLLM 价格 YAML | `price` |
| `site:<provider_id>` | 直接抓某个中转站 (e.g. `site:aihubmix`) | `price`, `detection` |
| `relay_detector` | 内部检测协议(L1/L2/L3) | `detection` |
| `huggingface_hub` | HuggingFace model 元数据 | `model_canonical`, `model_alias` |
| `human` | 人工录入 | `model_canonical`, `provider` |
| `normalize_run:<run_id>` | 规整化运行 ID (链回 normalize_run 表) | `model_canonical`, `model_alias` |
| `derived:<rule_id>` | 从其它行计算出来的(派生数据,如 v_price_canonical) | 视图 |

**禁止值:** `unknown` / `NULL` / 空字符串 — 写入即拒(check constraint,Sprint 1 之后)。

### 1.2 method 字典

| method 取值 | 含义 |
|---|---|
| `http_pricing_api` | 调供应商定价 HTTP API |
| `http_html_scrape` | 直抓 HTML 页面 |
| `protocol_probe` | 协议探测请求(检测器) |
| `manual_input` | 人工写入 |
| `normalize_run` | normalize 脚本写入 |
| `migration` | yoyo 数据迁移生成 |
| `view_derived` | SQL 视图计算 |
| `external_feed` | 第三方 feed/RSS 拉取 |

---

## 2. evidence_ref — 原始响应快照规则

### 2.1 落盘路径
```
web_data/raw_snapshots/<YYYY-MM-DD>/<sha256>.json
                                    └── 取响应体 utf-8 编码后 sha256 hex (小写)
```

- 每天一个目录(便于 TTL 删除)
- 同一个 sha256 复用文件(去重) — 多行 evidence_ref 可指同一文件
- 文件格式: 单 JSON 对象, key 强约:
  ```json
  {
    "url": "https://openrouter.ai/api/v1/models",
    "request_method": "GET",
    "request_headers_hash": "<sha256 of important headers>",
    "response_status": 200,
    "response_headers": {"content-type": "application/json"},
    "response_body": "<原始响应 string,或 base64 if binary>",
    "fetched_at": "2026-06-26T15:34:22Z",
    "scraper_version": "tools_dev/scrape_openrouter.py@<git_hash_or_mtime>"
  }
  ```

### 2.2 evidence_ref 列值格式
```
raw_snapshot/<YYYY-MM-DD>/<sha256>.json
```
**不存绝对路径**,不存 base64,不存 inline JSON。

### 2.3 TTL 与归档
- 热存(默认): 0-90 天 → `web_data/raw_snapshots/`
- 冷存: 91-365 天 → `web_data/raw_snapshots_archive/<YYYY-MM>/<sha256>.zst` (zstd 压缩,合并成月份 tar)
- 归档脚本: `tools_dev/governance/archive_raw_snapshots.py` (待建,P1)
- 超过 365 天: 删除(保留 sha256 + 入归档清单 CSV)

### 2.4 不强制存的场景(P2 豁免)
| 场景 | 原因 |
|---|---|
| `human` source | 没有 HTTP 响应可存 |
| `derived:*` source | 由其它行计算,evidence 是上游行 |
| `view_derived` method | 视图无快照 |

---

## 3. 当前 DB 字段覆盖度审计(实测)

> 2026-06-26 实测 `web_data/db/tokenapi.db`。

| 表 | source | method | fetched_at | verified_at | evidence_ref | 优先级 |
|---|---|---|---|---|---|---|
| `price` | ✅ | ❌ | ✅ | ❌ | ❌ | **P0** |
| `model_alias` | ✅ | ❌ | ❌ | ✅ | ⚠️ (列叫 `evidence`,语义不一致) | **P0** |
| `model_canonical` | ❌ | ❌ | ❌ | ❌ | ❌ | P1 |
| `detection` | ✅ | ❌ | ✅ (`detected_at`) | ❌ | ❌ | **P0** |
| `provider` | ❌ | ❌ | ❌ | ❌ | ❌ (有 `raw_json` 但语义混) | P1 |
| `model_spu` | ❌ | ❌ | ❌ | ❌ | ❌ | P2 |
| `model_sku` | ❌ | ❌ | ❌ | ❌ | ❌ | P2 |
| `ranking_snapshot` | ❌ | ❌ | ✅ (`generated_at`) | ❌ | ⚠️ (用 `raw_json` 整段塞) | P1 |
| `health_snapshot` | ❌ | ❌ | ✅ (`snapshot_date`) | ❌ | ⚠️ (用 `raw_json` 整段塞) | P1 |
| `notification` | ❌ | ❌ | ❌ | ❌ | ❌ | P2 |
| `authority_map` | ❌ | ❌ | ❌ | ❌ | ❌ | P1 |
| `catalog_metric` | ❌ | ❌ | ❌ | ❌ | ❌ | P2 |
| `detection.duration_ms` 等 | n/a | n/a | n/a | n/a | n/a | n/a |
| `normalize_run` | ✅ (内含) | ✅ (内含) | ✅ (`started_at`) | ✅ (`finished_at`) | ❌ | P1 |

总覆盖度: 五件套全齐 0/14 表 (0%)。
含 ≥3 件套: 4/14 (29%) — `price` / `model_alias` / `detection` / `normalize_run`。

---

## 4. DB ALTER 候选清单(执行顺序)

> **执行方式:** 走 `yoyo` migration (不在生产手动 ALTER)。
> **migration 文件命名:** `migrations/0NN__lineage_<table>.sql`。
> **生产回滚:** yoyo rollback。
> **执行前必做:** 备份 `web_data/db/tokenapi.db` (cp + sha256 入 `backups/`)。

### P0 — 三表加固(本周内)

#### M1 · price (3 列)
```sql
-- migrations/030__lineage_price.sql
ALTER TABLE price ADD COLUMN method        TEXT;
ALTER TABLE price ADD COLUMN verified_at   TEXT;
ALTER TABLE price ADD COLUMN evidence_ref  TEXT;
CREATE INDEX IF NOT EXISTS idx_price_method ON price(method);
```
**写入端改造:** `tools_dev/price_scraping/` 下所有 scraper 写入时填 method (`http_pricing_api` / `http_html_scrape`) + 落 evidence。

#### M2 · model_alias 列重命名 + 语义对齐
```sql
-- migrations/031__lineage_model_alias.sql
ALTER TABLE model_alias ADD COLUMN method       TEXT;
ALTER TABLE model_alias ADD COLUMN fetched_at   TEXT;
ALTER TABLE model_alias ADD COLUMN evidence_ref TEXT;
-- 把 evidence (JSON-string) 迁到 evidence_ref (落盘路径)
-- 迁移脚本: tools_dev/governance/migrate_alias_evidence.py (P1 写)
```
> **不动** 现有 `evidence` 列,先并行存 `evidence_ref`,P1 完成数据回填后再 DROP `evidence`。

#### M3 · detection (3 列)
```sql
-- migrations/032__lineage_detection.sql
ALTER TABLE detection ADD COLUMN method        TEXT;
ALTER TABLE detection ADD COLUMN verified_at   TEXT;
ALTER TABLE detection ADD COLUMN evidence_ref  TEXT;
CREATE INDEX IF NOT EXISTS idx_detection_method ON detection(method);
```
**写入端改造:** `src/detection/relay_detector*.py` 写入填 method=`protocol_probe`,evidence 落 `raw_snapshots/`。

### P1 — 5 表统一(Sprint 1, 2-4 周)

| migration 文件 | 表 | 加列 |
|---|---|---|
| `033__lineage_model_canonical.sql` | model_canonical | source/method/fetched_at/verified_at/evidence_ref |
| `034__lineage_provider.sql` | provider | source/method/fetched_at/verified_at/evidence_ref (并保留 raw_json 兼容) |
| `035__lineage_ranking_snapshot.sql` | ranking_snapshot | source/method/verified_at/evidence_ref(替换 raw_json 落盘) |
| `036__lineage_health_snapshot.sql` | health_snapshot | source/method/verified_at/evidence_ref |
| `037__lineage_authority_map.sql` | authority_map | source/method/fetched_at/verified_at |

### P2 — 收口(Sprint 2, 4-8 周)

- `model_spu` / `model_sku` / `notification` / `catalog_metric` — 五件套统一加列
- `evidence` 列 (model_alias) DROP — 数据回填完成后
- check constraint `source IN (...)` — 启用枚举强约
- `v_lineage_coverage` 视图 — 每表 5 列非空率,接 Grafana

---

## 5. 写入端契约(每个 scraper / scripter 必读)

每个写入 SoR 表的入口函数,**必须**在 INSERT/UPDATE 时:

1. **填 source** — 不允许 NULL,值取自 §1.1 字典
2. **填 method** — 不允许 NULL,值取自 §1.2 字典
3. **填 fetched_at** — `datetime.now(timezone.utc).isoformat(timespec='seconds')`
4. **落 evidence** — 调 `src/governance/evidence_store.py:save_evidence(response_obj) -> "raw_snapshot/<date>/<sha>.json"` (待建,P0 第二件事)
5. **回填 evidence_ref**

> Sprint 1 完成后,启用 pre-insert 校验装饰器: `@requires_lineage(["source","method","fetched_at"])`,缺一即抛 `LineageMissingError`。

---

## 6. 查询模式(给 Agent / 报表 / 用户)

### 6.1 任意一行回溯
```sql
SELECT canonical_id, raw_model_id, input_price_usd_per_1m,
       source, method, fetched_at, verified_at, evidence_ref
FROM price
WHERE provider_id = 'aihubmix' AND canonical_id = 'gpt-4o-2024-11-20'
ORDER BY fetched_at DESC LIMIT 1;
```
拿到 `evidence_ref` → `cat web_data/raw_snapshots/2026-06-26/<sha>.json` → 看原始响应。

### 6.2 覆盖度报表 (P1 视图)
```sql
CREATE VIEW v_lineage_coverage AS
SELECT 'price' AS table_name,
       COUNT(*) AS total,
       SUM(CASE WHEN source IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS source_rate,
       SUM(CASE WHEN method IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS method_rate,
       SUM(CASE WHEN fetched_at IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS fetched_rate,
       SUM(CASE WHEN evidence_ref IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS evidence_rate
FROM price
UNION ALL
SELECT 'model_alias', ... -- 同上
UNION ALL ...
```

### 6.3 SLO 目标
| 表 | source 非空率 | method 非空率 | evidence_ref 非空率(豁免后) |
|---|---|---|---|
| price | ≥ 99% | ≥ 95% | ≥ 90% (近 90 天) |
| detection | ≥ 99% | ≥ 99% | ≥ 95% (近 90 天) |
| model_alias | ≥ 95% | ≥ 90% | ≥ 80% (近 90 天) |
| 其它 | ≥ 90% | ≥ 80% | ≥ 70% (近 90 天) |

---

## 7. 与已有标准的关系

- **DATA_GOVERNANCE_FRAMEWORK.md §4 Pillar 3** — 这是细化落地。
- **DATA_VERIFICATION_STANDARD.md** — 二次验证写 `verified_at` 字段,evidence 引用相同体系。
- **DATA_CATALOG.md** — 每个 dataset 条目应引用本文档的 evidence_ref 规则。
- **CATALOG_STANDARD.md / SPU/SKU 三层** — SPU/SKU 表 P2 期收口加五件套。

---

## 8. 不在本文档范围

- ❌ 列血缘(column-level lineage,OpenLineage facets) — Sprint 2 之后
- ❌ 主动血缘事件流(emit RunEvent) — Sprint 3 之后  
- ❌ 跨服务血缘(微服务间 trace) — 暂不规划
- ❌ 隐私脱敏与 PII 处理 — Pillar 7 单独写

---

**变更记录**
- v0.1 (2026-06-26) — 初稿,P0 候选清单 + 字典固化。
