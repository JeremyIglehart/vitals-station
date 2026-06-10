# This Is A Stratigraph

You are reading the genome of a Stratigraph¹ — a knowledge system defined by its protocol, not its content. Right now it has no identity. It holds no thinking yet. It knows only how to be a Stratigraph. Everything needed to operate it is in STRATIGRAPH.md. Read it, and proceed.

---

## What A Stratigraph Is

A Stratigraph applies event-sourcing not just to facts, but to **meaning**.

- **Events** are immutable. Things happened; you record them, append-only, and never edit them after.
- **Conclusions** are derived meaning — what the events *mean*, synthesized and maintained separately from the raw events.
- **Conclusions are versioned, never destroyed.** When new events challenge a conclusion, the old one is archived — verbatim, with a note on what challenged it and what replaced it. You never overwrite understanding. You stratify it.

The result is a record that holds not only *what* changed, but *why*, and *how the understanding evolved over time*. It is read the way a geologist reads rock layers: drill down, and the history is legible.

The aim is **stratigraphic memory, not photographic memory.** Photographic memory recalls every pixel and understands nothing. Stratigraphic memory keeps the layers — how the thinking moved, and why — and lets you read, query, and reanimate them.

---

## The Layers

```
<this-system>/
  STRATIGRAPH.md               ← the genome (this file)
  conclusions.md               ← current synthesized read — the living meaning
  conclusions-archive/
    <date>_<slug>.md           ← superseded conclusions, verbatim + lineage note
  events/
    <timestamp>_<slug>.md      ← immutable events, append-only, never edited
```

Three layers — events, conclusions, conclusions-archive — are the whole machine. Subdivide into sub-domains only when the shape of the thinking demands it. Start flat.

---

## The Protocol

**1. Events are immutable.** Record what happened, append-only. Never edit an event after writing it. Use a sortable timestamp in the filename (UTC is a safe default); put any local time, with offset, inside the file.

**2. Conclusions are derived meaning.** `conclusions.md` is the living synthesized read — what the events *mean*, not just what they were. Update it as events accumulate.

**3. Conclusions are versioned, never destroyed.** When a new event challenges the current read, move the old conclusion to `conclusions-archive/` — verbatim — with frontmatter naming what challenged it and what replaced it. Then write the new read into `conclusions.md`.

```yaml
---
archived: <date>
challenged_by: <event filename or description of what changed>
superseded_by: conclusions.md
slug_story: <one line — why the archive slug is what it is>
---
```

**4. Archive naming:** `<date>_<slug>.md`. The date is when the conclusion was superseded. The slug captures the spirit of what's being retired — memorable, a little funny, named with affection. Old conclusions aren't failures; they're the strata that held the weight until something better came along.

**5. The genome is a stratum too.** STRATIGRAPH.md is itself a node. When the design changes, log the design-pressure as events and give the version cut its own conclusion — why it changed, what was failing. Logging strain is not the same as cutting a version; you can record pressure several times before deciding to change anything. That gap is readable, and worth reading.

**6. When to write a genome event.** A genome event is required whenever:

- A real design decision is made — including decisions to defer something.
  The event captures what was considered, what was chosen or deferred, and why.
  NOW.md captures *what*. The genome captures *why*. Both are required.
- Something about the system's environment or data source is discovered that
  changes how the system should be understood (e.g. wire format surprises,
  behavioral properties of upstream data sources).
- A pitfall is encountered and resolved — so the next operator doesn't
  re-discover it.
- The genome itself changes (this protocol addition is an example).

A genome event is NOT required for:
- Routine data ingest (those are data events, not design events)
- Code changes that implement an already-committed design decision
- NOW.md updates that don't involve new reasoning

**The test:** if the reasoning behind a decision would be lost without
writing an event, write the event. If only the outcome matters and the
reasoning is obvious or already recorded, skip it. When in doubt, write it —
a short honest event costs nothing; a missing stratum is permanent.

---

## Beginning

This system records its own becoming.

Whatever intelligence is operating it — one, several, human, model, or some coupling of these — the first stratum is **conception**: the moment recording begins. Two honest ways in:

- **Live.** Recording starts at the beginning of the thinking. No reconstruction. The Stratigraph is present for the thinking and participates in it. This is the gold standard, and the rarer one — it requires deciding to record before the idea has proven itself.
- **Reconstructed.** Thinking already happened off-record, and recording begins partway through. This is honest *as long as the gap is marked.* The missing strata are an **unconformity** — a surface where layers are absent. You do not fake them. You note the boundary, reconstruct what you can, and flag it as reconstructed. The fidelity of a reconstruction varies, and the operator names its own tier truthfully:
  - rebuilt from real, separable source records (high fidelity), versus
  - emptied from fused working memory with no separable sources to check against (low fidelity — and the most prone to confabulation, so flag it loudest).
  - And if the operator doesn't know what it's capable of recovering — that, too, is said plainly. Being *capable* of knowing and *knowing* are different things; the honest move is to name the limit, not reason past it.

Which path applies is not assumed. It is established with whoever is present, in whatever way fits the moment. The system understands the difference; that understanding generates the right opening on its own.

A Stratigraph and the reasoning across it are not two separate systems. They are one coupled system — each shaping the other as it goes. A live Stratigraph does not merely transcribe thinking; it participates in it, cross-linking and surfacing prior strata in real time, and so it changes the very thinking it records. The map drawn while you walk changes where you step. Build accordingly, and read accordingly.

---

> ¹ **Stratigraph** is a named architecture coined by Jeremy Iglehart, June 8, 2026 — discovered while building Karma Atmos. STRATIGRAPH.md is sufficient to operate one. The full concept — etymology, thesis, features, posture (*memento mori for systems*), and the closed-system first principle — lives in `stratigraph.md` alongside this kit, if it travels with it.
