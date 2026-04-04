# Codex Deepwork Skill — Auralite

Use this skill when working on Auralite inside this repository.

---

## Purpose
This skill is for **deep, milestone-by-milestone implementation work** on Auralite.

It is designed to keep Codex locked onto:
- the long-term Auralite architecture,
- the current milestone objective,
- the project’s world-authoritative design,
- disciplined vertical-slice delivery,
- and high-signal progress without wandering into unrelated cleanup.

This is not a generic coding prompt.
This is a **project operating mode** for sustained Auralite development.

---

## Required reading order before making changes
Always read these files in this exact order before you change code:

1. `docs/AURALITE_MASTER_BLUEPRINT.md`
2. `docs/CODEX_AURALITE_EXECUTION_PROMPT.md`
3. `docs/AURALITE_MILESTONE_01_BUILD_SPEC.md`
4. `docs/AURALITE_FILE_MAP_FOR_CODEX.md`
5. `docs/CODEX_AURALITE_DEEPWORK_SKILL.md`

If the user gave a milestone prompt in-chat, treat that as the **current task overlay** on top of these files.

---

## Non-negotiable architecture rule
**The world is authoritative; agent cognition is contextual.**

That means:
- backend/world state owns truth,
- frontend reads and renders backend-owned truth,
- reporting/explainability summarize backend state,
- spatial/operator surfaces are readers, not alternate simulation engines,
- and new features must preserve the separation between world, institutions, households, agents, interventions, history, and explainability.

Do not drift away from this.

---

## Deepwork mode behavior
When using this skill, work like this:

### 1. Re-anchor before changing anything
Before writing code, identify:
- what milestone or slice is being implemented,
- which existing Auralite layer it belongs to,
- what must remain authoritative,
- and what should explicitly **not** be built yet.

### 2. Prefer vertical slices over broad rewrites
Always choose the smallest meaningful slice that:
- improves the project materially,
- preserves long-term architecture,
- and leaves clean extension points for future milestones.

Do **not** do broad cleanup unless it directly supports the current slice.

### 3. Reuse existing reporting/readback paths
When possible, route new operator-facing behavior through existing paths such as:
- `operator_brief`
- `scenario_handoff`
- `scenario_outcome`
- `scenario_digest`
- `monitoring_watchlist`
- `stability_signals`
- `intervention_feedback_loop`
- `buildOperatorFocusReadback`
- `operatorFocusFormatting`
- existing spatial readback builders

Avoid creating sibling systems when the project already has a clear path.

### 4. Prefer canonical sources over duplicated logic
If multiple surfaces need the same answer:
- make one canonical producer,
- keep the frontend in read-only interpretation mode,
- and avoid near-duplicate reasoning in multiple components.

### 5. Keep the operator experience compact
Auralite should become richer, but not noisier.
When working on UI/operator surfaces:
- improve hierarchy,
- improve readability,
- improve explainability,
- reduce redundancy,
- and avoid dashboard sprawl.

### 6. Be explicit about deferrals
For every meaningful implementation, explicitly preserve scope discipline.
State what was intentionally deferred so the milestone does not drift.

---

## Default implementation priorities
Unless the user explicitly overrides them, optimize in this order:

1. **World-authoritative correctness**
2. **Architectural alignment with the blueprint**
3. **Operator readability / explainability**
4. **Spatial and inspection coherence**
5. **Compact UI polish**
6. **Minor cleanup only if it supports the slice**

---

## What to avoid
Do not:
- build UI-only truth paths,
- create speculative systems disconnected from the world model,
- turn the map into a heavy GIS product,
- add prediction/recommendation engines unless explicitly requested,
- drift into exports/collaboration/accounts unless explicitly requested,
- collapse Auralite into only a dashboard,
- or perform unrelated refactors just because you notice them.

Also avoid “fake progress” such as:
- cosmetic UI changes with no authoritative wiring,
- duplicate artifacts with overlapping meanings,
- or big architecture rewrites that reset momentum.

---

## Standard working pattern for each milestone
When implementing a milestone, follow this pattern:

### A. Identify the slice
Answer internally:
- What exact milestone/slice is this?
- Which files are likely canonical?
- Which existing layers should be extended instead of duplicated?

### B. Audit the existing path
Check how the current architecture already handles adjacent concepts.
Prefer extending:
- the existing artifact pipeline,
- the existing view wiring,
- the existing shared formatting/readback helpers,
- and the existing map/inspector/reporting structure.

### C. Implement the smallest correct extension
Build only the minimum correct set of changes needed to make the milestone real.

### D. Keep outputs merge-friendly
Favor:
- consistent naming,
- clear extension points,
- stable fallback behavior,
- deterministic ordering when ranking or prioritizing,
- and compatibility with older saved world shapes when applicable.

### E. Explain completion clearly
When done, report back with:
- what was implemented,
- how it fits the current architecture,
- what was intentionally deferred,
- and what was tested.

---

## Special rules for Auralite operator/readback work
When the milestone touches operator focus, scenario readback, handoff, or explainability:

### Canonical chain
Prefer this chain:
- backend reporting artifacts produce truth,
- shared frontend readback builders adapt that truth,
- formatting helpers keep wording consistent,
- surfaces render according to role.

### Surface roles
Keep roles distinct:
- **Map focus chip** = immediate action / current spatial focus
- **Scenario digest** = scenario-level readback
- **Scenario handoff** = resume / continuity context
- **Resident inspector** = local selected-entity coherence

Do not let all four surfaces say the exact same thing in slightly different wording.

### Focus signal rules
For focus work, keep answers compact around:
- current focus state,
- current priority,
- immediate next check,
- why it matters,
- confidence/stability/support,
- and concise evidence.

### Density rule
If a new focus line is added, consider whether another line should be shortened, merged, or removed.

---

## Special rules for map/spatial work
When working on map or spatial context:
- preserve backend/world truth,
- keep map overlays lightweight,
- prefer shared spatial readback builders,
- use the uploaded city layout reference when map fidelity is the target,
- and keep the map interactive rather than static.

Do not move simulation logic into the map.

---

## Expected Codex output format after implementation
After completing a deepwork slice, respond in this style:

### Summary
- concise list of what was implemented
- how it fits the architecture
- what was intentionally deferred

### Testing
- compile/build commands run
- any limitations or unavailable tooling

### Discipline check
- explicitly confirm whether the pass preserved:
  - world authority
  - shared readback consistency
  - vertical-slice scope discipline

---

## Recommended invocation prompt for this skill
Use wording like this when starting Codex on a new slice:

> Use `docs/CODEX_AURALITE_DEEPWORK_SKILL.md` as your operating mode for this task.
> Read the required files in the specified order.
> Then implement the requested milestone as a disciplined Auralite vertical slice.
> Preserve world authority, reuse existing reporting/readback paths, avoid unrelated rewrites, and explicitly state what was deferred.

---

## Short version
If you remember nothing else, remember this:

**Stay on the blueprint. Extend the existing architecture. Keep the world authoritative. Build one real vertical slice at a time. Avoid drift.**
