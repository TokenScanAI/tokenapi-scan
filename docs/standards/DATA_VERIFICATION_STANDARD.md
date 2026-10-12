# TokenAPI Scan · 数据验证标准（DATA_VERIFICATION_STANDARD）v1.0

定稿日期：2026-06-26　状态：v1.0
关联：DATA_GOVERNANCE_FRAMEWORK.md Pillar 4 · DATA_CATALOG.md · DATA_LINEAGE.md

---

## 0. 目的

> "数据进库、入产、对外发布,每一步必须过明确的闸口；每条闸的输入 / 校验项 / 通过条件 / 失败处置必须可执行,不是宣言。"

本文档把治理 9 大支柱里的 **Pillar 4(验证 & 闸口)** 落地为可在 cron / CI 里跑的 SOP。
任何新数据流入库前必须先在本文档加一行,声明它要过哪几道闸。

---

## 1. 三道闸总览

```
              外部源 / 抓取器 / 人工
                     │
            ┌────────▼────────┐
            │   Gate-IN       │   入库闸:写入 raw 表前
            │   schema/src    │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │  Gate-CURATE    │   治理闸:raw → cross_verified
            │  probe/跨源     │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │  Gate-OUT       │   发布闸:对外 API / 排名
            │  SLO/抽检       │
            └────────┬────────┘
                     │
                用户 / Agent
```

| 闸 | 谁触发 | 跑频 | 失败处置 |
|---|---|---|---|
| Gate-IN | 每次写入 | 同步阻塞 | 拒绝入库 + 告警 |
| Gate-CURATE | cron 每日 / 每 6h | 异步 | 标 `disputed/quarantined`,不删 |
| Gate-OUT | 每次发布 / 每周抽检 | 同步 + 异步 | 阻断发布 + 抽检报告 |

---

## 2. Gate-IN(入库闸)

### 2.1 校验项

| 校验 | 通过条件 | 失败动作 |
|---|---|---|
| Schema 合法 | 所有 NOT NULL 字段非空,类型匹配 | 拒绝 + ValueError |
| 来源白名单 | `source` 在 `data_sources.yaml` 注册 | 拒绝 + 告警 |
| 五件套齐全 | `source / method / fetched_at / verified_at / evidence_ref` 非空 | 拒绝 + 告警 |
| 主键已存在 | 走 UPSERT 而非 INSERT | UPSERT |
| 黑名单过滤 | 不在 `blocklist.yaml` | 拒绝 + audit log |
| evidence 落地 | `evidence_ref` 指向 sha256 文件实存 | 拒绝(强一致) |

### 2.2 实现路径

`scripts/governance/gate_in.py` 提供唯一写入 API:`gate_in.write(table, row)`,
其它代码必须走这个 API,**绕过会被 git pre-commit 检出**。

注册表 `scripts/governance/gate_in_registry.yaml`:

```yaml
provider:
  required_fields: [provider_id, name, source, method, fetched_at]
  source_whitelist: [human, auto_discover, openrouter_meta]
  evidence_required: true

model_canonical:
  required_fields: [canonical_id, source, method, fetched_at, verified_at, evidence_ref]
  source_whitelist: [openrouter_meta, litellm_meta, human, normalize_run]
  evidence_required: true

price:
  required_fields: [provider_id, model_canonical_id, price_input, price_output, source, fetched_at]
  source_whitelist: [openrouter, litellm, "site:*"]
  evidence_required: true
```

### 2.3 数据源注册(`data_sources.yaml`)

```yaml
openrouter:
  trust_tier: A          # A=权威 B=次权威 C=社区 D=低信
  refresh_cadence: 6h
  evidence_format: raw_json
  owner: cron@price-sync

litellm:
  trust_tier: A
  refresh_cadence: 6h
  evidence_format: raw_json
  owner: cron@price-sync

"site:*":
  trust_tier: B
  refresh_cadence: 12h
  evidence_format: raw_response
  owner: cron@daily_probe

tokenapi-legacy:
  trust_tier: D          # 仅候选发现源,不进 price/model_canonical
  refresh_cadence: 24h
  evidence_format: html
  owner: cron@daily_site_candidates
  brand_cleanup_phase: true
  enabled_by_default: false
```

---

## 3. Gate-CURATE(治理闸)

### 3.1 跨源对齐(`gate_curate_cross_source.py`)

适用:`price` / `model_canonical` / `provider`。

| 项 | 规则 |
|---|---|
| 跨源数 | ≥ 2 个 trust_tier=A 源,且 ≥ 1 个 site:* 源 |
| 价格分歧 | 相同 (provider, canonical_id),OpenRouter vs LiteLLM diff ≤ 10% → `cross_verified`;否则 `disputed` |
| 模型元数据分歧 | canonical_id 在两源都存在 & context_window diff ≤ 5% → `cross_verified` |

### 3.2 异常检测(`gate_curate_zscore.py`)

| 项 | 规则 |
|---|---|
| 价格 z-score | 同 canonical_id 跨 provider,中位数 ± 2σ 之外 → `suspicious` |
| 价格历史突变 | 同 (provider, canonical_id) 24h diff > 50% → 告警 + `disputed` |
| 检测频率突变 | 单 provider 24h detection 数 < 历史 P10 → `staleness_warning` |

### 3.3 探测回写(`gate_curate_probe.py`)

