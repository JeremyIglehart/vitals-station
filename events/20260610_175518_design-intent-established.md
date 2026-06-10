---
event_type: design-intent
recording_mode: live
date_time: 2026-06-10T11:55:18-06:00
---

## Vitals Station — Identity and Design Intent Established

The idea was fully spoken in this session. The system now has a name and a purpose.

---

## Name

**Vitals Station.**

Etymology: "Vitals" names what it records (the baseline clinical read of a body — pulse,
rhythm, sleep, movement, temperature). "Station" names what it does (receives telemetry
from instruments, records faithfully, serves any consumer that asks). Neither word owns
an interpreter. Any application — Atmos today, something unconceived tomorrow — reads
from it without the system needing to know.

Rejected: "The Station" (agnostic to content — too opaque at distance). Runner-up named
and held: "Datum" (geodetic/ML provenance — technically correct, less legible to humans).

---

## Purpose

The Vitals Station receives and immutably logs Apple Health telemetry exported from
Jeremy's iPhone via Health Auto Export (healthyapps.dev). It records events. It does
not interpret them. It creates a deterministic projection from all events, deduplicated
on (metric_type, source_timestamp_utc). The projection is the read model. Any consumer
reads the projection. No consumer should need to read raw events to understand current state.

One sentence: **It records. It does not interpret.**

---

## Design Decisions Made

- **Pattern:** EDA. Events are immutable, append-only. Projection is computed state,
  rebuilt deterministically from the full event log. This is not a Stratigraph
  conclusions layer — it is a projection layer. The distinction is named explicitly:
  conclusions = authored meaning (human+AI synthesis); projection = computed state
  (mechanical, reproducible, no interpretation required).

- **Stratigraph structure extension:** Top-level README/conclusions.md/conclusions-archive/
  serves as the design-thinking layer (this conversation, design decisions, why things
  changed). A `health-data/` subdomain carries events/, projection.md,
  projection-archive/. Two layers, two jobs, both visible.

- **Transport:** REST API endpoint. Binds exclusively to the Tailscale network interface
  on karma-01 (100.95.70.33). Not exposed to the public internet. iPhone is on Tailscale.
  One port, one surface.

- **Timezone handling:** Apple Health Auto Export embeds ISO 8601 timestamps with UTC
  offsets in the JSON. The converter reads the offset directly from the incoming data —
  no inference, no model involvement. UTC timestamp goes in the event filename (sort-safe).
  Original local timestamp + detected offset recorded verbatim inside the event file.

- **De-dupe key:** (metric_type, source_timestamp_utc). Duplicate data points across
  overlapping export windows collapse at the projection layer. Both events stay on disk.

- **Schema discipline:** First API call is a named schema-discovery event. The Markdown
  schema is derived from real incoming data, not documentation assumptions. Documentation
  consulted (help.healthyapps.dev — 100+ metrics, 13 active by default) but real wire
  format takes precedence. Schema evolution is free: new fields in newer events, old
  events don't break.

- **Server language / approach:** Classical programming, no AI in the ingestion pipeline.
  Deterministic. The model's job is design and projection reading — not data processing.

- **Projection format:** Single flat file to start (all metrics, current state). Finer
  granularity if the shape demands it later — Stratigraph's own "start flat" principle.

- **Consumer relationship:** Atmos is the first reader. The projection is agnostic to
  consumer. Atmos reads it; the Vitals Station does not know or care what Atmos does
  with it.

---

## Deliberately Deferred

- Actual JSON wire format (arrives with first test export)
- Markdown event schema (derived from first real call)
- Port number and server implementation details
- Projection file schema (derived after first event lands)
- health-data/ subdomain directory structure (scaffold on first real event)

---

## Commit Discipline Established

Every event write = one git commit. Conclusions update included in the same commit as
the event that drove it. Genome changes = their own commit. No uncommitted events.
