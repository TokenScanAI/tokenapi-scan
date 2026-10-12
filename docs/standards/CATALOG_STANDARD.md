# Pillar 1 · Catalog Standard — 商品信息管理标准 (SPU / SKU / 库存)

> **本文件 = TokenAPI Scan 9 支柱治理框架第 1 支柱: Catalog**
>
> 任何\"模型聚合、商品列表、合并切分、模型子页\"的工作前**必须先读本文**.
> 历史代价: 5/24 用价格判同异把 gpt-5 / gpt-5-chat 合并, 删了 1 个 SPU 又恢复.

**文档位置**: `docs/standards/CATALOG_STANDARD.md` (本文件, v1.0)
**6/27 v1.0 增补**: §0 与 Pillar 2/3 接口段 + §7 自检 evidence 落点
**对应主规划**: `docs/plans/2026-06-26-data-governance-master.md` T2 Pillar 1
**关联**: Pillar 2 (Schema 权威) · Pillar 3 (Provenance) · Pillar 4 (Quality Audit)
**关联 skill**: `tokenapi-catalog-spu-sku` (执行细则) · `tokenapi-model-alignment` (撞名仲裁)

---

## §0 与 Pillar 2/3 接口 (强制)

**Pillar 2 字段**: SPU/SKU 表 schema 已固化到 `docs/standards/PILLAR_2_SCHEMA_AUTHORITY.md`,
列定义任何变更必须先在 Pillar 2 文档生效, 再改本文档执行流程.

