# Auralite Endgame Roadmap

## Purpose

This document defines the roadmap from the **current merged repo state** to a fully built Auralite simulation.

It is intentionally written for both humans and Codex. The goal is to prevent local package-by-package drift and keep future work aligned to the real end state: a believable, durable, inspectable, operator-usable autonomous city simulation rather than a collection of isolated reporting improvements.

This file has been refreshed to reflect the repo **after the recent convergence runs** that deepened topology realism, household/institution carry-over, intervention sequencing realism, continuation-aware comparison, and long-horizon validation.

---

## Where Auralite Is Right Now

Auralite is no longer best described as “mostly a smart reporting engine with a thin world.”

It now has a serious simulation backbone:
- long-horizon district and city calibration
- topology-aware drag/support behavior
- fragile-vs-durable recovery logic
- spillover scar and containment memory
- household queue burden and queue-scar carry-over
- continuation rollups and long-horizon divergence state
- intervention sequencing penalties and compare diagnostics
- restore/continue durability work and expanding regression coverage

### Current strengths

- Strong backend-owned reasoning / explainability / artifact architecture
- Bounded intervention-quality ladder and canonical intervention-quality map
- Canonical artifact flow for digest / brief / handoff / scenario outcome / compare surfaces
- World realism work now reaches district, household, institution, city, and regime layers
- Topology-aware district/city divergence and continuation behavior
- Household and institution carry-over state with queue scars, rebound reserve, asymmetry, and social memory
- Intervention sequencing realism with repetition fatigue, mistimed-stack penalties, and richer compare diagnostics
- Continuation-aware operator readback through canonical compare surfaces and history panel
- Restore/backfill durability for a growing set of runtime and comparison fields
- Deterministic regression coverage that is meaningfully broader than syntax / happy-path checks

### Current limitations

Auralite is still **not yet a full endgame sim**.

The largest remaining gaps are now concentrated in the following areas:
- resident/household/institution autonomy still needs to feel more alive under repeated cycles
- intervention families still need a broader, longer-horizon acceptance matrix
- operator compare / checkpoint / time-navigation workflows are better, but not yet fully complete
- restore/replay/continue proof is stronger, but not yet wide enough to call “fully trusted”
- some remaining completion gates are still open around long soak packs and broader family calibration

### Honest position on the build

Approximate maturity from current state:

- **Reasoning / explainability / review semantics:** ~90%
- **World realism / long-horizon city dynamics:** ~68%
- **Household / institution consequence depth:** ~64%
- **Intervention realism / comparison depth:** ~67%
- **Operator usability as a sim product:** ~60%
- **Durability / restore / acceptance proof:** ~64%
- **Full believable autonomous sim / endgame v1 overall:** ~65–70%

In plain language:
- the **brain** is strong
- the **world** is now credible in many places
- the **living city** is emerging
- the **full sim product loop** is not complete yet

---

## What “Fully Built Sim” Means

Auralite should only be considered endgame-complete when all of the following are true.

### 1. The world behaves credibly without constant handholding
The city should generate believable pressure, recovery, drift, reinforcement, overload, relapse, and breakdown patterns over long runs.

### 2. Agents feel meaningfully alive
Residents, households, services, districts, and institutions should act according to needs, incentives, memory, relationships, routines, constraints, and repeated consequence chains rather than behaving like loosely connected counters.

### 3. Interventions have legible, testable causal effects
Interventions should be able to help, fail, localize, diffuse, overload, backfire, fade, require reinforcement, and produce second-order consequences in ways that remain comparable across runs.

### 4. The reporting layer matches the actual world
The system must not merely produce elegant explanations. The explanations must consistently correspond to believable simulation dynamics.

### 5. The operator loop is complete
An operator should be able to:
- observe what is happening
- understand why it is happening
- compare runs and branches
- inspect intervention outcomes
- track long-run drift
- load checkpoints and compare continuation paths
- steer the sim without confusion

### 6. Long-run behavior is stable
The sim should survive long sessions, restores, resets, replay-like comparisons, and continuation loops without losing coherence.

### 7. Completion is demonstrated, not claimed
Auralite should pass scenario packs, long-run regression tests, calibration checks, compare/continuation acceptance criteria, and operator acceptance gates before being considered truly complete.

---

## What Is Already Landed

These areas should now be treated as **substantially advanced**, not as if they were still untouched:

### Interpretation / bounded review spine
- Intervention-quality ladder is bounded and canonically mapped
- Reporting artifacts are backend-owned and structurally coherent
- Historical pattern memory and backfill paths are much more durable than earlier repo states

### World realism already landed
- topology-aware district/city divergence
- clustered drag/support and persistence signals
- fragile-vs-durable recovery behavior
- spillover scar memory and containment capacity
- long-horizon divergence state and delayed deterioration clues

