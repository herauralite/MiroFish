import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.auralite_seed_service import AuraliteSeedService  # noqa: E402
from app.services.auralite_intervention_service import AuraliteInterventionService  # noqa: E402
from app.services.auralite_explainability_service import AuraliteExplainabilityService  # noqa: E402
from app.services.auralite_runtime_service import AuraliteRuntimeService  # noqa: E402


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


def test_intervention_interaction_trace_captures_conflict_and_sequencing(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=120)
    district_id = world["districts"][0]["district_id"]
    world, record = AuraliteInterventionService.apply_changes(
        world_state=world,
        changes=[
            {"lever": "expand_service_access", "district_id": district_id, "intensity": 0.5, "delay_ticks": 2},
            {"lever": "boost_transit_service", "district_id": district_id, "intensity": 0.5},
            {"lever": "rebalance_housing_pressure", "district_id": district_id, "intensity": 0.5, "rollout_share": 0.6},
        ],
        notes="budget_austerity stress check",
    )
    AuraliteInterventionService.enrich_record_with_after(record, world)
    targeted = ((record.get("effects") or {}).get("targeted_aftermath") or {})
    trace = targeted.get("interaction_trace") or {}
    assert trace.get("conflict_penalty", 0.0) > 0.0
    assert targeted.get("lag_ticks", 0) >= 2
    assert any(
        float(item.get("effective_intensity", 1.0)) < 0.5
        for item in ((record.get("effects") or {}).get("applied") or [])
        if item.get("mode") == "lever"
    )


def test_institution_overload_builds_backlog_and_responsiveness_drag(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=120)
    target = next(
        (
            inst
            for inst in world["institutions"]
            if inst.get("institution_type") in {"service_access", "healthcare"}
        ),
        None,
    )
    assert target is not None
    target["capacity"] = 1
    target_id = target["institution_id"]

    for person in world["persons"]:
        if person.get("district_id") == target.get("district_id"):
            person["service_provider_id"] = target_id

    AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    refreshed = next(inst for inst in world["institutions"] if inst.get("institution_id") == target_id)
    arc = refreshed.get("arc_state") or {}
    assert float(arc.get("service_backlog", 0.0)) > 0.2
    assert float(arc.get("responsiveness_index", 1.0)) < 0.62


def test_delay_ticks_propagate_into_targeted_aftermath(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=100)
    district_id = world["districts"][0]["district_id"]
    world, record = AuraliteInterventionService.apply_changes(
        world_state=world,
        changes=[{"lever": "expand_service_access", "district_id": district_id, "intensity": 0.5, "delay_ticks": 3}],
        notes="sequencing",
    )
    AuraliteInterventionService.enrich_record_with_after(record, world)
    targeted = ((record.get("effects") or {}).get("targeted_aftermath") or {})
    assert targeted.get("lag_ticks", 0) >= 3
