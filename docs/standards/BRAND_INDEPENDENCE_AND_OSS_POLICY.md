# TokenAPI Scan · 品牌独立性 & 开源策略（BRAND_INDEPENDENCE_AND_OSS_POLICY）v1

定稿日期：2026-06-26　状态：v1.0
关联文档：DATA_GOVERNANCE_FRAMEWORK.md · AGENT_API_CONTRACT.md · AGENT_PROTOCOL_ROADMAP.md

---

## 0. 写这份文档的原因

TokenAPI Scan(Token 照妖镜)未来要走企业服务路线。任何"依附 / 借鉴 / fork"叙事都会被未来竞争对手放大攻击。这份文档把三件事一次性定死:

1. **品牌独立性声明**(给市场、客户、监管看)
2. **技术资产三层分级**(给团队 / 开源社区看)
3. **开源/闭源/受控开源决策标准**(给企业客户看)

定下来之后,**这三件事不再讨论**。任何 PR / blog / 对外通信都按这份文档走。

---

## 1. 品牌独立性声明

### 1.1 自主性硬证据(三条,可被外部验证)

| # | 证据 | 验证方式 |
|---|---|---|
| 1 | **检测技术全部自研** — thinking_signature 加密签名验证、12/8/7 维协议指纹、tier 评分算法、中国可达性测试方法论 | `docs/standards/FRAMEWORK_FINGERPRINT.md` git history 自 2026-05 起 |
| 2 | **数据全部自采** — seed_providers 38 站全部我们自己探测发现,price/canonical/alias 表全部自建 | `web_data/db/tokenapi.db` 行级 `source` 字段、git history、normalize_run 表 |
| 3 | **品牌资产全部独立** — tokenscanai.com 域名、紫绿配色、SVG LOGO、TokenAPI Scan/Token 照妖镜 命名 | WHOIS / 商标查询 / GitHub TokenScanAI/tokenapi-scan |

### 1.2 与同领域工具的关系

> **TokenAPI Scan 在 2026 年 5 月独立成立,与早期同领域工具(tokenapi-legacy / hvoy / aichat-aggregators 等)是竞品关系,无任何技术 / 代码 / 数据共享。**

具体边界:

| 项 | 我们 | tokenapi-legacy / hvoy / 其它 |
|---|---|---|
| 代码库 | `TokenScanAI/tokenapi-scan` + `$REPO_ROOT`(自建) | 各自独立 |
| 检测引擎 | `<INTERNAL>/`(全部自写) | 各自独立 |
| 数据库 | 自建 schema、自建 16 表 | 各自独立 |
| 检测方法 | thinking_signature + 12/8/7 维协议指纹 + 中国可达性双向测试 | 各自独立 |
| 探测节点 | 自有(IP / 路由 / 重试策略不公开) | 各自独立 |
| 数据源 | 自有 probe / 自建 seed_providers / OpenRouter + LiteLLM 双权威源 | 各自独立 |

**`tools_dev/tools/competitor_watch.py` 把 tokenapi-legacy 列为竞品监测对象** — 这是正面公开承认竞品关系,而非"曾经叫这个名字"。

### 1.3 历史品牌词残留处置(透明化,不掩盖)

实测:截至 2026-06-26,生产代码库存在历史品牌词 `tokenapi-legacy / tokenapi-legacy` 残留 ~30 处,均为:

| 类别 | 处置 |
|---|---|
| 历史归档快照(`docs/reference/archive/`, `web_data/notifications/archived/`) | **保留**,加 `_legacy_brand_pre_20260523` 标签 |
| 备份目录(`<hermes-config>/backups/`, `tokenscan_backups/`) | **保留**,不影响生产 |
| 安全审计脚本黑名单(`scripts/docs_audit.py`) | **保留**(这正是反污染机制) |
| 生产链路引用(`scripts/daily_site_candidates.py` tokenapi-legacy.org 抓取 / `scripts/seo_geo_audit.py` SEO 词典 / `scripts/crawler_monitor.py` /opt 路径 / `scripts/generate_promotion_proposals.py` 字段名 / `web/static/v2/*.css` 类名 / `<INTERNAL>/core/long_context.py` 注释) | **2026-06-26 起逐项清理,SOP 详见 §5** |
| 软链 `<legacy-path> -> <legacy-path>` | **2026-06-26 已删除** ✅ |
| 项目内残留 `tokenapi-legacy.service` | **2026-06-26 已挪到 backups** ✅ |
| `<legacy-path>` 真目录 | **2026-06-28 删除**(48h 观察期后) |

