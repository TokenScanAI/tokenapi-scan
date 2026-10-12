# 模型数据标准（Model Data Standard）v1

定稿日期：2026-06-20　适用：$REPO_ROOT 模型库（model_canonical / model_alias / price）

本标准回答三个问题：**什么模型该进库、一个模型的字段怎么填才算合格、别名怎么映射才可信**。
铁律继承自 AGENTS.md：数据真实、客观判据、抽检校验。本标准下所有字段填充都必须有可验证证据来源，禁止人工拍脑袋估算。

---

## 一、收录边界：什么模型该进 model_canonical

现状问题：vendor=unknown 的 142 个模型里，28 个根本不是对话 LLM（图像14/embedding11/语音3），它们"无厂商"是因为体系缺 `model_type` 维度，把图像模型和对话模型混在一张表里硬归类。

### 1.1 新增字段 model_type（收录前必判）

| model_type | 说明 | 是否进主榜 | 例 |
|---|---|---|---|
| `chat` | 对话/补全 LLM | ✅ 主榜核心 | gpt-4o, claude-4, qwen3 |
| `embedding` | 向量嵌入 | ❌ 不进价格主榜，单独归类 | bge-m3, gte-large, embed-v4.0 |
| `rerank` | 重排序 | ❌ 同上 | bge-reranker-v2-m3 |
| `image` | 图像生成 | ❌ 单独子库（计价单位不同） | dall-e-3, flux-1-dev |
| `audio` | 语音/TTS/ASR | ❌ 单独子库 | whisper-1, advanced-voice |
| `video` | 视频生成 | ❌ 单独子库 | sora, kling |
| `multimodal` | 纯多模态非对话 | ❌ 视情况 | avatar |
| `other` | 其他非对话专用端点 | ❌ 单独归类 | jev-preview(判别模型), omni-moderation(内容审核) |
| `invalid` | 脏数据/截断ID | ❌ 清理出库 | `accounts/fireworks/models/` |

> **`other` 格是 10/4 补的**。原 8 格表没有它，但上游 LiteLLM 存在
> evaluation / search / moderation / guardrail 四类非对话端点（实测 4473 条里 41 条）。
> 10/4 实测 `nimble`/`english`/`multilingual`/`typed-decisions`/`jev-preview`
> （Bespoke、Typesafe、Laya 的判别模型，source=litellm，mode=evaluation）
> 在旧规则下全部回落成 chat 污染主榜。塞进 chat 之前先在词表补这一格。

判定规则（**优先级从高到低，10/4 修正**），实现见 `scripts/align/classify_model_type.py`：
1. **上游 LiteLLM `mode` 字段优先** —— `MODEL_DATA_STANDARD` §1.1 原规则只有关键词，
   而关键词只认 `dall-e`/`flux`/`bge-` 这类明显词根。实测 82 处冲突：
   `deepgram/nova`、`vertex_ai/chirp`（语音）、`voyage/voyage-3.5`（向量）、
   `stability/sd3.5-large`（图像）、`runwayml/gen4.5`（视频）——
   这些 ID 里没有任何词根，靠字符串永远猜不出来。上游 mode 是逐条维护的端点语义标注，
   且有 `supported_endpoints` 可交叉印证（`chirp → /v1/audio/speech`）。
   ⚠️ **但上游自报 `chat` 时要让关键词复核**：实测 19 例上游把 `flux-1-dev`（图像）、
   `codestral-embed`（向量）、`gpt-audio`（语音）都标成 chat，只有细分词根能识别。
2. **关键词** —— image: dall-e/flux/sdxl/ssd-1b/stable-diffusion/imagen/seedream；
   embedding: bge/embed/uae-large/gte-/e5-/jina/m3e/nomic-embed；rerank: rerank；
   other: moderation；audio: voice/whisper/tts/audio/speech；
   video: video/veo/sora/kling/vidu/seedance
3. **vendor 权威性** —— vendor 非空 ⇒ 真实模型 ⇒ 短 ID（`o1`/`o3`）也不判 invalid
4. **路径形态** —— 以 `/` 结尾、空串 ⇒ invalid（唯一压过前三条的例外）

**收录门槛**：只有 model_type=chat 进价格主榜与对撞名裁决。其余类型可入库但单独标注，不参与对话模型的别名归一和排名。

### 1.2 门槛的落地位置（10/4 补：原规范只写"应该"，没写"在哪生效"）

§1.1 的门槛从 2026-06-20 写下起，**三个月内零个代码读 `model_type`**。落地当天实测
L1 主榜 3072 个模型里 616 个是非 chat。现已生效，四个落点：

