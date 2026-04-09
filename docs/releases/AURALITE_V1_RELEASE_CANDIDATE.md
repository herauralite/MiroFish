# Auralite v1 Release Candidate Artifact

## Release status
READY_FOR_V1_TAG

## Recommended tag/version
- `auralite-v1.0.0`

## What v1 includes
- Full-sim v1 readiness gates are closed with no material in-scope blockers.
- Canonical compare/checkpoint/continuation surfaces include divergence focus and path-state hinting.
- Long-horizon regression coverage spans calibration breadth, actor-memory durability, operator mixed-driver readability, and repeated restore-loop persistence.
- Runtime and compare contracts preserve trust/failure/calibration/mixed-transition signals across save/load/continue flows.

## What is post-v1
- Edge-case calibration widening outside frozen acceptance breadth.
- Additional autonomy richness and broader scenario families beyond current gate contracts.
- Any new reporting surfaces or feature-family expansions not required for v1 contract preservation.

## Operator smoke checklist
1. Run the frozen regression suites listed below and confirm all pass.
2. Generate a compare artifact from a snapshot-to-live pair and verify:
   - `compare_checkpoint_matrix` exists,
   - `operator_divergence_focus` is present,
   - `operator_path_state_hint` is readable.
3. Execute one restore→continue→restore→continue loop and verify compact compare deltas persist.
4. Confirm docs alignment:
   - `docs/AURALITE_V1_READINESS.md`
   - `docs/AURALITE_ENDGAME_COMPLETION_GATES.md`
   - `docs/AURALITE_V1_ACCEPTANCE_MATRIX.md`
5. Tag only after the above checks pass on the release commit.

## Frozen validation commands and latest results
- `pytest backend/tests/test_intervention_quality_contract.py backend/tests/test_intervention_posture_consistency.py backend/tests/test_intervention_aftermath_dynamics.py backend/tests/test_simulation_endgame_regressions.py`
  - Result: `105 passed in 84.66s`