**Pillar 3 七件套**: 当前 `model_spu` / `model_sku` 表是\"派生表\"(由 `build_catalog.py` 从
model_canonical / price 重算), provenance 简化为:
- `source`: 固定 `derived:build_catalog` (不是采集而是派生)
- `method`: 固定 `derive_catalog_v1`
- `fetched_at`: 写入派生表的时刻 (即 updated_at 列)
- `evidence_ref`: 当次构建的产物 `web_data/evidence/catalog/<run_id>.json`
- `status`: `active` (派生表每次 DELETE+INSERT, 没有 deprecated 概念)
- `verification_level`: `derived` (新增枚举值, 表示\"非采集, 派生表\")

**6/27 现状**: 派生表当前未带 source/method/evidence_ref 列, 待 Pillar 3 ALTER 上线后补全.

---

## 三层模型(对应电商概念)

> 把全网抓取的模型 + 价格数据,建成电商式的三层商品体系。
> 核心:SPU/SKU 边界客观可判(厂商命名规则 + 能力维度),不靠人选。
> 构建脚本 `scripts/catalog/build_catalog.py`,自进化闭环 `scripts/catalog/evolve_catalog.py`。

## 三层模型(对应电商概念)

| 层 | 概念 | 定义 | 本项目实例 |
|---|---|---|---|
| SPU | 标准商品单元 | 一个模型产品(同 family + 同参数规模 + 同代际) | gpt-5、codellama-34b、qwen2.5-coder-7b |
| SKU | 库存单元 | 可独立售卖/计费的接口或规格形态 | gpt-5 / gpt-5-chat;codellama-34b / -instruct |
| 库存 | 渠道报价 | 某 SKU 在某 provider 的当前价 | gpt-5-chat @ openrouter $1.25/$10 |

### 关键认知:SKU ≠ 用价格判同异
gpt-5 和 gpt-5-chat **同价**,但仍是两个 SKU(不同接口形态)。
"同价"只是定价巧合,**绝不能作为合并 SKU 的依据**。
合并只发生在"写法差异"层(qwen2p5 vs qwen2.5、CodeLlama-hf vs codellama),不跨接口形态。

## 客观切分规则(无人工)

### 1. 归一(normp)— 消除写法差异
- p→. 还原:`qwen2p5` → `qwen2.5`、`v1p5` → `v1.5`
- 大小写统一、`code-llama` → `codellama`
- `llama-vXpY` → `llama-X.Y`
- `-instruct-hf` → `-instruct`(hf 是同一 SKU 的命名变体)

### 2. SKU = normp(canonical_id) 去重
写法不同但归一后相同的,合并为一个 SKU(消除重复库存)。
6/20 实测:696 原始 canonical → 622 SKU(合并 67 个写法重复)。

### 3. SPU = SKU 剥接口形态后缀
剥 `-instruct`/`-chat`/`-it`/`-base` 得到 SPU 键。
6/20 实测:622 SKU → 594 SPU。

### 4. 厂商独立产品白名单(剥后缀会误并的,强制独立 SPU)
- `gpt-3.5-turbo-instruct`:OpenAI 独立补全模型,与 chat 行为/定价不同,独立 SPU。
- 未来发现同类(厂商文档声明为独立模型的"伪后缀")加入 `INDEP_PRODUCTS`。

### 5. 能力/规模维度天然分 SPU
mini/nano/不同参数规模(7b/32b/72b)= 不同模型 = 不同 SKU 串 → 自然落到不同 SPU。
无需特殊处理,normp 不剥这些。

## 数据表

- `model_spu`:spu_id / display_name / vendor / family / sku_count / updated_at
- `model_sku`:sku_id / spu_id / form / raw_ids(JSON) / provider_count / priced_count / min_input_price / max_input_price / updated_at
- `catalog_metric`:每期自检指标快照(自进化基线)

## 只读 API(web/server.py,FastAPI)

```
GET /api/catalog/spu?vendor=&q=&limit=&offset=     # 商品列表,按 SKU 数排序
GET /api/catalog/spu/{spu_id}                       # SPU 详情:SKU + 逐渠道库存价
```
表不存在时优雅降级返回 `catalog not built`,只读连接 `mode=ro`,不影响主服务。

## 自进化闭环(不是每次全量重报,而是攒指标+自比对)

```bash
python3 scripts/catalog/evolve_catalog.py            # 干跑,打印本期 vs 上期指标
python3 scripts/catalog/evolve_catalog.py --commit    # 重建目录+记快照+(异动时)写告警
```

每期记录 6 项指标到 catalog_metric,与上期对比,**只在退化/异动时告警**:
- 撞名归类需人工(D类)> 0 → 客观判据没覆盖,需补规则
- 出现孤儿 canonical(没挂进任何 SKU)
- 陈旧报价**新增**(超 14 天未更新,只报增量不报存量,防噪音)
- SKU 数单次波动 > 5%(可能抓取出错或归一规则漂移)

稳态静默,不占用通知额度。

## 通知排期(防微信限流)

- **不新建独立微信任务**。catalog 自检(cron 08:05,纯脚本 no_agent)只写 `web_data/push_queue/catalog_alert_*.txt`。
- 由现有「推送队列自动发送」任务(08:20)统一消费,合并发送,零新增微信频率。
- 微信现状已偏紧(多任务 last_delivery_error=rate limited),严禁再加独立微信 cron。
- 排期错峰:07:55 晨报转发 → 08:10 错误回顾 → **08:05 catalog 自检(写文件)** → 08:20 队列发送。

## Pitfalls
- **别拿同价合并 SKU**:gpt-5/gpt-5-chat 同价但是两个 SKU。这是上一轮踩过的概念错误。
- **陈旧报价存量别天天报**:第一期把 stale 基线记进 catalog_metric,之后只报增量,否则每天噪音。
- **手动测试会往 push_queue 塞文件**:测完记得 `rm web_data/push_queue/catalog_alert_*`,否则 08:20 误发。
- **微信限流是硬约束**:新通知一律走 push_queue 文件 + 既有 08:20 消费,不直连。
- **重建幂等**:build_catalog `--commit` 先 DELETE 再 INSERT,可反复跑;但跑前 DB 已被 cron 频繁读写,大改前仍要备份。

---

## §7 自检 evidence 落点 (Pillar 3 v1.1 增补)

`evolve_catalog.py` 每次跑要落一份当次快照到 `web_data/evidence/catalog/<run_id>.json`,
作为派生表的 evidence 证据. JSON schema 见 `PILLAR_3_PROVENANCE_STANDARD.md` §7.

字段示例:
```json
{
  "_meta": {
    "source": "derived:build_catalog",
    "method": "derive_catalog_v1",
    "fetched_at": "2026-06-27T08:05:00Z",
    "fetcher_version": "build_catalog.py@<git_sha>",
    "raw_path": "model_canonical + price (主库)"
  },
  "rows_extracted": 1151,
  "rows_written_spu": 1151,
  "rows_written_sku": 1181,
  "metrics": {
    "collision_human_review": 0,
    "orphans": 0,
    "stale_price_new": 3,
    "sku_drift_pct": 0.4
  },
  "method_chain": ["read_canonical", "normp", "dedupe_sku", "strip_suffix_spu",
                   "indep_product_authority_check", "writer_delete_insert"]
}
```

保留期 90 天 (按 Pillar 4 §3 默认派生表 TTL). 90 天前的可由 cron 清.
