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
                'insight_filter_catalog': {'source_types': [], 'directions': [], 'scenario_names': [], 'count': 0},
                'last_saved_insight_id': None,
            },
            'propagation_state': {
                'schema_version': 'm09-ripple-scaffold-v1',
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
        world = AuraliteRuntimeService.tick(world, 0)
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
        updated = AuraliteRuntimeService.tick(world, minutes)
        updated['world']['last_tick_at'] = datetime.utcnow().isoformat()
        self.save_world_payload(updated)
        return updated

    def apply_interventions(self, changes: list[dict], notes: str = '') -> dict:
        world = self.get_or_create_world()
        world, record = AuraliteInterventionService.apply_changes(world, changes, notes=notes)
        world = AuraliteRuntimeService.tick(world, 0)
        AuraliteInterventionService.enrich_record_with_after(record, world)
        world['intervention_state']['history'][-1] = record
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
        self.save_world_payload(world)
        return {'snapshot_id': snapshot_id, 'summary': summary}

    def load_named_snapshot(self, snapshot_id: str) -> dict | None:
        snapshot = AuralitePersistenceService.load_snapshot(self.WORLD_ID, snapshot_id)
        if not snapshot:
            return None
        snapshot = self._ensure_milestone_03_shape(snapshot)
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
        self.save_world_payload(world)
        return report

    def _auto_advance(self, world: dict) -> dict:
        if not world['world']['is_running']:
            world = AuraliteRuntimeService.tick(world, 0)
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
        updated = AuraliteRuntimeService.tick(world, sim_minutes)
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

        for household in world.get('households', []):
            household.setdefault('monthly_income', 0.0)
            household.setdefault('monthly_rent', 0.0)
            burden = household.setdefault('housing_cost_burden', 0.0)
            household.setdefault('pressure_index', round(min(1.0, burden + 0.1), 3))
            household.setdefault('pressure_level', 'medium' if burden >= 0.3 else 'low')
            household.setdefault('landlord_id', None)
            household.setdefault('eviction_risk', round(min(1.0, household.get('pressure_index', 0.0) * 0.85), 3))
            household.setdefault('context', {})
            household.setdefault('social_context', {})
            household.setdefault('trajectory', {'signals': {}, 'horizon': 'short_to_medium_term'})
            household.setdefault('derived_summary', {})

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
            person.setdefault('trajectory', {'signals': {}, 'horizon': 'short_to_medium_term'})
            person.setdefault('derived_summary', {})

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

        world.setdefault('city', {}).setdefault('world_metrics', {})
        world.setdefault('reporting_state', {})
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
            'insight_filter_catalog': {'source_types': [], 'directions': [], 'scenario_names': [], 'count': 0},
            'last_saved_insight_id': None,
        })
        world.setdefault('propagation_state', {
            'schema_version': 'm09-ripple-scaffold-v1',
            'last_updated_at': None,
            'district_neighbor_events': [],
            'social_events': [],
            'district_recent_impacts': {},
            'resident_recent_impacts': {},
            'household_recent_impacts': {},
            'notes': ['Lightweight propagation scaffold; bounded effects only.'],
        })
        world['scenario_state'].setdefault('active_scenario_name', 'default-baseline')
        world['scenario_state'].setdefault('snapshots', [])
        world['scenario_state'].setdefault('last_comparison', {})
        world['scenario_state'].setdefault('baseline_snapshot_id', None)
        world['scenario_state'].setdefault('last_comparison_report', {})
        world['scenario_state'].setdefault('scenario_start_anchor', {})
        world['scenario_state'].setdefault('timeline', [])
        world['scenario_state'].setdefault('last_timeline_moment_id', None)
        world['scenario_state'].setdefault('run_summary', {})
        world['scenario_state'].setdefault('saved_insights', [])
        world['scenario_state'].setdefault(
            'insight_filter_catalog',
            {'source_types': [], 'directions': [], 'scenario_names': [], 'count': 0},
        )
        world['scenario_state'].setdefault('last_saved_insight_id', None)
        if world['scenario_state'].get('saved_insights'):
            world['scenario_state']['insight_filter_catalog'] = AuraliteReportingService._build_insight_filter_catalog(
                world['scenario_state']['saved_insights'],
            )
        return AuraliteRuntimeService.tick(world, 0)

    def _world_comparison_summary(self, world: dict) -> dict:
        metrics = world.get('city', {}).get('world_metrics', {})
        return {
            'employment_rate': metrics.get('employment_rate', 0.0),
            'avg_housing_burden': metrics.get('avg_housing_burden', 0.0),
            'household_pressure_index': metrics.get('household_pressure_index', 0.0),
            'service_access_score': metrics.get('service_access_score', 0.0),
            'social_support_score': metrics.get('social_support_score', 0.0),
            'stressed_districts': (metrics.get('district_state_overview') or {}).get('stressed', 0),
        }