| 落点 | 位置 | 说明 |
|---|---|---|
| 主榜装配 | `web/server.py` `_load_price_data()` | 分组前按 `_type_map` 过滤，剔除计数写入 `excluded_non_chat_entries` |
| 热门模型榜 | `web/server.py` `_build_prices_hot_models()` + `_build_homepage_data()` 第 4 段 | 两份逐字相同的 SQL，**改一处必须改另一处** |
| 相关模型带 | `web/server.py` L3 详情页 `related_hot` | 同口径 |
| 字段正确性 | `scripts/align/classify_model_type.py --check` + DB CHECK 约束 | migration `20261004_0009` 两条 CHECK 兜底 |

**fail-closed 原则**：查不到 `model_type` 一律不进主榜。原实现写成 `if _mt and _mt != "chat"`，
空值直接放行 —— 10/4 实测有 15 个 `p0d_merge` 孤儿（codellama 系列，有报价有别名但
`model_canonical` 缺行）正是靠这个后门混进主榜的。已补齐（`backfill_orphan_price_canonical.py`），
且门槛改为 `_mt != "chat"`。

**归一碰撞取非 chat 优先**：`web/server.py` 的 `_normalize_model_name()` 会剥掉
`-latest`/`-preview` 后缀，于是 `openai/gpt-image-2`(image) 与 `gpt-image-2`(chat)
归一后同名。实测 6 例碰撞（gpt-image-2 / nano-banana-pro / mai-image-2.5 系列）。
原实现"先写入者胜"，chat 覆盖 image；现改为非 chat 优先 —— 门槛宁可少展示不可错展示。

**守卫**：`scripts/audit/verify_price_model_type_gate.py`（哨兵 5k 项），
配套 `tests/test_price_model_type_gate.py` 19 项含 4 项负向验证。

---

## 二、厂商归属（vendor）填充标准

现状：696 行 vendor 100% 非空，但 142 行=unknown（20%）。其中 28 个是上面的非 chat 类型（归类后自然消失），112 个是真 chat LLM 缺厂商。

### 2.1 权威证据来源（优先级从高到低）

1. **HuggingFace 官方 org**（最高）——owner 在权威白名单内即采信
2. **HF repo 名内嵌官方前缀**——社区量化版 repo 名常含 `baichuan-inc_xxx`，反解官方 org
3. **魔搭 ModelScope**（HF 搜不到的国产模型走魔搭）
4. **厂商官方文档/API 页**（闭源 API 模型如 codestral/dbrx 无 HF 权重时兜底）
5. **标记 `需文档兜底`**——前4步都拿不到，绝不猜测

### 2.2 关键陷阱（实测发现，必守）

⚠️ **HF search 按 downloads 排序，top1 往往是社区量化版（TheBloke/bartowski/mlx-community/GGUF/AWQ），不是官方仓库。直接取 top1 的 owner 会把厂商误判成量化作者**（实测 dbrx→dranger003、baichuan→bartowski 全错）。

正确做法：
- 维护「权威 org 白名单」`OFFICIAL_ORGS`（cohereforai→cohere, mistralai→mistral, meta-llama→meta, qwen→alibaba, deepseek-ai→deepseek, baichuan-inc→baichuan, databricks→databricks, fireworks-ai→fireworks ...）
- 维护「量化作者黑名单」`QUANT_OWNERS`（thebloke/bartowski/mlx-community/maziyarpanahi/lewdiculous/dranger003/mradermacher/unsloth ...）
- owner 命中白名单 → 直接采信；owner 命中黑名单或 repo 名含 gguf/awq/-bit → 从 repo 名反解官方前缀
- 反解也拿不到官方 → 标 `需文档兜底`，进人工核对队列

白名单/黑名单是**持续积累的资产**，每次补全遇到新官方 org 就追加，越用越准。

---

## 三、别名映射标准（model_alias 三级置信度）

现状：737 行 alias，688 条（93%）来自抓价时自动插入（unverified），22 条（3%）人工维护的 model_aliases.json，27 条（4%）归一化修正。**93% 的别名是"抓到啥算啥"，没有可信度标注，无法区分"OpenAI 官方确认的同一模型" 和 "某中转站自己起的奇怪名字"。**

### 3.1 新增字段 confidence（别名落库必带）

| confidence | 来源 | 含义 | 处理 |
|---|---|---|---|
| `official` | 厂商官方文档/model_aliases.json 人工校对 | 厂商确认的同一模型别名 | 直接采信，参与归一 |
| `framework` | 开源框架自报（New-API /api/pricing 的 model 字段、HF base_model 标签） | 框架/厂商声明的映射 | 采信，可抽检 |
| `auto` | 抓价时自动插入，未经校对 | 仅"见过这个名字"，映射关系未验证 | **不可直接信**，需升级到上面两级才参与归一 |

