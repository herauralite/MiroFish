from __future__ import annotations

from datetime import datetime

from ..models.auralite_intervention import AuraliteInterventionRecord


class AuraliteInterventionService:
    DISTRICT_ARCHETYPE_BIASES = {
        "finance_prestige": {"service_capacity": 0.92, "mobility_access": 1.08, "household_housing": 0.95},
        "startup_speculation": {"service_capacity": 1.08, "mobility_access": 1.04, "household_housing": 0.94},
        "historic_mixed_use": {"service_capacity": 1.0, "mobility_access": 1.0, "household_housing": 1.02},
        "industrial_logistics": {"service_capacity": 0.94, "mobility_access": 0.96, "household_housing": 1.04},
        "suburban_family": {"service_capacity": 1.06, "mobility_access": 0.98, "household_housing": 1.03},
        "elite_enclave": {"service_capacity": 0.86, "mobility_access": 1.02, "household_housing": 0.9},
        "transitional_stressed": {"service_capacity": 1.12, "mobility_access": 0.94, "household_housing": 1.08},
        "edge_hinterland": {"service_capacity": 0.95, "mobility_access": 0.92, "household_housing": 1.0},
        "education_civic": {"service_capacity": 1.05, "mobility_access": 1.0, "household_housing": 0.98},
        "nightlife_vice": {"service_capacity": 0.96, "mobility_access": 1.06, "household_housing": 0.94},
    }


    LEVER_TAXONOMY = {
        "rebalance_housing_pressure": {
            "target_layer": "household_housing",
            "intensity_profile": "redistributive",
            "duration_ticks": 8,
            "lag_ticks": 1,
            "fade_per_tick": 0.11,
            "base_backfire_risk": 0.16,
            "scope": "district_local",
            "synergies": ["expand_service_access"],
            "conflicts": ["tighten_rent_enforcement"],
        },
        "boost_transit_service": {
            "target_layer": "mobility_access",
            "intensity_profile": "infrastructure",
            "duration_ticks": 10,
            "lag_ticks": 2,
            "fade_per_tick": 0.09,
            "base_backfire_risk": 0.2,
            "scope": "district_local",
            "synergies": ["expand_service_access"],
            "conflicts": ["budget_austerity"],
        },
        "expand_service_access": {
            "target_layer": "service_capacity",
            "intensity_profile": "capacity_build",
            "duration_ticks": 12,
            "lag_ticks": 2,
            "fade_per_tick": 0.08,
            "base_backfire_risk": 0.14,
            "scope": "district_local",
            "synergies": ["rebalance_housing_pressure", "boost_transit_service"],
            "conflicts": ["budget_austerity"],
        },
    }
    INTERACTION_MATRIX = {
        ("rebalance_housing_pressure", "expand_service_access"): {"synergy": 0.12, "sequencing_bonus": 0.05},
        ("expand_service_access", "boost_transit_service"): {"synergy": 0.1, "sequencing_bonus": 0.04},
        ("rebalance_housing_pressure", "boost_transit_service"): {"cannibalization": 0.08},
    }
    @staticmethod
    def world_summary(world_state: dict) -> dict:
        return AuraliteInterventionService._world_summary(world_state)

    @staticmethod
    def summary_delta(before: dict, after: dict) -> dict:
        return AuraliteInterventionService._summary_delta(before, after)

    @staticmethod
    def apply_changes(world_state: dict, changes: list[dict], notes: str = "") -> tuple[dict, dict]:
        before = AuraliteInterventionService.world_summary(world_state)
        entity_indexes = {
            "district": {d["district_id"]: d for d in world_state.get("districts", [])},
            "resident": {p["person_id"]: p for p in world_state.get("persons", [])},
            "household": {h["household_id"]: h for h in world_state.get("households", [])},
            "institution": {i["institution_id"]: i for i in world_state.get("institutions", [])},
        }

        lever_plan = [change for change in changes if "lever" in change]
        applied = []
        for change in changes:
            if "lever" in change:
                leverage_effect = AuraliteInterventionService._apply_lever(
                    world_state=world_state,
                    change=change,
                    lever_plan=lever_plan,
                    notes=notes,
                )
                if leverage_effect:
                    leverage_effect["taxonomy"] = AuraliteInterventionService._lever_taxonomy(leverage_effect.get("lever"))
                    applied.append(leverage_effect)
                continue

            target = change.get("target")
            target_id = change.get("id")
            updates = change.get("set", {})
            entity = entity_indexes.get(target, {}).get(target_id)
            if not entity or not isinstance(updates, dict):
                continue
            entity.update(updates)
            applied.append({"mode": "direct", "target": target, "id": target_id, "fields": sorted(updates.keys())})

        intervention_id = f"intv_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        record = AuraliteInterventionRecord(
            intervention_id=intervention_id,
            applied_at=datetime.utcnow().isoformat(),
            change_count=len(applied),
            notes=notes,
            effects={
                "applied": applied,
                "before_summary": before,
                "interaction_trace": AuraliteInterventionService._interaction_trace(applied),
            },
        )

        world_state.setdefault("intervention_state", {})
        world_state["intervention_state"]["last_applied_at"] = record.applied_at
        world_state["intervention_state"].setdefault("history", []).append(record.to_dict())
        world_state["intervention_state"]["history"] = world_state["intervention_state"]["history"][-40:]
        world_state["intervention_state"]["active_aftermath"] = AuraliteInterventionService._next_active_aftermath(
            existing=world_state["intervention_state"].get("active_aftermath", []),
            record=record.to_dict(),
        )
        return world_state, record.to_dict()

    @staticmethod
    def enrich_record_with_after(record: dict, world_state: dict):
        before = (record.get("effects") or {}).get("before_summary") or {}
        after = AuraliteInterventionService.world_summary(world_state)
        record.setdefault("effects", {})
        record["effects"]["after_summary"] = after
        record["effects"]["delta_summary"] = AuraliteInterventionService.summary_delta(before, after)
        record["effects"]["aftermath_hooks"] = AuraliteInterventionService._aftermath_hooks(
            record["effects"]["delta_summary"],
        )
        record["effects"]["aftermath_profile"] = AuraliteInterventionService._aftermath_profile(
            delta=record["effects"]["delta_summary"],
            intervention_count=len((world_state.get("intervention_state") or {}).get("history", [])),
        )
        record["effects"]["targeted_aftermath"] = AuraliteInterventionService._targeted_aftermath(
            applied=(record.get("effects") or {}).get("applied", []),
            district_shifts=(record["effects"]["delta_summary"] or {}).get("district_shifts", []),
            aftermath_profile=record["effects"]["aftermath_profile"],
        )

    @staticmethod
    def comparison_report(
        baseline_state: dict,
        current_state: dict,
        baseline_label: str = "baseline",
        current_label: str = "current",
    ) -> dict:
        baseline_summary = AuraliteInterventionService.world_summary(baseline_state)
        current_summary = AuraliteInterventionService.world_summary(current_state)
        delta = AuraliteInterventionService.summary_delta(baseline_summary, current_summary)
        sequence_comparison = AuraliteInterventionService._intervention_sequence_comparison(
            baseline_state=baseline_state,
            current_state=current_state,
        )
        continuation_comparison = AuraliteInterventionService._continuation_window_comparison(
            baseline_state=baseline_state,
            current_state=current_state,
        )
        strategy_diagnostics = AuraliteInterventionService._strategy_diagnostics(
            delta=delta,
            sequence_comparison=sequence_comparison,
            continuation_comparison=continuation_comparison,
        )
        return {
            "baseline_label": baseline_label,
            "current_label": current_label,
            "generated_at": datetime.utcnow().isoformat(),
            "baseline_world_time": baseline_summary.get("world_time"),
            "current_world_time": current_summary.get("world_time"),
            "baseline_summary": baseline_summary,
            "current_summary": current_summary,
            "baseline_regime_state": ((baseline_state.get("city", {}).get("world_metrics", {}) or {}).get("regime_state", {})),
            "current_regime_state": ((current_state.get("city", {}).get("world_metrics", {}) or {}).get("regime_state", {})),
            "delta_summary": delta,
            "aftermath_hooks": AuraliteInterventionService._aftermath_hooks(delta),
            "intervention_sequence_comparison": sequence_comparison,
            "continuation_window_comparison": continuation_comparison,
            "strategy_diagnostics": strategy_diagnostics,
            "path_readback": AuraliteInterventionService._path_readback(
                baseline_state=baseline_state,
                current_state=current_state,
                baseline_label=baseline_label,
                current_label=current_label,
            ),
            "checkpoint_readback": AuraliteInterventionService._checkpoint_readback(
                sequence_comparison=sequence_comparison,
                continuation_comparison=continuation_comparison,
                strategy_diagnostics=strategy_diagnostics,
            ),
            "operator_compare_lines": AuraliteInterventionService._operator_compare_lines(
                strategy_diagnostics=strategy_diagnostics,
                sequence_comparison=sequence_comparison,
                continuation_comparison=continuation_comparison,
            ),
        }

    @staticmethod
    def _world_summary(world_state: dict) -> dict:
        metrics = world_state.get("city", {}).get("world_metrics", {})
        districts = world_state.get("districts", [])
        top_districts = sorted(
            [
                {
                    "district_id": d.get("district_id"),
                    "name": d.get("name"),
                    "pressure_index": d.get("pressure_index", 0.0),
                    "service_access_score": d.get("service_access_score", 0.0),
                    "household_pressure": d.get("household_pressure", 0.0),
                    "state_phase": d.get("state_phase", "steady"),
                }
                for d in districts
            ],
            key=lambda x: x["pressure_index"],
            reverse=True,
        )[:3]
        return {
            "world_time": world_state.get("world", {}).get("current_time"),
            "employment_rate": metrics.get("employment_rate", 0.0),
            "avg_housing_burden": metrics.get("avg_housing_burden", 0.0),
            "household_pressure_index": metrics.get("household_pressure_index", 0.0),
            "service_access_score": metrics.get("service_access_score", 0.0),
            "stressed_districts": (metrics.get("district_state_overview") or {}).get("stressed", 0),
            "top_pressure_districts": top_districts,
        }

    @staticmethod
    def _summary_delta(before: dict, after: dict) -> dict:
        numeric_keys = [
            "employment_rate",
            "avg_housing_burden",
            "household_pressure_index",
            "service_access_score",
            "stressed_districts",
        ]
        delta = {
            key: round(float(after.get(key, 0.0)) - float(before.get(key, 0.0)), 3)
            for key in numeric_keys
        }
        before_by_id = {d.get("district_id"): d for d in before.get("top_pressure_districts", [])}
        district_shifts = []
        for district in after.get("top_pressure_districts", []):
            previous = before_by_id.get(district.get("district_id"), {})
            district_shifts.append({
                "district_id": district.get("district_id"),
                "name": district.get("name"),
                "pressure_delta": round(district.get("pressure_index", 0.0) - previous.get("pressure_index", 0.0), 3),
                "service_access_delta": round(
                    district.get("service_access_score", 0.0) - previous.get("service_access_score", 0.0),
                    3,
                ),
                "phase_before": previous.get("state_phase", "n/a"),
                "phase_after": district.get("state_phase", "n/a"),
                "causal_notes": AuraliteInterventionService._district_causal_notes(previous, district),
            })
        delta["district_shifts"] = district_shifts
        return delta

    @staticmethod
    def _district_causal_notes(previous: dict, current: dict) -> list[str]:
        notes = []
        if current.get("pressure_index", 0.0) - previous.get("pressure_index", 0.0) >= 0.03:
            notes.append("District pressure climbed versus baseline.")
        if current.get("service_access_score", 0.0) - previous.get("service_access_score", 0.0) <= -0.02:
            notes.append("Service access slipped and likely amplified resident stress.")
        if not notes:
            notes.append("No single dominant shift detected yet; pressure remains distributed.")
        return notes

    @staticmethod
    def _aftermath_hooks(delta: dict) -> list[dict]:
        hooks = []
        pressure_delta = delta.get("household_pressure_index", 0.0)
        service_delta = delta.get("service_access_score", 0.0)
        stressed_delta = delta.get("stressed_districts", 0.0)
        if pressure_delta < 0:
            hooks.append({"kind": "pressure", "text": "Household pressure eased after intervention."})
        elif pressure_delta > 0:
            hooks.append({"kind": "pressure", "text": "Household pressure rose after intervention."})
        if service_delta > 0:
            hooks.append({"kind": "service", "text": "Service access improved relative to baseline."})
        elif service_delta < 0:
            hooks.append({"kind": "service", "text": "Service access deteriorated relative to baseline."})
        if stressed_delta != 0:
            direction = "more" if stressed_delta > 0 else "fewer"
            hooks.append({"kind": "districts", "text": f"{abs(stressed_delta):.3g} {direction} stressed districts versus baseline."})
        return hooks[:4]

    @staticmethod
    def _aftermath_profile(delta: dict, intervention_count: int) -> dict:
        amplitude = min(
            1.0,
            abs(float(delta.get("household_pressure_index", 0.0))) * 0.45
            + abs(float(delta.get("service_access_score", 0.0))) * 0.35
            + abs(float(delta.get("employment_rate", 0.0))) * 0.2,
        )
        persistence_ticks = max(1, min(16, int(round(4 + amplitude * 10))))
        reversal_risk = round(min(1.0, 0.28 + (intervention_count * 0.03) + (amplitude * 0.35)), 3)
        return {
            "amplitude": round(amplitude, 3),
            "persistence_ticks": persistence_ticks,
            "fade_per_tick": round(max(0.04, min(0.22, 1.0 / max(1, persistence_ticks))), 3),
            "reversal_risk": reversal_risk,
        }

    @staticmethod
    def _apply_lever(world_state: dict, change: dict, lever_plan: list[dict], notes: str = "") -> dict | None:
        lever = change.get("lever")
        district_id = change.get("district_id")
        base_intensity = max(0.0, min(1.0, float(change.get("intensity", 0.2))))
        rollout_share = max(0.25, min(1.0, float(change.get("rollout_share", 1.0))))
        sequencing_offset = max(0, int(change.get("delay_ticks", 0)))
        district = next((d for d in world_state.get("districts", []) if d.get("district_id") == district_id), {})
        archetype = district.get("archetype")
        target_layer = (AuraliteInterventionService._lever_taxonomy(lever) or {}).get("target_layer")
        archetype_bias = AuraliteInterventionService._archetype_bias(archetype, target_layer)
        rollout_penalty = max(0.55, 0.7 + (rollout_share * 0.3))
        delay_penalty = max(0.7, 1.0 - (sequencing_offset * 0.06))
        interaction = AuraliteInterventionService._resolve_interaction(
            lever=lever,
            district_id=district_id,
            lever_plan=lever_plan,
            notes=notes,
        )
        repetition_penalty, repetition_flags = AuraliteInterventionService._repetition_penalty(
            world_state=world_state,
            lever=lever,
            district_id=district_id,
        )
        mistimed_stack_penalty, mistimed_stack_note = AuraliteInterventionService._mistimed_stack_penalty(
            world_state=world_state,
            lever=lever,
            district_id=district_id,
            sequencing_offset=sequencing_offset,
            lever_plan=lever_plan,
        )
        intensity = max(
            0.0,
            min(
                1.0,
                base_intensity
                * rollout_share
                * rollout_penalty
                * delay_penalty
                * archetype_bias
                * (1.0 + float(interaction.get("synergy_bonus", 0.0)))
                * (1.0 - float(interaction.get("conflict_penalty", 0.0))),
            ),
        )
        intensity = round(
            max(
                0.0,
                min(
                    1.0,
                    intensity
                    * max(0.52, 1.0 - repetition_penalty)
                    * max(0.58, 1.0 - mistimed_stack_penalty),
                ),
            ),
            3,
        )
        side_effects = []
        side_effects.extend(repetition_flags)
        if mistimed_stack_note:
            side_effects.append(mistimed_stack_note)

        if lever == "rebalance_housing_pressure":
            households = [h for h in world_state.get("households", []) if h.get("district_id") == district_id]
            institutions = [i for i in world_state.get("institutions", []) if i.get("district_id") == district_id and i.get("institution_type") == "landlord"]
            for household in households:
                household["monthly_rent"] = round(max(300.0, household.get("monthly_rent", 0.0) * (1 - 0.15 * intensity)), 2)
                burden = household.get("housing_cost_burden", 0.0)
                household["housing_cost_burden"] = round(max(0.05, burden * (1 - 0.2 * intensity)), 3)
                household["pressure_index"] = round(max(0.05, household.get("pressure_index", 0.0) * (1 - 0.25 * intensity)), 3)
                if rollout_share < 0.75 and household["household_id"][-1] in {"6", "7", "8", "9"}:
                    household["pressure_index"] = round(min(1.0, household["pressure_index"] + (0.03 * (0.75 - rollout_share))), 3)
            for institution in institutions:
                institution["pressure_index"] = round(max(0.0, institution.get("pressure_index", 0.4) - 0.18 * intensity), 3)
                institution["access_score"] = round(min(1.0, institution.get("access_score", 0.5) + 0.1 * intensity), 3)
            if rollout_share < 0.75:
                side_effects.append("partial_rollout_left_high-risk renters under-eased pressure.")
            return {
                "mode": "lever",
                "lever": lever,
                "district_id": district_id,
                "households_touched": len(households),
                "institutions_touched": len(institutions),
                "effective_intensity": round(intensity, 3),
                "rollout_share": round(rollout_share, 3),
                "delay_ticks": sequencing_offset,
                "interaction": interaction,
                "archetype_bias": round(archetype_bias, 3),
                "repetition_penalty": round(repetition_penalty, 3),
                "mistimed_stack_penalty": round(mistimed_stack_penalty, 3),
                "side_effects": AuraliteInterventionService._dedupe_notes(side_effects),
            }

        if lever == "boost_transit_service":
            institutions = [
                i for i in world_state.get("institutions", []) if i.get("district_id") == district_id and i.get("institution_type") == "transit"
            ]
            residents = [p for p in world_state.get("persons", []) if p.get("district_id") == district_id]
            for institution in institutions:
                institution["access_score"] = round(min(1.0, institution.get("access_score", 0.5) + 0.25 * intensity), 3)
                institution["pressure_index"] = round(max(0.0, institution.get("pressure_index", 0.3) - 0.2 * intensity), 3)
                arc = institution.setdefault("arc_state", {})
                arc["service_backlog"] = round(min(1.0, float(arc.get("service_backlog", 0.0)) + (0.08 * intensity)), 3)
                arc["overload_fatigue"] = round(min(1.0, float(arc.get("overload_fatigue", 0.0)) + (0.05 * intensity)), 3)
                side_effects.append("transit throughput gain increased deferred maintenance backlog.")
            for resident in residents:
                resident["service_access_score"] = round(min(1.0, resident.get("service_access_score", 0.5) + 0.08 * intensity), 3)
                resident.setdefault("state_summary", {})
                resident["state_summary"]["commute_reliability"] = round(
                    min(1.0, resident["state_summary"].get("commute_reliability", 0.55) + 0.15 * intensity),
                    3,
                )
            return {
                "mode": "lever",
                "lever": lever,
                "district_id": district_id,
                "institutions_touched": len(institutions),
                "residents_touched": len(residents),
                "effective_intensity": round(intensity, 3),
                "rollout_share": round(rollout_share, 3),
                "delay_ticks": sequencing_offset,
                "interaction": interaction,
                "archetype_bias": round(archetype_bias, 3),
                "repetition_penalty": round(repetition_penalty, 3),
                "mistimed_stack_penalty": round(mistimed_stack_penalty, 3),
                "side_effects": AuraliteInterventionService._dedupe_notes(side_effects),
            }

        if lever == "expand_service_access":
            people = [p for p in world_state.get("persons", []) if p.get("district_id") == district_id]
            institutions = [
                i
                for i in world_state.get("institutions", [])
                if i.get("district_id") == district_id and i.get("institution_type") in {"healthcare", "service_access"}
            ]
            households = [h for h in world_state.get("households", []) if h.get("district_id") == district_id]
            for person in people:
                person["service_access_score"] = round(min(1.0, person.get("service_access_score", 0.5) + 0.2 * intensity), 3)
                person.setdefault("social_context", {})
                person["social_context"]["support_index"] = round(min(1.0, person["social_context"].get("support_index", 0.45) + 0.07 * intensity), 3)
            for institution in institutions:
                institution["capacity"] = int(max(1, round(institution.get("capacity", 1) * (1 + 0.18 * intensity))))
                institution["access_score"] = round(min(1.0, institution.get("access_score", 0.5) + 0.16 * intensity), 3)
                arc = institution.setdefault("arc_state", {})
                arc["service_backlog"] = round(min(1.0, float(arc.get("service_backlog", 0.0)) + (0.12 * intensity)), 3)
                arc["overload_fatigue"] = round(min(1.0, float(arc.get("overload_fatigue", 0.0)) + (0.08 * intensity)), 3)
                side_effects.append("service expansion introduced short-term onboarding backlog.")
            for household in households:
                household.setdefault("context", {})
                household["context"]["service_access_score"] = round(
                    min(1.0, household["context"].get("service_access_score", 0.5) + 0.1 * intensity),
                    3,
                )
            spillover_rows = AuraliteInterventionService._apply_neighbor_spillover(world_state, district_id, intensity)
            side_effects.extend([row["note"] for row in spillover_rows])
            return {
                "mode": "lever",
                "lever": lever,
                "district_id": district_id,
                "residents_touched": len(people),
                "households_touched": len(households),
                "institutions_touched": len(institutions),
                "effective_intensity": round(intensity, 3),
                "rollout_share": round(rollout_share, 3),
                "delay_ticks": sequencing_offset,
                "interaction": interaction,
                "archetype_bias": round(archetype_bias, 3),
                "repetition_penalty": round(repetition_penalty, 3),
                "mistimed_stack_penalty": round(mistimed_stack_penalty, 3),
                "side_effects": AuraliteInterventionService._dedupe_notes(side_effects),
                "spillover": spillover_rows[:4],
            }

        return None

    @staticmethod
    def _targeted_aftermath(applied: list[dict], district_shifts: list[dict], aftermath_profile: dict) -> dict:
        district_ids = []
        institution_ids = []
        for item in applied:
            district_id = item.get("district_id")
            if district_id and district_id not in district_ids:
                district_ids.append(district_id)
            if item.get("target") == "institution" and item.get("id"):
                institution_ids.append(item["id"])

        ranked_shift_ids = [
            row.get("district_id")
            for row in sorted(
                district_shifts,
                key=lambda entry: abs(float(entry.get("pressure_delta", 0.0))) + abs(float(entry.get("service_access_delta", 0.0))),
                reverse=True,
            )[:2]
            if row.get("district_id")
        ]
        for district_id in ranked_shift_ids:
            if district_id not in district_ids:
                district_ids.append(district_id)
        leverage_modes = [item.get("lever") for item in applied if item.get("mode") == "lever" and item.get("lever")]
        interaction_rows = [item.get("interaction") or {} for item in applied if item.get("mode") == "lever"]
        interaction_bonus = sum(float(row.get("synergy_bonus", 0.0)) for row in interaction_rows)
        interaction_penalty = sum(float(row.get("conflict_penalty", 0.0)) for row in interaction_rows)
        repetition_penalty = sum(float(item.get("repetition_penalty", 0.0)) for item in applied if item.get("mode") == "lever")
        mistimed_stack_penalty = sum(float(item.get("mistimed_stack_penalty", 0.0)) for item in applied if item.get("mode") == "lever")
        rollout_share = (
            sum(float(item.get("rollout_share", 1.0)) for item in applied if item.get("mode") == "lever")
            / max(1, len(leverage_modes))
        )
        delay_ticks = max([int(item.get("delay_ticks", 0)) for item in applied if item.get("mode") == "lever"] or [0])
        dominant_lever = leverage_modes[0] if leverage_modes else None
        taxonomy = AuraliteInterventionService._lever_taxonomy(dominant_lever)
        return {
            "district_ids": district_ids[:4],
            "institution_ids": institution_ids[:6],
            "amplitude": round(
                max(0.0, min(1.0, float(aftermath_profile.get("amplitude", 0.0)) * rollout_share * (1.0 + interaction_bonus - interaction_penalty))),
                3,
            ),
            "persistence_ticks": int(
                max(
                    1,
                    round(
                        int(aftermath_profile.get("persistence_ticks", taxonomy.get("duration_ticks", 1)))
                        * max(0.7, 1.0 + interaction_bonus * 0.8 - interaction_penalty),
                    ),
                )
            ),
            "lag_ticks": int(taxonomy.get("lag_ticks", 0)) + delay_ticks,
            "fade_per_tick": round(float(aftermath_profile.get("fade_per_tick", taxonomy.get("fade_per_tick", 0.12))), 3),
            "reversal_risk": round(
                min(
                    1.0,
                    float(aftermath_profile.get("reversal_risk", 0.0))
                    + float(taxonomy.get("base_backfire_risk", 0.0)) * 0.4
                    + interaction_penalty * 0.6,
                    + min(0.26, repetition_penalty * 0.45),
                    + min(0.28, mistimed_stack_penalty * 0.52),
                ),
                3,
            ),
            "interaction_trace": {
                "synergy_bonus": round(interaction_bonus, 3),
                "conflict_penalty": round(interaction_penalty, 3),
                "repetition_penalty": round(repetition_penalty, 3),
                "mistimed_stack_penalty": round(mistimed_stack_penalty, 3),
            },
            "taxonomy": taxonomy,
        }

    @staticmethod
    def _lever_taxonomy(lever: str | None) -> dict:
        if not lever:
            return {}
        return dict(AuraliteInterventionService.LEVER_TAXONOMY.get(lever, {}))

    @staticmethod
    def _backfire_seed(intervention_id: str | None, district_id: str | None) -> float:
        seed = f"{intervention_id or 'unknown'}:{district_id or 'all'}"
        return (sum(ord(ch) for ch in seed) % 1000) / 1000.0

    @staticmethod
    def _next_active_aftermath(existing: list[dict], record: dict | None) -> list[dict]:
        carried = []
        for entry in existing[-20:]:
            if not isinstance(entry, dict):
                continue
            lag_remaining = max(0, int(entry.get("lag_ticks_remaining", 0)))
            ticks_remaining = int(entry.get("ticks_remaining", 0))
            if lag_remaining > 0:
                carried.append({**entry, "lag_ticks_remaining": lag_remaining - 1})
                continue
            ticks_remaining -= 1
            if ticks_remaining <= 0:
                continue
            fade = max(0.0, min(1.0, float(entry.get("fade_per_tick", 0.12))))
            amplitude = float(entry.get("amplitude", 0.0))
            next_amplitude = max(0.0, amplitude * (1.0 - fade))
            backfire_risk = max(0.0, min(1.0, float(entry.get("reversal_risk", 0.0))))
            if entry.get("backfire_pending") and AuraliteInterventionService._backfire_seed(entry.get("intervention_id"), entry.get("district_id")) < backfire_risk:
                next_amplitude = min(1.0, next_amplitude + (backfire_risk * 0.08))
            carried.append({
                **entry,
                "ticks_remaining": ticks_remaining,
                "amplitude": round(next_amplitude, 3),
                "backfire_pending": False,
            })

        if not record:
            return carried[-24:]
        effects = (record.get("effects") or {})
        profile = effects.get("aftermath_profile") or {}
        targeted = effects.get("targeted_aftermath") or {}
        taxonomy = targeted.get("taxonomy") or {}
        interaction_trace = targeted.get("interaction_trace") or {}
        lag_ticks = int(targeted.get("lag_ticks", taxonomy.get("lag_ticks", 0)))
        for district_id in targeted.get("district_ids", []) or [None]:
            carried.append({
                "intervention_id": record.get("intervention_id"),
                "district_id": district_id,
                "amplitude": round(float(profile.get("amplitude", 0.0)), 3),
                "ticks_remaining": int(profile.get("persistence_ticks", taxonomy.get("duration_ticks", 1))),
                "lag_ticks_remaining": max(0, lag_ticks),
                "fade_per_tick": round(float(profile.get("fade_per_tick", taxonomy.get("fade_per_tick", 0.12))), 3),
                "reversal_risk": round(float(profile.get("reversal_risk", taxonomy.get("base_backfire_risk", 0.0))), 3),
                "backfire_pending": float(profile.get("reversal_risk", 0.0)) > 0.38,
                "taxonomy": taxonomy,
                "interaction_trace": interaction_trace,
            })
        return carried[-24:]

    @staticmethod
    def _interaction_trace(applied: list[dict]) -> dict:
        lever_rows = [item for item in applied if item.get("mode") == "lever"]
        if not lever_rows:
            return {}
        synergy = sum(float((item.get("interaction") or {}).get("synergy_bonus", 0.0)) for item in lever_rows)
        conflict = sum(float((item.get("interaction") or {}).get("conflict_penalty", 0.0)) for item in lever_rows)
        repetition = sum(float(item.get("repetition_penalty", 0.0)) for item in lever_rows)
        mistimed = sum(float(item.get("mistimed_stack_penalty", 0.0)) for item in lever_rows)
        return {
            "synergy_bonus": round(synergy, 3),
            "conflict_penalty": round(conflict, 3),
            "repetition_penalty": round(repetition, 3),
            "mistimed_stack_penalty": round(mistimed, 3),
            "net_multiplier": round(max(0.0, 1.0 + synergy - conflict - repetition - mistimed), 3),
            "stacked_levers": [item.get("lever") for item in lever_rows if item.get("lever")],
        }

    @staticmethod
    def _resolve_interaction(lever: str | None, district_id: str | None, lever_plan: list[dict], notes: str = "") -> dict:
        if not lever:
            return {"synergy_bonus": 0.0, "conflict_penalty": 0.0, "drivers": []}
        siblings = [
            row for row in lever_plan
            if row.get("lever") and row.get("lever") != lever and row.get("district_id") == district_id
        ]
        synergy_bonus = 0.0
        conflict_penalty = 0.0
        drivers = []
        for row in siblings:
            pair = (lever, row.get("lever"))
            reverse_pair = (row.get("lever"), lever)
            matrix = AuraliteInterventionService.INTERACTION_MATRIX.get(pair) or AuraliteInterventionService.INTERACTION_MATRIX.get(reverse_pair) or {}
            if matrix.get("synergy"):
                synergy_bonus += float(matrix.get("synergy", 0.0))
                drivers.append(f"synergy:{lever}+{row.get('lever')}")
            if matrix.get("sequencing_bonus"):
                delay = int(row.get("delay_ticks", 0))
                if delay > 0:
                    synergy_bonus += float(matrix.get("sequencing_bonus", 0.0))
                    drivers.append(f"sequencing_bonus:{lever}+{row.get('lever')}")
            if matrix.get("cannibalization"):
                conflict_penalty += float(matrix.get("cannibalization", 0.0))
                drivers.append(f"cannibalization:{lever}+{row.get('lever')}")
        if "budget_austerity" in (notes or "").lower():
            conflict_penalty += 0.07
            drivers.append("context:budget_austerity")
        return {
            "synergy_bonus": round(min(0.35, synergy_bonus), 3),
            "conflict_penalty": round(min(0.35, conflict_penalty), 3),
            "drivers": drivers[:6],
        }

    @staticmethod
    def _archetype_bias(archetype: str | None, target_layer: str | None) -> float:
        if not archetype or not target_layer:
            return 1.0
        profile = AuraliteInterventionService.DISTRICT_ARCHETYPE_BIASES.get(archetype, {})
        return max(0.82, min(1.18, float(profile.get(target_layer, 1.0))))

    @staticmethod
    def _apply_neighbor_spillover(world_state: dict, district_id: str | None, intensity: float) -> list[dict]:
        if not district_id:
            return []
        districts = world_state.get("districts", [])
        neighbors = []
        for district in districts:
            if district.get("district_id") == district_id:
                continue
            ripple = ((district.get("derived_summary") or {}).get("ripple_context") or {})
            if district_id not in (ripple.get("neighbor_ids") or []):
                continue
            drag = max(0.0, min(0.06, intensity * 0.035))
            district["pressure_index"] = round(min(1.0, float(district.get("pressure_index", 0.0)) + drag), 3)
            neighbors.append(
                {
                    "district_id": district.get("district_id"),
                    "pressure_drag": round(drag, 3),
                    "note": "local service gains shifted short-term access load into adjacent districts.",
                }
            )
        return neighbors[:3]

    @staticmethod
    def _dedupe_notes(notes: list[str]) -> list[str]:
        deduped = []
        seen = set()
        for note in notes:
            if note in seen:
                continue
            seen.add(note)
            deduped.append(note)
        return deduped[:4]

    @staticmethod
    def _repetition_penalty(world_state: dict, lever: str | None, district_id: str | None) -> tuple[float, list[str]]:
        if not lever or not district_id:
            return 0.0, []
        history = ((world_state.get("intervention_state") or {}).get("history") or [])[-8:]
        matching_recent = 0
        for record in history:
            applied = ((record or {}).get("effects") or {}).get("applied") or []
            for item in applied:
                if item.get("mode") != "lever":
                    continue
                if item.get("lever") == lever and item.get("district_id") == district_id:
                    matching_recent += 1
                    break
        if matching_recent <= 1:
            return 0.0, []
        penalty = min(0.28, (matching_recent - 1) * 0.07)
        notes = ["repeated_same_lever_sequence_reduced_marginal_gain_and_raised_backfire_risk."]
        if matching_recent >= 3:
            notes.append("district_lever_fatigue_detected; consider alternating with supporting levers.")
        return round(penalty, 3), notes

    @staticmethod
    def _mistimed_stack_penalty(
        world_state: dict,
        lever: str | None,
        district_id: str | None,
        sequencing_offset: int,
        lever_plan: list[dict],
    ) -> tuple[float, str]:
        if not lever or not district_id:
            return 0.0, ""
        active = ((world_state.get("intervention_state") or {}).get("active_aftermath") or [])
        active_same_district = [
            row for row in active
            if isinstance(row, dict)
            and row.get("district_id") == district_id
            and int(row.get("lag_ticks_remaining", 0)) > 0
        ]
        delayed_levers = [
            row for row in lever_plan
            if row.get("lever")
            and row.get("district_id") == district_id
            and int(row.get("delay_ticks", 0)) > 0
        ]
        if sequencing_offset > 0 and active_same_district:
            return min(0.22, 0.08 + len(active_same_district) * 0.04), "new_delayed_change_stacked_onto_unresolved_lag_window; local_overload_risk_up."
        if sequencing_offset == 0 and len(delayed_levers) >= 2:
            return min(0.2, 0.05 + len(delayed_levers) * 0.03), "mixed_immediate_and_delayed_stack_detected; sequencing_coherence_weakened."
        return 0.0, ""

    @staticmethod
    def _intervention_sequence_comparison(baseline_state: dict, current_state: dict) -> dict:
        def summarize(state: dict) -> dict:
            history = ((state.get("intervention_state") or {}).get("history") or [])
            applied_levers = []
            repeated = 0
            delayed_change_count = 0
            mistimed_change_count = 0
            fatigue_signal_count = 0
            conflict_signal_count = 0
            for record in history[-8:]:
                applied = (((record or {}).get("effects") or {}).get("applied") or [])
                levers = [item.get("lever") for item in applied if item.get("mode") == "lever" and item.get("lever")]
                applied_levers.extend(levers)
                for item in applied:
                    if item.get("mode") != "lever":
                        continue
                    if int(item.get("delay_ticks", 0)) > 0:
                        delayed_change_count += 1
                    if float(item.get("mistimed_stack_penalty", 0.0)) > 0.0:
                        mistimed_change_count += 1
                    if float(item.get("repetition_penalty", 0.0)) > 0.0:
                        fatigue_signal_count += 1
                    if float((item.get("interaction") or {}).get("conflict_penalty", 0.0)) > 0.0:
                        conflict_signal_count += 1
            for idx in range(1, len(applied_levers)):
                if applied_levers[idx] == applied_levers[idx - 1]:
                    repeated += 1
            alternations = max(0, len(applied_levers) - 1 - repeated)
            unique_count = len({lever for lever in applied_levers if lever})
            return {
                "history_count": len(history),
                "recent_levers": applied_levers[-6:],
                "repeated_sequence_count": repeated,
                "alternating_sequence_count": alternations,
                "unique_lever_count": unique_count,
                "delayed_change_count": delayed_change_count,
                "mistimed_change_count": mistimed_change_count,
                "fatigue_signal_count": fatigue_signal_count,
                "conflict_signal_count": conflict_signal_count,
            }

        baseline = summarize(baseline_state)
        current = summarize(current_state)
        return {
            "baseline_recent_levers": baseline["recent_levers"],
            "current_recent_levers": current["recent_levers"],
            "delta_history_count": current["history_count"] - baseline["history_count"],
            "delta_repeated_sequence_count": current["repeated_sequence_count"] - baseline["repeated_sequence_count"],
            "delta_alternating_sequence_count": current["alternating_sequence_count"] - baseline["alternating_sequence_count"],
            "delta_unique_lever_count": current["unique_lever_count"] - baseline["unique_lever_count"],
            "delta_delayed_change_count": current["delayed_change_count"] - baseline["delayed_change_count"],
            "delta_mistimed_change_count": current["mistimed_change_count"] - baseline["mistimed_change_count"],
            "delta_fatigue_signal_count": current["fatigue_signal_count"] - baseline["fatigue_signal_count"],
            "delta_conflict_signal_count": current["conflict_signal_count"] - baseline["conflict_signal_count"],
        }

    @staticmethod
    def _continuation_window_comparison(baseline_state: dict, current_state: dict) -> dict:
        baseline_active = ((baseline_state.get("intervention_state") or {}).get("active_aftermath") or [])
        current_active = ((current_state.get("intervention_state") or {}).get("active_aftermath") or [])
        baseline_prop = baseline_state.get("propagation_state", {}) or {}
        current_prop = current_state.get("propagation_state", {}) or {}
        baseline_rollup = baseline_prop.get("continuation_rollup", {}) or {}
        current_rollup = current_prop.get("continuation_rollup", {}) or {}
        baseline_split = ((((baseline_state.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
        current_split = ((((current_state.get("city") or {}).get("world_metrics") or {}).get("local_vs_broad_pressure_split") or {}))
        return {
            "active_aftermath_delta": len(current_active) - len(baseline_active),
            "district_neighbor_events_delta": len((current_prop.get("district_neighbor_events") or [])) - len((baseline_prop.get("district_neighbor_events") or [])),
            "social_events_delta": len((current_prop.get("social_events") or [])) - len((baseline_prop.get("social_events") or [])),
            "scenario_outcome_signal_delta": len((((current_state.get("scenario_state") or {}).get("scenario_outcome") or {}).get("continuation_signals") or {}))
            - len((((baseline_state.get("scenario_state") or {}).get("scenario_outcome") or {}).get("continuation_signals") or {})),
            "continuation_rollup_delta": {
                "total_district_events": int(current_rollup.get("total_district_events", 0)) - int(baseline_rollup.get("total_district_events", 0)),
                "total_social_events": int(current_rollup.get("total_social_events", 0)) - int(baseline_rollup.get("total_social_events", 0)),
                "ticks_with_neighbor_pressure": int(current_rollup.get("ticks_with_neighbor_pressure", 0)) - int(baseline_rollup.get("ticks_with_neighbor_pressure", 0)),
                "ticks_with_social_propagation": int(current_rollup.get("ticks_with_social_propagation", 0)) - int(baseline_rollup.get("ticks_with_social_propagation", 0)),
            },
            "recovery_lag_delta": {
                "household_recovery_lag_index": round(
                    float(current_split.get("household_recovery_lag_index", 0.0))
                    - float(baseline_split.get("household_recovery_lag_index", 0.0)),
                    3,
                ),
                "institution_recovery_lag_index": round(
                    float(current_split.get("institution_recovery_lag_index", 0.0))
                    - float(baseline_split.get("institution_recovery_lag_index", 0.0)),
                    3,
                ),
                "household_relief_interruption_index": round(
                    float(current_split.get("household_relief_interruption_index", 0.0))
                    - float(baseline_split.get("household_relief_interruption_index", 0.0)),
                    3,
                ),
            },
        }

    @staticmethod
    def _strategy_diagnostics(delta: dict, sequence_comparison: dict, continuation_comparison: dict) -> dict:
        pressure = float(delta.get("household_pressure_index", 0.0))
        service = float(delta.get("service_access_score", 0.0))
        stressed = float(delta.get("stressed_districts", 0.0))
        repeated = int(sequence_comparison.get("delta_repeated_sequence_count", 0))
        alternating = int(sequence_comparison.get("delta_alternating_sequence_count", 0))
        fatigue = int(sequence_comparison.get("delta_fatigue_signal_count", 0))
        mistimed = int(sequence_comparison.get("delta_mistimed_change_count", 0))
        continuation_neighbor = int((continuation_comparison.get("continuation_rollup_delta") or {}).get("ticks_with_neighbor_pressure", 0))
        lag_delta = continuation_comparison.get("recovery_lag_delta") or {}
        recovery_lag_signal = (
            max(0.0, float(lag_delta.get("household_recovery_lag_index", 0.0)))
            + max(0.0, float(lag_delta.get("institution_recovery_lag_index", 0.0)))
            + (max(0.0, float(lag_delta.get("household_relief_interruption_index", 0.0))) * 0.25)
        )
        local_win_broad_miss = service > 0.015 and (pressure >= -0.005 or stressed > 0.0)
        overload_backfire = pressure > 0.0 and (fatigue > 0 or mistimed > 0 or repeated > 0)
        return {
            "local_win_broad_miss": local_win_broad_miss,
            "overload_backfire_risk": overload_backfire,
            "sequence_regime": "alternating_complementary" if alternating > repeated else "repeated_or_flat",
            "continuation_drag_regime": (
                "neighbor_drag_dominant"
                if continuation_neighbor > 0
                else "contained_or_flat"
            ),
            "sequence_fatigue_signal": max(0, fatigue + repeated - alternating),
            "timing_mismatch_signal": max(0, mistimed + int(sequence_comparison.get("delta_delayed_change_count", 0)) - alternating),
            "recovery_lag_signal": round(recovery_lag_signal, 3),
        }

    @staticmethod
    def _checkpoint_readback(sequence_comparison: dict, continuation_comparison: dict, strategy_diagnostics: dict) -> dict:
        continuation_rollup_delta = continuation_comparison.get("continuation_rollup_delta") or {}
        return {
            "checkpoint_status": (
                "continuation_drag"
                if strategy_diagnostics.get("continuation_drag_regime") == "neighbor_drag_dominant"
                else "stable_or_localized"
            ),
            "sequence_signal": strategy_diagnostics.get("sequence_regime", "unknown"),
            "fatigue_signal": int(strategy_diagnostics.get("sequence_fatigue_signal", 0)),
            "timing_mismatch_signal": int(strategy_diagnostics.get("timing_mismatch_signal", 0)),
            "continuation_neighbor_drag_ticks": int(continuation_rollup_delta.get("ticks_with_neighbor_pressure", 0)),
            "continuation_social_drag_ticks": int(continuation_rollup_delta.get("ticks_with_social_propagation", 0)),
            "active_aftermath_delta": int(continuation_comparison.get("active_aftermath_delta", 0)),
            "sequence_delta_history_count": int(sequence_comparison.get("delta_history_count", 0)),
            "recovery_lag_signal": float(strategy_diagnostics.get("recovery_lag_signal", 0.0)),
            "recovery_lag_regime": (
                "lagged_recovery"
                if float(strategy_diagnostics.get("recovery_lag_signal", 0.0)) >= 0.1
                else "contained_recovery_lag"
            ),
        }

    @staticmethod
    def _operator_compare_lines(strategy_diagnostics: dict, sequence_comparison: dict, continuation_comparison: dict) -> list[str]:
        lines = []
        if strategy_diagnostics.get("local_win_broad_miss"):
            lines.append("Local relief gained traction, but citywide pressure did not fall with it.")
        if strategy_diagnostics.get("overload_backfire_risk"):
            lines.append("Sequence shows overload/backfire pressure from repeated or mistimed intervention cadence.")
        if int(strategy_diagnostics.get("sequence_fatigue_signal", 0)) > 0:
            lines.append("Repeated same-lever usage is generating visible fatigue versus complementary alternation.")
        if int(strategy_diagnostics.get("timing_mismatch_signal", 0)) > 0:
            lines.append("Delayed and immediate levers are misaligned; sequencing mismatch is suppressing follow-through.")
        if int((continuation_comparison.get("continuation_rollup_delta") or {}).get("ticks_with_neighbor_pressure", 0)) > 0:
            lines.append("Continuation rollup shows persistent neighbor-pressure drag after intervention windows.")
        if float(strategy_diagnostics.get("recovery_lag_signal", 0.0)) >= 0.1:
            lines.append("Nominal service relief is not yet converting into durable household/institution recovery momentum.")
        if not lines:
            lines.append("No dominant divergence driver detected; continue monitoring sequence and continuation signals.")
        return lines[:4]

    @staticmethod
    def _path_readback(baseline_state: dict, current_state: dict, baseline_label: str, current_label: str) -> dict:
        baseline_scenario = baseline_state.get("scenario_state") or {}
        current_scenario = current_state.get("scenario_state") or {}
        baseline_kind = "snapshot" if baseline_label.startswith("snapshot:") else "live"
        current_kind = "snapshot" if current_label.startswith("snapshot:") else "live"
        baseline_snapshot_id = (
            baseline_label.split("snapshot:", 1)[1]
            if baseline_kind == "snapshot" and ":" in baseline_label
            else baseline_scenario.get("baseline_snapshot_id")
        )
        current_snapshot_id = (
            current_label.split("snapshot:", 1)[1]
            if current_kind == "snapshot" and ":" in current_label
            else None
        )
        return {
            "baseline_path_kind": baseline_kind,
            "current_path_kind": current_kind,
            "baseline_snapshot_id": baseline_snapshot_id,
            "current_snapshot_id": current_snapshot_id,
            "baseline_scenario_name": baseline_scenario.get("active_scenario_name", "default-baseline"),
            "current_scenario_name": current_scenario.get("active_scenario_name", "default-baseline"),
            "continuation_mode": "checkpoint_compare" if baseline_kind == "snapshot" else "live_compare",
        }
