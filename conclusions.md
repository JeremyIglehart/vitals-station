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

**The system is fully operational and public.** Vitals Station is a live
health event log and projection engine at github.com/JeremyIglehart/vitals-station.

**Infrastructure:**
- Systemd user service on karma-01, TLS via Tailscale Let's Encrypt,
  port 8080, Tailscale-only. Survives reboots independently.
- Directory scaffold committed (`.keep` files) — fresh clone is
  immediately ready to receive data.
- GitHub: public repo, health data purged from all history via
  filter-repo. examples/ shows full pipeline with fictional data.

**Pipeline:**
- inbox/pending → converter → inbox/processed (YAML provenance header
  + raw JSON) + health-data/events/ (Markdown event record) + 3
  projections rebuilt in ~14 seconds (8-day windowed load).
- Telegram B-Side notification on every ingest complete.
- Health check: `systemctl --user status vitals-station` and
  `curl https://karma-01.tail3cae5f.ts.net:8080/health`

**Projections:**
- projection-micro.md: Current Read + Today + physiological anomalies
- projection-meso.md: Yesterday arc + 3-day rolling window
- projection-macro.md: 7-day rolling window + daily totals
- Anomaly detection: ANOMALY_METRICS whitelist, >2σ, 1 per minute max.

**Data state:** Directories exist on disk. Health exports need to be
re-sent from iPhone (10 days of data, re-uploadable from Health Auto
Export). Pipeline will process and rebuild projections on first ingest.

**Session paper:** docs/vitals-station-stratigraph-session.md
"Building Something That Knows How It Became Itself" — June 10 2026.
Also at ~/mac-shared/stratigraph-papers/.

Key design bets (all holding):
- Events immutable. Projection is computed state. Never mixed.
- Wire format drives schema. Documentation is a hint.
- Consumer-agnostic: projection carries measured values, no interpretation.
- Classical code in pipeline. Model reads; does not process.
- De-dupe key: (metric_name, date_utc_str).
- 8-day load window keeps runtime flat as history grows.

---

## Open Threads

- **Re-upload health data:** send 10 days of exports from iPhone to
  restart the data layer. Pipeline handles it cleanly.
- **iPhone daily automation:** configure "since last sync" trigger.
- **Atmos integration:** load projection-micro.md at session start.
- **Anomaly floor:** fixed-range minimum bar still deferred.
- **One-month lookback:** manual trigger for 30-day window, not yet built.

## Known Pitfalls

- **git filter-repo deletes gitignored directories** from working dir
  after rewrite. Always commit .keep files before running. Back up
  on-disk-only data. See event: 20260610_212119_filter-repo-directory-
  loss-pitfall.md
