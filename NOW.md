# NOW — Vitals Station Live Edge

Last updated: 2026-06-10T12:55:00-06:00
Session: vitals-station bootstrap session (June 10 2026)

> Update this file anytime state changes. Commit immediately — do not let
> this file drift from committed state. Even mid-session, commit the update.

---

## What's Working

- Server: running as systemd user service on `karma-01.tail3cae5f.ts.net:8080`
  (TLS, Tailscale-only). Check: `systemctl --user status vitals-station`
- TLS cert: provisioned June 10 2026, Let's Encrypt via Tailscale
- First test export: received and committed — 9.9MB, 19 metrics, June 9 2026 data
- Wire format: fully known. Three data-point shapes confirmed (see schema-discovery event)
- Project structure: STRATIGRAPH.md + README.md + NOW.md in place
- Git log: 9 commits, clean history from conception to here

## What's Not Built Yet

- Health data converter (JSON → Markdown event schema)
- health-data/events/ populated (empty — waiting for converter)
- projection.md (no projection until converter exists)
- De-dupe logic
- Aggregation strategy for high-frequency metrics (step_count: 21K pts/day)

## Open Design Questions

- **Aggregation strategy:** daily summary vs. hourly buckets vs. both?
  Step count / active energy → sum. Heart rate → avg/min/max.
  Sleep → stage breakdown. This gets decided when converter is written.
- **sleep_analysis `value` field:** HKCategoryValue strings need mapping
  to human-readable sleep stage names.
- **heart_rate `context` field:** unknown — inspect raw data to determine.
- **Projection schema:** what does Atmos need to read cleanly?

## Next Move

Design the aggregation strategy and Markdown event schema, then build
the converter. Start with the aggregation decision — it drives everything else.

---

## Git Log (last 5)
Run `git log --oneline -10` to see current state.
