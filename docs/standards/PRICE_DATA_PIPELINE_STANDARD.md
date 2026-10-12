# 价格数据管道标准（PRICE_DATA_PIPELINE_STANDARD）

适用范围：公开价格抓取、New-API/One-API 价格探测、`latest_prices.json`、SQLite `price` 表、历史快照、价格 ETL、价格 cron。

## 1. 三段链路

价格数据必须按三段闭环运行：

```text
[抓源] crawler/run_crawler.py / scripts/crawl/fetch_framework_prices.py
  -> web_data/crawler/latest_prices.json
[存档] crawler/save_price_snapshot.py
  -> web_data/crawler/history/YYYY-MM-DD.json
[入库] scripts/etl/run_all.py / scripts/etl/load_price.py
  -> web_data/db/tokenapi.db price / model_* / v_price_canonical
```

ETL 只重复入库旧 JSON 不等于价格自动刷新。抓源、存档、入库三段要串行确认。

## 2. 数据源优先级

优先使用可自动校验、低反爬、覆盖广的公开源：

1. OpenRouter API
2. LiteLLM model_prices JSON
3. New-API / One-API `/api/pricing` 等公开端点
4. 官方文档/API 价表
5. 横评/README/二级源（必须标历史/自报/非实时）

登录墙或无公开价时，不伪造数据。标“无公开价”或保留历史源。

## 3. New-API/One-API 入库红线

- 只取 `quota_type == 0` 的 token 文本模型。
- 按站点默认 group_ratio 计算展示价，不挑特殊折扣组误导用户。
- `model_ratio` 换算必须先用官方锚点模型抽检。
- 新模型、图像模型、按次模型、completion_ratio 明显非 token 语义的模型，不套公式入库。
- 每家站至少抽检 3-5 个官方锚点模型后再放行。

## 4. source / fetched_at 规范

- `source` 表示来源类型或来源 URL，不表示日期。
- 日期写入 `fetched_at`。
- `price.source` 不应为空。
- 二级源可用 `claude-api-relay-review`、`framework-pricing`、`openrouter`、`litellm`、`relay-crawler`、`manual` 等明确标签。
- 横评旧价页面必须展示时间，避免误认实时价。

## 5. latest_prices.json 结构兼容

下游必须兼容两类结构：

- 扁平：`provider -> model -> price`
- 嵌套：`provider -> models -> model -> price`

任何“某 N 家 provider 全空”的结论都必须先区分这两种结构统计，不能只 `.get('models')`。

## 6. 入库前后验收

入库前：

```bash
cp web_data/db/tokenapi.db web_data/db/backups/tokenapi.db.bak.$(date +%Y%m%d_%H%M%S)
```

入库后：

```bash
cd $REPO_ROOT
sqlite3 web_data/db/tokenapi.db 'PRAGMA integrity_check;'
sqlite3 web_data/db/tokenapi.db "SELECT COUNT(*) FROM price WHERE source IS NULL OR TRIM(source)='';"
python3 scripts/audit/verify_price_data_quality.py
python3 scripts/audit/verify_price_page_links.py
```

必须满足：

- DB integrity 为 `ok`。
- `price.source` 空值为 0。
- 抽检源头价格与 DB price 一致。
- `/prices` 和 `/sitemap-prices.xml` 无死链。
- L1 卡片和 L3 内页口径不出现明显分裂。

## 7. cron 规则

- 抓源频率不宜过高；价格源通常每日一次足够。
- 抓源必须在 ETL 前完成。
- CN 服务器访问 OpenRouter/GitHub raw/archive 等外部源默认走 `$LOCAL_PROXY` 代理。
- 脚本必须在仓库或 `<hermes-config>/scripts/`，不能放 `/tmp`。
- cron `last_status=ok` 不代表读对数据；必须检查输出里的路径和数据 mtime。
