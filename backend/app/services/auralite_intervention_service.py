from __future__ import annotations

from datetime import datetime

from ..models.auralite_intervention import AuraliteInterventionRecord


class AuraliteInterventionService:


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

        applied = []
        for change in changes:
            if "lever" in change:
                leverage_effect = AuraliteInterventionService._apply_lever(world_state, change)
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
    def _apply_lever(world_state: dict, change: dict) -> dict | None:
        lever = change.get("lever")
        district_id = change.get("district_id")
        intensity = max(0.0, min(1.0, float(change.get("intensity", 0.2))))

        if lever == "rebalance_housing_pressure":
            households = [h for h in world_state.get("households", []) if h.get("district_id") == district_id]
            institutions = [i for i in world_state.get("institutions", []) if i.get("district_id") == district_id and i.get("institution_type") == "landlord"]
            for household in households:
                household["monthly_rent"] = round(max(300.0, household.get("monthly_rent", 0.0) * (1 - 0.15 * intensity)), 2)
                burden = household.get("housing_cost_burden", 0.0)
                household["housing_cost_burden"] = round(max(0.05, burden * (1 - 0.2 * intensity)), 3)
                household["pressure_index"] = round(max(0.05, household.get("pressure_index", 0.0) * (1 - 0.25 * intensity)), 3)
            for institution in institutions:
                institution["pressure_index"] = round(max(0.0, institution.get("pressure_index", 0.4) - 0.18 * intensity), 3)
                institution["access_score"] = round(min(1.0, institution.get("access_score", 0.5) + 0.1 * intensity), 3)
            return {
                "mode": "lever",
                "lever": lever,
                "district_id": district_id,
                "households_touched": len(households),
                "institutions_touched": len(institutions),
            }

        if lever == "boost_transit_service":
            institutions = [
                i for i in world_state.get("institutions", []) if i.get("district_id") == district_id and i.get("institution_type") == "transit"
            ]
            residents = [p for p in world_state.get("persons", []) if p.get("district_id") == district_id]
            for institution in institutions:
                institution["access_score"] = round(min(1.0, institution.get("access_score", 0.5) + 0.25 * intensity), 3)
                institution["pressure_index"] = round(max(0.0, institution.get("pressure_index", 0.3) - 0.2 * intensity), 3)
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
            for household in households:
                household.setdefault("context", {})
                household["context"]["service_access_score"] = round(
                    min(1.0, household["context"].get("service_access_score", 0.5) + 0.1 * intensity),
                    3,
                )
            return {
                "mode": "lever",
                "lever": lever,
                "district_id": district_id,
                "residents_touched": len(people),
                "households_touched": len(households),
                "institutions_touched": len(institutions),
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
        dominant_lever = leverage_modes[0] if leverage_modes else None
        taxonomy = AuraliteInterventionService._lever_taxonomy(dominant_lever)
        return {
            "district_ids": district_ids[:4],
            "institution_ids": institution_ids[:6],
            "amplitude": round(float(aftermath_profile.get("amplitude", 0.0)), 3),
            "persistence_ticks": int(aftermath_profile.get("persistence_ticks", taxonomy.get("duration_ticks", 1))),
            "lag_ticks": int(taxonomy.get("lag_ticks", 0)),
            "fade_per_tick": round(float(aftermath_profile.get("fade_per_tick", taxonomy.get("fade_per_tick", 0.12))), 3),
            "reversal_risk": round(min(1.0, float(aftermath_profile.get("reversal_risk", 0.0)) + float(taxonomy.get("base_backfire_risk", 0.0)) * 0.4), 3),
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
            })
        return carried[-24:]
