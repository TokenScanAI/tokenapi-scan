#!/usr/bin/env python3
"""tokenscan — CLI client for the TokenAPI Scan (tokenscanai.com) public API.

Zero dependencies (Python 3.8+ stdlib only). Designed for AI agents and
humans to verify relay-provider trust, get routing candidates, and pull
verifiable evidence.

Discovery order (agents should try in this order):
  1. https://tokenscanai.com/.well-known/agent.json   (A2A AgentCard)
  2. https://tokenscanai.com/docs/for-agents          (human/agent quickstart)
  3. https://tokenscanai.com/openapi.json              (full schema)

Usage:
  tokenscan verify <provider_id_or_domain>   Trust level + success rate + evidence ref
  tokenscan route <model>                    Routing candidates (primary/backup roles)
  tokenscan price <model>                    Price across providers
  tokenscan evidence <provider_id_or_domain> Full L1 probe evidence (sha256 content-addressed)
  tokenscan meta                             Service metadata

Environment:
  TOKENSCAN_BASE   Base URL (default: https://tokenscanai.com)

Exit codes: 0 = ok, 1 = API error / not found, 2 = usage error.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

BASE = os.environ.get("TOKENSCAN_BASE", "https://tokenscanai.com").rstrip("/")
TIMEOUT = 20
PROXY = os.environ.get("TOKENSCAN_PROXY")  # e.g. http://127.0.0.1:7890

_opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": PROXY, "https": PROXY} if PROXY else {}))


def _get(path, attempts=3):
    url = path if path.startswith("http") else BASE + path
    req = urllib.request.Request(url, headers={"User-Agent": "tokenscan-cli/1.0", "Accept": "application/json"})
    last_err = None
    for _ in range(attempts):
        try:
            with _opener.open(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8", "replace")), None
        except urllib.error.HTTPError as e:
            try:
                body = json.loads(e.read().decode("utf-8", "replace"))
            except Exception:
                body = {}
            return body, "HTTP %d" % e.code
        except Exception as e:
            last_err = str(e)
    return {}, last_err


def _fmt_rate(x):
    try:
        return "%.1f%%" % (float(x) * 100)
    except (TypeError, ValueError):
        return "n/a"


def cmd_verify(args):
    if not args:
        print("usage: tokenscan verify <provider_id_or_domain>", file=sys.stderr)
        return 2
    pid = args[0]
    d, err = _get("/api/trust/provider/" + pid)
    if err or d.get("status") != "ok":
        print("error: %s (%s)" % (d.get("code", err), d.get("hint", "")))
        return 1
    p, t = d.get("provider", {}), d.get("trust", {})
    if not p.get("name") and not t.get("verified"):
        print("not found: no trust data for %r" % pid)
        return 1
    print("provider:   %s (%s)" % (p.get("name"), pid))
    print("endpoint:   %s" % p.get("endpoint"))
    print("category:   %s / region=%s / status=%s" % (p.get("category"), p.get("region"), p.get("service_status")))
    print("trust:      %s (success %s, %s/%s detections, latest %s)" % (
        t.get("verified"), _fmt_rate(t.get("success_rate")),
        t.get("success_count"), t.get("detection_count"), t.get("latest_detected_at")))
    lv = d.get("levels", {})
    if lv:
        print("levels:     " + ", ".join("%s=%s" % kv for kv in sorted(lv.items())))
    if d.get("evidence"):
        print("evidence:   %s" % d["evidence"])
    return 0


def cmd_route(args):
    if not args:
        print("usage: tokenscan route <model>", file=sys.stderr)
        return 2
    model = args[0]
    d, err = _get("/api/router/candidates?model=" + urllib.parse.quote(model))
    if err or d.get("status") != "ok":
        print("error: %s" % (d.get("detail") or err))
        return 1
    print("model: %s | providers with price: %s | candidates: %s" % (
        d.get("resolved_model"), d.get("price_provider_count"), d.get("count")))
    print("note: %s" % d.get("disclaimer", ""))
    for c in d.get("candidates", []):
        pr = c.get("price") or {}
        sc = c.get("scores") or {}
        price = ""
        if pr.get("input_usd_per_1m") is not None:
            price = " | $%s in / $%s out per 1M" % (pr.get("input_usd_per_1m"), pr.get("output_usd_per_1m"))
        print("  [%s] %s (score %s)%s" % (c.get("recommended_role"), c.get("provider_id"), sc.get("total"), price))
        if c.get("risk_flags"):
            print("        risk: %s" % ", ".join(c["risk_flags"]))
    return 0


def cmd_price(args):
    if not args:
        print("usage: tokenscan price <model>", file=sys.stderr)
        return 2
    model = args[0].lower()
    d, err = _get("/api/prices")
    if err:
        print("error: %s" % err)
        return 1
    rows = []
    for sid, p in (d.get("providers") or {}).items():
        for m, info in (p.get("models") or {}).items():
            if m.lower() == model or m.lower().startswith(model + "-"):
                rows.append((sid, m, info))
    if not rows:
        print("no price data for model %r" % model)
        return 1
    print("model %r: %d provider listings" % (model, len(rows)))
    for sid, m, info in sorted(rows, key=lambda r: (r[2].get("input_price") if isinstance(r[2], dict) else 0) or 0)[:50]:
        if isinstance(info, dict):
            print("  %-28s %-45s in=%s out=%s %s (updated %s)" % (
                sid, m, info.get("input_price"), info.get("output_price"),
                info.get("currency", ""), info.get("updated_at", "")))
        else:
            print("  %-28s %-45s %s" % (sid, m, info))
    if len(rows) > 50:
        print("  ... and %d more" % (len(rows) - 50))
    return 0


def cmd_evidence(args):
    if not args:
        print("usage: tokenscan evidence <provider_id_or_domain>", file=sys.stderr)
        return 2
    pid = args[0]
    d, err = _get("/api/evidence/" + pid)
    if err or d.get("status") != "ok":
        print("error: %s (%s)" % (d.get("code", err), d.get("hint", "")))
        return 1
    print("provider:   %s" % d.get("provider_id"))
    print("evidence:   %s" % d.get("evidence_ref"))
    print("sha256:     %s" % d.get("sha256"))
    print("checked_at: %s" % d.get("checked_at"))
    ev = d.get("evidence", {})
    print("homepage_ok: %s | models_endpoint_ok: %s | strategy: %s" % (
        ev.get("homepage_ok"), ev.get("models_endpoint_ok"), ev.get("winning_strategy")))
    print("verifiable: %s (content-addressed; re-hash the evidence object to independently verify)" % d.get("verifiable"))
    return 0


def cmd_meta(_args):
    d, err = _get("/api/_meta")
    if err:
        print("error: %s" % err)
        return 1
    print(json.dumps(d, ensure_ascii=False, indent=2))
    return 0


COMMANDS = {
    "verify": cmd_verify,
    "route": cmd_route,
    "price": cmd_price,
    "evidence": cmd_evidence,
    "meta": cmd_meta,
}


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0 if argv else 2
    fn = COMMANDS.get(argv[0])
    if not fn:
        print("unknown command: %s\ncommands: %s" % (argv[0], ", ".join(sorted(COMMANDS))), file=sys.stderr)
        return 2
    return fn(argv[1:])


if __name__ == "__main__":
    sys.exit(main())
