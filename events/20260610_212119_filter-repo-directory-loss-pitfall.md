---
event_type: pitfall
recording_mode: live
date_time: 2026-06-10T15:21:19-06:00
---

## Pitfall: git filter-repo Removes Filtered Paths From Working Directory

When `git filter-repo` rewrites history to remove paths, it checks out
the new HEAD after completing. Any path that no longer exists in the
rewritten history is deleted from the working directory.

**What happened:** After running filter-repo to remove health data from
history, the following directories vanished from disk entirely:
  - inbox/pending/
  - inbox/processed/
  - health-data/events/
  - health-data/projection-micro.md
  - health-data/projection-meso.md
  - health-data/projection-macro.md

The server kept running (systemd service, unaffected by git operations)
but `tree .` showed no data directories. The 10 days of processed
health exports were gone from disk.

**Why this matters:** These directories were gitignored (no committed
JSON/MD files), and the `.keep` files that should have preserved the
directory scaffolding were never committed before the filter-repo run.
filter-repo had nothing to leave behind.

**Fix applied:**
1. Recreated directory structure manually:
   `mkdir -p health-data/events inbox/pending inbox/processed`
2. Added `.keep` files to all three
3. Committed `.keep` files so the scaffold is tracked in git

Now a fresh clone always includes the directory structure. Data files
(JSON exports, event MDs, projection MDs) remain gitignored and never
committed — but the containers exist immediately after clone.

**Lesson for future filter-repo runs:**
Before running `git filter-repo --invert-paths` on data directories:
1. Ensure `.keep` files are committed in every directory to be preserved
2. Back up any on-disk-only data (gitignored files) before the run —
   filter-repo will delete those directories from the working directory
3. Verify directory structure with `tree` immediately after the run

**Data recovery:** The 10 processed exports are re-uploadable from the
iPhone via Health Auto Export. The pipeline recreates everything on the
next ingest. No permanent data loss — just a manual re-send required.
