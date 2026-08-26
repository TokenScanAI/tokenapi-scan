# Independence & conflict-of-interest policy

> Why anyone should trust a detection result published by TokenAPI Scan.

---

## What we are

TokenAPI Scan is an **independent third-party detector** for AI API relay
services. We measure observable protocol behavior. We publish the evidence.
We do not get paid by any party we measure.

## What we are not

- **We do not operate an AI API relay.** We do not resell access to OpenAI,
  Anthropic, Google, or any other upstream provider.
- **We do not accept provider sponsorship.** No relay, model vendor, or
  aggregator pays us to be listed, ranked, or de-ranked.
- **We do not run paid placement.** The leaderboard order is computed by a
  Bayesian-weighted score from public detection results; no provider can buy
  a higher rank.
- **We do not have a "preferred partner" tier.** Every provider in our
  catalog is reachable by the same probes and evaluated by the same checks.

## Funding & affiliations

The hosted service is operated and funded by the maintainers of the
`TokenScanAI` GitHub organization. We do not currently accept commercial
sponsorship. If this changes, we will disclose it here before any sponsored
content appears on the platform.

## Detection result disputes

A provider that disagrees with its score may:

1. Open a public GitHub Discussion or contact us via the live site.
2. Request the evidence bundle for the disputed detection.
3. Either reproduce a passing probe from the same `base_url` (which will be
   recorded and feed the next Bayesian update) or point to a specific check
   whose evidence is flawed.

Evidence is **replayable**. If the probe was wrong, the evidence will show it.
We will correct a flawed check publicly and re-score affected detections.

## Editorial independence

Detection logic decisions — what to check, what to weight, what to disclose
in the methodology doc — are made by the maintainers based on protocol
specifications and observable cryptographic facts, not on commercial
relationships with anyone.

## Reporter & user protection

- API keys submitted to the live detector are used in-memory and destroyed at
  the end of the probe run.
- Detection reports are tied to a probe ID, not to an account or IP.
- Vulnerability reporters acting in good faith under our
  [security policy](../SECURITY.md) will not be threatened with legal action.

---

If you find evidence that contradicts any statement on this page, please
treat it as a security/integrity issue and report it via
<https://github.com/TokenScanAI/tokenapi-scan/security/advisories/new>.
