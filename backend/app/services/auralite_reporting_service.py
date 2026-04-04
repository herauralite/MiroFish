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
    def assemble_artifact_stack(
        world_state: dict,
        base_artifacts: dict,
        world_artifact: dict,
        intervention_artifact: dict,
        comparison_artifact: dict,
    ) -> dict:
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
            watch_next.append(f"Monitor {district_threads[0].get('name', district_threads[0].get('district_id', 'top district'))} for continued phase drift.")
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
    ) -> dict:
        return {
            "artifact_type": "operator_brief",
            "world_time": scenario_outcome.get("world_time"),
            "scenario_name": scenario_outcome.get("scenario_name"),
            "what_happened": scenario_digest.get("what_happened_overall") or (scenario_outcome.get("why_changed") or ["No scenario-level shift detected yet."])[0],
            "who_matters": (key_actor_escalation.get("high_priority_actors") or [])[:3],
            "watch_now": {
                "districts": (monitoring_watchlist.get("districts_to_watch") or [])[:2],
                "residents_households": (monitoring_watchlist.get("residents_households_to_watch") or [])[:2],
                "systems": (monitoring_watchlist.get("systems_to_watch") or [])[:2],
            },
            "stability_now": {
                "districts": (stability_signals.get("districts") or [])[:2],
                "residents_households": (stability_signals.get("residents_households") or [])[:2],
                "systems": (stability_signals.get("systems") or [])[:2],
            },
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

    @staticmethod
    def _stability_label(score: float) -> str:
        if score >= 0.03:
            return "stabilizing"
        if score <= -0.03:
            return "deteriorating"
        return "holding_flat"
