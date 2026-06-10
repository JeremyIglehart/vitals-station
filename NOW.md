# NOW — Vitals Station Live Edge

Last updated: 2026-06-10T15:21:19-06:00
Session: vitals-station bootstrap session (June 10 2026) — FULLY CLOSED

> Update this file anytime state changes. Commit immediately.

---

## What's Working

- Server: systemd user service, karma-01.tail3cae5f.ts.net:8080, TLS, Tailscale-only
  Check: `systemctl --user status vitals-station`
  Logs:  `journalctl --user -u vitals-station -n 50`
- Full pipeline: POST → inbox/pending → converter → inbox/processed + events + projections
- GitHub: PUBLIC — https://github.com/JeremyIglehart/vitals-station
- Directory scaffold: inbox/pending/, inbox/processed/, health-data/events/ all present
  (committed via .keep files — fresh clone is immediately ready)
- examples/ shows full pipeline with fictional data
- docs/ has session paper: "Building Something That Knows How It Became Itself"
- Bootstrap genome: https://github.com/JeremyIglehart/stratigraph
- Git: 27 commits, clean history, all pushed

## Data State

Health data directories exist on disk but are empty — filter-repo
checkout deleted them during the privacy cleanup pass.

ACTION NEEDED: Re-send 10 days of exports from iPhone to restore the
data layer. Health Auto Export → any date range → POST to ingest endpoint.
Pipeline handles overlap/dedup automatically — order doesn't matter.

## How to Use in an Atmos Session

Load current vitals (after re-uploading data):
  read_file /home/jeremy/projects/stratigraph/vitals-station/health-data/projection-micro.md
  read_file /home/jeremy/projects/stratigraph/vitals-station/health-data/projection-meso.md
  read_file /home/jeremy/projects/stratigraph/vitals-station/health-data/projection-macro.md

## Daily Automation (to configure on iPhone)

  URL:    https://karma-01.tail3cae5f.ts.net:8080/ingest
  Method: POST
  Format: JSON
  Schedule: daily, "since last sync"
  iPhone must be on Tailscale when it fires.
  B-Side gets a Telegram ping when processing completes.

## Next Move

Re-send health data from iPhone. Then set up daily automation.
Then bring projection-micro.md into an Atmos weather report session.
