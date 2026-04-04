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

1. `docs/AURALITE_MASTER_BLUEPRINT.md`
2. `docs/CODEX_AURALITE_EXECUTION_PROMPT.md`
3. `docs/AURALITE_MILESTONE_01_BUILD_SPEC.md`
4. `docs/AURALITE_FILE_MAP_FOR_CODEX.md`
5. `docs/CODEX_AURALITE_DEEPWORK_SKILL.md`
6. `docs/CODEX_AURALITE_AUTOPILOT_SKILL.md`
7. `docs/CODEX_AURALITE_LONGRUN_SKILL.md`
8. `docs/AURALITE_90_DAY_EXECUTION_PROGRAM.md`

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
- prefer **one PR per major block cluster**, not one PR per tiny slice,
- do not open checkpoint PRs,
- do not open milestone PRs,
- and do not use PR creation as a progress marker.

Only create a PR when:
- a meaningful bundle of related work is complete,
- the branch is coherent enough to review,
- and there is a real review boundary.

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
8. Continue directly into the next block unless there is a real reason to stop.

---

## Good reasons to continue
Keep going automatically when:
- the next block is architecturally adjacent,
- the current work revealed an obvious next hardening step,
- there is no major product-direction fork,
- the source of truth is still clear,
- and the current branch remains coherent.

## Good reasons to stop
Stop only when:
- a true architecture uncertainty appears,
- a source-of-truth conflict makes safe progress unclear,
- a risky migration requires human review,
- the repo state becomes inconsistent enough that continuing would be irresponsible,
- or the user explicitly interrupts.

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
- do not write “final,” “done,” or “completed overall” unless the entire assigned long-run program has reached a true review boundary

---

## Recommended invocation
Use wording like this when starting a long run:

> Use `docs/CODEX_AURALITE_LONGRUN_SKILL.md` as your operating mode.
> Read all required files in the specified order.
> Then execute the next major blocks in the 90-day program on one long-lived branch.
> Use commits as checkpoints, do not create mini PRs, preserve world authority, reuse existing architecture, and continue automatically until you hit a true review boundary or I interrupt you.

---

## Short version
If you remember nothing else, remember this:

**Do not act like you are finishing one ticket. Act like you are executing a roadmap. Commit, continue, and only stop at real review boundaries.**