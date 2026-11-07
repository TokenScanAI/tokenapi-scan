# Agent 协议演进路线图（AGENT_PROTOCOL_ROADMAP）v1

定稿日期：2026-06-26　节奏：基础先行，不一口吃胖
依赖契约：`AGENT_API_CONTRACT.md`（宪法）
关联文档：`MODEL_DATA_STANDARD.md`、`CATALOG_STANDARD.md`、`PRICE_DATA_PIPELINE_STANDARD.md`、门面仓 `docs/api-reference.md`

本文档把"未来面向 agent 的 API / TUI / 工具体系"分阶段、可独立验收。
**每个 Phase 都有进入条件 + 验收条件 + 退出条件，达不到不进下一阶段。**

---

## 0. 全景：六阶段总览

```
Phase 0 · 契约对齐（本周 3-4 天）       ← 不可逆决定全部落地
Phase 1 · L1 资源发现层（下一周 2 天）  ← 五个 .well-known 工件
Phase 2 · L2 MCP Server（2 周）         ← 第一个能被外部 agent 调的工具
Phase 3 · L3 A2A AgentCard + 1 skill（1 个月）
Phase 4 · L4 配额 / AP2 付费层（条件触发，2-3 月后或永不）
Phase 5 · Agent ↔ GitHub 维护联动（Phase 2 完成后并行）
```

每阶段独立可验收，**Phase 5 是横切工程，不阻塞主线**。

---

## Phase 0 · 契约对齐（本周）

> **进度 (2026-06-27 W28)**: 10/12 项已落地 + 在副本 in-process 测试通过.
> 剩 0.6 cursor 分页 (D4 拍板已通过, 需破坏性变更, 单独排程) + 0.2 errors.py 模块化 (功能已在 server.py).
> 5 决策项 D1-D5 全部按 A 方案拍板, 详见 `AGENT_API_DECISION_REVIEW.md`.

> 目标：把 `AGENT_API_CONTRACT.md` 第 1 节"五条不可逆决定"全部落进生产 server.py + 仓库文档。

### 0.1 任务清单

| # | 任务 | 文件 | 工时 | 状态 |
|---|---|---|---|---|
| 0.1 | 中间件：`Idempotency-Key` 处理（2h 窗口去重） | `web/middlewares/idempotency.py`（新） | 2h | ✅ |
| 0.2 | 中间件：统一错误体 + `request_id` 生成 | `web/middlewares/errors.py`（新） | 2h | 🟡 部分 (request_id ✅; errors.py 模块化未拆, RFC7807 故意 DEFERRED) |
| 0.3 | 中间件：`X-RateLimit-*` 响应头 | 改造现有 `ratelimit.py` | 1h | ✅ |
| 0.4 | `/api/v1/*` alias 全量落（指向现有 endpoint，但响应已走 v1 规范） | `server.py` | 3h | ✅ |
| 0.5 | 全部公开 endpoint 加 `operation_id` | `server.py` | 1h | ✅ 25/25 = 100% |
| 0.6 | cursor 分页：`/api/v1/sites`、`/api/v1/prices`、`/api/v1/spus` | `server.py` + 数据层 | 3h | ⏳ 后续单独排程 |
| 0.7 | 字段规范化：时间 RFC3339Z、金额 string decimal、snake_case | `server.py` 序列化层 | 2h | 🟡 部分 (snake_case 已是默认, 金额/时间统一在后续单独排程) |
| 0.8 | `securitySchemes` 占位（apiKey/oauth2/ap2Mandate）加进 FastAPI app | `server.py` | 30min | ✅ |
| 0.9 | `/openapi.json` 加 `servers / info.contact / info.termsOfService` | `server.py` | 30min | ✅ |
| 0.10 | `/docs` Swagger UI 重开 | 改 `docs_url=None` → `"/docs"` | 5min | ✅ + /redoc |
| 0.11 | `/api/v1/_meta` endpoint（version / git_sha / supported_protocols） | `server.py` | 1h | ✅ + contract 区域 |
| 0.12 | `ERROR_CODES.md` 错误码字典定稿 | `docs/standards/ERROR_CODES.md` | 1h | ✅ |

