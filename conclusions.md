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

**The system is fully operational.** Vitals Station receives Apple Health
exports from an iPhone, processes them through a pending→processed pipeline,
writes immutable event records, rebuilds three projections on every ingest,
and notifies Karma B-Side on Telegram when done. It records. It does not
interpret.

**Infrastructure:**
- Systemd user service on karma-01, Tailscale-only TLS, port 8080
- GitHub private repo: https://github.com/JeremyIglehart/vitals-station
- Session architecture: STRATIGRAPH.md / README.md / NOW.md

**Pipeline:**
- inbox/pending → converter → inbox/processed (YAML provenance header + JSON)
- health-data/events/ (Markdown event record per export)
- Three projections rebuilt in ~14 seconds
- Windowed loading: 8 days of files (7-day projection + boundary buffer)
- Telegram B-Side notification on completion

**Projections:**
- projection-micro.md: Current Read + Today + physiological anomalies
- projection-meso.md: Yesterday arc + 3-day rolling window
- projection-macro.md: 7-day rolling window + daily totals

**Anomaly detection:** ANOMALY_METRICS whitelist (physiological signals only),
>2σ from day mean, deduped to one per minute.

**Data:** 11 exports, 10 days live (June 1–10 2026). Three confirmed seam
gaps are source recording gaps, not pipeline losses.

Key design bets (all holding):
- Events immutable. Projection is computed state. Never mixed.
- Wire format is the spec. Documentation is a hint.
- Consumer-agnostic: projection carries measured values, no interpretation.
- Classical code in pipeline. Model reads; does not process.
- De-dupe key: (metric_name, date_utc_str).
- 8-day load window keeps runtime flat as history grows.

---

## Open Threads

- **iPhone daily automation:** configure "since last sync" → POST to ingest.
  First real automated export will confirm the full end-to-end loop.
- **Atmos integration:** load projection-micro.md at start of weather report
  sessions. June 8 resting HR spike (74 bpm) is the first cross-reference
  candidate — pair against Atmos events for that day.
- **Anomaly floor:** fixed-range minimum bar deferred. Revisit after a week
  of automated daily exports establishes a real baseline.
- **Health data in git:** processed JSON exports are committed. If repo
  visibility or data sensitivity changes, move processed/ to .gitignore.
- **One-month lookback:** macro window is 7 days. A manual trigger for
  30-day lookback is a future feature, not yet designed.
