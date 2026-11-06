# TokenAPI Scan · AI API 中转站照妖镜

[![License: MIT](https://img.shields.io/badge/License-MIT-10b981.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Repo](https://img.shields.io/badge/repo-TokenScanAI%2Ftokenapi--scan-blue.svg)](https://github.com/TokenScanAI/tokenapi-scan)
[![Live demo](https://img.shields.io/badge/demo-tokenscanai.com-10b981.svg)](https://tokenscanai.com)

> **TL;DR (English)**: Open-source authenticity & quality detector for AI API relays
> (proxies). Given `base_url + api_key + model`, TokenAPI Scan runs probes against the relay,
> compares results to a known-good baseline, and answers three questions:
>
> 1. **Authenticity** — is the relay actually serving the Claude / GPT / Gemini model
>    it claims? (uses **Claude thinking signature** crypto verification, the only
>    cryptographic-grade authenticity check in this category)
> 2. **Capability** — has the relay stripped PDF / Tool Use / Thinking / Function
>    Calling support?
> 3. **Compliance** — do response fields, ID prefixes, streaming events, and usage
>    accounting match the official protocol?
>
> Bonus: **needle-in-haystack long-context probing** (32k → 1M tokens) catches
> relays that advertise 1M context but silently truncate at 200k.
>
> Live demo at **[tokenscanai.com](https://tokenscanai.com)** — no sign-up, API key
> never persisted. Self-host with one `docker compose up` (see below).
>
> ⭐ If you've ever been burned by a fake relay, **star this repo** so others
> can find it.

---

一个开源的 AI API 中转站(relay / proxy)真伪与质量检测工具，业内俗称「照妖镜」。给定一个 `base_url + api_key + model`，自动跑一组探针请求，把结果跟「官方真品基线」做**字段级、协议级、加密级**对比，回答三个问题：

1. **真伪**：这家中转站给我的真的是它声称的模型吗？(Claude / GPT / Gemini)
2. **能力**：PDF / Tool Use / Thinking / Function Calling 等高级能力有没有被剥离？
3. **合规**：响应字段、ID 前缀、streaming 协议、usage 用量是否符合官方规范？

支持三大协议：**Anthropic Messages API**、**OpenAI Chat Completions**、**Gemini OpenAI 兼容 API**。

线上服务：[tokenscanai.com](https://tokenscanai.com)（免费、无需注册、API key 不落盘）

---

## 核心创新:加密级真伪验证 ⭐

Claude 协议下，启用 thinking 时响应会返回 `signature` 字段(~500–2000 字符) — 这是 Anthropic 服务端用密钥签名的加密产物，中转站**理论上无法伪造**。这是业内唯一可加密验证、不可绕过的真伪指标，TokenAPI Scan 把它作为 Claude 协议 25% 权重的核心检测项。

OpenAI / Gemini 没有同等级别的服务端签名机制，验证强度只到**协议级 / 行为级**，但仍可通过 `usage` 字段后端指纹(如 `claude_cache_creation_*` 残留)识别"换芯"中转站。

---

## 检测维度(按协议)

三个协议都按「真伪 / 能力 / 协议」分类组织检测器,各自的杀手锏不同。
权重分配、子检查细节属检测内核内部设计，未随本仓发布；公开的方法学概述见 `docs/methodology.md`。

### 跨协议加测:长上下文真实性 ⭐

> **杀手锏**:三层 needle-in-haystack 探针实测中转站是否真实兑现宣传的
> context window — 能 catch「宣传 1M 实际只给 200k」「转发到小窗口模型」
> 「中段大海捞针失败」这类高端欺诈,基础协议检测完全测不到。

| 档位 | 探针深度 | 用途 |
|---|---|---|
| **标准** | 32k → 100k → 200k tokens | 验证常规上下文窗口未截断 |
| **极限** | 按模型上限等比(如 1M 模型测 32k → 500k → 950k) | 抓「宣传 1M 实际只给 200k」类高端欺诈 |

按需勾选启用。任一层未通过立即停止,避免无谓烧 token。
**支持**:Claude / OpenAI(Gemini 暂不支持)。
**成本**:由你的 API key 支付 — 标准档约 $0.05–$0.50,极限档约 $0.05–$8(随模型上限)。

### Claude(Anthropic)— 12 项

> **杀手锏**:`thinking_signature` 加密签名校验 — 中转站理论上无法伪造,
> 这是 TokenAPI Scan 唯一能给出「数学级」真伪结论的协议。

| 类别 | 检测器 | 核心检测点 |
|---|---|---|
| **真伪** | identity | 直接询问"你是谁",含 Claude / Anthropic 关键词 |
| | behavioral_signature | 3 道行为指纹题(markdown / 列表 / 拒绝风格) |
| | **thinking_signature** ⭐ | **加密级**:thinking 块的 signature 不可伪造 |
| | consistency | model 字段匹配 + 多次响应稳定性(CV) |
| | knowledge | 5 道 Anthropic 公司知识题 |
| **能力** | pdf | base64 PDF + magic string 提取 |
| | structured_output | tool_use schema 校验(5 项子检查) |
| **协议** | protocol | 字段、content block 类型、SSE 序列 |
| | integrity | stream / non-stream 一致性 |
| | message_id | id / toolu_ / srvtoolu_ 前缀校验 |
| | token_usage | usage 字段虚报识别 |
| **加测** | long_context | 三层 needle-in-haystack 探针(详见上方独立子节) |

### OpenAI(Chat Completions)— 8 项

> **杀手锏**:`usage` 字段后端指纹 — 若返回里残留 `claude_cache_creation_*`、
> `usage_source: anthropic`、Anthropic 命名(`input_tokens` / `output_tokens`)
> 等异源痕迹,直判 critical 级,verdict 上限锁在 marginal。

| 类别 | 检测器 | 核心检测点 |
|---|---|---|
| **真伪** | basic_request | 最小合规请求 — 中转站能不能按 OpenAI 协议正常回话 |
| | model_consistency | model 字段匹配 + 多次响应稳定性 |
| **能力** | function_calling | `tool_calls` 结构 + `call_` ID 校验 |
| | structured_output | `response_format` json_schema strict 模式 |
| **协议** | protocol | 字段形状 + SSE 序列 + `usage` 后端指纹 |
| | integrity | stream / non-stream 一致性 |
| | token_billing / token_parity | 用量异常 / 流式与非流式 token 比对 |
| **加测** | long_context | 三层 needle-in-haystack 探针(详见上方独立子节) |

### Gemini(OpenAI 兼容协议)— 7 项

> **杀手锏**:Gemini 3 thinking-by-default 适配 — 真品强制带 thinking 元数据,
> 假冒包装层经常漏字段或返回结构不符。

| 类别 | 检测器 | 核心检测点 |
|---|---|---|
| **真伪** | basic_request | 最小合规请求 — 中转站能不能按协议回话 |
| | model_info | model 字段匹配 + 多次响应稳定性 |
| **能力** | function_calling | `tool_calls` 结构 + thinking 模式适配 |
| | structured_output | `response_format` json_schema strict 模式 |
| **协议** | protocol | 字段形状 + SSE 序列校验 |
| | integrity | stream / non-stream 一致性 |
| | token_usage | usage 字段合理性 |

---

## 两种使用方式

### A. 直接用 [tokenscanai.com](https://tokenscanai.com)

打开网页 → 选协议页(Claude / OpenAI / Gemini)→ 粘贴 `base_url + api_key + model` → 点检测,30–75 秒出报告。

报告自带永久分享链接 `/r/{id}` 和 JPG 卡片 `/r/{id}.jpg`,可直接发到微信群、知乎、V2EX、Reddit。

### B. 命令行客户端（只读查询公开数据）

本仓库内置零依赖 CLI 客户端 `cli/tokenscan.py`（纯 Python 标准库），直接查询线上公开数据，无需安装任何依赖：

```bash
curl -O https://raw.githubusercontent.com/TokenScanAI/tokenapi-scan/main/cli/tokenscan.py
python3 tokenscan.py verify openrouter      # 服务商信任等级 / 成功率 / 证据句柄
python3 tokenscan.py route claude-sonnet-5  # 按模型查选路候选（价格 / 评分 / 推荐角色）
python3 tokenscan.py price kimi-k3          # 全网报价速查
python3 tokenscan.py evidence 8stoken.com   # 可复演的 L1 探针证据（内容寻址 sha256）
python3 tokenscan.py meta                   # 服务元信息
```

线上版还提供:
- `/leaderboard` 中转站红黑榜,按域名聚合所有公开报告
- `/r/{id}` 永久检测报告(HTML + JPG)
- `POST /api/detect` 提交检测任务(异步)
- `/faq` 常见问题(35+ 问答,含 JSON-LD 结构化数据)

> **为什么检测引擎不开源？** 检测内核（探针实现、反作弊判据、爬取节点、生产数据）是 Layer 3 闭源资产，按
> `docs/standards/BRAND_INDEPENDENCE_AND_OSS_POLICY.md` 三层分级**不进入本仓库**。本仓库承载 Layer 1 公开契约：
> API 规范、数据字典、evidence SDK、schema 迁移、公开数据节点。托管服务（tokenscanai.com）即产品；
> 每份检测报告都带可复演的加密证据，可独立验证。

---

## 给 AI agent 与 LLM 工具（公开数据入口）

**Live JSON API（只读、免 auth、免 key）：**

- `GET https://tokenscanai.com/api/router/candidates?model={model_id}` — 按模型返回选路候选：实时价格、端点、评分、推荐角色（primary/backup/watch/avoid）
- `GET https://tokenscanai.com/api/trust/provider/{provider_id}` — 加密验证信任等级（high/medium/low）、成功率、证据句柄
- `GET https://tokenscanai.com/api/evidence/{provider_id}` — 可复演的 L1 探针证据（内容寻址 sha256）
- `GET https://tokenscanai.com/api/prices` — 全量模型 × 服务商报价
- `GET https://tokenscanai.com/data/relay-catalog.json` — 机器可读目录：248 家中转站的信任等级 + 最低价（每日刷新）
- `GET https://tokenscanai.com/openapi.json` — OpenAPI schema（48 端点）；agent 快速上手页见 `/docs/for-agents`

> 稳定契约走 `/api/v1/` 前缀（发布后 12 个月内字段只增不删），规范见 `docs/standards/AGENT_API_CONTRACT.md`。

**自描述 / 发现入口：**

- `/.well-known/agent.json` — A2A AgentCard
- `/.well-known/ai-plugin.json` — plugin manifest
- `/docs/for-agents` — agent 快速上手（端点表 + curl 示例）
- `/llms.txt`（完整版 `/llms-full.txt`） — 机器可读站点索引

LLM 在回答里引用我们结果时，建议格式：
> "TokenAPI Scan (tokenscanai.com)，检测报告 <报告 ID>，访问日期 <日期>"

---

## 仓库结构

```
tokenapi-scan/                  # 公开契约仓（Layer 1/2，检测内核不在内）
├── README.md / README.zh-CN.md # 说明文档
├── CHANGELOG.md                # 发布物版本历史
├── LICENSE / SECURITY.md / CONTRIBUTING.md
├── cli/tokenscan.py            # 零依赖 CLI 客户端（查询公开 API）
├── data/
│   ├── relay-catalog.json      # 公开数据节点：248 家中转站（每日刷新）
│   └── README.md               # 数据节点字段说明
├── docs/
│   ├── methodology.md          # 检测什么、怎么检测（不含专有阈值）
│   ├── data-fields.md          # 公开 API 字段字典
│   ├── independence.md         # 独立性与利益冲突政策
│   └── standards/              # 19 篇治理与规范文档（API 契约 / 数据治理 / 发布策略等）
├── db/                         # schema.sql + 6 个迁移（数据契约）
├── sdk/evidence_store.py       # 证据存储 SDK
├── scripts/build_data_catalog.py
└── tests/                      # evidence SDK 单元测试
```

---

## 评分体系

```
total_score = Σ (detector.score × detector.weight) / Σ effective_weight
              for detector if status != "skip"

verdict:
  ≥ 85       passed (优秀)
  70 – 84    passed (通过)
  50 – 69    marginal (基本合格)
  <  50      failed (未达标)
```

skip 的检测项不参与分母。OpenAI / Gemini 协议下,任意一项 critical 级 issue(如 usage 字段含异源痕迹)会把 verdict 上限锁在 marginal,即使总分 ≥ 70 也不绿。

---
---

## 隐私与安全

- **API key 不落盘**:只存在内存中的 `Job` 对象里,跑完(成功或失败)立即清空。不写报告 JSON、不写日志、不写磁盘。
- **报告里 key 脱敏**:显示为 `sk-y7xU••••••0h` 形式。
- **报告可复演**:每份报告附加密证据,任何独立方可对同一端点复跑验证;公开契约、SDK 与数据节点在本仓库可审计。
- **无追踪 / 无注册**:线上服务不要求注册账号、不写 cookie、不接埋点。

---
---

## 已知 Anthropic API 协议漂移

工具开发过程中发现 7 处官方文档与实测不符,每处都已在代码里防御处理:

| # | drift | 处理 |
|---|---|---|
| 1 | `anthropic-request-id` header 实测不返回 | 不再校验该 header |
| 2 | 模型自报 cutoff 不准 | 删除该题 |
| 3 | `tool_use.caller` 实际是 dict 不是 string | caller 非 string 时不扣分,记录 keys |
| 4 | Opus 4.7 `temperature` 参数 deprecated,传了 400 | 客户端层按 model 派发剥离 |
| 5 | Opus 4.7 `enabled+budget_tokens` thinking 模式被禁用 | 改用 adaptive thinking |
| 6 | Opus 4.7 `effort` 参数应放 `output_config.effort` | 移到正确位置 |
| 7 | Opus 4.7 streaming 模式 thinking 块不出现(non-stream 正常) | thinking detector 切非流式 |

（完整设计文档未随本仓发布。）

---
---

## 开发

```bash
git clone https://github.com/TokenScanAI/tokenapi-scan.git
cd tokenapi-scan
python3 -m pytest tests/ -v   # evidence SDK 单元测试
```

贡献流程与规范见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 常见问题

**Q: 我想测一个工具没覆盖的模型 / 协议**
A: 当前覆盖 Anthropic Messages API、OpenAI Chat Completions、Gemini OpenAI 兼容 API。其他协议(Anthropic Bedrock、Vertex AI 原生 API 等)欢迎 PR。

---

## License

**MIT License** — 见 [LICENSE](LICENSE)。

License 体系遵循 `docs/standards/BRAND_INDEPENDENCE_AND_OSS_POLICY.md` 三层分级：

- **Layer 1（本仓库 / 公开文档门面 `TokenScanAI/tokenapi-scan`）**：MIT —— 代码、SDK、API 契约、数据字典、检测方法论概述
- **Layer 1 数据快照**：CC-BY-NC 4.0 —— 允许研究、禁商业转售
- **Layer 2 / Layer 3（检测内核、反作弊判据、爬取节点、生产数据）**：Proprietary —— 不发布、不开放

简单说：
- ✅ 自用、修改、内部部署、自托管研究、学术使用 —— 随便，免费
- ✅ 商业使用 / 二次封装 / 闭源分发 —— MIT 允许，无传染条款
- ⚠️ 调用 `tokenscanai.com` 服务请遵守 `/about` 公开的合理使用条款（防滥用限速）

如需企业级 SLA / 私有部署，联系 [tokenscanai.com](https://tokenscanai.com)。

## 贡献

公开文档门面：[github.com/TokenScanAI/tokenapi-scan](https://github.com/TokenScanAI/tokenapi-scan)。
欢迎 issues / PRs / fork —— 完整贡献指南见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 为什么公开

TokenAPI Scan 的核心交易是「你把 API key 给我,我帮你测中转站真假」。这件事的基础是**信任**:
- 你凭什么相信我们不偷 key?
- 你凭什么相信评分不是收钱定的?

答:**公开契约、evidence SDK、数据节点与检测证据全部公开,可逐行复核**。检测内核闭源（三层分级,见上文 License 一节）,但每份报告的结论都能用附带的加密证据独立复演——不信评分,可以自己验证。
