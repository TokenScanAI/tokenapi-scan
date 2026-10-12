# TokenAPI Scan · 数据资产清单（DATA_CATALOG）

自动生成于：2026-10-12 01:00 UTC（脚本 `scripts/governance/build_data_catalog.py`）
状态：本文档每周一 09:00 cron 自动刷新；**禁止手写**。
关联：DATA_GOVERNANCE_FRAMEWORK.md Pillar 1

## 0. 治理字段说明

五件套(Pillar 3):`source · method · fetched_at · verified_at · evidence_ref`
扩展信号:`updated_at · status · confidence · verified`

| Level | 含义 |
|---|---|
| **A** | 五件套 ≥ 4 + updated_at,**入产标杆** |
| **B** | 五件套 ≥ 3,**可用** |
| **C** | 有部分治理字段,**待加固** |
| **D** | 0 个五件套字段,**优先治理** |

---

## 1. 汇总

- 数据库:8 个
- 表:61  视图:2
- 五件套总覆盖率:**11.1%**
- 治理等级分布:A=4 / B=0 / C=19 / D=38

**北极星指标:** 12 个月内表 100% 达到 A 级。

---

## 2. 各表详细

### DB `data_lake.db`

| 表 | 行数 | 列数 | source | method | fetched_at | verified_at | evidence_ref | updated_at | 等级 |
|---|---|---|---|---|---|---|---|---|---|
| `data_snapshots` | 263 | 10 | — | — | ✅ | — | — | — | **C** |
| `data_sources` | 69 | 18 | — | ✅ | — | — | — | ✅ | **C** |
| `data_extractions` | 21027 | 11 | — | — | — | — | — | — | **D** |
| `fetch_health` | 69 | 11 | — | — | — | — | — | ✅ | **C** |
| `model_alias` | 614 | 6 | — | — | — | — | — | — | **D** |
| `model_canonical` | 324 | 9 | — | — | — | — | — | ✅ | **C** |
| `our_indices` | 1380 | 9 | — | — | — | — | — | — | **D** |
| `parser_runs` | 26 | 10 | — | — | — | — | — | — | **D** |

### DB `lab_features.db`

| 表 | 行数 | 列数 | source | method | fetched_at | verified_at | evidence_ref | updated_at | 等级 |
|---|---|---|---|---|---|---|---|---|---|
| `competitor_candidates` | 52 | 8 | ✅ | — | — | — | — | — | **C** |
| `competitor_watch` | 10156 | 13 | — | — | ✅ | — | — | — | **C** |
| `notices` | 10 | 10 | — | — | ✅ | — | — | — | **C** |
| `capability_promotion_queue` | 1 | 6 | — | — | — | — | — | — | **D** |
| `checkins` | 0 | 4 | — | — | — | — | — | — | **D** |
| `detection_capability_snapshot` | 286 | 9 | — | — | — | — | — | — | **D** |
| `feature_incubation` | 2844 | 15 | — | — | — | — | — | — | **D** |
| `iq_radar` | 280 | 9 | — | — | — | — | — | — | **D** |
| `key_test_log` | 0 | 9 | — | — | — | — | — | — | **D** |
| `redeem_codes` | 0 | 7 | — | — | — | — | — | — | **D** |
| `trial_keys` | 0 | 8 | — | — | — | — | — | — | **D** |
| `users` | 0 | 7 | — | — | — | — | — | — | **D** |

### DB `<internal-pipeline>.db`

### DB `push_queue.db`

### DB `tokenapi.db`

