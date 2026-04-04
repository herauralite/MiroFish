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
        artifacts = (world_state.get("reporting_state") or {}).get("artifacts", {})
        key_conditions = scenario_outcome.get("key_conditions", {})
        top_districts = scenario_outcome.get("top_shifted_districts", [])[:3]
        top_systems = scenario_outcome.get("top_system_contributors", [])[:3]
        drilldown = artifacts.get("outcome_drilldown", {})

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
            "residents_that_mattered": (drilldown.get("residents_that_mattered") or [])[:3],
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

        timeline = scenario_state.setdefault("timeline", [])
        next_order = len(timeline) + 1
        source_type = source.split("_", 1)[0] if source else "system"

        insight = {
            "insight_id": f"insight_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            "saved_at": datetime.utcnow().isoformat(),
            "source": source,
            "source_type": source_type,
            "note": note,
            "scenario_name": report.get("scenario_name", scenario_state.get("active_scenario_name", "default-baseline")),
            "world_time": report.get("world_time") or world_state.get("world", {}).get("current_time"),
            "condition_direction": report.get("condition_direction", "flat"),
            "direction": report.get("condition_direction", "flat"),
            "timeline_order": next_order,
            "what_happened": report.get("what_happened", "No scenario-level shift detected yet."),
            "districts_that_mattered": report.get("districts_that_mattered", [])[:3],
            "systems_that_mattered": report.get("systems_that_mattered", [])[:3],
            "conditions": report.get("conditions", {}),
            "anchors": report.get("anchors", {}),
            "filter_tags": {
                "source_type": source_type,
                "direction": report.get("condition_direction", "flat"),
                "scenario_name": report.get("scenario_name", scenario_state.get("active_scenario_name", "default-baseline")),
            },
        }

        scenario_state.setdefault("saved_insights", []).append(insight)
        scenario_state["saved_insights"] = scenario_state["saved_insights"][-30:]
        scenario_state["last_saved_insight_id"] = insight["insight_id"]
        scenario_state["insight_filter_catalog"] = AuraliteReportingService._build_insight_filter_catalog(
            scenario_state["saved_insights"],
        )
        AuraliteReportingService.record_scenario_moment(
            world_state=world_state,
            moment_type="insight_saved",
            source=source,
            payload={
                "insight_id": insight["insight_id"],
                "scenario_name": insight["scenario_name"],
                "direction": insight["direction"],
                "what_happened": insight["what_happened"],
            },
            note=note,
        )
        AuraliteReportingService.sync_reporting_history_views(world_state)
        return insight

    @staticmethod
    def record_scenario_moment(
        world_state: dict,
        moment_type: str,
        source: str,
        payload: dict | None = None,
        note: str = "",
    ) -> dict:
        scenario_state = world_state.setdefault("scenario_state", {})
        timeline = scenario_state.setdefault("timeline", [])
        category = AuraliteReportingService._moment_category(moment_type)
        payload = payload or {}
        replay_text = AuraliteReportingService._moment_replay_text(
            moment_type=moment_type,
            scenario_name=scenario_state.get("active_scenario_name", "default-baseline"),
            payload=payload,
            note=note,
        )
        moment = {
            "moment_id": f"moment_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            "recorded_at": datetime.utcnow().isoformat(),
            "world_time": world_state.get("world", {}).get("current_time"),
            "scenario_name": scenario_state.get("active_scenario_name", "default-baseline"),
            "moment_type": moment_type,
            "moment_category": category,
            "source": source,
            "source_type": source.split("_", 1)[0] if source else "system",
            "order": len(timeline) + 1,
            "note": note,
            "payload": payload,
            "replay_text": replay_text,
        }
        timeline.append(moment)
        scenario_state["timeline"] = timeline[-80:]
        scenario_state["last_timeline_moment_id"] = moment["moment_id"]
        AuraliteReportingService.sync_reporting_history_views(world_state)
        return moment

    @staticmethod
    def sync_reporting_history_views(world_state: dict) -> dict:
        scenario_state = world_state.setdefault("scenario_state", {})
        reporting_state = world_state.setdefault("reporting_state", {})
        artifacts = reporting_state.setdefault("artifacts", {})
        assembled = reporting_state.setdefault("assembled_reports", {})
        run_outcome = artifacts.get("scenario_outcome") or scenario_state.get("run_summary") or {}
        report = artifacts.get("scenario_insight_report") or assembled.get("scenario_insight_report") or {}
        timeline = scenario_state.get("timeline", [])

        replay = AuraliteReportingService._build_timeline_replay(timeline)
        groups = AuraliteReportingService._build_timeline_groups(timeline)
        comparison_views = run_outcome.get("comparison_views", {})
        district_story_threads = artifacts.get("district_story_threads", {})
        resident_story_threads = artifacts.get("resident_story_threads", {})
        outcome_drilldown = artifacts.get("outcome_drilldown", {})
        scenario_digest = artifacts.get("scenario_digest", {})
        key_actor_escalation = artifacts.get("key_actor_escalation", {})
        consistency = {
            "run_outcome": run_outcome,
            "scenario_outcome": run_outcome,
            "run_summary": run_outcome,
            "scenario_insight_report": report,
            "saved_insights": scenario_state.get("saved_insights", []),
            "timeline": timeline,
            "comparison_views": comparison_views,
            "timeline_replay": replay,
            "timeline_groups": groups,
            "district_story_threads": district_story_threads,
            "resident_story_threads": resident_story_threads,
            "outcome_drilldown": outcome_drilldown,
            "scenario_digest": scenario_digest,
            "key_actor_escalation": key_actor_escalation,
        }
        scenario_state["reporting_views"] = consistency
        scenario_state["timeline_replay"] = replay
        scenario_state["timeline_groups"] = groups
        scenario_state["run_summary"] = run_outcome
        scenario_state["scenario_outcome"] = run_outcome
        scenario_state["scenario_insight_report"] = report
        return consistency

    @staticmethod
    def build_scenario_digest(world_state: dict) -> dict:
        reporting_state = world_state.setdefault("reporting_state", {})
        artifacts = reporting_state.setdefault("artifacts", {})
        run_outcome = artifacts.get("scenario_outcome", {})
        district_threads = (artifacts.get("district_story_threads") or {}).get("threads", [])
        resident_threads = (artifacts.get("resident_story_threads") or {}).get("threads", [])
        drilldown = artifacts.get("outcome_drilldown", {})
        systems = run_outcome.get("top_system_contributors") or drilldown.get("systems_that_mattered", [])

        watch_next = []
        if (run_outcome.get("condition_direction") or "flat") in {"worsened", "mixed"}:
            watch_next.append("Track household pressure and service-access slippage in top shifted districts.")
        if district_threads:
            watch_next.append(f"Monitor {district_threads[0].get('name', district_threads[0].get('district_id', 'top district'))} for continued phase drift.")
        if resident_threads:
            watch_next.append(f"Check escalation around {resident_threads[0].get('resident_name', resident_threads[0].get('resident_id', 'top resident'))} household conditions.")

        return {
            "artifact_type": "scenario_digest",
            "scenario_name": run_outcome.get("scenario_name", world_state.get("scenario_state", {}).get("active_scenario_name", "default-baseline")),
            "world_time": run_outcome.get("world_time") or world_state.get("world", {}).get("current_time"),
            "what_happened_overall": (run_outcome.get("why_changed") or ["No run-level shift detected yet."])[0],
            "districts_that_mattered": (run_outcome.get("top_shifted_districts") or district_threads)[:3],
            "residents_households_that_mattered": (drilldown.get("residents_that_mattered") or resident_threads)[:3],
            "systems_that_mattered": systems[:3],
            "watch_next": watch_next[:3] or ["No dominant watch item yet; continue monitoring comparison deltas."],
        }

    @staticmethod
    def build_key_actor_escalation(world_state: dict) -> dict:
        reporting_state = world_state.setdefault("reporting_state", {})
        artifacts = reporting_state.setdefault("artifacts", {})
        district_threads = (artifacts.get("district_story_threads") or {}).get("threads", [])
        resident_threads = (artifacts.get("resident_story_threads") or {}).get("threads", [])
        households = world_state.get("households", [])
        households_by_id = {h.get("household_id"): h for h in households}

        residents = []
        for row in resident_threads[:5]:
            household = households_by_id.get(row.get("household_id"), {})
            household_stress = float((household.get("context") or {}).get("stress_index", household.get("pressure_index", 0.0)))
            residents.append(
                {
                    "actor_type": "resident_household",
                    "actor_id": row.get("resident_id"),
                    "label": row.get("resident_name"),
                    "district_id": row.get("district_id"),
                    "score": round((float(row.get("shift_score", 0.0)) * 0.7) + (household_stress * 0.3), 3),
                    "escalation_reason": row.get("headline", "Resident pressure shifts are increasing."),
                    "household_id": row.get("household_id"),
                }
            )

        districts = [
            {
                "actor_type": "district_pressure_point",
                "actor_id": row.get("district_id"),
                "label": row.get("name"),
                "district_id": row.get("district_id"),
                "score": round(float(row.get("shift_score", 0.0)), 3),
                "escalation_reason": row.get("headline", "District pressure shifts remain elevated."),
            }
            for row in district_threads[:5]
        ]

        ranked = sorted([*districts, *residents], key=lambda item: item.get("score", 0.0), reverse=True)[:8]
        return {
            "artifact_type": "key_actor_escalation",
            "scenario_name": world_state.get("scenario_state", {}).get("active_scenario_name", "default-baseline"),
            "world_time": world_state.get("world", {}).get("current_time"),
            "high_priority_actors": ranked,
            "district_pressure_points": districts[:4],
            "resident_household_pressure_points": residents[:4],
        }

    @staticmethod
    def _build_timeline_replay(timeline: list[dict]) -> dict:
        recent = timeline[-10:]
        return {
            "artifact_type": "scenario_timeline_replay",
            "count": len(recent),
            "moments": [
                {
                    "moment_id": item.get("moment_id"),
                    "order": item.get("order"),
                    "moment_type": item.get("moment_type"),
                    "moment_category": item.get("moment_category") or AuraliteReportingService._moment_category(item.get("moment_type", "")),
                    "world_time": item.get("world_time"),
                    "scenario_name": item.get("scenario_name"),
                    "text": item.get("replay_text") or "Scenario timeline moment captured.",
                }
                for item in recent
            ],
        }

    @staticmethod
    def _build_timeline_groups(timeline: list[dict]) -> list[dict]:
        grouped = {
            "interventions": [],
            "snapshots": [],
            "comparisons": [],
            "scenario_switches": [],
        }
        for item in timeline[-24:]:
            key = item.get("moment_category")
            if key not in grouped:
                continue
            grouped[key].append(item)
        rows = []
        for key, items in grouped.items():
            if not items:
                continue
            latest = items[-1]
            rows.append(
                {
                    "group": key,
                    "label": key.replace("_", " "),
                    "count": len(items),
                    "latest_moment_id": latest.get("moment_id"),
                    "latest_world_time": latest.get("world_time"),
                    "latest_text": latest.get("replay_text") or latest.get("moment_type", "moment"),
                }
            )
        return rows

    @staticmethod
    def _moment_category(moment_type: str) -> str:
        mapping = {
            "intervention_applied": "interventions",
            "snapshot_saved": "snapshots",
            "scenario_compared": "comparisons",
            "scenario_switched": "scenario_switches",
        }
        return mapping.get(moment_type, "comparisons" if "compare" in (moment_type or "") else "snapshots")

    @staticmethod
    def _moment_replay_text(moment_type: str, scenario_name: str, payload: dict, note: str) -> str:
        if moment_type == "intervention_applied":
            return f"Intervention applied in {scenario_name}; delta captured for current state."
        if moment_type == "snapshot_saved":
            return f"Snapshot saved for {scenario_name} ({payload.get('label') or 'manual'})."
        if moment_type == "scenario_compared":
            return f"Baseline comparison run for {scenario_name}; direction: {payload.get('direction', 'flat')}."
        if moment_type == "scenario_switched":
            return f"Scenario switched to {payload.get('scenario_name', scenario_name)}."
        if moment_type == "insight_saved":
            return f"Scenario insight saved for {scenario_name}."
        return note or f"Scenario moment recorded for {scenario_name}."

    @staticmethod
    def _build_insight_filter_catalog(insights: list[dict]) -> dict:
        return {
            "source_types": sorted({(item.get("source_type") or "system") for item in insights}),
            "directions": sorted({(item.get("direction") or "flat") for item in insights}),
            "scenario_names": sorted({(item.get("scenario_name") or "default-baseline") for item in insights}),
            "count": len(insights),
        }
