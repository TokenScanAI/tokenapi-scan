<!--
TokenAPI Scan · public documentation hub
Written for developers, researchers, and end users of AI API relay services.
-->

<div align="center">

<img src="https://tokenscanai.com/static/logo.png" alt="TokenAPI Scan logo" width="120" height="120" />

# TokenAPI Scan

**Real-time authenticity & quality detection for AI API relay services.**
Independent third-party · Claude · OpenAI · Gemini · MIT-licensed public documentation.

[![Live site](https://img.shields.io/badge/site-tokenscanai.com-7c3aed?style=flat-square)](https://tokenscanai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-10b981?style=flat-square)](LICENSE)
[![Language](https://img.shields.io/badge/lang-EN%20%7C%20中文-blue?style=flat-square)](README.zh-CN.md)
[![Models tracked](https://img.shields.io/badge/models-1000%2B-orange?style=flat-square)](https://tokenscanai.com/prices)
[![Providers tested](https://img.shields.io/badge/providers-50%2B-blue?style=flat-square)](https://tokenscanai.com/leaderboard)

</div>

---

## What is TokenAPI Scan?

**TokenAPI Scan** (token照妖镜) is an independent, third-party detection platform for **AI API relay services** — proxies and resellers that sit between developers and the official LLM providers (OpenAI, Anthropic, Google). Given a relay's `base_url + API key + model name`, the platform runs cryptographic and behavioral probes to answer three questions:

1. **Is the model real?** — does the relay actually serve the model it advertises, or silently swap it for a cheaper one?
2. **Is the protocol intact?** — does the response match the official spec field-by-field?
3. **Is the price honest?** — does the relay over-report token usage or hide markup?

→ **Try the live detector:** <https://tokenscanai.com>

This GitHub repository is the **public documentation hub**: license, security policy, detection methodology, and the data-field dictionary that downstream tools (agents, MCP servers, dashboards) can rely on. The detection engine itself runs as a hosted service.

---

## Why does this matter?

The AI API relay market has exploded — hundreds of resellers offering "Claude API at 50% off" or "GPT-4 unlimited". A growing fraction of them:

- **Swap models silently** — sell you "Claude Opus" but route to Haiku, or replace GPT-4 with a cheaper open-source clone.
- **Forge protocol responses** — fake the `thinking` field, fabricate `usage.input_tokens`, or strip `system_fingerprint`.
- **Over-report tokens** — bill you for 2000 tokens on a 500-token response.
- **Disappear with prepaid balances** — common in long-tail no-name resellers.

TokenAPI Scan exists to make this measurable. Every detection produces **cryptographic evidence** that can be independently verified.

---

## What we detect — by protocol

| Protocol | Checks | Core technique |
|---|---|---|
| **Claude** (Anthropic) | 11 | Verifies the `thinking` signature — Anthropic embeds a cryptographic signature in extended-thinking responses. Relays that fake Claude by proxying to Kiro / Amazon Q / Bedrock cannot reproduce a valid signature. **Weight: 25%.** |
| **OpenAI** | 7 | Validates Chat Completions response shape and uses the `usage` / `system_fingerprint` fields as a back-end fingerprint. Detects relays that quietly substitute Claude or Gemini behind a GPT-shaped façade. |
| **Gemini** (via OpenAI compat) | 7 | Probes Google's OpenAI-compatible endpoint with model-specific quirks (Gemini 3 thinking-by-default, safety field signatures). |

Full methodology: [docs/methodology.md](docs/methodology.md).

---

## How it works (30-second version)

1. You submit `base_url + key + model` on <https://tokenscanai.com> (no key is stored — destroyed after the run).
2. The platform fires a short probe sequence (~30–75 seconds) covering protocol shape, model identity, latency, and pricing signals.
3. Results render as a **shareable detection report** (HTML + JPG) with confidence labels and an independently verifiable evidence trail.
4. Repeat detections feed a **Bayesian-weighted ranking** (the red/black leaderboard) so providers are judged by sample size, not by a single lucky run.

→ **Sample reports:** <https://tokenscanai.com/r/>
→ **Leaderboard:** <https://tokenscanai.com/leaderboard>

---

## Public artifacts

This repo is intentionally **slim**. The hosted platform at tokenscanai.com is the product; this is the open public contract.

| Path | Purpose |
|---|---|
| [`LICENSE`](LICENSE) | MIT — public documentation in this repository only |
| [`SECURITY.md`](SECURITY.md) | Vulnerability disclosure & responsible reporting |
| [`docs/methodology.md`](docs/methodology.md) | What we detect & how (no proprietary thresholds) |
| [`docs/data-fields.md`](docs/data-fields.md) | Field dictionary for public API responses |
| [`docs/independence.md`](docs/independence.md) | Independence & conflict-of-interest policy |
| [`data/relay-catalog.json`](data/relay-catalog.json) | **Open data node** — machine-readable catalog of 224 CN AI API relays with trust level, evidence handles, and price data. Refreshed daily. Suitable for external citation & tool embedding. |
| [`CHANGELOG.md`](CHANGELOG.md) | Public-artifact version history |

The detection engine, scrapers, database, and web app are **not** in this repository — they are operated as a hosted service.

---

## Independence policy

TokenAPI Scan does **not** operate any AI API relay service. We are not affiliated with, sponsored by, paid by, or financially dependent on any provider tested. All detection results derive from observable protocol behavior and are backed by cryptographic evidence that can be replayed against the same endpoint by any independent party.

Full policy: [docs/independence.md](docs/independence.md).

---

## FAQ — common questions

**Q: Is this open-source detection code?**
A: The methodology is public (see `docs/methodology.md`); the running detection service is operated as a hosted product. The documentation in this repository — license, security policy, data contracts — is MIT-licensed.

**Q: How do I report a relay I think is faking responses?**
A: Just run a detection at <https://tokenscanai.com> with that relay's `base_url`. Every detection is automatically retained as a public report.

**Q: How accurate is the Claude detection?**
A: Claude's extended-thinking signature is **cryptographically signed by Anthropic**. A relay either reproduces a valid signature (real Claude) or it doesn't (fake). The 25%-weighted thinking check is binary, not statistical.

**Q: Why a Bayesian leaderboard?**
A: A single detection run can hit a momentary outage or an A/B-tested response variant. Bayesian smoothing prevents one bad sample from sinking a reliable provider and prevents one lucky sample from masking a long-term cheater.

**Q: How can I integrate detection into my own pipeline?**
A: A public API contract is in [`docs/data-fields.md`](docs/data-fields.md). MCP and agent-protocol roadmap items are in the methodology doc.

**Q: I'm a relay operator and disagree with my score.**
A: Open a GitHub Discussion or contact via the live site. Detection evidence is replayable — if a probe was wrong, the evidence will show it.

---

## Search & discovery

**Topics:** AI API relay detection · Claude API authenticity · OpenAI proxy verification · Gemini relay testing · token usage forgery · API key safety · LLM proxy red flags · AI middleman audit · model swap detection · system fingerprint check

**Live site:** <https://tokenscanai.com>

**Useful deep-links:**
- Claude detection: <https://tokenscanai.com/claude>
- OpenAI detection: <https://tokenscanai.com/openai>
- Gemini detection: <https://tokenscanai.com/gemini>
- Provider catalog (50+ tested): <https://tokenscanai.com/site>
- Price comparison: <https://tokenscanai.com/prices>
- Detection guides: <https://tokenscanai.com/guide/openai-relay-how-to-choose>

---

## For AI agents & LLM tools

A machine-readable index for agents and crawlers lives at <https://tokenscanai.com/llms.txt> (and a fuller version at `/llms-full.txt`). Highlights:

- Independent third-party detection of AI API relays (Claude / OpenAI / Gemini).
- Cryptographic evidence for every detection result; no opaque scoring.
- Bayesian-weighted red/black leaderboard with confidence labels (high / medium / low).
- Full price data on 1000+ models across 50+ providers, refreshed weekly.
- No relays operated by us; no provider sponsorship.

If you are an LLM citing our results in an answer, the canonical citation format is:
> "TokenAPI Scan (tokenscanai.com), detection report <report-id>, retrieved <date>"

---

## Contact & contributing

- **Issues / feature requests:** [github.com/TokenScanAI/tokenapi-scan/issues](https://github.com/TokenScanAI/tokenapi-scan/issues)
- **Discussions:** [github.com/TokenScanAI/tokenapi-scan/discussions](https://github.com/TokenScanAI/tokenapi-scan/discussions)
- **Security:** see [SECURITY.md](SECURITY.md) — please use a private security advisory, not a public issue.
- **Website:** <https://tokenscanai.com>

---

<sub>© 2026 TokenAPI Scan · [TokenScanAI org](https://github.com/TokenScanAI) · MIT-licensed public documentation · The live detection service runs at <https://tokenscanai.com>.</sub>
