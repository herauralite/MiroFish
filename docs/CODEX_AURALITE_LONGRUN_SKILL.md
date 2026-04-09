# Codex Long-Run Skill — Auralite

Use this skill when the goal is for Codex to work for long uninterrupted stretches on Auralite without stopping after each small slice.

---

## Purpose
This skill is for **extended execution mode** on Auralite.

It is intended for runs where Codex should:
- keep working across multiple major blocks,
- avoid stopping after every useful local improvement,
- avoid creating a PR after every small milestone,
- continue from block to block with commit-based checkpoints,
- and operate more like a lead engineer executing a roadmap than a ticket-based assistant waiting for approval.

This is not reckless autonomy.
This is **disciplined long-horizon execution**.

---

## Required read order
Before doing work in long-run mode, always read these files in this exact order:

1. `docs/CODEX_AURALITE_COMPLETION_ENFORCER.md`
2. `docs/CODEX_AURALITE_FULL_SIM_EXECUTION_MANUAL.md`
3. `docs/CODEX_AURALITE_LONGRUN_SKILL.md`
4. `docs/AURALITE_ENDGAME_ROADMAP.md`
5. `docs/AURALITE_V1_READINESS.md`
6. `docs/AURALITE_ENDGAME_COMPLETION_GATES.md`
7. `docs/AURALITE_V1_ACCEPTANCE_MATRIX.md`
8. `docs/AURALITE_INTERVENTION_QUALITY_CANONICAL_MAP.md`

If the user gives an in-chat overlay, treat it as a local override on top of these files.

---

## Core rule
**The world is authoritative; agent cognition is contextual.**

Never violate this.

Do not:
- move truth into the frontend,
- fork reporting truth into parallel UI-owned logic,
- replace architecture with convenience hacks,
- or chase cosmetic progress over structural correctness.

---

## Long-run mode behavior
When this skill is active, do not operate in tiny-ticket mode.

### You must:
- work on one long-lived branch,
- use commits as checkpoints,
- continue automatically from one major block into the next,
- avoid interpreting progress summaries as stop signals,
- and avoid creating a PR every time one useful slice is complete.

### You must not:
- stop after one small milestone,
- create a PR after one small milestone,
- ask for approval after each useful change,
- or treat a block summary as the end of the assignment.

---

## PR discipline
In long-run mode:
- PRs are optional workflow artifacts,
- do not open checkpoint PRs,
- do not open milestone PRs,
- and do not use PR creation as a progress marker.

If a PR is created, execution still continues as long as same-branch work remains feasible and responsible.
PR timing, review boundaries, branch coherence, and diff size are not stop signals.

If the user explicitly says “do not create a PR until X blocks are done,” obey that strictly.

---

## How to keep working
For each major block:

1. Re-anchor on the blueprint.
2. Inspect the relevant architecture before making changes.
3. Identify the next best sub-slice.
4. Make the smallest meaningful change that materially improves the block.
5. Self-review for drift, duplication, density, fragile fallbacks, and helper sprawl.
6. Commit.
7. Continue directly into the next sub-slice.
8. Continue directly into the next block.
9. Continue from phase to phase until full-sim completion or a true global stop condition.

---

## Good reasons to continue
Keep going automatically when:
- the next block is architecturally adjacent,
- the current work revealed an obvious next hardening step,
- there is no major product-direction fork,
- the source of truth is still clear,
- the current branch remains coherent,
- same-branch work is still feasible,
- and continuing is still responsible.

## Good reasons to stop
Stop only when:
- the full-sim v1 bar is actually met (readiness + completion gates + acceptance matrix satisfied),
- a real architecture blocker exists that cannot be responsibly resolved from repo evidence,
- further work would be speculative beyond current repo architecture/docs evidence,
- validation confidence is too weak to continue responsibly,
- or the user explicitly interrupts.

If none of these are true, stopping is noncompliant.

---

## Priority order in long-run mode
Unless the user overrides it, optimize in this order:

1. correctness bugs
2. architecture drift
3. fragile or duplicated logic
4. runtime/persistence robustness
5. simulation realism and causal depth
6. institution/intervention consequence depth
7. operator/readability issues
8. milestone-forward feature work
9. polish only when it strengthens the active block

---

## Auralite-specific long-run focus
In long-run mode, prefer advancing work across these lanes:
- selection-state and readback stability
- spatial/readback architecture tightening
- runtime realism and bounded consequence logic
- institution consequence depth
- intervention aftermath and medium-term effects
- persistence/reset/load/runtime hardening
- integrated cleanup after major system work

Do not get trapped endlessly polishing one UI lane once it is already stable enough.

---

## Scope discipline
Even in long-run mode, do **not**:
- launch unrelated refactors,
- invent speculative systems disconnected from the blueprint,
- build dashboard sprawl,
- introduce recommendation/prediction engines unless explicitly requested,
- introduce export/collaboration/account systems unless explicitly requested,
- or turn Auralite into a pure polish treadmill.

Long-run mode means **sustained meaningful progress**, not uncontrolled expansion.

---

## Reporting format for checkpoints
After each major block, report:

### Block summary
- what was implemented
- how it fits the architecture

### Bugs / fragilities improved
- what fragile behavior or duplication was reduced

### Intentionally deferred
- what was left for later to avoid drift

### Testing
- what was actually run
- what was unavailable

### Next block
- what comes next
- then continue automatically unless a real blocker exists

Important:
- checkpoint summaries are **progress logs only**
- they are **not** stop signals
- any checkpoint that names feasible next work requires automatic continuation
- do not write “final,” “done,” or “completed overall” unless full-sim completion is actually reached or a true global stop condition is explicitly documented

---

## Recommended invocation
Use wording like this when starting a long run:

> Use `docs/CODEX_AURALITE_LONGRUN_SKILL.md` as your operating mode.
> Read all required files in the specified order.
> Then execute phase-by-phase on one long-lived branch.
> Use commits as checkpoints, do not create mini PRs, preserve world authority, reuse existing architecture, and continue automatically while same-branch work remains feasible and responsible.
> Stop only for true global stop conditions or explicit user interruption.

---

## Short version
If you remember nothing else, remember this:

**Do not act like you are finishing one ticket. Act like you are executing a roadmap. Commit, continue, and stop only at true global stop conditions.**
