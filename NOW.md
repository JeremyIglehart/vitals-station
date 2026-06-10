# NOW — Vitals Station Live Edge

Last updated: 2026-06-10T14:10:00-06:00
Session: vitals-station bootstrap session (June 10 2026) — COMPLETE

> Update this file anytime state changes. Commit immediately.

---

## What's Working

- Server: systemd user service, karma-01.tail3cae5f.ts.net:8080, TLS, Tailscale-only
  Check: `systemctl --user status vitals-station`
  Logs:  `journalctl --user -u vitals-station -n 50`
- Full pipeline: POST → inbox/pending → converter → inbox/processed + events + projections
- 10 exports processed: June 1–10 2026 (10 days of real data)
- Three live projections in health-data/
- Seam analysis: 3 real gaps in source data (June 4→5, June 7→8, June 9→10)
  These are Watch recording gaps, not pipeline losses.
- Git: 17 commits, clean history from conception

## Current Projection State (June 10 2026)

Sleep last night (June 9): 8h 53m — best night this week
Resting HR trend: 69→59→74→67→63 bpm (June 8 spike notable)
Steps range: 710 (today, partial) to 13,601 (June 6)
Active energy June 5: 28 kcal (anomaly — trailer move day, minimal activity)

## How to Use in an Atmos Session

Load this project first:
  read_file /home/jeremy/projects/stratigraph/vitals-station/README.md

Then load current vitals:
  read_file /home/jeremy/projects/stratigraph/vitals-station/health-data/projection-micro.md

Optional historical context:
  read_file /home/jeremy/projects/stratigraph/vitals-station/health-data/projection-meso.md
  read_file /home/jeremy/projects/stratigraph/vitals-station/health-data/projection-macro.md

## Daily Automation

Set up Health Auto Export automation:
  URL:    https://karma-01.tail3cae5f.ts.net:8080/ingest
  Method: POST
  Format: JSON
  Schedule: daily, "since last sync"
  iPhone must be on Tailscale when it fires.

## Next Move

Nothing urgent. Let daily automation run for a week.
First Atmos integration: load projection-micro.md at start of a weather report session
and see how it reads alongside Atmos events.
