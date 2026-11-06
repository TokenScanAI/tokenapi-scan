# Agent API 契约标准（AGENT_API_CONTRACT）v1.0

**定稿日期**：2026-06-26 起草 / 2026-06-27 锁定
**状态**：🔒 **v1.0 LOCKED** — D1-D5 五条决定全部按 A 方案拍板（见 §1.6 与 AGENT_API_DECISION_REVIEW.md）
**生效**：2026-06-27 21:39:47 CST（生产 6723 重启时刻）
**冻结期**：v1.0 字段只增不删 **≥ 12 个月**（至 2027-06-27），破坏性变更走 §10 Sunset 流程
**适用范围**：所有 `/api/*`、`/.well-known/*`、未来 MCP/A2A/AP2/ARD 工件、SDK、对外 agent 文档
**关联**：AGENT_PROTOCOL_ROADMAP.md（迭代节奏）· AGENT_API_DECISION_REVIEW.md（D1-D5 决策评审，未随本仓发布）· MODEL_DATA_STANDARD.md（字段权威）· ERROR_CODES.md（错误码字典，未随本仓发布）
**部署状态（2026-11-06 外网实测）**：v1 已公开上线 —— `/api/v1/sites`、`/api/v1/models`、`/api/v1/prices`、`/api/v1/_meta`、`/api/v1/trust/providers` 实测 200；`/.well-known/agent.json`、`/.well-known/ai-plugin.json` 已上线；`/openapi.json` 公开（48 端点）。下文 TODO 标记为定稿时状态。

本文档回答一件事：**今天每一个 API 设计决定，怎样才能不挖未来 agent 协议（MCP / A2A / AP2 / ARD）的坑。**

铁律：API 一旦发 v1 → 12 个月内只能加字段不能删；operation_id 一旦公开 → 永不重命名；
错误格式一旦稳定 → 全协议层共享同一套语义。

---

## 1. 设计前提：五条不可逆决定（契约宪法）

这五条是**今天就要锁死**的，因为它们渗入 OpenAPI、MCP tool 定义、A2A AgentCard、ARD 资源描述、未来 AP2 mandate 校验**全部四层**，任何一条后期改 = 所有下游接入方掉头。

### 1.1 稳定标识符 + 版本前缀

- 所有公开 endpoint 走 `/api/v1/` 前缀。v1 一发布，**12 个月内字段只增不删**。
- 资源标识符（`{slug}`）一律 **不可变 ASCII slug**（小写 + 短横线，无 `:path` 通配）。
  - ❌ `/api/catalog/spu/{spu_id:path}`（path 参数对 agent 不友好）
  - ✅ `/api/v1/spus/{slug}`
- 旧数字 id / 旧路径永久 308 重定向到 v1 slug，不双轨维护。
- v2 启动时 v1 与 v2 并行 ≥ 12 个月，deprecation 在响应头 `Sunset:` + `Deprecation:` 提前 90 天预告。

### 1.2 幂等性 + 错误体统一

- 所有 **POST / PUT / DELETE** endpoint 必须接受 `Idempotency-Key: <agent-生成-uuid>` 请求头。
  - 服务端 2 小时窗口内同 key 同 body 返回同 job_id（或同结果），不重复触发。
  - 不带 key 的 POST 也允许，但 agent 客户端**应当**带；MCP/A2A 文档要求带。
- 所有错误体（4xx / 5xx）统一：
  ```json
  {
    "error": {
      "code": "rate_limited",
      "message": "Too many requests from this client",
      "detail": "60/h limit exceeded at 14:32 UTC",
      "hint": "Wait 28 seconds or upgrade quota",
      "docs_url": "https://tokenscanai.com/docs/errors#rate_limited",
      "retry_after_seconds": 28
    },
    "request_id": "req_01H..."
  }
  ```
- `error.code` 用 **snake_case 短码**（不是 HTTP 数字），稳定字典见 `docs/standards/ERROR_CODES.md`（后续单独维护）。
- 任何 5xx 必须带 `request_id`，便于 agent 报障 / 我们追溯。

### 1.3 分页一律 cursor，不要 offset

- agent 巡检往往跨小时跨天，offset 翻页期间数据增删会**漏行/重行**，cursor 不会。
- 响应：
  ```json
  { "items": [...], "next_cursor": "eyJpZCI6MTIzfQ", "has_more": true }
  ```
- `limit` 默认 50，最大 200。
- 内部 cursor 编码 = base64url(JSON{anchor})，不暴露内部主键。

### 1.4 字段命名 + 类型规范

