# TokenAPI Scan · 数据治理总纲（DATA_GOVERNANCE_FRAMEWORK）v0.1

定稿日期：2026-06-26　状态：草案 v0.1 → **本文档是治理体系顶层框架,允许并预期慢慢迭代**
适用范围：所有数据资产(SQLite / JSON / 日志 / 缓存 / 报告)
关联文档：MODEL_DATA_STANDARD.md · CATALOG_STANDARD.md · PRICE_DATA_PIPELINE_STANDARD.md · COLLISION_CLASSIFICATION_STANDARD.md · DATA_QUALITY_AUDIT_STANDARD.md

---

## 0. 写这份文档的原因

用户反复强调:**"主要问题是在数据标准和后续治理,而不是数值抓取源。"**

这话的含义是:

| 错觉 | 真相 |
|---|---|
| 数据问题 = 源问题(抓哪个站) | 数据问题 = **入库后到用户决策之间整条链路的治理薄弱** |
| 换个干净源就好了 | 任何源都可能污染,**关键是从源到产品的每一道闸口** |
| 加点验证脚本就行 | 验证脚本只是治理体系**一个环节**,缺顶层标准等于做点状救火 |
| 字段加多了再说 | **字段从一开始就缺治理元数据**,加一次改全库,代价大 |

所以这份文档不是"再写一个验证脚本",而是把治理拆成**九个相互独立又咬合**的子系统,
每一个都有自己的标准 + 工具 + 验收。允许慢做,**但每加一个新数据流必须先过这九个**。

---

## 1. 治理体系九大支柱(Pillars)

```
            ┌────────────────────────────────────────────────────┐
            │              用户 / 外部 Agent / API 消费方         │
            └─────────────────────────▲──────────────────────────┘
                                      │ 9. 退役 & 归档
                                      │ 8. 治理可观测性
   ┌──────────────────────────────────┼──────────────────────────┐
   │              ⬇ 数据资产 ⬇                                    │
   │  ┌──────────────────────────────────────────────────────┐  │
   │  │ Pillar 1 数据资产清单(Data Catalog)                  │  │
   │  │ Pillar 2 数据模型 & Schema 规范                      │  │
   │  │ Pillar 3 来源 & Provenance 溯源                      │  │
   │  │ Pillar 4 验证 & 闸口(Verification Gates)            │  │
   │  │ Pillar 5 质量度量 & SLO                              │  │
   │  │ Pillar 6 生命周期(Ingest → Curate → Publish)         │  │
   │  │ Pillar 7 隐私 / 合规 / 安全(PII / License)           │  │
   │  └──────────────────────────────────────────────────────┘  │
   └──────────────────────────────────────────────────────────────┘
```

| Pillar | 核心问题 | 输出 | 当前评分 |
|---|---|---|---|
| 1 数据资产清单 | 我们到底有多少数据,在哪 | DATA_CATALOG.md(自动生成) | C |
| 2 Schema 规范 | 每张表 / 字段是怎么约定的 | per-table schema + ER 图 | B |
| 3 Provenance | 每条数据从哪来、怎么验过 | 每行带 source/method/at | D+ |
| 4 验证闸口 | 数据进 / 出 / 改要过哪些门 | 三道闸 SOP + 验证脚本 | D |
| 5 质量度量 | 我们怎么知道数据"好" | 5 大维度 SLO + dashboard | C |
| 6 生命周期 | 数据状态怎么流转 | raw → probed → cross-verified → published 四态 | D |
| 7 合规 | PII / License / 红线 | 黑名单 + 字段脱敏规则 | C |
| 8 可观测性 | 治理本身怎么监控 | governance_health.json + 告警 | F(无) |
| 9 退役归档 | 旧数据怎么停用 | TTL + 归档策略 | F(无) |

**评分含义:** A=同业最佳 / B=合格 / C=有但不全 / D=有但不可靠 / F=不存在

---

## 2. 我们今天数据治理的真实现状(实测,而非自我宣称)

> 用 2026-06-26 实测生产 DB `web_data/db/tokenapi.db` 3.8M 16 表 的扫描结果。

