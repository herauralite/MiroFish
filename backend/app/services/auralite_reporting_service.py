from __future__ import annotations

from datetime import datetime

from .auralite_intervention_service import AuraliteInterventionService


class AuraliteReportingService:
    """Milestone 12 lightweight report assembly and saved insight helpers."""

    @staticmethod
    def assemble_report_artifacts(
        world_state: dict,
        world_artifact: dict,
        scenario_outcome: dict,
        intervention_artifact: dict,
        comparison_artifact: dict,
        outcome_drilldown: dict | None = None,
    ) -> dict:
        key_conditions = scenario_outcome.get("key_conditions", {})
        top_districts = scenario_outcome.get("top_shifted_districts", [])[:3]
        top_systems = scenario_outcome.get("top_system_contributors", [])[:3]
        drilldown = outcome_drilldown or {}

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
                    "archetype": row.get("archetype"),
                    "state_phase": row.get("state_phase", "steady"),
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
            "intervention_aftermath": {
                "effect_signal": intervention_artifact.get("effect_signal", "unclear"),
                "profile": intervention_artifact.get("aftermath_profile", {}),
                "targeted": intervention_artifact.get("targeted_aftermath", {}),
                "active_target_count": len((intervention_artifact.get("targeted_aftermath") or {}).get("district_ids", [])),
            },
        }

        report_state = world_state.setdefault("reporting_state", {})
        assembled_reports = report_state.setdefault("assembled_reports", {})
        assembled_reports["scenario_insight_report"] = compact
        assembled_reports["updated_at"] = datetime.utcnow().isoformat()
        return compact

    @staticmethod
    def assemble_artifact_stack(
        world_state: dict,
        base_artifacts: dict,
        world_artifact: dict,
        intervention_artifact: dict,
        comparison_artifact: dict,
    ) -> dict:
        previous_focus = (
            (
                (world_state.get("reporting_state", {}).get("artifacts", {}).get("operator_brief", {}) or {}).get("focus_prioritization")
                or {}
            )
            or (
                (world_state.get("reporting_state", {}).get("artifacts", {}).get("scenario_handoff", {}) or {}).get("focus_prioritization")
                or {}
            )
        )
        scenario_outcome = base_artifacts.get("scenario_outcome", {})
        outcome_drilldown = base_artifacts.get("outcome_drilldown", {})
        district_threads = (base_artifacts.get("district_story_threads") or {}).get("threads", [])
        resident_threads = (base_artifacts.get("resident_story_threads") or {}).get("threads", [])

        scenario_insight_report = AuraliteReportingService.assemble_report_artifacts(
            world_state=world_state,
            world_artifact=world_artifact,
            scenario_outcome=scenario_outcome,
            intervention_artifact=intervention_artifact,
            comparison_artifact=comparison_artifact,
            outcome_drilldown=outcome_drilldown,
        )
        scenario_digest = AuraliteReportingService._build_scenario_digest(
            world_state=world_state,
            run_outcome=scenario_outcome,
            outcome_drilldown=outcome_drilldown,
            district_threads=district_threads,
            resident_threads=resident_threads,
        )
        key_actor_escalation = AuraliteReportingService._build_key_actor_escalation(
            world_state=world_state,
            district_threads=district_threads,
            resident_threads=resident_threads,
        )
        monitoring_watchlist = AuraliteReportingService._build_monitoring_watchlist(
            world_state=world_state,
            run_outcome=scenario_outcome,
            scenario_digest=scenario_digest,
            key_actor_escalation=key_actor_escalation,
            district_threads=district_threads,
            resident_threads=resident_threads,
        )
        stability_signals = AuraliteReportingService._build_stability_signals(
            world_state=world_state,
            run_outcome=scenario_outcome,
            district_threads=district_threads,
            resident_threads=resident_threads,
        )
        operator_brief = AuraliteReportingService._build_operator_brief(
            scenario_outcome=scenario_outcome,
            scenario_digest=scenario_digest,
            key_actor_escalation=key_actor_escalation,
            monitoring_watchlist=monitoring_watchlist,
            stability_signals=stability_signals,
            previous_focus=previous_focus,
        )
        intervention_feedback_loop = AuraliteReportingService._build_intervention_feedback_loop(
            world_state=world_state,
            scenario_outcome=scenario_outcome,
            intervention_artifact=intervention_artifact,
            monitoring_watchlist=monitoring_watchlist,
            stability_signals=stability_signals,
            scenario_digest=scenario_digest,
            district_threads=district_threads,
        )
        scenario_handoff = AuraliteReportingService._build_scenario_handoff(
            world_state=world_state,
            scenario_outcome=scenario_outcome,
            scenario_digest=scenario_digest,
            key_actor_escalation=key_actor_escalation,
            monitoring_watchlist=monitoring_watchlist,
            stability_signals=stability_signals,
            intervention_feedback_loop=intervention_feedback_loop,
            previous_focus=previous_focus,
        )
        operator_session_continuity = AuraliteReportingService._build_operator_session_continuity(
            world_state=world_state,
            scenario_handoff=scenario_handoff,
            operator_brief=operator_brief,
        )
        return {
            **base_artifacts,
            "scenario_insight_report": scenario_insight_report,
            "run_summary": scenario_outcome,
            "scenario_digest": scenario_digest,
            "key_actor_escalation": key_actor_escalation,
            "monitoring_watchlist": monitoring_watchlist,
            "stability_signals": stability_signals,
            "operator_brief": operator_brief,
            "intervention_feedback_loop": intervention_feedback_loop,
            "intervention_aftermath": intervention_feedback_loop.get("aftermath", {}),
            "scenario_handoff": scenario_handoff,
            "operator_session_continuity": operator_session_continuity,
        }

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
        monitoring_watchlist = artifacts.get("monitoring_watchlist", {})
        stability_signals = artifacts.get("stability_signals", {})
        intervention_feedback_loop = artifacts.get("intervention_feedback_loop", {})
        intervention_aftermath = artifacts.get("intervention_aftermath", intervention_feedback_loop.get("aftermath", {}))
        scenario_handoff = artifacts.get("scenario_handoff", {})
        operator_session_continuity = artifacts.get("operator_session_continuity", {})
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
            "monitoring_watchlist": monitoring_watchlist,
            "stability_signals": stability_signals,
            "intervention_feedback_loop": intervention_feedback_loop,
            "intervention_aftermath": intervention_aftermath,
            "scenario_handoff": scenario_handoff,
            "operator_session_continuity": operator_session_continuity,
        }
        scenario_state["reporting_views"] = consistency
        scenario_state["timeline_replay"] = replay
        scenario_state["timeline_groups"] = groups
        scenario_state["run_summary"] = run_outcome
        scenario_state["scenario_outcome"] = run_outcome
        scenario_state["scenario_insight_report"] = report
        scenario_state["operator_session_view"] = operator_session_continuity
        return consistency

    @staticmethod
    def build_scenario_digest(world_state: dict) -> dict:
        reporting_state = world_state.setdefault("reporting_state", {})
        artifacts = reporting_state.setdefault("artifacts", {})
        run_outcome = artifacts.get("scenario_outcome", {})
        district_threads = (artifacts.get("district_story_threads") or {}).get("threads", [])
        resident_threads = (artifacts.get("resident_story_threads") or {}).get("threads", [])
        drilldown = artifacts.get("outcome_drilldown", {})
        return AuraliteReportingService._build_scenario_digest(
            world_state=world_state,
            run_outcome=run_outcome,
            outcome_drilldown=drilldown,
            district_threads=district_threads,
            resident_threads=resident_threads,
        )

    @staticmethod
    def _build_scenario_digest(world_state: dict, run_outcome: dict, outcome_drilldown: dict, district_threads: list[dict], resident_threads: list[dict]) -> dict:
        systems = run_outcome.get("top_system_contributors") or outcome_drilldown.get("systems_that_mattered", [])

        watch_next = []
        if (run_outcome.get("condition_direction") or "flat") in {"worsened", "mixed"}:
            watch_next.append("Track household pressure and service-access slippage in top shifted districts.")
        if district_threads:
            top = district_threads[0]
            watch_next.append(
                f"Monitor {top.get('name', top.get('district_id', 'top district'))} ({top.get('archetype', 'mixed')}) for continued phase drift."
            )
        if resident_threads:
            watch_next.append(f"Check escalation around {resident_threads[0].get('resident_name', resident_threads[0].get('resident_id', 'top resident'))} household conditions.")

        return {
            "artifact_type": "scenario_digest",
            "scenario_name": run_outcome.get("scenario_name", world_state.get("scenario_state", {}).get("active_scenario_name", "default-baseline")),
            "world_time": run_outcome.get("world_time") or world_state.get("world", {}).get("current_time"),
            "what_happened_overall": (run_outcome.get("why_changed") or ["No run-level shift detected yet."])[0],
            "districts_that_mattered": (run_outcome.get("top_shifted_districts") or district_threads)[:3],
            "residents_households_that_mattered": (outcome_drilldown.get("residents_that_mattered") or resident_threads)[:3],
            "systems_that_mattered": systems[:3],
            "watch_next": watch_next[:3] or ["No dominant watch item yet; continue monitoring comparison deltas."],
        }

    @staticmethod
    def build_monitoring_watchlist(world_state: dict) -> dict:
        reporting_state = world_state.setdefault("reporting_state", {})
        artifacts = reporting_state.setdefault("artifacts", {})
        return AuraliteReportingService._build_monitoring_watchlist(
            world_state=world_state,
            run_outcome=artifacts.get("scenario_outcome", {}),
            scenario_digest=artifacts.get("scenario_digest", {}),
            key_actor_escalation=artifacts.get("key_actor_escalation", {}),
            district_threads=(artifacts.get("district_story_threads") or {}).get("threads", []),
            resident_threads=(artifacts.get("resident_story_threads") or {}).get("threads", []),
        )

    @staticmethod
    def _build_monitoring_watchlist(
        world_state: dict,
        run_outcome: dict,
        scenario_digest: dict,
        key_actor_escalation: dict,
        district_threads: list[dict],
        resident_threads: list[dict],
    ) -> dict:
        districts_source = (run_outcome.get("top_shifted_districts") or district_threads)[:4]
        districts_to_watch = []
        for row in districts_source:
            shift_score = float(row.get("shift_score", 0.0))
            districts_to_watch.append(
                {
                    "district_id": row.get("district_id"),
                    "label": row.get("name") or row.get("district_id"),
                    "watch_score": round(shift_score, 3),
                    "watch_reason": row.get("headline") or "District shift remains one of the strongest current movers.",
                    "urgency": "high" if shift_score >= 0.16 else ("medium" if shift_score >= 0.08 else "observe"),
                }
            )
        districts_to_watch = sorted(
            districts_to_watch,
            key=lambda row: (-float(row.get("watch_score", 0.0)), str(row.get("district_id", ""))),
        )

        resident_points = [
            row for row in (key_actor_escalation.get("resident_household_pressure_points") or [])
            if (row.get("actor_type") == "resident_household" or row.get("household_id"))
        ]
        if not resident_points:
            resident_points = resident_threads[:4]
        residents_to_watch = []
        for row in resident_points[:4]:
            score = float(row.get("score", row.get("shift_score", 0.0)))
            residents_to_watch.append(
                {
                    "resident_id": row.get("actor_id") or row.get("resident_id"),
                    "resident_name": row.get("label") or row.get("resident_name") or row.get("resident_id"),
                    "household_id": row.get("household_id"),
                    "district_id": row.get("district_id"),
                    "watch_score": round(score, 3),
                    "watch_reason": row.get("escalation_reason") or row.get("headline") or "Resident/household pressure is elevated.",
                    "urgency": "high" if score >= 0.18 else ("medium" if score >= 0.1 else "observe"),
                }
            )
        residents_to_watch = sorted(
            residents_to_watch,
            key=lambda row: (-float(row.get("watch_score", 0.0)), str(row.get("resident_id", ""))),
        )

        systems_to_watch = []
        for row in (run_outcome.get("top_system_contributors") or [])[:4]:
            score = float(row.get("score", 0.0))
            systems_to_watch.append(
                {
                    "system": row.get("system"),
                    "watch_score": round(score, 3),
                    "watch_reason": row.get("label") or "System-level contributor remains material in the latest outcome.",
                    "urgency": "high" if score >= 0.12 else ("medium" if score >= 0.07 else "observe"),
                }
            )
        systems_to_watch = sorted(
            systems_to_watch,
            key=lambda row: (-float(row.get("watch_score", 0.0)), str(row.get("system", ""))),
        )

        return {
            "artifact_type": "monitoring_watchlist",
            "scenario_name": run_outcome.get("scenario_name", world_state.get("scenario_state", {}).get("active_scenario_name", "default-baseline")),
            "world_time": run_outcome.get("world_time") or world_state.get("world", {}).get("current_time"),
            "watch_next": (scenario_digest.get("watch_next") or [])[:3],
            "districts_to_watch": districts_to_watch,
            "residents_households_to_watch": residents_to_watch,
            "systems_to_watch": systems_to_watch,
        }

    @staticmethod
    def build_stability_signals(world_state: dict) -> dict:
        reporting_state = world_state.setdefault("reporting_state", {})
        artifacts = reporting_state.setdefault("artifacts", {})
        return AuraliteReportingService._build_stability_signals(
            world_state=world_state,
            run_outcome=artifacts.get("scenario_outcome", {}),
            district_threads=(artifacts.get("district_story_threads") or {}).get("threads", []),
            resident_threads=(artifacts.get("resident_story_threads") or {}).get("threads", []),
        )

    @staticmethod
    def _build_stability_signals(world_state: dict, run_outcome: dict, district_threads: list[dict], resident_threads: list[dict]) -> dict:
        districts_by_id = {row.get("district_id"): row for row in world_state.get("districts", [])}
        persons_by_id = {row.get("person_id"): row for row in world_state.get("persons", [])}

        district_rows = []
        for row in district_threads[:4]:
            district = districts_by_id.get(row.get("district_id"), {})
            changed = ((district.get("derived_summary") or {}).get("causal_readout") or {}).get("what_changed", {})
            stability_delta = (
                float(changed.get("service_access_score", 0.0))
                + float(changed.get("social_support_score", 0.0))
                + float(changed.get("employment_rate", 0.0))
                - float(changed.get("pressure_index", 0.0))
            )
            district_rows.append(
                {
                    "district_id": row.get("district_id"),
                    "label": row.get("name") or row.get("district_id"),
                    "signal": AuraliteReportingService._stability_label(stability_delta),
                    "score": round(stability_delta, 3),
                }
            )

        resident_rows = []
        for row in resident_threads[:4]:
            person = persons_by_id.get(row.get("resident_id"), {})
            changed = ((person.get("derived_summary") or {}).get("causal_readout") or {}).get("what_changed", {})
            stability_delta = (
                float(changed.get("housing_stability", 0.0))
                + float(changed.get("employment_stability", 0.0))
                + float(changed.get("service_access", 0.0))
                + float(changed.get("social_support", 0.0))
                - float(changed.get("stress", 0.0))
            )
            resident_rows.append(
                {
                    "resident_id": row.get("resident_id"),
                    "label": row.get("resident_name") or row.get("resident_id"),
                    "household_id": row.get("household_id"),
                    "signal": AuraliteReportingService._stability_label(stability_delta),
                    "score": round(stability_delta, 3),
                }
            )

        systems = []
        for key, condition in (run_outcome.get("key_conditions") or {}).items():
            direction = condition.get("direction", "flat")
            signal = "holding_flat"
            if direction == "improving":
                signal = "stabilizing"
            elif direction == "worsening":
                signal = "deteriorating"
            systems.append(
                {
                    "system": key,
                    "signal": signal,
                    "delta": round(float(condition.get("delta", 0.0)), 3),
                }
            )

        return {
            "artifact_type": "stability_signals",
            "scenario_name": run_outcome.get("scenario_name", world_state.get("scenario_state", {}).get("active_scenario_name", "default-baseline")),
            "world_time": run_outcome.get("world_time") or world_state.get("world", {}).get("current_time"),
            "districts": district_rows,
            "residents_households": resident_rows,
            "systems": systems[:4],
        }

    @staticmethod
    def build_key_actor_escalation(world_state: dict) -> dict:
        reporting_state = world_state.setdefault("reporting_state", {})
        artifacts = reporting_state.setdefault("artifacts", {})
        return AuraliteReportingService._build_key_actor_escalation(
            world_state=world_state,
            district_threads=(artifacts.get("district_story_threads") or {}).get("threads", []),
            resident_threads=(artifacts.get("resident_story_threads") or {}).get("threads", []),
        )

    @staticmethod
    def _build_key_actor_escalation(world_state: dict, district_threads: list[dict], resident_threads: list[dict]) -> dict:
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
    def _build_operator_brief(
        scenario_outcome: dict,
        scenario_digest: dict,
        key_actor_escalation: dict,
        monitoring_watchlist: dict,
        stability_signals: dict,
        previous_focus: dict | None = None,
    ) -> dict:
        priority_actors = (key_actor_escalation.get("high_priority_actors") or [])[:3]
        watch_districts = (monitoring_watchlist.get("districts_to_watch") or [])[:2]
        watch_residents = (monitoring_watchlist.get("residents_households_to_watch") or [])[:2]
        watch_systems = (monitoring_watchlist.get("systems_to_watch") or [])[:2]
        stable_districts = (stability_signals.get("districts") or [])[:2]
        stable_residents = (stability_signals.get("residents_households") or [])[:2]
        stable_systems = (stability_signals.get("systems") or [])[:2]
        deteriorating = [row for row in stable_systems if row.get("signal") == "deteriorating"]
        stabilizing = [row for row in stable_systems if row.get("signal") == "stabilizing"]
        main_problem = (
            (scenario_digest.get("watch_next") or [None])[0]
            or (deteriorating[0].get("system") if deteriorating else None)
            or "No dominant pressure spike yet."
        )
        most_important_focus = (
            (priority_actors[0] or {}).get("label")
            or (watch_districts[0] or {}).get("label")
            or (watch_systems[0] or {}).get("system")
            or "No single dominant focus yet."
        )
        check_next = [
            item
            for item in [
                (scenario_digest.get("watch_next") or [None, None])[0],
                (scenario_digest.get("watch_next") or [None, None])[1],
                f"Validate {watch_systems[0].get('system')} direction" if watch_systems else None,
            ]
            if item
        ][:3]
        top_district_watch = AuraliteReportingService._pick_focus_row(
            rows=watch_districts,
            previous_key=(previous_focus or {}).get("current_district_id"),
            key_fields=("district_id", "label"),
            score_field="watch_score",
        )
        top_resident_watch = AuraliteReportingService._pick_focus_row(
            rows=watch_residents,
            previous_key=(previous_focus or {}).get("resident_id"),
            key_fields=("resident_id", "resident_name"),
            score_field="watch_score",
        )
        top_system_watch = AuraliteReportingService._pick_focus_row(
            rows=watch_systems,
            previous_key=(previous_focus or {}).get("top_system"),
            key_fields=("system",),
            score_field="watch_score",
        )
        top_actor = priority_actors[0] if priority_actors else {}
        top_check = check_next[0] if check_next else "Continue watchlist monitoring."
        stable_check = AuraliteReportingService._pick_focus_check(
            options=check_next,
            previous_value=(previous_focus or {}).get("next_check"),
        )
        district_driver = (
            top_district_watch.get("watch_reason")
            or top_district_watch.get("label")
            or (scenario_digest.get("districts_that_mattered") or [{}])[0].get("headline")
            or "No dominant district driver surfaced yet."
        )
        resident_relevance = (
            top_resident_watch.get("watch_reason")
            or top_resident_watch.get("label")
            or top_actor.get("escalation_reason")
            or "No high-relevance resident/household tie surfaced yet."
        )
        institution_link = (
            f"{top_system_watch.get('system')} service path"
            if top_system_watch.get("system")
            else "No dominant institution/service link surfaced yet."
        )
        next_check_why = AuraliteReportingService._focus_next_check_why(
            district_driver=district_driver,
            institution_link=institution_link,
            has_system_link=bool(top_system_watch.get("system")),
        )
        focus_confidence = AuraliteReportingService._focus_confidence_snapshot(
            top_district_watch=top_district_watch,
            top_resident_watch=top_resident_watch,
            top_system_watch=top_system_watch,
            stable_check=stable_check or top_check,
            check_candidates=check_next,
            previous_focus=previous_focus,
        )
        focus_evidence = AuraliteReportingService._focus_evidence_snapshot(
            district_watch=top_district_watch,
            resident_watch=top_resident_watch,
            system_watch=top_system_watch,
            next_check=stable_check or top_check,
            next_check_why=next_check_why,
        )
        return {
            "artifact_type": "operator_brief",
            "world_time": scenario_outcome.get("world_time"),
            "scenario_name": scenario_outcome.get("scenario_name"),
            "what_happened": scenario_digest.get("what_happened_overall") or (scenario_outcome.get("why_changed") or ["No scenario-level shift detected yet."])[0],
            "main_problem_now": main_problem,
            "matters_most_now": most_important_focus,
            "check_next": check_next,
            "next_check_why": next_check_why,
            "focus_prioritization": {
                "current_district_driver": district_driver,
                "current_district_id": top_district_watch.get("district_id"),
                "resident_household_service_relevance": resident_relevance,
                "resident_id": top_resident_watch.get("resident_id"),
                "top_institution_link": institution_link,
                "top_system": top_system_watch.get("system"),
                "next_check": stable_check or top_check,
                "next_check_why": next_check_why,
                "confidence": focus_confidence,
                "evidence": focus_evidence,
            },
            "who_matters": priority_actors,
            "watch_now": {
                "districts": watch_districts,
                "residents_households": watch_residents,
                "systems": watch_systems,
            },
            "stability_now": {
                "districts": stable_districts,
                "residents_households": stable_residents,
                "systems": stable_systems,
            },
            "stabilizing_vs_deteriorating": {
                "stabilizing_count": len(stabilizing),
                "deteriorating_count": len(deteriorating),
                "stabilizing_top": (stabilizing[0] or {}).get("system") if stabilizing else None,
                "deteriorating_top": (deteriorating[0] or {}).get("system") if deteriorating else None,
            },
            "focus_confidence": focus_confidence,
            "focus_evidence": focus_evidence,
        }

    @staticmethod
    def _build_scenario_handoff(
        world_state: dict,
        scenario_outcome: dict,
        scenario_digest: dict,
        key_actor_escalation: dict,
        monitoring_watchlist: dict,
        stability_signals: dict,
        intervention_feedback_loop: dict,
        previous_focus: dict | None = None,
    ) -> dict:
        timeline = (world_state.get("scenario_state", {}) or {}).get("timeline", [])
        recent_moments = timeline[-3:]
        stabilizing_count = len([row for row in (stability_signals.get("systems") or []) if row.get("signal") == "stabilizing"])
        deteriorating_count = len([row for row in (stability_signals.get("systems") or []) if row.get("signal") == "deteriorating"])
        if stabilizing_count > deteriorating_count:
            trend_label = "stabilizing_bias"
        elif deteriorating_count > stabilizing_count:
            trend_label = "deteriorating_bias"
        else:
            trend_label = "mixed_or_flat"
        top_district_watch = AuraliteReportingService._pick_focus_row(
            rows=(monitoring_watchlist.get("districts_to_watch") or [])[:2],
            previous_key=(previous_focus or {}).get("current_district_id"),
            key_fields=("district_id", "label"),
            score_field="watch_score",
        )
        top_resident_watch = AuraliteReportingService._pick_focus_row(
            rows=(monitoring_watchlist.get("residents_households_to_watch") or [])[:2],
            previous_key=(previous_focus or {}).get("resident_id"),
            key_fields=("resident_id", "resident_name"),
            score_field="watch_score",
        )
        top_system_watch = AuraliteReportingService._pick_focus_row(
            rows=(monitoring_watchlist.get("systems_to_watch") or [])[:2],
            previous_key=(previous_focus or {}).get("top_system"),
            key_fields=("system",),
            score_field="watch_score",
        )
        top_watch_system = top_system_watch.get("system")
        stable_next_check = AuraliteReportingService._pick_focus_check(
            options=(scenario_digest.get("watch_next") or monitoring_watchlist.get("watch_next") or [])[:2],
            previous_value=(previous_focus or {}).get("next_check"),
        )
        handoff_next_check_why = AuraliteReportingService._focus_next_check_why(
            district_driver=(top_district_watch.get("watch_reason") or top_district_watch.get("label") or "current district pressure line"),
            institution_link=(f"{top_watch_system} service path" if top_watch_system else None),
            has_system_link=bool(top_watch_system),
        )
        stable_next_check_choice = stable_next_check or ((scenario_digest.get("watch_next") or monitoring_watchlist.get("watch_next") or ["Continue watchlist monitoring."])[0])
        focus_confidence = AuraliteReportingService._focus_confidence_snapshot(
            top_district_watch=top_district_watch,
            top_resident_watch=top_resident_watch,
            top_system_watch=top_system_watch,
            stable_check=stable_next_check_choice,
            check_candidates=(scenario_digest.get("watch_next") or monitoring_watchlist.get("watch_next") or [])[:2],
            previous_focus=previous_focus,
        )
        focus_evidence = AuraliteReportingService._focus_evidence_snapshot(
            district_watch=top_district_watch,
            resident_watch=top_resident_watch,
            system_watch=top_system_watch,
            next_check=stable_next_check_choice,
            next_check_why=handoff_next_check_why,
        )

        return {
            "artifact_type": "scenario_handoff",
            "scenario_name": scenario_outcome.get("scenario_name", world_state.get("scenario_state", {}).get("active_scenario_name", "default-baseline")),
            "world_time": scenario_outcome.get("world_time") or world_state.get("world", {}).get("current_time"),
            "what_happened_so_far": {
                "summary": scenario_digest.get("what_happened_overall") or (scenario_outcome.get("why_changed") or ["No scenario-level shift detected yet."])[0],
                "recent_moments": [
                    {
                        "moment_type": row.get("moment_type"),
                        "world_time": row.get("world_time"),
                        "text": row.get("replay_text") or row.get("moment_type", "moment"),
                    }
                    for row in recent_moments
                ],
            },
            "what_matters_now": {
                "priority_actors": (key_actor_escalation.get("high_priority_actors") or [])[:3],
                "districts": (monitoring_watchlist.get("districts_to_watch") or [])[:2],
                "residents_households": (monitoring_watchlist.get("residents_households_to_watch") or [])[:2],
                "systems": (monitoring_watchlist.get("systems_to_watch") or [])[:2],
            },
            "watch_next": (scenario_digest.get("watch_next") or monitoring_watchlist.get("watch_next") or [])[:3],
            "decision_support": {
                "main_problem_now": ((scenario_digest.get("watch_next") or [None])[0] or "No dominant pressure spike yet."),
                "matters_most_now": (
                    ((key_actor_escalation.get("high_priority_actors") or [{}])[0] or {}).get("label")
                    or ((monitoring_watchlist.get("districts_to_watch") or [{}])[0] or {}).get("label")
                    or ((monitoring_watchlist.get("systems_to_watch") or [{}])[0] or {}).get("system")
                    or "No single dominant focus yet."
                ),
                "check_next": (scenario_digest.get("watch_next") or monitoring_watchlist.get("watch_next") or [])[:2],
                "next_check_why": handoff_next_check_why,
            },
            "focus_prioritization": {
                "current_district_driver": (top_district_watch.get("watch_reason") or top_district_watch.get("label") or "No dominant district driver surfaced yet."),
                "current_district_id": top_district_watch.get("district_id"),
                "resident_household_service_relevance": (top_resident_watch.get("watch_reason") or top_resident_watch.get("label") or "No high-relevance resident/household tie surfaced yet."),
                "resident_id": top_resident_watch.get("resident_id"),
                "top_institution_link": (
                    f"{top_system_watch.get('system')} service path"
                    if top_system_watch.get("system")
                    else "No dominant institution/service link surfaced yet."
                ),
                "top_system": top_system_watch.get("system"),
                "next_check": stable_next_check_choice,
                "next_check_why": handoff_next_check_why,
                "confidence": focus_confidence,
                "evidence": focus_evidence,
            },
            "focus_confidence": focus_confidence,
            "focus_evidence": focus_evidence,
            "intervention_feedback": intervention_feedback_loop,
            "trend_balance": {
                "label": trend_label,
                "stabilizing_signals": stabilizing_count,
                "deteriorating_signals": deteriorating_count,
                "districts": (stability_signals.get("districts") or [])[:3],
                "residents_households": (stability_signals.get("residents_households") or [])[:3],
                "systems": (stability_signals.get("systems") or [])[:3],
            },
        }

    @staticmethod
    def _pick_focus_row(rows: list[dict], previous_key: str | None, key_fields: tuple[str, ...], score_field: str) -> dict:
        if not rows:
            return {}
        ranked = sorted(
            rows,
            key=lambda row: (
                -float(row.get(score_field, 0.0)),
                *(str(row.get(field, "")) for field in key_fields),
            ),
        )
        top = ranked[0]
        if not previous_key:
            return top
        previous = next((row for row in ranked if any(str(row.get(field, "")) == str(previous_key) for field in key_fields)), None)
        if not previous:
            return top
        if float(top.get(score_field, 0.0)) - float(previous.get(score_field, 0.0)) <= 0.02:
            return previous
        return top

    @staticmethod
    def _pick_focus_check(options: list[str], previous_value: str | None) -> str | None:
        if not options:
            return previous_value
        normalized = [item for item in options if item]
        if not normalized:
            return previous_value
        if previous_value and previous_value in normalized[:2]:
            return previous_value
        return normalized[0]

    @staticmethod
    def _build_intervention_feedback_loop(
        world_state: dict,
        scenario_outcome: dict,
        intervention_artifact: dict,
        monitoring_watchlist: dict,
        stability_signals: dict,
        scenario_digest: dict,
        district_threads: list[dict],
    ) -> dict:
        effect_signal = intervention_artifact.get("effect_signal", "unclear")
        affected = intervention_artifact.get("most_affected", {})
        top_district = ((affected.get("districts") or [{}])[0] or {})
        top_watch = ((monitoring_watchlist.get("districts_to_watch") or [{}])[0] or {})
        aftermath = AuraliteReportingService._build_intervention_aftermath(
            world_state=world_state,
            intervention_artifact=intervention_artifact,
            stability_signals=stability_signals,
            district_threads=district_threads,
            scenario_outcome=scenario_outcome,
        )
        next_checks = (
            (aftermath.get("operator_checks") or [])
            + (intervention_artifact.get("check_next") or [])
            + (scenario_digest.get("watch_next") or [])
            + [
                f"Track {top_watch.get('label')} urgency: {top_watch.get('urgency')}." if top_watch else None,
            ]
        )
        unique_checks = []
        for item in next_checks:
            if not item or item in unique_checks:
                continue
            unique_checks.append(item)
        systems = (stability_signals.get("systems") or [])[:3]
        return {
            "artifact_type": "intervention_feedback_loop",
            "world_time": scenario_outcome.get("world_time"),
            "scenario_name": scenario_outcome.get("scenario_name"),
            "intervention_id": intervention_artifact.get("intervention_id"),
            "effect_signal": effect_signal,
            "aftermath": aftermath,
            "aftermath_profile": intervention_artifact.get("aftermath_profile", {}),
            "targeted_aftermath": intervention_artifact.get("targeted_aftermath", {}),
            "readback": {
                "what_changed": intervention_artifact.get("what_changed", {}),
                "what_changed_line": (
                    f"Δpressure {float((intervention_artifact.get('what_changed') or {}).get('household_pressure_index', 0.0)):+.3f}, "
                    f"Δservice {float((intervention_artifact.get('what_changed') or {}).get('service_access_score', 0.0)):+.3f}, "
                    f"Δemployment {float((intervention_artifact.get('what_changed') or {}).get('employment_rate', 0.0)):+.3f}."
                ),
                "effect_line": f"Intervention looks {effect_signal}; aftermath is {aftermath.get('status', 'unclear')}.",
                "follow_through_line": aftermath.get("follow_through_line", "Follow-through focus still forming."),
                "persistence_line": aftermath.get("persistence_line", "Persistence signal still forming."),
                "reversal_risk_line": (
                    f"Estimated reversal risk: {float((intervention_artifact.get('aftermath_profile') or {}).get('reversal_risk', 0.0)):.3f}."
                    if intervention_artifact.get("aftermath_profile")
                    else "Reversal risk signal not available."
                ),
                "top_district_line": (
                    f"Most affected district: {top_district.get('name') or top_district.get('district_id', 'none')} "
                    f"(shift {float(top_district.get('shift_score', 0.0)):.3f})."
                    if top_district else "Most affected district: none detected."
                ),
            },
            "most_affected": affected,
            "systems_snapshot": systems,
            "check_next": unique_checks[:3],
        }

    @staticmethod
    def _build_intervention_aftermath(
        world_state: dict,
        intervention_artifact: dict,
        stability_signals: dict,
        district_threads: list[dict],
        scenario_outcome: dict,
    ) -> dict:
        history = (world_state.get("intervention_state", {}).get("history") or [])
        if not history or intervention_artifact.get("status") == "none":
            return {
                "artifact_type": "intervention_aftermath",
                "status": "none",
                "ticks_observed": 0,
                "persistence_index": 0.0,
                "dominant_zone": "none",
                "follow_through_line": "No intervention aftermath to track yet.",
                "persistence_line": "No intervention applied yet.",
                "operator_checks": [],
                "trace": [],
            }

        last_record = history[-1]
        effects = last_record.setdefault("effects", {})
        before_summary = effects.get("before_summary") or {}
        after_summary = effects.get("after_summary") or {}
        current_summary = AuraliteInterventionService.world_summary(world_state)
        if before_summary and after_summary:
            immediate_delta = AuraliteInterventionService.summary_delta(before_summary, after_summary)
            drift_from_after = AuraliteInterventionService.summary_delta(after_summary, current_summary)
        else:
            immediate_delta = {}
            drift_from_after = {}

        tick_trace = effects.setdefault("post_ticks", [])
        now_world_time = world_state.get("world", {}).get("current_time")
        if now_world_time and ((tick_trace[-1:] or [{}])[0].get("world_time") != now_world_time):
            tick_trace.append(
                {
                    "world_time": now_world_time,
                    "drift": {
                        "household_pressure_index": round(float(drift_from_after.get("household_pressure_index", 0.0)), 3),
                        "service_access_score": round(float(drift_from_after.get("service_access_score", 0.0)), 3),
                        "employment_rate": round(float(drift_from_after.get("employment_rate", 0.0)), 3),
                        "stressed_districts": round(float(drift_from_after.get("stressed_districts", 0.0)), 3),
                    },
                }
            )
            effects["post_ticks"] = tick_trace[-6:]
            tick_trace = effects["post_ticks"]

        persistence_index, status = AuraliteReportingService._aftermath_persistence_status(
            immediate_delta=immediate_delta,
            drift_from_after=drift_from_after,
        )
        dominant_zone_ref = AuraliteReportingService._aftermath_dominant_zone(
            intervention_artifact=intervention_artifact,
            stability_signals=stability_signals,
            district_threads=district_threads,
            scenario_outcome=scenario_outcome,
        )
        dominant_zone = dominant_zone_ref.get("label", "none")
        checks = [
            f"Recheck {dominant_zone} next tick for {status} follow-through." if dominant_zone != "none" else None,
            "Escalate only if persistence stays below 0.35 for two checks." if persistence_index < 0.35 else "Hold intervention; verify persistence for one more tick.",
        ]
        checks = [item for item in checks if item]
        return {
            "artifact_type": "intervention_aftermath",
            "status": status,
            "ticks_observed": len(tick_trace),
            "persistence_index": round(persistence_index, 3),
            "dominant_zone": dominant_zone,
            "dominant_zone_ref": dominant_zone_ref,
            "follow_through_line": f"Follow-through strongest in {dominant_zone}." if dominant_zone != "none" else "Follow-through zone is still diffuse.",
            "persistence_line": (
                f"After {len(tick_trace)} tracked ticks, effect is {status} (persistence {round(persistence_index, 3):.3f})."
            ),
            "operator_checks": checks[:2],
            "trace": tick_trace[-3:],
        }

    @staticmethod
    def _aftermath_persistence_status(immediate_delta: dict, drift_from_after: dict) -> tuple[float, str]:
        tracked_keys = {
            "household_pressure_index": -1.0,
            "service_access_score": 1.0,
            "employment_rate": 1.0,
            "stressed_districts": -1.0,
        }
        scores = []
        for key, desirability in tracked_keys.items():
            immediate = float(immediate_delta.get(key, 0.0))
            if abs(immediate) < 0.003:
                continue
            drift = float(drift_from_after.get(key, 0.0))
            expected_direction = 1.0 if (immediate * desirability) > 0 else -1.0
            normalized = max(-1.0, min(1.0, (drift * expected_direction) / max(abs(immediate), 0.001)))
            retention = max(-1.0, min(1.0, 1.0 + normalized))
            scores.append(retention)
        if not scores:
            return 0.0, "unclear"
        persistence_index = sum(scores) / len(scores)
        if persistence_index >= 0.7:
            return persistence_index, "persisted"
        if persistence_index <= -0.15:
            return persistence_index, "reversed"
        return persistence_index, "faded"

    @staticmethod
    def _aftermath_dominant_zone(
        intervention_artifact: dict,
        stability_signals: dict,
        district_threads: list[dict],
        scenario_outcome: dict,
    ) -> dict:
        affected = intervention_artifact.get("most_affected", {})
        top_affected = ((affected.get("districts") or [{}])[0] or {})
        if top_affected.get("name") or top_affected.get("district_id"):
            return {
                "zone_type": "district",
                "district_id": top_affected.get("district_id"),
                "label": top_affected.get("name") or top_affected.get("district_id"),
            }

        destabilizing_system = next(
            (row for row in (stability_signals.get("systems") or []) if row.get("signal") in {"stabilizing", "deteriorating"}),
            None,
        )
        if destabilizing_system and destabilizing_system.get("system"):
            return {
                "zone_type": "system",
                "system": destabilizing_system.get("system"),
                "label": f"system:{destabilizing_system.get('system')}",
            }

        top_shift = ((scenario_outcome.get("top_shifted_districts") or district_threads or [{}])[0] or {})
        if top_shift.get("name") or top_shift.get("district_id"):
            return {
                "zone_type": "district",
                "district_id": top_shift.get("district_id"),
                "label": top_shift.get("name") or top_shift.get("district_id"),
            }
        return {"zone_type": "none", "label": "none"}

    @staticmethod
    def _build_operator_session_continuity(world_state: dict, scenario_handoff: dict, operator_brief: dict) -> dict:
        scenario_state = world_state.setdefault("scenario_state", {})
        timeline = scenario_state.get("timeline", [])
        timeline_groups = scenario_state.get("timeline_groups", [])
        saved_insights = scenario_state.get("saved_insights", [])
        latest_insight = saved_insights[-1] if saved_insights else {}
        latest_timeline_moment = timeline[-1] if timeline else {}
        resume_focus = {
            "what_happened": scenario_handoff.get("what_happened_so_far", {}).get("summary"),
            "what_matters_now": scenario_handoff.get("what_matters_now", {}),
            "watch_next": (scenario_handoff.get("watch_next") or [])[:3],
            "trend_label": (scenario_handoff.get("trend_balance") or {}).get("label", "mixed_or_flat"),
            "stabilizing_vs_deteriorating": {
                "stabilizing_signals": (scenario_handoff.get("trend_balance") or {}).get("stabilizing_signals", 0),
                "deteriorating_signals": (scenario_handoff.get("trend_balance") or {}).get("deteriorating_signals", 0),
            },
        }
        continuity = {
            "artifact_type": "operator_session_continuity",
            "session_view_id": f"session_view_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "scenario_name": scenario_handoff.get("scenario_name", scenario_state.get("active_scenario_name", "default-baseline")),
            "world_time": scenario_handoff.get("world_time") or world_state.get("world", {}).get("current_time"),
            "resume_focus": {
                **resume_focus,
                "watch_now": operator_brief.get("watch_now", {}),
            },
            "resume_stack": {
                "recent_timeline": [
                    {
                        "moment_id": row.get("moment_id"),
                        "moment_type": row.get("moment_type"),
                        "world_time": row.get("world_time"),
                        "text": row.get("replay_text") or row.get("moment_type", "moment"),
                    }
                    for row in timeline[-4:]
                ],
                "timeline_groups": timeline_groups[:4],
                "last_saved_insight": {
                    "insight_id": latest_insight.get("insight_id"),
                    "saved_at": latest_insight.get("saved_at"),
                    "what_happened": latest_insight.get("what_happened"),
                    "direction": latest_insight.get("direction"),
                } if latest_insight else {},
            },
            "resume_quality": {
                "latest_timeline_moment": {
                    "moment_id": latest_timeline_moment.get("moment_id"),
                    "moment_type": latest_timeline_moment.get("moment_type"),
                    "world_time": latest_timeline_moment.get("world_time"),
                } if latest_timeline_moment else {},
                "priority_actor_count": len((scenario_handoff.get("what_matters_now") or {}).get("priority_actors") or []),
                "watch_item_count": len((scenario_handoff.get("watch_next") or [])[:3]),
            },
        }
        scenario_state["operator_session_view"] = continuity

        history = scenario_state.setdefault("operator_session_history", [])
        previous_entry = history[-1] if history else {}
        latest_moment_type = latest_timeline_moment.get("moment_type")
        latest_moment_id = latest_timeline_moment.get("moment_id")
        compact_signature = AuraliteReportingService._operator_continuity_signature(
            scenario_name=continuity["scenario_name"],
            resume_focus=resume_focus,
            latest_moment_id=latest_moment_id,
            latest_moment_type=latest_moment_type,
        )
        should_capture, capture_reason = AuraliteReportingService._should_capture_session_history(
            previous_entry=previous_entry,
            continuity_signature=compact_signature,
            scenario_name=continuity["scenario_name"],
            latest_moment_type=latest_moment_type,
            world_time=continuity["world_time"],
            resume_focus=resume_focus,
        )
        if should_capture:
            history.append(
                {
                    "session_view_id": continuity["session_view_id"],
                    "scenario_name": continuity["scenario_name"],
                    "world_time": continuity["world_time"],
                    "captured_at": datetime.utcnow().isoformat(),
                    "continuity_signature": compact_signature,
                    "capture_reason": capture_reason,
                    "latest_moment_id": latest_moment_id,
                    "latest_moment_type": latest_moment_type,
                    "trend_label": resume_focus.get("trend_label"),
                    "watch_lead": (resume_focus.get("watch_next") or [None])[0],
                }
            )
        history = history[-12:]
        scenario_state["operator_session_history"] = history
        continuity["history_state"] = {
            "entries": len(history),
            "captured_this_refresh": should_capture,
            "capture_reason": capture_reason,
            "last_captured_at": (history[-1] or {}).get("captured_at") if history else None,
        }
        return continuity

    @staticmethod
    def _operator_continuity_signature(
        scenario_name: str,
        resume_focus: dict,
        latest_moment_id: str | None,
        latest_moment_type: str | None,
    ) -> str:
        watch_next = "|".join((resume_focus.get("watch_next") or [])[:2])
        watch_now = resume_focus.get("what_matters_now", {})
        top_district = ((watch_now.get("districts") or [{}])[0] or {}).get("district_id") or ((watch_now.get("districts") or [{}])[0] or {}).get("label")
        top_resident = ((watch_now.get("residents_households") or [{}])[0] or {}).get("resident_id") or ((watch_now.get("residents_households") or [{}])[0] or {}).get("household_id")
        top_system = ((watch_now.get("systems") or [{}])[0] or {}).get("system")
        return "::".join(
            [
                scenario_name or "default-baseline",
                resume_focus.get("trend_label") or "mixed_or_flat",
                watch_next,
                str(top_district or ""),
                str(top_resident or ""),
                str(top_system or ""),
                str(latest_moment_type or ""),
                str(latest_moment_id or "")[-12:],
            ]
        )

    @staticmethod
    def _should_capture_session_history(
        previous_entry: dict,
        continuity_signature: str,
        scenario_name: str,
        latest_moment_type: str | None,
        world_time: str | None,
        resume_focus: dict,
    ) -> tuple[bool, str]:
        if not previous_entry:
            return True, "initial_capture"
        if previous_entry.get("scenario_name") != scenario_name:
            return True, "scenario_changed"
        if previous_entry.get("continuity_signature") == continuity_signature:
            return False, "unchanged_refresh"
        significant_moment_types = {
            "intervention_applied",
            "scenario_switched",
            "scenario_compared",
            "snapshot_saved",
            "insight_saved",
        }
        if latest_moment_type in significant_moment_types:
            return True, f"moment:{latest_moment_type}"
        previous_world_time = previous_entry.get("world_time")
        if AuraliteReportingService._world_time_gap_hours(previous_world_time, world_time) >= 6:
            return True, "time_anchor_advanced"
        previous_trend = previous_entry.get("trend_label")
        if previous_trend and previous_trend != resume_focus.get("trend_label"):
            return True, "trend_shifted"
        previous_watch = previous_entry.get("watch_lead")
        current_watch = (resume_focus.get("watch_next") or [None])[0]
        if previous_watch and current_watch and previous_watch != current_watch:
            return True, "watch_lead_shifted"
        return False, "unchanged_refresh"

    @staticmethod
    def _world_time_gap_hours(previous_world_time: str | None, current_world_time: str | None) -> float:
        if not previous_world_time or not current_world_time:
            return 0.0
        try:
            previous_dt = datetime.fromisoformat(previous_world_time.replace("Z", "+00:00"))
            current_dt = datetime.fromisoformat(current_world_time.replace("Z", "+00:00"))
        except ValueError:
            return 0.0
        delta = current_dt - previous_dt
        return abs(delta.total_seconds()) / 3600.0

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

    @staticmethod
    def _stability_label(score: float) -> str:
        if score >= 0.03:
            return "stabilizing"
        if score <= -0.03:
            return "deteriorating"
        return "holding_flat"


    @staticmethod
    def _focus_next_check_why(district_driver: str, institution_link: str | None, has_system_link: bool) -> str:
        district_label = (district_driver or "current district pressure line").strip().rstrip(".")
        if has_system_link and institution_link:
            return (
                f"Best immediate follow-up to confirm whether {district_label} is still driving pressure "
                f"through {institution_link.lower()} and resident/household relevance."
            )
        return "Best immediate follow-up to confirm whether district pressure and resident/household relevance are holding or fading."

    @staticmethod
    def _focus_confidence_snapshot(
        top_district_watch: dict,
        top_resident_watch: dict,
        top_system_watch: dict,
        stable_check: str | None,
        check_candidates: list[str],
        previous_focus: dict | None,
    ) -> dict:
        district_score = float(top_district_watch.get("watch_score", 0.0))
        resident_score = float(top_resident_watch.get("watch_score", 0.0))
        system_score = float(top_system_watch.get("watch_score", 0.0))
        coverage = sum(1 for row in [top_district_watch, top_resident_watch, top_system_watch] if row)
        score = min(1.0, max(0.0, (district_score * 0.45) + (resident_score * 0.35) + (system_score * 0.20)))
        score = round(score, 3)
        if score >= 0.62 and coverage >= 2:
            level = "strong"
        elif score >= 0.42:
            level = "moderate"
        else:
            level = "weak"
        was_stable = (
            bool(previous_focus)
            and previous_focus.get("current_district_id") == top_district_watch.get("district_id")
            and previous_focus.get("resident_id") == top_resident_watch.get("resident_id")
            and previous_focus.get("top_system") == top_system_watch.get("system")
        )
        stability = "stable" if was_stable else "tentative"
        check_support = "strongly_supported" if stable_check and stable_check in (check_candidates or [])[:2] else "weakly_supported"
        return {
            "focus_confidence_level": level,
            "focus_confidence_score": score,
            "focus_stability": stability,
            "next_check_support": check_support,
            "evidence_coverage_count": coverage,
        }

    @staticmethod
    def _focus_evidence_snapshot(
        district_watch: dict,
        resident_watch: dict,
        system_watch: dict,
        next_check: str | None,
        next_check_why: str,
    ) -> dict:
        return {
            "district_driver": {
                "source": district_watch.get("watch_reason") or district_watch.get("label"),
                "watch_score": round(float(district_watch.get("watch_score", 0.0)), 3) if district_watch else 0.0,
            },
            "resident_household_relevance": {
                "source": resident_watch.get("watch_reason") or resident_watch.get("resident_name") or resident_watch.get("label"),
                "watch_score": round(float(resident_watch.get("watch_score", 0.0)), 3) if resident_watch else 0.0,
            },
            "institution_link": {
                "source": system_watch.get("system"),
                "watch_score": round(float(system_watch.get("watch_score", 0.0)), 3) if system_watch else 0.0,
            },
            "next_check": {
                "source": next_check,
                "rationale": next_check_why,
            },
        }
