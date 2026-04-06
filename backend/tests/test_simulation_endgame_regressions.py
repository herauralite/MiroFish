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


def test_person_memory_chain_accumulates_debt_under_repeated_service_failure(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=120)
    person = world["persons"][0]
    person["service_access_score"] = 0.2
    person.setdefault("social_context", {})["support_index"] = 0.2
    person.setdefault("state_summary", {})["stress"] = 0.65

    for _ in range(8):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
        person = next(row for row in world["persons"] if row["person_id"] == person["person_id"])
        person["service_access_score"] = min(person.get("service_access_score", 0.2), 0.28)
        person.setdefault("social_context", {})["support_index"] = min(
            person.get("social_context", {}).get("support_index", 0.2),
            0.28,
        )

    adaptation = person.get("adaptation_state") or {}
    summary = person.get("state_summary") or {}
    assert adaptation.get("failed_assistance_events", 0) >= 4
    assert float(adaptation.get("recovery_debt", 0.0)) > 0.08
    assert float(summary.get("support_erosion_index", 0.0)) > 0.04
    assert float(summary.get("reversal_risk", 0.0)) >= 0.0


def test_institution_recovery_remains_partial_after_backlog_spike(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=100)
    target = next(
        inst for inst in world["institutions"] if inst.get("institution_type") in {"service_access", "healthcare"}
    )
    target["capacity"] = 1
    target_id = target["institution_id"]

    for person in world["persons"]:
        if person.get("district_id") == target.get("district_id"):
            person["service_provider_id"] = target_id

    AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    stressed = next(inst for inst in world["institutions"] if inst["institution_id"] == target_id)
    stressed_arc = stressed.get("arc_state") or {}
    assert float(stressed_arc.get("service_backlog", 0.0)) > 0.18

    stressed["capacity"] = max(8, stressed["capacity"] * 10)
    for _ in range(3):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    recovered = next(inst for inst in world["institutions"] if inst["institution_id"] == target_id)
    recovered_arc = recovered.get("arc_state") or {}
    assert "partial_recovery_index" in recovered_arc
    assert float(recovered_arc.get("service_backlog", 0.0)) > 0.05
    assert float(recovered_arc.get("overload_fatigue", 0.0)) > 0.0
    assert "recovery_gate_index" in recovered_arc


def test_intervention_rollout_and_delay_reduce_effective_intensity(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=120)
    district_id = world["districts"][0]["district_id"]
    world, record = AuraliteInterventionService.apply_changes(
        world_state=world,
        changes=[
            {
                "lever": "expand_service_access",
                "district_id": district_id,
                "intensity": 0.7,
                "rollout_share": 0.45,
                "delay_ticks": 3,
            }
        ],
        notes="comparison run",
    )
    applied = ((record.get("effects") or {}).get("applied") or [])[0]
    assert float(applied.get("effective_intensity", 0.0)) < 0.5
    assert float(applied.get("archetype_bias", 1.0)) > 0.0


def test_expand_service_access_captures_overload_side_effects(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=120)
    district_id = world["districts"][0]["district_id"]
    world, record = AuraliteInterventionService.apply_changes(
        world_state=world,
        changes=[{"lever": "expand_service_access", "district_id": district_id, "intensity": 0.7}],
        notes="stacked realism",
    )
    applied = ((record.get("effects") or {}).get("applied") or [])[0]
    assert any("backlog" in note for note in (applied.get("side_effects") or []))
    assert "spillover" in applied


def test_service_overload_leaves_lingering_household_strain_after_capacity_relief(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=120)
    target = next(inst for inst in world["institutions"] if inst.get("institution_type") in {"service_access", "healthcare"})
    district_id = target["district_id"]
    target["capacity"] = 1
    for person in world["persons"]:
        if person.get("district_id") == district_id:
            person["service_provider_id"] = target["institution_id"]
    AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    stressed_households = [h for h in world["households"] if h.get("district_id") == district_id]
    target["capacity"] = 16
    AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    assert stressed_households
    assert any(float((h.get("adaptation_state") or {}).get("recovery_debt", 0.0)) > 0.03 for h in stressed_households)


