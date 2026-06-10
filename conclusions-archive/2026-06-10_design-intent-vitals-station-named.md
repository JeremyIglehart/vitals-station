---
archived: 2026-06-10
challenged_by: e7e0e72 — design-intent: Vitals Station named, pattern locked
superseded_by: conclusions.md
slug_story: design-intent-vitals-station-named
reconstruction_fidelity: separable-sources
reconstruction_note: >
  Archived retroactively June 10 2026 from git history (commit dc1db0f).
  Content is verbatim from that commit — high fidelity, real source record.
  Not archived live at the time of update. Unconformity named in genome event
  20260610_*_conclusions-archive-retroactive-reconstruction.md
---

# Conclusions — Vitals Station

> The living synthesized read. This is what the events *mean*, not just what they were.
> This layer covers the design of the Vitals Station itself — decisions made, why, and
> how the understanding of the system evolved. The health data layer lives in health-data/
> and uses a projection model, not this conclusions model.

---

## The Question

What is the right architecture for receiving Apple Health telemetry from an iPhone,
storing it immutably, and serving it as a clean read model to any consumer — starting
with Atmos, but agnostic to future applications?

---

## Current Read

The system is **Vitals Station**: an immutable health event log and projection engine.
It receives JSON exports from Health Auto Export (iPhone), converts them to a standard
Markdown event schema, appends them to an event log, and rebuilds a deduplicated
projection on every ingest. It records. It does not interpret.

Key design bets:
- Events are immutable. The projection is the mutable read model. These are never mixed.
- Conclusions (authored meaning) live here. Projections (computed state) live in health-data/.
- The first ingest is a schema-discovery event — the wire format drives the schema, not docs.
- Tailscale-only exposure. No public internet surface.
- Classical code in the ingestion pipeline. The model reads projections; it does not process data.

Atmos is the first consumer. The projection is agnostic to who reads it.

---

## Open Threads

- What does the actual JSON wire format look like? (Arrives with first test export)
- What metrics will Jeremy have active in his Health Auto Export configuration?
- What does the projection schema need to look like for Atmos to read it cleanly?
- Does health-data/ need sub-domains per metric category, or is flat sufficient?
