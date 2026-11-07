# TokenAPI Scan · 数据资产清单（DATA_CATALOG）

> **Pillar 1 落地文档 (DATA_GOVERNANCE_FRAMEWORK §4 Pillar 1)。** 把全站数据资产按 9 大类登记成台账,每条记录"是什么 / 在哪 / 谁拥有 / 治理等级 / 下一步动作"。
> **状态:** v0.3 (2026-06-27) — M1/M2/M3 三张表 ALTER 落地后刷新。
> **更新模式:** 9 类资产分两轨——
>   - **DB 表** 视角由 `scripts/governance/build_data_catalog.py` 每周一 09:00 自动刷新到 `DATA_CATALOG.auto.md`(脚本输出已改名,**不再覆盖本文档**)。
>   - **9 类资产 inventory + 责任方 / 决策项** 由本文档手维护(决策性内容,不可机器覆盖)。

---

## 0. 治理等级速查

| Level | 含义 | 五件套门槛 |
|---|---|---|
| **A** | 入产标杆 | source/method/fetched_at/verified_at/evidence_ref 至少 4 项 + updated_at |
| **B** | 可用 | 五件套 ≥ 3 项 |
| **C** | 待加固 | 有部分治理字段 |
| **D** | 优先治理 | 0 个五件套字段 |

五件套定义参见 `DATA_LINEAGE.md` §1.1-1.2。

---

## 1. 资产汇总(2026-06-27 实测,M1/M2/M3 后)

| # | 资产类 | 物理位置 | 体量 | 等级分布 | 责任方 |
|---|---|---|---|---|---|
| 1 | **结构化 SoR(系统记录)** | `web_data/db/tokenapi.db` 等 3 DB | 28 表 + 2 视图 / 19K 行 | **A=4** / B=0 / C=7 / D=17 | TUI agent |
| 2 | **协议探测 raw** | `web_data/jobs/<protocol>/` | 925 文件 / 10.7 MB | C(无五件套但有 timestamp) | <internal-pipeline> |
| 3 | **健康快照** | `web_data/health_checks/*.json` | 40 文件 / 753 KB | C | cron health_check |
| 4 | **排名/路由快照** | `web_data/ranking/`, `router_sample_matrix*/` | 121 文件 / 6.4 MB | C | cron ranking_build |
| 5 | **爬虫产物** | `web_data/crawler/`, `crawl/`, `enrichment/` | 38 文件 / 7.6 MB | D | tools_dev/<internal-pipeline> |
| 6 | **配置 / 字典 (source of governance)** | `<INTERNAL>/*.yaml`, `docs/standards/` | 13 文件 | n/a (元数据) | TUI agent (手维护) |
| 7 | **通知 / 推送队列** | `web_data/notifications/`, `push_queue*/` | 55 文件 / 105 KB | D | notification_store |
| 8 | **SEO / GSC 报告** | `web_data/seo_reports/` | 75 文件 / 119 KB | D | GSC pipeline |
| 9 | **审计 / 备份 / 归档** | `web_data/access_logs/`, `$HOME/tokenscan_backups/` | 8 + N 文件 / 9.3+ MB | n/a | runtime + 手维护 |

**总磁盘:** `web_data/` = 86 MB。
**五件套覆盖率:** **从 10.7% → 待 auto 脚本重跑刷新**(M1/M2/M3 加 method/verified_at/evidence_ref/status_*/updated_at 共 7 列 × 3 表 = 21 列)。
**北极星指标:** 12 个月内表 100% 达到 A 级,文件类资产 80% 写入路径走"统一 evidence/snapshot 落盘"(参见 §3.2 决策项 8)。

---

## 2. 各资产类详细

### 资产 1 · 结构化 SoR(28 表 / 2 视图)

详见 `DATA_CATALOG.auto.md`(脚本生成,每周一 09:00 刷新)。
**关键摘要(2026-06-27 实测 · M1/M2/M3 后):**

| DB | 表数 | 行数合计 | 关键表(行数) |
|---|---|---|---|
| `tokenapi.db` | 20 表 + 2 视图 | ~18,500 行 | detection(7503) · price(3807) · model_alias(1370) · model_canonical(1260) · model_sku(1181) · model_spu(1151) · authority_map(476) · framework_registry(243) · normalize_run(132) · provider(117) |
| `lab_features.db` | 8 表 | ~700 行 | competitor_watch(402) · iq_radar(280) · notices(10) |
| `<internal-pipeline>.db` | (独立) | — | <internal-pipeline> 自有 db,见 skill `leak-radar-realtime-collection-pipeline-2026-06-23.md` |

