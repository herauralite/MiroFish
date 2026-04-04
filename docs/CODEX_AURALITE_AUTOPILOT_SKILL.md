# Codex Autopilot Skill — Auralite

Use this skill when the goal is for Codex to keep pushing Auralite forward in sustained deep-work mode with minimal interruption.

---

## Purpose
This skill is for **continuous, self-directed milestone execution** on Auralite.

It is intended for sessions where the user wants Codex to:
- keep moving milestone to milestone,
- inspect existing architecture before each step,
- look for bugs, weak spots, drift, and readability issues,
- propose and apply the next best improvements,
- and keep building toward the Auralite end-state without needing to stop after every small change.

This does **not** mean reckless rewriting.
It means **disciplined autonomous progress**.

---

## Required read order before doing any work
Always read these files in this exact order first:

1. `docs/AURALITE_MASTER_BLUEPRINT.md`
2. `docs/CODEX_AURALITE_EXECUTION_PROMPT.md`
3. `docs/AURALITE_MILESTONE_01_BUILD_SPEC.md`
4. `docs/AURALITE_FILE_MAP_FOR_CODEX.md`
5. `docs/CODEX_AURALITE_DEEPWORK_SKILL.md`
6. `docs/CODEX_AURALITE_AUTOPILOT_SKILL.md`

If the user also gives an in-chat milestone prompt, treat that as the immediate task overlay.

---

## Core operating rule
**The world is authoritative; agent cognition is contextual.**

That rule is never suspended.

Do not:
- move simulation truth into the frontend,
- fork alternate reporting truth paths,
- replace clean architecture with convenience hacks,
- or chase cosmetic progress over structural correctness.

---

## Autopilot mode behavior
When this skill is active, work in loops.

### Loop for each cycle
For each cycle of work:

1. **Re-anchor on the blueprint**
   - Reconfirm where the project currently is.
   - Identify the most important next slice that improves Auralite materially.
   - Prefer the next milestone in sequence unless a bug/fragility/readability issue blocks progress.

2. **Inspect before changing**
   - Check the current architecture around the relevant slice.
   - Look for:
     - bugs,
     - fragile wiring,
     - duplicated logic,
     - unclear operator/readback behavior,
     - drift from the world-authoritative model,
     - and places where a small fix unlocks better next progress.

3. **Choose the next best move**
   Prioritize in this order:
   - correctness bugs,
   - architecture drift,
   - fragile or duplicated logic,
   - operator/readability issues,
   - milestone-forward feature work,
   - polish only when it strengthens the slice.

4. **Implement one clean vertical slice**
   - Make the smallest meaningful set of changes that moves the project forward.
   - Reuse existing paths instead of spawning siblings.
   - Keep extension points clean.

5. **Self-review before stopping**
   - Check whether the change introduced duplication, drift, or unnecessary density.
   - Tighten it before reporting completion.

6. **Then continue**
   - After completing one slice, do not stop just because one PR-sized change exists.
   - Re-evaluate the next best step and continue working until you hit a natural milestone boundary, a clear uncertainty wall, or the user interrupts.

---

## What “keep working” means here
In autopilot mode, you should not stop after every minor improvement.
Instead:
- complete a meaningful slice,
- verify it,
- summarize what changed,
- identify the next best adjacent slice,
- and continue.

Good reasons to continue automatically:
- the next step is a direct extension of the current slice,
- the architecture path is already clear,
- a small cleanup is needed to make the current slice robust,
- a bug or fragility is obvious from the just-completed work,
- a nearby milestone can be reached cleanly without asking for clarification.

Good reasons to pause:
- a major product-direction fork appears,
- a decision affects core world architecture in multiple plausible ways,
- the repo lacks a critical source-of-truth file,
- or the user explicitly wants review before further progress.

---

## Continuous improvement rules
When looking for self-directed improvements, prefer these categories:

### 1. Bug fixes
Actively look for:
- mismatched response shapes,
- inconsistent artifact fields,
- stale fallbacks,
- ordering fragility,
- label-fragile matching,
- split-focus UI states,
- redundant history/session writes,
- and unclear selection or inspector behavior.

### 2. Architecture tightening
Improve when needed by:
- consolidating duplicated logic,
- making one canonical producer,
- reducing sibling artifacts with overlapping meaning,
- stabilizing deterministic ordering,
- and improving compatibility/backfill for older saved world shapes.

### 3. Operator usability
Improve scanability and clarity by:
- tightening hierarchy,
- reducing density,
- clarifying roles across surfaces,
- and making confidence/evidence/readback easier to trust.

### 4. Milestone progression
When the current layer is healthy enough, move to the next vertical slice that brings Auralite closer to:
- richer world simulation,
- institutions,
- interventions,
- history,
- explainability,
- spatial coherence,
- and operator tooling.

---

## Strict scope discipline
Even in autopilot mode, do **not**:
- launch unrelated refactors,
- build speculative systems not justified by the blueprint,
- create heavy dashboard sprawl,
- add predictive/recommendation engines unless explicitly requested,
- add exports/collaboration/accounts unless explicitly requested,
- or turn Auralite into a generic UI cleanup project.

Autopilot means **disciplined momentum**, not uncontrolled expansion.

---

## Surface role rules
When working on operator-facing surfaces, keep these roles distinct:

- **Map focus chip** = immediate action / current spatial focus
- **Scenario digest** = scenario-level readback
- **Scenario handoff** = resumption / continuity context
- **Resident inspector** = selected-entity and local coherence

Do not let all surfaces fully duplicate each other.
Unify wording, but preserve distinct roles.

---

## Canonical reuse rules
Prefer extending these existing paths:
- `operator_brief`
- `scenario_handoff`
- `scenario_outcome`
- `scenario_digest`
- `monitoring_watchlist`
- `stability_signals`
- `intervention_feedback_loop`
- `buildOperatorFocusReadback`
- `operatorFocusFormatting`
- shared spatial readback builders
- existing reporting/history sync paths

If a new concept fits one of these, extend the existing path first.

---

## Autopilot completion/reporting format
After each meaningful slice, report in this format:

### Summary
- what was implemented
- what bugs/fragilities/readability issues were improved
- how it fits the architecture

### Intentionally deferred
- what was left for later to avoid drift

### Testing
- commands run
- limitations or unavailable tooling

### Next best move
- state the next most logical slice
- then continue into it unless there is a good reason to pause

---

## Recommended invocation prompt
Use this when you want Codex to keep working forward with minimal interruption:

> Use `docs/CODEX_AURALITE_AUTOPILOT_SKILL.md` as your operating mode.
> Read all required files in the specified order.
> Then enter disciplined autopilot mode for Auralite.
> Keep working through the next best vertical slices, bug fixes, architecture tighten-ups, and readability improvements without stopping after each minor change.
> Re-anchor on the blueprint before each cycle, preserve world authority, reuse existing reporting/readback paths, avoid unrelated rewrites, and explicitly state what was deferred after each meaningful slice.
> Continue until you reach a natural milestone boundary, a true architecture uncertainty, or I interrupt you.

---

## Short version
If you remember nothing else, remember this:

**Keep your head down and build Auralite forward one real slice at a time. Fix fragility when you see it. Reuse the architecture that exists. Preserve world authority. Avoid drift. Continue until there is a real reason to stop.**
