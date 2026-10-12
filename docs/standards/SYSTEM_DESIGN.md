# TokenAPI Scan 数据积累体系设计 (SYSTEM_DESIGN)
> 2026-06-20 | 把"一次性盘点"升级为"自己跑、自己攒"的活体系
> 对应需求三点:1 模型别名权威校对 / 2 价格框架源数据 / 3 扩展边界评估

## 0. 一句话

不再产出静态清单,而是建三张积累表 + 两条可定期跑的闭环脚本,
每跑一次就把新校对/新探测结果沉淀进库,日积月累形成可追溯、可复用的权威数据资产。
扩展(泛化)在核心样本标准摸清后才做。

---

## 1. 积累表(数据资产载体)

### authority_map — 模型别名权威映射(对应需求1)
| 字段 | 含义 |
|---|---|
| alias | 中转站原始模型名 |
| canonical_id | 归一标准 id |
| authority | 权威源: huggingface / modelscope / vendor_rule / prefix_rule |
| authority_ref | 证据链接(HF/魔搭 repo / 厂商文档 / 中转站说明页) |
| base_model | HF base_model 标签声明的上游(客观证据) |
| relation | base / finetune / quant / alias / closed_api |
| vendor / confidence / verified_at | 厂商 / high·medium·low / 校对时间 |

**首轮落库实绩**: 476 条 (high 392 = HF 181 + 闭源直判 211 / medium 84 = 前缀规则)

### framework_registry — 价格框架端点谱(对应需求2)
| 字段 | 含义 |
|---|---|
| domain / framework | 站点 / new-api·one-api·veloera·done-hub·shell-api |
| price_endpoint / endpoint_status | 可拿价端点 / open·auth·empty·dead |
| models_count / recoverable / last_probed_at | 拿到条数 / 是否可入库 / 探测时间 |

**首轮落库实绩**: 23 站 (open 7 = 355 条 / dead 16 已记录避免重试)

### model_alias 补字段
新增 confidence / evidence / verified_at,解决历史"93% 未验证"——现已验证率 64%。

---

## 2. 两条闭环脚本(自己跑的引擎)

### 模型: scripts/align/sync_authority.py
增量取 model_alias 里 confidence=low/null 的 → 逐条判定 →
本地前缀(medium) → 闭源厂商直判(high) → 裸名补官方 org/repo 查 HF(high) → 魔搭兜底(high) →
写 authority_map + 回填 model_alias。已 high 的下轮不重复。
- 关键规则(已实测,踩坑沉淀):
  - 裸名必须 family→官方org精确补 repo,**禁 HF search top-1**(量化作者/子变体陷阱)
  - `-hf` 是 Meta 官方命名不能剥;`-tput/-fast` 是中转站后缀要剥
  - 闭源 API(gpt/claude/gemini/doubao...)社区永远查不到,前缀直判=客观边界非失败
  - distill 蒸馏模型 vendor 以 HF 官方 owner 为准,前缀会误判

### 价格: scripts/crawl/probe_framework.py
对无价站批量探测 → HTML 指纹初判 + 多框架端点谱逐个试(硬证据优先) →
写 framework_registry。dead 站记录在案,下轮增量更新。
- 关键规则:端点返回数据 > HTML 指纹;quota_type=0 才可换算价格;completion_ratio 站点自定义须用站点值;新模型无官方锚价禁公式入库。

---

## 3. cron 时刻表(让它日复一日)— 待你拍板

| 任务 | 建议频率 | 脚本 | 说明 |
|---|---|---|---|
| 模型别名校对 | 每天 1 次 03:30 | sync_authority.py --commit | 增量,只跑 low |
| 框架端点探测 | 每周 1 次 周日 04:00 | probe_framework.py --commit | 端点变动慢,周频足够 |
| (现有)价格 ETL | 已有 8:30/20:30 | — | 不动 |

> 所有通知统一发微信,间隔≥30 分钟避免限流(符合你的既定偏好)。
> **是否上 cron 等你审完本方案再定**,脚本已就绪可随时挂。

---

## 4. 扩展边界评估(对应需求3)— 核心样本先摸清

### 现状判断
核心样本标准已基本建成:模型权威库 64% 已验证 + 价格框架库 7 站可拿源。
但仍有两块"标准未完全摸清",**扩展应等这两块收口**:

1. **模型 261 条 low 未深挖** — 归类已清:
   - 连字符变体(code-llama-13b vs CodeLlama-13b-hf):归一化规则可救
   - 非对话模型(SSD-1B/bge-*/dall-e):classify_model_type 已能识别,应过滤出对话榜
   - 社区微调(Stheno/chronos-hermes):HF search 兜底或人工
   - 中转站自有变体(coding-glm-5.2):需查**中转站自己说明页**(你强调的深挖)
2. **价格 355 条新源未抽检入库** — 需逐站抽检 5 个锚点模型对官方价,过了才 ETL。

### 扩展顺序(摸清后再泛化)
- **Phase 0 地基收口(现在)**: 把 low 261 的归一化规则补全、非对话过滤、355 源抽检入库。
- **Phase 1 存量恢复**: 7 站框架源 ETL(quota_type=0 文本模型,逐站抽检)。
- **Phase 2 泛化扩展(摸清后)**: 国产官方源优先 dashscope(阿里百炼,HF常缺正好魔搭补),
  再评估海外聚合源。**每阶段过质量门(抽检通过率)才进下一阶段**,不一次性大改。

---

## 5. 给你的审核点

1. cron 时刻表(模型日频 / 框架周频)认不认可?要不要现在挂?
2. 355 条框架新源,是否按"逐站抽检 5 锚点→过了才入库"推进?
3. 261 low 深挖优先级:先做归一化规则(救连字符变体)还是先做非对话过滤?
4. 扩展到魔搭源(国产模型 HF 缺失兜底)要不要纳入 Phase 2?

文件: docs/standards/SYSTEM_DESIGN.md | 脚本: scripts/align/sync_authority.py, scripts/crawl/probe_framework.py | 表: authority_map, framework_registry