| 表 | 行数 | 列数 | source | method | fetched_at | verified_at | evidence_ref | updated_at | 等级 |
|---|---|---|---|---|---|---|---|---|---|
| `detection` | 108604 | 23 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **A** |
| `model_alias` | 6301 | 13 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **A** |
| `model_canonical` | 5719 | 19 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **A** |
| `price` | 21028 | 18 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **A** |
| `news_items` | 2227 | 9 | ✅ | — | ✅ | — | — | — | **C** |
| `trending_keywords` | 22365 | 11 | ✅ | — | ✅ | — | — | — | **C** |
| `authority_map` | 917 | 11 | — | — | — | ✅ | — | — | **C** |
| `price_history_snapshot` | 1609519 | 10 | ✅ | — | — | — | — | — | **C** |
| `provider_model_support` | 150 | 6 | ✅ | — | — | — | — | — | **C** |
| `_yoyo_log` | 10 | 8 | — | — | — | — | — | — | **D** |
| `_yoyo_migration` | 10 | 3 | — | — | — | — | — | — | **D** |
| `_yoyo_version` | 1 | 2 | — | — | — | — | — | — | **D** |
| `catalog_metric` | 92 | 9 | — | — | — | — | — | — | **D** |
| `codex_iq_models` | 6 | 6 | — | — | — | — | — | — | **D** |
| `codex_iq_scores` | 379 | 12 | — | — | — | — | — | — | **D** |
| `egress_channel_matrix` | 21 | 11 | — | — | — | — | — | — | **D** |
| `framework_registry` | 243 | 11 | — | — | — | — | — | — | **D** |
| `health_snapshot` | 103 | 7 | — | — | — | — | — | — | **D** |
| `leak_report_types` | 6 | 5 | — | — | — | — | — | — | **D** |
| `leak_reports` | 1 | 16 | — | — | — | — | — | ✅ | **C** |
| `model_popularity` | 5719 | 8 | — | — | — | — | — | ✅ | **C** |
| `model_sku` | 5450 | 9 | — | — | — | — | — | ✅ | **C** |
| `model_spu` | 5360 | 6 | — | — | — | — | — | ✅ | **C** |
| `normalize_run` | 1500 | 8 | — | — | — | — | — | — | **D** |
| `notification` | 0 | 6 | — | — | — | — | — | — | **D** |
| `operations_signals` | 386 | 10 | — | — | — | — | — | — | **D** |
| `provider` | 422 | 17 | — | — | — | — | — | ✅ | **C** |
| `ranking_snapshot` | 0 | 5 | — | — | — | — | — | — | **D** |
| `seo_report` | 0 | 4 | — | — | — | — | — | — | **D** |
| `water_rate_v2` | 184 | 24 | — | — | — | — | — | — | **D** |
| `yoyo_lock` | 0 | 3 | — | — | — | — | — | — | **D** |

**视图:** `v_price_canonical`, `v_provider_health_7d`

### DB `tokenscan.db`

### DB `$REPO_ROOT.db`

### DB `traffic_sources.db`

| 表 | 行数 | 列数 | source | method | fetched_at | verified_at | evidence_ref | updated_at | 等级 |
|---|---|---|---|---|---|---|---|---|---|
| `ai_referral_stats` | 16 | 4 | ✅ | — | — | — | — | — | **C** |
| `referer_stats` | 694 | 5 | ✅ | — | — | — | — | — | **C** |
| `ai_crawler_stats` | 1329 | 4 | — | — | — | — | — | — | **D** |
| `bing_index` | 419 | 3 | — | — | — | — | — | — | **D** |
| `country_stats` | 4477 | 3 | — | — | — | — | — | — | **D** |
| `gsc_snapshots` | 5 | 11 | — | — | — | — | — | — | **D** |
| `search_index_compare` | 419 | 4 | — | — | — | — | — | — | **D** |
| `similarweb_stats` | 0 | 10 | — | — | — | — | — | — | **D** |
| `tranco_ranks` | 190 | 3 | — | — | — | — | — | — | **D** |
| `utm_click_stats` | 0 | 4 | — | — | — | — | — | — | **D** |

---

## 3. 优先治理目标(D 级表清单)

