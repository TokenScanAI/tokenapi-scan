# 价格页标准（PRICE_PAGE_STANDARD）

适用范围：`/prices`、`/prices/{model}`、`/price/{model}/{provider}`、`/sitemap-prices.xml`，以及所有价格页内部链接、模型 slug、服务商入口。

本标准是当前权威入口。历史事故和长篇过程记录可参考 Hermes skills，但实际执行以本文和脚本验收为准。

## 1. 页面分层

| 层级 | URL | 职责 | 不做什么 |
|---|---|---|---|
| L1 摘要页 | `/prices` | 热门模型摘要、最低价、筛选、服务商入口 | 不内嵌逐家大表，不塞全量明细 |
| 模型聚合页 | `/prices/{model}` | 一个模型/SKU 在多 provider 的报价、source、fetched_at | 不用展示名生成 canonical URL |
| L3 细节页 | `/price/{model}/{provider}` | 单模型 × 单 provider 的 SEO 细节页、Product/Offer 结构化 | 不合并到主 sitemap |
| 价格 sitemap | `/sitemap-prices.xml` | 价格详情 URL 独立提交，启动量受控 | 不和主 sitemap 混在一起 |

## 2. URL 与 slug 规则

铁律：展示名不能当 canonical URL。

- 详情页链接必须从真实 `canonical_id` / `sku_id` / `raw_model_id` 生成。
- slug 只做 URL 安全归一，不得全局删除 `-instruct`、`-chat`、`-preview`、`-latest`、`-codex` 等后缀。
- 展示名 slug 只允许作为旧 URL 兜底：命中后 301 到真实 SKU URL。
- 301 必须检查自循环；`/prices/x` 不能重定向回 `/prices/x`。
- `qwen3-coder-30b-a3b` 这类展示名可以聚合显示，但真实有价 SKU 如果是 `qwen3-coder-30b-a3b-instruct`，链接必须指向后者。

## 3. L1 摘要页职责

`/prices` 是摘要和导航页：

- 显示最低价、价格带、证据覆盖、已定价 provider 数。
- 完整逐家对比交给 `/prices/{model}`。
- 单 provider 细节交给 `/price/{model}/{provider}`。
- L1 可以为了用户理解聚合展示名，但不能丢失 SKU 精确路由。
- 有报价模型优先保留；无报价 pending 模型可以限量展示。

## 4. 服务商目录与下架站

`/prices` 的服务商目录只展示当前仍在收录/检测范围内的 provider。

- `merged_providers` 必须携带 `service_status`。
- `service_status == 'discontinued'` 不得进入主服务商分类目录。
- discontinued provider 进入折叠区：`历史档案：N 家已下架服务商（不参与当前价格筛选）`。
- 历史档案链接保留到 `/site/{id}#price`，不做 404。
- 主目录文案必须写“当前仍在收录/检测范围内”，不能写“所有已收录服务商”。
- 主目录里不能显示 discontinued 为“收集中”。

## 5. 价格可信度字段

价格详情页和底层数据必须保留来源信息：

- `price.source` 不应为空。
- `fetched_at` 必须保存日期/时间。
- 页面逐条报价展示 source + fetched_at。
- source 写来源类型或来源 URL；日期不要塞进 source。
- 横评/二级源价格不得标成实时价，必要时标“历史横评价 / 非实时抓取 / 仅供参考”。

## 6. sitemap 与 SEO

- 价格详情 URL 使用独立 `/sitemap-prices.xml`。
- 启动量受控，按真实索引反馈逐步扩量。
- lastmod 必须真实，不能批量伪造当天日期。
- discontinued provider 不主动推入 sitemap。
- L3 页必须有 canonical、title、description、Schema.org Product/Offer。

## 7. 发布前验收

每次修改价格页、slug、价格数据、provider 状态后，至少执行：

```bash
cd $REPO_ROOT
python3 -m py_compile web/server.py
python3 scripts/audit/verify_price_page_links.py
bash <hermes-config>/skills/tokenapi-scan/tokenapi-scan-docs/scripts/verify_v2_health.sh
```

> **2026-10-03 起 `verify_price_page_links.py` 已由哨兵第 5d 项自动执行。**
>
> 它此前**从未被任何东西调用过**（只有本文档和 skill 引用），而且坏在一个特别
> 隐蔽的地方：574 条内部链接是**串行** fetch（最坏 57 分钟、实测 90 秒），
> 而所有结果都在**最后**才 print。任何带 `timeout` 的调用方都会在它打印之前
> 把它 kill 掉，于是拿到**零输出**——而零输出与「通过」无法区分。
> 已改为 10 线程并发（90s → 15s）+ 首行即输出进度 + 哨兵显式区分
> 「超时退出码 124」与「审计发现违规」。

必须满足：

- `/prices` 200。
- 渲染后内部链接 BAD=0。
- `/prices/*` 自循环重定向=0。
- discontinued provider 不在主服务商目录。
- retired cards 数量等于 seed 中 discontinued 数量。
- 抽测用户点名模型 200 或合理 301 到真实 SKU。