### 1.4 公开声明文案(用于 README / about 页 / FAQ)

> **About TokenAPI Scan**
>
> TokenAPI Scan(Token 照妖镜)is an independent AI API relay detection platform, established in May 2026. All detection methodologies, scoring algorithms, data pipelines, and the brand are developed in-house. We treat existing tools in the space (tokenapi-legacy, hvoy, and others) as competitors that we monitor, not as predecessors. Any historical residue of legacy brand names in our codebase is being systematically cleaned per our brand independence policy (`docs/standards/BRAND_INDEPENDENCE_AND_OSS_POLICY.md`).

---

## 2. 技术资产三层分级

> **核心原则:暴露"我们能告诉外部 agent 什么",不暴露"我们怎么知道的"。**

### 2.1 Layer 1 · 完全开源(开发者吸引层)

**目的:** 最大化生态采纳,建立公信力。

| 资产 | 仓库 | License | 价值 |
|---|---|---|---|
| API 契约文档 + OpenAPI schema | `TokenScanAI/tokenapi-scan` | MIT | 让开发者放心接入 |
| MCP server SDK | `TokenScanAI/tokenapi-scan-mcp` | MIT | Claude/Hermes/Cursor 直接装 |
| Python 客户端 SDK | `TokenScanAI/tokenapi-scan-cli` | MIT | 标准客户端 |
| 公开数据快照(月度,延迟 7 天,字段脱敏) | GitHub Release | CC-BY-NC 4.0 | 研究者可用,不可商业转售 |
| `.well-known/{ai-plugin,agent,ard}.json` schema | 站点静态资源 | 公开 | 协议合规证据 |
| Detection 方法论概述(只到方法论层) | `docs/detection-methods.md` | MIT | 公信力建立 |
| 数据字典 / 数据治理框架公开版 | `docs/standards/DATA_GOVERNANCE_FRAMEWORK.md` | MIT | 行业标准输出 |

### 2.2 Layer 2 · 有限开源 / 受控开源(护城河边界)

**目的:** 接口公开,实现闭源。给开发者"用得起来"的能力,不给"自己复刻"的能力。

| 资产 | 公开形式 | 闭源部分 |
|---|---|---|
| Tier 评分体系 | 公布 5 档定义 + 4-5 个主因子名称(可达性 / 协议完整性 / 价格合理性 / 上线时长 / 抗作弊修正项) | 具体权重 / 阈值 / 抗作弊修正项细节 |
| 协议检测维度 | 公布 12 / 8 / 7 维度名称(`FRAMEWORK_FINGERPRINT.md` 公开版) | 具体 challenge payload / 判定阈值 / 加密签名验证步骤 |
| 中国可达性测试 | 公布"我们测什么"(DNS/TLS/HTTP/CN+overseas 双向) | 测试节点 IP / 真实路由 / 重试策略 |
| Leak Radar | 公布"我们扫 7 个源"+ 公开 dashboard | 源清单 / 指纹库 / 去重算法 / 假阳判定规则 |
| 价格双源对齐 | 公布"我们用 OpenRouter + LiteLLM 双权威源" | 跨源差异调和算法 / 异常值过滤阈值 |
| 撞名归类 4 层判据 | 公布判据名称 + 优先级(`COLLISION_CLASSIFICATION_STANDARD.md` 公开版) | 具体短路阈值 / 边界案例处理 |

### 2.3 Layer 3 · 永久闭源(企业服务核心护城河)

**目的:** 任何能让对手在 1 个月内复刻我们的能力,都不公开。

| 资产 | 为什么闭源 |
|---|---|
| 检测引擎完整源码(`<INTERNAL>/core/*`) | 18 个月探索成果,最大护城河 |
| seed_providers 完整列表 + 历史 probe_history | 数据资产,公开 = 帮对手冷启动 |
| `model_canonical` / `model_alias` 完整映射(1260 / 1370 行) | 行业最稀缺数据资产 |
| 反作弊判定完整规则(`COLLISION_CLASSIFICATION_STANDARD.md` 内部版) | 公开 = 教对手怎么伪造 |
| 价格抓取反 ban 完整策略(`PRICE_DATA_PIPELINE_STANDARD.md` 内部版) | 公开 = 让被检测站点学会反爬 |
| Hermes agent 配置 + 微信 pipeline | 运营 know-how |
| 客户企业服务定制规则引擎(Phase 4 之后) | SaaS 收费核心 |
| 探测节点 IP / 路由 / UA 池 / 出口策略 | 公开 = 立即被被检测站封锁 |
| 治理 9 大支柱内部完整 SOP(`DATA_GOVERNANCE_FRAMEWORK.md` 内部细节版) | 企业服务交付核心 |