| 类目 | 规范 | 示例 |
|---|---|---|
| 字段命名 | **snake_case 全局** | `last_probed_at`, `tier_score` |
| 时间 | RFC3339 UTC，末尾 `Z`，**永远 string** | `"2026-06-26T07:14:00Z"` |
| 时长 | `*_seconds` 或 `*_ms` 整数 | `latency_ms: 1240` |
| 金额 / 价格 | **string decimal**（防 IEEE 754 精度坑，AP2 付费层关键） | `"price_input_per_1m": "3.00"` |
| 货币 | 单独字段 ISO 4217 | `"currency": "USD"` |
| 枚举 | 全小写 snake_case | `tier: "s"`、`region: "cn"` |
| 布尔 | `is_*` / `has_*` / `reachable_*` 前缀 | `is_active: true` |
| 空值 | 缺失字段干脆不返回（不用 `""` / `0` / `null` 占位） | — |

### 1.5 operation_id：每个 endpoint 的稳定身份

- FastAPI 路由必须显式声明 `operation_id`，**这是 OpenAPI schema 字段，MCP tool 名 / A2A skill id / SDK 方法名全部直接用它**。
- 命名公约：`<verb>_<resource>[_<qualifier>]`，全 snake_case。
  - ✅ `list_relay_sites`, `get_relay_site`, `submit_detection`, `get_detection_result`, `get_ranking`
  - ❌ `getSiteData`（camelCase）、`api_v1_sites_get`（带版本/路径）
- **公开后永不重命名**。需要语义变更 → 新 operation_id + 旧 id 通过 `deprecated: true` + `x-replaced-by` 指向新 id，并行 ≥ 12 个月。
- 命名前必须 grep OpenAI Plugin / Anthropic MCP / Google A2A 公共生态有无重名（避免抢身份）。

### 1.6 拍板备忘（2026-06-27 锁定）

D1-D5 五条按 A 方案锁定，进 §10 Sunset 才能改：

| # | 决策 | A 方案（已采纳） | 落地证据 |
|---|---|---|---|
| **D1** | 协议形态 | REST + JSON + OpenAPI 3.1 | `/openapi.json` 200, `info.openapi='3.1.0'` |
| **D2** | 鉴权 | Phase 0/1 无 auth + IP 限流；Phase 4+ 三槽 `apiKey/oauth2/ap2Mandate` | `components.securitySchemes` 三槽就位（占位） |
| **D3** | 缓存 / Sunset | v1 字段稳定 ≥ 12 个月 + 破坏性变更 90 天 `Sunset` + `Deprecation` 预告 | §10 流程 |
| **D4** | 分页游标 | `base64url(JSON{anchor})`；实现单独排程 | 设计稿 §1.3 已锁 |
| **D5** | 错误体 | `error.code` snake_case + `ERROR_CODES.md` 字典 | `docs/standards/ERROR_CODES.md` 已就位 |

完整 trade-off 矩阵见 `AGENT_API_DECISION_REVIEW.md`。

---

## 2. 四层 Agent 协议映射

按"agent 接触我们的路径"分四层。每一层都使用第 1 节定义的契约语义。

```
L1 资源发现 (Discovery)
  │  ├─ /llms.txt                   人类 + agent 都读，自然语言能力清单
  │  ├─ /.well-known/ai-plugin.json OpenAI plugin 兼容入口（事实标准，仍被多客户端引用）
  │  ├─ /.well-known/agent.json     Google A2A AgentCard
  │  ├─ /.well-known/ard.json       Agent Resource Description（见第 3 节）
  │  └─ /openapi.json               OpenAPI 3.1 schema（机器读）
  ↓
L2 工具调用 (Tool invocation)
  │  ├─ REST + OpenAPI              所有 agent 都可降级到此
  │  └─ MCP server (stdio + HTTP)   Claude Desktop / Hermes / Cursor / Cline 等
  ↓
L3 Agent 协作 (Delegation)
  │  └─ A2A Skill: evaluate_relay   外部 agent 委托我们跑检测，流式回报告
  ↓
L4 价值结算 (Settlement)            条件触发，不抢跑
     ├─ API Key + 配额
     ├─ OAuth2 / API Key auth
     └─ AP2 Intent Mandate          agent 替用户花钱，JWS 签名校验
```

**契约共享原则：** 同一个能力在四层应当映射到**同一个 operation_id**。例：

| 层 | 形态 |
|---|---|
| REST | `POST /api/v1/detections` |
| OpenAPI | `operationId: submit_detection` |
| MCP | `tool: submit_detection` |
| A2A | skill 内部 step `submit_detection` |
| SDK | `client.submit_detection(...)` |

---

## 3. ARD（Agent Resource Description）单独说

### 3.1 ARD 是什么、和 llms.txt / agent.json 关系