def test_delayed_intervention_payoff_requires_lag_window(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=120)
    district_id = world["districts"][0]["district_id"]
    before_service = sum(p.get("service_access_score", 0.5) for p in world["persons"] if p.get("district_id") == district_id)
    world, record = AuraliteInterventionService.apply_changes(
        world_state=world,
        changes=[{"lever": "expand_service_access", "district_id": district_id, "intensity": 0.6, "delay_ticks": 3}],
        notes="delay lag test",
    )
    AuraliteInterventionService.enrich_record_with_after(record, world)
    targeted = ((record.get("effects") or {}).get("targeted_aftermath") or {})
    assert targeted.get("lag_ticks", 0) >= 3
    after_service = sum(p.get("service_access_score", 0.5) for p in world["persons"] if p.get("district_id") == district_id)
    assert after_service > before_service


def test_restore_path_preserves_memory_and_institution_arc_fields(monkeypatch, tmp_path):
    _mute_explainability(monkeypatch)
    monkeypatch.setattr(AuralitePersistenceService, "BASE_DIR", str(tmp_path / "worlds"))
    monkeypatch.setattr(AuralitePersistenceService, "SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    service = AuraliteWorldService()
    world = _fresh_world(population_target=120)
    AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    person = world["persons"][0]
    institution = world["institutions"][0]
    person.setdefault("adaptation_state", {})["recovery_debt"] = 0.22
    institution.setdefault("arc_state", {})["overload_fatigue"] = 0.31
    AuralitePersistenceService.save_world("restore_test", world)
    loaded = AuralitePersistenceService.load_world("restore_test")
    restored = service._ensure_milestone_03_shape(loaded)
    assert float((restored["persons"][0].get("adaptation_state") or {}).get("recovery_debt", 0.0)) >= 0.22
    assert "overload_fatigue" in (restored["institutions"][0].get("arc_state") or {})


def test_local_stabilization_can_coexist_with_citywide_regime_block(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=120)
    for idx, district in enumerate(world["districts"]):
        if idx == 0:
            district["pressure_index"] = 0.42
            district["state_phase"] = "stabilizing"
            district.setdefault("arc_state", {})["shallow_recovery_risk"] = 0.61
        else:
            district["pressure_index"] = 0.74
            district["state_phase"] = "strained"
            district.setdefault("arc_state", {})["shallow_recovery_risk"] = 0.58
    AuraliteRuntimeService._update_city_metrics(world_state=world, hour=12)
    diagnostics = ((world.get("city", {}).get("world_metrics", {}) or {}).get("causal_diagnostics", {}))
    assert diagnostics.get("citywide_regime_recovery_blocked") is True


def test_city_metrics_expose_memory_fatigue_and_local_vs_broad_split(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=120)
    AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    metrics = (world.get("city", {}).get("world_metrics", {}) or {})
    assert "person_memory_debt_index" in metrics
    assert "institution_fatigue_index" in metrics
    split = metrics.get("local_vs_broad_pressure_split") or {}
    assert "spread_gap" in split


def test_repeated_strain_erodes_relationship_usefulness_and_capacity(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=120)
    person = world["persons"][0]
    person.setdefault("state_summary", {})["stress"] = 0.82
    person["service_access_score"] = 0.2
    for tie in person.get("social_ties", []):
        tie["support_usefulness"] = 0.72
        tie["support_capacity"] = 0.7
        tie["support_fatigue"] = 0.14

    for _ in range(6):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
        person = next(row for row in world["persons"] if row["person_id"] == person["person_id"])
        person["service_access_score"] = min(0.26, person.get("service_access_score", 0.26))
        person.setdefault("state_summary", {})["stress"] = max(0.74, person.get("state_summary", {}).get("stress", 0.74))

    refreshed = next(row for row in world["persons"] if row["person_id"] == person["person_id"])
    ties = refreshed.get("social_ties", [])
    assert ties
    assert any(float(t.get("support_usefulness", 1.0)) < 0.65 for t in ties)
    assert any(float(t.get("support_capacity", 1.0)) < 0.64 for t in ties)
    assert float((refreshed.get("social_context") or {}).get("support_fatigue_index", 0.0)) > 0.12


def test_household_propagation_is_asymmetric_when_member_fragility_splits(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=140)
    household = next((h for h in world["households"] if len(h.get("member_ids", [])) >= 3), None)
    assert household is not None
    members = [p for p in world["persons"] if p.get("person_id") in set(household["member_ids"])]
    assert len(members) >= 3
    members[0].setdefault("adaptation_state", {})["fragility_index"] = 0.82
    members[0].setdefault("state_summary", {})["stress"] = 0.86
    members[1].setdefault("adaptation_state", {})["resilience_reserve"] = 0.8
    members[1].setdefault("adaptation_state", {})["recovery_debt"] = 0.2
    members[1].setdefault("state_summary", {})["stress"] = 0.34
    members[2].setdefault("adaptation_state", {})["fragility_index"] = 0.3
    members[2].setdefault("state_summary", {})["stress"] = 0.42

    AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    refreshed_household = next(h for h in world["households"] if h["household_id"] == household["household_id"])
    ctx = refreshed_household.get("context") or {}
    assert float(ctx.get("asymmetry_strain_index", 0.0)) > 0.05
    assert float(ctx.get("fragile_member_share", 0.0)) > 0.0
    assert float(ctx.get("buffered_member_share", 0.0)) > 0.0


def test_restore_path_preserves_new_social_and_household_dynamics(monkeypatch, tmp_path):
    _mute_explainability(monkeypatch)
    monkeypatch.setattr(AuralitePersistenceService, "BASE_DIR", str(tmp_path / "worlds"))
    monkeypatch.setattr(AuralitePersistenceService, "SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    service = AuraliteWorldService()
    world = _fresh_world(population_target=120)
    AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    person = world["persons"][0]
    household = next(h for h in world["households"] if h["household_id"] == person["household_id"])
    person.setdefault("social_context", {})["support_fatigue_index"] = 0.37
    person.setdefault("social_context", {})["relationship_usefulness_index"] = 0.44
    if person.get("social_ties"):
        person["social_ties"][0]["support_capacity"] = 0.39
        person["social_ties"][0]["support_usefulness"] = 0.41
    household.setdefault("context", {})["asymmetry_strain_index"] = 0.33
    household.setdefault("social_context", {})["support_fatigue_index"] = 0.29

    AuralitePersistenceService.save_world("restore_social_household_test", world)
    loaded = AuralitePersistenceService.load_world("restore_social_household_test")
    restored = service._ensure_milestone_03_shape(loaded)
    restored_person = restored["persons"][0]
    restored_household = next(h for h in restored["households"] if h["household_id"] == household["household_id"])
    assert float((restored_person.get("social_context") or {}).get("support_fatigue_index", 0.0)) >= 0.37
    assert float((restored_person.get("social_ties") or [{}])[0].get("support_capacity", 1.0)) <= 0.39
    assert float((restored_household.get("context") or {}).get("asymmetry_strain_index", 0.0)) >= 0.33
    assert "support_fatigue_index" in (restored_household.get("social_context") or {})


def test_backlog_partial_clearance_can_leave_city_fatigue_and_fragile_recovery(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=130)
    target = next(inst for inst in world["institutions"] if inst.get("institution_type") in {"service_access", "healthcare"})
    district_id = target["district_id"]
    target["capacity"] = 1
    for person in world["persons"]:
        if person.get("district_id") == district_id:
            person["service_provider_id"] = target["institution_id"]

    AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    target["capacity"] = 20
    for _ in range(4):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)

    metrics = (world.get("city", {}).get("world_metrics", {}) or {})
    assert metrics.get("service_backlog_index", 0.0) < 0.6
    assert metrics.get("institution_fatigue_index", 0.0) > 0.005
    assert metrics.get("fragile_recovery_index", 0.0) >= 0.0


def test_tie_recovery_requires_multi_tick_low_strain_window(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=130)
    person = world["persons"][0]
    person.setdefault("state_summary", {})["stress"] = 0.86
    person["service_access_score"] = 0.2
    for tie in person.get("social_ties", []):
        tie["support_usefulness"] = 0.7
        tie["support_capacity"] = 0.68
        tie["support_fatigue"] = 0.12

    for _ in range(5):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
        person = next(row for row in world["persons"] if row["person_id"] == person["person_id"])
        person.setdefault("state_summary", {})["stress"] = 0.82
        person["service_access_score"] = 0.24
    eroded = next(row for row in world["persons"] if row["person_id"] == person["person_id"])
    eroded_tie = (eroded.get("social_ties") or [{}])[0]
    eroded_usefulness = float(eroded_tie.get("support_usefulness", 1.0))

    for _ in range(2):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
        person = next(row for row in world["persons"] if row["person_id"] == person["person_id"])
        person.setdefault("state_summary", {})["stress"] = 0.3
        person["service_access_score"] = 0.78
    early_recovery = next(row for row in world["persons"] if row["person_id"] == person["person_id"])
    early_usefulness = float((early_recovery.get("social_context") or {}).get("relationship_usefulness_index", 0.0))

    for _ in range(6):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
        person = next(row for row in world["persons"] if row["person_id"] == person["person_id"])
        person.setdefault("state_summary", {})["stress"] = 0.26
        person["service_access_score"] = 0.82
    recovering = next(row for row in world["persons"] if row["person_id"] == person["person_id"])
    recovering_usefulness = float((recovering.get("social_context") or {}).get("relationship_usefulness_index", 0.0))
    recovering_tie = (recovering.get("social_ties") or [{}])[0]

    assert eroded_usefulness < 0.62
    assert early_usefulness <= recovering_usefulness
    assert float(recovering_tie.get("failed_support_memory", 0.0)) > 0.0
    assert int(recovering_tie.get("low_strain_window_ticks", 0)) >= 0


def test_household_asymmetry_persistence_slows_recovery_even_after_relief(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=150)
    household = next((h for h in world["households"] if len(h.get("member_ids", [])) >= 3), None)
    assert household is not None
    members = [p for p in world["persons"] if p.get("person_id") in set(household["member_ids"])]
    for idx, member in enumerate(members[:3]):
        member.setdefault("state_summary", {})["stress"] = 0.86 if idx == 0 else 0.74 if idx == 1 else 0.32
        member.setdefault("adaptation_state", {})["fragility_index"] = 0.84 if idx == 0 else 0.66 if idx == 1 else 0.28
        member.setdefault("social_context", {})["support_fatigue_index"] = 0.62 if idx < 2 else 0.24

    for _ in range(4):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    stressed = next(h for h in world["households"] if h["household_id"] == household["household_id"])
    stressed_ctx = stressed.get("context") or {}

    for _ in range(4):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
        for member in world["persons"]:
            if member.get("household_id") == household["household_id"]:
                member.setdefault("state_summary", {})["stress"] = min(0.34, member.get("state_summary", {}).get("stress", 0.34))
                member.setdefault("social_context", {})["support_index"] = 0.74
                member["service_access_score"] = 0.8
    recovered = next(h for h in world["households"] if h["household_id"] == household["household_id"])
    recovered_ctx = recovered.get("context") or {}
    recovered_adaptation = recovered.get("adaptation_state") or {}

    assert float(stressed_ctx.get("asymmetry_strain_index", 0.0)) > 0.12
    assert float(recovered_ctx.get("asymmetry_persistence", 0.0)) > 0.05
    assert recovered_adaptation.get("durable_recovery_window") in {True, False}
    assert float(recovered_ctx.get("hardship_index", 1.0)) >= 0.0


def test_weak_social_network_district_recovers_slower_than_strong_network_district(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=140)
    district_ids = [world["districts"][0]["district_id"], world["districts"][1]["district_id"]]
    weak_id, strong_id = district_ids[0], district_ids[1]
    for district in world["districts"]:
        if district["district_id"] in {weak_id, strong_id}:
            district["pressure_index"] = 0.66
            district["state_phase"] = "tightening"
    for person in world["persons"]:
        if person.get("district_id") == weak_id:
            person.setdefault("social_context", {})["support_fatigue_index"] = 0.72
            person.setdefault("social_context", {})["relationship_usefulness_index"] = 0.34
        elif person.get("district_id") == strong_id:
            person.setdefault("social_context", {})["support_fatigue_index"] = 0.16
            person.setdefault("social_context", {})["relationship_usefulness_index"] = 0.74

    for _ in range(6):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    weak_district = next(d for d in world["districts"] if d["district_id"] == weak_id)
    strong_district = next(d for d in world["districts"] if d["district_id"] == strong_id)
    weak_arc = weak_district.get("arc_state") or {}
    strong_arc = strong_district.get("arc_state") or {}

    assert float(weak_arc.get("network_fragility", 0.0)) > float(strong_arc.get("network_fragility", 0.0))
    assert float(weak_arc.get("recovery_durability", 0.0)) <= float(strong_arc.get("recovery_durability", 1.0))
    assert float(weak_district.get("pressure_index", 0.0)) >= float(strong_district.get("pressure_index", 1.0))


def test_restore_then_continue_ticks_preserves_social_memory_continuity(monkeypatch, tmp_path):
    _mute_explainability(monkeypatch)
    monkeypatch.setattr(AuralitePersistenceService, "BASE_DIR", str(tmp_path / "worlds"))
    monkeypatch.setattr(AuralitePersistenceService, "SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    service = AuraliteWorldService()
    world = _fresh_world(population_target=120)
    person_id = world["persons"][0]["person_id"]
    for _ in range(3):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    person = next(p for p in world["persons"] if p["person_id"] == person_id)
    person.setdefault("state_summary", {})["stress"] = 0.8
    person["service_access_score"] = 0.25
    for _ in range(3):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    before_save = next(p for p in world["persons"] if p["person_id"] == person_id)
    tie_before = (before_save.get("social_ties") or [{}])[0]

    AuralitePersistenceService.save_world("restore_continuity_test", world)
    loaded = AuralitePersistenceService.load_world("restore_continuity_test")
    restored = service._ensure_milestone_03_shape(loaded)
    for _ in range(2):
        AuraliteRuntimeService.tick(restored, elapsed_minutes=60)
    after_restore = next(p for p in restored["persons"] if p["person_id"] == person_id)
    tie_after = (after_restore.get("social_ties") or [{}])[0]

    assert float(tie_before.get("failed_support_memory", 0.0)) > 0.0
    assert float(tie_after.get("failed_support_memory", 0.0)) > 0.0
    assert float(tie_after.get("strain_transfer_memory", 0.0)) >= 0.0
    assert "tie_rebuild_readiness" in (after_restore.get("social_context") or {})


def test_similar_districts_diverge_when_network_and_asymmetry_foundations_differ(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=180)
    weak_id, strong_id = world["districts"][0]["district_id"], world["districts"][1]["district_id"]
    for district in world["districts"]:
        if district["district_id"] in {weak_id, strong_id}:
            district["pressure_index"] = 0.63
            district["state_phase"] = "tightening"
    for household in world["households"]:
        if household.get("district_id") == weak_id:
            household.setdefault("context", {})["asymmetry_persistence"] = 0.72
            household.setdefault("adaptation_state", {})["recovery_debt"] = 0.64
        elif household.get("district_id") == strong_id:
            household.setdefault("context", {})["asymmetry_persistence"] = 0.26
            household.setdefault("adaptation_state", {})["recovery_debt"] = 0.22
    for person in world["persons"]:
        if person.get("district_id") == weak_id:
            person.setdefault("social_context", {})["support_fatigue_index"] = 0.72
            person.setdefault("social_context", {})["relationship_usefulness_index"] = 0.34
        elif person.get("district_id") == strong_id:
            person.setdefault("social_context", {})["support_fatigue_index"] = 0.18
            person.setdefault("social_context", {})["relationship_usefulness_index"] = 0.76

    for _ in range(7):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)

    weak = next(d for d in world["districts"] if d["district_id"] == weak_id)
    strong = next(d for d in world["districts"] if d["district_id"] == strong_id)
    weak_arc = weak.get("arc_state") or {}
    strong_arc = strong.get("arc_state") or {}
    assert float(weak_arc.get("recovery_gate_index", 1.0)) < float(strong_arc.get("recovery_gate_index", 0.0))
    assert float(weak_arc.get("fragile_recovery_memory", 0.0)) > float(strong_arc.get("fragile_recovery_memory", 1.0))
    assert float(weak.get("pressure_index", 0.0)) >= float(strong.get("pressure_index", 1.0))


def test_local_relief_can_remain_fragile_when_backlog_and_fatigue_stay_high(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=160)
    district_id = world["districts"][0]["district_id"]
    target = next(inst for inst in world["institutions"] if inst.get("district_id") == district_id and inst.get("institution_type") in {"service_access", "healthcare"})
    target["capacity"] = 1
    for person in world["persons"]:
        if person.get("district_id") == district_id:
            person["service_provider_id"] = target["institution_id"]
            person["service_access_score"] = 0.32
            person.setdefault("social_context", {})["support_fatigue_index"] = 0.68

    for _ in range(3):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    pre_relief_district = next(d for d in world["districts"] if d["district_id"] == district_id)
    pre_relief_service = float(pre_relief_district.get("service_access_score", 0.0))
    world, _record = AuraliteInterventionService.apply_changes(
        world_state=world,
        changes=[{"lever": "expand_service_access", "district_id": district_id, "intensity": 0.7}],
        notes="fragile relief",
    )
    target["capacity"] = 3
    for _ in range(4):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)

    district = next(d for d in world["districts"] if d["district_id"] == district_id)
    arc = district.get("arc_state") or {}
    assert float(district.get("service_access_score", 0.0)) >= pre_relief_service
    assert float(arc.get("service_backlog", 0.0)) > 0.1
    assert float(arc.get("fragile_recovery_memory", 0.0)) > 0.05
    assert float(arc.get("recovery_gate_index", 1.0)) < 0.55


