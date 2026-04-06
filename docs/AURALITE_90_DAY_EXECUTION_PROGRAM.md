# Auralite 90-Day Execution Program

This document gives Codex a long-horizon execution queue for Auralite.

Use it together with:
- `docs/CODEX_AURALITE_LONGRUN_SKILL.md`
- `docs/CODEX_AURALITE_AUTOPILOT_SKILL.md`
- the blueprint and file map

---

## Intent
The purpose of this program is to let Codex keep working for long stretches on Auralite without needing a new tiny milestone prompt every few minutes.

This is a **roadmap execution document**, not a strict chronological guarantee.
Codex should still inspect the repo and use judgment, but should stay inside these lanes unless the user redirects the project.

---

## Global success condition
By the end of this execution program, Auralite should be materially stronger in all of these ways:
- more stable world/readback architecture,
- more believable city simulation,
- stronger institution and intervention consequence chains,
- more durable persistence/runtime behavior,
- and more coherent operator tooling.

---

## Rules for using this program
When executing this program:
- prefer major block completion over tiny milestone completion,
- use commits as checkpoints,
- avoid mini PRs,
- preserve world authority,
- preserve canonical readback/reporting paths,
- and only stop at real review boundaries.

If a block reveals a necessary lower-level hardening task, do it before continuing.

---

# EXECUTION BLOCKS

## BLOCK 1 — selection-state and readback stability
### Goal
Make selection, focus, and readback state deterministic and resilient.

### Focus
- stale selected IDs after refresh/load/tick/reset
- resident ↔ district selection precedence
- resident ↔ household ↔ institution context joins
- nullability and partial-world handling
- artifact fallback precedence
- selected-entity coherence under evolving world state

### Good outcomes
- fewer split-focus states
- fewer stale-context states
- clearer precedence and resolver logic
- less duplicated fallback code

### Stop condition
This block is done when selection/readback behavior is predictably stable and obvious weak fallback chains are removed.

---

## BLOCK 2 — spatial/readback architecture tightening
### Goal
Make the spatial/readback layer easier to extend without drift.

### Focus
- `buildSpatialReadback`
- `buildResidentSpatialReadback`
- `buildHouseholdSpatialReadback`
- `buildInstitutionSpatialReadback`
- `buildOperatorFocusReadback`
- resolver reuse
- context assembly boundaries
- canonical producers vs duplicated join logic

### Good outcomes
- cleaner architecture boundaries
- less repeated context assembly
- more explicit precedence rules
- lower drift risk for future UI and simulation features

### Stop condition
This block is done when the readback architecture is materially cleaner and safer to build on.

---

## BLOCK 3 — runtime realism pass 1
### Goal
Increase the sense that the city is alive through backend consequence logic.

### Focus
- resident routine consequences
- household pressure consequences
- district pressure evolution
- service access influence
- institution influence on local conditions
- social propagation spillover
- bounded causal effects that preserve explainability

### Good outcomes
- districts evolve more believably
- residents and households feel more connected to local pressures
- institutions matter more as causal actors
- metrics shift in ways that feel meaningful, not arbitrary
- topology shocks leave temporary **spillover scar memory** that does not disappear immediately after one improving tick
- district recovery now reflects both neighborhood containment weakness and explicit **containment capacity** recovery, which enables uneven local rebound while preserving broad-city drag realism

### Stop condition
This block is done when simulation changes produce more believable downstream effects without uncontrolled system sprawl.

---

## BLOCK 4 — institution consequence deepening
### Goal
Make institutions more materially important to the simulation.

### Focus
- institution stress/capacity logic
- effects on district conditions
- effects on resident outcomes
- effects on household pressure
- effects on service access
- institution explainability through current reporting paths

### Good outcomes
- institutions feel like active world actors
- institution state matters to real outcomes
- operator surfaces reflect real institution consequences

### Stop condition
This block is done when institutions exert stronger causal influence without requiring a giant new subsystem.

---

## BLOCK 5 — intervention aftermath and medium-term consequence depth
### Goal
Make interventions feel more real over time.

