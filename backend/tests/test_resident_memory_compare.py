import sys
import copy
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.auralite_seed_service import AuraliteSeedService  # noqa: E402
from app.services.auralite_intervention_service import AuraliteInterventionService  # noqa: E402
from app.services.auralite_explainability_service import AuraliteExplainabilityService  # noqa: E402
from app.services.auralite_world_service import AuraliteWorldService  # noqa: E402
from app.services.auralite_persistence_service import AuralitePersistenceService  # noqa: E402


def _mute_explainability(monkeypatch):
    monkeypatch.setattr(AuraliteExplainabilityService, "augment_world_state", staticmethod(lambda world_state: world_state))


def _fresh_world(population_target: int = 120) -> dict:
    seed_bundle = AuraliteSeedService(seed=42).create_seed_bundle(population_target=population_target)
    now = datetime.utcnow().isoformat()
    return {
        "world": {
            "world_id": "test_world",
            "city_id": seed_bundle["city"]["city_id"],
            "current_time": datetime(2026, 1, 5, 6, 0, 0).isoformat(),
            "time_speed": 12,
            "is_running": True,
            "created_at": now,
            "updated_at": now,
            "last_tick_at": now,
        },
        "city": seed_bundle["city"],
        "districts": seed_bundle["districts"],
        "locations": seed_bundle["locations"],
        "persons": seed_bundle["persons"],
        "households": seed_bundle["households"],
        "institutions": seed_bundle["institutions"],
        "social_graph": seed_bundle.get("social_graph", {}),
        "intervention_state": {"history": [], "active_aftermath": []},
        "scenario_state": {},
        "reporting_state": {"artifacts": {}, "assembled_reports": {}, "previous_world_summary": {}, "previous_district_metrics": {}, "previous_person_metrics": {}, "previous_household_metrics": {}},
        "propagation_state": {},
    }


def test_comparison_report_surfaces_resident_memory_deltas(monkeypatch):
    _mute_explainability(monkeypatch)
    baseline = _fresh_world(population_target=140)
    current = copy.deepcopy(baseline)

    for person in current["persons"][:18]:
        adaptation = person.setdefault("adaptation_state", {})
        social = person.setdefault("social_context", {})
        state = person.setdefault("state_summary", {})
        adaptation["failed_assistance_events"] = 8
        adaptation["support_erosion_index"] = 0.82
        adaptation["recovery_debt"] = 0.64
        adaptation["fragility_index"] = 0.72
        adaptation["resilience_reserve"] = 0.08
        adaptation["stability_streak"] = 0
        adaptation["instability_episodes"] = 6
        social["support_index"] = 0.18
        state["support_erosion_index"] = 0.82
        state["recovery_debt"] = 0.64
        state["fragility_index"] = 0.72
        person["service_access_score"] = 0.22

    report = AuraliteInterventionService.comparison_report(
        baseline_state=baseline,
        current_state=current,
        baseline_label="snapshot:resident-baseline",
        current_label="current",
    )

    trust_delta = report["continuation_window_comparison"]["trust_responsiveness_delta"]
    assert "resident_assistance_trust_index" in trust_delta
    assert "resident_responsiveness_memory_index" in trust_delta
    assert "resident_assistance_failure_streak_index" in trust_delta
    assert "resident_trust_collapse_share" in trust_delta
    assert report["compact_compare_summary"]["resident_trust_delta"] < 0.0
    assert report["compact_compare_summary"]["resident_responsiveness_memory_delta"] > 0.0
    assert report["checkpoint_readback"]["divergence_driver"] == "trust_collapse"
    assert "Resident and household trust declined" in " ".join(report["operator_compare_lines"])
    assert any(
        clue in (report.get("compare_divergence_clues") or [])
        for clue in ["resident_trust_decline", "resident_failed_help_streak_rising", "resident_trust_collapse_widening"]
    )


def test_restore_compare_path_keeps_resident_memory_fingerprint(monkeypatch, tmp_path):
    _mute_explainability(monkeypatch)
    monkeypatch.setattr(AuralitePersistenceService, "BASE_DIR", str(tmp_path / "worlds"))
    monkeypatch.setattr(AuralitePersistenceService, "SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    service = AuraliteWorldService()
    baseline = _fresh_world(population_target=130)
    current = copy.deepcopy(baseline)

    for person in current["persons"][:12]:
        adaptation = person.setdefault("adaptation_state", {})
        social = person.setdefault("social_context", {})
        adaptation["failed_assistance_events"] = 6
        adaptation["support_erosion_index"] = 0.74
        adaptation["recovery_debt"] = 0.58
        adaptation["fragility_index"] = 0.66
        adaptation["resilience_reserve"] = 0.1
        adaptation["stability_streak"] = 0
        adaptation["instability_episodes"] = 5
        social["support_index"] = 0.24
        person["service_access_score"] = 0.26

    AuralitePersistenceService.save_world("resident_memory_loop", current)
    restored = service._ensure_milestone_03_shape(AuralitePersistenceService.load_world("resident_memory_loop"))

    report = AuraliteInterventionService.comparison_report(
        baseline_state=baseline,
        current_state=restored,
        baseline_label="snapshot:resident-memory-baseline",
        current_label="current",
    )

    fp = (report["path_readback"]["current_path_state"] or {}).get("continuation_fingerprint") or {}
    delta = report.get("continuation_state_delta") or {}
    assert "resident_assistance_trust_index" in fp
    assert "resident_responsiveness_memory_index" in fp
    assert "resident_assistance_failure_streak_index" in fp
    assert "resident_trust_collapse_share" in fp
    assert "resident_assistance_trust_index" in delta
    assert "resident_responsiveness_memory_index" in delta
    assert "resident_assistance_failure_streak_index" in delta
    assert "resident_trust_collapse_share" in delta