### Household / institution consequence depth already landed
- social tie usefulness/capacity/fatigue
- household asymmetry persistence
- institution queue burden
- institution queue scar memory and rebound reserve
- cross-tick continuation and carry-over state

### Intervention realism already landed
- intervention taxonomy foundations
- interaction trace support
- repetition fatigue penalties
- mistimed-stack penalties
- local-win/broad-miss and overload/backfire comparison signals
- comparison artifact sequence / continuation diagnostics

### Operator usability already landed
- canonical compare artifacts
- checkpoint readback
- operator compare lines
- continuation-aware scenario outcome signals
- intervention history panel now surfaces compare diagnostics without creating a parallel reporting system

### Durability / validation already landed
- repeated restore→continue coverage exists
- long-horizon deterministic regressions exist
- completion-gates documentation exists

The roadmap below should therefore focus on **closing the remaining gaps**, not re-describing already completed groundwork as if it still needs to be invented from scratch.

---

## Endgame Roadmap Overview (Refreshed)

From the current repo state to a fully built sim, the remaining work now breaks into six major bands:

1. **Complete the intervention acceptance matrix and long-horizon strategy comparison**
2. **Deepen household / institution / district consequence chains under repeated cycles**
3. **Complete operator compare / checkpoint / continuation workflows**
4. **Expand soak, restore, replay, and acceptance proof**
5. **Close the remaining world calibration matrix gaps**
6. **Freeze semantics, tighten completion gates, and define release-grade v1 readiness**

These bands are intentionally ordered around the **biggest remaining endgame gaps**, not the historical order the project started from.

---

# Band 1 — Complete the intervention acceptance matrix and long-horizon strategy comparison

## Goal
Turn current intervention realism into a broader, harder-to-fake comparison system.

## Why this matters
Auralite now has meaningful intervention sequencing realism, but it still needs a broader acceptance matrix before intervention behavior can be called endgame-ready.

## End-state for this band
Operators and tests can compare intervention families over long windows and see believable differences in:
- speed
- durability
- fatigue
- overload
- backfire risk
- local vs broad effects
- continuation drag

## Required work

### 1. Expand intervention family matrix
Build and validate families such as:
- no intervention
- delayed intervention
- immediate stack
- staggered stack
- repeated same lever
- alternating complementary levers
- short support burst
- sustained reinforcement
- partial rollout vs full rollout
- mistimed vs well-timed sequence

### 2. Expand acceptance-style comparisons
Add bounded relationship checks such as:
- alternating sequence reduces fatigue relative to repeated same-lever usage
- short burst can improve faster but hold worse than sustained reinforcement
- local-win/broad-miss cases remain visible under stronger city drag
- overloaded service-facing interventions increase later queue/fatigue pressure

### 3. Improve comparison contract completeness
Comparison artifacts should consistently expose:
- sequence diagnostics
- continuation-window diagnostics
- checkpoint-oriented readback
- operator compare lines
- strategy deltas that are useful in long-horizon path comparison

### 4. Expand intervention path sensitivity
Same lever families should diverge by:
- district archetype
- backlog / fatigue state
- household scar state
- support corridor weakness
- continuation pressure

## Exit criteria
- Intervention families are broad enough to meaningfully compare strategy paths
- Comparison outputs explain why paths diverged without backend spelunking
- Acceptance-style tests cover more than one or two hand-picked intervention scenarios

---

# Band 2 — Deepen household / institution / district consequence chains under repeated cycles

## Goal
Make the actor layer feel more alive under repeated relief, overload, relapse, and partial recovery.

## Why this matters
The sim is now credible at macro and meso levels, but it still needs stronger repeated-cycle realism at the household and institution layer.

## End-state for this band
Households and institutions carry state through repeated cycles in ways that materially affect later district and city behavior.

## Required work

### 1. Deepen queue-scar and rebound dynamics
Needed:
- repeated short relief should build less reserve than sustained relief
- queue scars should slow later household recovery more explicitly
- rebound reserve should be harder to build under repeated interrupted relief

### 2. Strengthen institution recovery prerequisites
Needed:
- backlog reduction should not instantly imply real service recovery
- overload fatigue should continue to mute service gains after nominal capacity increases
- recovery should require sustained lower burden windows rather than one good tick

### 3. Improve micro-to-macro propagation
Needed:
- household scars should affect district stabilization capacity more explicitly
- institutional fatigue should influence later intervention effectiveness more clearly
- repeated local service stress should accumulate into broader district drag in more believable ways

