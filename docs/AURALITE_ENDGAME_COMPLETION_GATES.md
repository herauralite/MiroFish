# Auralite Endgame Completion Gates (Convergence Update)

This document tightens the endgame definition from `docs/AURALITE_ENDGAME_ROADMAP.md` into concrete acceptance gates.

Pair this with:
- `docs/AURALITE_ENDGAME_ROADMAP.md`
- `docs/AURALITE_V1_READINESS.md`

## Why this exists
- Prevent “reviewable branch” from being confused with “endgame complete.”
- Tie intervention realism, long-horizon behavior, operator compare usability, and restore durability to explicit proof.
- Keep a strict record of what is landed versus what still blocks a truthful v1 declaration.

## Gate Set

### Gate 1 — Intervention family realism
Required evidence:
- No-intervention vs delayed vs immediate-stack vs repeated-same-lever vs alternating-complementary scenario families.
- Sequence A vs Sequence B comparison output must include fatigue/timing/continuation diagnostics.
- At least one local-win/broad-miss case and one overload/backfire case with bounded assertions.

Pass condition:
- Comparison artifacts expose strategy diagnostics and checkpoint readback fields, and tests validate divergence relationships.

### Gate 2 — Long-horizon acceptance packs
Required evidence:
- 10–20+ tick scenario families run in regression tests.
- Assertions are bounded (relationships/signals), not brittle exact values.
- City-vs-local divergence remains observable under long windows.

Pass condition:
- Endgame regression suite includes multi-family long-window tests with stable bounded checks.

### Gate 3 — Operator compare/checkpoint usability
Required evidence:
- Compare artifacts surface compact “why paths diverged” clues:
  - sequence fatigue
  - timing mismatch
  - continuation drag
  - trust collapse / repeated failed-help burden
  - calibration drag / mixed-transition drag where relevant
- Surfaces show checkpoint-oriented continuation clues without new parallel reporting architecture.

Pass condition:
- Operators can inspect divergence drivers from canonical compare surfaces.

### Gate 4 — Consequence propagation depth
Required evidence:
- Household/institution carry-over state deepens under repeated relief/failure cycles.
- Queue scar, fatigue, delayed rebound, trust collapse, and failed-help memory stay visible over continuation windows.

Pass condition:
- Regression tests capture repeated-cycle carry-over and partial recovery behavior.

### Gate 5 — Restore/replay/continue durability
Required evidence:
- Repeated restore→continue→restore→continue flows preserve newer compare/continuation fields.
- No shape drift for continuation rollups and compare diagnostics.

Pass condition:
- Persistence regression coverage validates compare diagnostics and continuation rollups across loops.

### Gate 6 — v1 declaration clarity
Required evidence:
- A release-grade document states what still blocks calling Auralite a full-sim v1.
- The remaining blockers are small and explicit enough to audit.
- The repo can clearly distinguish between landed work, open work, and out-of-scope work.

Pass condition:
- v1 readiness can be stated plainly without hand-waving.

## Current convergence checklist
- [x] Intervention sequence family diagnostics expanded.
- [x] Long-horizon acceptance families widened with bounded checks.
- [x] Compare/checkpoint readback surfaced in operator history panel.
- [x] Compact compare summary + continuation-state deltas now emitted in canonical compare artifacts.
- [x] Compare/continuation contracts now carry household trust-collapse and responsiveness-memory deltas through checkpoint/live pairing.
- [x] Restore/continue durability coverage widened for compare diagnostics.
- [x] Soak packs now include additional 20-tick intervention-family acceptance windows.
- [x] Repeated restore-loop proof now validates compact compare/continuation deltas under snapshot-vs-live pairing.
- [x] Mixed-transition calibration diagnostics now surface `mixed_transition_drag_index` and `corridor_reconnect_gap` through city metrics, continuation deltas, compact compare summaries, and divergence clues.
- [x] Household repeated failed-help memory now carries `assistance_failure_streak` through runtime adaptation state.
- [x] `docs/AURALITE_V1_READINESS.md` now records what still blocks a truthful full-sim v1 declaration.
- [ ] Wider district-family calibration matrix remains open.
- [ ] Cross-family 20+ tick soak coverage is still narrower than final endgame target breadth.
- [ ] Final operator-loop finishing pass is still not fully closed.
- [ ] Final semantic freeze and v1 declaration remains open.

## Stop rule
Do not stop an endgame run merely because:
- the diff is coherent,
- tests pass once,
- or one PR boundary is available.

If same-branch work is still feasible, continue automatically.
If continuing is still responsible, continue automatically.
If a checkpoint lists feasible next work, that checkpoint requires continuation.

Stop only when one of these global stop conditions is true:
1. the full-sim v1 bar is actually met (readiness + completion gates + acceptance matrix),
2. a real architecture blocker exists that cannot be responsibly resolved from repo evidence,
3. further work would be speculative beyond current architecture/docs evidence,
4. validation confidence is too weak to continue responsibly.