### 2.1 表治理字段覆盖度(治理底盘)

| 表 | 行数 | 时间戳 | 来源 | 置信度 | 溯源 | 治理等级 |
|---|---|---|---|---|---|---|
| provider | 117 | ✅ added_at + updated_at | — | — | — | C |
| model_canonical | 1260 | — | — | — | — | **D** |
| model_alias | 1370 | — | ✅ source | ✅ verified | ✅ evidence | B |
| model_spu | 1151 | ✅ | — | — | — | C |
| model_sku | 1181 | ✅ | — | — | — | C |
| price | 3807 | ✅ | ✅ | — | — | C |
| detection | 7363 | — | ✅ | — | — | C |
| framework_registry | 243 | — | — | — | ✅ evidence | C |
| authority_map | 476 | — | — | ✅ | — | C |
| catalog_metric | 14 | — | — | — | — | D |
| normalize_run | 125 | — | ✅ | — | — | B |
| health_snapshot | 8 | — | — | — | — | D |
| provider_model_support | 147 | — | ✅ | — | — | C |
| notification | 0 | — | — | — | — | — |
| ranking_snapshot | 0 | — | — | — | — | — |
| seo_report | 0 | — | — | — | — | — |

**几个关键判读:**

1. **`model_canonical` 1260 行 — 0 治理字段** ❌
   - 这是行业最稀缺的字典型资产,但没记"是谁、用什么方法、什么时候、基于什么证据"判定的
   - **任何改动都不可审计**
2. **`model_alias` 是范本** ✅
   - source / verified / evidence 三件套齐全
   - 其它表应当对标这套
3. **`detection` 7363 行没有 created_at** ❌
   - 检测结果没时间戳意味着"什么时候检测的"无法追溯,SLO 评估时全废

### 2.2 数据库 schema migrations

| 项 | 现状 |
|---|---|
| schema.sql | 6577 字节,2026-06-19 定稿 |
| migrations 目录 | 仅 1 个文件(`0620_accumulation_system.sql`) |
| migration 工具 | **无**(没用 alembic / sqlx / yoyo) |
| 改 schema 流程 | 手写 SQL + 手跑,无 review |

**问题:** 6/20 之后所有 schema 变更(model_canonical 663 行加入、price 765 行扩容、model_alias 677 行扩容,见 memory)都**没进 migrations**,只有 `schema.sql` 这一份当前快照。换言之:**回滚 / 复现 / CI/CD 全做不了。**

### 2.3 验证脚本现状(Pillar 4)

| 数据流 | 验证脚本 | 在跑吗 |
|---|---|---|
| 候选发现 | **无** | ❌ |
| 价格抓取 | **无** | ❌ |
| 协议探测 | 见 FRAMEWORK_FINGERPRINT.md | ✅ |
| 撞名归类 | `tools_dev/auto_classify_collision.py` | ✅ |
| 凭据泄漏 | `tools_dev/leak_validator/` | ✅(假阳检测) |
| Model 字段填充 | 见 MODEL_DATA_STANDARD.md | 半 ✅ |
| Schema 一致性 | **无** | ❌ |
| 跨表外键完整性 | **无** | ❌(虽然 PRAGMA foreign_keys=ON) |
| 治理字段覆盖度 | **无** | ❌ |
| 数据时效性 | **无** | ❌ |

### 2.4 治理文档现状

| 文档 | 行数 | 评分 | 覆盖 |
|---|---|---|---|
| MODEL_DATA_STANDARD.md | ? | A | Model 资产 |
| CATALOG_STANDARD.md | ? | B+ | SPU/SKU/库存 |
| PRICE_DATA_PIPELINE_STANDARD.md | ? | B+ | 价格抓取 |
| COLLISION_CLASSIFICATION_STANDARD.md | ? | A | 撞名归类 |
| DATA_QUALITY_AUDIT_STANDARD.md | ? | B | 事后质检 |
| PROVIDER_STATUS_STANDARD.md | ? | C | provider 状态 |
| FRAMEWORK_FINGERPRINT.md | ? | A | 协议指纹 |
| **DATA_GOVERNANCE_FRAMEWORK.md** | 本文档 | — | **顶层框架(原本无)** |
| **DATA_CATALOG.md** | 0 | F | **每张表干嘛(原本无)** |
| **DATA_LINEAGE.md** | 0 | F | **数据从哪流到哪(原本无)** |
| **DATA_VERIFICATION_STANDARD.md** | 0 | F | **进 / 出 / 改三道闸(原本无)** |
| **DATA_SLO.md** | 0 | F | **质量度量与目标(原本无)** |
| **DATA_RETENTION_POLICY.md** | 0 | F | **TTL / 归档(原本无)** |

