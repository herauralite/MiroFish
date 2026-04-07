# Auralite v1 Readiness

## Purpose

This document turns the roadmap and completion gates into a simple release question:

**What still blocks Auralite from being honestly called a full-sim v1?**

This is a practical status document, not a marketing document.

---

## Current read

Auralite is now best described as:

**a credible sim core with strong long-horizon behavior and strong compare/readback support, but not yet a finished full-sim v1.**

### What is already strong

- reasoning and explainability architecture
- bounded intervention-quality semantics
- district and city topology realism
- household and institution carry-over state
- compare, checkpoint, and continuation artifacts
- restore and continue durability
- long-horizon acceptance coverage across multiple scenario families

### What is still open

- wider district-family calibration breadth
- broader 20+ tick cross-family soak coverage
- final operator workflow polish
- remaining thin spots in resident/household/institution autonomy
- final semantic freeze and v1 declaration rules

---

## What must be true before calling this v1

### 1. World realism is broad enough
The sim must behave credibly across a wider family matrix, not just a few tuned cases.

This includes:
- fragile-core vs resilient-ring districts
- resilient pockets vs weak corridors
- mixed-support and mixed-transition regimes
- local-win / broad-miss intervention cases
- repeated failed-help and trust-collapse pockets inside otherwise improving areas
- backlog-heavy and lag-heavy paths

**Current status:** partially satisfied.

### 2. Repeated-cycle actor memory changes later outcomes
Residents, households, and institutions must not just store memory fields. Those fields must change what happens later.

Examples:
- failed-help streaks worsen later help conversion
- trust collapse widens recovery gaps
- repeated lag mutes later relief
- debt and service scars shape later district and city behavior

**Current status:** meaningfully advanced, not fully closed.

### 3. Compare / checkpoint / continuation flows feel complete
An operator should be able to inspect:
- what diverged
- why it diverged
- whether the path is live vs checkpoint vs restored continuation
- whether divergence is being driven by trust collapse, lag, calibration drag, topology persistence, or local-vs-broad mismatch

without backend spelunking.

**Current status:** strong but not fully finished.

### 4. Restore / replay / continuation durability is trusted
Repeated save/load/continue loops must preserve:
- compare diagnostics
- compact summaries
- continuation delta classes
- divergence clues
- trust, failed-help, and calibration fields
- mixed-transition fields

across important long-horizon families.

**Current status:** strong but still needs broader matrix proof.

### 5. Release semantics are frozen
The repo must clearly say:
- what is complete
- what remains open
- what counts as enough proof for v1
- what is out of scope for v1

**Current status:** improved, but still needs final freeze.

---

## Current hard blockers for v1

### Blocker A — Wider district-family calibration matrix
Still needed:
- more cross-family calibration coverage
- better proof that realism holds across mixed topology and mixed support regimes
- broader pressure / recovery / reconnect / deterioration combinations

Why this blocks v1:
The sim looks convincing in many places, but not yet across enough of the matrix to claim the world is broadly calibrated.

### Blocker B — Broader 20+ tick soak and restore families
Still needed:
- more 20+ tick scenario matrices
- more restore-continue-restore proof across those matrices
- more bounded acceptance bundles across families

Why this blocks v1:
The compare/runtime contract is much stronger, but final trust comes from breadth, not just depth in a few families.

### Blocker C — Final operator-loop finishing pass
Still needed:
- tighter compare ergonomics inside existing surfaces
- clearer path-state distinctions across checkpoint, live, and restored continuation
- stronger compact surfacing of dominant divergence modes when many signals coexist

Why this blocks v1:
The backend truth is strong, but a full-sim product also needs a finished operator loop.

### Blocker D — Remaining thin spots in autonomy
Still needed:
- more resident-level repeated-failure adaptation where current architecture supports it
- stronger institution-side repeated-failure memory where grounded
- more believable cross-layer effects from actor memory into later city behavior

Why this blocks v1:
The sim feels increasingly alive, but not yet evenly enough to call the actor layer complete.

---

## What is enough for v1

Auralite does not need infinite scope before shipping v1.

The following should count as sufficient for a truthful v1:
- broad believable behavior across the main district-family matrix
- stable long-horizon comparison and restore behavior across representative scenario families
- strong operator compare and continuation usability in current canonical surfaces
- meaningful repeated-cycle actor memory with clear downstream effects
- explicit completion docs and frozen compare/continuation semantics

It does not need:
- infinite scenario generation
- perfect realism in every edge case
- a new intervention-quality ladder
- a separate reporting subsystem
- broad real-world claims outside the sim itself

---

## Non-goals for v1

Unless separately re-scoped, these should remain outside the v1 bar:

- infinite scenario breadth
- endless semantic expansion beyond the current bounded intervention-quality spine
- a separate reporting subsystem
- exhaustive proof across every imaginable district/intervention pairing
- perfect UI/UX for every hypothetical workflow

---

## Recommended remaining order

### Step 1 — Finish the calibration matrix
Prioritize:
- fragile core / resilient ring
- resilient pocket / weak corridor
- mixed-support corridor families
- trust-collapse / failed-help pockets inside recovering areas
- calibration-drag-heavy vs contained-recovery families

### Step 2 — Widen long-horizon acceptance and restore proof
Prioritize:
- broader 20+ tick matrices
- more repeated restore-loop coverage across those matrices
- bounded relationship assertions, not brittle exact snapshots

### Step 3 — Finish operator-loop clarity
Prioritize:
- clearer checkpoint/live/restored path interpretation
- better compact compare surfacing inside existing panels and surfaces
- stronger "why this stalled" readback for multi-driver paths

### Step 4 — Close the last thin autonomy gaps
Prioritize:
- resident-side repeated-failure adaptation
- institution-side repeated-failure / overload memory where grounded
- additional cross-layer consequence propagation from actor memory into city behavior

### Step 5 — Freeze semantics and declare v1 honestly
Prioritize:
- update completion gates to final truth state
- list closed vs open items explicitly
- state whether Auralite has crossed the v1 bar or what exact blockers remain

---

## v1 declaration checklist

Before declaring v1, the answer to each question below should be yes.

- Does the sim behave credibly across a broader district-family matrix, not just a few tuned scenarios?
- Do repeated actor-memory signals materially change later outcomes?
- Can operators understand divergence and continuation from canonical compare surfaces?
- Do restore / replay / continuation loops preserve the modern compare/runtime contract across representative long-horizon families?
- Are remaining blockers small enough to be edge-case work rather than major uncovered families?
- Are semantics and completion docs stable enough that the team can explain exactly what v1 is?

If any answer is still no, the sim is not yet a truthful full-sim v1.

---

## Final reading

Auralite is in the back half of the build and much closer to a real full sim than it was before the convergence work.

But the honest current state is still:

**not blocked by missing architecture,**
**blocked by remaining breadth, final operator polish, and final proof.**