### 4. Deepen resident autonomy and carry-over
Resident-level behavior still needs more endgame depth around:
- routines and disruption adaptation
- trust / responsiveness to help
- repeated failure shaping future choices and vulnerability
- more meaningful need systems beyond generic strain

## Exit criteria
- Households and institutions behave like long-memory actors under repeated cycles
- Repeated relief/failure changes later system behavior in believable ways
- Micro-level consequence chains visibly shape district and city outcomes

---

# Band 3 — Complete operator compare / checkpoint / continuation workflows

## Goal
Make Auralite usable as a real operator-facing simulation product rather than a strong backend plus partial compare surfaces.

## Why this matters
The current compare/readback improvements are real, but the operator loop is still not complete.

## End-state for this band
An operator can run, inspect, compare, checkpoint, continue, and understand divergence over time without backend spelunking.

## Required work

### 1. Improve checkpoint workflows
Needed:
- clearer checkpoint-oriented comparison
- better distinction between baseline, branch, continuation window, and restored continuation
- more visible path-to-path divergence clues

### 2. Improve continuation usability
Needed:
- clearer surfacing of why a path is stalling
- better view of long-horizon drag vs local lift
- more visible distinction between local stabilization and broad recovery

### 3. Strengthen compare surfaces without UI sprawl
Use existing canonical surfaces to improve:
- intervention history comparisons
- scenario outcome compare flows
- checkpoint vs current run inspection
- long-run drift reasoning

### 4. Improve time-navigation ergonomics where repo supports it
If not yet complete, continue strengthening:
- pause / resume / step / skip flows
- compare-to-snapshot ergonomics
- continuation after restore / checkpoint load clarity

## Exit criteria
- Operators can compare and inspect path divergence confidently
- Checkpoint and continuation workflows feel like product features, not debug utilities
- Important divergence drivers are visible through canonical surfaces

---

# Band 4 — Expand soak, restore, replay, and acceptance proof

## Goal
Turn current realism gains into something closer to trusted endgame evidence.

## Why this matters
Auralite now has much better proof than before, but it still needs broader and longer-horizon validation to justify “full sim” claims.

## End-state for this band
The repo can prove believable behavior under longer runs, broader scenario families, and repeated restore/continue loops.

## Required work

### 1. Expand long-horizon scenario families
Needed:
- 12–20+ tick families across intervention and topology cases
- city-vs-local divergence families
- delayed deterioration families
- overload/backfire families
- fragile-recovery families

### 2. Expand repeated restore→continue loops
Needed:
- restore→continue→restore→continue on more scenario families
- proof that compare diagnostics and continuation signals survive repeated loops
- proof that newly added runtime fields do not drift or disappear

### 3. Add acceptance-style bundles
Tests should increasingly assert:
- bounded relationships
- persistent divergence classes
- continuation behavior stability
- compare artifact contract durability
rather than brittle exact values

### 4. Add broader calibration matrix coverage
The completion gates already note that a wider district-family calibration matrix remains open. That should now be treated as a first-class remaining gap.

## Exit criteria
- Long-horizon proof is broad enough that failure modes are unlikely to hide in untested path families
- Restore/continue durability is trusted across the newer compare/runtime surfaces
- Acceptance-style validation looks like a real endgame harness, not just a collection of narrow regressions

---

# Band 5 — Close the remaining world calibration matrix gaps

## Goal
Finish the remaining realism tuning that still blocks “full believable sim” confidence.

## Why this matters
The world is much more believable now, but some calibration breadth remains open.

## End-state for this band
The sim produces believable behavior across a wider matrix of district archetypes, topology shapes, intervention families, and repeated-cycle conditions.

## Required work

### 1. Expand district-family calibration matrix
Make sure the sim has believable bounded behavior across:
- fragile core / resilient outer ring
- resilient pocket / weak corridor
- broad strain / local relief
- partial reconnect / delayed deterioration
- high-backlog / low-trust / overloaded-service environments

### 2. Strengthen city-regime calibration under mixed conditions
Needed:
- better behavior under mixed-support corridors
- better separation between narrow wins and broad recovery
- better handling of long-lived mixed-transition states

### 3. Continue second-order effect refinement
Needed:
- more believable delayed consequences from backlog, fatigue, queue scars, and intervention overload
- stronger relation between institutional strain and later recovery opportunities

## Exit criteria
- The sim’s believable behavior generalizes across a wider calibration matrix
- Remaining realism failures are edge cases, not major uncovered families

---

# Band 6 — Freeze semantics, tighten completion gates, and define release-grade v1 readiness

## Goal
Finish the project like a product, not just a codebase.

## Why this matters
Auralite is now in the back half of the build. The remaining work should increasingly tighten completion rather than reopening architecture indefinitely.

