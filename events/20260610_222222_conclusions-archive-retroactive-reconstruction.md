---
event_type: pitfall + protocol-fix
recording_mode: live
date_time: 2026-06-10T16:22:22-06:00
---

## Conclusions Archive — Retroactive Reconstruction + Protocol Fixed

---

## The Failure

conclusions.md was updated 9 times during the bootstrap session. Each update
superseded the prior version. None of them were archived before being
overwritten. The conclusions-archive/ directory remained empty the entire
session.

This is a direct violation of Stratigraph protocol rule 3 — the most
important rule in the system. The strata were being destroyed, not stratified.

Root cause: the protocol describes the archiving mechanism but did not
state the mandatory order (archive-first, then update). In a fast-moving
session, the archive step was silently skipped every time.

---

## The Recovery

All 9 superseded versions were recovered from git history using
`git show <sha>:conclusions.md`. Git is a separable source — the recovery
fidelity is high, not reconstructed from memory.

Files written to conclusions-archive/:
  2026-06-10_bootstrap-template-no-identity-yet.md
  2026-06-10_conception-the-idea-not-yet-spoken.md
  2026-06-10_design-intent-vitals-station-named.md
  2026-06-10_schema-discovered-wire-format-known.md
  2026-06-10_readme-restructured-three-files-named.md
  2026-06-10_projection-architecture-three-scales.md
  2026-06-10_bootstrap-complete-pipeline-live.md
  2026-06-10_filter-repo-pitfall-data-state-honest.md
  2026-06-10_session-closed-atmos-wired-in.md

Each file carries frontmatter with:
  reconstruction_fidelity: separable-sources
  reconstruction_note: archived retroactively from git commit <sha>

The unconformity is marked. The strata are recoverable. The record is honest.

---

## The Protocol Fix

**STRATIGRAPH.md rule 3 updated** — explicit archive-first mandate added:

  Archive-then-update, never update-then-archive. If the session dies after
  the archive write but before the conclusions update, the old version is safe.
  If the session dies after the update but before the archive, the old version
  is gone. Archive first — always.

**karma-atmos skill updated** — session-close discipline added to step 5:
  Before final commit, check: did conclusions.md change? If yes, was the prior
  version archived BEFORE the update? If not, recover from git and archive
  retroactively with reconstruction_fidelity: separable-sources.

---

## Unconformity Statement

The conclusions-archive/ directory for this project was empty from conception
(June 10 2026 morning) through the end of the bootstrap session. This is an
unconformity — a surface where layers should exist but don't. The gap has been
filled retroactively from git. The reconstruction is high fidelity. The
boundary is named here.

Everything filed in conclusions-archive/ with date 2026-06-10 was recovered
this way. Future archives will be written live, archive-first.
