---
archived: 2026-06-10
challenged_by: 1a18d2e — genome: README restructure — STRATIGRAPH.md/README.md/NOW.md named
superseded_by: conclusions.md
slug_story: readme-restructured-three-files-named
reconstruction_fidelity: separable-sources
reconstruction_note: >
  Archived retroactively June 10 2026 from git history (commit 5025a59).
  Content is verbatim from that commit — high fidelity, real source record.
  Not archived live at the time of update. Unconformity named in genome event
  20260610_*_conclusions-archive-retroactive-reconstruction.md
---

# Conclusions — Vitals Station

> The living synthesized read. This covers the design of the Vitals Station
> itself — decisions made, why, and how understanding evolved. Health data
> state lives in health-data/ and uses a projection model, not this layer.

---

## The Question

What is the right architecture for receiving Apple Health telemetry from an
iPhone, storing it immutably, and serving it as a clean read model to any
consumer — starting with Atmos, but agnostic to future applications?

---

## Current Read

The system is **Vitals Station**: an immutable health event log and
projection engine. It receives JSON from Health Auto Export (iPhone),
stores raw events immutably, and will rebuild a deduplicated projection
on every ingest. It records. It does not interpret.

**Infrastructure is stable.** Server runs as a systemd user service on
karma-01 (Tailscale-only, TLS, port 8080). Survives reboots and session
restarts independently. Three-file architecture (STRATIGRAPH.md /
README.md / NOW.md) gives fresh sessions full cold-start orientation
from a single `read README.md` command.

**Wire format is fully known.** Three distinct data-point shapes exist
in the real export. The converter must handle all three. Sleep analysis
and heart rate are special cases. 17 remaining metrics split between
interval (Shape A: date/start/end/qty/source) and point-in-time
(Shape D: date/qty/source).

**High-frequency granulation is the next design problem.** Step count
arrives at 21K+ data points per day. The projection needs aggregation
strategy before it can be useful. That decision is next.

Key design bets (all standing):
- Events are immutable. Projection is the mutable read model. Never mixed.
- Design decisions live here. Computed health state lives in health-data/.
- Wire format drives schema. Documentation is a hint, not a spec.
- Tailscale-only exposure. TLS via Let's Encrypt. No public surface.
- Classical code in the ingestion pipeline. Model reads; does not process.
- De-dupe key: (metric_name, date_utc).

Atmos is the first consumer. The projection is agnostic to who reads it.

---

## Open Threads

- **Aggregation strategy:** daily summary vs. hourly buckets vs. both?
  Step count / active energy → sum. Heart rate → avg/min/max. Sleep →
  stage breakdown. Decides when converter is written.
- **sleep_analysis `value` field:** HKCategoryValue strings need mapping
  to human-readable stage names.
- **heart_rate `context` field:** unknown until raw data inspected.
- **startDate/endDate in sleep_analysis:** may duplicate start/end.
  Confirm before schema is written.
- **Projection schema:** what does Atmos need to read cleanly?