- **llms.txt**：自然语言写的"我有什么"，给人 + LLM 直读，**非结构化**。
- **ai-plugin.json**：OpenAI ChatGPT plugin 时代遗留的结构化清单，业内仍兜底引用。
- **agent.json (A2A AgentCard)**：Google A2A 协议要求的 agent 自描述，**只描述 agent 自己**（capabilities / skills / endpoint）。
- **ard.json (Agent Resource Description)**：比 AgentCard 更广，描述 **"agent 可访问的资源 + 工具 + 数据集 + 操作语义"** 整套清单。可以理解为 `llms.txt + ai-plugin.json + agent.json` 的结构化超集，给**多 agent 协调器 / agent 路由器**消费。
  - ARD 协议规范本身仍在草案阶段（生态有多个版本：a2a-ext / google ARD draft / 业界 W3C-style 提案），**字段层级未定**。

### 3.2 我们的 ARD 策略：先占位、后跟标准

- **占位发布**：`/.well-known/ard.json` 今天就发，返回**有兼容性裸字段** + 通过 `x-tokenscan-*` 扩展承载实际信息。
  ```json
  {
    "$schema": "https://tokenscanai.com/schemas/ard-tokenscan-v0.json",
    "ard_version": "0.1-draft",
    "agent": {
      "name": "TokenAPI Scan",
      "url": "https://tokenscanai.com",
      "agent_card_url": "/.well-known/agent.json"
    },
    "resources": [
      {
        "id": "relay_sites",
        "type": "dataset",
        "operation_id": "list_relay_sites",
        "endpoint": "/api/v1/sites",
        "summary": "Curated registry of AI API relay services with monthly probe history"
      },
      {
        "id": "detection_engine",
        "type": "action",
        "operation_id": "submit_detection",
        "endpoint": "/api/v1/detections",
        "summary": "Submit a relay URL for live authenticity probing"
      }
    ],
    "skills": [
      {
        "id": "evaluate_relay",
        "summary": "End-to-end evaluation: probe + protocol detection + tier scoring + markdown report",
        "agent_card_skill_ref": "evaluate_relay"
      }
    ],
    "x-tokenscan-tier-system": {
      "tiers": ["s", "a", "b", "c", "d"],
      "scoring_docs": "/docs/standards/SCORING.md"
    }
  }
  ```
- **跟踪策略**：每周一次自动检查上游 ARD 草案 commit（GitHub 上的 a2aproject/agent-resource-description 或后续标准仓），有 breaking 更新 → cron 推送微信告警，**人工评估**后再升 version。
- **承诺口径**：仓库 README 写 `"ARD: experimental, schema follows draft spec"`，不承诺稳定。

### 3.3 ARD 与其它发现资源的去重原则

- agent.json **只**保留 A2A 协议要求字段。
- ard.json **聚合**所有资源（含 dataset / tool / skill / 文档链接）。
- ai-plugin.json **冻结**在 OpenAI plugin 历史 schema，不再演进。
- llms.txt **保持自然语言**，不机器序列化。

---

## 4. `.well-known` 资源清单

| URL | 用途 | 状态 |
|---|---|---|
| `/llms.txt` | 自然语言能力描述（人 + LLM） | 现有 148 行，需补 agent endpoint 章节 |
| `/.well-known/ai-plugin.json` | OpenAI plugin 兼容 | ✅ 已上线（2026-11-06 实测 200） |
| `/.well-known/agent.json` | A2A AgentCard | ✅ 已上线（2026-11-06 实测 200；capabilities-only，先不接 A2A 协议本身） |
| `/.well-known/ard.json` | Agent Resource Description（草案占位） | 未上线 |
| `/openapi.json` | OpenAPI 3.1 schema | ✅ 已自动生成，需暴露 + 加 servers/contact/security |
| `/docs` | Swagger UI | 当前关闭 (`docs_url=None`)，需重开 |
| `/redoc` | ReDoc UI | 可选，看需求 |
| `/api/v1/_meta` | 运行时元信息（version / build / git_sha / supported_protocols） | ✅ 已上线（2026-11-06 实测 200） |

---

## 5. 自定义扩展命名空间

OpenAPI / MCP / A2A / ARD 都允许 `x-vendor-*` 字段。我们统一用：

| 前缀 | 用途 |
|---|---|
| `x-tokenscan-*` | TokenAPI Scan 专有数据（tier / 中国可达性 / thinking_signature 检测结果等） |
| `x-ard-*` | ARD 草案规范字段实验区，标准定稿后迁出 |

**禁令**：不要把专有字段塞进标准字段（如把 `tier_score` 塞进 OpenAPI 的 `summary`），会污染兼容性。

---

## 6. 版本与 Deprecation 策略