### 2.4 三层划分边界判定(争议时按这套)

> **决策树(按顺序问,任一是 → 进上一层闭源):**
>
> 1. 公开后,是否让对手 ≤ 1 个月复刻同等能力? → Layer 3
> 2. 公开后,是否让被检测站学会反爬 / 反检测? → Layer 3
> 3. 公开后,是否泄漏正在使用的探测节点 / 资源 / 凭据? → Layer 3
> 4. 公开后,是否让企业客户 "免费拿到付费版" 同等价值? → Layer 3
> 5. 公开后,是否暴露反作弊判据 / 阈值,让作弊方绕过? → Layer 3
> 6. 接口公开实现闭源够吗? → Layer 2
> 7. 完全公开能否换来开发者生态采纳? → Layer 1

---

## 3. License 决策

### 3.1 License 矩阵

| 资产类型 | License | 理由 |
|---|---|---|
| Layer 1 代码 / SDK / docs | **MIT** | 目标是最大化生态采纳,GPL/AGPL 会吓退企业用户 |
| Layer 1 数据快照 | **CC-BY-NC 4.0** | 允许研究但禁商业转售 |
| Layer 2 公开规范 | MIT(文档)+ 闭源(实现) | 标准开放,实现保留 |
| Layer 3 全资产 | **Proprietary** | 不发布、不开放 |

### 3.2 License 一致性硬约束

**问题:** 实测发现 `llms.txt:73` 写 `AGPL-3.0`,与 `README-DISCLAIMER.md` 的 MIT 矛盾。

**整改:** 2026-06-26 起,所有 License 声明统一为:
- 公开 Layer 1 代码:**MIT**
- 公开 Layer 1 数据:**CC-BY-NC 4.0**
- Layer 2 / 3:不出现 License 字样,标 "Proprietary" 或不发布

**SOP:**
- 任何 PR 改动 License 字样,必须同时改 `LICENSE` / `README.md` / `README-DISCLAIMER.md` / `llms.txt` / `pyproject.toml` 五个文件,**少一个 PR 不合**
- 加入 `scripts/governance/license_consistency_check.py` cron 每日 09:00 跑

---

## 4. 反向风险评估(开源后会被如何利用)

| 风险 | 概率 | 应对 |
|---|---|---|
| 对手 fork MCP SDK 接到他们 API | 高 | SDK 默认 `server_url=tokenscanai.com`,改了用户自由 — 不算损失 |
| 对手用公开 detection methodology 训自己的检测 | 中 | 方法论只描述"测什么",实现细节闭源 |
| 对手抓我们公开 API 反建数据库 | 高 | Phase 0 限流(免费 60/h)+ Phase 4 API Key + IP 黑名单;**公开 API 只允许"按条查",不允许"批量导"** |
| 数据快照被偷用 | 中 | CC-BY-NC + 字段水印(故意留少量噪声数据,可追踪) |
| 反作弊规则公开后被绕过 | 高 | Layer 3 永久闭源 — 红线 |
| 治理框架公开后被对手抄 SOP | 低 | 治理框架公开有利于行业,**SOP 公开 ≠ 我们停止迭代**,行业标准输出反而强化品牌 |

---

## 5. 残留品牌词清理 SOP

### 5.1 已完成(2026-06-26)

- ✅ 备份 `<legacy-path>` → `tokenscan_backups/opt_legacy_20260626.tar.gz`(884K, sha256=`1b8315ca...0133130`)
- ✅ 删除 `<legacy-path> -> <legacy-path>` 软链(5/18 旧别名,无引用)
- ✅ 移走 `$REPO_ROOT/tokenapi-legacy.service` → `tokenscan_backups/tokenapi-legacy.service.deprecated_20260626`
- ✅ 生产健康验证:health 200, journal 0 error
- ✅ 落地本文档

### 5.2 待执行(本周)