---

## 3. 治理目标(锚定 12 个月)

### 3.1 北极星指标

> **"任意一条被产品消费的数据,在 60s 内能回答:它是谁、什么时候、用什么方法、从哪来、可信度多高、是否过期、谁动过、合规等级。"**

7 个问题,缺一不可。我们今天能稳定回答其中 1-2 个,目标是 12 个月内全部能答。

### 3.2 SLO 锚点(初稿,待 DATA_SLO.md 细化)

| 指标 | 当前 | 30 天 | 90 天 | 12 月 |
|---|---|---|---|---|
| 表带完整治理字段(time/source/conf/lineage) | 1/16=6% | 50% | 80% | 100% |
| 每条数据可溯源到原始 evidence | < 10% | 50% | 80% | 95% |
| Schema 变更走 migration | 0% | 100% | 100% | 100% |
| 数据生命周期状态字段 | 0/16 表 | 5 表 | 12 表 | 16 表 |
| 异常数据自动告警覆盖 | 0 类 | 3 类 | 8 类 | 全部 |
| 治理 KPI dashboard | 无 | 框架 | 完整 | 自动化 |

### 3.3 治理原则(写下来不再讨论)

1. **每条数据带身份证** — `source / method / verified_at / verification_level / evidence_ref` 五件套,缺一不可
2. **不在不可逆地方做猜测** — `is_official_baseline`、`network_status`、`verification_level` 任何"算出来"的字段必须能复现
3. **变更走 migration** — 任何 schema 变化 ≥ 一个 SQL 文件落 `migrations/`,文件名规则 `YYYYMMDD_HHMM__<change>.sql`
4. **多源决定,单源不杀** — 一个数据点只一个来源说它有问题 → 标记 `suspicious` 不删;两个来源 → 标 `disputed`;三个 → `quarantined`
5. **写比删容易** — 任何 production DELETE 必须先 `INSERT INTO _trash` 同结构表
6. **治理自身要可观测** — 治理脚本不跑、跑挂、跑出 0 行都得告警
7. **行业惯例对标** — 任何一条标准都有"我们参考了 X(dbt / Great Expectations / OpenLineage / data-mesh)"标注

---

## 4. 九大支柱 — 详细规划(草案)

### Pillar 1 · 数据资产清单(DATA CATALOG)

**目标:** 任何成员能用 60s 看完 "我们有什么数据 / 在哪 / 谁负责 / 怎么用"。

**输出:** `docs/standards/DATA_CATALOG.md`(自动生成,不允许手写)

**字段(每张表):**
```
table_name        provider
purpose           站点档案表
storage           web_data/db/tokenapi.db
schema_owner      你
data_owner        @cron(daily_promote)
row_count         117
size              ~30KB
freshness         updated_at < 24h
governance_level  C
referenced_by     ranking_snapshot / detection / price
references        —
retention         永久(快照)
```

**实施方案:**
- 写 `scripts/governance/build_data_catalog.py` 扫所有 DB + JSON 资产 → 生成 markdown
- cron 每周一 09:00 跑一次
- diff 入 git,变化邮件 / 微信告警

**优先级:** P0(本周可起,200 行 Python)

---

### Pillar 2 · 数据模型 & Schema 规范

**目标:** Schema 变更可追溯、可回滚、可在 dev 重放。

