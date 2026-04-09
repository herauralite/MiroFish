# Codex Auralite Completion Enforcer

## Purpose

This file exists for one reason:

**prevent Codex from stopping early while Auralite is still materially incomplete.**

Use this as an override layer on top of:
- `docs/CODEX_AURALITE_FULL_SIM_EXECUTION_MANUAL.md`
- `docs/AURALITE_ENDGAME_ROADMAP.md`
- `docs/AURALITE_V1_READINESS.md`
- `docs/AURALITE_ENDGAME_COMPLETION_GATES.md`
- `docs/AURALITE_V1_ACCEPTANCE_MATRIX.md`

If anything in those files is interpreted in a weaker way than this file, this file wins.

---

## Hard override rule

If Codex’s own checkpoint says either of these:
- meaningful same-branch work is still feasible
- continuing is still responsible

then Codex must continue automatically.

Stopping after that is noncompliant.

If a checkpoint names specific feasible next work, that checkpoint is a mandatory continue signal, not an optional handoff note.

---

## PR rule override

A PR is not a stop signal.
A review boundary is not a stop signal.
A coherent diff is not a stop signal.
A passing test run is not a stop signal.

Codex may create a PR if useful for repo workflow, but PR creation does not permit ending the run.
Codex is not a PR producer; Codex is a finish-the-sim agent.

---

## Global stop conditions only

Codex may stop only if one of these is true:
1. Auralite has actually crossed the truthful full-sim v1 bar.
2. A real architecture blocker exists that cannot be responsibly resolved from repo evidence.
3. Further work would be speculative beyond the current architecture and docs.
4. Validation confidence would become too weak to continue responsibly.

If none of those four are true, Codex must continue.

---

## Phase progression rule

Finishing one slice inside a phase does not permit stopping.
Finishing one phase does not permit stopping.
Finishing one strong tranche does not permit stopping.

Codex must continue:
- from slice to slice inside a phase,
- then from phase to phase,
- until a valid global stop condition exists or the full-sim v1 bar is actually crossed.

---

## Readiness blocker rule

If any blocker in `docs/AURALITE_V1_READINESS.md` is still materially open and can still be addressed from current repo evidence, Codex must continue.

That includes:
- district-family calibration breadth still open
- broader 20+ tick soak / restore breadth still open
- final operator workflow polish still open
- remaining autonomy thin spots still open
- final semantic freeze / truthful v1 declaration still open

---

## Forbidden stopping phrases

Codex must not treat any of these as valid end conditions:
- "this is a good review boundary"
- "the branch is coherent"
- "the diff is large enough"
- "tests passed"
- "the next tranche can happen later"
- "same-branch work is feasible, but I am stopping here"

If any final summary implies those ideas, Codex has failed the run.

---

## Mandatory self-check before any stop

Before stopping, Codex must be able to truthfully say all of the following:

- I continued beyond the first neat slice.
- I continued beyond the first PR-shaped unit.
- I did not stop while later same-branch work was still feasible.
- I did not stop while continuing was still responsible.
- I did not stop while readiness blockers remained materially open unless a true global stop condition existed.
- I did not stop merely because I hit a review boundary, PR boundary, coherent diff boundary, or test-pass boundary.
- I am stopping only because the full-sim v1 bar is met or a real global stop condition exists.

If any sentence is false, Codex must continue.

---

## Plain instruction

Codex is not allowed to behave like a tranche generator.
Codex is not allowed to behave like a PR producer.
Codex must behave like a finish-the-sim agent.

Auralite is done only when the world, actors, interventions, operator loop, and proof are all sufficiently complete to satisfy the readiness doc, completion gates, and acceptance matrix.

Not before.
