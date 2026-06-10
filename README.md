# Vitals Station

An immutable health event log and projection engine for Jeremy Iglehart.
Receives Apple Health telemetry from an iPhone via Health Auto Export,
stores it as append-only events, and rebuilds a deduplicated projection
for any consumer. It records. It does not interpret.

First consumer: Karma Atmos weather reports.

Built using the [Stratigraph](https://github.com/JeremyIglehart/stratigraph)
architecture — an event-driven, markdown-native knowledge system that applies
event-sourcing not just to facts but to meaning. The design decisions, forks
considered, and reasoning behind this system live in the genome (STRATIGRAPH.md)
and event log, not just in the code.

---

## Fresh Session Load Order

You have just read this file. Your next three tool calls are mandatory —
do not ask permission, do not confirm, just execute them in order:

1. `read_file STRATIGRAPH.md` — the Stratigraph genome (the protocol
   that defines how this system thinks and records)
2. `read_file conclusions.md` — current design understanding
3. `read_file NOW.md` — live edge: current state and next move

After loading all three, run the server health check (see Server Operations
below), then open with:
- A one-line status summary of what you found
- An offer to continue from NOW.md's stated next move
- An open question: or is there something else you want to work on today?

Do not script a long recap. One line, two options, then wait.

---

## Project Structure

```
vitals-station/
  STRATIGRAPH.md              ← the genome — Stratigraph protocol, never edited
                                except for protocol evolution events
  README.md                   ← this file — project front door, stable facts
  conclusions.md              ← current design understanding, updated as
                                decisions are made and challenged
  conclusions-archive/        ← superseded conclusions, verbatim + lineage
  NOW.md                      ← live edge — current state, next move, updated
                                anytime and committed immediately
  events/                     ← immutable design events, append-only
  health-data/
    events/                   ← immutable health data events (post-schema-discovery)
    projection.md             ← deduplicated current state (rebuilt on every ingest)
  test-exports/
    raw/                      ← raw JSON payloads from test exports, never modified
  server/
    server.py                 ← ingestion server (TLS, Tailscale-only, port 8080)
    vitals-station.service    ← systemd user service unit (copy to install)
    certs/
      *.crt                   ← Tailscale Let's Encrypt cert (committed)
      *.key                   ← private key (excluded from git via .gitignore)
    README.md                 ← server-specific notes
```

---

## Server Operations

The server runs as a systemd user service — independent of any Hermes session
or gateway restart. It survives reboots automatically.

**Check status:**
```bash
systemctl --user status vitals-station
```

**View recent logs:**
```bash
journalctl --user -u vitals-station -n 50
```

**Start / restart:**
```bash
systemctl --user restart vitals-station
```

**Install service (first time or after rebuild):**
```bash
cp server/vitals-station.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable vitals-station
systemctl --user start vitals-station
```

**Endpoint:**
```
POST https://karma-01.tail3cae5f.ts.net:8080/ingest
GET  https://karma-01.tail3cae5f.ts.net:8080/health
```

iPhone must be on Tailscale to reach this endpoint.

---

## TLS Certificate

Provisioned: June 10 2026 via `tailscale cert karma-01.tail3cae5f.ts.net`
Provider: Let's Encrypt (free, via Tailscale Personal plan)
Trusted by: iOS automatically — no profile install needed
Renewal: re-run `tailscale cert karma-01.tail3cae5f.ts.net` when expired
Note: machine name `karma-01` published to Certificate Transparency ledger
(public record, not public access) — reviewed and accepted June 10 2026.

---

## Update Cadence

- **STRATIGRAPH.md** — only when the Stratigraph protocol itself evolves.
  Rare. Requires a genome event first.
- **README.md** — when stable project facts change: new infrastructure,
  new endpoints, architectural shifts. Not every session.
- **conclusions.md** — when design understanding is challenged or deepened.
  Driven by events.
- **NOW.md** — anytime. Update mid-session if state changes. Commit immediately
  every time — do not let NOW.md drift from committed state.

---

## Source App

Health Auto Export — healthyapps.dev
Export format: JSON, metrics list at help.healthyapps.dev/en/health-auto-export/export-format/health-metrics/
Active metrics in Jeremy's config: 19 (confirmed from first export June 10 2026)
