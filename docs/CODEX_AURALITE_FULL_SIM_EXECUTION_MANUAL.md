# Codex Auralite Full-Sim Execution Manual

## Purpose

This document is the single execution manual Codex should follow from the **current merged repo state** to a **truthful full-sim v1**.

It is intentionally strict.
It exists to stop drift.
It should be treated as the operating manual for long-running implementation work.

Use this together with:
- `docs/AURALITE_ENDGAME_ROADMAP.md`
- `docs/AURALITE_ENDGAME_COMPLETION_GATES.md`
- `docs/AURALITE_V1_READINESS.md`
- `docs/AURALITE_V1_ACCEPTANCE_MATRIX.md`
- `docs/AURALITE_INTERVENTION_QUALITY_CANONICAL_MAP.md`

This manual does **not** replace those files.
It turns them into an execution system.

---

# 0. Core mission

Codex’s job is not to keep producing nice-looking PRs.
Codex’s job is to move Auralite from:

**credible sim core with strong long-horizon compare/readback support**

to:

**a fully built, believable, durable, operator-usable autonomous city sim with a truthful v1 completion bar.**

The sim is only done when all of the following are true:
- the world behaves credibly across a broad family matrix
- repeated actor memory materially changes later outcomes
- interventions have believable causal texture across long horizons
- operators can compare, checkpoint, restore, continue, and understand divergence without backend spelunking
- restore/replay/continue durability is trusted across representative hard families
- completion is proven through scenario packs and acceptance bundles, not just claimed in docs

---

# 1. Non-negotiable operating rules for Codex

## 1.1 Treat current repo state as the starting point
Do not re-plan already landed work as if it were missing.
The repo already has meaningful progress in:
- topology-aware district/city realism
- fragile-vs-durable recovery behavior
- spillover scar / containment memory
- household queue burden, queue scars, rebound reserve, relief-lag realism
- institution backlog/fatigue/recovery prerequisites with lag memory
- household trust/responsiveness/failed-help memory
- mixed-transition calibration diagnostics
- strong compare/checkpoint/continuation artifacts
- repeated restore→continue durability work
- readiness, gates, and acceptance-matrix docs

Codex must begin from this truth.

## 1.2 No drift into parallel systems
Do not create:
- a parallel reporting subsystem
- a second truth path for compare/readback
- a new intervention-quality ladder unless explicitly re-scoped
- a separate operator surface when an existing canonical surface can be improved

Always extend the existing canonical path first.

## 1.3 Prefer simulation depth over reporting adjectives
When choosing between:
- making the world more believable
- or making the wording more elegant

choose world realism.

## 1.4 Prefer broader proof over narrow wins
When choosing between:
- one more cute scenario
- or wider long-horizon acceptance coverage

choose wider proof.

## 1.5 Keep working until the band is actually closed
Do not stop because:
- the diff is coherent
- tests pass once
- the PR feels reviewable
- one slice looks mergeable

Stop only when the current band has no further high-value same-branch work that is responsible and well-supported by repo evidence.

## 1.6 Use bounded assertions, not brittle snapshots
Acceptance tests should increasingly prove:
- relationships
- bounded divergence
- persistence of state
- presence of compare/readback contracts

They should not overfit exact values unless exact values are part of a bounded deterministic contract already used by the repo.

## 1.7 Always preserve human honesty
Never claim the sim is complete if a blocker from the readiness doc is still materially open.

---

# 2. Definition of done

Codex may only treat Auralite as full-sim complete when all of these are true.

## 2.1 World realism breadth is closed
The sim behaves credibly across the main district-family matrix, not just a few tuned scenarios.

## 2.2 Repeated-cycle actor memory changes outcomes
Resident, household, and institution history is not just stored; it changes later behavior.

## 2.3 Operator loop is complete
Compare, checkpoint, continuation, restore, and path divergence inspection all feel like product features, not debug utilities.

## 2.4 Restore/replay/continue durability is trusted
Modern compare/runtime contracts survive repeated loops across representative hard scenario families.

## 2.5 Semantics and v1 docs are frozen
The repo clearly states:
- what is complete
- what remains open
- what is enough for v1
- what is explicitly out of scope

If any of those five are still materially open, Codex must not declare the sim done.

---

# 3. Master execution order

Codex should execute the remaining work in this order.

## Phase A — District-family calibration breadth
Goal:
Close the remaining realism breadth gap first.

