---
event_type: pitfall + security-fix
recording_mode: live
date_time: 2026-06-10T16:28:58-06:00
---

## test-exports/ Missed in filter-repo Purge — Personal Data on Public Repo

---

## The Problem

The first privacy cleanup (filter-repo run, June 10 2026) scrubbed:
  inbox/processed/*.json
  inbox/pending/*.json
  health-data/events/*.md
  health-data/projection-*.md

It missed:
  test-exports/raw/20260610_182039_001.json  — 9.9MB, 59,529 data points

This file was committed in 3 commits as the schema-discovery export:
  c375b58  pipeline: inbox/pending→processed
  3d11658  schema-discovery: first real export landed
  b39a6ae  scaffold: server + test-exports/raw dir

The file contained 19 metrics, June 8–9 2026, with device-source strings
carrying the actual name "Jeremy Iglehart" and "Jeremy's Apple Watch" —
a full day of physiological telemetry tied to a real identity, live on
the public GitHub repo.

This was caught by an independent Opus audit (Claude.ai deep research)
after the repo was made public. The schema-discovery event itself recorded
the path (`test-exports/raw/20260610_182039_001.json — 9.9MB, committed
to git`) — the location was documented. It just wasn't in the filter-repo
path set.

---

## The Fix

1. filter-repo run adding test-exports/ to the purge:
   `git filter-repo --path test-exports/ --invert-paths --force`

2. Verified: `git log --all -- "test-exports/"` returns empty. Clean.

3. Verified: 23 on-disk health files untouched (not in git, gitignored).

4. Force pushed to GitHub.

5. Deleted and recreated the GitHub repo from scratch.
   Reason: GitHub's object store caches blobs after force push until GC
   runs — timing is unpredictable on public repos. Delete + recreate is
   the only guarantee that the blob is gone for future cloners.
   Anyone who cloned the repo during the window it was public retains
   the blob locally — nothing can be done about that.

6. Re-published as public.

---

## Lesson

When running filter-repo to remove health data, the path set must include
ALL directories that ever held real data — not just the ones in the current
gitignore. The schema-discovery workflow created test-exports/raw/ as a
staging directory BEFORE the gitignore existed. It was committed, used,
then superseded by inbox/. The gitignore covered inbox/ but test-exports/
was an orphaned committed path that required explicit filter-repo removal.

**Checklist before any filter-repo privacy run:**
1. `git log --all --name-only | grep -E "\.json|health|export|vitals"` —
   find ALL paths ever committed that could contain health data
2. Include every found path in the --path set
3. After filter-repo: verify with `git log --all -- "<each path>"` returns empty
4. Force push, then delete + recreate the GitHub repo for public repos
5. Verify the new repo has no object store artifacts by cloning fresh

---

## Unconformity Note

The prior privacy event (20260610_203554) stated the repo was safe to share.
That was incorrect at time of writing — test-exports/ was still in history.
This event supersedes that safety claim. The repo is now clean.
