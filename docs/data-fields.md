# Public data-field dictionary

> Stable field names and types for the public-facing endpoints on
> tokenscanai.com. Internal scoring fields and proprietary signals are not
> documented here.

---

## 1. Detection report (`/r/<id>`)

A finalized detection result, addressable by a stable URL.

| Field | Type | Description |
|---|---|---|
| `id` | string | Stable report ID. URL-safe. |
| `created_at` | ISO-8601 string | UTC timestamp of the probe run. |
| `target.base_url` | string | The endpoint that was probed. |
| `target.model` | string | The model name requested. |
| `protocol` | enum | `claude` / `openai` / `gemini`. |
| `score` | integer 0–100 | Aggregate score for this single probe. |
| `confidence` | enum | `high` / `medium` / `low` — derived from probe completeness, not score. |
| `verdict` | enum | `genuine` / `suspect` / `forged` / `inconclusive`. |
| `checks[]` | array | One entry per individual check. |
| `checks[].id` | string | Stable check ID (see `docs/methodology.md`). |
| `checks[].status` | enum | `pass` / `fail` / `skip` / `error`. |
| `checks[].weight` | float 0–1 | Contribution of this check to the score. |
| `evidence_url` | string | Replayable evidence bundle. |
| `share_image_url` | string | Pre-rendered JPG card for the report. |

---

## 2. Provider profile (`/site/<slug>`)

Public profile of an AI API service provider.

| Field | Type | Description |
|---|---|---|
| `slug` | string | URL-safe identifier. |
| `display_name` | string | Display name on the platform. |
| `website` | string | Provider's own marketing site. |
| `api_endpoints[]` | array of strings | `base_url`s tested. |
| `category` | enum | `official` / `relay` / `aggregator` / `inference-platform`. |
| `protocols_supported[]` | array | Subset of `claude` / `openai` / `gemini`. |
| `models_observed[]` | array | Model IDs observed at this provider. |
| `detection_count` | integer | Total detections to date. |
| `bayesian_score` | float 0–100 | Smoothed score; `null` when below sample threshold. |
| `confidence_label` | enum | `high` / `medium` / `low` / `insufficient`. |
| `last_tested_at` | ISO-8601 string | Most recent probe timestamp. |

---

## 3. Leaderboard entry (`/leaderboard`)

| Field | Type | Description |
|---|---|---|
| `rank` | integer | Position in the current view. |
| `provider_slug` | string | Stable slug; link to `/site/<slug>`. |
| `bayesian_score` | float 0–100 | Smoothed score. |
| `confidence_label` | enum | `high` / `medium` / `low`. |
| `sample_size` | integer | Detections used for the score. |
| `trend_7d` | enum | `up` / `down` / `flat` / `new`. |

---

## 4. Price record (`/prices`)

A single pricing observation for a `(provider, model)` pair.

| Field | Type | Description |
|---|---|---|
| `provider_slug` | string | Provider this price applies to. |
| `model_id` | string | Canonical model identifier. |
| `input_price_per_mtok` | float USD | Price per million input tokens. |
| `output_price_per_mtok` | float USD | Price per million output tokens. |
| `currency` | string | Always `USD` in the public feed. |
| `observed_at` | ISO-8601 string | When the price was scraped. |
| `source_url` | string | Page the price was scraped from. |

---

## 5. Versioning

- Field names in this dictionary are **stable** within a major version.
- Additions are non-breaking.
- Removals and type changes bump the major version and are announced in
  [`CHANGELOG.md`](../CHANGELOG.md).
- The current contract version is **v1**.