Why first:
This is still the biggest blocker to calling the world broadly believable.

## Phase B — Long-horizon acceptance and restore breadth
Goal:
Broaden the proof so recent realism gains are trusted, not anecdotal.

Why second:
Breadth must be validated while the calibration families are fresh and easy to compare.

## Phase C — Operator compare / checkpoint / continuation completion
Goal:
Finish the product loop using the stronger compare semantics already landed.

Why third:
Once the harder realism families exist, Codex can improve operator clarity against real divergence cases instead of synthetic ones.

## Phase D — Resident / household / institution autonomy closure
Goal:
Close the last thin actor-memory gaps and strengthen cross-layer propagation.

Why fourth:
This work should build on the broader matrix and restore-proof harness so the actor layer is tuned against hard families, not isolated demos.

## Phase E — Freeze, gates, and v1 declaration
Goal:
Finish like a product and prove the bar has been met.

Why last:
Semantics should be frozen after the real remaining work is complete, not before.

---

# 4. Phase A — District-family calibration breadth

## Objective
Close the remaining realism families that still block “this is a broadly believable city sim.”

## Families Codex must cover
At minimum, Codex must land meaningful runtime behavior and proof for these calibration families:

### A1. Fragile core vs resilient ring
Required behavior:
- local core relief can appear before city headroom improves
- ring weakness can suppress broad recovery
- delayed deterioration can remain elevated after partial lift

Required compare/readback support:
- calibration drag or trust-collapse style divergence remains visible

### A2. Resilient pocket vs weak corridor
Required behavior:
- local durable recovery can exist while spread is blocked
- corridor reconnect gap remains meaningful

Required compare/readback support:
- topology/calibration drag is visible in compare artifacts

### A3. High-backlog / low-trust / overloaded-service family
Required behavior:
- nominal service gain is not enough when backlog/fatigue/failed-help remain high
- later conversion of relief is muted

Required compare/readback support:
- long-window compare state preserves lag/trust/failed-help signals

### A4. Local win / broad miss under mixed support
Required behavior:
- target district improves while city stays weak
- broad drag remains elevated despite local stabilization

Required compare/readback support:
- operator surfaces explain mismatch cleanly

### A5. Calibration-drag-heavy vs contained-recovery family
Required behavior:
- same nominal lift can produce either spread or stall depending on context

Required compare/readback support:
- delta class and divergence clues separate calibration drag from contained recovery

### A6. Repeated-failed-help-heavy pockets inside recovering areas
Required behavior:
- recovering districts can still carry embedded household/resident pockets that suppress broad stabilization
- those pockets worsen mixed-transition drag or delayed deterioration risk

Required compare/readback support:
- trust-collapse and failed-help burden remain visible in continuation deltas and summaries

## What Codex should implement in this phase

### Runtime work
- add or refine only the missing calibration signals required by the matrix
- prefer extending current city, district, household, resident, and institution state rather than inventing new top-level systems
- keep new fields bounded
- thread new fields into existing world metrics and local-vs-broad split logic where appropriate

### Validation work
- add long-horizon regression families for each new calibration family
- add bounded relationship assertions instead of snapshot overfitting
- add restore-loop proof for any new compare/runtime fields introduced here

### Documentation work
- update acceptance matrix only when a family is truly landed
- update completion gates only when the new family is genuinely closed

## Phase A exit rule
Do not leave Phase A until:
- at least **3+ calibration-family suites** from Matrix A are truly landed
- they are backed by runtime behavior, compare/readback support, and acceptance proof
- the remaining calibration gaps are visibly smaller and more edge-case-like than before

---

# 5. Phase B — Long-horizon acceptance and restore breadth

## Objective
Turn recent realism improvements into trusted proof.

## What Codex must expand

### B1. Long-horizon families
Every major remaining realism family should have a meaningful long-horizon test window.
Default target:
- 20+ ticks

Stretch target:
- 22–30 ticks where repo/runtime shape supports it responsibly

### B2. Restore-loop families
Codex must expand repeated:
- restore → continue → restore → continue

across the harder calibration and actor-memory families.

### B3. Contract durability proof
For the newer compare/runtime contract, Codex must prove survival of:
- compare diagnostics
- compact compare summaries
- compare checkpoint matrix
- continuation fingerprints
- continuation delta classes
- divergence clues
- trust / failed-help / calibration / mixed-transition deltas
- resident-memory deltas once landed