## End-state for this band
Auralite has a declared v1 completion standard, stable semantics, and a release-grade quality bar.

## Required work

### 1. Freeze touched semantics
Lock down:
- intervention compare contract names
- continuation signal contract names
- checkpoint/readback surface expectations
- scenario-family acceptance expectations
- remaining intervention-quality semantics

### 2. Tighten completion-gate docs
The completion gates should evolve from “what was just added” into:
- what is complete
- what remains open
- what counts as enough proof for v1
- what still blocks calling the sim “full”

### 3. Add release-grade docs
Needed:
- architecture summary
- simulation model summary
- intervention model summary
- operator workflow summary
- testing/acceptance model summary
- known non-goals
- v1 completion definition

### 4. Declare remaining non-goals for v1
Examples:
- not a real-world predictor
- not a policy optimizer
- not an infinite semantics ladder
- not a fully open-ended generative world without bounded contracts

## Exit criteria
- There is a clear v1 completion document
- Touched semantics and compare contracts are stable
- The team can say what is complete, what is not, and what proof is still required

---

## Suggested Remaining Build Order

From the current repo state, the shortest path to endgame is now:

### Phase 1 — Finish intervention-family realism
- widen intervention family matrix
- add longer-horizon acceptance families
- deepen compare diagnostics where needed

### Phase 2 — Deepen repeated-cycle actor realism
- queue-scar and rebound behavior
- institution recovery prerequisites
- resident / household carry-over under repeated relief/failure

### Phase 3 — Finish operator compare / continuation loop
- checkpoint ergonomics
- compare usability
- long-run drift / continuation inspection

### Phase 4 — Prove hard
- 12–20+ tick scenario families
- restore→continue families
- acceptance bundles
- wider district-family calibration matrix

### Phase 5 — Freeze and ship toward v1
- tighten completion gates
- stabilize semantics
- finalize docs and remaining acceptance bar

---

## What “Endgame Complete” Should Look Like In Practice

Auralite should feel complete when a user can do the following in one coherent workflow:

1. Run the simulation forward
2. Watch districts, households, institutions, and systems change in believable ways
3. Apply different intervention strategies and observe local + downstream effects
4. See the system distinguish between local success, broad success, fragile success, overload, backfire, delayed deterioration, and unresolved results
5. Inspect clear operator-facing evidence for why the system judged the path the way it did
6. Compare current behavior to alternate intervention families, historical patterns, and checkpoints
7. Save, restore, continue, and compare without state corruption or semantic drift
8. Trust that the reporting layer is describing a world that actually behaves with depth

If those eight things all work together consistently, Auralite is near the finish line.

---

## Practical Definition of “Done Enough for v1”

Auralite can be considered v1-complete when all of the following are true:

- The intervention-quality ladder is stable and no longer drifting
- The world dynamics feel believable over long runs
- Household and institution behavior produces meaningful repeated-cycle emergence
- Interventions have realistic causal texture, tradeoffs, and comparison value
- Operator workflows are end-to-end usable for compare / checkpoint / continuation
- Persistence and continuation state are durable under repeated loops
- Tests prove regression resistance across scenario families, restores, and acceptance bundles
- Documentation clearly explains architecture, limits, and completion criteria

If any one of those is still missing in a serious way, the sim is not endgame-complete yet.

---

## Anti-Drift Rules For Future Work

Future packages should not drift away from endgame completion. Use these rules:

1. Do not add new intervention-quality lanes casually.
2. Prefer broader believable world/actor behavior over more reporting adjectives.
3. Prefer acceptance families and restore-proof validation over narrow one-off regressions.
4. Prefer operator clarity over new parallel surfaces.
5. Prefer bounded compare truth over elegant but weak summaries.
6. Every major package should answer: does this move the sim closer to a believable living world and a complete operator workflow?

---

## Recommended Immediate Next Focus From Current State

From the current repo state, the highest-value next moves are:

1. **Expand the intervention acceptance matrix over 12–20+ tick families**
2. **Deepen repeated-cycle household/institution consequence realism under intervention paths**
3. **Strengthen operator compare/checkpoint/continuation workflows using existing canonical surfaces**
4. **Widen repeated restore→continue proof across intervention families and compare artifacts**
5. **Close the wider district-family calibration matrix and then tighten v1 completion gates**

That is now the shortest path from “credible sim core with strong compare/readback” to “fully built endgame sim.”

---

## Final Principle

Auralite does not reach the endgame by sounding smarter.
It reaches the endgame when:
- the world behaves more believably over long horizons,
- households and institutions carry real consequence chains,
- intervention strategies diverge in realistic and inspectable ways,
- operators can compare and continue runs with confidence,
- and the system can prove those claims through acceptance-style validation.
