import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.auralite_intervention_quality import find_non_normalized_postures  # noqa: E402


def test_posture_consistency_accepts_normalized_prefixes():
    evidence = {
        "overall_intervention_accreditability_posture": "for_now_intervention_accreditable_review",
        "intervention_accreditability_qualifier": "not_yet_intervention_accreditable_review",
        "main_blocking_pressure": "housing_cost_pressure",
    }
    assert find_non_normalized_postures(evidence) == []


def test_posture_consistency_flags_non_normalized_tokens():
    evidence = {
        "overall_intervention_accreditability_posture": "accreditable",
        "intervention_accreditability_qualifier": "unstable_but_possible",
        "intervention_predictability_qualifier": "for_now_predictable_review",
    }
    invalid = find_non_normalized_postures(evidence)
    assert "overall_intervention_accreditability_posture" in invalid
    assert "intervention_accreditability_qualifier" in invalid
    assert "intervention_predictability_qualifier" not in invalid
