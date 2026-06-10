# Examples

These files illustrate how Vitals Station works — the data shapes,
file formats, and projection output. All values are fictional.
The source is listed as "Example Apple Watch" throughout.

Nothing in this directory is real health data.

## What's here

```
inbox/processed/
  20260101_received-20260101T140000Z.json
    A single-day export with 5 metrics (12 records total).
    Shows the YAML provenance frontmatter + JSON payload structure.

health-data/events/
  20260101_received-20260101T140000Z.md
    The event record produced when the export was processed.

health-data/
  projection-micro.md   — Current Read + Today (default Atmos load)
  projection-meso.md    — Yesterday arc + 3-day rolling window
  projection-macro.md   — 7-day rolling window + daily totals
```

## How the real pipeline works

1. iPhone sends a POST to `/ingest` with a JSON export
2. Server writes raw payload to `inbox/pending/`
3. Converter processes pending → writes event to `health-data/events/`
   → prepends YAML provenance header → moves to `inbox/processed/`
4. Converter rebuilds all three projections from the full processed history
5. Telegram notification fires to Karma B-Side with a summary

The live projections live in `health-data/` (gitignored — not committed).
The live processed exports live in `inbox/processed/` (gitignored — not committed).
