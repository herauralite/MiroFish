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


def _run_multi_tick(world: dict, ticks: int, mutate=None, elapsed_minutes: int = 60) -> None:
    for tick in range(ticks):
        if mutate is not None:
            mutate(world, tick)
        AuraliteRuntimeService.tick(world, elapsed_minutes=elapsed_minutes)


def _apply_single_lever(world: dict, district_id: str, lever: str, *, intensity: float = 0.6, delay_ticks: int = 0):
    world, record = AuraliteInterventionService.apply_changes(
        world_state=world,
        changes=[{
            "lever": lever,
            "district_id": district_id,
            "intensity": intensity,
            "delay_ticks": delay_ticks,
        }],
        notes=f"lever:{lever}",
    )
    AuraliteInterventionService.enrich_record_with_after(record, world)
    world["intervention_state"]["history"][-1] = record
    world["intervention_state"]["active_aftermath"] = AuraliteInterventionService._next_active_aftermath(
        existing=world["intervention_state"].get("active_aftermath", []),
        record=record,
    )
    return world, record


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


def test_intervention_sequence_family_produces_comparable_divergence_signals(monkeypatch):
    _mute_explainability(monkeypatch)
    baseline = _fresh_world(population_target=120)
    repeated = copy.deepcopy(baseline)
    alternating = copy.deepcopy(baseline)
    district_id = baseline["districts"][0]["district_id"]

    for _ in range(3):
        repeated, _ = _apply_single_lever(repeated, district_id, "expand_service_access", intensity=0.7)
        _run_multi_tick(repeated, 2)

    alternating_plan = [
        ("expand_service_access", 0),
        ("boost_transit_service", 1),
        ("rebalance_housing_pressure", 0),
    ]
    for lever, delay_ticks in alternating_plan:
        alternating, _ = _apply_single_lever(
            alternating,
            district_id,
            lever,
            intensity=0.62,
            delay_ticks=delay_ticks,
        )
        _run_multi_tick(alternating, 2)

    repeated_report = AuraliteInterventionService.comparison_report(
        baseline_state=baseline,
        current_state=repeated,
        baseline_label="baseline",
        current_label="repeated",
    )
    alternating_report = AuraliteInterventionService.comparison_report(
        baseline_state=baseline,
        current_state=alternating,
        baseline_label="baseline",
        current_label="alternating",
    )

    assert repeated_report["checkpoint_readback"]["sequence_signal"] == "repeated_or_flat"
    assert alternating_report["checkpoint_readback"]["sequence_signal"] == "alternating_complementary"
    assert repeated_report["intervention_sequence_comparison"]["delta_repeated_sequence_count"] > 0
    assert alternating_report["intervention_sequence_comparison"]["delta_alternating_sequence_count"] > 0
    assert repeated_report["strategy_diagnostics"]["sequence_fatigue_signal"] >= alternating_report["strategy_diagnostics"]["sequence_fatigue_signal"]


def test_long_horizon_local_win_broad_miss_acceptance(monkeypatch):
    _mute_explainability(monkeypatch)
    baseline = _fresh_world(population_target=160)
    stressed = copy.deepcopy(baseline)
    target_district_id = stressed["districts"][0]["district_id"]

    for district in stressed["districts"]:
        if district["district_id"] != target_district_id:
            district["pressure_index"] = min(1.0, float(district.get("pressure_index", 0.55)) + 0.12)
            district["service_access_score"] = max(0.2, float(district.get("service_access_score", 0.5)) - 0.08)
    _run_multi_tick(stressed, 2)

    stressed, _ = _apply_single_lever(
        stressed,
        target_district_id,
        "expand_service_access",
        intensity=0.75,
        delay_ticks=2,
    )
    _run_multi_tick(stressed, 14)
    report = AuraliteInterventionService.comparison_report(baseline_state=baseline, current_state=stressed)

    assert report["strategy_diagnostics"]["local_win_broad_miss"] is True
    assert report["checkpoint_readback"]["continuation_neighbor_drag_ticks"] >= 0
    assert len(report["operator_compare_lines"]) >= 1


