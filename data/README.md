# Open Data Node — relay-catalog.json

`relay-catalog.json` is a machine-readable, MIT-licensed snapshot of **CN AI API relay (中转站) trust & price data**, published so external tools, agents, and researchers can pull and cite it without signing up or using a key.

## Schema (v1.1)

| Field | Meaning |
|---|---|
| `provider_id` / `name` | Relay identity |
| `endpoint` / `homepage` | API endpoint & site |
| `active` | `service_status` is active |
| `trust.verified` | `high` / `medium` / `low` (from detection success rate ≥0.9 / ≥0.7 / else) |
| `trust.effective_verified` | `unavailable` when the relay is dead/discontinued (avoids "high trust but dead" contradiction) |
| `trust.success_rate` / `detection_count` | Measured probe success rate & sample size |
| `evidence` | Evidence handle (`evidence://detection/...`) so claims are verifiable, not marketing |
| `prices` | Model count, min input/output price, cheapest input model |

## Freshness

Regenerated **daily at 08:45 (CST)** by the hosted platform, immediately after the price ETL. Check `generated_at` in the file.

## Online equivalent

The same live file is served at:
- `https://tokenscanai.com/data/relay-catalog.json`
- Trust primitive: `https://tokenscanai.com/api/trust/provider/{provider_id}`

## License

MIT — you may freely pull, cite, and build on this data. See repo `LICENSE`.
