# NOW — Vitals Station Live Edge

Last updated: 2026-06-10T13:32:00-06:00
Session: vitals-station bootstrap session (June 10 2026)

> Update this file anytime state changes. Commit immediately — do not let
> this file drift from committed state. Even mid-session, commit the update.

---

## What's Working

- Server: running as systemd user service on `karma-01.tail3cae5f.ts.net:8080`
  (TLS, Tailscale-only). Check: `systemctl --user status vitals-station`
- Converter: auto-runs on every POST — rebuilds all three projections immediately
- TLS cert: provisioned June 10 2026, Let's Encrypt via Tailscale
- First test export: received, 9.9MB, 19 metrics, June 9 2026 data
- Three projections: live on disk at health-data/
  - projection-micro.md  — Current Read + Today + today's anomalies
  - projection-meso.md   — Yesterday arc + 3-day rolling
  - projection-macro.md  — 7-day rolling window
- Anomaly detection: physiological signals only (ANOMALY_METRICS whitelist)
  deduped to one per minute, >2σ from day mean
- Git log: 15 commits, clean history from conception

## Current Projection State (June 10 2026)

Sleep last night (June 9): 8h 53m — Deep 0h49m | REM 2h00m | Core 5h53m | Awake 0h12m
Resting HR: 67 bpm | HRV: 43.5ms | Blood O2: 94% | Resp Rate: 18.5/min
Overnight anomalies: SpO2 dip to 91% at 12:40am, resp rate spike 22.5/min at 4:36am

## What's Not Built Yet

- health-data/events/ populated with real ingest events (currently uses raw test exports)
- Ingest event writer (JSON → health-data/events/YYYYMMDD_ingest-NNN.md)
- projection-macro.md has only 2 days of data (more exports needed)

## Open Design Questions

- Fixed-range anomaly floor (deferred until more data in hand)
- Macro rebuild cadence — daily vs. every-ingest (decide when it matters)

## Next Move

Wire up your iPhone automation to send daily exports. After a week of data
lands, review projection quality and tune anomaly thresholds. Then integrate
projection-micro.md as a standard read into Atmos weather reports.

---

## How to Use in an Atmos Session

1. Load this README.md (triggers genome + conclusions + NOW load)
2. Then: `read_file /home/jeremy/projects/stratigraph/vitals-station/health-data/projection-micro.md`
3. Optionally for historical context: projection-meso.md or projection-macro.md