**关键工具:**
- 引入 **yoyo-migrations**(轻量,无 ORM 入侵)
- 所有 migration 文件命名:`YYYYMMDD_HHMM__<verb>_<noun>.sql`
- 必带 `-- up` / `-- down` 两段
- 引入 **schemathesis** 跑 schema 一致性

**新增标准文档:** `docs/standards/SCHEMA_EVOLUTION_STANDARD.md`

**红线:**
- ❌ 手 ALTER TABLE production DB
- ❌ schema.sql 与 production DB 不一致(每日 cron 校验)

**优先级:** P1(本月)

---

### Pillar 3 · 来源 & Provenance 溯源

**目标:** 任意一行能查 "哪个采集器 + 什么 URL/API + 什么时候 + 用什么验证方法 + 当时原始响应快照"。

**Schema 加固(五件套):**
```sql
ALTER TABLE <each_data_table> ADD COLUMN source         TEXT;     -- 'openrouter' / 'litellm' / 'site:<provider_id>' / 'human'
ALTER TABLE <each_data_table> ADD COLUMN method         TEXT;     -- 'http_pricing_api' / 'manual_input' / 'normalize_run:<id>'
ALTER TABLE <each_data_table> ADD COLUMN fetched_at     TEXT;     -- RFC3339 UTC
ALTER TABLE <each_data_table> ADD COLUMN verified_at    TEXT;
ALTER TABLE <each_data_table> ADD COLUMN evidence_ref   TEXT;     -- 'raw_snapshot/<sha256>.json'
```

**evidence 存储:**
- 每次抓取响应 raw JSON 落盘 `web_data/raw_snapshots/<YYYY-MM-DD>/<sha256>.json`
- 表里只存 `sha256` 引用,不存全内容
- TTL 90 天 → 进归档冷存

**新增标准文档:** `docs/standards/DATA_LINEAGE.md` + OpenLineage 对标

**优先级:** P0-P1(本月内分表逐个加)

---

### Pillar 4 · 验证 & 闸口(三道闸 Gates)

**目标:** 任何数据进 / 出 / 改产品必须过三道闸,缺一不可。

```
Gate-IN(入库)      Gate-CURATE(治理)      Gate-OUT(发布)
   │                  │                       │
   ▼                  ▼                       ▼
- 格式合法           - 探测验证               - SLO 通过
- 来源已注册         - 跨源交叉               - 抽检 5%
- 不在黑名单         - z-score 异常           - 合规字段过滤
- 字段必填齐         - 历史突变               - 用户决策影响审计
```

每张表声明 "我必须过哪几个闸"(在 DATA_CATALOG.md 标注)。

**新增脚本(分阶段,慢做):**

> ⚠️ **10/4 实测: 下表 7 个脚本全部不存在**（`tools_dev/governance/` 下只有
> `schema_drift_check.py` / `schema_guardrails.py` / `provenance_backfill.py` /
> `infer_payment_methods.py` / `apply_migration.sh`）。本表是**规划**, 不是现存机制 ——
> 读的人容易误以为闸已在跑。`DATA_VERIFICATION_STANDARD.md` 里"Gate-OUT 每次发布阻断发布"
> 同理, 那条阻断目前也不存在。
> 处置原则同本项目铁律: 规划要么建成会失败的检查, 要么显式标注"未实现"。
> **不允许**长期留一张看起来像现状的规划表。实际在跑的闸见
> `tools_dev/governance/schema_guardrails.py`（G1-G9, 由 `apply_migration.sh` 强制执行）。

| 脚本 | 闸 | 频次 | 优先级 | 实现状态 @10-4 |
|---|---|---|---|---|
| `governance/gate_in_schema_check.py` | IN | 每次写入(trigger) | P0 | ❌ 未实现 |
| `governance/gate_in_source_whitelist.py` | IN | 每次写入 | P0 | ❌ 未实现 |
| `governance/gate_curate_cross_source.py` | CURATE | 每日 | P1 | ❌ 未实现 |
| `governance/gate_curate_zscore.py` | CURATE | 每日 | P1 | ❌ 未实现 |
| `governance/gate_curate_diff_alert.py` | CURATE | 每日 | P1 | ❌ 未实现 |
| `governance/gate_out_slo_check.py` | OUT | 每次发布 ranking | P2 | ❌ 未实现 |
| `governance/gate_out_sampling_audit.py` | OUT | 每周 | P2 | ❌ 未实现 |

