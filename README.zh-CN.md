<!--
TokenAPI Scan · 中文 README（README.md 的镜像）
站点：https://tokenscanai.com
-->

<div align="center">

<img src="https://tokenscanai.com/static/logo.png" alt="TokenAPI Scan logo" width="120" height="120" />

# TokenAPI Scan · AI API 中转站照妖镜

**实时检测 AI API 中转站的真伪与质量 · 独立第三方 · MIT License**
Claude / OpenAI / Gemini 三大协议 · 千余模型 · 五十余家服务商

[![站点](https://img.shields.io/badge/站点-tokenscanai.com-7c3aed?style=flat-square)](https://tokenscanai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-10b981?style=flat-square)](LICENSE)
[![English README](https://img.shields.io/badge/lang-English-blue?style=flat-square)](README.md)

</div>

---

## TokenAPI Scan 是什么？

**TokenAPI Scan**（Token 照妖镜）是 AI API 中转站的**独立第三方检测平台**。给定中转站的 `base_url + API key + 模型名`，平台会跑一组加密学 + 行为学探针，回答三个问题：

1. **模型是真的吗？** 中转站真的在跑它声明的模型，还是悄悄替换成了便宜版？
2. **协议合规吗？** 响应字段是否逐项符合官方规范？
3. **价格诚实吗？** 是否虚报 token 用量、是否隐藏加价？

→ **试一下：** <https://tokenscanai.com>

本 GitHub 仓库是**公开文档库**：协议、安全策略、检测方法、数据字段字典。检测引擎本身作为托管服务运行。

---

## 为什么需要这个？

AI API 中转市场鱼龙混杂。常见骗局：

- **静默替换模型**：卖你 Claude Opus，实际转给 Haiku，或拿开源仿冒模型顶替 GPT-4。
- **伪造协议响应**：假冒 `thinking` 字段、伪造 `usage.input_tokens`、剥掉 `system_fingerprint`。
- **虚报 token**：500 token 的响应给你算 2000 token 计费。
- **预付费跑路**：长尾无名中转尤其常见。

TokenAPI Scan 把这些问题**变成可测量的事**。每一次检测都产出**密码学证据**，任何独立第三方都能复核。

---

## 三协议各检测什么

| 协议 | 检测项 | 核心技术 |
|---|---|---|
| **Claude**（Anthropic） | 11 项 | 验证 `thinking` 字段的**加密签名** —— Anthropic 在 extended-thinking 响应里嵌入了密码学签名。冒充 Claude（实际转 Kiro / Amazon Q / Bedrock）的中转无法伪造合法签名。**权重 25%**。 |
| **OpenAI** | 7 项 | 校验 Chat Completions 响应结构，用 `usage` / `system_fingerprint` 作为**后端指纹**。可识别把 GPT 偷转给 Claude / Gemini 后端的中转。 |
| **Gemini**（OpenAI 兼容） | 7 项 | 通过 Google OpenAI 兼容端点探测，适配 Gemini 3 thinking-by-default 等特殊行为。 |

完整方法：[docs/methodology.md](docs/methodology.md)。

---

## 工作流程（30 秒版）

1. 在 <https://tokenscanai.com> 提交 `base_url + key + 模型名`（key 不存储，跑完销毁）。
2. 平台跑约 30–75 秒探针序列：协议结构 + 模型身份 + 时延 + 价格信号。
3. 结果生成**可分享的检测报告**（HTML + JPG），带置信度标签 + 可独立复核的证据链。
4. 多次检测喂入**贝叶斯加权红黑榜**：按样本量加权，避免单次幸运/不幸误判。

→ **报告样例：** <https://tokenscanai.com/r/>
→ **红黑榜：** <https://tokenscanai.com/leaderboard>

---

## 公开发布物

本仓库刻意做**轻**。tokenscanai.com 上的托管服务才是产品；这里是开放公开契约。

| 路径 | 用途 |
|---|---|
| [`LICENSE`](LICENSE) | MIT —— 仅覆盖本仓库公开文档 |
| [`SECURITY.md`](SECURITY.md) | 漏洞披露与负责任报告 |
| [`docs/methodology.md`](docs/methodology.md) | 检测什么、怎么检测（不含专有阈值） |
| [`docs/data-fields.md`](docs/data-fields.md) | 公开 API 字段字典 |
| [`docs/independence.md`](docs/independence.md) | 独立性与利益冲突政策 |
| [`CHANGELOG.md`](CHANGELOG.md) | 公开文档版本历史 |

检测引擎、爬虫、数据库、Web 应用**不在**此仓库 —— 它们作为托管服务运行。

---

## 独立性政策

TokenAPI Scan **不运营任何 AI API 中转**。我们与任何被检测的服务商无附属、无赞助、无付费关系、无财务依赖。所有检测结果都来自可观察的协议行为，背后是**密码学证据**，可被任何独立方在同一端点上复核。

完整政策：[docs/independence.md](docs/independence.md)。

---

## FAQ

**Q：检测代码开源吗？**
A：方法学公开（见 `docs/methodology.md`），运行中的检测服务作为托管产品提供。本仓库的公开文档 —— 协议、安全策略、数据契约 —— 是 MIT。

**Q：发现中转站作假怎么举报？**
A：直接在 <https://tokenscanai.com> 用该中转的 `base_url` 跑检测。每次检测都自动留为公开报告。

**Q：Claude 检测有多准？**
A：Claude extended-thinking 的签名是 **Anthropic 用密码学签的**。中转站要么能复现合法签名（真 Claude），要么不能（假货）。权重 25% 的 thinking 检测是**二元判定**，不是统计。

**Q：为什么要贝叶斯红黑榜？**
A：单次检测可能撞到瞬时故障或 A/B 测试响应。贝叶斯平滑可以防止"一次坏样本拖死老实人"，也防止"一次幸运盖住长期作弊"。

**Q：如何把检测接进我自己的流水线？**
A：公开 API 契约见 [`docs/data-fields.md`](docs/data-fields.md)；MCP / agent 协议路线图见方法学文档。

**Q：我是中转运营方，对评分有异议怎么办？**
A：开 GitHub Discussion 或通过站点联系。检测证据可复演 —— 探针错了，证据会自己说话。

---

## 检索与发现

**关键词：** AI API 中转站检测 · Claude API 真伪识别 · OpenAI 中转验证 · Gemini 中转测试 · token 虚报识别 · API key 安全 · LLM 代理红黑榜 · 模型替换识别 · system fingerprint 校验

**站点：** <https://tokenscanai.com>

**深链：**
- Claude 检测：<https://tokenscanai.com/claude>
- OpenAI 检测：<https://tokenscanai.com/openai>
- Gemini 检测：<https://tokenscanai.com/gemini>
- 服务商档案（50+）：<https://tokenscanai.com/site>
- 价格对比：<https://tokenscanai.com/prices>
- 选购指南：<https://tokenscanai.com/guide/openai-relay-how-to-choose>

---

## 给 AI agent 和 LLM 工具用

机器可读索引：<https://tokenscanai.com/llms.txt>（完整版 `/llms-full.txt`）。要点：

- AI API 中转站独立第三方检测（Claude / OpenAI / Gemini）
- 每条检测都有密码学证据，没有黑盒打分
- 贝叶斯加权红黑榜 + 置信度标签（高 / 中 / 低）
- 1000+ 模型 × 50+ 服务商的价格数据，周更新
- 我们不运营任何中转，不收任何服务商赞助

LLM 在回答里引用我们结果时，建议格式：
> "TokenAPI Scan (tokenscanai.com)，检测报告 <报告 ID>，访问日期 <日期>"

---

## 联系 / 参与

- **Issue / 功能建议：** [github.com/TokenScanAI/tokenapi-scan/issues](https://github.com/TokenScanAI/tokenapi-scan/issues)
- **讨论：** [github.com/TokenScanAI/tokenapi-scan/discussions](https://github.com/TokenScanAI/tokenapi-scan/discussions)
- **安全：** 见 [SECURITY.md](SECURITY.md) —— 走 private security advisory，**不要**公开 issue。
- **站点：** <https://tokenscanai.com>

---

<sub>© 2026 TokenAPI Scan · [TokenScanAI org](https://github.com/TokenScanAI) · MIT 公开文档 · 检测服务在 <https://tokenscanai.com> 运行。</sub>