### 3.2 别名归一规则（对撞名裁决依据）

承接 P0-D 对齐裁决（已落 P0D_对齐裁决清单_2026-06-20.csv，70 组）：

1. **A 类 归一化残留（40 组）**：纯机械 p→. 还原（qwen2p5→qwen2.5, v3p1→v3.1, p0p5→p0.5）。零判断，脚本直接合并。
2. **B 类 对话后缀（5 组）**：-instruct/-chat/-it 后缀差异，合并到主条目。
3. **C 类 真 base 权重（21 组）**：HF API 实测确认为 base 权重（CodeLlama/Mistral-7B-v0.1/Mixtral-v0.1/Qwen2.5-32B/Kimi-K2-Base/Yi-34B 等，200 OK 且无上游 base_model 标签）。产品合并到 instruct 但保留 base 标注（99% 中转站卖 instruct）。
4. **C 类 厂商独立产品（4 组）**：gpt-3.5-turbo-instruct、gpt-5-chat/5.1-chat/5.2-chat——厂商独立 SKU，**保持拆分**。

判据全部可机器验证（p→. 规则 / HF base_model 标签 / 厂商文档），不依赖人工主观。详见 skill `tokenapi-model-alignment`。

---

## 四、字段完整度路线（model_canonical 当前缺口）

> ⚠️ **本表数字由 `scripts/audit/verify_doc_coverage_claims.py` 逐行实测核对
> （哨兵 5l 项，容差 ±2 个百分点）。改数据后必须同步改这里，否则哨兵报 FAIL。**
>
> **10/4 首次机器化**：这张表从写下起无人核对，实测四行全漂 ——
> `vendor` 文档写 80% 实为 **52.7%**（虚高 27 点，读者据此以为"只剩 20% 要补"，
> 实际 47.3%）、`release_date` 写 0% 实为 3.9%、`is_thinking` 写 0% 实为
> **全表有值**。**一张从不核对的现状表既制造假绿，又把真实缺口藏起来。**

| 字段 | 当前填充率 | 目标 | 来源 |
|---|---|---|---|
| canonical_id | 100%（5697 行中 1 行为空，99.98%） | 维持 | 归一化 |
| vendor | **52.7%**（unknown 2693 行 = 47.3%） | chat 类 ≥98%（实测 chat 内 58.7%） | 本标准第二节 |
| model_type | ✅ 100%（10/4 落库 5697 行；migration 0008 迁移 + 0009 两条 CHECK 约束 + `--check` 漂移守卫） | 维持 | 本标准第一节 |
| variant | 0%（全表 NULL） | chat 类逐步补 | HF/厂商 |
| release_date | 3.9%（220 行） | 旗舰模型优先 | 厂商发布页 |
| is_thinking | **100% 有值，但仅 2.0% 为 1**（116/5697） | 按需 | 厂商文档 |
| is_vision | **100% 有值，但仅 3.4% 为 1**（192/5697） | 按需 | 厂商文档 |
| is_audio | **100% 有值，但仅 0.5% 为 1**（30/5697） | 按需 | 厂商文档 |

> **`is_*` 三个能力位的坑（10/4 实测）**：列名是 `is_vision`/`is_audio`，
> 不是 `vision`/`audio`（原表写错，查文档的人会去 SELECT 不存在的列）。
> 更本质的是**它们不是"没填"而是"填满了 0"** —— 全表 5697 行都有值，
> 但只有 116/192/30 行为 1。**任何 `NOT NULL` 检查都不会报警**，
> 覆盖率 100% 还会给人"这字段已填满"的错觉。
> 判断这类布尔位的健康度要看 `=1 占比`（`pct_set`），不看填充率。
> 真正的债是这 1946 个 chat 模型里绝大多数没有能力标注 —— 
> 要补只能从厂商文档/HF 逐个查，属于"按需迭代"范畴，不是靠检查能解决的。

原则：**先把 chat 收录边界和 vendor 补到位（地基），variant/release_date/能力位按需迭代，不一次性大改**（用户偏好：每天小步迭代）。

---

## 五、抽检校验门槛（落库前强制）

任何批量字段填充落 DB 前：
1. 随机抽 5-10 条，对比权威源（HF/魔搭/厂商文档）人工确认正确
2. 价格类抽检对比源 API（见 skill tokenapi-price-scraping）
3. 备份 DB（本地备份，禁 git checkout）再写
4. 记录到 normalize_run 表，留可追溯日志

违反抽检直接落库 = 违反 AGENTS.md 抽检校验铁律。
