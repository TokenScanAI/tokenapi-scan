# TokenAPI Scan

> **Real-time detection and ranking for AI API relay services.**

🌐 [tokenscanai.com](https://tokenscanai.com) · 📖 [中文 README](README.zh-CN.md)

[![Website](https://img.shields.io/badge/website-tokenscanai.com-7b3ff2)](https://tokenscanai.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Monitored Sites](https://img.shields.io/badge/monitored-34%2B%20sites-success)](https://tokenscanai.com/sites)
[![Last Updated](https://img.shields.io/badge/updated-monthly-orange)](docs/changelog.md)

---

**TokenAPI Scan** is an independent monitoring service that continuously tests
**AI API relay providers** — third-party services that proxy OpenAI, Anthropic,
Google, and other major LLM APIs.

We answer the questions developers and procurement teams actually care about:

- Is this relay **really online** today, from both China and overseas networks?
- Does it actually serve the **models it claims** to (GPT-4o, Claude 3.5, etc.)?
- What is its **tier** (S / A / B / C / D) based on stability, transparency, and pricing?
- Is it likely to **disappear next week** like the dozen others before it?

## Why this exists

The AI API relay market is full of opaque providers, fake model lists, and sites
that vanish overnight with prepaid balances. Every assessment on
[tokenscanai.com](https://tokenscanai.com) is generated from **automated probes,
not paid reviews** — see [detection methods](docs/detection-methods.md).

## Quick links

- 🔍 **Browse all monitored sites** → <https://tokenscanai.com/sites>
- 📊 **Live ranking leaderboard** → <https://tokenscanai.com/ranking>
- 📡 **API reference** → [docs/api-reference.md](docs/api-reference.md) · <https://tokenscanai.com/api>
- 🧪 **Detection methodology** → [docs/detection-methods.md](docs/detection-methods.md)
- 📦 **Python SDK** → [`tokenscanai-cli`](https://github.com/haruki3rd/tokenscanai-cli)
- 📰 **Monthly changelog** → [docs/changelog.md](docs/changelog.md)

## What's in this repo

This repository is the **public documentation hub** for the TokenAPI Scan service.
The detection engine, scoring algorithms, and site database are operated as a
hosted service at [tokenscanai.com](https://tokenscanai.com) and are **not**
open-sourced here.

```
.
├── README.md                  # This file (English)
├── README.zh-CN.md            # 中文版
├── LICENSE                    # MIT
├── docs/
│   ├── api-reference.md       # Public REST API documentation
│   ├── detection-methods.md   # What we test and how we score
│   └── changelog.md           # Monthly service updates
└── data/
    └── README.md              # Public dataset release notes
```

## Contributing

We welcome:

- **Bug reports** about the public API or detection accuracy → [open an issue](https://github.com/haruki3rd/tokenscanai/issues/new/choose)
- **New relay submissions** for monitoring → open a "New site" issue
- **Documentation fixes** → pull requests welcome on `docs/`
- **Other inquiries** → email <help@tokenscanai.com>

We do not accept code contributions to the detection engine itself, as it is
maintained as a closed-source service.

## License

Documentation in this repository is licensed under the [MIT License](LICENSE).

The hosted service at [tokenscanai.com](https://tokenscanai.com), its data, and
detection algorithms are proprietary and **not** covered by this license.

---

<sub>Maintained by the TokenAPI Scan team · <https://tokenscanai.com></sub>