总工时估：~17h（3 天专注期或 4-5 天穿插）

### 0.2 验收（沿用 AGENT_API_CONTRACT § 8 全部 9 条）

- 9/9 必须通过，**任一未过 → 不进 Phase 1**。

### 0.3 退出条件

- 上述验收过 + 生产灰度 48h 无错误堆积。

---

## Phase 1 · L1 资源发现层（Phase 0 完成 +0 天，2 天）

> 目标：agent 第一次接触 tokenscanai.com 时，能从一个 URL 就读懂能干啥。

### 1.1 工件清单

| # | 工件 | 说明 |
|---|---|---|
| 1.1 | `/.well-known/ai-plugin.json` | OpenAI plugin schema 兼容；引用 `/openapi.json` |
| 1.2 | `/.well-known/agent.json` | A2A AgentCard 1.0；capabilities-only（不接 A2A 服务） |
| 1.3 | `/.well-known/ard.json` | ARD 0.1-draft 占位；按 `AGENT_API_CONTRACT § 3.2` 结构 |
| 1.4 | `/llms.txt` 升级 | 加 "## API endpoints for agents" 章节 + curl 示例 |
| 1.5 | 仓库 `docs/for-agents.md` | 一页纸告诉外部 agent dev "怎么调"（MCP/REST/A2A 入口） |
| 1.6 | `docs/standards/AGENT_API_CHANGELOG.md` | 字段增量日志（每次改 v1 必写） |

### 1.2 ARD 0.1 草案占位策略

- **现在发什么**：基础三块 `agent` / `resources` / `skills` + 我们的 `x-tokenscan-*` 扩展。
- **跟踪什么**：每周一 cron 检查 `https://github.com/a2aproject` 与 `https://github.com/google/agent-resource-description`（若存在）的 commit；上游有更新 → 微信告警。
- **不承诺什么**：稳定 schema、生产级 SLA。README 写明 "experimental, draft spec"。

### 1.3 验收

- `curl https://tokenscanai.com/.well-known/agent.json | jq .capabilities` 返非空
- `curl https://tokenscanai.com/.well-known/ard.json | jq '.resources | length'` ≥ 5
- ChatGPT 自定义 GPT 配置 `ai-plugin.json` URL，能识别 schema
- 仓库 `docs/for-agents.md` 提交后 PR review 由本人通过

### 1.4 退出条件

- 5 个工件上线 + 7 天无外部投诉 schema 错。

---

## Phase 2 · L2 MCP Server（Phase 1 完成 +0 天，2 周）

> 目标：让任何 MCP 客户端（Claude Desktop / Hermes / Cursor / Cline）像调本地函数一样用我们。

### 2.1 为什么 MCP 排在 A2A 前

- MCP 已有数十万真实日活客户端（Claude Desktop / Hermes / Cursor / Cline）。
- A2A 生态客户端 < 10 个，**做了没人用**。
- **抓现成生态用户**才有真实反馈驱动后续。

### 2.2 工件清单

| # | 工件 | 说明 |
|---|---|---|
| 2.1 | 新仓 `TokenScanAI/tokenapi-scan-mcp` | Python FastMCP 框架 |
| 2.2 | 5 个初始工具（不要一上来全暴露 21 个） | 见下表 |
| 2.3 | stdio transport 优先 | Claude Desktop / Codex 走这个 |
| 2.4 | HTTP transport（可选 Phase 2.5） | 后补 |
| 2.5 | `pip install tokenscanai-mcp` | PyPI 发布 |
| 2.6 | README + 一份 Claude Desktop config 示例 | 复制粘贴可跑 |

### 2.3 五个初始工具

| operation_id | 描述 | 风险 |
|---|---|---|
| `list_relay_sites` | 列站点（tier/region 过滤） | 低 |
| `get_relay_site` | 站点详情 + 30 天 probe 历史 | 低 |
| `get_ranking` | 红黑榜 | 低 |
| `submit_detection` | 触发检测（返 job_id，非阻塞） | 中（接受用户 api key） |
| `get_detection_result` | 取 job 结果 | 低 |

