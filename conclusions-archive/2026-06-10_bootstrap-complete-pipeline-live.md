---
archived: 2026-06-10
challenged_by: b6b551d — genome: bootstrap complete — inbox pipeline, anomaly scope fix
superseded_by: conclusions.md
slug_story: bootstrap-complete-pipeline-live
reconstruction_fidelity: separable-sources
reconstruction_note: >
  Archived retroactively June 10 2026 from git history (commit 72f1d2b).
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

**The system is operational.** Vitals Station is a fully running health
event log and projection engine. It receives JSON from Health Auto Export,
processes it through a pending→processed pipeline with full provenance
headers, writes immutable event records, and rebuilds three projections
on every ingest. It records. It does not interpret.

**Infrastructure:** Systemd user service on karma-01, Tailscale-only TLS,
port 8080. Survives reboots and session restarts independently. Three-file
session architecture (STRATIGRAPH.md / README.md / NOW.md) enables cold-start
from a single read command.

**Pipeline:** inbox/pending → converter → inbox/processed (YAML provenance
header + original JSON) + health-data/events/ (Markdown event record) +
three rebuilt projections. Health check: `inbox/pending/` count = 0 means
current.

**Projections — three temporal scales matching Atmos vocabulary:**
- projection-micro.md: Current Read + Today + physiological anomalies
- projection-meso.md: Yesterday arc + 3-day rolling window
- projection-macro.md: 7-day rolling window + daily totals

**Anomaly detection:** Physiological signals only (ANOMALY_METRICS whitelist).
Accumulator metrics excluded — per-second Watch granularity makes statistical
deviation meaningless on them. One anomaly per minute maximum (most extreme
value). Threshold: >2σ from day mean.

**Data:** 10 days live (June 1–10 2026). Three real seam gaps confirmed as
source recording gaps, not pipeline losses.

Key design bets (all holding):
- Events immutable. Projection is computed state. Never mixed.
- Wire format is the spec. Documentation is a hint.
- Consumer-agnostic: projection carries measured values, no interpretation.
- Classical code in pipeline. Model reads; does not process.
- De-dupe key: (metric_name, date_utc_str).

Atmos is the first consumer. Daily automation is ready to configure.

---

## Open Threads

- **Atmos integration:** load projection-micro.md at start of weather report
  sessions. First test: does it add useful signal without adding noise?
- **Anomaly floor:** fixed-range minimum bar still deferred. Revisit after
  a week of automated daily exports provides a real baseline.
- **Macro rebuild cadence:** currently rebuilds on every ingest. Fine for now;
  revisit if large historical exports make it slow.
- **June 8 HR spike (74 bpm):** resting HR elevated vs baseline 59–69.
  Worth cross-referencing against Atmos events for that day.
