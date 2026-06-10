---
event_type: design-evolution
recording_mode: live
date_time: 2026-06-10T13:59:38-06:00
---

## Bootstrap Session Complete — Three Implementation Decisions

The bootstrap session ran to completion. Three design decisions were made
during implementation that weren't pre-planned — all surfaced by real data
or real execution, not by design discussion alone.

---

## Decision 1: Inbox Pipeline Architecture

**What was built:** Two-directory inbox split — `inbox/pending/` and
`inbox/processed/`.

**Fork considered:**
- Process in place, no archive — rejected. No way to know what had been
  processed. No provenance trail. Silent loss if converter failed.
- Single directory with a processed flag file — workable but awkward.
  Two files per export, naming gets complicated.
- pending/processed split (chosen) — clean separation. pending = not yet
  processed; processed = done, archived. Health check reads `pending/` count
  directly: zero means current, non-zero means something didn't process.
  Unambiguous at a glance.

**YAML provenance header on processed files:**
The raw wire payload is immutable — never edited. Moving it to `processed/`
is itself an event. The YAML frontmatter captures: when it was processed,
what data date it covers, what event file was written, what projections were
rebuilt, record and metric counts. Standard `---` delimiters — consistent
with Atmos event files and all other Stratigraph files in this system.
The body below the frontmatter is the original JSON verbatim. Strip the
header and you have the original payload for reprocessing.

---

## Decision 2: Anomaly Detection Scope — Physiological Signals Only

**What happened:** First real projections were built and the anomaly section
in projection-meso.md produced hundreds of entries — step_count alone
generated thousands of anomaly lines filling the entire file.

**Root cause:** Step count, active energy, distance, and stand time arrive
at per-second Watch sampling granularity — thousands of near-identical
micro-values per day. Standard deviation across them is extremely small.
Almost every value is "statistically unusual" relative to the others because
they're all nearly identical sub-integer fragments, not meaningful readings.

**Fix:** Introduced `ANOMALY_METRICS` whitelist — physiological signals only:
  heart_rate, resting_heart_rate, heart_rate_variability,
  blood_oxygen_saturation, respiratory_rate, body_temperature,
  wrist_temperature, walking_heart_rate_average

Accumulator metrics (steps, distance, active energy, stand time) excluded
entirely from anomaly detection. They belong in daily totals, not anomaly
flags. Additionally deduped anomalies to one per minute (most extreme value
wins) to prevent the same event generating multiple entries.

**Result:** First clean anomaly output — four entries for June 9:
  - Blood oxygen dip to 91% at 12:40am (genuinely low, worth noting)
  - Respiratory rate spike to 22.5/min at 4:36am (elevated during sleep)
  - Two lower respiratory readings mid-morning

This is the kind of signal Atmos can cross-reference against its own
event log without the Station needing to know what caused it.

---

## Decision 3: System Operational — First Week of Real Data

**Bootstrap session output:**
- 10 exports processed: June 1–10 2026
- 11 files in inbox/processed/ (June 9 exported twice — dedup handled it)
- 10 event files in health-data/events/
- Three projections live and Atmos-ready

**Seam analysis — real gaps confirmed as source gaps, not pipeline losses:**
  June 4→5:  159 min gap — trailer move night, Watch likely off/unsynced
  June 7→8:  181 min gap — June 7 export ends at 9pm, Watch may have been off
  June 9→10:  81 min gap — overnight sync delay, normal Watch behavior
  All other seams: smooth (overlapping exports, dedup handled correctly)

**First week pattern visible in macro projection:**
  - June 8 resting HR spike to 74 bpm (baseline 59–69) — notable
  - June 5 active energy near-zero (28 kcal) — trailer move day, minimal movement
  - June 9 best sleep of the week (8h 53m)
  - June 6 highest step count (13,601)

These are the first data points available for Atmos cross-reference.

---

## System State at Session Close

Pipeline: fully operational. Server: systemd user service, running
independently of any session. Daily automation: ready to configure on iPhone
("since last sync" → POST to ingest endpoint). Next: let automation run for
a week, then integrate projection-micro.md as standard read into Atmos
weather reports.