**新增标准文档:** `docs/standards/DATA_VERIFICATION_STANDARD.md`

---

### Pillar 5 · 质量度量 & SLO

**目标:** 数据"好不好"可被一个数字回答,不靠感觉。

**5 大维度(借鉴 dbt / Great Expectations / DAMA-DMBOK):**

| 维度 | 度量 | 例子 |
|---|---|---|
| Completeness | 必填字段非空率 | model_canonical.canonical_id 非空率 |
| Accuracy | 抽检通过率 | 5% 抽检 price 与公开页面一致 |
| Consistency | 跨表外键完整性 | model_sku.canonical_id 在 model_canonical 中存在 |
| Timeliness | 数据新鲜度 | price.updated_at < 7d 比例 |
| Validity | 取值合法率 | provider.region in {CN, US, EU, GLOBAL} |

**SLO 表(每表):**
```
table             completeness  accuracy  consistency  timeliness  validity
provider          ≥99%         ≥95%      ≥99%         ≥80%       ≥99%
model_canonical   ≥95%         ≥90%      ≥99%         —          ≥99%
price             ≥80%         ≥85%      ≥99%         ≥90%       ≥95%
```

**新增标准文档:** `docs/standards/DATA_SLO.md`

**实施:** `governance/quality_runner.py` 每日跑,结果落 `data_quality_metric` 表,跌破 SLO → 微信告警。

---

### Pillar 6 · 生命周期(Status Machine)

**目标:** 每条数据有四态,转换需理由,不允许跳态。

```
raw  ──probe─→  probed  ──cross_verify─→  cross_verified  ──audit─→  published
                  │            │                  │
                  ▼            ▼                  ▼
              quarantined    disputed         retired
```

**Schema 加固:**
```sql
ALTER TABLE <each_data_table> ADD COLUMN status       TEXT NOT NULL DEFAULT 'raw';
ALTER TABLE <each_data_table> ADD COLUMN status_since TEXT;
ALTER TABLE <each_data_table> ADD COLUMN status_reason TEXT;
```

**Where each state is visible:**
- `raw` — 候选池,内部 dev 可见,**不上 prod**
- `probed` — 价格表 / 检测表,UI 标"单源"
- `cross_verified` — 进红黑榜
- `published` — 进 API / 数据快照
- `quarantined` — 仅内部审计可见
- `disputed` — UI 标"有争议"
- `retired` — 仅历史归档

**新增标准文档:** `docs/standards/DATA_LIFECYCLE.md`

---

### Pillar 7 · 隐私 / 合规 / 安全

**目标:** PII 不出库,License 不踩雷,凭据不落地。

**字段分级(借鉴 GDPR / DAMA-DMBOK):**

| 等级 | 例子 | 处置 |
|---|---|---|
| PUBLIC | provider.endpoint, model_canonical.canonical_id | 直接 API 公开 |
| INTERNAL | detection.raw_response, normalize_run.params | 只内部脚本 |
| SENSITIVE | leak_radar.credential_sample | 永不落 DB 完整字段,仅指纹 |
| FORBIDDEN | 用户 API Key | 永不触碰 |

**License 矩阵(借鉴 Layer 1/2/3 资产分级):**

| 数据 | License | 商业转售 |
|---|---|---|
| provider 公开元数据 | CC-BY 4.0 | ✅ |
| 月度数据快照(脱敏) | CC-BY-NC 4.0 | ❌ |
| 实时全量价格 | 商业 License | ❌(企业版才有) |
| 检测引擎完整日志 | 不发布 | ❌ |

**新增标准文档:** `docs/standards/DATA_PRIVACY_AND_LICENSE.md`

---

### Pillar 8 · 治理可观测性

**目标:** 治理体系自己出问题,我们能 5 分钟知道。

