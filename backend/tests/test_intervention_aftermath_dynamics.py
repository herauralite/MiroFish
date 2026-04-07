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


def test_comparison_report_exposes_checkpoint_and_strategy_diagnostics():
    baseline = {
        "world": {"current_time": "2026-01-01T00:00:00"},
        "city": {"world_metrics": {"district_state_overview": {"stressed": 1}}},
        "districts": [],
        "intervention_state": {"history": [], "active_aftermath": []},
        "propagation_state": {"continuation_rollup": {"total_district_events": 1, "ticks_with_neighbor_pressure": 0}},
        "scenario_state": {"scenario_outcome": {"continuation_signals": {}}},
    }
    current = {
        "world": {"current_time": "2026-01-01T12:00:00"},
        "city": {
            "world_metrics": {
                "household_pressure_index": 0.6,
                "service_access_score": 0.52,
                "district_state_overview": {"stressed": 2},
            }
        },
        "districts": [],
        "intervention_state": {
            "history": [
                {"effects": {"applied": [{"mode": "lever", "lever": "expand_service_access", "delay_ticks": 1, "repetition_penalty": 0.1}]}}
            ],
            "active_aftermath": [{"district_id": "d1"}],
        },
        "propagation_state": {"continuation_rollup": {"total_district_events": 4, "ticks_with_neighbor_pressure": 2}},
        "scenario_state": {"scenario_outcome": {"continuation_signals": {"drag": True}}},
    }
    report = AuraliteInterventionService.comparison_report(baseline_state=baseline, current_state=current)
    assert "strategy_diagnostics" in report
    assert "checkpoint_readback" in report
    assert "operator_compare_lines" in report
    assert report["continuation_window_comparison"]["continuation_rollup_delta"]["total_district_events"] == 3
    assert "compact_compare_summary" in report
    assert "continuation_state_delta" in report
    assert report["compare_checkpoint_matrix"]["continuation_state_delta"]["neighbor_drag_ticks"] == 2