**A/B 级标杆(M1/M2/M3 后):**
- `model_canonical`(A): 18 列五件套全套(M0 模板)
- `price`(A 待 auto 重判): 18 列含五件套 + status/status_since/status_reason/updated_at,3807 行全 status='legacy_unverified',Sprint 1 加 evidence_ref 即可保 A 级写入
- `model_alias`(A 待 auto 重判): 13 列含五件套 + evidence(legacy 双列保留) + 状态机,1370 行 = 834 legacy_unverified + 536 verified(按 verified_at 智能分流)
- `detection`(A 待 auto 重判): 23 列含五件套 + status,7503 行 = 1132 legacy_unverified + 1418 probe_failed + 4953 probe_ok

**D 级优先治理(8 表非 0 行):** iq_radar(280) · framework_registry(243) · normalize_run(132) · catalog_metric(14) · health_snapshot(8) · _yoyo_* 3 表

### 资产 2 · 协议探测 raw(jobs/)
- 路径: `web_data/jobs/{anthropic,openai,gemini}/<date>/<job_id>.json`
- 容量: 925 文件 / 10.7 MB
- 内容: 单次探测请求/响应原始数据(API key 已 mask)
- 治理: 文件名含时间戳,**无五件套元数据**,等级 C
- 改造方向: 入 SoR 时落 `evidence_ref → web_data/raw_snapshots/<date>/<sha>.json`,job-id 写 `detection.evidence_ref`(M3 已开列,待写入侧改造)

### 资产 3 · 健康快照(health_checks/)
- 路径: `web_data/health_checks/<date>.json` + `web_data/health/`
- 容量: 40+ 文件 / 753 KB
- 治理: 文件 mtime 即 fetched_at,**进 health_snapshot 表后丢失 evidence 引用**,等级 C
- 改造方向: M5 `health_snapshot` ALTER 加 evidence_ref 指回 `web_data/health_checks/<date>.json`

### 资产 4 · 排名 / 路由 / 增长(ranking + router_*)
- 路径: `web_data/ranking/{records,seed_history,llm_drafts,candidate_history}/`,`web_data/router_sample_matrix{,_prod}/`,`web_data/router_growth/`
- 容量: 121 文件 / 6.4 MB
- 治理: **大头**,写入端混乱(LLM draft、人工种子、生产输出三种来源混存),等级 C
- 改造方向: M6 `ranking_snapshot` ALTER 加五件套 + 文件名加 source 前缀(`llm-`/`seed-`/`prod-`)

### 资产 5 · 爬虫产物(crawler + crawl + enrichment)
- 路径: `web_data/crawler/`(32 文件 / 7.5 MB)+ `web_data/crawl/`(3 文件)+ `web_data/enrichment/`(3 文件 / 84 KB)
- 治理: 等级 D — 文件级,无统一元数据
- 改造方向: 全部进 raw_snapshots/<date>/<sha>.json,SoR(price/detection) 行用 evidence_ref 指过来

