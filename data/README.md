# Public dataset releases

This directory hosts **periodic public snapshots** of the TokenAPI Scan
monitoring dataset. Snapshots are released on a curated, delayed basis — they
are **not** a live mirror of the production database.

> Live data is always available via the REST API at
> <https://tokenscanai.com/api> and is the authoritative source. Use snapshots
> for offline analysis, research, or backup reference only.

---

## Release cadence

- **Monthly snapshot**: published on the 1st of each month, covering the
  previous calendar month's monitoring data.
- **Delay**: ~7 days behind the live database (avoids exposing in-flight
  state and gives us a window to correct anomalies).

The first public snapshot release schedule is TBA. Watch
[the main repo](https://github.com/haruki3rd/tokenscanai) for the
announcement.

---

## What snapshots include

- Site directory: slug, display name, tier, first-seen date
- Aggregated probe stats (uptime %, latency p50/p95)
- Network reachability matrix per site
- Tier change history

## What snapshots do not include

- Real-time probe logs (those stay live on the site)
- Raw HTTP captures
- Internal scoring weights
- Anything that would let an operator reverse-engineer the detection logic

---

## License

Snapshots will be released under **CC BY 4.0**. Attribution required:

> Source: TokenAPI Scan (https://tokenscanai.com), monthly dataset YYYY-MM.

---

<sub>Questions? Open an issue or email <help@tokenscanai.com></sub>