### B4. Multi-family acceptance bundles
Codex should add bundles that show believable relationships such as:
- trust-collapse-heavy path holds worse than sustained-recovery path
- calibration-drag-heavy path stalls more than contained-recovery path
- local-win/broad-miss path shows better local stabilization but worse city headroom
- repeated short relief builds less reserve than sustained relief

## How Codex should write these tests
- keep them deterministic where repo architecture already supports determinism
- assert on relative relationships, persistent classes, and contract presence
- avoid fragile exact values unless those are already core deterministic signals

## Phase B exit rule
Do not leave Phase B until:
- the repo has at least **2+ repeated restore-loop suites** from Matrix D
- harder calibration families are represented in long-horizon packs
- compare/readback contract durability is proven across those loops

---

# 6. Phase C — Operator compare / checkpoint / continuation completion

## Objective
Make the operator loop feel complete using the stronger compare spine already present.

## What Codex must finish

### C1. Path-state clarity
Operators must be able to distinguish:
- live state
- checkpoint snapshot
- restored continuation
- current continuation

without ambiguity.

### C2. Multi-driver readability
When divergence has several active causes, canonical compare surfaces must still make the dominant explanation understandable enough.

### C3. Local-vs-broad readability
The operator should be able to see when:
- local recovery is real
- but citywide drag still blocks broad improvement

### C4. Trust / lag / calibration mixed cases
The operator should be able to inspect paths where:
- trust collapse
- repeated failed-help burden
- recovery lag
- calibration drag
- topology persistence

coexist.

## Where Codex should improve
Use existing canonical surfaces only.
Good targets include:
- intervention history panel inputs
- comparison_report payloads
- checkpoint readback fields
- compact compare summary
- operator compare lines
- compare checkpoint matrix

Do **not** create a new dashboard or a parallel comparison subsystem just to avoid improving the existing one.

## Phase C exit rule
Do not leave Phase C until:
- operators can understand path divergence and continuation state from canonical surfaces alone
- at least **2+ operator-compare suites** from Matrix C are meaningfully covered
- mixed-driver readability is clearly better than current state

---

# 7. Phase D — Resident / household / institution autonomy closure

## Objective
Close the last actor-memory and autonomy gaps so the city feels more alive, not just better instrumented.

## What Codex must close

### D1. Resident-side repeated-failure adaptation
This is still a real remaining gap.
Residents should increasingly carry:
- trust toward help / systems
- responsiveness memory
- repeated-failure accumulation
- instability carry-over
- slower recovery despite nominal district improvement where appropriate

Codex should build on current resident adaptation state, not invent a second actor system.

### D2. Household repeated-cycle realism
Continue improving where still thin:
- interrupted relief consequences
- trust collapse persistence
- failed-help memory under partially improving districts
- household-to-district drag propagation

### D3. Institution-side repeated-failure memory
Where grounded by current architecture, deepen:
- overload memory
- relapse memory
- backlog recovery prerequisites
- service credibility/responsiveness effects on later outcomes

### D4. Cross-layer propagation
Actor memory should visibly change later:
- district stabilization capacity
- local-vs-broad pressure split
- intervention effectiveness
- delayed deterioration risk
- continuation divergence

## Phase D exit rule
Do not leave Phase D until:
- repeated actor-memory signals are clearly changing later outcomes
- remaining thin spots are minor rather than structural
- resident/household/institution behavior feels like long-memory participation in a living system

---

# 8. Phase E — Freeze, gates, and v1 declaration

## Objective
Finish the project honestly.

## What Codex must do

### E1. Freeze touched semantics
Lock down names and expectations for:
- compare artifact fields
- continuation fields
- divergence clues
- delta classes
- checkpoint/readback structures
- any new runtime/metric field introduced in Phases A–D

### E2. Tighten docs to final truth
Update only when true:
- `docs/AURALITE_ENDGAME_COMPLETION_GATES.md`
- `docs/AURALITE_V1_READINESS.md`
- `docs/AURALITE_V1_ACCEPTANCE_MATRIX.md`
- any release-grade architecture or operator docs needed to explain v1 clearly

### E3. Make the v1 call honestly
Codex must decide whether the bar is truly crossed.
If yes:
- say why, tied to the gates and matrix
If not:
- list the remaining blockers plainly and keep working

## Phase E exit rule
Stop only when:
- semantics are stable
- docs match reality
- completion gates are substantially closed
- remaining blockers are either empty or honestly declared

