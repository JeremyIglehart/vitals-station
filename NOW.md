# NOW — Vitals Station Live Edge

Last updated: 2026-06-10T14:45:00-06:00
Session: vitals-station bootstrap session (June 10 2026) — COMPLETE

> Update this file anytime state changes. Commit immediately.

---

## What's Working

- Server: systemd user service, karma-01.tail3cae5f.ts.net:8080, TLS, Tailscale-only
  Check: `systemctl --user status vitals-station`
  Logs:  `journalctl --user -u vitals-station -n 50`
- Full pipeline: POST → inbox/pending → converter → inbox/processed + events + projections
- 11 exports processed: June 1–10 2026 (10 days of real data)
- Three live projections in health-data/
- Windowed loading: 8 days (7-day projection + 1 day boundary buffer) — ~14s rebuild
- Telegram notify: B-Side gets a ping on every ingest complete (anomalies included)
- GitHub: https://github.com/JeremyIglehart/vitals-station (private, up to date)
- Git: 24 commits, clean history from conception
- GitHub: health data purged from all history — repo is PUBLIC
  https://github.com/JeremyIglehart/vitals-station
- examples/ directory shows full pipeline with fictional data
- docs/ directory: session paper (MD + PDF) — "Building Something That
  Knows How It Became Itself" (June 10 2026)

## Current Projection State (June 10 2026)

Sleep last night (June 9): 8h 53m — best night this week
Resting HR trend: 69→59→74→67→63 bpm (June 8 spike notable)
Steps range: 710 (today, partial) to 13,601 (June 6)
Active energy June 5: 28 kcal (anomaly — trailer move day)

## Seam Gaps (source recording gaps, not pipeline losses)

  June 4→5:  159 min   trailer move night
  June 7→8:  181 min   Watch likely off/unsynced
  June 9→10:  81 min   overnight sync delay

## How to Use in an Atmos Session

Load this project:
  read_file /home/jeremy/projects/stratigraph/vitals-station/README.md

Load current vitals:
  read_file /home/jeremy/projects/stratigraph/vitals-station/health-data/projection-micro.md

Optional historical context:
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

Set up the daily iPhone automation. Then bring projection-micro.md
into an Atmos weather report session and see what it adds.