| 事件 | 协议要求 |
|---|---|
| 加字段 | 不算 breaking，但需 changelog 记录 |
| 改字段类型 | breaking，必须新字段 + 旧字段 deprecated 12 个月 |
| 改 operation_id | breaking，永不允许；只能新增 + alias |
| 删 endpoint | 必须 12 个月 deprecation 期，期间响应头：`Deprecation: true` / `Sunset: <RFC3339>` / `Link: <new>; rel="successor-version"` |
| 改语义（非字段） | 视同 breaking，走 v2 |

每次 v1 内的字段增量 → `docs/standards/AGENT_API_CHANGELOG.md` 一行记录（**与门面仓 changelog.md 同步**）。

---

## 7. 安全与认证

| 层 | Phase 0/1（公开） | Phase 4（条件触发） |
|---|---|---|
| 读 endpoint | 无 auth，IP 限流 60/h | 可选 ApiKey，配额提至 600/h |
| 写 endpoint（POST detect） | IP 限流 + Idempotency-Key 必须 | ApiKey 必须，配额按 plan |
| MCP stdio | 客户端本地进程，自然隔离 | 同 |
| MCP HTTP | 暂不开放 | OAuth2 |
| A2A | 公开 skill 无 auth | OAuth2 / AP2 Mandate |

`securitySchemes`（OpenAPI components）今天就要预留三个槽：`apiKey`、`oauth2`、`ap2Mandate`，**Phase 0 都写在 schema 里但全部 endpoint `security: []`**，未来不动 schema 只动 endpoint 引用。

---

## 8. 验收清单（Phase 0 收尾用）

任一条不达标，Phase 0 不能视为完成、不可进 Phase 1。

- [ ] `curl /api/v1/sites?limit=1` 200，返回 `next_cursor`、字段 snake_case、时间 RFC3339
- [ ] `curl -X POST /api/v1/detections -H 'Idempotency-Key: xxx' ...` 两次返回同 job_id
- [ ] 触发限流 → 响应体匹配第 1.2 节错误格式，含 `request_id` + `retry_after_seconds`
- [ ] `curl /openapi.json | jq '.paths | keys[]'` 全部出现 v1 endpoint + 每个有 `operationId`
- [ ] `curl /openapi.json | jq '.components.securitySchemes | keys'` = `["apiKey","oauth2","ap2Mandate"]`
- [ ] `curl /.well-known/ard.json` 200，至少含 `agent`、`resources`、`skills` 三块
- [ ] `curl /docs` 200，Swagger UI 可交互
- [ ] `grep -rn "operationId" web/server.py` 数量 = v1 公开 endpoint 总数
- [ ] 仓库 TokenScanAI/tokenapi-scan 的 `docs/api-reference.md` 与生产 `/openapi.json` 字段、operation_id 完全一致（diff 脚本通过）

---

## 9. 红线（实战教训）

1. **MCP / A2A / ARD 任何一项都不能在 Phase 0 契约未稳定前发布。** 否则 breaking change 一波带走全部下游。
2. **协议跟潮不抢跑。** ARD 草案变了 → 评估后升 minor version；未稳定字段一律走 `x-ard-*`。
3. **不在 v1 期间引入 GraphQL / gRPC。** REST + MCP + A2A 已经够，多协议 = 多套适配负担。
4. **operation_id 命名前必须 grep 公共生态**（OpenAI plugin marketplace / Anthropic MCP registry / Google A2A directory）防身份冲突。
5. **付费 endpoint 永远不和检测准确性绑定。** 检测能力终身免费，付费仅换配额 / 数据快照频率 / 高级 skill。
6. **任何 agent-facing 字段变更 PR 必须同步改三处**：server.py + 门面仓 docs/api-reference.md + AGENT_API_CHANGELOG.md。漏一处 = revert。

---

## 10. 与其它标准的关系

| 文档 | 关系 |
|---|---|
| `MODEL_DATA_STANDARD.md` | 字段权威源；agent API 响应中 model 字段命名以此为准 |
| `CATALOG_STANDARD.md` | SPU/SKU 在 agent API 中的边界与命名 |
| `PRICE_DATA_PIPELINE_STANDARD.md` | `/api/v1/prices` 数据出处口径 |
| `DATA_QUALITY_AUDIT_STANDARD.md` | agent 报错"数据不一致"时的复核流程 |
| `AGENT_PROTOCOL_ROADMAP.md`（待建） | 本契约落地的时间线 / Phase 0-4 计划 |
| 门面仓 `docs/api-reference.md` | 本契约的**对外**呈现，必须同步 |

---

**核心一句话：** 这份契约不是约束今天，而是约束**未来 12 个月每一个 agent 接入方的体验**。今天多花 3 天写对，未来不用 3 个月给所有客户写迁移指南。