**用户 api key 安全**：stdio 走本地进程内，自然隔离；HTTP 走 OAuth 时 key 不出客户端。

### 2.4 验收

- Claude Desktop 配置后 5 个工具可见、可调
- `mcp inspect tokenscanai-mcp` 通过
- PyPI 首日下载 ≥ 1（我们自己装）
- 至少 1 个外部用户 issue 反馈（社群发出后 7 天内）

### 2.5 退出条件

- MCP 上线 ≥ 14 天 + GitHub stars ≥ 10 + 真实 issue ≥ 1

---

## Phase 3 · L3 A2A AgentCard + 1 skill（1 个月）

> 目标：让"评估一个 relay"成为可被其他 agent 委托的能力。我们从"工具"升级为"agent 节点"。

### 3.1 工件清单

| # | 工件 | 说明 |
|---|---|---|
| 3.1 | `/.well-known/agent.json` 升级 | capabilities 加 `streaming: true`, `taskManagement: true` |
| 3.2 | A2A 服务端 | `a2a-python` SDK，HTTP + SSE |
| 3.3 | 第一个 skill：`evaluate_relay` | probe → detect-{claude,openai,gemini} → tier → markdown 报告 |
| 3.4 | 进度推送 | `agent/notification` 推 probe 中、检测中、评分中 |
| 3.5 | 最终交付 | `agent/artifact` 返 markdown 报告 |
| 3.6 | demo | `examples/a2a/evaluate_relay_demo.py` 用 a2a-cli 触发 |

### 3.2 关键设计决策

- 这个 skill **免费** + 严格速率限制（5 次/小时/IP）。
- 出现"想多用但配额不够"反馈 → 触发 Phase 4。
- skill 内部串多个 operation_id 调用，**完全复用 Phase 0 契约**。

### 3.3 验收

- 外部 a2a-cli 客户端委托 `evaluate_relay`，收到流式进度 + 最终 markdown
- AgentCard schema 通过 a2a 官方 validator
- demo 能在自己 Hermes 实例上跑通

### 3.4 退出条件

- A2A 上线 ≥ 21 天 + 至少 1 个外部 agent 真调用记录

---

## Phase 4 · L4 配额 / AP2 付费（条件触发）

> **进入条件（全满足才启动）**：
> 1. Phase 3 A2A skill 日调 > 100
> 2. 有 ≥ 3 个用户反馈"想多用但配额不够"
> 3. 我们决定 SaaS 化

> 任一条件未满足 → **永远停在 Phase 3，不抢跑**。

### 4.1 工件清单（条件满足才落）

| # | 工件 | 说明 |
|---|---|---|
| 4.1 | API Key 表 + 自助申请页 | free / basic / pro 三档 |
| 4.2 | 配额体系 | free 60/h, basic 600/h, pro 6000/h |
| 4.3 | AP2 Intent Mandate 校验 | agent 出示用户 JWS 签名 mandate，我们扣费 |
| 4.4 | 结算通道 | Stripe Treasury / USDC（待选） |
| 4.5 | MCP HTTP transport + OAuth | 远程 MCP 接入正式开放 |
| 4.6 | AgentCard `authentication` 字段升级 | `[api-key, oauth2, ap2-mandate]` |
| 4.7 | 数据快照分级 | 月度免费（7 天延迟） / 每日付费 |

### 4.2 红线

- **检测能力永远免费可用**。付费仅换：配额、数据快照频率、高级 skill 调用次数。
- 不和准确性 / 完整性绑定 → 否则信任崩。

---

## Phase 5 · Agent ↔ GitHub 维护联动（Phase 2 完成后并行）

> 目标：让 agent 自己维护门面仓 `TokenScanAI/tokenapi-scan` 的内容同步、issue 回复、数据快照发布。
> **横切工程，不在主线 Phase 0-4 上**，但 Phase 2 完成后即可启动。

### 5.1 价值定位