| # | 任务 | 工时 |
|---|---|---|
| 5.1 | `llms.txt:73` License `AGPL-3.0` → `MIT`,与 README 一致 | 5min |
| 5.2 | `scripts/seo_geo_audit.py:36` SEO 词典移除 `tokenapi-legacy / tokenapi-legacy`(改成竞品监测专用词典分离) | 15min |
| 5.3 | `scripts/crawler_monitor.py:150` 删 `<legacy-path>` 路径 | 5min |
| 5.4 | `web/jobs.py:43` fallback 改 `PROJECT_ROOT/web_data/jobs` | 5min |
| 5.5 | `<INTERNAL>/protocols/openai/detectors/token_billing.py:540` 删 `<legacy-path>` fallback | 5min |
| 5.6 | `web/server.py` 4 处 `TOKENAPI_LEGACY*` env fallback 加 deprecation 警告(保留 90 天兼容期) | 20min |
| 5.7 | `tests/conftest.py` + `tests/test_jobs_long_context.py` 改注释 | 5min |
| 5.8 | `<INTERNAL>/core/long_context.py:209` 注释改写 | 5min |
| 5.9 | `scripts/daily_site_candidates.py` 拆分 — 见 §5.3 | 30min |
| 5.10 | `scripts/generate_promotion_proposals.py` 字段重命名 + JSON 文件改名 | 30min |
| 5.11 | `web/static/v2/all-*.css` 排查 `tokenapi-legacy` 字符串具体用途 | 30min |

### 5.3 关键决策:`daily_site_candidates.py` 处理方式

**不是删 tokenapi-legacy 源,而是:**

1. **保留多源候选发现**(GitHub trending / awesome-list / tokenapi-legacy.org / 其它),全部标 `source_trust: low`
2. **新增** `source_filter` 配置文件 `scripts/source_filters.yaml`,启动时可禁用某源(品牌切割期默认禁用 tokenapi-legacy)
3. **强制**:任何 candidate 入表标 `verification_level=raw`,禁止跳过 candidate_sanity_check 直入 seed_providers
4. **公开声明**:"我们监测竞品(含 tokenapi-legacy)的公开候选清单作为发现源之一,但所有数据均独立验证后入库" — 化被动为主动

### 5.4 防回归(写进 `scripts/docs_audit.py` git pre-commit)

```python
forbidden_in_production_code = ['tokenapi-legacy', 'tokenapi-legacy', '<legacy-path>', 'TOKENAPI_LEGACY']
allowed_paths = [
    'docs/reference/archive/',
    'web_data/notifications/archived/',
    '<hermes-config>/backups/',
    'tokenscan_backups/',
    'scripts/docs_audit.py',
    'tools_dev/tools/competitor_watch.py',
    'tools_dev/tools/hvoy_lab.py',
]
```

任何 PR 触碰 `forbidden_in_production_code`,**必须 commit message 含 `[brand-cleanup]`** + 走人审。

---

## 6. 不可逆决定(写下来不再讨论)

1. **品牌独立性叙事永久**:TokenAPI Scan 自 2026-05 独立成立,与所有同领域工具是竞品关系
2. **三层资产分级永久**:Layer 1 完全开源 / Layer 2 接口公开实现闭源 / Layer 3 永久闭源
3. **License 永久统一**:Layer 1 代码 MIT / Layer 1 数据 CC-BY-NC 4.0 / Layer 2-3 Proprietary
4. **核心检测引擎永远闭源**:`<INTERNAL>/core/*` 永不开源
5. **完整 seed_providers / model_canonical / model_alias 永不公开完整版**
6. **付费层不绑定准确性**:检测能力永远免费,付费仅换配额 / 数据快照频率 / 高级 skill 调用次数
7. **企业服务为最终目标**:任何开源决策必须问 "这能帮还是损害企业服务"

---

## 7. 公开声明触发点

任何时候发生以下事件,**24h 内**对外公告本文档相关内容:

| 触发 | 公告内容 |
|---|---|
| 媒体把我们写成 "tokenapi-legacy fork / 后继者" | 引本文档 §1.2,正名 |
| 监管 / 客户尽调要求技术自主性证据 | 引本文档 §1.1 三条硬证据 |
| 开发者社群质疑"为什么核心引擎不开源" | 引本文档 §2.3 / §2.4 决策树 |
| 数据被对手抓取 / 转售 | 引本文档 §3.1 CC-BY-NC + 字段水印追溯 |
| 任何同业工具公开宣称"借鉴 / 兼容 / 复用 我们" | 法务保留追究权利 |

---

**核心一句:** TokenAPI Scan 是独立品牌、自主研发、有限开源、企业服务为终。任何决策按本文档三层资产分级 + 决策树走,**定下来不再讨论**。
