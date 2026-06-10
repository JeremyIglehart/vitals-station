---
archived: 2026-06-10
challenged_by: 72f1d2b — genome: projection architecture — three scales, meso/micro/macro
superseded_by: conclusions.md
slug_story: projection-architecture-three-scales
reconstruction_fidelity: separable-sources
reconstruction_note: >
  Archived retroactively June 10 2026 from git history (commit 1a18d2e).
  Content is verbatim from that commit — high fidelity, real source record.
  Not archived live at the time of update. Unconformity named in genome event
  20260610_*_conclusions-archive-retroactive-reconstruction.md
---

# Conclusions — Vitals Station

> The living synthesized read. Design decisions and why. Health data state
> lives in health-data/ and uses a projection model, not this layer.

---

## The Question

What is the right architecture for receiving Apple Health telemetry from an
iPhone, storing it immutably, and serving it as a clean read model to any
consumer — starting with Atmos, but agnostic to future applications?

---

## Current Read

The system is **Vitals Station**: an immutable health event log and
projection engine. It records. It does not interpret.

**Infrastructure is stable.** Systemd user service, TLS, Tailscale-only.
Three-file session architecture (STRATIGRAPH.md / README.md / NOW.md)
gives fresh sessions full cold-start orientation.

**Wire format is fully known.** Three data-point shapes. All timestamps
carry -0600 (MDT). Deterministic parse.

**Projection architecture is decided.** Three files, three temporal scales,
matching Atmos's own micro/meso/macro vocabulary:

- projection-micro.md: Current Read + Today + today's anomalies (default load)
- projection-meso.md: Yesterday arc + 3-day rolling window
- projection-macro.md: 7-day rolling window + trend direction

Anomaly detection: pure statistical (>2 std dev from day mean). Timestamped,
value + deviation recorded. No interpretation.

Key design bets (all standing):
- Events immutable. Projections are computed state. Never mixed.
- Wire format drives schema. Docs are hints.
- Tailscale-only, TLS, no public surface.
- Classical code in ingestion pipeline. Model reads; does not process.
- De-dupe key: (metric_name, date_utc).
- Consumer-agnostic: projection carries measured values only, no labels.

---

## Open Threads

- **Converter:** JSON → health-data/events/ + rebuild all three projections.
  Next build target.
- **sleep_analysis `value` field:** HKCategoryValue strings → human stage names.
- **heart_rate `context` field:** unknown until inspected in converter build.
- **Anomaly floor:** fixed-range minimum bar deferred until first real output.
- **Macro rebuild cadence:** daily vs. every-ingest — decide when it matters.