- 门面仓 5/23 上线后 34 天没动过 → **agent 维护**让它"活起来"
- 每次生产 endpoint 改动 → agent 自动同步 `docs/api-reference.md`
- 每次配置改动 → agent 自动写 `docs/changelog.md`
- 用户提交"新候选站"issue → agent 跑探测 + 自动回复

### 5.2 自动化清单

| # | 自动化 | 触发 | 周期 |
|---|---|---|---|
| 5.1 | 同步 `/openapi.json` 到 `docs/openapi.json` | server.py PR 合并 | 实时 GitHub Action |
| 5.2 | 同步 `AGENT_API_CHANGELOG.md` → 门面仓 `docs/changelog.md` | 月底 | 每月 1 日 cron |
| 5.3 | 生成月度数据快照 + 自动 release | 月底 + 7 天延迟 | 每月 8 日 cron |
| 5.4 | issue 触发：用户提交"新候选站" | Issue label `new-site` | webhook |
| 5.5 | issue 触发：用户报"site 数据有误" | Issue label `data-correction` | webhook |
| 5.6 | PR 触发：用户提交 `model_alias` 纠正 | PR label `data` | webhook |
| 5.7 | star 阈值通知 | repo stars 每涨 10 | webhook → 微信 |
| 5.8 | weekly digest 发 Discussions | 每周一 09:00 | cron |

### 5.3 实现路径

- **GitHub App** 用 `tokenscanai-bot`（独立机器人账号）+ fine-grained PAT
- agent 实例用独立 Hermes profile `tokenscanai-github`（不污染 default）
- webhook 接进 `$REPO_ROOT/web/server.py` 的 `/webhooks/github/*`，限定 GitHub IP 段
- 所有 agent PR 必须开 `auto-merge: false`，**人审通过才合**（防 agent 误改主线）

### 5.4 安全红线

- agent 永远不能改 `LICENSE` / `README.md` / `.github/workflows/`
- agent 改的 PR 必须有 `agent-authored` label + Co-Authored-By 标记
- 主仓 `main` 分支保护开启，至少 1 reviewer

### 5.5 验收

- 任一生产 endpoint 改动 24h 内门面仓 `docs/openapi.json` 自动更新
- 月度数据快照按时发 release
- 至少 1 个真实用户 issue 由 agent 处理并人审通过

---

## 6. 时间线（自然周）

```
W1 (本周)          Phase 0 全部落
W2 (下周)          Phase 1 全部落
W3-W4              Phase 2 MCP 开发 + 内测
W5                 Phase 2 PyPI 发布 + Phase 5 启动（5.1/5.2/5.7）
W6-W7              Phase 3 A2A 开发 + Phase 5 5.3-5.6 推进
W8                 Phase 3 上线 + Phase 5 全量
W9+                观察 Phase 4 进入条件是否满足
```

注：上述是**理想节奏**。实际按"小步迭代不一口吃胖"，Phase 间允许停 1-2 周复盘。

---

## 7. 跨阶段不变量（无论哪个 Phase 都不能违反）

1. **每个新 endpoint 三件套同步上**：OpenAPI 定义 + MCP 工具定义 + A2A skill 描述。哪个落后了**不发**。
2. **operation_id 一旦发布永久锁定**。
3. **所有 agent-facing 文档双语**：en（A2A 生态）+ zh-CN（微信生态）。
4. **协议不抢跑**：AP2 / ARD 草案变 → 评估再决定升 version，不追新追到内伤。
5. **每发一个 agent 工件，跑真实客户端验证**：MCP → Claude Desktop；A2A → a2a-cli；OpenAPI → Postman/Bruno/Hermes。**永远不靠协议合规自我宣称**。

---

## 8. 风险登记册

| 风险 | 缓解 |
|---|---|
| ARD 草案标准变化 → 我们 schema 失效 | 占位字段走 `x-ard-*`，cron 监控上游 commit |
| MCP 客户端碎片化（每个客户端兼容性微差） | 只测 3 个主流（Claude Desktop / Hermes / Cursor），其它 best-effort |
| A2A 生态客户端少导致 Phase 3 价值低 | 进入 Phase 3 前 review A2A 客户端清单，< 5 个则推迟 |
| 付费层动了检测公信力 | 红线：检测能力永远免费 |
| GitHub 维护 agent 误改主线 | PR 必人审、main 分支保护、agent-authored label 必带 |
| operation_id 与 OpenAI plugin / 公共 MCP registry 冲突 | 命名前 grep 全量公共 registry |

