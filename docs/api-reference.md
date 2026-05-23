# TokenAPI Scan — Public API Reference

> Live endpoints at **<https://tokenscanai.com/api>**.

This document describes the public read-only REST API exposed by
[tokenscanai.com](https://tokenscanai.com). All endpoints are versioned
under `/api/v1/` and return JSON.

The official Python SDK lives at
[`tokenscanai-cli`](https://github.com/haruki3rd/tokenscanai-cli).

---

## Conventions

- **Base URL**: `https://tokenscanai.com`
- **Auth**: Public endpoints require no authentication. Rate-limited per IP.
- **Format**: All responses are `application/json; charset=utf-8`
- **Errors**: Non-2xx responses include `{"error": "<message>", "code": "<symbol>"}`
- **Versioning**: Breaking changes ship as `/api/v2/...`. v1 is supported for
  at least 12 months after a successor ships.

---

## Endpoints

### `GET /api/v1/sites`

List all monitored relay sites.

**Query parameters**

| Name | Type | Description |
|------|------|-------------|
| `tier` | string | Filter by tier: `S`, `A`, `B`, `C`, `D` |
| `region` | string | `cn`, `overseas`, `both` |
| `limit` | int | Page size, default 50, max 200 |
| `offset` | int | Pagination offset |

**Example**

```bash
curl https://tokenscanai.com/api/v1/sites?tier=S&limit=10
```

**Response (abridged)**

```json
{
  "total": 34,
  "sites": [
    {
      "slug": "example-relay",
      "name": "Example Relay",
      "tier": "S",
      "url": "https://example.com",
      "first_seen": "2024-08-12",
      "last_probed": "2026-05-23T03:14:00Z",
      "reachable_cn": true,
      "reachable_overseas": true
    }
  ]
}
```

---

### `GET /api/v1/sites/{slug}`

Full detail for a single site, including probe history.

**Example**

```bash
curl https://tokenscanai.com/api/v1/sites/example-relay
```

Returns the same shape as the list endpoint plus:

- `probe_history` — last 30 days of probe results
- `model_list_claimed` — what the site advertises
- `model_list_verified` — what we confirmed via `/v1/models`
- `network_profile` — CDN, ASN, China-reachability flags
- `screenshot_url` — most recent monthly screenshot

---

### `GET /api/v1/ranking`

The live red/black leaderboard (红黑榜).

**Query parameters**

| Name | Type | Description |
|------|------|-------------|
| `board` | string | `red` (top performers) or `black` (warning list) |
| `limit` | int | Default 10 |

---

### `GET /api/v1/detect`

⚠️ **Status: currently in development.** Public release date TBA.

Submit an arbitrary URL for on-demand detection. The Python SDK exposes this
as `client.detect(url)`.

---

## Rate limits

Requests are rate-limited per IP. Current limits are returned in response headers:

```
X-RateLimit-Limit: <max requests in window>
X-RateLimit-Remaining: <requests left>
X-RateLimit-Reset: <unix timestamp when window resets>
```

For higher quota, contact <help@tokenscanai.com>.

---

## Stability

These endpoints back the public site itself; they are operationally critical
and changes are announced in [changelog.md](changelog.md) at least 2 weeks
before deployment.

---

<sub>Service status · <https://tokenscanai.com> · Issues · <https://github.com/haruki3rd/tokenscanai/issues></sub>
