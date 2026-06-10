# NOW — Vitals Station Live Edge

Last updated: 2026-06-10T15:47:57-06:00
Session: vitals-station bootstrap session (June 10 2026) — COMPLETE

> Update this file anytime state changes. Commit immediately.

---

## What's Working

- Server: systemd user service, karma-01.tail3cae5f.ts.net:8080, TLS, Tailscale-only
  Check: `systemctl --user status vitals-station`
  Logs:  `journalctl --user -u vitals-station -n 50`
- Full pipeline: POST → inbox/pending → converter → inbox/processed + events + projections
- Health data: current — re-uploaded and processed after filter-repo cleanup
- GitHub: PUBLIC — https://github.com/JeremyIglehart/vitals-station
- Atmos integration: LIVE — karma-atmos skill step 4 loads projection-micro.md
  automatically at every Atmos session start
- First real Atmos weather read using instrument data: filed June 10 2026
- Session paper in docs/ and ~/mac-shared/stratigraph-papers/
- Bootstrap genome: https://github.com/JeremyIglehart/stratigraph
- Git: 31 commits (after this one), clean, all pushed

## How to Use in an Atmos Session

The karma-atmos skill now handles this automatically (step 4).
Manual load if needed:
  read_file ~/projects/stratigraph/vitals-station/health-data/projection-micro.md
  read_file ~/projects/stratigraph/vitals-station/health-data/projection-meso.md
  read_file ~/projects/stratigraph/vitals-station/health-data/projection-macro.md

## Daily Automation (to configure on iPhone)

  URL:    https://karma-01.tail3cae5f.ts.net:8080/ingest
  Method: POST
  Format: JSON
  Schedule: daily, "since last sync"
  iPhone must be on Tailscale when it fires.
  B-Side gets a Telegram ping when processing completes.

## Future Work (deferred)

- Telegram: include date range covered + today vitals summary for current-day exports
- 30-day lookback projection (manual trigger — wait for 60+ days of data)
- Anomaly floor: fixed-range minimum bar
