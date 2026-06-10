---
event_type: design-decision
recording_mode: live
date_time: 2026-06-10T14:14:08-06:00
---

## Session Close — Three Operational Decisions

Three decisions made in the final stretch of the bootstrap session
that weren't captured in the prior genome event.

---

## Decision 1: Load Window — 8 Days, Not 7

**The question:** How many days of processed exports should the converter
load to build a 7-day macro projection?

**The answer surfaced by real data:** The seam analysis showed that export
files regularly carry records from the prior day at the boundary. The June 9
export had records starting at June 8 23:58:41 — nearly midnight the night
before. A strict 7-day load window would silently drop those records.

**Decision: LOAD_DAYS = 8.** Load 8 days of files to guarantee the 7-day
projection is complete. The extra file costs negligible time and closes a
real data loss risk. Not paranoia — boundary bleed is confirmed in the
actual wire data.

**Fork considered:** Load all history, filter at projection build time.
Rejected — load time grows linearly with history. Windowed file selection
keeps runtime flat at ~14 seconds regardless of how much history accumulates.

---

## Decision 2: Telegram Notification via Hermes CLI

**What was built:** At the end of every `converter.run()`, a summary
notification is sent to the Karma B-Side Telegram group via `hermes send`.

**Message format:**
  ✓ Vitals Station — ingest complete
  Date: YYYY-MM-DD  |  Ns  |  NNN,NNN records  |  N exports on file
  Anomalies yesterday (YYYY-MM-DD):
    metric: value at HH:MMam

**Why B-Side:** Health data is personal context for Karma sessions, not
a system alert. B-Side is the right channel — private, already used for
Karma context work.

**Implementation note:** `hermes send -t "telegram:Karma B-Side (group)" msg`
is the correct CLI invocation. `python -m hermes` does not work — hermes
is a CLI binary at `~/.local/bin/hermes`, not a Python module.

**Anomaly cap:** Maximum 5 anomalies in the notification to prevent flooding.
Full anomaly list always available in projection-meso.md.

---

## Decision 3: GitHub Remote — Private Repo

**Motivation:** The repo lived only on karma-01. A single machine failure
would lose 21 commits of design thinking, a week of health data, and the
full pipeline implementation.

**Action:** Created private repo at https://github.com/JeremyIglehart/vitals-station
via `gh repo create vitals-station --private --source . --push`.
All 21 commits pushed. Branch tracking set. Future commits push with
`git push` from the vitals-station directory.

**Note:** The processed JSON exports in inbox/processed/ are committed to
git — this means health data lives in the GitHub repo. This was a conscious
choice: the data is already on karma-01 (a remote server), and GitHub
private repos are private. If this changes (e.g. repo goes public, data
sensitivity increases), the processed/ directory should be added to
.gitignore and health data managed separately.
