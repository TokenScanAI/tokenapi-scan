# Token 照妖镜（TokenAPI Scan）

> **AI API 中转站实时检测与可靠性排行。**

🌐 [tokenscanai.com](https://tokenscanai.com) · 📖 [English README](README.md)

[![网站](https://img.shields.io/badge/website-tokenscanai.com-7b3ff2)](https://tokenscanai.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![监测站点](https://img.shields.io/badge/monitored-34%2B%20sites-success)](https://tokenscanai.com/sites)
[![更新频率](https://img.shields.io/badge/updated-monthly-orange)](docs/changelog.md)

---

**Token 照妖镜（TokenAPI Scan）** 是独立运营的 **AI API 中转站监测服务**，
对市面上代理 OpenAI / Anthropic / Google 等主流大模型 API 的第三方中转站
做持续探测与可靠性评分。

我们回答开发者和采购真正关心的问题：

- 这家中转站**今天还在不在**？国内外网络都能访问吗？
- 它**真的提供它声称的模型**吗？（GPT-4o、Claude 3.5、Gemini 等）
- 综合稳定性、透明度、价格，它属于哪个 **tier**（S / A / B / C / D）？
- 它会不会**下周就跑路**，像前面那十几家一样？

## 为什么需要照妖镜

AI API 中转市场充斥着不透明的服务方、虚假的模型列表，以及一夜消失卷走预付款的站点。
[tokenscanai.com](https://tokenscanai.com) 上的每一项判定都来自
**自动化探测，而非付费评测** — 见 [检测方法](docs/detection-methods.md)（英文）。

## 快速入口

- 🔍 **浏览全部监测站点** → <https://tokenscanai.com/sites>
- 📊 **实时红黑榜** → <https://tokenscanai.com/ranking>
- 📡 **API 文档** → [docs/api-reference.md](docs/api-reference.md) · <https://tokenscanai.com/api>
- 🧪 **检测方法论** → [docs/detection-methods.md](docs/detection-methods.md)
- 📦 **Python SDK** → [`tokenscanai-cli`](https://github.com/haruki3rd/tokenscanai-cli)
- 📰 **月度更新日志** → [docs/changelog.md](docs/changelog.md)

## 这个仓库包含什么

这是 TokenAPI Scan 服务的**公开文档中心**。检测引擎、评分算法、站点数据库
都作为托管服务运行在 [tokenscanai.com](https://tokenscanai.com)，**不在此处开源**。

> 注：`docs/` 内的详细技术文档仅有英文版。中文用户的完整产品体验请直接访问
> [tokenscanai.com](https://tokenscanai.com)。

## 贡献

欢迎以下贡献：

- **报告 Bug**（公开 API 或检测准确性问题）→ [提 issue](https://github.com/haruki3rd/tokenscanai/issues/new/choose)
- **推荐新站点**纳入监测 → 用 "New site" issue 模板
- **修订文档** → 欢迎对 `docs/` 提 pull request
- **其他咨询** → 邮件 <help@tokenscanai.com>

我们不接受对检测引擎的代码贡献，因为它作为闭源服务维护。

## 许可

本仓库的文档采用 [MIT License](LICENSE)。

托管在 [tokenscanai.com](https://tokenscanai.com) 的服务、数据、检测算法
为专有资产，**不**适用此 License。

---

<sub>由 TokenAPI Scan 团队维护 · <https://tokenscanai.com></sub>
