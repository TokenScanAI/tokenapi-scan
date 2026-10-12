# Provider 状态标准（PROVIDER_STATUS_STANDARD）

适用范围：`seed_providers.json`、`provider.service_status`、`/site`、`/site/{slug}`、`/leaderboard`、`/prices` 服务商目录、sitemap、巡检/红黑榜解释。

## 1. 状态字段

核心字段：`service_status`。

| 状态 | 含义 | 页面语义 |
|---|---|---|
| `active` | 当前仍在监控/展示范围内 | 正常展示，参与当前筛选和推荐 |
| `discontinued` | 已停运、下架、不可作为当前服务商推荐 | 保留历史档案，不参与当前推荐/价格筛选 |
| `crawler_error` | 抓取异常或端点不可稳定判定 | 进入观察/异常区，不直接定性停运 |
| `insufficient` | 证据不足 | 数据收集中，不进强结论 |
| `needs_review` | 需人工复核 | 不自动晋升，不强推荐 |

当前最重要的稳定规则是 discontinued 的全站一致处理。

## 2. discontinued 统一展示策略

下架站不是删除，也不是 404。统一策略：历史档案保留，当前入口降权。

| 页面/模块 | 处理 |
|---|---|
| `/site/{slug}` | 保留 200，作为历史档案和旧链接收口 |
| `/site` 主目录 | 卡片灰显、降透明、已停运角标、排序降权 |
| `/leaderboard` 主榜 | 不参与正常红黑榜结论；A-Z 索引灰显并标“已停” |
| `/leaderboard/{site_id}` 旧入口 | 301 到 `/site/{slug}` |
| `/prices` 主服务商目录 | 不展示为当前可选服务商 |
| `/prices` 历史档案 | 折叠展示，文案注明“不参与当前价格筛选” |
| sitemap | 不主动推送 discontinued 站点 |
| 巡检/连通率 | 0% 对 discontinued 是预期，不算故障 |

## 3. 数据装配要求

凡是构建 provider entry 的地方都必须携带：

- `id`
- `name`
- `category`
- `service_status`
- `homepage`
- `endpoint_domain`
- `models_total` / `models_priced`（价格页需要）
- `updated_at`（如有）

禁止某页自己重新构造 provider 时漏掉 `service_status`。

## 4. 文案标准

推荐文案：

- 卡片角标：`已停运` 或 `已下架`
- 历史区标题：`历史档案：N 家已下架服务商（不参与当前价格筛选）`
- 说明：`仅保留历史档案，不参与当前推荐/价格筛选`

避免文案：

- “收集中”用于 discontinued 站。
- “所有已收录服务商”用于当前服务商目录。
- 把 discontinued 0% 连通率写成“故障”或“风险升高”。

## 5. 验收脚本

每次改 `service_status`、`seed_providers.json`、`/site`、`/leaderboard`、`/prices` 服务商目录后执行：

```bash
cd $REPO_ROOT
python3 scripts/audit/verify_provider_status_consistency.py
python3 scripts/audit/verify_price_page_links.py
```

> **2026-10-03 起这两个脚本已由哨兵自动执行**（`verify_v2_health.sh` 第 5d/5e 项）。
> 本节保留给需要单独复现时用。
>
> 为什么改：这两个脚本从 6/21 写好后**零调用方** —— 只有文档引用，从未跑过。
> 实测两个都坏：provider_status 的 `fetch()` 不 catch `URLError`/`TimeoutError`，
> 网络抖一下整个审计抛 traceback 崩掉；`price_page_links` 串行 574 链接要 90s
> 且全部结果在最后 print，任何带 `timeout` 的调用方都会在打印前 kill 掉它，
> 拿到**零输出**——而零输出和「通过」长得一模一样。
>
> 判据也修过一处假通过：`data-status="discontinued"` 原先是**页面级**判断
> （`data-id="x" in html and 'data-status="discontinued"' in html`），
> 同屏 7 个停运站时任意一个站的状态都能顶成全通过。现改为 provider 级
> （`card_marked()` 要求同一张 `<article>` 标签内同时带 `data-id` 和
> `data-status`；`_badge_after_anchor()` 要求徽标落在该站自己的 `<a>` 内）。
> 回归测试：`scripts/audit/test_audit_judgements.py`（10 项，含 4 项反例）。

必须满足：

- seed 中 discontinued 数量与 `/prices` 历史档案卡数量一致。
- discontinued 不出现在 `/prices` 主目录。
- `/site/{id}` 返回 200。
- `/leaderboard/{id}` 返回 301/302 到 `/site/{id}`。
- `/site` 页面存在 `data-status="discontinued"`。
- sitemap 不主动包含 discontinued 的 `/site/{id}`。
