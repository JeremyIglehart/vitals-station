---
event_type: design-decision
recording_mode: live
date_time: 2026-06-10T14:35:54-06:00
---

## Health Data Removed From Git History — Privacy Decision

The processed exports, event files, and projection files were committed
to git in the bootstrap session before the privacy implications were
named explicitly. This event records the decision to remove them and
why.

---

## Addendum (June 10 2026 — same session)

This event was INCOMPLETE at time of writing. test-exports/raw/ was not
included in the filter-repo path set and remained in git history. See:
20260610_222858_test-exports-missed-in-filter-repo-purge.md

The repo was not fully clean until that second filter-repo run and
repo delete+recreate completed.

---

## What Was Removed From History

All files matching these paths were purged from the full git history
using `git filter-repo --path <path> --invert-paths`:

  inbox/processed/*.json      — raw wire payloads with actual health data
  inbox/pending/*.json        — (precautionary — same class of data)
  health-data/events/*.md     — event records derived from exports
  health-data/projection-micro.md
  health-data/projection-meso.md
  health-data/projection-macro.md

The local files on disk are untouched. The data lives on karma-01 and
is re-uploadable from the iPhone at any time. Only git history was
rewritten.

---

## Why

The repo is private but intended to be shareable — with collaborators,
reviewers, anyone Jeremy chooses to give access to in the future. Health
data (even aggregated summaries in projections) should not be in that
share surface. The pipeline and the examples fully illustrate how the
system works without requiring real data to be present.

**Fork considered:**
- Keep data in git, document it as private — rejected. Private today
  does not guarantee private forever. Git history survives mistakes;
  health data in history is a permanent liability.
- Separate branch for data — rejected. More complexity, same risk.
- gitignore + history rewrite (chosen) — clean separation. The repo
  is code and genome only. Data lives locally.

---

## What Replaced the Real Data

`examples/` directory added — fictional data with round numbers and
source listed as "Example Apple Watch". Shows the full pipeline:

  examples/inbox/processed/   — one fake export with YAML provenance header
  examples/health-data/events/  — the event file it would produce
  examples/health-data/        — all three projection formats

The examples README explains these are illustrative, not real. Anyone
reading the repo sees exactly how the system works without any exposure
of real health data.

---

## .gitignore

Added to root. Covers:
  inbox/processed/*.json
  inbox/pending/*.json
  health-data/events/*.md
  health-data/projection-*.md
  **/__pycache__/ and *.pyc
  *.key (TLS private key — was already excluded via server/certs/.gitignore)

Future exports and projections will never be committed.

---

## Git History Note

`git filter-repo` rewrites commit SHAs. All 22 prior commits are
preserved with their messages and content — only the health data paths
are removed. The history is structurally intact; SHA references from
before this rewrite are stale. Force push to GitHub completed.
