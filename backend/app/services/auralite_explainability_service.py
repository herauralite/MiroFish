from __future__ import annotations


class AuraliteExplainabilityService:
    @staticmethod
    def augment_world_state(world_state: dict):
        reporting_state = world_state.setdefault("reporting_state", {})
        previous_world = reporting_state.get("previous_world_summary", {})
        previous_districts = reporting_state.get("previous_district_metrics", {})

        current_world = AuraliteExplainabilityService._world_metrics_snapshot(world_state)
        world_artifact = AuraliteExplainabilityService._world_state_artifact(
            current_world=current_world,
            previous_world=previous_world,
            districts=world_state.get("districts", []),
        )
        district_readouts = AuraliteExplainabilityService._district_causal_readouts(
            districts=world_state.get("districts", []),
            previous_districts=previous_districts,
        )

        for district in world_state.get("districts", []):
            district_id = district.get("district_id")
            district.setdefault("derived_summary", {})
            district["derived_summary"]["causal_readout"] = district_readouts.get(district_id, {})

        comparison_report = (world_state.get("scenario_state", {}).get("last_comparison_report") or {}).get("report", {})
        last_intervention = (world_state.get("intervention_state", {}).get("history") or [])[-1:] or []
        intervention_record = last_intervention[0] if last_intervention else {}

        reporting_state["artifacts"] = {
            "current_world_state": world_artifact,
            "last_intervention": AuraliteExplainabilityService._intervention_artifact(intervention_record),
            "latest_comparison_run": AuraliteExplainabilityService._comparison_artifact(comparison_report),
        }
        world_state.setdefault("scenario_state", {})["reporting_artifact_hint"] = (world_artifact.get("why_changed") or ["No dominant citywide shift detected."])[0]
        reporting_state["previous_world_summary"] = current_world
        reporting_state["previous_district_metrics"] = {
            d.get("district_id"): {
                "pressure_index": d.get("pressure_index", 0.0),
                "service_access_score": d.get("service_access_score", 0.0),
                "employment_rate": d.get("employment_rate", 0.0),
                "state_phase": d.get("state_phase", "steady"),
            }
            for d in world_state.get("districts", [])
        }

    @staticmethod
    def _world_metrics_snapshot(world_state: dict) -> dict:
        metrics = world_state.get("city", {}).get("world_metrics", {})
        return {
            "world_time": world_state.get("world", {}).get("current_time"),
            "employment_rate": float(metrics.get("employment_rate", 0.0)),
            "avg_housing_burden": float(metrics.get("avg_housing_burden", 0.0)),
            "household_pressure_index": float(metrics.get("household_pressure_index", 0.0)),
            "service_access_score": float(metrics.get("service_access_score", 0.0)),
            "stressed_districts": float((metrics.get("district_state_overview") or {}).get("stressed", 0.0)),
        }

    @staticmethod
    def _world_state_artifact(current_world: dict, previous_world: dict, districts: list[dict]) -> dict:
        delta = {
            key: round(current_world.get(key, 0.0) - float(previous_world.get(key, 0.0)), 3)
            for key in ["employment_rate", "avg_housing_burden", "household_pressure_index", "service_access_score", "stressed_districts"]
        }
        contributors = AuraliteExplainabilityService._top_system_contributors(districts)
        summary_hooks = []
        if delta["household_pressure_index"] > 0.01:
            summary_hooks.append("Household pressure rose versus the previous simulation state.")
        elif delta["household_pressure_index"] < -0.01:
            summary_hooks.append("Household pressure eased versus the previous simulation state.")

        if delta["service_access_score"] > 0.01:
            summary_hooks.append("Service access improved and buffered stress propagation.")
        elif delta["service_access_score"] < -0.01:
            summary_hooks.append("Service access weakened, increasing friction for vulnerable households.")

        if not summary_hooks:
            summary_hooks.append("No dominant citywide shift detected; pressure remains distributed.")

        return {
            "artifact_type": "current_world_state",
            "world_time": current_world.get("world_time"),
            "what_changed": delta,
            "why_changed": summary_hooks,
            "top_system_contributors": contributors,
        }

    @staticmethod
    def _district_causal_readouts(districts: list[dict], previous_districts: dict) -> dict:
        readouts = {}
        for district in districts:
            district_id = district.get("district_id")
            previous = previous_districts.get(district_id, {})
            pressure_delta = round(district.get("pressure_index", 0.0) - float(previous.get("pressure_index", 0.0)), 3)
            service_delta = round(district.get("service_access_score", 0.0) - float(previous.get("service_access_score", 0.0)), 3)
            employment_delta = round(district.get("employment_rate", 0.0) - float(previous.get("employment_rate", 0.0)), 3)

            why_changed = list((district.get("derived_summary", {}) or {}).get("pressure_drivers", []))[:2]
            if not why_changed:
                why_changed = ["No dominant local driver identified yet."]

            top_systems = AuraliteExplainabilityService._district_top_systems(district)
            readouts[district_id] = {
                "what_changed": {
                    "pressure_index": pressure_delta,
                    "service_access_score": service_delta,
                    "employment_rate": employment_delta,
                    "state_phase": f"{previous.get('state_phase', 'n/a')} -> {district.get('state_phase', 'steady')}",
                },
                "why_changed": why_changed,
                "top_system_contributors": top_systems,
            }
        return readouts

    @staticmethod
    def _intervention_artifact(intervention_record: dict) -> dict:
        if not intervention_record:
            return {
                "artifact_type": "last_intervention",
                "status": "none",
                "what_changed": {},
                "why_changed": ["No intervention has been applied yet."],
                "top_system_contributors": [],
            }

        effects = intervention_record.get("effects", {})
        delta = effects.get("delta_summary", {})
        applied = effects.get("applied", [])
        touched_systems = sorted({item.get("lever") or item.get("target") for item in applied if (item.get("lever") or item.get("target"))})
        return {
            "artifact_type": "last_intervention",
            "intervention_id": intervention_record.get("intervention_id"),
            "applied_at": intervention_record.get("applied_at"),
            "what_changed": {
                "household_pressure_index": delta.get("household_pressure_index", 0.0),
                "service_access_score": delta.get("service_access_score", 0.0),
                "stressed_districts": delta.get("stressed_districts", 0.0),
            },
            "why_changed": [hook.get("text") for hook in effects.get("aftermath_hooks", [])][:3] or ["Intervention applied; no dominant aftermath hook yet."],
            "top_system_contributors": touched_systems[:4],
        }

    @staticmethod
    def _comparison_artifact(comparison_report: dict) -> dict:
        if not comparison_report:
            return {
                "artifact_type": "latest_comparison_run",
                "status": "none",
                "what_changed": {},
                "why_changed": ["No baseline comparison run yet."],
                "top_system_contributors": [],
            }

        delta = comparison_report.get("delta_summary", {})
        district_shifts = delta.get("district_shifts", [])
        dominant_districts = sorted(
            district_shifts,
            key=lambda shift: abs(float(shift.get("pressure_delta", 0.0))),
            reverse=True,
        )[:3]
        return {
            "artifact_type": "latest_comparison_run",
            "generated_at": comparison_report.get("generated_at"),
            "baseline_label": comparison_report.get("baseline_label"),
            "current_label": comparison_report.get("current_label"),
            "what_changed": {
                "household_pressure_index": delta.get("household_pressure_index", 0.0),
                "service_access_score": delta.get("service_access_score", 0.0),
                "employment_rate": delta.get("employment_rate", 0.0),
                "stressed_districts": delta.get("stressed_districts", 0.0),
            },
            "why_changed": [hook.get("text") for hook in comparison_report.get("aftermath_hooks", [])][:3] or ["Comparison generated; no single driver dominates yet."],
            "top_system_contributors": [
                {
                    "district_id": district.get("district_id"),
                    "name": district.get("name"),
                    "pressure_delta": district.get("pressure_delta", 0.0),
                }
                for district in dominant_districts
            ],
        }

    @staticmethod
    def _top_system_contributors(districts: list[dict]) -> list[dict]:
        if not districts:
            return []

        sums = {
            "household_pressure": 0.0,
            "employment_pressure": 0.0,
            "service_gap": 0.0,
            "transit_gap": 0.0,
            "landlord_pressure": 0.0,
            "employer_pressure": 0.0,
        }
        for district in districts:
            inst = district.get("institution_summary", {})
            sums["household_pressure"] += float(district.get("household_pressure", 0.0))
            sums["employment_pressure"] += float(district.get("employment_pressure", 0.0))
            sums["service_gap"] += 1.0 - float(district.get("service_access_score", 1.0))
            sums["transit_gap"] += 1.0 - float(district.get("transit_reliability", 1.0))
            sums["landlord_pressure"] += float(inst.get("landlord_pressure", 0.0))
            sums["employer_pressure"] += float(inst.get("employer_pressure", 0.0))

        contributor_map = {
            "household_pressure": "household",
            "employment_pressure": "employment",
            "service_gap": "service_access",
            "transit_gap": "transit",
            "landlord_pressure": "landlord",
            "employer_pressure": "employer",
        }
        ranked = sorted(sums.items(), key=lambda item: item[1], reverse=True)[:3]
        return [{"system": contributor_map[key], "score": round(value / max(1, len(districts)), 3)} for key, value in ranked]

    @staticmethod
    def _district_top_systems(district: dict) -> list[dict]:
        institution_summary = district.get("institution_summary", {})
        values = [
            ("household", float(district.get("household_pressure", 0.0))),
            ("employment", float(district.get("employment_pressure", 0.0))),
            ("service_access", 1.0 - float(district.get("service_access_score", 1.0))),
            ("transit", 1.0 - float(district.get("transit_reliability", 1.0))),
            ("landlord", float(institution_summary.get("landlord_pressure", 0.0))),
            ("employer", float(institution_summary.get("employer_pressure", 0.0))),
        ]
        return [{"system": k, "score": round(v, 3)} for k, v in sorted(values, key=lambda item: item[1], reverse=True)[:3]]
