# 撞名归类客观判据标准 (Collision Classification Standard)

> 核心命题:撞名归类**不依赖人工分辨**。每一组都能引用客观可验证的数据落到确定类别。
> 验证脚本:`scripts/align/auto_classify_collision.py`(可复跑,可入 cron)
> 实测基线 2026-06-20:71 组撞名,需人工 = **0 组**。

## 四层客观判据(按优先级短路)

判据按下列顺序逐层判定,命中即停。每层都引用机器可读的客观信号,不引入人类主观判断。

### A 机械合并 — 字符串归一证据
- **信号**:`normp()` 处理后(p→. 还原、大小写归一)两个 ID 字符串完全相同。
- **例**:`deepseek-v2.5` vs `deepseek-v2p5`;`code-qwen-1.5-7b` vs `code-qwen-1p5-7b`。
- **裁决**:直接合并。这是抓取写法差异,根本不是两个模型。零判断。
- **占比**:40/71。

### C 厂商独立产品 — 多权威源交叉验证证据(自动确认,零人工)
- **核心**:闭源模型"该不该拆"不依赖人工点头,靠多个互相独立的权威源交叉投票自动确认。
- **三源投票**:
  - 源A `OpenRouter /api/v1/models`(第三方聚合,680+ id)
  - 源B `models.dev/api.json`(开放模型元数据库,带官方 provider 归属,2600+ id)
  - 源C 价格签名异价(本地 DB,仅作"否定证据":异价→铁定不同 SKU;同价不反推同物)
- **判定**:任一权威源把组里 >=2 成员各自当独立 model id 上架 → **自动确认拆分**;
  全部源都不支持独立 → **自动确认合并**;仅当两上架源结论矛盾且无异价破局才升级人工(实测=0)。
- **例**:gpt-5/gpt-5-chat → OpenRouter ✓ + models.dev ✓(同价,但双源独立上架)→ 自动拆分,无需人工。
- **铁律**:**SKU 不靠价格判同异**。价格异价只能作拆分的否定证据,同价不能当合并的肯定证据。
- **可程序化、新代际自动覆盖**:gpt-6/gpt-6-chat 上架即被两源识别,无需改代码、无需人工。
- 数据源缓存:`authority_model_ids.json` + `modelsdev_ids.json`(带时间戳,联网失败回退)。
- **占比**:4/70(4 组全部双源确认拆分)。
- 引擎脚本:`scripts/align/cross_verify_collision.py`(可入 cron,产投票明细 CSV)。

### B 后缀变体 — 官方后缀 + 市场信号证据
- **信号1**:成员仅相差官方后缀(`-instruct`/`-chat`/`-it`/`-hf`),且有开放权重(非 closed_api)。
- **信号2(市场信号)**:用**在售家数**(`COUNT(DISTINCT provider_id)`)决定展示主版本——市场用脚投票,谁主流展示谁。
- **裁决**:合并到市场在售家数最多的变体,保留 base/instruct 权重差异注记。
- **例**:`gemma-7b`(1家) vs `gemma-7b-it`(3家)→ 主版 gemma-7b-it。
- **占比**:27/71。

### D 需人工 — 唯一的人工边界
- **信号**:以上三层均未命中。
- **2026-06-20 实测:0 组**。即当前数据下不存在必须人工分辨的撞名。
- 一旦未来出现 D 类组,才进入人工队列;且应回头补强 A/B/C 判据或权威源,把 D 重新降为可自动判定。

## 为什么不需要人工

| 过去的"人工判断" | 替换为客观信号 |
|---|---|
| "这俩是不是同一个模型" | normp 后字符串是否相同 |
| "base 和 instruct 要不要合" | authority_map base_model 关系 + 市场在售家数定主版 |
| "闭源 -chat 是独立产品吗" | 权威源(OpenRouter)是否各自独立上架 model id(不靠价格) |
| "展示哪个为主版" | 市场在售家数(provider_count) |

人工判断的本质被拆解为:**字符串归一 + 权威关系(HF base_model) + 权威源独立上架(OpenRouter model id) + 市场在售信号**。四者皆机器可读、可复跑、可审计。

> ⚠️ 历史教训:C 层一度用"价格签名异同"判同/异 SKU,违反"SKU 不靠价格判同异"铁律(gpt-5 与 gpt-5-chat 同价但是两个 SKU,会被误并)。现已统一改为权威源独立上架判据,两个脚本(verify_collisions.py / auto_classify_collision.py)判据一致,消除漂移。

## 例行化(已闭环,零人工)

### 周巡检 cron(已部署 2026-06-20)
- Hermes cron `tokenapi_collision_weekly.py`,每周日 04:30 自动跑,`no_agent` 纯脚本。
- 流程:跑 cross_verify → 对比基线 `.collision_baseline.json` → A 类自动入库(幂等)→
  只在「新撞名组 / 分类变化 / D 类」时写 `web_data/push_queue`,由既有 08:20 队列发微信。
- **静默原则**:无变化不打扰(符合「陈旧告警只报增量」);复用 08:20 队列,不新建独立微信 cron。

### 手动复跑
```bash
# 主入口: 多权威源交叉验证(自动确认 C 类拆分,零人工)
python3 scripts/align/cross_verify_collision.py --csv
# 备用: 单源 + HF 判据(快,无 models.dev)
python3 scripts/align/verify_collisions.py
# 入库: 幂等、事务安全、可 dry-run(不加 --commit 只打印)
python3 scripts/align/apply_p0d_verdicts.py            # dry-run
python3 scripts/align/apply_p0d_verdicts.py --commit   # 写库(先备份 DB)
```

### 入库执行器 apply_p0d_verdicts.py(2026-06-20 新增)
- A 类 → `UPDATE OR IGNORE price.canonical_id=normp(标准形式)`,撞主键的等价重复行 DELETE,登记 `model_alias(source=p0d_merge)`。
- C-厂商独立 → 数据不动,登记 `model_alias(source=p0d_split_locked, evidence=双源证据)`,防未来误并。
- 全程单事务,异常自动 rollback。幂等:重复跑无副作用(已归一的 no-op)。

### ⚠️ 覆盖盲区铁律(2026-06-20 实战教训)
裁决 CSV 只列**成对撞名组**,孤立的写法变体(`qwen2p5-32b`、`code-llama-13b` 这类没有 `.` 对照、没撞名的)
**不在 CSV 里**,会漏归一。入库器必须在 CSV 之外**全量扫 DB**:
`SELECT DISTINCT canonical_id FROM price WHERE 匹配 \dp\d|llama-v\d|code-llama → normp 归一`。
本期实测:CSV 内 49 组 + 全量兜底扫出 49 个孤立写法(20 个 \dp\d + 29 个 code-llama),
最终 canonical_id 从 ~590 收敛到 541,残留非标准写法 = 0。**只信 CSV 必漏,归一铁律要全量真扫。**

### 升级路径
- 若输出「需人工组数 > 0」(D 类),写 push 告警,人工只看升级组(实测长期为 0)。
- 出现 D 类后应回头补强 A/B/C 判据或权威源,把 D 重新降为可自动判定。
