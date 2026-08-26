# Detection methodology

> This document describes **what** TokenAPI Scan checks for and the **reasoning** behind each check, at a level suitable for public review and academic citation. Proprietary thresholds, weights, and probe sequences live in the hosted service and are not published here.

---

## 1. Detection goals

For any AI API relay (a third-party endpoint that resells access to an upstream LLM), we answer three questions:

1. **Identity** — does the relay actually serve the model it claims to serve?
2. **Protocol fidelity** — does the response match the upstream protocol field-by-field?
3. **Honest billing** — does `usage` accurately reflect the work performed?

Each question reduces to **observable, replayable evidence**. We never trust self-reported claims (model name in `model` field, fabricated `system_fingerprint`, etc.) without independent corroboration.

---

## 2. Protocol-specific checks

### 2.1 Claude (Anthropic)

11 checks. The strongest single signal is the **`thinking` signature**:

- Anthropic's extended-thinking endpoints return a cryptographic signature embedded in the response.
- The signature can only be produced with Anthropic's signing key.
- A relay that proxies to a non-Claude back-end (Kiro, Amazon Q Developer, Bedrock-without-Claude, or an open-source model wearing a Claude wrapper) **cannot reproduce a valid signature** — the math doesn't work out.
- Weight: **25%** of the Claude score. This single check is binary, not statistical: a valid signature exists or it doesn't.

Additional Claude checks include:
- Tool-use response schema conformance.
- `usage.cache_creation_input_tokens` / `cache_read_input_tokens` plausibility.
- Streaming SSE event sequence (`message_start` → `content_block_start` → … → `message_stop`).
- Stop-reason vocabulary (`end_turn` / `max_tokens` / `tool_use` / `stop_sequence`).

### 2.2 OpenAI

7 checks. Core technique: **back-end fingerprinting via `usage` and `system_fingerprint`**.

- Genuine OpenAI responses include a `system_fingerprint` whose value rotates across infrastructure roll-outs in a way that is **observable but not forgeable** by a downstream relay.
- The `usage.prompt_tokens` / `completion_tokens` values follow the official tokenizer (`cl100k_base` / `o200k_base`) exactly. Relays that bill by a different tokenizer or that inflate counts deviate detectably.
- A relay that quietly substitutes Claude or Gemini for GPT-4 produces:
  - Wrong tokenizer behavior on edge-case inputs (multi-byte characters, BPE merges).
  - Missing or fabricated `system_fingerprint`.
  - Subtly different stop-reason enum values.

### 2.3 Gemini

7 checks via Google's OpenAI-compatible endpoint. Adaptations:

- Gemini 3 returns `thinking` content by default and requires special handling to distinguish "thinking" tokens from "answer" tokens.
- Safety-rating fields (`safetyRatings`) follow a Google-specific schema; relays that proxy non-Gemini back-ends omit this field or fake it incorrectly.
- OpenAI-compat shape conformance (Gemini deviates in `tool_calls` formatting).

---

## 3. Aggregation: Bayesian leaderboard

Per-detection scores feed a public red/black leaderboard:

- **Bayesian smoothing** with a global prior: a single bad sample cannot sink a provider with otherwise consistent good samples, and a single lucky sample cannot mask a provider with consistent bad samples.
- **Confidence labels** (high / medium / low) derive from sample size, not from score itself. A provider with 3 detections is labeled "low confidence" even if all 3 scored 100/100.
- **Minimum 3 detections** required for inclusion in the main leaderboard. Below that, providers appear only on the long-tail / candidate list.

---

## 4. Evidence handling

Every detection produces an **evidence bundle**:

- Request headers + body (with API keys redacted before storage).
- Raw response headers + body.
- Computed signature / hash values used for the check.
- The exact probe seed and timestamp.

Evidence is retained for at least 90 days. Detection reports include a stable URL that lets any third party reproduce the check from the recorded probe.

---

## 5. What we do NOT do

- **We do not store API keys.** Keys are used in-memory during the probe run and destroyed at the end of the request.
- **We do not crawl private endpoints.** Only public-facing `base_url`s reachable from the open internet are tested.
- **We do not run undisclosed probes.** Every check has a public documentation entry; we do not run fuzzing or load-testing under the guise of detection.
- **We do not de-anonymize users.** Detection reports are tied to a probe ID, not to an account or IP.

---

## 6. Limitations

- **Tokenizer drift**: OpenAI and others occasionally adjust tokenizers without versioning. We re-baseline against the official endpoint when this happens.
- **Region-specific routing**: a relay that routes Asia traffic to one back-end and US traffic to another may score differently from different probe locations. We disclose probe origin on each report.
- **A/B-tested model variants**: upstream providers ship A/B variants that look like different models. Bayesian smoothing absorbs this noise.

---

## 7. Reproducibility

The high-level checks above are sufficient for independent researchers to build their own probes and reproduce our category-level conclusions. We do not publish proprietary weights or the exact decision boundaries used in scoring; we do publish enough that **a determined third party can reproduce the qualitative finding** (e.g., "this relay is not real Claude") from the same response stream.
