# 开源中转框架指纹库 + 公开价格端点探测标准 v1

定稿：2026-06-20　适用：$REPO_ROOT 价格抓取扩面
配套脚本：scripts/crawl/probe_framework.py　关联 skill：tokenapi-price-scraping

本文档推翻旧结论"中转站登录墙 100% 不可破"。实测：多数中转站基于开源框架（New-API/One-API/Veloera），
其 `/api/pricing` 等端点**无需鉴权即可公开访问**，可系统化批量恢复价格。

---

## 一、核心原则：端点硬证据 > HTML 指纹

⚠️ **不要只靠首页 HTML 指纹判断。实测 whatai/apiyi/deepkey 首页指纹识别为"未知"，但 /api/pricing 返回 1049/329/186 条价格数据。**

判定顺序：
1. **先打公开端点**（/api/pricing → /api/models → /api/ratio_config）——返回 JSON 且含 `data`/`model_ratio`/`success` = 硬证据，可用
2. HTML 指纹（`__APP_CONFIG__`/new-api/one-api/veloera）仅作辅助，帮助理解框架类型和字段语义

---

## 二、实测探测结果（2026-06-20，15 个候选中转站）

| 域名 | 框架指纹 | 公开端点 | 模型条目 | 备注 |
|---|---|---|---|---|
| api.whatai.cc | 未知 | /api/pricing | **1049** | 神马中转，最大 |
| api.apiyi.com | 未知 | /api/pricing | 329 | APIYI |
| deepkey.top | 未知 | /api/pricing | 186 | |
| www.packyapi.com | 未知 | /api/pricing | 52 | |
| 1xm.ai | 未知 | /api/pricing | 31 | OneXModel |
| hk.rootflowai.com | 未知 | /api/pricing | 30 | |
| api.vectorengine.ai | 未知 | /api/pricing | 5 | |
| api.muskapi.cc | New-API系 | /api/pricing | 0* | 端点存在，data 空，需 token |
| api.nekoapi.com | 未知 | /api/ratio_config | 0* | ratio 字典，无 base 锚 |
| timicc.com / ddshub.cc / clawapi | New-API系 | 无 | 0 | 端点关闭或改路径 |
| api.koozhan.com / poloapi / laozhang | 未知 | 无 | 0 | 无公开端点 |

**结论：9/15 站可公开恢复价格，合计 1682 模型条目**（旧分析只发现 4 站）。

---

## 三、价格转换公式（New-API 系，已抽检验证）

/api/pricing 返回的是 ratio（倍率），不是直接价格。换算：

```
input_price_usd_per_1m  = model_ratio × 2.0          # New-API 硬编码基价 $2/1M per ratio
output_price_usd_per_1m = input_price × completion_ratio
```

抽检验证（whatai，对照 OpenAI 官方）：
- gpt-4o-mini：model_ratio=0.075 → $0.15，completion_ratio=4 → $0.6　✓ 完全符合官方
- gpt-4o：model_ratio=1.25 → $2.5，completion_ratio=4 → $10　✓ 完全符合
- gpt-4.1：model_ratio=1 → $2，completion_ratio=2 → $4（官方 $8）

⚠️ **completion_ratio 是各站自定义的，不能假设统一**（whatai 给 gpt-4.1 设 2 而非官方 4）。输出价必须用该站自己的 completion_ratio 算，禁止套官方比例。

---

## 四、字段辨别（避免脏数据入库）

/api/pricing 单条关键字段：

| 字段 | 含义 | 处理 |
|---|---|---|
| `model_name` | 模型名 | 走归一化 + alias |
| `quota_type` | 计费类型：0=按 token，1=按次 | **只有 quota_type=0 套 ratio 公式；=1（图像/视频）读 model_price 固定价，单独标 model_type** |
| `model_ratio` | 输入倍率 | × 2.0 = 输入价 |
| `completion_ratio` | 输出/输入比 | 各站自定义，本站值算输出价 |
| `model_price` | 固定单价（按次模型用） | quota_type=1 时直接采用 |
| `vendor_id` / `owner_by` | 厂商线索 | 辅助 vendor 归属 |

---

## 五、落库红线（继承 tokenapi-price-scraping + 模型数据标准）

1. **只对有官方价锚的 text 模型套 ratio 公式入库**。新模型（无官方锚可验证）、图像模型（quota_type=1）禁止套公式。
2. 落库前抽检 5-10 条对照官方价，公式算得偏差 > 10% 的标记复核。
3. 该批价格 confidence 标 `framework`（框架自报），不是 `official`。
4. source 字段写明 `{domain}_apipricing_{date}`，可追溯。
5. 备份 DB（本地备份）后再 ETL，记录 normalize_run。

---

## 六、例行扩面 SOP

1. 新中转站进 seed → 跑 `probe_framework.py <domain>` 看是否有公开端点
2. 有端点 → 抽检官方锚模型验证公式 → 通过则纳入 crawler 抓取清单
3. 框架指纹库（OFFICIAL 端点路径）持续积累：发现新端点路径/新框架就追加到 ENDPOINTS
4. 探测器可定期对全 seed 跑一遍，捕捉中转站从"登录墙"变为"开放端点"的变化（中转站常改配置）