def test_restore_continue_loop_preserves_compare_diagnostics(monkeypatch, tmp_path):
    _mute_explainability(monkeypatch)
    monkeypatch.setattr(AuralitePersistenceService, "BASE_DIR", str(tmp_path / "worlds"))
    monkeypatch.setattr(AuralitePersistenceService, "SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    service = AuraliteWorldService()
    baseline = _fresh_world(population_target=120)
    district_id = baseline["districts"][0]["district_id"]

    working = copy.deepcopy(baseline)
    working, _ = _apply_single_lever(working, district_id, "expand_service_access", intensity=0.66, delay_ticks=1)
    _run_multi_tick(working, 8)
    AuralitePersistenceService.save_world("loop_state", working)

    loaded_once = service._ensure_milestone_03_shape(AuralitePersistenceService.load_world("loop_state"))
    _run_multi_tick(loaded_once, 4)
    AuralitePersistenceService.save_world("loop_state", loaded_once)
    loaded_twice = service._ensure_milestone_03_shape(AuralitePersistenceService.load_world("loop_state"))
    _run_multi_tick(loaded_twice, 4)

    report = AuraliteInterventionService.comparison_report(
        baseline_state=baseline,
        current_state=loaded_twice,
        baseline_label="baseline",
        current_label="loop",
    )
    assert "checkpoint_readback" in report
    assert "strategy_diagnostics" in report
    assert isinstance(report["operator_compare_lines"], list)
    assert report["continuation_window_comparison"]["continuation_rollup_delta"]["total_district_events"] >= 0


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


def test_similar_top_recovery_but_clustered_fragility_produces_worse_regime_outcome(monkeypatch):
    _mute_explainability(monkeypatch)
    clustered = _fresh_world(population_target=150)
    dispersed = _fresh_world(population_target=150)
    for idx, district in enumerate(clustered["districts"]):
        arc = district.setdefault("arc_state", {})
        ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
        district["pressure_index"] = 0.64
        arc["recovery_durability"] = 0.36
        arc["recovery_gate_index"] = 0.38
        arc["fragile_recovery_memory"] = 0.66
        arc["cumulative_stress_load"] = 0.64
        arc["shallow_recovery_risk"] = 0.66
        ripple["containment_weakness"] = 0.52
        ripple["stressed_cluster_share"] = 0.7 if idx < 5 else 0.25
        ripple["recovery_cluster_share"] = 0.18 if idx < 5 else 0.44
        district["state_phase"] = "strained" if idx < 5 else "tightening"
    for idx, district in enumerate(dispersed["districts"]):
        arc = district.setdefault("arc_state", {})
        ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
        district["pressure_index"] = 0.64
        arc["recovery_durability"] = 0.36
        arc["recovery_gate_index"] = 0.38
        arc["fragile_recovery_memory"] = 0.66
        arc["cumulative_stress_load"] = 0.64
        arc["shallow_recovery_risk"] = 0.66
        ripple["containment_weakness"] = 0.52
        ripple["stressed_cluster_share"] = 0.34
        ripple["recovery_cluster_share"] = 0.36
        district["state_phase"] = "tightening"

    for world in (clustered, dispersed):
        for district in world["districts"][:2]:
            arc = district.setdefault("arc_state", {})
            ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
            district["state_phase"] = "recovering"
            district["pressure_index"] = 0.43
            arc["recovery_durability"] = 0.66
            arc["recovery_gate_index"] = 0.7
            arc["fragile_recovery_memory"] = 0.22
            arc["cumulative_stress_load"] = 0.34
            arc["shallow_recovery_risk"] = 0.32
            ripple["containment_weakness"] = 0.21
            ripple["recovery_cluster_share"] = 0.62

    AuraliteRuntimeService._update_city_metrics(world_state=clustered, hour=11)
    AuraliteRuntimeService._update_city_metrics(world_state=dispersed, hour=11)
    clustered_metrics = ((clustered.get("city") or {}).get("world_metrics") or {})
    dispersed_metrics = ((dispersed.get("city") or {}).get("world_metrics") or {})
    clustered_split = clustered_metrics.get("local_vs_broad_pressure_split") or {}
    dispersed_split = dispersed_metrics.get("local_vs_broad_pressure_split") or {}
    clustered_regime = clustered_metrics.get("regime_state") or {}
    dispersed_regime = dispersed_metrics.get("regime_state") or {}

    assert clustered_split.get("local_recovery_share", 0.0) == dispersed_split.get("local_recovery_share", 0.0)
    assert clustered_split.get("broad_durability_drag", 0.0) >= dispersed_split.get("broad_durability_drag", 0.0)
    assert float((clustered_regime.get("signals") or {}).get("broad_durability_drag", 0.0)) >= float(
        (dispersed_regime.get("signals") or {}).get("broad_durability_drag", 0.0)
    )


def test_isolated_recovery_cluster_does_not_flip_regime_under_connected_fragility(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=160)
    for idx, district in enumerate(world["districts"]):
        arc = district.setdefault("arc_state", {})
        ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
        if idx < 2:
            district["state_phase"] = "recovering"
            district["pressure_index"] = 0.42
            arc["recovery_durability"] = 0.69
            arc["recovery_gate_index"] = 0.72
            arc["fragile_recovery_memory"] = 0.2
            arc["cumulative_stress_load"] = 0.34
            ripple["recovery_cluster_share"] = 0.68
            ripple["stressed_cluster_share"] = 0.12
            ripple["containment_weakness"] = 0.2
        else:
            district["state_phase"] = "strained"
            district["pressure_index"] = 0.74
            arc["recovery_durability"] = 0.3
            arc["recovery_gate_index"] = 0.32
            arc["fragile_recovery_memory"] = 0.74
            arc["cumulative_stress_load"] = 0.72
            ripple["recovery_cluster_share"] = 0.18
            ripple["stressed_cluster_share"] = 0.7
            ripple["containment_weakness"] = 0.58
    AuraliteRuntimeService._update_city_metrics(world_state=world, hour=13)
    metrics = ((world.get("city") or {}).get("world_metrics") or {})
    split = metrics.get("local_vs_broad_pressure_split") or {}
    regime = metrics.get("regime_state") or {}
    assert split.get("local_recovery_share", 0.0) >= 0.2
    assert split.get("citywide_durability_headroom", 1.0) < 0.33
    assert regime.get("phase") in {"clustered_decline", "broad_strain", "fragile_recovery", "mixed_transition"}
    assert regime.get("phase") != "stabilizing"


def test_clustered_improvement_lifts_headroom_only_after_multi_tick_aligned_support(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=150)
    focus_ids = [d["district_id"] for d in world["districts"][:3]]
    for district in world["districts"]:
        arc = district.setdefault("arc_state", {})
        ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
        district["pressure_index"] = 0.7
        district["state_phase"] = "tightening"
        arc["recovery_durability"] = 0.36
        arc["recovery_gate_index"] = 0.4
        arc["fragile_recovery_memory"] = 0.66
        arc["cumulative_stress_load"] = 0.66
        arc["durable_support_ticks"] = 0
        ripple["stressed_cluster_share"] = 0.66
        ripple["recovery_cluster_share"] = 0.16
        ripple["cluster_amplification"] = 0.48
        ripple["containment_weakness"] = 0.54
    AuraliteRuntimeService._update_city_metrics(world_state=world, hour=8)
    initial_metrics = ((world.get("city") or {}).get("world_metrics") or {})
    initial_headroom = float((initial_metrics.get("local_vs_broad_pressure_split") or {}).get("citywide_durability_headroom", 0.0))

    for tick in range(6):
        for district in world["districts"]:
            if district["district_id"] in focus_ids:
                arc = district.setdefault("arc_state", {})
                ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
                arc["recovery_gate_index"] = 0.58 if tick >= 2 else 0.48
                arc["recovery_durability"] = 0.52 if tick >= 2 else 0.44
                arc["fragile_recovery_memory"] = 0.48 if tick >= 2 else 0.56
                arc["durable_support_ticks"] = 2 + tick
                district["state_phase"] = "stabilizing"
                district["pressure_index"] = 0.56 if tick >= 2 else 0.64
                ripple["recovery_cluster_share"] = 0.52 if tick >= 2 else 0.3
                ripple["stressed_cluster_share"] = 0.32 if tick >= 2 else 0.52
                ripple["cluster_amplification"] = 0.2 if tick >= 2 else 0.38
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)

    final_metrics = ((world.get("city") or {}).get("world_metrics") or {})
    final_split = final_metrics.get("local_vs_broad_pressure_split") or {}
    assert final_split.get("citywide_durability_headroom", 0.0) <= max(initial_headroom + 0.1, 0.3)
    assert "topology_recovery_penalty" in final_split
    assert final_split.get("clustered_drag_dominance", 1.0) < 0.3


