import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.auralite_intervention_quality import (  # noqa: E402
    INTERVENTION_QUALITY_TOP_LANE,
    intervention_quality_contract_keys,
    intervention_quality_lane_keys,
)
from app.services.auralite_world_service import AuraliteWorldService  # noqa: E402


def test_intervention_quality_ladder_is_bounded_to_accreditability():
    lane_keys = intervention_quality_lane_keys()
    assert lane_keys[-1] == INTERVENTION_QUALITY_TOP_LANE
    assert INTERVENTION_QUALITY_TOP_LANE == "accreditability"


def test_run_outcome_exposes_all_intervention_quality_lane_state_contract_fields():
    service = AuraliteWorldService()
    run_outcome = service._ensure_run_outcome_defaults({})

    for lane_key in intervention_quality_lane_keys():
        contract = intervention_quality_contract_keys(lane_key)
        assert contract["state"] in run_outcome
        assert contract["evidence"] in run_outcome
        assert contract["history"] in run_outcome


def test_scenario_insight_exposes_lane_snapshots_takeaways_and_lane_order():
    service = AuraliteWorldService()
    insight = service._ensure_scenario_insight_defaults({})

    assert insight["intervention_quality_top_lane"] == "accreditability"
    assert insight["intervention_quality_lane_order"] == list(intervention_quality_lane_keys())

    for lane_key in intervention_quality_lane_keys():
        contract = intervention_quality_contract_keys(lane_key)
        assert contract["snapshot"] in insight
        assert contract["takeaway"] in insight
