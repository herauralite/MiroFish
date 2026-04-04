from __future__ import annotations

from datetime import datetime

from ..models.auralite_intervention import AuraliteInterventionRecord


class AuraliteInterventionService:
    @staticmethod
    def apply_changes(world_state: dict, changes: list[dict], notes: str = "") -> tuple[dict, dict]:
        before = AuraliteInterventionService._world_summary(world_state)
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
        return world_state, record.to_dict()

    @staticmethod
    def enrich_record_with_after(record: dict, world_state: dict):
        before = (record.get("effects") or {}).get("before_summary") or {}
        after = AuraliteInterventionService._world_summary(world_state)
        record.setdefault("effects", {})
        record["effects"]["after_summary"] = after
        record["effects"]["delta_summary"] = AuraliteInterventionService._summary_delta(before, after)

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
            })
        delta["district_shifts"] = district_shifts
        return delta

    @staticmethod
    def _apply_lever(world_state: dict, change: dict) -> dict | None:
        lever = change.get("lever")
        district_id = change.get("district_id")
        intensity = max(0.0, min(1.0, float(change.get("intensity", 0.2))))

        if lever == "rebalance_housing_pressure":
            households = [h for h in world_state.get("households", []) if h.get("district_id") == district_id]
            for household in households:
                household["monthly_rent"] = round(max(300.0, household.get("monthly_rent", 0.0) * (1 - 0.15 * intensity)), 2)
                burden = household.get("housing_cost_burden", 0.0)
                household["housing_cost_burden"] = round(max(0.05, burden * (1 - 0.2 * intensity)), 3)
                household["pressure_index"] = round(max(0.05, household.get("pressure_index", 0.0) * (1 - 0.25 * intensity)), 3)
            return {"mode": "lever", "lever": lever, "district_id": district_id, "households_touched": len(households)}

        if lever == "boost_transit_service":
            institutions = [
                i for i in world_state.get("institutions", []) if i.get("district_id") == district_id and i.get("institution_type") == "transit"
            ]
            for institution in institutions:
                institution["access_score"] = round(min(1.0, institution.get("access_score", 0.5) + 0.25 * intensity), 3)
                institution["pressure_index"] = round(max(0.0, institution.get("pressure_index", 0.3) - 0.2 * intensity), 3)
            return {"mode": "lever", "lever": lever, "district_id": district_id, "institutions_touched": len(institutions)}

        if lever == "expand_service_access":
            people = [p for p in world_state.get("persons", []) if p.get("district_id") == district_id]
            for person in people:
                person["service_access_score"] = round(min(1.0, person.get("service_access_score", 0.5) + 0.2 * intensity), 3)
            return {"mode": "lever", "lever": lever, "district_id": district_id, "residents_touched": len(people)}

        return None