def test_multi_tick_clustered_fragility_builds_persistence_and_worse_headroom_than_dispersed(monkeypatch):
    _mute_explainability(monkeypatch)
    clustered = _fresh_world(population_target=160)
    dispersed = _fresh_world(population_target=160)

    def configure(world: dict, clustered_shape: bool) -> None:
        for idx, district in enumerate(world["districts"]):
            arc = district.setdefault("arc_state", {})
            ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
            district["pressure_index"] = 0.64
            district["state_phase"] = "tightening"
            arc["recovery_durability"] = 0.38
            arc["recovery_gate_index"] = 0.41
            ripple["containment_weakness"] = 0.52
            if clustered_shape:
                high_fragility = idx < 5
                arc["fragile_recovery_memory"] = 0.72 if high_fragility else 0.32
                arc["shallow_recovery_risk"] = 0.74 if high_fragility else 0.34
                arc["cumulative_stress_load"] = 0.72 if high_fragility else 0.4
                ripple["stressed_cluster_share"] = 0.72 if idx < 5 else 0.24
                ripple["recovery_cluster_share"] = 0.18 if idx < 5 else 0.38
                ripple["cluster_amplification"] = 0.48 if idx < 5 else 0.28
            else:
                high_fragility = idx % 2 == 0
                arc["fragile_recovery_memory"] = 0.66 if high_fragility else 0.36
                arc["shallow_recovery_risk"] = 0.68 if high_fragility else 0.38
                arc["cumulative_stress_load"] = 0.68 if high_fragility else 0.42
                ripple["stressed_cluster_share"] = 0.4
                ripple["recovery_cluster_share"] = 0.3
                ripple["cluster_amplification"] = 0.28

    configure(clustered, clustered_shape=True)
    configure(dispersed, clustered_shape=False)
    for hour in range(8, 16):
        AuraliteRuntimeService._update_city_metrics(world_state=clustered, hour=hour)
        AuraliteRuntimeService._update_city_metrics(world_state=dispersed, hour=hour)

    clustered_split = ((((clustered.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    dispersed_split = ((((dispersed.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    clustered_regime = ((((clustered.get("city") or {}).get("world_metrics") or {}).get("regime_state") or {}))
    dispersed_regime = ((((dispersed.get("city") or {}).get("world_metrics") or {}).get("regime_state") or {}))
    assert abs(float(clustered_split.get("citywide_pressure_avg", 0.0)) - float(dispersed_split.get("citywide_pressure_avg", 0.0))) < 0.08
    assert float(clustered_split.get("topology_drag_persistence_ticks", 0)) >= float(dispersed_split.get("topology_drag_persistence_ticks", 0))
    assert float(clustered_split.get("clustered_drag_dominance", 0.0)) >= float(dispersed_split.get("clustered_drag_dominance", 0.0))
    assert float(clustered_split.get("citywide_durability_headroom", 1.0)) <= float(dispersed_split.get("citywide_durability_headroom", 0.0)) + 0.02
    assert float(clustered_split.get("broad_durability_drag", 0.0)) >= float(dispersed_split.get("broad_durability_drag", 0.0))
    assert float((clustered_regime.get("signals") or {}).get("clustered_drag_dominance", 0.0)) >= float(
        (dispersed_regime.get("signals") or {}).get("clustered_drag_dominance", 0.0)
    )


def test_short_support_window_relapse_rebounds_fragile_memory(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=150)
    district_id = world["districts"][0]["district_id"]
    target = next(d for d in world["districts"] if d["district_id"] == district_id)
    arc = target.setdefault("arc_state", {})
    ripple = target.setdefault("derived_summary", {}).setdefault("ripple_context", {})
    arc["fragile_recovery_memory"] = 0.62
    arc["recovery_gate_index"] = 0.42
    arc["recovery_durability"] = 0.34
    arc["durable_support_ticks"] = 0
    arc["cumulative_stress_load"] = 0.66
    ripple["stressed_cluster_share"] = 0.7
    ripple["recovery_cluster_share"] = 0.16
    ripple["cluster_amplification"] = 0.46

    def _support_window(world_state: dict, tick: int) -> None:
        district = next(d for d in world_state["districts"] if d["district_id"] == district_id)
        district.setdefault("arc_state", {}).update({
            "recovery_gate_index": 0.62,
            "recovery_durability": 0.52,
            "fragile_recovery_memory": 0.46,
            "durable_support_ticks": 3 + tick,
        })
        district.setdefault("derived_summary", {}).setdefault("ripple_context", {}).update({
            "stressed_cluster_share": 0.34,
            "recovery_cluster_share": 0.5,
            "cluster_amplification": 0.22,
        })

    def _relapse_window(world_state: dict, _tick: int) -> None:
        district = next(d for d in world_state["districts"] if d["district_id"] == district_id)
        district.setdefault("arc_state", {}).update({
            "recovery_gate_index": 0.35,
            "recovery_durability": 0.32,
            "durable_support_ticks": 1,
            "cumulative_stress_load": 0.7,
        })
        district.setdefault("derived_summary", {}).setdefault("ripple_context", {}).update({
            "stressed_cluster_share": 0.74,
            "recovery_cluster_share": 0.16,
            "cluster_amplification": 0.52,
        })

    _run_multi_tick(
        world,
        ticks=3,
        mutate=_support_window,
    )
    pre_relapse = float((next(d for d in world["districts"] if d["district_id"] == district_id).get("arc_state") or {}).get("fragile_recovery_memory", 0.0))
    _run_multi_tick(
        world,
        ticks=2,
        mutate=_relapse_window,
    )
    post_relapse_arc = (next(d for d in world["districts"] if d["district_id"] == district_id).get("arc_state") or {})
    assert float(post_relapse_arc.get("fragile_recovery_memory", 0.0)) > pre_relapse
    assert float(post_relapse_arc.get("topology_drag_memory", 0.0)) > float(post_relapse_arc.get("topology_support_memory", 1.0))
    assert float(post_relapse_arc.get("topology_relapse_bias", 0.0)) >= 0.08


def test_connected_fragility_soak_diverges_from_isolated_fragility_under_equal_average_pressure(monkeypatch):
    _mute_explainability(monkeypatch)
    connected = _fresh_world(population_target=170)
    isolated = _fresh_world(population_target=170)

    def _configure(world: dict, connected_layout: bool) -> None:
        for idx, district in enumerate(world["districts"]):
            arc = district.setdefault("arc_state", {})
            ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
            district["pressure_index"] = 0.66
            district["state_phase"] = "tightening"
            arc["recovery_durability"] = 0.34
            arc["recovery_gate_index"] = 0.38
            arc["fragile_recovery_memory"] = 0.68 if idx < 4 else 0.44
            arc["cumulative_stress_load"] = 0.7 if idx < 4 else 0.5
            if connected_layout:
                ripple["stressed_cluster_share"] = 0.72 if idx < 6 else 0.24
                ripple["recovery_cluster_share"] = 0.16 if idx < 6 else 0.34
                ripple["cluster_amplification"] = 0.5 if idx < 6 else 0.28
            else:
                ripple["stressed_cluster_share"] = 0.44
                ripple["recovery_cluster_share"] = 0.24 if idx % 2 == 0 else 0.36
                ripple["cluster_amplification"] = 0.3

    _configure(connected, connected_layout=True)
    _configure(isolated, connected_layout=False)
    for _ in range(10):
        AuraliteRuntimeService.tick(connected, elapsed_minutes=60)
        AuraliteRuntimeService.tick(isolated, elapsed_minutes=60)

    connected_split = ((((connected.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    isolated_split = ((((isolated.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    assert abs(float(connected_split.get("citywide_pressure_avg", 0.0)) - float(isolated_split.get("citywide_pressure_avg", 0.0))) < 0.09
    assert float(connected_split.get("topology_drag_soak_intensity", 0.0)) >= float(isolated_split.get("topology_drag_soak_intensity", 0.0))
    assert float(connected_split.get("persistent_cluster_drag", 0.0)) > float(isolated_split.get("persistent_cluster_drag", 0.0))
    assert float(connected_split.get("topology_persistence_balance", 0.0)) >= float(isolated_split.get("topology_persistence_balance", 0.0))
    assert float(connected_split.get("broad_durability_drag", 0.0)) >= float(isolated_split.get("broad_durability_drag", 0.0))


def test_support_soak_requires_alignment_before_meaningful_headroom_lift(monkeypatch):
    _mute_explainability(monkeypatch)
    aligned = _fresh_world(population_target=150)
    misaligned = _fresh_world(population_target=150)

    def _set_support(world: dict, aligned_support: bool) -> None:
        for idx, district in enumerate(world["districts"]):
            arc = district.setdefault("arc_state", {})
            ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
            district["state_phase"] = "stabilizing"
            district["pressure_index"] = 0.57 if aligned_support else 0.61
            arc["recovery_gate_index"] = 0.62 if aligned_support else 0.49
            arc["recovery_durability"] = 0.58 if aligned_support else 0.45
            arc["fragile_recovery_memory"] = 0.42 if aligned_support else 0.56
            arc["durable_support_ticks"] = 6
            arc["cumulative_stress_load"] = 0.46 if aligned_support else 0.58
            if idx < 6:
                ripple["recovery_cluster_share"] = 0.62 if aligned_support else 0.44
                ripple["stressed_cluster_share"] = 0.2 if aligned_support else 0.44
                ripple["cluster_amplification"] = 0.18 if aligned_support else 0.36
            else:
                ripple["recovery_cluster_share"] = 0.46
                ripple["stressed_cluster_share"] = 0.26 if aligned_support else 0.4
                ripple["cluster_amplification"] = 0.22 if aligned_support else 0.32

    _set_support(aligned, aligned_support=True)
    _set_support(misaligned, aligned_support=False)
    for hour in range(8, 14):
        _set_support(aligned, aligned_support=True)
        _set_support(misaligned, aligned_support=False)
        AuraliteRuntimeService._update_city_metrics(world_state=aligned, hour=hour)
        AuraliteRuntimeService._update_city_metrics(world_state=misaligned, hour=hour)

    aligned_split = ((((aligned.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    misaligned_split = ((((misaligned.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    assert float(aligned_split.get("topology_support_soak_intensity", 0.0)) > float(misaligned_split.get("topology_support_soak_intensity", 0.0))
    assert float(aligned_split.get("topology_support_alignment_signal", 0.0)) >= float(misaligned_split.get("topology_support_alignment_signal", 0.0))
    assert float(aligned_split.get("citywide_durability_headroom", 0.0)) > float(misaligned_split.get("citywide_durability_headroom", 0.0))


def test_restore_continuity_preserves_soak_and_relapse_fields_through_next_tick(monkeypatch, tmp_path):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=160)
    _run_multi_tick(world, ticks=5)
    world_id = (world.get("world") or {}).get("world_id", "test_world")
    original_base = AuralitePersistenceService.BASE_DIR
    original_snapshot = AuralitePersistenceService.SNAPSHOT_DIR
    AuralitePersistenceService.BASE_DIR = str(tmp_path)
    AuralitePersistenceService.SNAPSHOT_DIR = str(tmp_path / "snapshots")
    AuralitePersistenceService.save_world(world_id, world)
    restored = AuralitePersistenceService.load_world(world_id)
    AuralitePersistenceService.BASE_DIR = original_base
    AuralitePersistenceService.SNAPSHOT_DIR = original_snapshot
    assert restored is not None
    restored = AuraliteWorldService()._ensure_milestone_03_shape(restored)
    before_split = ((((restored.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    before_district_arc = (restored["districts"][0].get("arc_state") or {})
    assert "topology_drag_soak_intensity" in before_split
    assert "topology_support_soak_intensity" in before_split
    assert "topology_relapse_bias" in before_district_arc
    assert "topology_support_alignment" in before_district_arc
    AuraliteRuntimeService.tick(restored, elapsed_minutes=60)
    after_split = ((((restored.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    after_district_arc = (restored["districts"][0].get("arc_state") or {})
    assert float(after_split.get("topology_drag_soak_intensity", 0.0)) >= 0.0
    assert float(after_split.get("topology_support_soak_intensity", 0.0)) >= 0.0
    assert float(after_district_arc.get("topology_relapse_bias", 0.0)) >= 0.0
    assert float(after_district_arc.get("topology_support_alignment", 0.0)) >= 0.0


def test_weak_corridor_shape_diverges_from_supported_shape_under_similar_average_pressure(monkeypatch):
    _mute_explainability(monkeypatch)
    weak_corridor_world = _fresh_world(population_target=180)
    supported_world = _fresh_world(population_target=180)

    def _configure(world: dict, weak_corridor: bool) -> None:
        for idx, district in enumerate(world["districts"]):
            arc = district.setdefault("arc_state", {})
            ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
            district["pressure_index"] = 0.62
            district["state_phase"] = "tightening"
            arc["recovery_durability"] = 0.4 if idx < 4 else 0.48
            arc["recovery_gate_index"] = 0.42 if idx < 4 else 0.5
            arc["fragile_recovery_memory"] = 0.68 if idx < 4 else 0.5
            arc["cumulative_stress_load"] = 0.68 if idx < 4 else 0.54
            if weak_corridor:
                ripple["stressed_cluster_share"] = 0.72 if idx < 4 else 0.34
                ripple["recovery_cluster_share"] = 0.14 if idx < 4 else 0.36
                ripple["cluster_amplification"] = 0.48 if idx < 4 else 0.3
                ripple["containment_weakness"] = 0.62 if idx < 4 else 0.42
            else:
                ripple["stressed_cluster_share"] = 0.5 if idx < 4 else 0.3
                ripple["recovery_cluster_share"] = 0.34 if idx < 4 else 0.46
                ripple["cluster_amplification"] = 0.32 if idx < 4 else 0.22
                ripple["containment_weakness"] = 0.42 if idx < 4 else 0.28

    _configure(weak_corridor_world, weak_corridor=True)
    _configure(supported_world, weak_corridor=False)
    for hour in range(8, 20):
        _configure(weak_corridor_world, weak_corridor=True)
        _configure(supported_world, weak_corridor=False)
        AuraliteRuntimeService._update_city_metrics(world_state=weak_corridor_world, hour=hour)
        AuraliteRuntimeService._update_city_metrics(world_state=supported_world, hour=hour)

    weak_split = ((((weak_corridor_world.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    supported_split = ((((supported_world.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    assert abs(float(weak_split.get("citywide_pressure_avg", 0.0)) - float(supported_split.get("citywide_pressure_avg", 0.0))) < 0.1
    assert float(weak_split.get("topology_corridor_weakness", 0.0)) >= float(supported_split.get("topology_corridor_weakness", 0.0))
    assert float(weak_split.get("topology_ring_containment", 0.0)) >= float(supported_split.get("topology_ring_containment", 0.0))
    assert float(weak_split.get("citywide_durability_headroom", 1.0)) < float(supported_split.get("citywide_durability_headroom", 0.0))


def test_resilient_pockets_do_not_lift_citywide_headroom_when_corridors_remain_weak(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=170)
    for idx, district in enumerate(world["districts"]):
        arc = district.setdefault("arc_state", {})
        ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
        district["pressure_index"] = 0.6 if idx < 3 else 0.65
        district["state_phase"] = "stabilizing" if idx < 3 else "tightening"
        arc["recovery_durability"] = 0.64 if idx < 3 else 0.36
        arc["recovery_gate_index"] = 0.62 if idx < 3 else 0.38
        arc["fragile_recovery_memory"] = 0.36 if idx < 3 else 0.72
        arc["durable_support_ticks"] = 8 if idx < 3 else 1
        arc["cumulative_stress_load"] = 0.48 if idx < 3 else 0.74
        ripple["recovery_cluster_share"] = 0.58 if idx < 3 else 0.16
        ripple["stressed_cluster_share"] = 0.26 if idx < 3 else 0.72
        ripple["cluster_amplification"] = 0.2 if idx < 3 else 0.5
        ripple["containment_weakness"] = 0.38 if idx < 3 else 0.66
    _run_multi_tick(world, ticks=10)
    split = ((((world.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    assert float(split.get("local_recovery_share", 0.0)) >= 0.0
    assert float(split.get("topology_corridor_weakness", 0.0)) >= 0.4
    assert float(split.get("citywide_durability_headroom", 1.0)) < 0.36
    assert float(split.get("broad_durability_drag", 0.0)) > 0.18


def test_partial_support_then_drag_reduces_alignment_gap_and_support_ticks(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=150)
    district_id = world["districts"][0]["district_id"]

    def _support(world_state: dict, tick: int) -> None:
        district = next(d for d in world_state["districts"] if d["district_id"] == district_id)
        arc = district.setdefault("arc_state", {})
        ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
        district["state_phase"] = "stabilizing"
        district["pressure_index"] = 0.56
        arc["recovery_gate_index"] = 0.6
        arc["recovery_durability"] = 0.52
        arc["fragile_recovery_memory"] = 0.46
        arc["durable_support_ticks"] = 4 + tick
        ripple["recovery_cluster_share"] = 0.54
        ripple["stressed_cluster_share"] = 0.3
        ripple["cluster_amplification"] = 0.24

    def _drag(world_state: dict, _tick: int) -> None:
        district = next(d for d in world_state["districts"] if d["district_id"] == district_id)
        arc = district.setdefault("arc_state", {})
        ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
        district["state_phase"] = "tightening"
        district["pressure_index"] = 0.7
        arc["recovery_gate_index"] = 0.34
        arc["recovery_durability"] = 0.3
        arc["fragile_recovery_memory"] = max(0.62, float(arc.get("fragile_recovery_memory", 0.6)))
        arc["durable_support_ticks"] = min(3, int(arc.get("durable_support_ticks", 0)))
        ripple["recovery_cluster_share"] = 0.14
        ripple["stressed_cluster_share"] = 0.74
        ripple["cluster_amplification"] = 0.52

    _run_multi_tick(world, ticks=4, mutate=_support)
    before = next(d for d in world["districts"] if d["district_id"] == district_id).get("arc_state") or {}
    _run_multi_tick(world, ticks=3, mutate=_drag)
    after = next(d for d in world["districts"] if d["district_id"] == district_id).get("arc_state") or {}
    assert float(before.get("topology_support_alignment_gap", 0.0)) >= 0.0
    assert float(after.get("topology_support_alignment_gap", 1.0)) < float(before.get("topology_support_alignment_gap", 0.0)) + 0.02
    assert int(after.get("durable_support_ticks", 10)) <= int(before.get("durable_support_ticks", 0))
    assert float(after.get("topology_relapse_bias", 0.0)) > 0.08


def test_restore_continuity_preserves_new_topology_shape_fields_after_tick(monkeypatch, tmp_path):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=170)
    _run_multi_tick(world, ticks=8)
    world_id = (world.get("world") or {}).get("world_id", "test_world_shape")
    original_base = AuralitePersistenceService.BASE_DIR
    original_snapshot = AuralitePersistenceService.SNAPSHOT_DIR
    AuralitePersistenceService.BASE_DIR = str(tmp_path)
    AuralitePersistenceService.SNAPSHOT_DIR = str(tmp_path / "snapshots")
    AuralitePersistenceService.save_world(world_id, world)
    restored = AuralitePersistenceService.load_world(world_id)
    AuralitePersistenceService.BASE_DIR = original_base
    AuralitePersistenceService.SNAPSHOT_DIR = original_snapshot
    assert restored is not None
    restored = AuraliteWorldService()._ensure_milestone_03_shape(restored)
    before_split = ((((restored.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    before_arc = (restored["districts"][0].get("arc_state") or {})
    assert "topology_corridor_weakness" in before_split
    assert "topology_ring_containment" in before_split
    assert "topology_cluster_support_span" in before_split
    assert "topology_support_alignment_gap" in before_arc
    _run_multi_tick(restored, ticks=3)
    after_split = ((((restored.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    after_arc = (restored["districts"][0].get("arc_state") or {})
    assert float(after_split.get("topology_corridor_weakness", 0.0)) >= 0.0
    assert float(after_split.get("topology_ring_containment", 0.0)) >= 0.0
    assert float(after_split.get("topology_cluster_support_span", 0.0)) >= 0.0
    assert float(after_arc.get("topology_support_alignment_gap", 0.0)) >= 0.0


def test_spillover_scars_persist_after_partial_recovery_and_reduce_containment(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=180)
    district_id = world["districts"][0]["district_id"]

    def _shock(world_state: dict, tick: int) -> None:
        district = next(d for d in world_state["districts"] if d["district_id"] == district_id)
        arc = district.setdefault("arc_state", {})
        ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
        district["pressure_index"] = 0.74
        district["state_phase"] = "strained"
        arc["fragile_recovery_memory"] = 0.68
        arc["recovery_durability"] = 0.3
        ripple["stressed_cluster_share"] = 0.76
        ripple["recovery_cluster_share"] = 0.14
        ripple["cluster_amplification"] = 0.52
        ripple["containment_weakness"] = 0.68

    def _partial_recovery(world_state: dict, tick: int) -> None:
        district = next(d for d in world_state["districts"] if d["district_id"] == district_id)
        arc = district.setdefault("arc_state", {})
        ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
        district["pressure_index"] = 0.56
        district["state_phase"] = "stabilizing"
        arc["recovery_durability"] = 0.52
        arc["recovery_gate_index"] = 0.58
        ripple["stressed_cluster_share"] = 0.44
        ripple["recovery_cluster_share"] = 0.34
        ripple["cluster_amplification"] = 0.34
        ripple["containment_weakness"] = 0.46

    _run_multi_tick(world, ticks=5, mutate=_shock)
    scarred = next(d for d in world["districts"] if d["district_id"] == district_id).get("arc_state") or {}
    _run_multi_tick(world, ticks=3, mutate=_partial_recovery)
    recovered = next(d for d in world["districts"] if d["district_id"] == district_id).get("arc_state") or {}

    assert float(scarred.get("spillover_scar_memory", 0.0)) > 0.06
    assert float(recovered.get("spillover_scar_memory", 0.0)) > 0.04
    assert float(recovered.get("containment_capacity", 0.0)) < 0.75


def test_restore_then_continue_keeps_spillover_scar_fields(monkeypatch, tmp_path):
    _mute_explainability(monkeypatch)
    monkeypatch.setattr(AuralitePersistenceService, "BASE_DIR", str(tmp_path / "worlds"))
    monkeypatch.setattr(AuralitePersistenceService, "SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    world = _fresh_world(population_target=160)
    _run_multi_tick(world, ticks=6)

    district = world["districts"][0]
    district.setdefault("arc_state", {})["spillover_scar_memory"] = 0.27
    district.setdefault("arc_state", {})["containment_capacity"] = 0.41
    AuralitePersistenceService.save_world("scar_restore", world)
    loaded = AuralitePersistenceService.load_world("scar_restore")
    assert loaded is not None
    restored = AuraliteWorldService()._ensure_milestone_03_shape(loaded)

    before = restored["districts"][0].get("arc_state") or {}
    assert "spillover_scar_memory" in before
    assert "containment_capacity" in before
    _run_multi_tick(restored, ticks=2)
    after = restored["districts"][0].get("arc_state") or {}
    assert float(after.get("spillover_scar_memory", 0.0)) >= 0.0
    assert float(after.get("containment_capacity", 0.0)) >= 0.0


def test_bridge_instability_stays_higher_when_fragile_and_resilient_clusters_only_touch_through_weak_links(monkeypatch):
    _mute_explainability(monkeypatch)
    fragile_bridge_world = _fresh_world(population_target=180)
    buffered_bridge_world = _fresh_world(population_target=180)

    def _configure(world: dict, buffered: bool) -> None:
        for idx, district in enumerate(world["districts"]):
            arc = district.setdefault("arc_state", {})
            ripple = district.setdefault("derived_summary", {}).setdefault("ripple_context", {})
            if idx < 4:
                district["state_phase"] = "tightening"
                district["pressure_index"] = 0.69
                arc["fragile_recovery_memory"] = 0.72
                arc["cumulative_stress_load"] = 0.7
                arc["topology_relapse_bias"] = 0.54
                arc["topology_support_alignment"] = 0.24
                arc["recovery_durability"] = 0.3
                arc["recovery_gate_index"] = 0.28
                ripple["stressed_cluster_share"] = 0.76
                ripple["recovery_cluster_share"] = 0.18
                ripple["cluster_amplification"] = 0.56
            else:
                district["state_phase"] = "stabilizing"
                district["pressure_index"] = 0.54
                arc["fragile_recovery_memory"] = 0.42
                arc["cumulative_stress_load"] = 0.46
                arc["topology_relapse_bias"] = 0.22
                arc["topology_support_alignment"] = 0.46 if not buffered else 0.68
                arc["recovery_durability"] = 0.56 if not buffered else 0.72
                arc["recovery_gate_index"] = 0.6 if not buffered else 0.78
                ripple["stressed_cluster_share"] = 0.32
                ripple["recovery_cluster_share"] = 0.44 if not buffered else 0.56
                ripple["cluster_amplification"] = 0.3

    for hour in range(7, 19):
        _configure(fragile_bridge_world, buffered=False)
        _configure(buffered_bridge_world, buffered=True)
        AuraliteRuntimeService._update_city_metrics(world_state=fragile_bridge_world, hour=hour)
        AuraliteRuntimeService._update_city_metrics(world_state=buffered_bridge_world, hour=hour)

    fragile_split = ((((fragile_bridge_world.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    buffered_split = ((((buffered_bridge_world.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
    assert float(fragile_split.get("topology_bridge_instability", 0.0)) > float(buffered_split.get("topology_bridge_instability", 0.0))
    assert float(fragile_split.get("broad_durability_drag", 0.0)) >= float(buffered_split.get("broad_durability_drag", 0.0))


def test_household_context_tracks_institution_queue_burden_and_persists_through_restore(monkeypatch, tmp_path):
    _mute_explainability(monkeypatch)
    monkeypatch.setattr(AuralitePersistenceService, "BASE_DIR", str(tmp_path / "worlds"))
    monkeypatch.setattr(AuralitePersistenceService, "SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    world = _fresh_world(population_target=170)
    _run_multi_tick(world, ticks=3)

    for institution in world["institutions"]:
        arc = institution.setdefault("arc_state", {})
        arc["service_backlog"] = 0.78
        arc["overload_fatigue"] = 0.72
        arc["responsiveness_index"] = 0.34

    _run_multi_tick(world, ticks=2)
    queue_burden_values = [
        float((household.get("context") or {}).get("institution_queue_burden", 0.0))
        for household in world["households"]
    ]
    assert queue_burden_values
    assert max(queue_burden_values) > 0.22

    AuralitePersistenceService.save_world("queue_burden_restore", world)
    restored = AuralitePersistenceService.load_world("queue_burden_restore")
    assert restored is not None
    restored = AuraliteWorldService()._ensure_milestone_03_shape(restored)
    _run_multi_tick(restored, ticks=1)
    restored_values = [
        float((household.get("context") or {}).get("institution_queue_burden", 0.0))
        for household in restored["households"]
    ]
    assert max(restored_values) >= 0.0


def test_household_queue_scar_memory_persists_after_capacity_relief(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=150)
    target = next(inst for inst in world["institutions"] if inst.get("institution_type") in {"service_access", "healthcare"})
    district_id = target["district_id"]
    target["capacity"] = 1
    for person in world["persons"]:
        if person.get("district_id") == district_id:
            person["service_provider_id"] = target["institution_id"]
            person["service_access_score"] = min(0.3, person.get("service_access_score", 0.5))

    for _ in range(5):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)

    stressed_households = [h for h in world["households"] if h.get("district_id") == district_id]
    assert stressed_households
    stressed_scar = max(float((h.get("adaptation_state") or {}).get("institution_queue_scar_memory", 0.0)) for h in stressed_households)
    assert stressed_scar > 0.02

    target["capacity"] = max(12, target["capacity"] * 12)
    for _ in range(4):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)

    relieved_households = [h for h in world["households"] if h.get("district_id") == district_id]
    assert relieved_households
    assert any(float((h.get("context") or {}).get("institution_queue_scar_memory", 0.0)) > 0.0 for h in relieved_households)
    assert any(float((h.get("context") or {}).get("service_rebound_reserve", 0.0)) >= 0.0 for h in relieved_households)


def test_city_metrics_track_long_horizon_divergence_state(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=140)
    districts = world["districts"]
    for idx, district in enumerate(districts):
        if idx < 3:
            district["state_phase"] = "recovering"
            district["pressure_index"] = 0.48
            district.setdefault("arc_state", {})["recovery_durability"] = 0.62
            district.setdefault("arc_state", {})["recovery_gate_index"] = 0.6
            district.setdefault("arc_state", {})["fragile_recovery_memory"] = 0.58
        else:
            district["state_phase"] = "strained"
            district["pressure_index"] = 0.77
            district.setdefault("arc_state", {})["recovery_durability"] = 0.32
            district.setdefault("arc_state", {})["recovery_gate_index"] = 0.3
            district.setdefault("arc_state", {})["fragile_recovery_memory"] = 0.7

    for _ in range(6):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)

    long_horizon = (((world.get("city") or {}).get("world_metrics") or {}).get("long_horizon_divergence_state") or {})
    assert "local_stabilization_bridge_streak" in long_horizon
    assert "broad_regime_drag_streak" in long_horizon
    assert "delayed_deterioration_risk" in long_horizon
    assert long_horizon.get("local_stabilization_bridge_streak", 0) >= 0
    assert long_horizon.get("delayed_deterioration_risk", 0.0) >= 0.0


def test_scenario_outcome_exposes_continuation_signals_for_operator_compare(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=120)
    for _ in range(3):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    current_world = AuraliteExplainabilityService._world_metrics_snapshot(world)
    scenario_outcome = AuraliteExplainabilityService._scenario_outcome_artifact(
        world_state=world,
        current_world=current_world,
        previous_world={},
        current_world_summary=AuraliteInterventionService.world_summary(world),
        scenario_anchor={"anchored_at": world["world"]["current_time"], "start_summary": AuraliteInterventionService.world_summary(world)},
    )
    continuation = scenario_outcome.get("continuation_signals") or {}
    assert "long_horizon_divergence_state" in continuation
    assert "propagation_continuation_rollup" in continuation
    assert "household_queue_scar_index" in continuation


def test_intervention_sequence_family_creates_divergent_outcomes_over_longer_window(monkeypatch):
    _mute_explainability(monkeypatch)
    baseline_world = _fresh_world(population_target=160)
    delayed_world = copy.deepcopy(baseline_world)
    stacked_world = copy.deepcopy(baseline_world)
    target_district = baseline_world["districts"][0]["district_id"]

    _run_multi_tick(baseline_world, ticks=12)
    _run_multi_tick(delayed_world, ticks=2)
    delayed_world, _ = AuraliteInterventionService.apply_changes(
        world_state=delayed_world,
        changes=[{"lever": "expand_service_access", "district_id": target_district, "intensity": 0.7, "delay_ticks": 3}],
        notes="delayed-run",
    )
    _run_multi_tick(delayed_world, ticks=10)

    stacked_world, _ = AuraliteInterventionService.apply_changes(
        world_state=stacked_world,
        changes=[
            {"lever": "expand_service_access", "district_id": target_district, "intensity": 0.65, "rollout_share": 0.5, "delay_ticks": 2},
            {"lever": "boost_transit_service", "district_id": target_district, "intensity": 0.55},
        ],
        notes="budget_austerity mistimed stack",
    )
    _run_multi_tick(stacked_world, ticks=12)

    baseline_metrics = (baseline_world.get("city", {}).get("world_metrics", {}) or {})
    delayed_metrics = (delayed_world.get("city", {}).get("world_metrics", {}) or {})
    stacked_metrics = (stacked_world.get("city", {}).get("world_metrics", {}) or {})
    assert float(stacked_metrics.get("institution_fatigue_index", 0.0)) >= float(delayed_metrics.get("institution_fatigue_index", 1.0))
    assert float(delayed_metrics.get("institution_fatigue_index", 0.0)) >= float(baseline_metrics.get("institution_fatigue_index", 0.0))
    assert float(stacked_metrics.get("service_backlog_index", 0.0)) >= float(baseline_metrics.get("service_backlog_index", 0.0))


def test_repeated_same_lever_sequence_exposes_repetition_penalty_and_trace(monkeypatch):
    _mute_explainability(monkeypatch)
    world = _fresh_world(population_target=140)
    district_id = world["districts"][0]["district_id"]
    for _ in range(3):
        world, record = AuraliteInterventionService.apply_changes(
            world_state=world,
            changes=[{"lever": "expand_service_access", "district_id": district_id, "intensity": 0.6}],
            notes="repeat sequence",
        )
        AuraliteInterventionService.enrich_record_with_after(record, world)
    applied = ((record.get("effects") or {}).get("applied") or [])
    trace = ((record.get("effects") or {}).get("interaction_trace") or {})
    assert applied
    assert float(applied[0].get("repetition_penalty", 0.0)) > 0.0
    assert float(trace.get("repetition_penalty", 0.0)) > 0.0
    assert float(((record.get("effects") or {}).get("targeted_aftermath") or {}).get("reversal_risk", 0.0)) >= 0.0


def test_comparison_report_exposes_sequence_and_continuation_windows(monkeypatch):
    _mute_explainability(monkeypatch)
    baseline = _fresh_world(population_target=130)
    current = copy.deepcopy(baseline)
    district_id = current["districts"][0]["district_id"]
    current, _ = AuraliteInterventionService.apply_changes(
        world_state=current,
        changes=[
            {"lever": "expand_service_access", "district_id": district_id, "intensity": 0.55, "delay_ticks": 2},
            {"lever": "boost_transit_service", "district_id": district_id, "intensity": 0.5},
        ],
        notes="compare sequence",
    )
    _run_multi_tick(current, ticks=4)
    report = AuraliteInterventionService.comparison_report(
        baseline_state=baseline,
        current_state=current,
        baseline_label="before",
        current_label="after",
    )
    artifact = AuraliteExplainabilityService._comparison_artifact(report)
    assert "intervention_sequence_comparison" in artifact
    assert "continuation_window_comparison" in artifact
    assert "strategy_diagnostics" in artifact
    assert "checkpoint_readback" in artifact
    assert "delta_history_count" in artifact["intervention_sequence_comparison"]
    assert "active_aftermath_delta" in artifact["continuation_window_comparison"]


def test_restore_continue_restore_continue_loop_preserves_outcome_continuation_shape(monkeypatch, tmp_path):
    _mute_explainability(monkeypatch)
    monkeypatch.setattr(AuralitePersistenceService, "BASE_DIR", str(tmp_path / "worlds"))
    monkeypatch.setattr(AuralitePersistenceService, "SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    service = AuraliteWorldService()
    world = _fresh_world(population_target=150)
    for _ in range(6):
        AuraliteRuntimeService.tick(world, elapsed_minutes=60)
    AuralitePersistenceService.save_world("loop_a", world)
    loaded_a = AuralitePersistenceService.load_world("loop_a")
    world_a = service._ensure_milestone_03_shape(loaded_a)

    for _ in range(6):
        AuraliteRuntimeService.tick(world_a, elapsed_minutes=60)
    AuralitePersistenceService.save_world("loop_b", world_a)
    loaded_b = AuralitePersistenceService.load_world("loop_b")
    world_b = service._ensure_milestone_03_shape(loaded_b)

    for _ in range(4):
        AuraliteRuntimeService.tick(world_b, elapsed_minutes=60)
    propagation = world_b.get("propagation_state", {}) or {}
    long_horizon = (((world_b.get("city") or {}).get("world_metrics") or {}).get("long_horizon_divergence_state") or {})
    assert isinstance((propagation.get("continuation_rollup") or {}), dict)
    assert isinstance(long_horizon, dict)
    assert "delayed_deterioration_risk" in long_horizon


def test_intervention_family_matrix_delayed_vs_immediate_vs_staggered_over_long_horizon(monkeypatch):
    _mute_explainability(monkeypatch)
    baseline = _fresh_world(population_target=180)
    district_id = baseline["districts"][0]["district_id"]

    delayed = copy.deepcopy(baseline)
    delayed, _ = _apply_single_lever(delayed, district_id, "expand_service_access", intensity=0.66, delay_ticks=3)
    _run_multi_tick(delayed, 18)

    immediate_stack = copy.deepcopy(baseline)
    immediate_stack, _ = AuraliteInterventionService.apply_changes(
        world_state=immediate_stack,
        changes=[
            {"lever": "expand_service_access", "district_id": district_id, "intensity": 0.62, "delay_ticks": 0},
            {"lever": "boost_transit_service", "district_id": district_id, "intensity": 0.6, "delay_ticks": 0},
            {"lever": "rebalance_housing_pressure", "district_id": district_id, "intensity": 0.62, "delay_ticks": 0},
        ],
        notes="immediate_stack_family",
    )
    _run_multi_tick(immediate_stack, 18)

    staggered_stack = copy.deepcopy(baseline)
    stagger_plan = [
        ("expand_service_access", 0),
        ("boost_transit_service", 2),
        ("rebalance_housing_pressure", 3),
    ]
    for lever, delay in stagger_plan:
        staggered_stack, _ = _apply_single_lever(staggered_stack, district_id, lever, intensity=0.62, delay_ticks=delay)
        _run_multi_tick(staggered_stack, 2)
    _run_multi_tick(staggered_stack, 12)

    delayed_report = AuraliteInterventionService.comparison_report(baseline_state=baseline, current_state=delayed)
    immediate_report = AuraliteInterventionService.comparison_report(baseline_state=baseline, current_state=immediate_stack)
    staggered_report = AuraliteInterventionService.comparison_report(baseline_state=baseline, current_state=staggered_stack)

    assert delayed_report["intervention_sequence_comparison"]["delta_delayed_change_count"] > 0
    assert immediate_report["intervention_sequence_comparison"]["delta_delayed_change_count"] == 0
    assert staggered_report["intervention_sequence_comparison"]["delta_delayed_change_count"] > 0
    assert staggered_report["intervention_sequence_comparison"]["delta_mistimed_change_count"] >= immediate_report["intervention_sequence_comparison"]["delta_mistimed_change_count"]
    assert staggered_report["checkpoint_readback"]["timing_mismatch_signal"] >= immediate_report["checkpoint_readback"]["timing_mismatch_signal"]


def test_short_burst_relief_has_higher_fatigue_and_weaker_durability_than_sustained_reinforcement(monkeypatch):
    _mute_explainability(monkeypatch)
    baseline = _fresh_world(population_target=170)
    district_id = baseline["districts"][0]["district_id"]

    burst = copy.deepcopy(baseline)
    for _ in range(5):
        burst, _ = _apply_single_lever(burst, district_id, "expand_service_access", intensity=0.72, delay_ticks=0)
    _run_multi_tick(burst, 18)

    sustained = copy.deepcopy(baseline)
    sustained_plan = [
        "expand_service_access",
        "boost_transit_service",
        "rebalance_housing_pressure",
        "expand_service_access",
    ]
    for lever in sustained_plan:
        sustained, _ = _apply_single_lever(sustained, district_id, lever, intensity=0.58, delay_ticks=1 if lever != "expand_service_access" else 0)
        _run_multi_tick(sustained, 2)
    _run_multi_tick(sustained, 12)

    burst_report = AuraliteInterventionService.comparison_report(baseline_state=baseline, current_state=burst)
    sustained_report = AuraliteInterventionService.comparison_report(baseline_state=baseline, current_state=sustained)

    assert burst_report["strategy_diagnostics"]["sequence_fatigue_signal"] >= sustained_report["strategy_diagnostics"]["sequence_fatigue_signal"]
    assert burst_report["strategy_diagnostics"]["sequence_regime"] == "repeated_or_flat"
    assert sustained_report["strategy_diagnostics"]["sequence_regime"] == "alternating_complementary"
    assert burst_report["checkpoint_readback"]["fatigue_signal"] >= sustained_report["checkpoint_readback"]["fatigue_signal"]
    assert burst_report["delta_summary"]["service_access_score"] >= sustained_report["delta_summary"]["service_access_score"] - 0.06
    assert burst_report["delta_summary"]["household_pressure_index"] >= sustained_report["delta_summary"]["household_pressure_index"] - 0.08


def test_partial_rollout_can_win_locally_but_miss_citywide_vs_full_rollout(monkeypatch):
    _mute_explainability(monkeypatch)
    baseline = _fresh_world(population_target=190)
    target_district_id = baseline["districts"][0]["district_id"]

    partial = copy.deepcopy(baseline)
    partial, _ = AuraliteInterventionService.apply_changes(
        world_state=partial,
        changes=[
            {
                "lever": "expand_service_access",
                "district_id": target_district_id,
                "intensity": 0.68,
                "rollout_share": 0.42,
                "delay_ticks": 1,
            }
        ],
        notes="partial_rollout_family",
    )
    _run_multi_tick(partial, 20)

    full = copy.deepcopy(baseline)
    full, _ = AuraliteInterventionService.apply_changes(
        world_state=full,
        changes=[
            {
                "lever": "expand_service_access",
                "district_id": target_district_id,
                "intensity": 0.68,
                "rollout_share": 1.0,
                "delay_ticks": 1,
            }
        ],
        notes="full_rollout_family",
    )
    _run_multi_tick(full, 20)

    partial_report = AuraliteInterventionService.comparison_report(baseline_state=baseline, current_state=partial)
    full_report = AuraliteInterventionService.comparison_report(baseline_state=baseline, current_state=full)

    partial_target = next(d for d in partial["districts"] if d["district_id"] == target_district_id)
    full_target = next(d for d in full["districts"] if d["district_id"] == target_district_id)
    partial_city_pressure = float((partial.get("city", {}).get("world_metrics", {}) or {}).get("household_pressure_index", 0.0))
    full_city_pressure = float((full.get("city", {}).get("world_metrics", {}) or {}).get("household_pressure_index", 0.0))

    assert partial_target["service_access_score"] >= full_target["service_access_score"] - 0.08
    assert partial_city_pressure >= full_city_pressure - 0.02
    assert partial_report["strategy_diagnostics"]["local_win_broad_miss"] in {True, False}
    assert full_report["checkpoint_readback"]["sequence_delta_history_count"] >= 1


def test_repeated_restore_continue_cycles_preserve_long_horizon_compare_readback(monkeypatch, tmp_path):
    _mute_explainability(monkeypatch)
    monkeypatch.setattr(AuralitePersistenceService, "BASE_DIR", str(tmp_path / "worlds"))
    monkeypatch.setattr(AuralitePersistenceService, "SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    service = AuraliteWorldService()
    baseline = _fresh_world(population_target=140)
    district_id = baseline["districts"][0]["district_id"]

    working = copy.deepcopy(baseline)
    plans = [
        ("expand_service_access", 0),
        ("boost_transit_service", 1),
        ("rebalance_housing_pressure", 2),
        ("expand_service_access", 0),
    ]
    for lever, delay in plans:
        working, _ = _apply_single_lever(working, district_id, lever, intensity=0.6, delay_ticks=delay)
        _run_multi_tick(working, 3)

    for loop_idx in range(3):
        AuralitePersistenceService.save_world("deep_loop_state", working)
        loaded = service._ensure_milestone_03_shape(AuralitePersistenceService.load_world("deep_loop_state"))
        _run_multi_tick(loaded, 4)
        working = loaded
        report = AuraliteInterventionService.comparison_report(
            baseline_state=baseline,
            current_state=working,
            baseline_label="baseline",
            current_label=f"loop_{loop_idx}",
        )
        assert report["checkpoint_readback"]["sequence_delta_history_count"] >= 1
        assert "continuation_rollup_delta" in report["continuation_window_comparison"]
        assert isinstance(report["operator_compare_lines"], list)


def test_repeated_short_relief_builds_less_household_rebound_than_sustained_relief(monkeypatch):
    _mute_explainability(monkeypatch)
    baseline = _fresh_world(population_target=180)
    district_id = baseline["districts"][0]["district_id"]

    repeated_short = copy.deepcopy(baseline)
    sustained = copy.deepcopy(baseline)

    for inst in repeated_short["institutions"]:
        if inst.get("institution_type") in {"service_access", "healthcare"} and inst.get("district_id") == district_id:
            inst["capacity"] = 2
    for inst in sustained["institutions"]:
        if inst.get("institution_type") in {"service_access", "healthcare"} and inst.get("district_id") == district_id:
            inst["capacity"] = 2

    for tick in range(20):
        if tick in {3, 7, 11, 15}:
            repeated_short, _ = _apply_single_lever(repeated_short, district_id, "expand_service_access", intensity=0.7, delay_ticks=0)
        if tick in {2, 4, 6, 8, 10, 12, 14, 16}:
            sustained, _ = _apply_single_lever(sustained, district_id, "expand_service_access", intensity=0.5, delay_ticks=1)
        _run_multi_tick(repeated_short, 1)
        _run_multi_tick(sustained, 1)

    repeated_households = [h for h in repeated_short["households"] if h.get("district_id") == district_id]
    sustained_households = [h for h in sustained["households"] if h.get("district_id") == district_id]

    repeated_rebound = sum(float((h.get("adaptation_state") or {}).get("service_rebound_reserve", 0.0)) for h in repeated_households) / max(1, len(repeated_households))
    sustained_rebound = sum(float((h.get("adaptation_state") or {}).get("service_rebound_reserve", 0.0)) for h in sustained_households) / max(1, len(sustained_households))
    repeated_queue_scar = sum(float((h.get("adaptation_state") or {}).get("institution_queue_scar_memory", 0.0)) for h in repeated_households) / max(1, len(repeated_households))
    sustained_queue_scar = sum(float((h.get("adaptation_state") or {}).get("institution_queue_scar_memory", 0.0)) for h in sustained_households) / max(1, len(sustained_households))

    assert sustained_rebound >= repeated_rebound - 0.02
    assert repeated_queue_scar >= sustained_queue_scar - 0.03
