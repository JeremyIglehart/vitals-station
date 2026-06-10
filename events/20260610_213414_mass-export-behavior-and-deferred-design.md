---
event_type: design-decision
recording_mode: live
date_time: 2026-06-10T15:34:14-06:00
---

## Mass Export Behavior Confirmed + Three Design Decisions Deferred

---

## Discovery: Mass Export Splits By Day Automatically

Health Auto Export, when given a multi-day date range, automatically
splits the export into one file per day and queues them sequentially.
Each day arrives as a separate POST to /ingest.

**Why this matters:** The pipeline was designed to handle multi-day
exports in a single file (dedup by metric+timestamp). That still works.
But the real behavior is cleaner — one file per day, arriving in order,
no overlap to resolve. The dedup logic remains correct and necessary
(re-sending a day produces a duplicate POST) but the primary ingestion
pattern is now confirmed as single-day files.

**Operational consequence:** Re-uploading 10 days of data is one button
tap with a date range — Health Auto Export handles the rest. No manual
per-day sends required.

---

## Design Decision 1: Telegram Notification — Date Range (deferred)

**What was named:** The current notification reports when the export
arrived, not what time period it covers. The more useful signal is
the data date — "June 9 processed" rather than "received at 14:32Z."

**Also named:** For exports covering today, the notification should
include a baseline vitals summary (resting HR, HRV, blood oxygen,
respiratory rate) and activity summary (steps, distance, active energy,
sleep) inline — a quick instrument read without opening a session.

**Why deferred:** Low urgency. The pipeline works. This is a UX
improvement, not a correctness fix. Deferred to a future session.

---

## Design Decision 2: 30-Day Lookback Projection (deferred)

**What was named:** projection-macro.md covers 7 days. A 30-day
rolling window would enable baseline calibration, seasonal pattern
detection, and longitudinal Atmos cross-reference over a longer arc.

**Design constraints already named:**
- Not rebuilt on every ingest — too expensive at 30-day scale
- Triggered manually when needed
- Same projection format as macro — daily totals + trend direction

**Why deferred:** Not enough data yet (10 days on file). Revisit after
60+ days of automated daily exports. Deferred to a future session.

---

## Stratigraphic Discipline Note

These items were initially written only to NOW.md (as future work)
without a genome event. The genome event was prompted after the fact.

This is the named failure mode: items land in NOW.md but the reasoning
behind deferral and the design context that produced the decision are
not captured. NOW.md is the live edge — it names *what* is deferred.
The genome is the reasoning record — it names *why*, what was considered,
and what would change the decision. Both are required.

See STRATIGRAPH.md for the updated protocol on when genome events are
required.
