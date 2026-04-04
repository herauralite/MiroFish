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
            propagation_state=world_state.get("propagation_state", {}),
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
            "scenario_outcome": AuraliteExplainabilityService._scenario_outcome_artifact(
                world_state=world_state,
                current_world=current_world,
                previous_world=previous_world,
            ),
            "last_intervention": AuraliteExplainabilityService._intervention_artifact(intervention_record),
            "latest_comparison_run": AuraliteExplainabilityService._comparison_artifact(comparison_report),
            "resident_focus": AuraliteExplainabilityService._resident_focus_artifact(world_state.get("persons", [])),
            "household_focus": AuraliteExplainabilityService._household_focus_artifact(world_state.get("households", [])),
        }
        world_state.setdefault("scenario_state", {})["run_summary"] = reporting_state["artifacts"]["scenario_outcome"]
        world_state.setdefault("scenario_state", {})["reporting_artifact_hint"] = (world_artifact.get("why_changed") or ["No dominant citywide shift detected."])[0]
        reporting_state["previous_world_summary"] = current_world
        reporting_state["previous_district_metrics"] = {
            d.get("district_id"): {
                "pressure_index": d.get("pressure_index", 0.0),
                "service_access_score": d.get("service_access_score", 0.0),
                "social_support_score": d.get("social_support_score", 0.0),
                "employment_rate": d.get("employment_rate", 0.0),
                "state_phase": d.get("state_phase", "steady"),
            }
            for d in world_state.get("districts", [])
        }
        reporting_state["previous_person_metrics"] = {
            person.get("person_id"): {
                "stress": float((person.get("state_summary") or {}).get("stress", 0.0)),
                "housing_stability": float(max(0.0, 1.0 - person.get("housing_burden_share", 0.0))),
                "employment_stability": 1.0 if person.get("employment_status") == "employed" else 0.0,
                "service_access": float(person.get("service_access_score", 0.5)),
                "social_support": float((person.get("social_context") or {}).get("support_index", 0.5)),
            }
            for person in world_state.get("persons", [])
        }
        reporting_state["previous_household_metrics"] = {
            hh.get("household_id"): {
                "stress": float((hh.get("context") or {}).get("stress_index", hh.get("pressure_index", 0.0))),
                "housing_stability": float((hh.get("context") or {}).get("housing_stability_index", max(0.0, 1.0 - hh.get("housing_cost_burden", 0.0)))),
                "employment_stability": float((hh.get("context") or {}).get("employment_stability_index", 0.0)),
                "service_access": float((hh.get("context") or {}).get("service_access_score", 0.5)),
                "social_support": float((hh.get("social_context") or {}).get("support_exposure", (hh.get("context") or {}).get("social_support_score", 0.5))),
            }
            for hh in world_state.get("households", [])
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
            "social_support_score": float(metrics.get("social_support_score", 0.0)),
            "stressed_districts": float((metrics.get("district_state_overview") or {}).get("stressed", 0.0)),
        }

    @staticmethod
    def _world_state_artifact(current_world: dict, previous_world: dict, districts: list[dict], propagation_state: dict) -> dict:
        delta = {
            key: round(current_world.get(key, 0.0) - float(previous_world.get(key, 0.0)), 3)
            for key in ["employment_rate", "avg_housing_burden", "household_pressure_index", "service_access_score", "social_support_score", "stressed_districts"]
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
        if delta["social_support_score"] > 0.01:
            summary_hooks.append("Social support networks strengthened and reduced spillover strain.")
        elif delta["social_support_score"] < -0.01:
            summary_hooks.append("Social support networks thinned, exposing households to higher strain spillover.")

        if not summary_hooks:
            summary_hooks.append("No dominant citywide shift detected; pressure remains distributed.")

        neighbor_events = len((propagation_state or {}).get("district_neighbor_events", []))
        social_events = len((propagation_state or {}).get("social_events", []))
        if neighbor_events or social_events:
            summary_hooks.append(
                f"Propagation scaffold tracked {neighbor_events} district-neighbor and {social_events} social spillover events."
            )

        return {
            "artifact_type": "current_world_state",
            "world_time": current_world.get("world_time"),
            "what_changed": delta,
            "why_changed": summary_hooks,
            "top_system_contributors": contributors,
        }

    @staticmethod
    def _scenario_outcome_artifact(world_state: dict, current_world: dict, previous_world: dict) -> dict:
        districts = world_state.get("districts", [])
        delta = {
            key: round(current_world.get(key, 0.0) - float(previous_world.get(key, 0.0)), 3)
            for key in ["employment_rate", "avg_housing_burden", "household_pressure_index", "service_access_score", "social_support_score", "stressed_districts"]
        }
        condition_score = (
            delta["employment_rate"] * 1.2
            + delta["service_access_score"] * 1.0
            + delta["social_support_score"] * 0.8
            - delta["household_pressure_index"] * 1.2
            - delta["avg_housing_burden"] * 1.0
            - delta["stressed_districts"] * 0.7
        )
        if condition_score > 0.025:
            direction = "improved"
        elif condition_score < -0.025:
            direction = "worsened"
        elif abs(condition_score) < 0.008:
            direction = "flat"
        else:
            direction = "mixed"

        district_shifts = []
        for district in districts:
            change = (district.get("derived_summary", {}).get("causal_readout", {}) or {}).get("what_changed", {})
            pressure_delta = float(change.get("pressure_index", 0.0))
            service_delta = float(change.get("service_access_score", 0.0))
            support_delta = float(change.get("social_support_score", 0.0))
            composite = round(abs(pressure_delta) + abs(service_delta) + abs(support_delta), 3)
            district_shifts.append(
                {
                    "district_id": district.get("district_id"),
                    "name": district.get("name"),
                    "pressure_delta": round(pressure_delta, 3),
                    "service_access_delta": round(service_delta, 3),
                    "social_support_delta": round(support_delta, 3),
                    "shift_score": composite,
                }
            )
        top_shifted = sorted(district_shifts, key=lambda row: row["shift_score"], reverse=True)[:3]
        key_conditions = {
            "employment_rate": {"delta": delta["employment_rate"], "direction": AuraliteExplainabilityService._condition_direction(delta["employment_rate"])},
            "household_pressure_index": {"delta": delta["household_pressure_index"], "direction": AuraliteExplainabilityService._condition_direction(delta["household_pressure_index"], better_when_lower=True)},
            "service_access_score": {"delta": delta["service_access_score"], "direction": AuraliteExplainabilityService._condition_direction(delta["service_access_score"])},
            "social_support_score": {"delta": delta["social_support_score"], "direction": AuraliteExplainabilityService._condition_direction(delta["social_support_score"])},
        }

        summary_lines = [
            f"Run is {direction}: pressure {delta['household_pressure_index']:+.3f}, service {delta['service_access_score']:+.3f}, support {delta['social_support_score']:+.3f}.",
            "Largest district shifts: " + ", ".join(item.get("name", item.get("district_id", "unknown")) for item in top_shifted) if top_shifted else "Largest district shifts: none detected.",
        ]
        return {
            "artifact_type": "scenario_outcome",
            "scenario_name": (world_state.get("scenario_state", {}) or {}).get("active_scenario_name", "default-baseline"),
            "world_time": current_world.get("world_time"),
            "condition_direction": direction,
            "what_changed": delta,
            "key_conditions": key_conditions,
            "top_shifted_districts": top_shifted,
            "top_system_contributors": AuraliteExplainabilityService._top_system_contributors(districts),
            "why_changed": summary_lines,
        }

    @staticmethod
    def _condition_direction(delta: float, better_when_lower: bool = False) -> str:
        if abs(delta) < 0.01:
            return "flat"
        improving = delta < 0 if better_when_lower else delta > 0
        return "improving" if improving else "worsening"

    @staticmethod
    def _district_causal_readouts(districts: list[dict], previous_districts: dict) -> dict:
        readouts = {}
        for district in districts:
            district_id = district.get("district_id")
            previous = previous_districts.get(district_id, {})
            pressure_delta = round(district.get("pressure_index", 0.0) - float(previous.get("pressure_index", 0.0)), 3)
            service_delta = round(district.get("service_access_score", 0.0) - float(previous.get("service_access_score", 0.0)), 3)
            social_delta = round(district.get("social_support_score", 0.0) - float(previous.get("social_support_score", 0.0)), 3)
            employment_delta = round(district.get("employment_rate", 0.0) - float(previous.get("employment_rate", 0.0)), 3)

            why_changed = list((district.get("derived_summary", {}) or {}).get("pressure_drivers", []))[:2]
            propagation_context = (district.get("derived_summary", {}) or {}).get("propagation_context", {})
            incoming_neighbor_pressure = float(propagation_context.get("incoming_neighbor_pressure", 0.0))
            if abs(incoming_neighbor_pressure) >= 0.012:
                direction = "upward" if incoming_neighbor_pressure > 0 else "downward"
                why_changed.append(f"Neighbor spillover pushed a {direction} pressure contribution this tick.")
            if not why_changed:
                why_changed = ["No dominant local driver identified yet."]

            top_systems = AuraliteExplainabilityService._district_top_systems(district)
            readouts[district_id] = {
                "what_changed": {
                    "pressure_index": pressure_delta,
                    "service_access_score": service_delta,
                    "social_support_score": social_delta,
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
            "social_support_gap": 0.0,
            "landlord_pressure": 0.0,
            "employer_pressure": 0.0,
        }
        for district in districts:
            inst = district.get("institution_summary", {})
            sums["household_pressure"] += float(district.get("household_pressure", 0.0))
            sums["employment_pressure"] += float(district.get("employment_pressure", 0.0))
            sums["service_gap"] += 1.0 - float(district.get("service_access_score", 1.0))
            sums["transit_gap"] += 1.0 - float(district.get("transit_reliability", 1.0))
            sums["social_support_gap"] += 1.0 - float(district.get("social_support_score", 1.0))
            sums["landlord_pressure"] += float(inst.get("landlord_pressure", 0.0))
            sums["employer_pressure"] += float(inst.get("employer_pressure", 0.0))

        contributor_map = {
            "household_pressure": "household",
            "employment_pressure": "employment",
            "service_gap": "service_access",
            "transit_gap": "transit",
            "social_support_gap": "social_support",
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
            ("social_support", 1.0 - float(district.get("social_support_score", 1.0))),
            ("landlord", float(institution_summary.get("landlord_pressure", 0.0))),
            ("employer", float(institution_summary.get("employer_pressure", 0.0))),
        ]
        return [{"system": k, "score": round(v, 3)} for k, v in sorted(values, key=lambda item: item[1], reverse=True)[:3]]

    @staticmethod
    def _resident_focus_artifact(persons: list[dict]) -> dict:
        if not persons:
            return {
                "artifact_type": "resident_focus",
                "status": "none",
                "what_changed": {},
                "why_changed": ["No resident records available yet."],
                "top_system_contributors": [],
            }
        resident = max(persons, key=lambda p: (p.get("state_summary") or {}).get("stress", 0.0))
        readout = (resident.get("derived_summary") or {}).get("causal_readout", {})
        return {
            "artifact_type": "resident_focus",
            "resident_id": resident.get("person_id"),
            "label": resident.get("name"),
            "what_changed": readout.get("what_changed", {}),
            "why_changed": readout.get("why_changed", ["No dominant resident-level driver identified."]),
            "top_system_contributors": readout.get("top_system_contributors", []),
        }

    @staticmethod
    def _household_focus_artifact(households: list[dict]) -> dict:
        if not households:
            return {
                "artifact_type": "household_focus",
                "status": "none",
                "what_changed": {},
                "why_changed": ["No household records available yet."],
                "top_system_contributors": [],
            }
        household = max(households, key=lambda h: (h.get("context") or {}).get("stress_index", h.get("pressure_index", 0.0)))
        readout = (household.get("derived_summary") or {}).get("causal_readout", {})
        return {
            "artifact_type": "household_focus",
            "household_id": household.get("household_id"),
            "label": household.get("household_type"),
            "what_changed": readout.get("what_changed", {}),
            "why_changed": readout.get("why_changed", ["No dominant household-level driver identified."]),
            "top_system_contributors": readout.get("top_system_contributors", []),
        }
