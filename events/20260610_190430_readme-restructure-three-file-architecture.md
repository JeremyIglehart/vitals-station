---
event_type: design-evolution
recording_mode: live
date_time: 2026-06-10T13:04:30-06:00
---

## README Restructure — Three-File Architecture Established

The original genome (README.md) was doing three jobs that belong to
three different things with three different update cadences. Separating
them was a design decision with real alternatives considered.

---

## The Problem

A fresh session needed cold-start orientation — what is this project,
what's working, what's next. The genome (README.md) was the natural
place to put it. But writing operational state into the genome would
have overwritten the Stratigraph protocol. That's not a README update.
That's a lobotomy.

**Fork considered:**

- Overwrite README.md with project content — rejected. Destroys the genome.
  The Stratigraph protocol is what makes this system work. It is not
  replaceable with operational notes.
- Add a NOW.md alongside the unchanged README.md — closer, but the
  README would still be a generic bootstrap template with no project
  identity at the root.
- Three-file split (chosen): rename genome to STRATIGRAPH.md, write a
  project-specific README.md, and keep NOW.md as the live edge only.

---

## The Three Files and Their Jobs

**STRATIGRAPH.md** — the genome. The Stratigraph protocol exactly as
designed. Updated only when the protocol itself evolves — rare, requires
its own genome event first. Four self-references patched from "README.md"
to "STRATIGRAPH.md" so the genome is honest about its own location.
TEMPLATE_conception.md removed — it served its purpose and was noise.

**README.md** — the project front door. Vitals Station identity, fresh
session load order (imperative, tool-call level), project structure map,
server operations, TLS cert info, update cadence. Updated when stable
project facts change — not every session.

**NOW.md** — the live edge. Current state, open threads, next move.
Updated anytime — even mid-session. Committed immediately every time.
The rule: NOW.md must never drift from committed state. A session crash
only loses the conversation since the last commit, never committed state.

---

## Why This Preserves Stratigraphic Memory

The Stratigraph still runs exactly as designed:
- Events are immutable. The restructure is itself an event (this one).
- Conclusions are updated when understanding shifts.
- The genome (STRATIGRAPH.md) is intact and honest.
- NOW.md is operational state, not protocol — it doesn't mix layers.

A fresh session reads README.md → STRATIGRAPH.md → conclusions.md →
NOW.md → git log. Full context. No reconstruction needed. No session
memory required. The system is self-orienting.

---

## Systemd Service Decision

Recorded here because it was made in the same session and is
architectural. The server was previously a Hermes background process —
it would die with the session or a gateway restart, silently dropping
exports sent during the gap.

**Fork considered:**
- Keep as Hermes background process — rejected. Session-coupled.
  Health Auto Export sends on a schedule, not when a session is open.
- systemd user service — chosen. Independent of session lifecycle.
  Survives reboots, auto-restarts on crash, logs to journalctl.
  Service file committed to repo at server/vitals-station.service so
  the install procedure is always reproducible.

---

## Files Changed

- README.md → STRATIGRAPH.md (renamed, 4 self-references patched)
- TEMPLATE_conception.md (deleted)
- README.md (new — project front door)
- NOW.md (new — live edge)
- server/vitals-station.service (new — systemd unit, committed to repo)
