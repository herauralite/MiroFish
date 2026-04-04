from __future__ import annotations

from datetime import datetime


class AuraliteReportingService:
    """Milestone 12 lightweight report assembly and saved insight helpers."""

    @staticmethod
    def assemble_report_artifacts(
        world_state: dict,
        world_artifact: dict,
        scenario_outcome: dict,
        intervention_artifact: dict,
        comparison_artifact: dict,
    ) -> dict:
        key_conditions = scenario_outcome.get("key_conditions", {})
        top_districts = scenario_outcome.get("top_shifted_districts", [])[:3]
        top_systems = scenario_outcome.get("top_system_contributors", [])[:3]

        compact = {
            "artifact_type": "scenario_insight_report",
            "scenario_name": scenario_outcome.get("scenario_name", "default-baseline"),
            "world_time": scenario_outcome.get("world_time") or world_artifact.get("world_time"),
            "condition_direction": scenario_outcome.get("condition_direction", "flat"),
            "what_happened": (scenario_outcome.get("why_changed") or ["No scenario-level shift detected yet."])[0],
            "districts_that_mattered": [
                {
                    "district_id": row.get("district_id"),
                    "name": row.get("name"),
                    "shift_score": row.get("shift_score", 0.0),
                    "pressure_delta": row.get("pressure_delta", 0.0),
                    "service_access_delta": row.get("service_access_delta", 0.0),
                }
                for row in top_districts
            ],
            "systems_that_mattered": top_systems,
            "conditions": {
                "employment_rate": key_conditions.get("employment_rate", {}),
                "household_pressure_index": key_conditions.get("household_pressure_index", {}),
                "service_access_score": key_conditions.get("service_access_score", {}),
                "social_support_score": key_conditions.get("social_support_score", {}),
            },
            "anchors": {
                "scenario_start": (scenario_outcome.get("comparison_views", {}).get("scenario_start_to_current") or {}).get("scenario_start_time"),
                "baseline_available": bool((scenario_outcome.get("comparison_views", {}).get("baseline_to_current") or {}).get("available")),
                "current_world_time": scenario_outcome.get("world_time"),
            },
            "evidence": {
                "world": world_artifact,
                "intervention": intervention_artifact,
                "comparison": comparison_artifact,
            },
        }

        report_state = world_state.setdefault("reporting_state", {})
        assembled_reports = report_state.setdefault("assembled_reports", {})
        assembled_reports["scenario_insight_report"] = compact
        assembled_reports["updated_at"] = datetime.utcnow().isoformat()
        return compact

    @staticmethod
    def build_saved_scenario_insight(world_state: dict, source: str, note: str = "") -> dict:
        scenario_state = world_state.setdefault("scenario_state", {})
        report = (world_state.get("reporting_state", {}).get("assembled_reports", {}) or {}).get("scenario_insight_report", {})
        if not report:
            report = {
                "scenario_name": scenario_state.get("active_scenario_name", "default-baseline"),
                "world_time": world_state.get("world", {}).get("current_time"),
                "condition_direction": "flat",
                "what_happened": "No assembled scenario insight available yet.",
                "districts_that_mattered": [],
                "systems_that_mattered": [],
            }

        insight = {
            "insight_id": f"insight_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            "saved_at": datetime.utcnow().isoformat(),
            "source": source,
            "note": note,
            "scenario_name": report.get("scenario_name", scenario_state.get("active_scenario_name", "default-baseline")),
            "world_time": report.get("world_time") or world_state.get("world", {}).get("current_time"),
            "condition_direction": report.get("condition_direction", "flat"),
            "what_happened": report.get("what_happened", "No scenario-level shift detected yet."),
            "districts_that_mattered": report.get("districts_that_mattered", [])[:3],
            "systems_that_mattered": report.get("systems_that_mattered", [])[:3],
            "conditions": report.get("conditions", {}),
            "anchors": report.get("anchors", {}),
        }

        scenario_state.setdefault("saved_insights", []).append(insight)
        scenario_state["saved_insights"] = scenario_state["saved_insights"][-30:]
        scenario_state["last_saved_insight_id"] = insight["insight_id"]
        return insight
