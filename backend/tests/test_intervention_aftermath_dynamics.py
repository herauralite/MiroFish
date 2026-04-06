import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.auralite_intervention_service import AuraliteInterventionService  # noqa: E402


def test_next_active_aftermath_honors_lag_before_tick_decay():
    entries = [
        {
            "intervention_id": "intv_1",
            "district_id": "d1",
            "amplitude": 0.6,
            "ticks_remaining": 5,
            "lag_ticks_remaining": 2,
            "fade_per_tick": 0.1,
            "reversal_risk": 0.2,
        }
    ]
    updated = AuraliteInterventionService._next_active_aftermath(existing=entries, record=None)
    assert updated[0]["ticks_remaining"] == 5
    assert updated[0]["lag_ticks_remaining"] == 1


def test_next_active_aftermath_adds_record_with_taxonomy_metadata():
    record = {
        "intervention_id": "intv_2",
        "effects": {
            "aftermath_profile": {"amplitude": 0.5, "persistence_ticks": 6, "fade_per_tick": 0.1, "reversal_risk": 0.45},
            "targeted_aftermath": {
                "district_ids": ["d1"],
                "taxonomy": {"lag_ticks": 2, "duration_ticks": 8, "fade_per_tick": 0.09, "base_backfire_risk": 0.2},
            },
        },
    }

    updated = AuraliteInterventionService._next_active_aftermath(existing=[], record=record)
    assert updated[0]["district_id"] == "d1"
    assert updated[0]["lag_ticks_remaining"] == 2
    assert updated[0]["ticks_remaining"] == 6
    assert "taxonomy" in updated[0]
