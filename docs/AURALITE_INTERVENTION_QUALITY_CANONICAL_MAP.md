# Auralite Intervention-Quality Canonical Map

This map freezes the intervention-quality ladder to a bounded top lane.

## Ladder decision
- The ladder **stops at `accreditability`**.
- No additional synonym lanes should be added unless the roadmap is explicitly amended.

## Canonical lane order
1. adaptability
2. sustainability
3. repeatability
4. reliability
5. predictability
6. dependability
7. assurability
8. certifiability
9. accreditability

## Contract expectations per lane
Each intervention-quality lane must expose:
- `review_intervention_<lane>_state`
- `operator_review_intervention_<lane>_evidence`
- `compact_historical_intervention_<lane>_lines`
- `operator_intervention_<lane>_snapshot`
- `intervention_<lane>_takeaway`

## Posture vocabulary normalization
Posture and qualifier tokens must use normalized prefixes:
- `strongly_`
- `for_now_`
- `not_yet_`
- `unresolved_`
- `blocked_`
- `weakly_`

This keeps lane semantics stable across state, evidence, history, snapshot, and takeaway surfaces.
