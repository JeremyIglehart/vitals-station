---
archived: 2026-06-10
challenged_by: 6576270 — security: test-exports purged from history, repo recreated
superseded_by: conclusions.md
slug_story: repo-recreated-security-fix-complete
reconstruction_fidelity: live
---

# Conclusions — Vitals Station

> The living synthesized read. Design decisions and why. Health data state
> lives in health-data/ and uses a projection model, not this layer.

---

## The Question

What is the right architecture for receiving Apple Health telemetry from an
iPhone, storing it immutably, and serving it as a clean read model to any
consumer — starting with Atmos, but agnostic to future applications?

---

## Current Read

**The system is fully operational, public, and integrated.**

Vitals Station receives Apple Health exports from an iPhone, processes them
through a pending→processed pipeline, writes immutable event records, rebuilds
three projections on every ingest, and notifies Karma B-Side on Telegram.
It records. It does not interpret.

**Infrastructure:** Systemd user service, karma-01, TLS via Tailscale
Let's Encrypt, port 8080. Survives reboots independently. Directory scaffold
committed. GitHub public: https://github.com/JeremyIglehart/vitals-station

**Pipeline:** inbox/pending → converter → inbox/processed (YAML provenance
header) + health-data/events/ + three projections rebuilt in ~14 seconds
(8-day windowed load). Telegram B-Side notification on every ingest.

**Projections:**
- projection-micro.md: Current Read + Today + physiological anomalies
- projection-meso.md: Yesterday arc + 3-day rolling window
- projection-macro.md: 7-day rolling window + daily totals

**Atmos integration:** karma-atmos skill step 4 now loads projection-micro.md
automatically at every Atmos session start. First real weather cross-reference
completed June 10 2026 — instrument data contributed to a filed Atmos event.

**Session paper:** docs/vitals-station-stratigraph-session.md
"Building Something That Knows How It Became Itself" — June 10 2026.

Key design bets (all holding):
- Events immutable. Projection is computed state. Never mixed.
- Wire format drives schema. Documentation is a hint.
- Consumer-agnostic. The Station records; consumers interpret.
- Classical code in pipeline. Model reads; does not process.
- De-dupe key: (metric_name, date_utc_str).
- 8-day load window keeps runtime flat as history grows.

---

## Open Threads

- **iPhone daily automation:** configure "since last sync" trigger.
- **Telegram improvements:** date range in notification, today vitals summary.
- **30-day lookback projection:** manual trigger, deferred until 60+ days on file.
- **Anomaly floor:** fixed-range minimum bar deferred.

## Known Pitfalls

- **git filter-repo deletes gitignored directories** from working dir after
  rewrite. Always commit .keep files first. See event:
  20260610_212119_filter-repo-directory-loss-pitfall.md