### 资产 6 · 配置 / 字典(治理来源)
- 路径:
  - `<INTERNAL>/source_filters.yaml`(1.4 KB) — 数据源开关 + source_trust(trusted/verified/community/experimental/**blacklisted**)
  - `docs/standards/*.md`(13 文件 / 156 KB) — 治理规范文档
- 治理: **元数据**,本身不归 governance level
- 责任方: 手维护,Git 跟踪
- 红线: source_filters.yaml 任何改动必须落 plan(decision 文档),不允许直接生产改

### 资产 7 · 通知 / 推送队列
- 路径: `web_data/notifications/`(9 文件)+ `web_data/push_queue/`(2)+ `web_data/push_queue_archive/`(44 历史归档)
- 治理: `notification` 表 0 行(未启用 SoR),全部走文件,等级 D
- 改造方向: P2 期把 notification_store 写入 `notification` 表 + 落 source/method/sent_at/delivered_at

### 资产 8 · SEO / GSC 报告
- 路径: `web_data/seo_reports/`(75 文件 / 119 KB)
- 治理: `seo_report` 表 0 行(未启用 SoR),全部走文件,等级 D
- 改造方向: GSC pipeline 重做时入 SoR(skill `tokenapi-gsc-analysis`)

### 资产 9 · 审计 / 备份 / 归档
- 路径:
  - `web_data/access_logs/`(8 文件 / 9.3 MB) — Web 请求日志
  - `$HOME/tokenscan_backups/`(L1 外部) — 备份 tar.gz,含旧品牌归档包 883 KB
  - `web_data/governance/`(snapshot JSON,每日刷新)
  - `web_data/db/backups/`(M0 前两次 tokenapi_db 备份 + M1/M2/M3 前 `$HOME/tokenscan_backups/db_pre_lineage_20260626/`)
- 治理: 操作型,不参与 SoR 评级
- 红线: 备份必落本地,**禁用 git history 回滚**(历史含已弃用旧品牌版本)

---

## 3. 决策项(Open Loops,需逐条拍板)

> 这些决策影响后续 Sprint 1 执行,**不解决就推不下去**,按编号逐条解决。

| # | 决策项 | 候选 | 影响 | 状态 |
|---|---|---|---|---|
| 1 | `model_alias.evidence`(JSON-string)→ `evidence_ref`(raw_snapshot 路径) 数据回填策略 | (a) 一次性脚本回填+DROP evidence (b) 双列并行 6 月观察 | M2 migration 是否能立即完成 | **已选 (b)** — M2 已落 evidence_ref 列,双列并行,Sprint 2 再 DROP |
| 2 | `web_data/jobs/` 925 文件是否迁入 `raw_snapshots/<date>/<sha>/` | (a) 全迁(去重收益) (b) 保留+加 symlink | 磁盘 ~10MB / 写入端改造工作量 | **待定** |
| 3 | `ranking_snapshot` 表 0 行 — 是否启用 SoR | (a) 启用,文件转表 (b) 继续文件式,但加 manifest 表 | router 页查询性能 | **待定** |
| 4 | `<internal-pipeline>.db` 是否进 DATA_CATALOG | (a) 进(治理可见性) (b) 留独立(skill 已管) | 治理一致性 vs 隔离边界 | **倾向 (a) — 进 inventory 但不掺数据** |
| 5 | `web_data/seo_reports/` 是否进 SoR | (a) 入 `seo_report` 表 (b) 维持文件 | GSC pipeline 重做时机 | **挂起到 GSC pipeline P1** |
| 6 | `competitor_watch`(lab_features.db, 402 行) 是否走五件套 | (a) 加 (b) 保留 last_seen_at 即可 | 竞品监控数据可信度 | **倾向 (a)** |
| 7 | `framework_registry`(243 行) 内容审计 — 这表存什么、还在用吗 | 先 read 抽样 → 决定保留/废弃 | D 级表是否需要 ALTER | **待 R&D** |
| 8 | 文件资产统一 `evidence_store` 落盘(资产 2/3/4/5 全走) | 写 `src/governance/evidence_store.py` 接口 | 所有 scraper 写入路径改造 | **P0 进行中(本轮)** |

---

## 4. Sprint 1 (2-4 周) 待办映射

| 任务 | 涉及资产 | 关联 migration | 状态 |
|---|---|---|---|
| 五件套统一(M1-M3) | 资产 1 - price/model_alias/detection | 0003/0004/0005 | ✅ 已落 (2026-06-27) |
| evidence_store SDK | 资产 1 + 2 + 5 | n/a (代码) | 🟡 本轮在写 |
| auto catalog 升级:扫文件类(资产 2-9) | 全部 | 改 build_data_catalog.py 加 file scanner | ⏳ Sprint 2 |
| iq_radar / framework_registry 内容审计 | 资产 1 D 级 | 决策项 7 | ⏳ |
| jobs/ 文件去重统计 | 资产 2 | 决策项 2 探数据 | ⏳ |

---

## 5. 与其它文档关系

- **DATA_GOVERNANCE_FRAMEWORK.md** § Pillar 1 — 这是落地文档
- **DATA_LINEAGE.md** — Pillar 3 五件套字典,本文档引用
- **DATA_VERIFICATION_STANDARD.md** — Pillar 4 三道闸,与 governance level 评定挂钩
- **BRAND_INDEPENDENCE_AND_OSS_POLICY.md** — Layer 1/2/3 划分,**资产 6(配置/字典)对应 Layer 1 公开 / 资产 1-2(生产 SoR + raw)对应 Layer 3 闭源**
- **DATA_CATALOG.auto.md** — 脚本生成的纯表视角,本文档不重复

---

## 6. 变更记录

- **v0.3** (2026-06-27) — M1/M2/M3 落地 (price/model_alias/detection 加五件套+状态机),决策项 1 拍板 (b),决策项 8 进入实施。脚本输出改名 .auto.md 防误覆盖。
- **v0.2** (2026-06-26 23:42) — 重写为 9 类资产 inventory,加决策项 8 条,A/B 级标杆固化,与 Pillar 3 联动
- **v0.1** (2026-06-26 上午) — auto-only,纯 DB 视角(已归档为 DATA_CATALOG.auto.md)

---

## 7. 操作指引

- 跑一次 auto 刷新:`python3 scripts/governance/build_data_catalog.py`(输出 `DATA_CATALOG.auto.md` + `web_data/governance/data_catalog_snapshot_<date>.json`)
- 给一张表加五件套:见 `DATA_LINEAGE.md` §4 候选清单
- 加新资产类(超出 9 类)时:在 §1 汇总表加行 + §2 加段 + §3 看是否产生决策项