def test_restore_then_continue_preserves_district_calibration_state(monkeypatch, tmp_path):
    _mute_explainability(monkeypatch)
    monkeypatch.setattr(AuralitePersistenceService, "BASE_DIR", str(tmp_path / "worlds"))
    monkeypatch.setattr(AuralitePersistenceService, "SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    service = AuraliteWorldService()
    world = _fresh_world(population_target=140)
    for _ in range(5):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    district_id = world["districts"][0]["district_id"]
    district = next(d for d in world["districts"] if d["district_id"] == district_id)
    district.setdefault("arc_state", {})["fragile_recovery_memory"] = 0.29
    district.setdefault("arc_state", {})["recovery_gate_index"] = 0.41
    district.setdefault("derived_summary", {}).setdefault("ripple_context", {})["containment_weakness"] = 0.22
    AuralitePersistenceService.save_world("restore_district_state_test", world)
    loaded = AuralitePersistenceService.load_world("restore_district_state_test")
    restored = service._ensure_milestone_03_shape(loaded)
    restored_district = next(d for d in restored["districts"] if d["district_id"] == district_id)
    before_memory = float((restored_district.get("arc_state") or {}).get("fragile_recovery_memory", 0.0))
    for _ in range(2):
        AuraliteRuntimeService.tick(restored, elapsed_minutes=60)
    after_district = next(d for d in restored["districts"] if d["district_id"] == district_id)
    after_arc = after_district.get("arc_state") or {}
    after_ripple = (after_district.get("derived_summary") or {}).get("ripple_context", {})
    assert before_memory >= 0.29
    assert "recovery_gate_index" in after_arc
    assert "fragile_recovery_memory" in after_arc
    assert "containment_weakness" in after_ripple


def test_clustered_fragility_blocks_city_headroom_even_when_some_districts_recover(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=160)
    for idx, district in enumerate(world["districts"]):
        arc = district.setdefault("arc_state", {})
        ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
        if idx < 2:
            district["state_phase"] = "recovering"
            district["pressure_index"] = 0.44
            arc["recovery_durability"] = 0.67
            arc["recovery_gate_index"] = 0.69
            arc["fragile_recovery_memory"] = 0.22
            arc["cumulative_stress_load"] = 0.31
            arc["shallow_recovery_risk"] = 0.35
            ripple["containment_weakness"] = 0.18
        else:
            district["state_phase"] = "strained"
            district["pressure_index"] = 0.76
            arc["recovery_durability"] = 0.28
            arc["recovery_gate_index"] = 0.33
            arc["fragile_recovery_memory"] = 0.72
            arc["cumulative_stress_load"] = 0.7
            arc["shallow_recovery_risk"] = 0.74
            ripple["containment_weakness"] = 0.55

    AuraliteRuntimeService._update_city_metrics(world_state=world, hour=18)
    metrics = (world.get("city", {}).get("world_metrics", {}) or {})
    split = metrics.get("local_vs_broad_pressure_split") or {}
    assert split.get("local_recovery_share", 0.0) >= 0.2
    assert split.get("clustered_fragility_pressure", 0.0) >= 0.2
    assert split.get("broad_durability_drag", 0.0) >= 0.05
    assert split.get("citywide_durability_headroom", 1.0) < 0.35


def test_durable_recovery_requires_multi_tick_support_not_single_relief_jump(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=150)
    district_id = world["districts"][0]["district_id"]
    district = next(d for d in world["districts"] if d["district_id"] == district_id)
    arc = district.setdefault("arc_state", {})
    arc["recovery_durability"] = 0.46
    arc["fragile_recovery_memory"] = 0.57
    arc["recovery_gate_index"] = 0.44
    arc["cumulative_stress_load"] = 0.62
    arc["durable_support_ticks"] = 0
    district["state_phase"] = "stabilizing"
    district["pressure_index"] = 0.54

    AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    first_tick = next(d for d in world["districts"] if d["district_id"] == district_id)
    first_arc = first_tick.get("arc_state") or {}
    first_durability = float(first_arc.get("recovery_durability", 0.0))
    for _ in range(7):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    refreshed = next(d for d in world["districts"] if d["district_id"] == district_id)
    refreshed_arc = refreshed.get("arc_state") or {}
    assert first_durability < 0.6
    assert "durable_support_ticks" in refreshed_arc
    assert float(refreshed_arc.get("recovery_durability", 0.0)) <= first_durability + 0.05
    assert float(refreshed_arc.get("fragile_recovery_memory", 0.0)) >= 0.0


def test_local_recovery_share_can_rise_while_broad_drag_still_suppresses_city_progress(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=150)
    districts = world["districts"]
    for idx, district in enumerate(districts):
        arc = district.setdefault("arc_state", {})
        ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
        if idx % 2 == 0:
            district["state_phase"] = "stabilizing"
            district["pressure_index"] = 0.49
            arc["recovery_durability"] = 0.54
            arc["recovery_gate_index"] = 0.57
            arc["fragile_recovery_memory"] = 0.43
            arc["cumulative_stress_load"] = 0.53
            arc["shallow_recovery_risk"] = 0.48
            ripple["containment_weakness"] = 0.33
        else:
            district["state_phase"] = "tightening"
            district["pressure_index"] = 0.68
            arc["recovery_durability"] = 0.36
            arc["recovery_gate_index"] = 0.39
            arc["fragile_recovery_memory"] = 0.65
            arc["cumulative_stress_load"] = 0.64
            arc["shallow_recovery_risk"] = 0.67
            ripple["containment_weakness"] = 0.49

    AuraliteRuntimeService._update_city_metrics(world_state=world, hour=9)
    split = ((world.get("city", {}).get("world_metrics", {}) or {}).get("local_vs_broad_pressure_split") or {})
    assert split.get("local_recovery_share", 0.0) >= 0.4
    assert split.get("broad_durability_drag", 0.0) >= 0.04
    assert split.get("citywide_durability_headroom", 1.0) < 0.35
    assert split.get("clustered_fragility_pressure", 0.0) > 0.1


def test_restore_and_replay_path_keeps_city_calibration_consistent(monkeypatch, tmp_path):
    _mute_explainability(monkeypatch)
    monkeypatch.setattr(AuralitePersistenceService, "BASE_DIR", str(tmp_path / "worlds"))
    monkeypatch.setattr(AuralitePersistenceService, "SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    service = AuraliteWorldService()
    world = _fresh_world(population_target=140)
    for _ in range(4):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)

    checkpoint_world = copy.deepcopy(world)
    checkpoint_world["city"]["world_metrics"] = copy.deepcopy((world.get("city") or {}).get("world_metrics") or {})
    AuralitePersistenceService.save_world("calibration_replay", checkpoint_world)
    loaded = AuralitePersistenceService.load_world("calibration_replay")
    restored = service._ensure_milestone_03_shape(loaded)
    replay = copy.deepcopy(checkpoint_world)

    for _ in range(3):
        AuraliteRuntimeService.tick(restored, elapsed_minutes=60)
        AuraliteRuntimeService.tick(replay, elapsed_minutes=60)

    restored_split = (((restored.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {})
    replay_split = (((replay.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {})
    assert restored_split.keys() >= {"citywide_durability_headroom", "clustered_fragility_pressure", "broad_durability_drag"}
    for key in ["citywide_durability_headroom", "clustered_fragility_pressure", "broad_durability_drag"]:
        assert abs(float(restored_split.get(key, 0.0)) - float(replay_split.get(key, 0.0))) < 1e-6
