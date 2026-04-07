# Auralite Endgame Completion Gates (Convergence Update)

This document tightens the endgame definition from `docs/AURALITE_ENDGAME_ROADMAP.md` into concrete acceptance gates.

## Why this exists
- Prevent “reviewable branch” from being confused with “endgame complete.”
- Tie intervention realism, long-horizon behavior, operator compare usability, and restore durability to explicit proof.

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
- Surfaces show checkpoint-oriented continuation clues without new parallel reporting architecture.

Pass condition:
- Operators can inspect divergence drivers from canonical compare surfaces.

### Gate 4 — Consequence propagation depth
Required evidence:
- Household/institution carry-over state deepens under repeated relief/failure cycles.
- Queue scar, fatigue, and delayed rebound signals stay visible over continuation windows.

Pass condition:
- Regression tests capture repeated-cycle carry-over and partial recovery behavior.

### Gate 5 — Restore/replay/continue durability
Required evidence:
- Repeated restore→continue→restore→continue flows preserve newer compare/continuation fields.
- No shape drift for continuation rollups and compare diagnostics.

Pass condition:
- Persistence regression coverage validates compare diagnostics and continuation rollups across loops.

## Current convergence checklist (this run)
- [x] Intervention sequence family diagnostics expanded.
- [x] Long-horizon acceptance families widened with bounded checks.
- [x] Compare/checkpoint readback surfaced in operator history panel.
- [x] Compact compare summary + continuation-state deltas now emitted in canonical compare artifacts.
- [x] Compare/continuation contracts now carry household trust-collapse and responsiveness-memory deltas through checkpoint/live pairing.
- [x] Restore/continue durability coverage widened for compare diagnostics.
- [x] Soak packs now include additional 20-tick intervention-family acceptance windows.
- [x] Repeated restore-loop proof now validates compact compare/continuation deltas under snapshot-vs-live pairing.
- [ ] Wider district-family calibration matrix remains open.
- [ ] Cross-family 20+ tick soak coverage is still narrower than final endgame target breadth.

## Stop rule
Do not stop an endgame run merely because:
- the diff is coherent,
- tests pass once,
- or one PR boundary is available.

Stop only when no additional high-value same-branch endgame work is feasible without speculative redesign or weak validation confidence.