**dashboard 指标(governance_health.json):**
```
- governance_field_coverage   每表治理字段覆盖率
- migration_drift             schema.sql vs production diff
- gate_pass_rate              过去 24h 各闸通过率
- slo_breach_count            过去 24h SLO 跌破数
- raw_snapshot_orphan_count   evidence_ref 引用但快照不存在
- retention_overdue           应归档但未归档行数
```

**告警通道:**
- 微信(daily summary + 即时严重告警)
- 内部 status page

**优先级:** P2(数据治理本身先有几个 Pillar 跑起来再监控)

---

### Pillar 9 · 退役 & 归档

**目标:** 数据不无限堆积,旧数据按价值分级归档。

**TTL 策略(初稿):**

| 数据 | hot | warm | cold | delete |
|---|---|---|---|---|
| raw_snapshots | 0-30d | 30-90d | 90d-2y | 2y+ |
| detection 详细 raw | 0-7d | 7-30d | 30-180d | 180d+(仅留摘要) |
| price 历史 | 永久 hot | — | — | — |
| access_logs | 0-7d | 7-30d | 30-180d | 180d+ |
| 内部告警 / cron output | 0-30d | — | 30-90d | 90d+ |

**归档存储:** `web_data/_cold/<YYYY>/` + tar.gz + sha256

**新增标准文档:** `docs/standards/DATA_RETENTION_POLICY.md`

**优先级:** P2

---

## 5. 实施路线图(慢做,12 个月)

### Sprint 0 · 框架对齐(本周,3-5 天)

| # | 任务 | 文档 |
|---|---|---|
| 0.1 | 写本文档 v0.1 | DATA_GOVERNANCE_FRAMEWORK.md ✅ |
| 0.2 | 写 DATA_CATALOG.md 初稿(自动生成器 + 当前 16 表) | Pillar 1 |
| 0.3 | 写 DATA_VERIFICATION_STANDARD.md 三道闸 SOP | Pillar 4 |
| 0.4 | 引入 yoyo-migrations,把现有 schema.sql 转 baseline migration | Pillar 2 |
| 0.5 | model_canonical 加 5 件套治理字段(优先级最高,因为最稀缺) | Pillar 3 |

### Sprint 1 · 字段加固(2-4 周)

| # | 任务 |
|---|---|
| 1.1 | 16 表逐个加治理 5 件套(分批,每周 3-4 表) |
| 1.2 | 引入 raw_snapshots evidence 存储 + cron |
| 1.3 | 写 gate_in_schema_check + gate_in_source_whitelist |
| 1.4 | DATA_LINEAGE.md 起草(对标 OpenLineage) |

### Sprint 2 · 验证闸口(4-8 周)

| # | 任务 |
|---|---|
| 2.1 | gate_curate_cross_source.py(价格双源对齐) |
| 2.2 | gate_curate_zscore.py(异常检测) |
| 2.3 | gate_curate_diff_alert.py(历史突变) |
| 2.4 | leak_revalidation.py(凭据失效回写) |
| 2.5 | candidate_sanity_check.py(候选晋升) |

### Sprint 3 · SLO 与质量度量(8-12 周)

| # | 任务 |
|---|---|
| 3.1 | DATA_SLO.md 定稿 |
| 3.2 | quality_runner.py 跑五大维度 |
| 3.3 | data_quality_metric 表落地 + 微信告警 |
| 3.4 | UI 加 "数据质量分" 卡片 |

### Sprint 4 · 生命周期 & 状态(12-20 周)

| # | 任务 |
|---|---|
| 4.1 | DATA_LIFECYCLE.md 定稿 |
| 4.2 | 16 表加 status / status_since / status_reason |
| 4.3 | UI 区分 published / probed / disputed |

### Sprint 5 · 可观测性(20-26 周)

| # | 任务 |
|---|---|
| 5.1 | governance_health.json + dashboard |
| 5.2 | 治理告警通道 |

### Sprint 6 · 归档 & 隐私(26-40 周)

| # | 任务 |
|---|---|
| 6.1 | DATA_RETENTION_POLICY.md |
| 6.2 | DATA_PRIVACY_AND_LICENSE.md |
| 6.3 | cold 存储 + TTL 自动化 |

