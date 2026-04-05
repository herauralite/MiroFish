from datetime import datetime

from ..models.auralite_world import AuraliteWorld
from .auralite_intervention_service import AuraliteInterventionService
from .auralite_persistence_service import AuralitePersistenceService
from .auralite_reporting_service import AuraliteReportingService
from .auralite_runtime_service import AuraliteRuntimeService
from .auralite_seed_service import AuraliteSeedService


class AuraliteWorldService:
    WORLD_ID = 'auralite_world_v1'

    def __init__(self):
        self.seed_service = AuraliteSeedService(seed=42)

    def get_or_create_world(self) -> dict:
        world = AuralitePersistenceService.load_world(self.WORLD_ID)
        if world:
            world = self._ensure_milestone_03_shape(world)
            world = self._sync_reporting_scenario_state(world)
            return self._auto_advance(world)
        return self.reset_world()

    def reset_world(self, population_target: int = 240) -> dict:
        now = datetime.utcnow().isoformat()
        seed_bundle = self.seed_service.create_seed_bundle(population_target=population_target)
        world_model = AuraliteWorld(
            world_id=self.WORLD_ID,
            city_id=seed_bundle['city']['city_id'],
            current_time=datetime(2026, 1, 5, 6, 0, 0).isoformat(),
            time_speed=12,
            is_running=True,
            created_at=now,
            updated_at=now,
            seed=42,
            last_tick_at=now,
        )
        world = {
            'world': world_model.to_dict(),
            'city': seed_bundle['city'],
            'districts': seed_bundle['districts'],
            'locations': seed_bundle['locations'],
            'persons': seed_bundle['persons'],
            'households': seed_bundle['households'],
            'institutions': seed_bundle['institutions'],
            'social_graph': seed_bundle.get('social_graph', {}),
            'intervention_state': {
                'last_applied_at': None,
                'history': [],
                'available_levers': ['rebalance_housing_pressure', 'boost_transit_service', 'expand_service_access'],
            },
            'scenario_state': {
                'active_scenario_name': 'default-baseline',
                'snapshots': [],
                'last_comparison': {},
                'baseline_snapshot_id': None,
                'last_comparison_report': {},
                'scenario_start_anchor': {},
                'timeline': [],
                'last_timeline_moment_id': None,
                'saved_insights': [],
                'reporting_views': {},
                'timeline_replay': {},
                'timeline_groups': [],
                'insight_filter_catalog': {'source_types': [], 'directions': [], 'scenario_names': [], 'count': 0},
                'last_saved_insight_id': None,
                'operator_session_view': {},
                'operator_session_history': [],
                'historical_pattern_memory': {},
            },
            'propagation_state': {
                'schema_version': 'm11-regime-cycle-v1',
                'last_updated_at': None,
                'district_neighbor_events': [],
                'social_events': [],
                'district_recent_impacts': {},
                'resident_recent_impacts': {},
                'household_recent_impacts': {},
                'notes': [
                    'Lightweight propagation scaffold; bounded effects only.',
                    'Designed for explainability and future event-system expansion.',
                ],
            },
        }
        world = self._recompute_world_views(world, reason='reset', tick_minutes=0)
        self.save_world_payload(world)
        return world

    def save_world_payload(self, world: dict):
        AuralitePersistenceService.save_world(self.WORLD_ID, world)

    def load_world_payload(self) -> dict | None:
        return AuralitePersistenceService.load_world(self.WORLD_ID)

    def control_runtime(self, action: str, time_speed: float | None = None) -> dict:
        world = self.get_or_create_world()
        if action == 'start':
            world['world']['is_running'] = True
            world['world']['last_tick_at'] = datetime.utcnow().isoformat()
        elif action == 'pause':
            world['world']['is_running'] = False
        elif action == 'speed' and time_speed is not None:
            world['world']['time_speed'] = max(0.25, min(60, float(time_speed)))
        self.save_world_payload(world)
        return world

    def manual_tick(self, minutes: int = 15) -> dict:
        world = self.get_or_create_world()
        updated = self._recompute_world_views(world, reason='manual_tick', tick_minutes=minutes)
        updated['world']['last_tick_at'] = datetime.utcnow().isoformat()
        self.save_world_payload(updated)
        return updated

    def apply_interventions(self, changes: list[dict], notes: str = '') -> dict:
        world = self.get_or_create_world()
        world, record = AuraliteInterventionService.apply_changes(world, changes, notes=notes)
        world = self._recompute_world_views(world, reason='intervention_apply', tick_minutes=0)
        AuraliteInterventionService.enrich_record_with_after(record, world)
        world['intervention_state']['history'][-1] = record
        world['intervention_state']['active_aftermath'] = AuraliteInterventionService._next_active_aftermath(
            existing=world['intervention_state'].get('active_aftermath', []),
            record=record,
        )
        world['scenario_state']['last_comparison'] = record.get('effects', {}).get('delta_summary', {})
        world['scenario_state']['last_comparison_report'] = {
            'kind': 'intervention',
            'report': {
                'delta_summary': record.get('effects', {}).get('delta_summary', {}),
                'aftermath_hooks': record.get('effects', {}).get('aftermath_hooks', []),
            },
        }
        AuraliteReportingService.record_scenario_moment(
            world_state=world,
            moment_type='intervention_applied',
            source='intervention_apply',
            payload={
                'intervention_id': record.get('intervention_id'),
                'changes': record.get('changes', []),
                'delta_summary': record.get('effects', {}).get('delta_summary', {}),
            },
            note=notes,
        )
        AuraliteReportingService.build_saved_scenario_insight(
            world_state=world,
            source='intervention_apply',
            note=notes or f"intervention:{record.get('intervention_id', 'unknown')}",
        )
        self.save_world_payload(world)
        return {'world': world, 'record': record}

    def save_named_snapshot(self, snapshot_name: str, label: str = 'manual') -> dict:
        world = self.get_or_create_world()
        snapshot_id = AuralitePersistenceService.save_snapshot(self.WORLD_ID, world)
        summary = self._world_comparison_summary(world)
        world.setdefault('scenario_state', {})
        world['scenario_state'].setdefault('snapshots', []).append({
            'snapshot_id': snapshot_id,
            'snapshot_name': snapshot_name,
            'label': label,
            'captured_at': datetime.utcnow().isoformat(),
            'world_time': world.get('world', {}).get('current_time'),
            'summary': summary,
        })
        world['scenario_state']['snapshots'] = world['scenario_state']['snapshots'][-20:]
        if label == 'baseline':
            world['scenario_state']['baseline_snapshot_id'] = snapshot_id
        AuraliteReportingService.record_scenario_moment(
            world_state=world,
            moment_type='snapshot_saved',
            source='snapshot_save',
            payload={
                'snapshot_id': snapshot_id,
                'snapshot_name': snapshot_name,
                'label': label,
                'summary': summary,
            },
            note=f'{label}:{snapshot_name}',
        )
        AuraliteReportingService.build_saved_scenario_insight(
            world_state=world,
            source='snapshot_save',
            note=f'{label}:{snapshot_name}',
        )
        AuraliteReportingService.sync_reporting_history_views(world)
        self.save_world_payload(world)
        return {'snapshot_id': snapshot_id, 'summary': summary}

    def load_named_snapshot(self, snapshot_id: str) -> dict | None:
        snapshot = AuralitePersistenceService.load_snapshot(self.WORLD_ID, snapshot_id)
        if not snapshot:
            return None
        snapshot = self._ensure_milestone_03_shape(snapshot)
        snapshot = self._recompute_world_views(snapshot, reason='snapshot_load', tick_minutes=0)
        self.save_world_payload(snapshot)
        return snapshot

    def set_active_scenario(self, scenario_name: str) -> dict:
        world = self.get_or_create_world()
        world.setdefault('scenario_state', {})
        next_name = scenario_name.strip() or 'default-baseline'
        world['scenario_state']['active_scenario_name'] = next_name
        world['scenario_state']['scenario_start_anchor'] = {
            'scenario_name': next_name,
            'anchored_at': world.get('world', {}).get('current_time'),
            'anchor_source': 'scenario_switch',
            'start_summary': AuraliteInterventionService.world_summary(world),
        }
        AuraliteReportingService.record_scenario_moment(
            world_state=world,
            moment_type='scenario_switched',
            source='scenario_switch',
            payload={'scenario_name': next_name},
            note=f'scenario:{next_name}',
        )
        AuraliteReportingService.build_saved_scenario_insight(
            world_state=world,
            source='scenario_switch',
            note=f'scenario:{next_name}',
        )
        world = self._recompute_world_views(world, reason='scenario_switch', tick_minutes=0)
        AuraliteReportingService.sync_reporting_history_views(world)
        self.save_world_payload(world)
        return world

    def compare_states(
        self,
        baseline_snapshot_id: str | None = None,
        compare_snapshot_id: str | None = None,
    ) -> dict:
        world = self.get_or_create_world()
        scenario_state = world.setdefault('scenario_state', {})
        baseline_snapshot_id = baseline_snapshot_id or scenario_state.get('baseline_snapshot_id')
        if not baseline_snapshot_id:
            raise ValueError('baseline snapshot is required')

        baseline = AuralitePersistenceService.load_snapshot(self.WORLD_ID, baseline_snapshot_id)
        if not baseline:
            raise ValueError('baseline snapshot not found')
        baseline = self._ensure_milestone_03_shape(baseline)

        target_world = world
        current_label = 'current'
        if compare_snapshot_id:
            candidate = AuralitePersistenceService.load_snapshot(self.WORLD_ID, compare_snapshot_id)
            if not candidate:
                raise ValueError('comparison snapshot not found')
            target_world = self._ensure_milestone_03_shape(candidate)
            current_label = f'snapshot:{compare_snapshot_id}'

        report = AuraliteInterventionService.comparison_report(
            baseline_state=baseline,
            current_state=target_world,
            baseline_label=f'snapshot:{baseline_snapshot_id}',
            current_label=current_label,
        )
        scenario_state['baseline_snapshot_id'] = baseline_snapshot_id
        scenario_state['last_comparison'] = report.get('delta_summary', {})
        scenario_state['last_comparison_report'] = {
            'kind': 'snapshot_compare',
            'report': report,
        }
        AuraliteReportingService.record_scenario_moment(
            world_state=world,
            moment_type='scenario_compared',
            source='snapshot_compare',
            payload={
                'baseline_snapshot_id': baseline_snapshot_id,
                'compare_snapshot_id': compare_snapshot_id,
                'direction': (report.get('condition_direction') or 'flat'),
                'delta_summary': report.get('delta_summary', {}),
            },
            note=f'baseline:{baseline_snapshot_id}',
        )
        AuraliteReportingService.build_saved_scenario_insight(
            world_state=world,
            source='snapshot_compare',
            note=f'baseline:{baseline_snapshot_id}',
        )
        AuraliteReportingService.sync_reporting_history_views(world)
        self.save_world_payload(world)
        return report

    def _auto_advance(self, world: dict) -> dict:
        if not world['world']['is_running']:
            world = self._recompute_world_views(world, reason='auto_pause_refresh', tick_minutes=0)
            self.save_world_payload(world)
            return world
        last_tick_at = world['world'].get('last_tick_at')
        if not last_tick_at:
            world['world']['last_tick_at'] = datetime.utcnow().isoformat()
            self.save_world_payload(world)
            return world
        elapsed = (datetime.utcnow() - datetime.fromisoformat(last_tick_at)).total_seconds()
        sim_minutes = int((elapsed / 60) * world['world'].get('time_speed', 1))
        if sim_minutes <= 0:
            return world
        updated = self._recompute_world_views(world, reason='auto_advance', tick_minutes=sim_minutes)
        updated['world']['last_tick_at'] = datetime.utcnow().isoformat()
        self.save_world_payload(updated)
        return updated

    def _ensure_milestone_03_shape(self, world: dict) -> dict:
        world.setdefault('institutions', [])
        world.setdefault('social_graph', {
            'schema_version': 'm08-lightweight-social-v1',
            'edge_counts': {'household': 0, 'coworker': 0, 'district_local': 0},
            'district_neighbors': {},
            'notes': ['Lightweight relationship hooks only; not a full social-memory graph.'],
        })
        world['social_graph'].setdefault('district_neighbors', {})
        world.setdefault('intervention_state', {
            'last_applied_at': None,
            'history': [],
            'available_levers': ['rebalance_housing_pressure', 'boost_transit_service', 'expand_service_access'],
        })
        world['intervention_state'].setdefault('last_applied_at', None)
        world['intervention_state'].setdefault('history', [])
        world['intervention_state'].setdefault(
            'available_levers',
            ['rebalance_housing_pressure', 'boost_transit_service', 'expand_service_access'],
        )
        world['intervention_state']['active_aftermath'] = self._normalize_active_aftermath(
            world['intervention_state'].get('active_aftermath', []),
        )

        for household in world.get('households', []):
            household.setdefault('monthly_income', 0.0)
            household.setdefault('monthly_rent', 0.0)
            burden = household.setdefault('housing_cost_burden', 0.0)
            household.setdefault('pressure_index', round(min(1.0, burden + 0.1), 3))
            household.setdefault('pressure_level', 'medium' if burden >= 0.3 else 'low')
            household.setdefault('landlord_id', None)
            household.setdefault('eviction_risk', round(min(1.0, household.get('pressure_index', 0.0) * 0.85), 3))
            household.setdefault('context', {})
            household['context'].setdefault('hardship_index', household.get('pressure_index', 0.0))
            household['context'].setdefault('hardship_cluster_weight', 0.0)
            household['context'].setdefault('pressure_cycle_load', 0.0)
            household.setdefault('social_context', {})
            household.setdefault('trajectory', {'signals': {}, 'horizon': 'short_to_medium_term'})
            household.setdefault('derived_summary', {})
            household.setdefault('adaptation_state', {
                'service_scarcity_streak': 0,
                'housing_instability_streak': 0,
                'commute_friction_streak': 0,
                'job_quality_streak': 0,
                'support_buffer_streak': 0,
                'adaptation_drag': 0.0,
                'hardship_cluster_weight': 0.0,
            })

        household_index = {h['household_id']: h for h in world.get('households', [])}
        for person in world.get('persons', []):
            person.setdefault('employment_status', 'employed')
            person.setdefault('hourly_wage', 0.0)
            hh = household_index.get(person.get('household_id', ''), {})
            person.setdefault('housing_burden_share', hh.get('housing_cost_burden', 0.0))
            person.setdefault('shift_window', 'day')
            person.setdefault('employer_id', None)
            person.setdefault('transit_service_id', None)
            person.setdefault('service_provider_id', None)
            person.setdefault('service_access_score', 0.5)
            person.setdefault('social_ties', [])
            person.setdefault('social_context', {})
            person.setdefault('state_summary', {})
            person['state_summary'].setdefault('social_support_index', person['social_context'].get('support_index', 0.5))
            person['state_summary'].setdefault('social_strain_index', person['social_context'].get('strain_index', 0.5))
            person['state_summary'].setdefault('job_quality_pressure', 0.0)
            person['state_summary'].setdefault('housing_instability_pressure', 0.0)
            person['state_summary'].setdefault('commute_friction', 0.0)
            person['state_summary'].setdefault('service_scarcity', 0.0)
            person['state_summary'].setdefault('support_buffer', 0.5)
            person['state_summary'].setdefault('adaptation_drag', 0.0)
            person['state_summary'].setdefault('adaptation_support', 0.0)
            person.setdefault('trajectory', {'signals': {}, 'horizon': 'short_to_medium_term'})
            person.setdefault('derived_summary', {})
            person.setdefault('adaptation_state', {
                'service_scarcity_streak': 0,
                'housing_instability_streak': 0,
                'commute_friction_streak': 0,
                'job_quality_streak': 0,
                'support_buffer_streak': 0,
                'adaptation_drag': 0.0,
                'adaptation_support': 0.0,
            })

        for institution in world.get('institutions', []):
            institution.setdefault('pressure_index', 0.35)
            institution.setdefault('access_score', 0.55)
            institution.setdefault('arc_state', {
                'effective_pressure': float(institution.get('pressure_index', 0.35)),
                'effective_access': float(institution.get('access_score', 0.55)),
                'pressure_delta': 0.0,
                'stress_streak': 0,
                'recovery_streak': 0,
                'utilization': 0.0,
                'utilization_pressure': 0.0,
                'district_pressure_context': 0.0,
                'drift_signal': 0.0,
                'resilience_buffer': 0.0,
                'type_service_impact': 0.0,
                'type_buffering': 0.0,
            })

        for district in world.get('districts', []):
            district.setdefault('pressure_index', 0.0)
            district.setdefault('employment_rate', 0.0)
            district.setdefault('average_hourly_wage', 0.0)
            district.setdefault('average_housing_burden', 0.0)
            district.setdefault('state_phase', 'steady')
            district.setdefault('employment_pressure', 0.0)
            district.setdefault('household_pressure', 0.0)
            district.setdefault('service_access_score', 0.0)
            district.setdefault('transit_reliability', 0.0)
            district.setdefault('social_support_score', 0.0)
            district.setdefault('institution_summary', {})
            district.setdefault('derived_summary', {})
            district.setdefault('arc_state', {
                'phase': district.get('state_phase', 'steady'),
                'last_pressure_index': float(district.get('pressure_index', 0.0)),
                'effective_pressure_index': float(district.get('pressure_index', 0.0)),
                'pressure_delta': 0.0,
                'rolling_pressure_delta': 0.0,
                'sustained_pressure_ticks': 0,
                'sustained_recovery_ticks': 0,
                'local_recovery_context': 0.5,
                'archetype_recovery_bias': 1.0,
                'phase_momentum': 0.0,
                'inflection_score': 0.0,
                'hardship_cluster': 0.0,
                'institution_drift': 0.0,
                'resilience_buffer': 0.0,
                'cumulative_stress_load': 0.0,
                'recovery_durability': 0.0,
                'shallow_recovery_risk': 0.0,
                'decline_lock': False,
                'recovery_lock': False,
                'tipping_thresholds': {},
                'momentum_management': {},
            })
            district['arc_state'].setdefault('cumulative_stress_load', 0.0)
            district['arc_state'].setdefault('recovery_durability', 0.0)
            district['arc_state'].setdefault('shallow_recovery_risk', 0.0)
            district.setdefault('derived_summary', {}).setdefault('ripple_context', {})
            district['derived_summary']['ripple_context'].setdefault('stressed_cluster_share', 0.0)
            district['derived_summary']['ripple_context'].setdefault('recovery_cluster_share', 0.0)
            district['derived_summary']['ripple_context'].setdefault('cluster_amplification', 0.0)

        world.setdefault('city', {}).setdefault('world_metrics', {})
        world['city'].setdefault('regime_state', {})
        world['city']['world_metrics'].setdefault('regime_state', {
            'phase': 'mixed_transition',
            'confidence': 0.0,
            'regime_shift_candidate': False,
            'signals': {},
            'interpretation': {},
            'lead_lag_districts': {
                'phase_context': 'mixed_transition',
                'decline_leaders': [],
                'recovery_leaders': [],
                'fragile_laggards': [],
                'mixed_transition_districts': [],
            },
            'recovery_spread_state': {'lane': 'mixed'},
            'intervention_regime_effect': {'signal': 'no_active_intervention_signal'},
            'tipping_thresholds': {},
            'leverage_points': {},
            'intervention_lever_relevance': {'levers': {}},
            'momentum_management': {},
        })
        regime_state = world['city']['world_metrics'].setdefault('regime_state', {})
        regime_state.setdefault('interpretation', {})
        regime_state.setdefault('lead_lag_districts', {
            'phase_context': regime_state.get('phase', 'mixed_transition'),
            'decline_leaders': [],
            'recovery_leaders': [],
            'fragile_laggards': [],
            'mixed_transition_districts': [],
        })
        regime_state.setdefault('recovery_spread_state', {'lane': 'mixed'})
        regime_state.setdefault('intervention_regime_effect', {'signal': 'no_active_intervention_signal'})
        regime_state.setdefault('tipping_thresholds', {})
        regime_state.setdefault('leverage_points', {})
        regime_state.setdefault('intervention_lever_relevance', {'levers': {}})
        regime_state.setdefault('momentum_management', {})
        world['city']['regime_state'] = regime_state
        world.setdefault('reporting_state', {})
        world['reporting_state'].setdefault('artifacts', {})
        world['reporting_state'].setdefault('assembled_reports', {})
        world['reporting_state'].setdefault('previous_world_summary', {})
        world['reporting_state'].setdefault('previous_district_metrics', {})
        world['reporting_state'].setdefault('previous_person_metrics', {})
        world['reporting_state'].setdefault('previous_household_metrics', {})
        world.setdefault('scenario_state', {
            'active_scenario_name': 'default-baseline',
            'snapshots': [],
            'last_comparison': {},
            'baseline_snapshot_id': None,
            'last_comparison_report': {},
            'scenario_start_anchor': {},
            'timeline': [],
            'last_timeline_moment_id': None,
            'saved_insights': [],
            'reporting_views': {},
            'timeline_replay': {},
            'timeline_groups': [],
            'insight_filter_catalog': {'source_types': [], 'directions': [], 'scenario_names': [], 'count': 0},
            'last_saved_insight_id': None,
            'operator_session_view': {},
            'operator_session_history': [],
            'historical_pattern_memory': {},
        })
        world.setdefault('propagation_state', {
            'schema_version': 'm11-regime-cycle-v1',
            'last_updated_at': None,
            'district_neighbor_events': [],
            'social_events': [],
            'district_recent_impacts': {},
            'resident_recent_impacts': {},
            'household_recent_impacts': {},
            'notes': ['Cross-system turning and contagion scaffold; bounded effects only.'],
        })
        world['propagation_state']['schema_version'] = 'm11-regime-cycle-v1'
        world['scenario_state'].setdefault('active_scenario_name', 'default-baseline')
        world['scenario_state'].setdefault('snapshots', [])
        world['scenario_state'].setdefault('last_comparison', {})
        world['scenario_state'].setdefault('baseline_snapshot_id', None)
        world['scenario_state'].setdefault('last_comparison_report', {})
        world['scenario_state'].setdefault('scenario_start_anchor', {})
        world['scenario_state'].setdefault('timeline', [])
        world['scenario_state'].setdefault('last_timeline_moment_id', None)
        world['scenario_state'].setdefault('run_summary', {})
        world['scenario_state'].setdefault('scenario_outcome', {})
        world['scenario_state'].setdefault('scenario_insight_report', {})
        world['scenario_state'].setdefault('saved_insights', [])
        world['scenario_state'].setdefault('reporting_views', {})
        world['scenario_state'].setdefault('timeline_replay', {})
        world['scenario_state'].setdefault('timeline_groups', [])
        world['scenario_state'].setdefault(
            'insight_filter_catalog',
            {'source_types': [], 'directions': [], 'scenario_names': [], 'count': 0},
        )
        world['scenario_state'].setdefault('last_saved_insight_id', None)
        world['scenario_state'].setdefault('operator_session_view', {})
        world['scenario_state'].setdefault('operator_session_history', [])
        world['scenario_state'].setdefault('historical_pattern_memory', {})
        world['scenario_state'].setdefault('city_regime_state', {})
        world['scenario_state'].setdefault('regime_shift_candidate', False)
        run_summary = self._ensure_run_outcome_defaults(world['scenario_state'].setdefault('run_summary', {}))
        scenario_outcome = self._ensure_run_outcome_defaults(world['scenario_state'].setdefault('scenario_outcome', {}))
        scenario_insight_report = self._ensure_scenario_insight_defaults(world['scenario_state'].setdefault('scenario_insight_report', {}))
        if world['scenario_state'].get('saved_insights'):
            world['scenario_state']['insight_filter_catalog'] = AuraliteReportingService._build_insight_filter_catalog(
                world['scenario_state']['saved_insights'],
            )
        return world

    def _recompute_world_views(self, world: dict, reason: str, tick_minutes: int = 0) -> dict:
        updated = AuraliteRuntimeService.tick(world, tick_minutes)
        updated.setdefault('world', {})['last_recompute_reason'] = reason
        updated = self._sync_reporting_scenario_state(updated)
        AuraliteReportingService.sync_reporting_history_views(updated)
        return updated

    def _sync_reporting_scenario_state(self, world: dict) -> dict:
        scenario_state = world.setdefault('scenario_state', {})
        reporting_state = world.setdefault('reporting_state', {})
        artifacts = reporting_state.setdefault('artifacts', {})
        assembled = reporting_state.setdefault('assembled_reports', {})

        run_outcome = artifacts.get('scenario_outcome') or scenario_state.get('run_summary') or {}
        insight_report = assembled.get('scenario_insight_report') or scenario_state.get('scenario_insight_report') or {}
        session_view = artifacts.get('operator_session_continuity') or scenario_state.get('operator_session_view') or {}
        if not artifacts.get('scenario_outcome') and scenario_state.get('scenario_outcome'):
            artifacts['scenario_outcome'] = scenario_state.get('scenario_outcome')
        if not assembled.get('scenario_insight_report') and scenario_state.get('scenario_insight_report'):
            assembled['scenario_insight_report'] = scenario_state.get('scenario_insight_report')
        scenario_state['run_summary'] = run_outcome
        scenario_state['scenario_outcome'] = run_outcome
        scenario_state['city_regime_state'] = run_outcome.get('city_regime_state', {})
        scenario_state['regime_shift_candidate'] = bool(run_outcome.get('regime_shift_candidate', False))
        run_outcome = self._ensure_run_outcome_defaults(run_outcome)
        scenario_state['scenario_insight_report'] = insight_report
        scenario_state['scenario_insight_report'] = self._ensure_scenario_insight_defaults(scenario_state['scenario_insight_report'])
        for artifact_key in ('scenario_digest', 'operator_brief', 'scenario_handoff'):
            artifact = artifacts.setdefault(artifact_key, {})
            artifact.setdefault('scenario_archetype_memory', run_outcome.get('scenario_archetype_memory', {}))
            artifact.setdefault('combined_pattern_groupings', run_outcome.get('combined_pattern_groupings', {}))
            artifact.setdefault('weak_vs_broad_review_signals', run_outcome.get('weak_vs_broad_review_signals', {}))
            artifact.setdefault('family_level_intervention_review', run_outcome.get('family_level_intervention_review', {}))
            artifact.setdefault('scenario_family_fit_state', run_outcome.get('scenario_family_fit_state', {}))
            artifact.setdefault('scenario_novelty_state', run_outcome.get('scenario_novelty_state', {}))
            artifact.setdefault('hybrid_family_state', run_outcome.get('hybrid_family_state', {}))
            artifact.setdefault('evidence_confidence_state', run_outcome.get('evidence_confidence_state', {}))
            artifact.setdefault('nearest_analog_state', run_outcome.get('nearest_analog_state', {}))
            artifact.setdefault('analog_confidence_state', run_outcome.get('analog_confidence_state', {}))
            artifact.setdefault('partial_analog_support_state', run_outcome.get('partial_analog_support_state', {}))
            artifact.setdefault('precedent_quality_state', run_outcome.get('precedent_quality_state', {}))
            artifact.setdefault('precedent_agreement_state', run_outcome.get('precedent_agreement_state', {}))
            artifact.setdefault('precedent_readiness_state', run_outcome.get('precedent_readiness_state', {}))
            artifact.setdefault('review_readiness_state', run_outcome.get('review_readiness_state', {}))
            artifact.setdefault('exception_review_state', run_outcome.get('exception_review_state', {}))
            artifact.setdefault('precedent_downgrade_state', run_outcome.get('precedent_downgrade_state', {}))
            artifact.setdefault('audit_basis_state', run_outcome.get('audit_basis_state', {}))
            artifact.setdefault('evidence_lane_state', run_outcome.get('evidence_lane_state', {}))
            artifact.setdefault('underdetermined_review_state', run_outcome.get('underdetermined_review_state', {}))
            artifact.setdefault('review_synthesis_state', run_outcome.get('review_synthesis_state', {}))
            artifact.setdefault('synthesis_contestation_state', run_outcome.get('synthesis_contestation_state', {}))
            artifact.setdefault('synthesis_downweight_state', run_outcome.get('synthesis_downweight_state', {}))
            artifact.setdefault('review_conclusion_state', run_outcome.get('review_conclusion_state', {}))
            artifact.setdefault('review_takeaway_caveat_state', run_outcome.get('review_takeaway_caveat_state', {}))
            artifact.setdefault('cautious_conclusion_state', run_outcome.get('cautious_conclusion_state', {}))
            artifact.setdefault('operator_conclusion_evidence', run_outcome.get('operator_conclusion_evidence', {}))
            artifact.setdefault('review_verdict_state', run_outcome.get('review_verdict_state', {}))
            artifact.setdefault('verdict_stability_state', run_outcome.get('verdict_stability_state', {}))
            artifact.setdefault('verdict_caveat_override_state', run_outcome.get('verdict_caveat_override_state', {}))
            artifact.setdefault('operator_verdict_evidence', run_outcome.get('operator_verdict_evidence', {}))
            artifact.setdefault('review_disposition_state', run_outcome.get('review_disposition_state', {}))
            artifact.setdefault('disposition_distinction_state', run_outcome.get('disposition_distinction_state', {}))
            artifact.setdefault('unresolved_disposition_state', run_outcome.get('unresolved_disposition_state', {}))
            artifact.setdefault('operator_disposition_evidence', run_outcome.get('operator_disposition_evidence', {}))
            artifact.setdefault('review_closure_state', run_outcome.get('review_closure_state', {}))
            artifact.setdefault('operator_review_closure_evidence', run_outcome.get('operator_review_closure_evidence', {}))
            artifact.setdefault('review_resolution_state', run_outcome.get('review_resolution_state', {}))
            artifact.setdefault('operator_review_resolution_evidence', run_outcome.get('operator_review_resolution_evidence', {}))
            artifact.setdefault('review_finalization_state', run_outcome.get('review_finalization_state', {}))
            artifact.setdefault('operator_review_finalization_evidence', run_outcome.get('operator_review_finalization_evidence', {}))
            artifact.setdefault('review_settlement_state', run_outcome.get('review_settlement_state', {}))
            artifact.setdefault('operator_review_settlement_evidence', run_outcome.get('operator_review_settlement_evidence', {}))
            artifact.setdefault('review_archival_state', run_outcome.get('review_archival_state', {}))
            artifact.setdefault('operator_review_archival_evidence', run_outcome.get('operator_review_archival_evidence', {}))
            artifact.setdefault('operator_family_fit_confidence', [])
            artifact.setdefault('operator_scenario_archetype_evidence', run_outcome.get('operator_scenario_archetype_evidence', {}))
            artifact.setdefault('operator_analog_evidence', run_outcome.get('operator_analog_evidence', {}))
            artifact.setdefault('operator_precedent_evidence', run_outcome.get('operator_precedent_evidence', {}))
            artifact.setdefault('operator_review_stance_evidence', run_outcome.get('operator_review_stance_evidence', {}))
            artifact.setdefault('operator_audit_basis_evidence', run_outcome.get('operator_audit_basis_evidence', {}))
            artifact.setdefault('operator_review_synthesis_evidence', run_outcome.get('operator_review_synthesis_evidence', {}))
            artifact.setdefault('operator_novelty_outlier_evidence', {})
            artifact.setdefault('divergence_review_state', run_outcome.get('divergence_review_state', {}))
            artifact.setdefault('leverage_vs_regime_separation', (run_outcome.get('divergence_review_state', {}) or {}).get('leverage_vs_regime_separation', {}))
            artifact.setdefault('threshold_momentum_sensitivity', (run_outcome.get('divergence_review_state', {}) or {}).get('threshold_momentum_sensitivity', {}))
            artifact.setdefault('operator_intervention_review_evidence', {})
            artifact.setdefault('operator_divergence_evidence', {})
            artifact.setdefault('historical_divergence_evidence_lines', [])
            artifact.setdefault('compact_historical_evidence_lines', [])
            artifact.setdefault('what_differed_this_time', [])
            artifact.setdefault('counterfactual_operator_evidence', {})
            artifact.setdefault('operator_scenario_archetype_summary', [])
            artifact.setdefault('compact_historical_synthesis_lines', [])
            artifact.setdefault('compact_historical_conclusion_lines', [])
            artifact.setdefault('compact_historical_verdict_lines', [])
            artifact.setdefault('compact_historical_disposition_lines', run_outcome.get('compact_historical_disposition_lines', []))
            artifact.setdefault('compact_historical_closure_lines', run_outcome.get('compact_historical_closure_lines', []))
            artifact.setdefault('compact_historical_resolution_lines', run_outcome.get('compact_historical_resolution_lines', []))
            artifact.setdefault('compact_historical_finalization_lines', run_outcome.get('compact_historical_finalization_lines', []))
            artifact.setdefault('compact_historical_settlement_lines', run_outcome.get('compact_historical_settlement_lines', []))
            artifact.setdefault('compact_historical_archival_lines', run_outcome.get('compact_historical_archival_lines', []))
        scenario_state.setdefault('historical_pattern_memory', run_outcome.get('historical_pattern_memory', {}))
        if scenario_state.get('historical_pattern_memory') and not scenario_state['historical_pattern_memory'].get('divergence_review_state'):
            scenario_state['historical_pattern_memory']['divergence_review_state'] = {}
        if scenario_state.get('historical_pattern_memory'):
            scenario_state['historical_pattern_memory'].setdefault('family_level_intervention_review', run_outcome.get('family_level_intervention_review', {}))
            scenario_state['historical_pattern_memory'].setdefault('scenario_family_fit_state', run_outcome.get('scenario_family_fit_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('scenario_novelty_state', run_outcome.get('scenario_novelty_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('hybrid_family_state', run_outcome.get('hybrid_family_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('evidence_confidence_state', run_outcome.get('evidence_confidence_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('nearest_analog_state', run_outcome.get('nearest_analog_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('analog_confidence_state', run_outcome.get('analog_confidence_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('partial_analog_support_state', run_outcome.get('partial_analog_support_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('precedent_quality_state', run_outcome.get('precedent_quality_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('precedent_agreement_state', run_outcome.get('precedent_agreement_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('precedent_readiness_state', run_outcome.get('precedent_readiness_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('review_readiness_state', run_outcome.get('review_readiness_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('exception_review_state', run_outcome.get('exception_review_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('precedent_downgrade_state', run_outcome.get('precedent_downgrade_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('audit_basis_state', run_outcome.get('audit_basis_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('evidence_lane_state', run_outcome.get('evidence_lane_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('underdetermined_review_state', run_outcome.get('underdetermined_review_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('review_synthesis_state', run_outcome.get('review_synthesis_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('synthesis_contestation_state', run_outcome.get('synthesis_contestation_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('synthesis_downweight_state', run_outcome.get('synthesis_downweight_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('review_conclusion_state', run_outcome.get('review_conclusion_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('review_takeaway_caveat_state', run_outcome.get('review_takeaway_caveat_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('cautious_conclusion_state', run_outcome.get('cautious_conclusion_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('operator_conclusion_evidence', run_outcome.get('operator_conclusion_evidence', {}))
            scenario_state['historical_pattern_memory'].setdefault('review_verdict_state', run_outcome.get('review_verdict_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('verdict_stability_state', run_outcome.get('verdict_stability_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('verdict_caveat_override_state', run_outcome.get('verdict_caveat_override_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('operator_verdict_evidence', run_outcome.get('operator_verdict_evidence', {}))
            scenario_state['historical_pattern_memory'].setdefault('review_disposition_state', run_outcome.get('review_disposition_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('disposition_distinction_state', run_outcome.get('disposition_distinction_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('unresolved_disposition_state', run_outcome.get('unresolved_disposition_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('operator_disposition_evidence', run_outcome.get('operator_disposition_evidence', {}))
            scenario_state['historical_pattern_memory'].setdefault('review_closure_state', run_outcome.get('review_closure_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('operator_review_closure_evidence', run_outcome.get('operator_review_closure_evidence', {}))
            scenario_state['historical_pattern_memory'].setdefault('review_resolution_state', run_outcome.get('review_resolution_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('operator_review_resolution_evidence', run_outcome.get('operator_review_resolution_evidence', {}))
            scenario_state['historical_pattern_memory'].setdefault('review_finalization_state', run_outcome.get('review_finalization_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('operator_review_finalization_evidence', run_outcome.get('operator_review_finalization_evidence', {}))
            scenario_state['historical_pattern_memory'].setdefault('review_settlement_state', run_outcome.get('review_settlement_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('operator_review_settlement_evidence', run_outcome.get('operator_review_settlement_evidence', {}))
            scenario_state['historical_pattern_memory'].setdefault('review_archival_state', run_outcome.get('review_archival_state', {}))
            scenario_state['historical_pattern_memory'].setdefault('operator_review_archival_evidence', run_outcome.get('operator_review_archival_evidence', {}))
            scenario_state['historical_pattern_memory'].setdefault('operator_analog_evidence', run_outcome.get('operator_analog_evidence', {}))
            scenario_state['historical_pattern_memory'].setdefault('operator_review_stance_evidence', run_outcome.get('operator_review_stance_evidence', {}))
            scenario_state['historical_pattern_memory'].setdefault('operator_audit_basis_evidence', run_outcome.get('operator_audit_basis_evidence', {}))
            scenario_state['historical_pattern_memory'].setdefault('operator_review_synthesis_evidence', run_outcome.get('operator_review_synthesis_evidence', {}))
            scenario_state['historical_pattern_memory'].setdefault('compact_historical_disposition_lines', run_outcome.get('compact_historical_disposition_lines', []))
            scenario_state['historical_pattern_memory'].setdefault('compact_historical_closure_lines', run_outcome.get('compact_historical_closure_lines', []))
            scenario_state['historical_pattern_memory'].setdefault('compact_historical_resolution_lines', run_outcome.get('compact_historical_resolution_lines', []))
            scenario_state['historical_pattern_memory'].setdefault('compact_historical_finalization_lines', run_outcome.get('compact_historical_finalization_lines', []))
            scenario_state['historical_pattern_memory'].setdefault('compact_historical_settlement_lines', run_outcome.get('compact_historical_settlement_lines', []))
            scenario_state['historical_pattern_memory'].setdefault('compact_historical_archival_lines', run_outcome.get('compact_historical_archival_lines', []))
        scenario_state['operator_session_view'] = session_view
        return world

    def _normalize_active_aftermath(self, entries: list[dict]) -> list[dict]:
        normalized = []
        for entry in entries[-30:]:
            if not isinstance(entry, dict):
                continue
            ticks_remaining = max(0, int(entry.get('ticks_remaining', 0)))
            if ticks_remaining <= 0:
                continue
            normalized.append({
                'intervention_id': entry.get('intervention_id'),
                'district_id': entry.get('district_id'),
                'amplitude': round(max(0.0, min(1.0, float(entry.get('amplitude', 0.0)))), 3),
                'ticks_remaining': ticks_remaining,
                'fade_per_tick': round(max(0.0, min(1.0, float(entry.get('fade_per_tick', 0.12)))), 3),
                'reversal_risk': round(max(0.0, min(1.0, float(entry.get('reversal_risk', 0.0)))), 3),
            })
        return normalized[-24:]

    def _ensure_run_outcome_defaults(self, run_outcome: dict) -> dict:
        run_outcome.setdefault('regime_interpretation', {})
        run_outcome.setdefault('lead_lag_signals', {})
        run_outcome.setdefault('recovery_spread_state', {})
        run_outcome.setdefault('intervention_regime_effect', {})
        run_outcome.setdefault('tipping_thresholds', {})
        run_outcome.setdefault('leverage_points', {})
        run_outcome.setdefault('intervention_lever_relevance', {'levers': {}})
        run_outcome.setdefault('momentum_management', {})
        run_outcome.setdefault('regime_comparison_views', {})
        run_outcome.setdefault('intervention_learning_signals', {})
        run_outcome.setdefault('lead_lag_response_tracking', {})
        run_outcome.setdefault('historical_pattern_memory', {})
        run_outcome.setdefault('regime_family_memory', {})
        run_outcome.setdefault('lever_family_tendencies', [])
        run_outcome.setdefault('archetype_response_patterns', {})
        run_outcome.setdefault('operator_playbook_evidence', {})
        run_outcome.setdefault('scenario_archetype_memory', {})
        run_outcome.setdefault('combined_pattern_groupings', {})
        run_outcome.setdefault('weak_vs_broad_review_signals', {})
        run_outcome.setdefault('family_level_intervention_review', {})
        run_outcome.setdefault('scenario_family_fit_state', {})
        run_outcome.setdefault('scenario_novelty_state', {})
        run_outcome.setdefault('hybrid_family_state', {})
        run_outcome.setdefault('evidence_confidence_state', {})
        run_outcome.setdefault('nearest_analog_state', {})
        run_outcome.setdefault('analog_confidence_state', {})
        run_outcome.setdefault('partial_analog_support_state', {})
        run_outcome.setdefault('precedent_quality_state', {})
        run_outcome.setdefault('precedent_agreement_state', {})
        run_outcome.setdefault('precedent_readiness_state', {})
        run_outcome.setdefault('review_readiness_state', {})
        run_outcome.setdefault('exception_review_state', {})
        run_outcome.setdefault('precedent_downgrade_state', {})
        run_outcome.setdefault('audit_basis_state', {})
        run_outcome.setdefault('evidence_lane_state', {})
        run_outcome.setdefault('underdetermined_review_state', {})
        run_outcome.setdefault('review_synthesis_state', {})
        run_outcome.setdefault('synthesis_contestation_state', {})
        run_outcome.setdefault('synthesis_downweight_state', {})
        run_outcome.setdefault('review_conclusion_state', {})
        run_outcome.setdefault('review_takeaway_caveat_state', {})
        run_outcome.setdefault('cautious_conclusion_state', {})
        run_outcome.setdefault('operator_conclusion_evidence', {})
        run_outcome.setdefault('review_verdict_state', {})
        run_outcome.setdefault('verdict_stability_state', {})
        run_outcome.setdefault('verdict_caveat_override_state', {})
        run_outcome.setdefault('operator_verdict_evidence', {})
        run_outcome.setdefault('review_disposition_state', {})
        run_outcome.setdefault('disposition_distinction_state', {})
        run_outcome.setdefault('unresolved_disposition_state', {})
        run_outcome.setdefault('operator_disposition_evidence', {})
        run_outcome.setdefault('review_closure_state', {})
        run_outcome.setdefault('operator_review_closure_evidence', {})
        run_outcome.setdefault('review_resolution_state', {})
        run_outcome.setdefault('operator_review_resolution_evidence', {})
        run_outcome.setdefault('review_finalization_state', {})
        run_outcome.setdefault('operator_review_finalization_evidence', {})
        run_outcome.setdefault('review_settlement_state', {})
        run_outcome.setdefault('operator_review_settlement_evidence', {})
        run_outcome.setdefault('review_archival_state', {})
        run_outcome.setdefault('operator_review_archival_evidence', {})
        run_outcome.setdefault('operator_scenario_archetype_evidence', {})
        run_outcome.setdefault('operator_analog_evidence', {})
        run_outcome.setdefault('operator_precedent_evidence', {})
        run_outcome.setdefault('operator_review_stance_evidence', {})
        run_outcome.setdefault('operator_audit_basis_evidence', {})
        run_outcome.setdefault('operator_review_synthesis_evidence', {})
        run_outcome.setdefault('operator_novelty_outlier_evidence', {})
        run_outcome.setdefault('divergence_review_state', {})
        run_outcome.setdefault('operator_intervention_review_evidence', {})
        run_outcome.setdefault('counterfactual_operator_evidence', {})
        run_outcome.setdefault('compact_historical_synthesis_lines', [])
        run_outcome.setdefault('compact_historical_conclusion_lines', [])
        run_outcome.setdefault('compact_historical_verdict_lines', [])
        run_outcome.setdefault('compact_historical_disposition_lines', [])
        run_outcome.setdefault('compact_historical_closure_lines', [])
        run_outcome.setdefault('compact_historical_resolution_lines', [])
        run_outcome.setdefault('compact_historical_finalization_lines', [])
        run_outcome.setdefault('compact_historical_settlement_lines', [])
        run_outcome.setdefault('compact_historical_archival_lines', [])
        divergence_review = run_outcome.setdefault('divergence_review_state', {})
        divergence_review.setdefault('similar_archetype_comparison_signals', {})
        divergence_review.setdefault('leverage_vs_regime_separation', {})
        divergence_review.setdefault('threshold_momentum_sensitivity', {})
        return run_outcome

    def _ensure_scenario_insight_defaults(self, scenario_insight_report: dict) -> dict:
        scenario_insight_report.setdefault('steering_watch_items', [])
        scenario_insight_report.setdefault('tipping_thresholds', {})
        scenario_insight_report.setdefault('leverage_points', {})
        scenario_insight_report.setdefault('intervention_lever_relevance', {'levers': {}})
        scenario_insight_report.setdefault('momentum_management', {})
        scenario_insight_report.setdefault('regime_comparison_views', {})
        scenario_insight_report.setdefault('intervention_learning_signals', {})
        scenario_insight_report.setdefault('lead_lag_response_tracking', {})
        scenario_insight_report.setdefault('historical_pattern_memory', {})
        scenario_insight_report.setdefault('historical_pattern_evidence', [])
        scenario_insight_report.setdefault('regime_family_memory', {})
        scenario_insight_report.setdefault('lever_family_tendencies', [])
        scenario_insight_report.setdefault('archetype_response_patterns', {})
        scenario_insight_report.setdefault('operator_playbook_evidence', {})
        scenario_insight_report.setdefault('scenario_archetype_memory', {})
        scenario_insight_report.setdefault('combined_pattern_groupings', {})
        scenario_insight_report.setdefault('weak_vs_broad_review_signals', {})
        scenario_insight_report.setdefault('family_level_intervention_review', {})
        scenario_insight_report.setdefault('scenario_family_fit_state', {})
        scenario_insight_report.setdefault('scenario_novelty_state', {})
        scenario_insight_report.setdefault('hybrid_family_state', {})
        scenario_insight_report.setdefault('evidence_confidence_state', {})
        scenario_insight_report.setdefault('nearest_analog_state', {})
        scenario_insight_report.setdefault('analog_confidence_state', {})
        scenario_insight_report.setdefault('partial_analog_support_state', {})
        scenario_insight_report.setdefault('precedent_quality_state', {})
        scenario_insight_report.setdefault('precedent_agreement_state', {})
        scenario_insight_report.setdefault('precedent_readiness_state', {})
        scenario_insight_report.setdefault('review_readiness_state', {})
        scenario_insight_report.setdefault('exception_review_state', {})
        scenario_insight_report.setdefault('precedent_downgrade_state', {})
        scenario_insight_report.setdefault('audit_basis_state', {})
        scenario_insight_report.setdefault('evidence_lane_state', {})
        scenario_insight_report.setdefault('underdetermined_review_state', {})
        scenario_insight_report.setdefault('review_synthesis_state', {})
        scenario_insight_report.setdefault('synthesis_contestation_state', {})
        scenario_insight_report.setdefault('synthesis_downweight_state', {})
        scenario_insight_report.setdefault('review_conclusion_state', {})
        scenario_insight_report.setdefault('review_takeaway_caveat_state', {})
        scenario_insight_report.setdefault('cautious_conclusion_state', {})
        scenario_insight_report.setdefault('operator_conclusion_evidence', {})
        scenario_insight_report.setdefault('review_verdict_state', {})
        scenario_insight_report.setdefault('verdict_stability_state', {})
        scenario_insight_report.setdefault('verdict_caveat_override_state', {})
        scenario_insight_report.setdefault('operator_verdict_evidence', {})
        scenario_insight_report.setdefault('review_disposition_state', {})
        scenario_insight_report.setdefault('disposition_distinction_state', {})
        scenario_insight_report.setdefault('unresolved_disposition_state', {})
        scenario_insight_report.setdefault('operator_disposition_evidence', {})
        scenario_insight_report.setdefault('review_closure_state', {})
        scenario_insight_report.setdefault('operator_review_closure_evidence', {})
        scenario_insight_report.setdefault('review_resolution_state', {})
        scenario_insight_report.setdefault('operator_review_resolution_evidence', {})
        scenario_insight_report.setdefault('review_finalization_state', {})
        scenario_insight_report.setdefault('operator_review_finalization_evidence', {})
        scenario_insight_report.setdefault('review_settlement_state', {})
        scenario_insight_report.setdefault('operator_review_settlement_evidence', {})
        scenario_insight_report.setdefault('review_archival_state', {})
        scenario_insight_report.setdefault('operator_review_archival_evidence', {})
        scenario_insight_report.setdefault('operator_family_fit_confidence', [])
        scenario_insight_report.setdefault('operator_scenario_archetype_evidence', {})
        scenario_insight_report.setdefault('operator_analog_evidence', {})
        scenario_insight_report.setdefault('operator_precedent_evidence', {})
        scenario_insight_report.setdefault('operator_review_stance_evidence', {})
        scenario_insight_report.setdefault('operator_audit_basis_evidence', {})
        scenario_insight_report.setdefault('operator_review_synthesis_evidence', {})
        scenario_insight_report.setdefault('operator_novelty_outlier_evidence', {})
        scenario_insight_report.setdefault('operator_intervention_review_evidence', {})
        scenario_insight_report.setdefault('divergence_review_state', {})
        scenario_insight_report.setdefault('operator_divergence_evidence', {})
        scenario_insight_report.setdefault('historical_divergence_evidence_lines', [])
        scenario_insight_report.setdefault('similar_archetype_comparison_signals', {})
        scenario_insight_report.setdefault('leverage_vs_regime_separation', {})
        scenario_insight_report.setdefault('threshold_momentum_sensitivity', {})
        scenario_insight_report.setdefault('counterfactual_operator_evidence', {})
        scenario_insight_report.setdefault('compact_historical_evidence_lines', [])
        scenario_insight_report.setdefault('compact_historical_audit_lines', [])
        scenario_insight_report.setdefault('compact_historical_synthesis_lines', [])
        scenario_insight_report.setdefault('compact_historical_conclusion_lines', [])
        scenario_insight_report.setdefault('compact_historical_verdict_lines', [])
        scenario_insight_report.setdefault('compact_historical_disposition_lines', [])
        scenario_insight_report.setdefault('compact_historical_closure_lines', [])
        scenario_insight_report.setdefault('compact_historical_resolution_lines', [])
        scenario_insight_report.setdefault('compact_historical_finalization_lines', [])
        scenario_insight_report.setdefault('compact_historical_settlement_lines', [])
        scenario_insight_report.setdefault('compact_historical_archival_lines', [])
        return scenario_insight_report

    def _world_comparison_summary(self, world: dict) -> dict:
        metrics = world.get('city', {}).get('world_metrics', {})
        return {
            'employment_rate': metrics.get('employment_rate', 0.0),
            'avg_housing_burden': metrics.get('avg_housing_burden', 0.0),
            'household_pressure_index': metrics.get('household_pressure_index', 0.0),
            'service_access_score': metrics.get('service_access_score', 0.0),
            'social_support_score': metrics.get('social_support_score', 0.0),
            'stressed_districts': (metrics.get('district_state_overview') or {}).get('stressed', 0),
            'city_regime_phase': ((metrics.get('regime_state') or {}).get('phase', 'mixed_transition')),
            'regime_shift_candidate': bool((metrics.get('regime_state') or {}).get('regime_shift_candidate', False)),
        }