---

## 9. 退出条件（什么时候这份路线图本身可以归档）

- Phase 4 已上线 OR Phase 4 进入条件 6 个月未满足且明确不做
- Phase 5 自动化全部上线 ≥ 30 天稳定
- AGENT_API_CONTRACT v1 已稳定 ≥ 6 个月

---

**核心一句：** 基础先行（Phase 0 五条不可逆决定 + ARD 占位），然后 L1 发现 → L2 MCP → L3 A2A → L4 付费 单向推进，**Phase 5 GitHub 维护并行不阻塞**，永远不一口吃胖。

---

## 2026-11-08 增补：外部生态落地锚点（四线做深）

> 外部实测调研（MCP Registry / x402 / A2A v1.0 / 检测学术圈），给 L1-L4 各自锚上现实坐标。

- **L2 MCP → 官方 Registry**：`registry.modelcontextprotocol.io`（preview）。发布用 `mcp-publisher` CLI + `server.json`（GitHub 授权 → namespace `io.github.TokenScanAI/*`）；registry 只存元数据，安装方式必须公开（PyPI 包或 remote URL）。支持 **remote server（streamable-http）**条目 = 零安装分发。行动：① tokenscan-mcp 打 tag 发 PyPI（publish.yml 已就绪，缺 repo secret PYPI_TOKEN）② 补 `/mcp` streamable-http 只读端点（LAN 先行）③ server.json 提交。
- **L3 A2A → v1.0 已换代**：2026-03 v1.0（AAIF 治理，150+ 组织，Bedrock/Azure AI Foundry 原生支持）。**AgentCard 路径已从 `/.well-known/agent.json` 改为 `/.well-known/agent-card.json`**，v1.0 SDK 不再读老路径；新增签名卡（signed agent cards）。行动：我们 `/agent.json` 需补 `agent-card.json`（v1.0 形态）；是否实现完整 A2A task 服务（SendMessage/GetTask）由演进周报按外部消费信号裁决。
- **L4 结算 → x402 已成事实标准**：Linux Foundation x402 Foundation（2026-07 运营，Visa/Mastercard/Stripe/Google 会员）；AWS WAF AI traffic monetization、Cloudflare Agents `paidTool`（MCP 工具按次收费）已原生支持。$50M/年量级（2026-04）尚早，但与"数据节点=可售卖资源"完全同构。行动：演进周报跟踪 x402 spec；当 trust/catalog 数据出现稳定程序化消费（当前 prices 万级 IP/月、trust 个位/日）且出现付费意愿信号时，优先在 CF Worker 层做 x402 门（Premium 数据端点），不动免费层。
- **检测能力 → 2026 学术三件套**：DFA 分布式指纹审计（arXiv 2610.37086：纯文本响应 + Cauchy combination test，5 probes/250 请求出端点级 p 值，支持模型归因与掺杂比例估计）；Logprob Tracking（ICLR 2026：首 token logprobs 双样本置换检验，OpenRouter 23% 端点支持）；rank-based uniformity test（ICLR 2026）。与现有 mfp_* 指纹参考库互补：DFA = 在参考指纹之上加统计检验层。行动：演进周报跟踪 arxiv；实现排队（先 logprob 探针（成本最低），后 DFA 统计层）。
- **自进化底座（11/08 已上线）**：`protocol_evolution_watch.py`（每周一，9 源：两家 changelog/llms + MCP/A2A/x402/CF Agents 规范页 + arxiv）→ `web_data/detection/protocol_watch_queue.jsonl`；`intake_issues.py`（每 6h，GitHub issue→候选池自动接线）；`/api/intake`（邮件→CF worker→分类→入池→自动回信）；`evolution_strategy_weekly.py` v2（周日聚合四线→周报 memo）。