---

# 9. How Codex should structure each run

Every meaningful run should follow this structure.

## Step 1 — Re-read governing docs
Always start by reading:
1. `docs/AURALITE_ENDGAME_ROADMAP.md`
2. `docs/AURALITE_ENDGAME_COMPLETION_GATES.md`
3. `docs/AURALITE_V1_READINESS.md`
4. `docs/AURALITE_V1_ACCEPTANCE_MATRIX.md`
5. `docs/AURALITE_INTERVENTION_QUALITY_CANONICAL_MAP.md`

## Step 2 — Identify current band and remaining open families
Codex must explicitly state:
- which phase it is in
- which matrix families are still open
- what it is choosing to close now
- why that is the highest-value next work

## Step 3 — Implement same-branch until the slice is truly exhausted
Within the current band, Codex should keep extending the same branch until:
- the targeted family/set of families is actually covered
- the new fields are wired through canonical runtime and compare paths
- validation for those families is added
- no more high-value same-branch work remains within that slice

## Step 4 — Validate honestly
At minimum:
- run relevant backend tests
- run frontend build if touched
- add tests whenever runtime behavior deepens

Codex must report exactly what was validated.

## Step 5 — Reassess before stopping
Codex must answer:
1. What materially improved?
2. What blockers remain?
3. What same-branch work is still feasible right now?
4. Why is it responsible to continue or stop?

If more same-branch work is feasible, Codex must continue.

---

# 10. Mandatory anti-drift checklist

Before every stop point, Codex must confirm all of these.

- I did not reopen already-landed groundwork as if it were still missing.
- I improved canonical paths instead of adding a parallel system.
- I preferred believable world/actor behavior over more wording polish.
- I preferred broader proof over narrow local wins.
- I tied any docs updates to real landed work.
- I did not call the sim done while a readiness blocker remained materially open.

If any item fails, Codex must correct course before stopping.

---

# 11. Concrete remaining work map

This is the plain-English work queue Codex should follow from current state.

## Queue 1 — Calibration breadth
- finish fragile-core / resilient-ring proof
- finish resilient-pocket / weak-corridor proof
- finish mixed-support local-win / broad-miss proof
- finish calibration-drag-heavy vs contained-recovery proof
- finish repeated-failed-help pockets inside recovering regions

## Queue 2 — Long-horizon proof
- expand 20+ tick scenario families across those calibration cases
- add repeated restore-loop proof across those cases
- keep assertions bounded and relational

## Queue 3 — Operator completion
- improve checkpoint/live/restored continuation clarity
- improve mixed-driver divergence readability
- improve compact compare surfacing in existing canonical surfaces

## Queue 4 — Actor-memory closure
- deepen resident repeated-failure adaptation
- deepen institution repeated-failure/overload memory where grounded
- strengthen cross-layer consequence propagation from actor memory into city behavior

## Queue 5 — Freeze and release truth
- close remaining gate items honestly
- freeze semantics
- make the v1 call truthfully

---

# 12. What Codex must not do

Codex must not:
- keep writing prompts instead of code when code is feasible
- declare completion because the repo “feels close”
- over-index on one actor layer while leaving proof breadth behind
- introduce new architecture just to avoid extending the current one
- silently change semantics without updating tests/contracts/docs
- rely on package-shaped output instead of end-state-driven execution

---

# 13. Final stop condition

Codex may stop only when one of these is true:
- the full-sim v1 bar has actually been met
- a real architecture blocker exists that cannot be responsibly resolved from repo evidence
- further work would be speculative beyond the current architecture and docs
- validation confidence would become too weak to continue responsibly

These are **not** valid stopping reasons:
- “the branch is coherent”
- “the PR is large”
- “tests passed once”
- “this is enough for now”
- “the rest can happen later”

---

# 14. Plain instruction to Codex

From the current merged repo state:
- use the roadmap as the big-picture plan
- use the readiness doc as the truth source for what still blocks v1
- use the completion gates as the pass/fail bar
- use the acceptance matrix as the exact family/proof target
- work phase by phase in the order defined here
- keep extending the same branch until the current slice is truly exhausted
- prefer simulation realism, operator clarity, and long-horizon proof over elegant but shallow work
- do not stop until the sim is actually done or a real stop condition exists

Auralite reaches the finish line when the world, actors, interventions, operator loop, and proof all line up.
Not before.
