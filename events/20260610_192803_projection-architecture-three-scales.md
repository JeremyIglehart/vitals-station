---
event_type: design-decision
recording_mode: live
date_time: 2026-06-10T13:28:03-06:00
---

## Projection Architecture — Three Temporal Scales

The projection layer uses three separate files, each covering a different
temporal scale. Atmos already thinks in micro / meso / macro. The projection
files speak that language natively.

---

## The Three Files

**projection-micro.md** — Current Read + Today (default Atmos load)
- Current Read: most recent individual value per metric with exact timestamp
- Today running summary: aggregates since midnight, partial until day closes
- Anomalies today: timestamped spikes (>2 std dev from day mean)
- Sleep: lives in Today (not Current Read) — it's a day-level metric
- Small, fast, always current. Atmos loads this every session by default.

**projection-meso.md** — Yesterday complete with arc
- Not just daily averages — the shape of the day
- Morning baseline / midday / afternoon / evening buckets
- Anomalies timestamped: exact value, exact time, deviation magnitude
- Enables Atmos to cross-reference "HR spike at 12:31pm" against its own
  event log without the Station knowing what caused it. Clean separation.
- Also carries rolling 3-day arc (today partial + yesterday + day before)
  for near-term trend visibility.

**projection-macro.md** — Rolling 7-day window
- Daily totals per metric
- Trend direction per metric (stable / rising / falling)
- Establishes personal baseline for anomaly context
- Answers: "is today normal?"

---

## Anomaly Detection Strategy

Purely deterministic. No model involvement in detection.
- Compute mean and standard deviation for each metric across all readings
  in the day's export
- Flag any reading more than 2 standard deviations from the day's mean
- Record: metric name, value, timestamp (local MDT + UTC), deviation magnitude
- No interpretation — just the number and when it happened
- Threshold tuning: start with pure statistical deviation, adjust after
  seeing first real output. Minimum fixed-range bar deferred — add if
  high-variability days produce noise.

---

## Design Rationale

Separate files keep sessions light. Atmos loads projection-micro.md by
default — small, fast, covers this moment and today. Historical depth
(meso, macro) is available but optional. The session stays clean unless
context demands the depth.

Atmos brings interpretation. The Station brings instrument readings.
These are two genuinely different jobs and the file split makes that
visible at the filesystem level — not just in the design docs.

---

## Deferred

- Fixed-range anomaly floor (add after seeing first real projection output)
- Projection cadence for macro (rebuild on every ingest vs. daily — decide
  when macro file gets costly enough to matter)
