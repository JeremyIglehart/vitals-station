---
archived: 2026-06-10
challenged_by: 5025a59 — genome: schema-discovery event — wire format known
superseded_by: conclusions.md
slug_story: schema-discovered-wire-format-known
reconstruction_fidelity: separable-sources
reconstruction_note: >
  Archived retroactively June 10 2026 from git history (commit e7e0e72).
  Content is verbatim from that commit — high fidelity, real source record.
  Not archived live at the time of update. Unconformity named in genome event
  20260610_*_conclusions-archive-retroactive-reconstruction.md
---

# Conclusions — Vitals Station

> The living synthesized read. This covers the design of the Vitals Station itself —
> decisions made, why, and how understanding evolved. The health data layer lives in
> health-data/ and uses a projection model, not this conclusions model.

---

## The Question

What is the right architecture for receiving Apple Health telemetry from an iPhone,
storing it immutably, and serving it as a clean read model to any consumer — starting
with Atmos, but agnostic to future applications?

---

## Current Read

The system is **Vitals Station**: an immutable health event log and projection engine.
It receives JSON exports from Health Auto Export (iPhone), converts them to a standard
Markdown event schema, appends to an event log, and rebuilds a deduplicated projection
on every ingest. It records. It does not interpret.

**Wire format is now known (not assumed).** Three distinct data-point shapes exist in
the real export — not one. The converter must handle all three. Sleep analysis and
heart rate are special cases; the remaining 17 metrics split cleanly between interval
(Shape A) and point-in-time (Shape D).

**High-frequency granulation is the next design problem.** Step count arrives as
21,000+ data points per day at watch-sample granularity. The projection needs
aggregation strategy before it can be useful to Atmos. That decision is the next event.

Key design bets (still standing):
- Events are immutable. Projection is the mutable read model. Never mixed.
- Design decisions live here. Computed health state lives in health-data/.
- Wire format drives schema. Documentation is a hint, not a spec.
- Tailscale-only exposure. TLS via Let's Encrypt (tailscale cert). No public surface.
- Classical code in the ingestion pipeline. Model reads projections, does not process data.
- De-dupe key: (metric_name, date_utc) — collapses overlapping export windows at projection time.

Atmos is the first consumer. The projection is agnostic to who reads it.

---

## Open Threads

- **Aggregation strategy:** Daily summary vs. hourly buckets vs. both? Decide when
  converter is written. Step count / active energy need summation; heart rate needs
  avg/min/max; sleep needs stage breakdown.
- **sleep_analysis `value` field:** Contains HKCategoryValue strings (Apple internal
  sleep stage names). Need a clean mapping to human-readable stage names.
- **heart_rate `context` field:** Unknown until inspected. May indicate measurement
  context (resting, workout, etc.).
- **startDate/endDate in sleep_analysis:** Appear to duplicate start/end. Confirm
  before deciding whether to discard or preserve in the event schema.
- **Projection schema:** What does Atmos actually need to read cleanly? Design this
  with the first Atmos integration in mind.