### Sprint 7 · 自检 & 自进化(40-52 周)

| # | 任务 |
|---|---|
| 7.1 | 治理体系本身的"治理审计" — 每季度对 9 大支柱评分 |
| 7.2 | 行业对标:对照 dbt / OpenLineage / DAMA-DMBOK 找差距 |
| 7.3 | 治理标准外发(blog + GitHub) |

---

## 6. 不可逆决定(治理底线,定了不再变)

1. **每条数据五件套** — `source / method / fetched_at / verified_at / evidence_ref`,缺一不入库
2. **schema 走 migration** — 没 migration 的 ALTER 视为事故
3. **多源决定** — 单源永远只 suspicious,不删
4. **DELETE 必先 INSERT _trash** — 任何生产 DELETE 必带 trash 备份
5. **治理字段不可降级** — 已有 verified 的表不能再回到无 verified
6. **抽检 5% 强制** — 全自动 = 全自动被骗
7. **凭据级数据永不入主 DB** — Leak Radar 独立库,主 DB 永不见完整 key
8. **License 与商业转售边界永久闭源决定**(本文档外不可声明开放)

---

## 7. 关联标准映射

| 已有标准 | 在本框架的位置 |
|---|---|
| MODEL_DATA_STANDARD.md | Pillar 3 model_canonical 治理 |
| CATALOG_STANDARD.md | Pillar 2 SPU/SKU schema |
| PRICE_DATA_PIPELINE_STANDARD.md | Pillar 4 价格闸口 |
| COLLISION_CLASSIFICATION_STANDARD.md | Pillar 4 model_alias 闸口 |
| DATA_QUALITY_AUDIT_STANDARD.md | Pillar 5 质量度量(并入) |
| PROVIDER_STATUS_STANDARD.md | Pillar 6 生命周期 |
| FRAMEWORK_FINGERPRINT.md | Pillar 4 协议检测闸口 |

| 待新增标准 | Pillar |
|---|---|
| DATA_CATALOG.md(自动生成) | 1 |
| SCHEMA_EVOLUTION_STANDARD.md | 2 |
| DATA_LINEAGE.md | 3 |
| DATA_VERIFICATION_STANDARD.md | 4 |
| DATA_SLO.md | 5 |
| DATA_LIFECYCLE.md | 6 |
| DATA_PRIVACY_AND_LICENSE.md | 7 |
| DATA_RETENTION_POLICY.md | 9 |

---

## 8. 行业对标(给方法论加锚)

| 来源 | 我们借鉴的 |
|---|---|
| **dbt** | 数据 lineage + tests + docs(Pillar 1/3/5) |
| **Great Expectations** | 数据验证套件(Pillar 4/5) |
| **OpenLineage** | 数据血缘统一规范(Pillar 3) |
| **DAMA-DMBOK** | 治理 9 大职能框架(本文档骨架) |
| **Google Data Quality Whitepaper** | 5 维度质量(Pillar 5) |
| **Airbnb Dataportal** | 资产清单(Pillar 1) |
| **Lyft Amundsen** | 字典型资产管理(Pillar 1/3) |
| **Uber DataBook** | data ownership 模型(Pillar 1) |
| **Yelp data infrastructure** | data mesh 域划分(Pillar 6) |
| **Spotify Backstage** | catalog as code(Pillar 1) |

---

## 9. 退出条件(治理项目什么时候算"建成")

- 9 个 Pillar SLO 全部 ≥ 12 个月目标值
- 16 表 100% 带治理 5 件套
- 三道闸 100% 覆盖每张表
- 治理 dashboard 自动化跑 ≥ 90 天稳定
- 任何成员 5 分钟能回答"这条数据是谁/什么时候/怎么验"

到那时,这份文档会从 "总纲" 改为 "运维手册"。

---

**核心一句:** 数据治理不是写一堆脚本,**而是建立 "每条数据带身份证、每次变更走 migration、每个产出过三道闸、每个 SLO 有告警、每个状态有生命周期" 的体系。本文档定 What / Why,具体 How 在 9 个子标准文档慢慢做。**
