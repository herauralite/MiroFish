# Auralite v1 Acceptance Matrix

## Purpose

This document turns the remaining endgame blockers into a concrete acceptance matrix.

Use it with:
- `docs/AURALITE_ENDGAME_ROADMAP.md`
- `docs/AURALITE_ENDGAME_COMPLETION_GATES.md`
- `docs/AURALITE_V1_READINESS.md`

This file is intentionally narrow:
- which scenario families still need broader proof
- what bounded relationships each family should prove
- what restore / checkpoint / continuation contracts must survive
- what should count as enough evidence for v1

It is not a backlog dump.

---

## Current use

Auralite already has meaningful long-horizon proof across multiple 18–24 tick families.

As of the v1 hardening pass, matrix breadth coverage is no longer a blocker.

This matrix remains the canonical contract for what breadth was required before crossing the v1 bar and for guarding post-v1 regression risk.

---

# Matrix A — District-family calibration breadth

These families are still the biggest realism blocker.

## A1. Fragile core vs resilient ring
Goal:
- prove that local gains in a fragile center do not automatically become broad recovery when surrounding ring support is uneven

Required assertions:
- mixed-transition drag remains bounded but visible
- local recovery may appear before city headroom improves
- delayed deterioration risk can remain elevated even after partial local lift
- compare artifacts surface calibration drag or trust-collapse style divergence when appropriate

## A2. Resilient pocket vs weak corridor
Goal:
- prove that a durable recovery pocket can exist while corridor weakness still blocks spread

Required assertions:
- corridor reconnect gap remains visible when broad lift lags local stabilization
- topology or calibration drag stays inspectable in canonical compare surfaces
- restore loops preserve the corridor/mixed-transition fields

## A3. High-backlog / low-trust / overloaded-service family
Goal:
- prove that nominal service gain is not enough when backlog, failed-help memory, and trust collapse remain high

Required assertions:
- repeated failed-help or trust-collapse fields worsen later conversion of relief
- institution lag / backlog pressure remains visible in long-window compare state
- compact compare summaries preserve these deltas across restore loops

## A4. Local win / broad miss under mixed support
Goal:
- prove that a path can improve a target district while still missing citywide recovery

Required assertions:
- local_recovery_share may rise while citywide_durability_headroom stays weak
- broad_durability_drag or neighborhood_regime_drag remains elevated
- operator compare surfaces explain the mismatch cleanly

## A5. Calibration-drag-heavy vs contained-recovery family
Goal:
- distinguish families where the same nominal intervention lift results in either durable spread or stalled recovery

Required assertions:
- continuation delta class / divergence clues differentiate calibration drag from contained recovery
- checkpoint/live comparisons preserve those differences
- 20+ tick windows remain stable under restore→continue loops

---

# Matrix B — Repeated-cycle actor realism

## B1. Repeated short relief vs sustained relief
Goal:
- prove that sustained relief builds stronger reserve while repeated short relief builds more lag, debt, and interruption burden

Required assertions:
- rebound reserve differs across families
- nominal_relief_lag and relief_interruption_count remain meaningfully different
- later household and city metrics diverge because of those histories

## B2. Repeated failed-help pockets inside otherwise improving districts
Goal:
- prove that repeated failed-help households remain a drag even when district-level conditions improve

Required assertions:
- assistance_failure_streak and trust_collapse share remain visible
- mixed-transition drag or delayed deterioration risk can stay elevated because of those pockets
- compare artifacts preserve the failed-help and trust deltas across restore loops

## B3. Household trust collapse vs sustained recovery family
Goal:
- prove that trust-collapse paths remain behaviorally distinct from sustained-recovery paths over 20+ ticks

Required assertions:
- trust/responsiveness deltas remain separated
- compact compare summaries preserve the difference
- divergence driver selection stays truthful when trust collapse dominates

## B4. Institution lag-memory family
Goal:
- prove that backlog relapse and recovery lag continue to suppress downstream recovery after nominal service improvement

Required assertions:
- institution_recovery_lag_index remains inspectable
- household recovery can still lag after service access nominally improves
- restore loops preserve the lag-memory compare state

---

# Matrix C — Operator compare / checkpoint / continuation usability

## C1. Snapshot vs live vs restored continuation pairing
Goal:
- prove that operators can distinguish path kinds without backend spelunking

Required assertions:
- compare_checkpoint_matrix keeps state kinds and path kinds intact
- compact compare summary remains readable in restore-loop families
- divergence clues remain stable enough to be useful after repeated loops

## C2. Multi-driver divergence family
Goal:
- prove that when many signals coexist, canonical compare still surfaces the dominant explanation clearly enough

Required assertions:
- divergence_driver stays bounded and interpretable
- compact compare summary plus clues remain sufficient for quick readback
- operator-facing readback does not require a parallel surface

## C3. Local-vs-broad + trust + calibration mixed family
Goal:
- prove that the compare layer remains readable when local-win/broad-miss, trust collapse, lag, and calibration drag coexist

Required assertions:
- driver and clue surfacing remain coherent
- no key fields disappear across restore loops
- pair-kind / checkpoint/live interpretation still holds

---

# Matrix D — Restore / replay / continuation durability

## D1. Repeated restore→continue→restore→continue across calibration families
Goal:
- prove that modern compare/runtime contracts survive repeated persistence cycles across the harder calibration families

Required assertions:
- continuation fingerprints persist
- compact compare summary persists
- compare checkpoint matrix persists
- trust / failed-help / calibration / mixed-transition deltas persist

## D2. Repeated restore loops across actor-memory families
Goal:
- prove that repeated-cycle actor history remains meaningful after multiple restores

Required assertions:
- household memory fields do not reset unexpectedly
- city aggregates still reflect those histories
- compare artifacts still show those differences after continuation

---

# Minimum breadth target for v1

Before declaring v1, the repo should have at least:

- **3+ calibration-family suites** from Matrix A
- **3+ actor-memory suites** from Matrix B
- **2+ operator-compare suites** from Matrix C
- **2+ repeated restore-loop suites** from Matrix D

Each suite should use bounded assertions, not brittle exact snapshots.

---

# What counts as a passing family

A family counts as complete when all of the following are true:

1. The family runs for a meaningful long horizon, normally 20+ ticks.
2. The family proves a believable relationship, not a hand-picked exact value.
3. The relevant compare/checkpoint/continuation contracts remain present.
4. The same family still behaves coherently after restore→continue cycles if persistence is in scope.
5. The family adds breadth rather than duplicating a family already covered.

---

# Post-v1 maintenance order (no scope expansion)

1. Keep Matrix A/B/C/D suites green as frozen contract coverage.
2. Add only bounded regression assertions when a concrete v1 contract risk appears.
3. Preserve compare/checkpoint/continuation shape compatibility in persistence loops.
4. Update readiness/completion docs only when reflecting already-landed truth.
5. Treat broader family expansion as post-v1 roadmap work, not v1-gate work.

---

# Final rule

Auralite reaches v1 not when one more branch looks polished,
but when enough of this matrix is closed that the remaining gaps are edge cases rather than whole missing families.