### Focus
- persistence / fade / reversal logic
- downstream effects on districts, households, residents, institutions
- aftermath signals in backend-owned artifacts
- stronger consequence linkage through current reporting architecture

### Good outcomes
- interventions have believable medium-term effects
- aftermath signals are grounded in actual world changes
- consequence reporting becomes more trustworthy

### Stop condition
This block is done when intervention effects feel more materially connected to later state.

---

## BLOCK 6 — persistence / compatibility / runtime hardening
### Goal
Make longer-running Auralite sessions less brittle.

### Focus
- save/load/reset/runtime control
- recomputation after restore/reset/intervention
- reporting_state / scenario_state sync assumptions
- compatibility and backfill paths for older worlds
- stale mirrored state where safe to reduce

### Good outcomes
- safer transitions
- less brittle world-shape evolution
- fewer stale derived-state issues after load/reset

### Stop condition
This block is done when persistence/runtime behavior is materially more trustworthy.

---

## BLOCK 7 — operator tooling stabilization after system work
### Goal
After system changes land, make sure operator surfaces still reflect truth cleanly.

### Focus
- operator family scan rhythm after backend/runtime changes
- artifact precedence safety
- coherence of map chip / digest / handoff / inspectors
- low-risk readability fixes only where system work introduced roughness

### Good outcomes
- UI remains coherent after deeper system changes
- no drift between backend-owned truth and frontend readback surfaces

### Stop condition
This block is done when operator tooling remains stable after the deeper system work.

---

## BLOCK 8 — explainability/reporting strengthening
### Goal
Strengthen the usefulness of reporting artifacts without replacing current architecture.

### Focus
- scenario_outcome clarity
- scenario_insight_report usefulness
- operator_brief quality
- handoff and continuity usefulness
- district/resident/household story-thread usefulness
- artifact coherence and non-duplication

### Good outcomes
- better backend-owned summaries
- less overlapping artifact meaning
- better operator trust in readback surfaces

### Stop condition
This block is done when reporting feels stronger without spawning a parallel report framework.

---

## BLOCK 9 — realism pass 2
### Goal
Deepen the living-world feel after the architecture is stronger.

### Focus
- stronger routine diversity
- stronger service scarcity / access effects
- stronger district differentiation over time
- stronger social/support/strain consequence chains
- more believable institution-mediated outcomes

### Good outcomes
- the city feels more like a true simulation and less like a dashboard over a toy state machine

### Stop condition
This block is done when runtime behavior feels meaningfully richer than the initial world shell.

---

## BLOCK 10 — integrated cleanup and review boundary
### Goal
Prepare a coherent major review boundary after substantial progress.

### Focus
- remove obvious roughness introduced by previous blocks
- tighten naming and helper boundaries
- reduce drift and duplication that accumulated during long-run work
- fix only meaningful rough edges
- avoid endless polish

### Good outcomes
- the branch is reviewable as a strong evolution step
- architecture remains coherent
- the project is materially better, not just differently worded

### Stop condition
This block is done when the current branch is ready for a major review boundary.

---

# EXECUTION GUIDELINES

## How to choose the next sub-slice
Inside a block, always prefer:
1. correctness bug
2. fragile logic hardening
3. canonical architecture tightening
4. meaningful simulation consequence improvement
5. operator/readability cleanup only where needed

## How big a sub-slice should be
A good sub-slice:
- materially improves the block,
- preserves architecture,
- is small enough to verify honestly,
- and leaves clean extension points.

## What not to do
Do not:
- create mini PRs after tiny progress,
- invent speculative systems outside the blueprint,
- do broad unrelated rewrites,
- move truth into the frontend,
- build a heavy analytics/dashboard sprawl,
- or loop forever on wording polish after the operator family is already stable enough.

---

# CHECKPOINT STYLE

After each major block, record:
- what was implemented,
- what bugs/fragilities were improved,
- what was intentionally deferred,
- what was tested,
- and what the next block is.

Then continue automatically unless a true blocker appears.

---

# SHORT VERSION

If you remember nothing else, remember this:

**Use this document as the long queue. Finish real blocks, not tiny tickets. Keep the world authoritative. Strengthen the simulation, not just the wording. Stop only at real review boundaries.**
