# 数据质量审计标准（DATA_QUALITY_AUDIT_STANDARD）

适用范围：页面数字对不上、价格家数不一致、协议覆盖数异常、audit 接续、checkpoint 复核、DB/JSON/runtime 多源数据冲突。

## 1. 基本原则

看到“数字不对”先不要改页面，也不要归因“数据不足”。先列数据源，再逐源实测。

常见数据源：

- SQLite 表：`price`、`provider`、`detection`、`model_canonical`、`model_alias`、`model_spu`、`model_sku`
- SQLite view：`v_price_canonical` 等
- JSON：`latest_prices.json`、`seed_providers.json`、report JSON、ranking JSON
- runtime：`web/server.py::_load_price_data()` 的装配结果
- 模板上下文：Jinja 传入字段
- 线上渲染：`curl http://https://tokenscanai.com/...`
- sitemap 渲染结果
- cron 输出和文件 mtime

## 2. 三件套诊断

对同一个 provider/model，同步查三类证据：

```bash
# DB
sqlite3 web_data/db/tokenapi.db "SELECT ...;"

# JSON/runtime
python3 - <<'PY'
import json
# 读取 latest_prices.json / seed_providers.json / report
PY

# 页面渲染
curl -sS http://https://tokenscanai.com/prices | python3 - <<'PY'
# 解析页面文本/链接/计数
PY
```

把三个数字并排后再判断：

- DB 有，页面没有：模板/runtime 读错源或过滤过度。
- JSON 有，DB 没有：ETL 未入库或 canonical 归一失败。
- 页面有，DB/JSON 都没有：缓存、旧目录、硬编码或 report 源混入。
- sitemap 有，页面没有：URL 生成规则与页面入口不一致。

## 3. 接手 audit/checkpoint 的重测铁律

上一个 agent 的 audit 数字只能当线索，不能当事实。

- 接续任务第一步跑哨兵：`verify_v2_health.sh`。
- audit 数字必须重跑 SQL/curl/脚本。
- 发现一处数字不符，整组相关 audit 全部重验。
- 禁止凭“已完成清单”继续做新功能。

## 4. 多源合并决策

把新数据源合并到排行榜、价格页、首页榜单前，先做三检查：

1. schema 是否同维度。
2. join key 是否稳定。
3. metric 单位是否相同。

任一不一致，不得直接 union 到同一 bucket。改用：

- 辅助列
- 独立分组
- 过滤器
- 页面明确标注口径

## 5. 常见事故模式

- latest_prices 扁平/嵌套结构混用，导致误判 provider 空壳。
- L1 卡片读 runtime，L3 内页读 DB，家数不一致。
- detection 表已有三协议，但页面读手动 report JSON，协议覆盖数显示 1。
- cron last_status=ok，但脚本读旧软链目录。
- discontinued 0% 连通率被误报成故障。
- `error_kind` 脏数据不可用于错误分组，应优先用 `success` 和 `error_msg`。

## 6. 输出要求

审计报告必须写清：

- 查了哪些源。
- 每个源的实际数字。
- 哪个源是黄金源。
- 当前是“数据缺失”“读错源”“过滤错误”“缓存/旧路径”还是“页面文案口径问题”。
- 已跑哪些验证命令，输出是什么。