| 数据 | 探测项 | 失败动作 |
|---|---|---|
| provider | DNS+TCP+TLS+HTTP+endpoint 五连测 | service_status=`unreachable`,**不删** |
| price | endpoint 实测可返回 | source=`stale`,标 |
| leak_radar hits | 失效复测 | status=`revoked`,UI 隐藏 |

### 3.4 候选晋升(`candidate_sanity_check.py`)

candidates → seed_providers 晋升前必须过:

1. DNS 解析 2 节点交叉一致
2. HTTP 200 真站点(非 parking / 占位)
3. 公开 endpoint 有响应(`/api/pricing` 或 `/v1/models`)
4. 同域已存在 → 不晋升(去重)
5. 黑名单匹配 → 拒绝晋升
6. **抽检 5%:人工 / agent 看一眼,确认非已知作弊站**

---

## 4. Gate-OUT(发布闸)

### 4.1 排名 / 红黑榜发布前

| 项 | 规则 |
|---|---|
| SLO 通过 | 数据 timeliness < 24h,completeness ≥ SLO 阈值 |
| 状态过滤 | 仅 `cross_verified` / `published` 进 ranking,`raw/probed/disputed/quarantined` 不进 |
| 抽检 5% | 每周一份 audit 报告 |
| diff 报告 | 与上一版排名 diff > 30% → 阻断 + 人审 |

### 4.2 公开 API 响应前

| 项 | 规则 |
|---|---|
| 字段脱敏 | SENSITIVE / FORBIDDEN 字段不出 |
| 速率限制 | 免费 60/h,付费 600/h,企业 6000/h |
| 水印数据 | 月度公开快照含少量噪声标记位(可追溯转售) |
| License 提示 | response header 带 `X-License: CC-BY-NC-4.0` |

### 4.3 数据快照导出前

| 项 | 规则 |
|---|---|
| 仅导 cross_verified+ | published / cross_verified 状态 |
| evidence_ref 脱敏 | 不导出 raw_snapshots 路径 |
| 字段过滤 | 内部诊断字段(`raw_json`, `evidence_ref`)剔除 |
| 完整性签名 | tar.gz + sha256 + GPG 签名 |

---

## 5. 失败处置矩阵

| 闸 | 失败 | 不删 | 标 | 告警 |
|---|---|---|---|---|
| IN-Schema | 拒绝 | — | — | ✓ |
| IN-Source | 拒绝 | — | — | ✓ |
| IN-Blocklist | 拒绝 | — | — | ✓ |
| CURATE-CrossSource | 入库 | ✓ | `disputed` | dashboard |
| CURATE-ZScore | 入库 | ✓ | `suspicious` | dashboard |
| CURATE-Probe | 入库 | ✓ | `unreachable` | 微信(provider 级) |
| CURATE-Sanity | 不晋升 | ✓ | `raw` | log |
| OUT-SLO | 阻断 | ✓ | — | 微信(立即) |
| OUT-Diff | 阻断 | ✓ | — | 微信(立即) |
| OUT-Sample | 报告 | ✓ | — | 周报 |

**铁律:Gate-IN 拒绝才不入库,Gate-CURATE / OUT 失败一律标记不删。**

---

## 6. 治理可观测性(给闸装监控)

`web_data/governance/gate_health_<YYYY-MM-DD>.json`:

```json
{
  "date": "2026-06-26",
  "gate_in": {"total": 12345, "rejected": 23, "rejection_rate": 0.0019},
  "gate_curate_cross_source": {"checked": 1181, "cross_verified": 1102, "disputed": 79},
  "gate_curate_zscore": {"checked": 3807, "suspicious": 12},
  "gate_curate_probe": {"providers": 117, "unreachable": 8},
  "gate_out_slo": {"published_count": 117, "blocked": 0},
  "gate_out_diff": {"ranking_diff_pct": 4.2, "blocked": 0}
}
```

告警阈值:`rejection_rate > 5%` / `disputed > 10%` / `unreachable > 15%` / `slo_blocked > 0` → 微信。

---

## 7. SOP 验收清单

新数据流接入,必须按以下顺序执行,否则不合入:

```
[ ] 1. data_sources.yaml 注册源 + trust_tier
[ ] 2. gate_in_registry.yaml 注册表 + 必填字段
[ ] 3. evidence 落地路径定义(web_data/raw_snapshots/<sha256>.json)
[ ] 4. 走 gate_in.write() 写入,禁直连 sqlite execute INSERT
[ ] 5. CURATE 阶段挂 cron(若适用)
[ ] 6. OUT 阶段挂 SLO 检查(若进排名)
[ ] 7. 在 DATA_CATALOG.md 加一行
[ ] 8. 在 DATA_LINEAGE.md 加流向图
```

---

## 8. 不可逆决定

1. **Gate-IN 五件套缺一不入库** — `source / method / fetched_at / verified_at / evidence_ref`
2. **失败一律不删** — Gate-CURATE / OUT 失败仅标记,不 DELETE
3. **单源永远只 `suspicious`,不杀** — 两源 disputed,三源 quarantined
4. **evidence 强一致** — sha256 文件不存在 → Gate-IN 拒绝
5. **DELETE 必先 INSERT _trash** — 任何 production DELETE 必带备份
6. **抽检 5% 强制** — 全自动 = 全自动被骗
7. **绕过 gate_in.write() 写入 = 事故**