| DB | 表 | 行数 | 推荐动作 |
|---|---|---|---|
| `data_lake.db` | `data_extractions` | 21027 | Sprint 1 加五件套 |
| `data_lake.db` | `model_alias` | 614 | Sprint 1 加五件套 |
| `data_lake.db` | `our_indices` | 1380 | Sprint 1 加五件套 |
| `data_lake.db` | `parser_runs` | 26 | Sprint 1 加五件套 |
| `lab_features.db` | `capability_promotion_queue` | 1 | Sprint 1 加五件套 |
| `lab_features.db` | `checkins` | 0 | 暂缓(0 行) |
| `lab_features.db` | `detection_capability_snapshot` | 286 | Sprint 1 加五件套 |
| `lab_features.db` | `feature_incubation` | 2844 | Sprint 1 加五件套 |
| `lab_features.db` | `iq_radar` | 280 | Sprint 1 加五件套 |
| `lab_features.db` | `key_test_log` | 0 | 暂缓(0 行) |
| `lab_features.db` | `redeem_codes` | 0 | 暂缓(0 行) |
| `lab_features.db` | `trial_keys` | 0 | 暂缓(0 行) |
| `lab_features.db` | `users` | 0 | 暂缓(0 行) |
| `tokenapi.db` | `_yoyo_log` | 10 | Sprint 1 加五件套 |
| `tokenapi.db` | `_yoyo_migration` | 10 | Sprint 1 加五件套 |
| `tokenapi.db` | `_yoyo_version` | 1 | Sprint 1 加五件套 |
| `tokenapi.db` | `catalog_metric` | 92 | Sprint 1 加五件套 |
| `tokenapi.db` | `codex_iq_models` | 6 | Sprint 1 加五件套 |
| `tokenapi.db` | `codex_iq_scores` | 379 | Sprint 1 加五件套 |
| `tokenapi.db` | `egress_channel_matrix` | 21 | Sprint 1 加五件套 |
| `tokenapi.db` | `framework_registry` | 243 | Sprint 1 加五件套 |
| `tokenapi.db` | `health_snapshot` | 103 | Sprint 1 加五件套 |
| `tokenapi.db` | `leak_report_types` | 6 | Sprint 1 加五件套 |
| `tokenapi.db` | `normalize_run` | 1500 | Sprint 1 加五件套 |
| `tokenapi.db` | `notification` | 0 | 暂缓(0 行) |
| `tokenapi.db` | `operations_signals` | 386 | Sprint 1 加五件套 |
| `tokenapi.db` | `ranking_snapshot` | 0 | 暂缓(0 行) |
| `tokenapi.db` | `seo_report` | 0 | 暂缓(0 行) |
| `tokenapi.db` | `water_rate_v2` | 184 | Sprint 1 加五件套 |
| `tokenapi.db` | `yoyo_lock` | 0 | 暂缓(0 行) |
| `traffic_sources.db` | `ai_crawler_stats` | 1329 | Sprint 1 加五件套 |
| `traffic_sources.db` | `bing_index` | 419 | Sprint 1 加五件套 |
| `traffic_sources.db` | `country_stats` | 4477 | Sprint 1 加五件套 |
| `traffic_sources.db` | `gsc_snapshots` | 5 | Sprint 1 加五件套 |
| `traffic_sources.db` | `search_index_compare` | 419 | Sprint 1 加五件套 |
| `traffic_sources.db` | `similarweb_stats` | 0 | 暂缓(0 行) |
| `traffic_sources.db` | `tranco_ranks` | 190 | Sprint 1 加五件套 |
| `traffic_sources.db` | `utm_click_stats` | 0 | 暂缓(0 行) |

---

## 4. 标杆表(A/B 级,作为治理模板)

| DB | 表 | 等级 | 五件套字段 |
|---|---|---|---|
| `tokenapi.db` | `detection` | **A** | source, method, fetched_at, verified_at, evidence_ref |
| `tokenapi.db` | `model_alias` | **A** | source, method, fetched_at, verified_at, evidence_ref |
| `tokenapi.db` | `model_canonical` | **A** | source, method, fetched_at, verified_at, evidence_ref |
| `tokenapi.db` | `price` | **A** | source, method, fetched_at, verified_at, evidence_ref |

---

## 5. 操作指引

- 给一张表加治理字段:见 `DATA_GOVERNANCE_FRAMEWORK.md` Pillar 3
- 走 Gate-IN 写入:见 `DATA_VERIFICATION_STANDARD.md` §2
- 评估表治理等级:跑本脚本 `python3 scripts/governance/build_data_catalog.py`

