from datetime import datetime, timedelta

from .auralite_explainability_service import AuraliteExplainabilityService


class AuraliteRuntimeService:
    DISTRICT_NEIGHBORS = {
        'the_crown': ['glass_harbor', 'old_meridian', 'highgarden'],
        'glass_harbor': ['the_crown', 'neon_market', 'riverwake'],
        'old_meridian': ['the_crown', 'riverwake', 'ember_district', 'southline'],
        'southline': ['old_meridian', 'ember_district', 'ironwood_fringe', 'neon_market'],
        'north_vale': ['riverwake', 'old_meridian', 'ironwood_fringe'],
        'highgarden': ['the_crown', 'glass_harbor'],
        'ember_district': ['old_meridian', 'southline', 'ironwood_fringe', 'riverwake'],
        'ironwood_fringe': ['ember_district', 'southline', 'north_vale'],
        'riverwake': ['north_vale', 'old_meridian', 'glass_harbor', 'ember_district'],
        'neon_market': ['glass_harbor', 'southline', 'old_meridian'],
    }

    @staticmethod
    def tick(world_state: dict, elapsed_minutes: int):
        previous_district_snapshot = {
            district['district_id']: {
                'pressure_index': float(district.get('pressure_index', 0.0)),
                'service_access_score': float(district.get('service_access_score', 0.0)),
                'social_support_score': float(district.get('social_support_score', 0.0)),
            }
            for district in world_state.get('districts', [])
        }
        previous_person_snapshot = {
            person['person_id']: float((person.get('state_summary') or {}).get('stress', 0.0))
            for person in world_state.get('persons', [])
        }
        previous_household_snapshot = {
            household['household_id']: float((household.get('context') or {}).get('stress_index', household.get('pressure_index', 0.0)))
            for household in world_state.get('households', [])
        }

        current_time = datetime.fromisoformat(world_state['world']['current_time'])
        current_time += timedelta(minutes=elapsed_minutes)
        world_state['world']['current_time'] = current_time.isoformat()
        world_state['world']['updated_at'] = datetime.utcnow().isoformat()

        hour = current_time.hour
        district_activity = {d['district_id']: 0 for d in world_state['districts']}
        district_working = {d['district_id']: 0 for d in world_state['districts']}
        district_pressure = {d['district_id']: [] for d in world_state['districts']}
        district_service_access = {d['district_id']: [] for d in world_state['districts']}
        district_transit = {d['district_id']: [] for d in world_state['districts']}
        district_social_support = {d['district_id']: [] for d in world_state['districts']}
        household_service_access = {}
        household_employment = {}
        household_social_support = {}

        households_by_id = {h['household_id']: h for h in world_state.get('households', [])}
        institutions_by_id = {i['institution_id']: i for i in world_state.get('institutions', [])}
        institution_load_context = AuraliteRuntimeService._build_institution_load_context(
            persons=world_state.get('persons', []),
            households=world_state.get('households', []),
            institutions=world_state.get('institutions', []),
        )

        for person in world_state.get('persons', []):
            household = households_by_id.get(person['household_id'], {})
            employer = institutions_by_id.get(person.get('employer_id') or '', {})
            transit_service = institutions_by_id.get(person.get('transit_service_id') or '', {})
            service_provider = institutions_by_id.get(person.get('service_provider_id') or '', {})
            landlord = institutions_by_id.get(household.get('landlord_id') or '', {})
            employer_load = institution_load_context.get(person.get('employer_id') or '', {})
            transit_load = institution_load_context.get(person.get('transit_service_id') or '', {})
            service_load = institution_load_context.get(person.get('service_provider_id') or '', {})
            landlord_load = institution_load_context.get(household.get('landlord_id') or '', {})

            employer_pressure = AuraliteRuntimeService._institution_pressure(employer, default=0.35)
            landlord_pressure = AuraliteRuntimeService._institution_pressure(landlord, default=0.4)
            transit_pressure = AuraliteRuntimeService._institution_pressure(transit_service, default=0.3)
            service_pressure = AuraliteRuntimeService._institution_pressure(service_provider, default=0.32)
            transit_reliability = AuraliteRuntimeService._institution_access(transit_service, fallback=0.58)
            service_access_anchor = AuraliteRuntimeService._institution_access(service_provider, fallback=0.52)
            transit_overload = float(transit_load.get('utilization_pressure', 0.0))
            service_overload = float(service_load.get('utilization_pressure', 0.0))
            landlord_overload = float(landlord_load.get('utilization_pressure', 0.0))
            employer_overload = float(employer_load.get('utilization_pressure', 0.0))

            person['housing_burden_share'] = round(
                max(person.get('housing_burden_share', 0.0), household.get('housing_cost_burden', 0.0)),
                3,
            )
            person['service_access_score'] = round(
                max(
                    0.05,
                    min(
                        1.0,
                        (person.get('service_access_score', 0.5) * 0.45)
                        + (service_access_anchor * 0.55)
                        - (service_pressure * 0.12),
                        - (service_overload * 0.08),
                    ),
                ),
                3,
            )
            person['state_summary'] = person.get('state_summary', {})
            person['state_summary']['employer_pressure'] = round(employer_pressure, 3)
            person['state_summary']['landlord_pressure'] = round(landlord_pressure, 3)
            person['state_summary']['transit_pressure'] = round(transit_pressure, 3)
            person['state_summary']['service_pressure'] = round(service_pressure, 3)
            person['state_summary']['commute_reliability'] = round(transit_reliability, 3)
            person['state_summary']['institution_load'] = {
                'employer': round(employer_overload, 3),
                'landlord': round(landlord_overload, 3),
                'transit': round(transit_overload, 3),
                'service': round(service_overload, 3),
            }
            person['social_context'] = person.get('social_context', {})
            existing_support = float(person['social_context'].get('support_index', 0.45))
            existing_strain = float(person['social_context'].get('strain_index', 0.45))
            tie_weight = (
                min(0.25, float(person['social_context'].get('household_ties', 0)) * 0.03)
                + min(0.15, float(person['social_context'].get('coworker_ties', 0)) * 0.04)
                + min(0.1, float(person['social_context'].get('district_local_ties', 0)) * 0.03)
            )
            support_index = max(
                0.05,
                min(
                    1.0,
                    (existing_support * 0.58)
                    + (person['service_access_score'] * 0.26)
                    + (transit_reliability * 0.08)
                    + tie_weight,
                ),
            )
            strain_index = max(
                0.0,
                min(
                    1.0,
                    (existing_strain * 0.56)
                    + (person['housing_burden_share'] * 0.23)
                    + (employer_pressure * 0.11)
                    + (landlord_pressure * 0.08)
                    + (service_overload * 0.05)
                    + (0.12 if person.get('employment_status') != 'employed' else 0.0)
                    - (support_index * 0.2),
                ),
            )
            person['social_context']['support_index'] = round(support_index, 3)
            person['social_context']['strain_index'] = round(strain_index, 3)
            person['state_summary']['social_support_index'] = round(support_index, 3)
            person['state_summary']['social_strain_index'] = round(strain_index, 3)

            person['state_summary']['stress'] = round(
                min(
                    1.0,
                    person['housing_burden_share'] * 0.95
                    + landlord_pressure * 0.3
                    + landlord_overload * 0.08
                    + employer_pressure * 0.26
                    + employer_overload * 0.07
                    + transit_pressure * 0.18
                    + transit_overload * 0.06
                    + service_pressure * 0.18
                    + service_overload * 0.08
                    + (1 - person['service_access_score']) * 0.35
                    + strain_index * 0.22
                    - support_index * 0.16
                    + (0.16 if person.get('employment_status') != 'employed' else 0.0),
                ),
                3,
            )

            target, activity = AuraliteRuntimeService._resolve_person_activity(hour, person)
            person['current_location_id'] = target
            person['current_activity'] = activity

            district_id = person['district_id']
            district_activity[district_id] += 1
            if activity in {'work', 'night_shift', 'commute', 'swing_shift'}:
                district_working[district_id] += 1
            district_pressure[district_id].append(person.get('housing_burden_share', 0.0))
            district_service_access[district_id].append(person.get('service_access_score', 0.5))
            district_transit[district_id].append(person.get('state_summary', {}).get('commute_reliability', 0.6))
            district_social_support[district_id].append(person.get('social_context', {}).get('support_index', 0.5))
            household_service_access.setdefault(person['household_id'], []).append(person.get('service_access_score', 0.5))
            household_employment.setdefault(person['household_id'], []).append(
                1.0 if person.get('employment_status') == 'employed' else 0.0
            )
            household_social_support.setdefault(person['household_id'], []).append(
                person.get('social_context', {}).get('support_index', 0.5),
            )

        AuraliteRuntimeService._update_households(
            world_state=world_state,
            household_service_access=household_service_access,
            household_employment=household_employment,
            household_social_support=household_social_support,
        )
        AuraliteRuntimeService._update_personal_explainability(world_state=world_state)

        AuraliteRuntimeService._update_districts(
            world_state,
            hour,
            district_activity,
            district_working,
            district_pressure,
            district_service_access,
            district_transit,
            district_social_support,
            institution_load_context,
        )
        AuraliteRuntimeService._build_propagation_state(
            world_state=world_state,
            previous_district_snapshot=previous_district_snapshot,
            previous_person_snapshot=previous_person_snapshot,
            previous_household_snapshot=previous_household_snapshot,
        )
        AuraliteRuntimeService._update_city_metrics(world_state, hour)
        AuraliteExplainabilityService.augment_world_state(world_state)
        return world_state

    @staticmethod
    def _update_households(
        world_state: dict,
        household_service_access: dict,
        household_employment: dict,
        household_social_support: dict,
    ):
        for household in world_state.get('households', []):
            hh_id = household['household_id']
            member_count = max(1, len(household.get('member_ids', [])))
            employment_values = household_employment.get(hh_id, [])
            service_values = household_service_access.get(hh_id, [])
            social_values = household_social_support.get(hh_id, [])
            employment_rate = sum(employment_values) / max(1, len(employment_values))
            service_access = sum(service_values) / max(1, len(service_values))
            social_support = sum(social_values) / max(1, len(social_values))
            rent_share = household.get('housing_cost_burden', 0.0)
            pressure = household.get('pressure_index', 0.0)

            housing_instability = min(1.0, (rent_share * 0.72) + (pressure * 0.38) + (household.get('eviction_risk', 0.0) * 0.35))
            employment_instability = max(0.0, min(1.0, 1.0 - employment_rate))
            stress = min(
                1.0,
                pressure * 0.5
                + housing_instability * 0.26
                + employment_instability * 0.18
                + (1.0 - service_access) * 0.16,
            )
            household.setdefault('context', {})
            household['social_context'] = household.get('social_context', {})
            household['social_context'].update({
                'support_exposure': round(
                    max(
                        0.05,
                        min(1.0, (float(household['social_context'].get('support_exposure', social_support)) * 0.6) + (social_support * 0.4)),
                    ),
                    3,
                ),
                'local_strain_index': round(
                    min(
                        1.0,
                        (float(household['social_context'].get('local_strain_index', pressure)) * 0.55)
                        + (stress * 0.28)
                        + ((1.0 - social_support) * 0.17),
                    ),
                    3,
                ),
            })
            household['context'].update({
                'member_count': member_count,
                'employment_rate': round(employment_rate, 3),
                'service_access_score': round(service_access, 3),
                'social_support_score': round(social_support, 3),
                'stress_index': round(stress, 3),
                'housing_stability_index': round(max(0.0, 1.0 - housing_instability), 3),
                'employment_stability_index': round(max(0.0, 1.0 - employment_instability), 3),
            })

    @staticmethod
    def _update_personal_explainability(world_state: dict):
        reporting_state = world_state.setdefault('reporting_state', {})
        previous_person = reporting_state.get('previous_person_metrics', {})
        previous_household = reporting_state.get('previous_household_metrics', {})

        households_by_id = {h['household_id']: h for h in world_state.get('households', [])}

        for person in world_state.get('persons', []):
            person_id = person['person_id']
            household = households_by_id.get(person.get('household_id'), {})
            current = {
                'stress': float((person.get('state_summary') or {}).get('stress', 0.0)),
                'housing_stability': float(max(0.0, 1.0 - person.get('housing_burden_share', 0.0))),
                'employment_stability': 1.0 if person.get('employment_status') == 'employed' else 0.0,
                'service_access': float(person.get('service_access_score', 0.5)),
                'social_support': float((person.get('social_context') or {}).get('support_index', 0.5)),
            }
            previous = previous_person.get(person_id, {})
            person['trajectory'] = AuraliteRuntimeService._trajectory_payload(current, previous, inverse={'stress'})
            person['derived_summary'] = {
                'causal_readout': AuraliteRuntimeService._personal_causal_readout(
                    current=current,
                    previous=previous,
                    system_pressures={
                        **(person.get('state_summary') or {}),
                        'social_support': (person.get('social_context') or {}).get('support_index', 0.5),
                        'social_strain': (person.get('social_context') or {}).get('strain_index', 0.5),
                    },
                    domain='resident',
                ),
            }
            person['derived_summary']['causal_readout']['linked_household'] = household.get('household_id')
            person['derived_summary']['causal_readout']['social_context'] = person.get('social_context', {})

        for household in world_state.get('households', []):
            hh_id = household['household_id']
            context = household.get('context') or {}
            current = {
                'stress': float(context.get('stress_index', household.get('pressure_index', 0.0))),
                'housing_stability': float(context.get('housing_stability_index', max(0.0, 1.0 - household.get('housing_cost_burden', 0.0)))),
                'employment_stability': float(context.get('employment_stability_index', 0.0)),
                'service_access': float(context.get('service_access_score', 0.5)),
                'social_support': float((household.get('social_context') or {}).get('support_exposure', context.get('social_support_score', 0.5))),
            }
            previous = previous_household.get(hh_id, {})
            household['trajectory'] = AuraliteRuntimeService._trajectory_payload(current, previous, inverse={'stress'})
            household['derived_summary'] = {
                'causal_readout': AuraliteRuntimeService._personal_causal_readout(
                    current=current,
                    previous=previous,
                    system_pressures={
                        'landlord_pressure': household.get('eviction_risk', 0.0),
                        'income_pressure': household.get('pressure_index', 0.0),
                        'service_pressure': max(0.0, 1.0 - current['service_access']),
                        'social_strain': (household.get('social_context') or {}).get('local_strain_index', 0.0),
                        'social_support': current['social_support'],
                    },
                    domain='household',
                ),
            }

    @staticmethod
    def _trajectory_payload(current: dict, previous: dict, inverse: set[str] | None = None) -> dict:
        inverse = inverse or set()
        signals = {}
        for key in ['stress', 'housing_stability', 'employment_stability', 'service_access', 'social_support']:
            delta = round(float(current.get(key, 0.0)) - float(previous.get(key, current.get(key, 0.0))), 3)
            direction = AuraliteRuntimeService._direction_label(delta, better_when_lower=key in inverse)
            signals[f'{key}_trend'] = {
                'current': round(float(current.get(key, 0.0)), 3),
                'delta': delta,
                'direction': direction,
            }
        return {'signals': signals, 'horizon': 'short_to_medium_term'}

    @staticmethod
    def _personal_causal_readout(current: dict, previous: dict, system_pressures: dict, domain: str) -> dict:
        what_changed = {
            'stress': round(float(current.get('stress', 0.0)) - float(previous.get('stress', current.get('stress', 0.0))), 3),
            'housing_stability': round(float(current.get('housing_stability', 0.0)) - float(previous.get('housing_stability', current.get('housing_stability', 0.0))), 3),
            'employment_stability': round(float(current.get('employment_stability', 0.0)) - float(previous.get('employment_stability', current.get('employment_stability', 0.0))), 3),
            'service_access': round(float(current.get('service_access', 0.0)) - float(previous.get('service_access', current.get('service_access', 0.0))), 3),
            'social_support': round(float(current.get('social_support', 0.0)) - float(previous.get('social_support', current.get('social_support', 0.0))), 3),
        }

        ranked = sorted(
            [
                ('housing', float(system_pressures.get('landlord_pressure', 0.0) + system_pressures.get('income_pressure', 0.0) * 0.7)),
                ('employment', float(system_pressures.get('employer_pressure', system_pressures.get('income_pressure', 0.0)))),
                ('transit', float(system_pressures.get('transit_pressure', 0.0))),
                ('service_access', float(system_pressures.get('service_pressure', 0.0))),
                ('social_strain', float(system_pressures.get('social_strain', system_pressures.get('social_strain_index', 0.0)))),
                ('social_support', max(0.0, 1.0 - float(system_pressures.get('social_support', 0.5)))),
            ],
            key=lambda item: item[1],
            reverse=True,
        )[:3]
        why_changed = [f"{system.replace('_', ' ').title()} pressure remains a leading driver." for system, score in ranked if score >= 0.28]
        if not why_changed:
            why_changed = [f"No dominant {domain}-level driver; trends remain distributed."]
        return {
            'what_changed': what_changed,
            'why_changed': why_changed[:2],
            'top_system_contributors': [{'system': k, 'score': round(v, 3)} for k, v in ranked],
        }

    @staticmethod
    def _direction_label(delta: float, better_when_lower: bool = False) -> str:
        if abs(delta) < 0.01:
            return 'flat'
        improving = delta < 0 if better_when_lower else delta > 0
        if improving:
            return 'improving'
        return 'worsening'

    @staticmethod
    def _resolve_person_activity(hour: int, person: dict) -> tuple[str, str]:
        home = person['home_location_id']
        work = person.get('work_location_id') or home
        shift_window = person.get('shift_window', 'day')

        if person.get('employment_status') != 'employed':
            if 10 <= hour < 16:
                return work, 'local_errands'
            return home, 'home'

        if shift_window == 'night':
            if hour >= 21 or hour < 5:
                return work, 'night_shift'
            if 18 <= hour < 21:
                return work, 'commute'
            return home, 'sleep_recovery' if 7 <= hour < 14 else 'home'

        if shift_window == 'swing':
            if 12 <= hour < 14:
                return work, 'commute'
            if 14 <= hour < 22:
                return work, 'swing_shift'
            return home, 'home'

        if 7 <= hour < 9:
            return work, 'commute'
        if 9 <= hour < 17:
            return work, 'work'
        if 17 <= hour < 20:
            return home, 'return_home'
        if 20 <= hour < 23 and person.get('routine_type') in {'mixed', 'local'}:
            return work, 'leisure'
        return home, 'home'

    @staticmethod
    def _update_districts(
        world_state: dict,
        hour: int,
        district_activity: dict,
        district_working: dict,
        district_pressure: dict,
        district_service_access: dict,
        district_transit: dict,
        district_social_support: dict,
        institution_load_context: dict,
    ):
        total_people = max(1, len(world_state.get('persons', [])))
        households = world_state.get('households', [])
        institutions = world_state.get('institutions', [])
        district_lookup = {district['district_id']: district for district in world_state.get('districts', [])}

        for district in world_state.get('districts', []):
            district_id = district['district_id']
            residents = [p for p in world_state.get('persons', []) if p['district_id'] == district_id]
            resident_count = max(1, len(residents))
            district_households = [h for h in households if h['district_id'] == district_id]
            district_institutions = [i for i in institutions if i['district_id'] == district_id]

            raw_activity = district_activity[district_id] / total_people
            peak_bonus = 0.12 if district.get('activity_profile', {}).get('peak_hour') == hour else 0.0
            district['current_activity_level'] = round(min(1.0, raw_activity * 5 + peak_bonus), 3)

            employment_rate = sum(1 for p in residents if p.get('employment_status') == 'employed') / resident_count
            employment_pressure = 1.0 - employment_rate
            avg_wage = sum(max(0.0, p.get('hourly_wage', 0.0)) for p in residents) / resident_count
            avg_burden = sum(district_pressure[district_id]) / resident_count
            service_access = sum(district_service_access[district_id]) / resident_count
            transit_reliability = sum(district_transit[district_id]) / resident_count
            social_support = sum(district_social_support[district_id]) / resident_count
            household_pressure = sum(h.get('pressure_index', 0.0) for h in district_households) / max(1, len(district_households))

            service_institutions = [i for i in district_institutions if i.get('institution_type') in {'healthcare', 'service_access'}]
            service_capacity = sum(i.get('capacity', 0) for i in service_institutions)
            institution_stress = (
                sum(i.get('pressure_index', 0.0) for i in district_institutions) / max(1, len(district_institutions))
            )
            avg_utilization_pressure = (
                sum(float(institution_load_context.get(i.get('institution_id'), {}).get('utilization_pressure', 0.0)) for i in district_institutions)
                / max(1, len(district_institutions))
            )
            employer_pressure = AuraliteRuntimeService._average_pressure(district_institutions, 'employer')
            landlord_pressure = AuraliteRuntimeService._average_pressure(district_institutions, 'landlord')
            transit_pressure = AuraliteRuntimeService._average_pressure(district_institutions, 'transit')
            service_pressure = AuraliteRuntimeService._average_pressure(
                district_institutions,
                include_types={'healthcare', 'service_access'},
            )
            district_stress = (
                sum(p.get('state_summary', {}).get('stress', 0.0) for p in residents) / resident_count
            )

            pressure_index = min(
                1.0,
                (avg_burden * 0.4)
                + (employment_pressure * 0.22)
                + (household_pressure * 0.2)
                + ((1 - service_access) * 0.1)
                + (institution_stress * 0.04)
                + (avg_utilization_pressure * 0.08)
                + (employer_pressure * 0.06)
                + (landlord_pressure * 0.1)
                + (transit_pressure * 0.05)
                + (service_pressure * 0.05)
                + (district_stress * 0.08)
                + ((1.0 - social_support) * 0.1),
            )

            district['employment_rate'] = round(employment_rate, 3)
            district['average_hourly_wage'] = round(avg_wage, 2)
            district['average_housing_burden'] = round(avg_burden, 3)
            district['pressure_index'] = round(pressure_index, 3)
            district['employment_pressure'] = round(employment_pressure, 3)
            district['household_pressure'] = round(household_pressure, 3)
            district['service_access_score'] = round(service_access, 3)
            district['transit_reliability'] = round(transit_reliability, 3)
            district['social_support_score'] = round(social_support, 3)
            district['state_phase'] = AuraliteRuntimeService._phase_for_pressure(pressure_index, district['current_activity_level'])
            district['institution_summary'] = {
                'employers': sum(1 for i in district_institutions if i.get('institution_type') == 'employer'),
                'landlords': sum(1 for i in district_institutions if i.get('institution_type') == 'landlord'),
                'transit_services': sum(1 for i in district_institutions if i.get('institution_type') == 'transit'),
                'care_services': len(service_institutions),
                'service_capacity': service_capacity,
                'institution_stress': round(institution_stress, 3),
                'utilization_pressure': round(avg_utilization_pressure, 3),
                'employer_pressure': round(employer_pressure, 3),
                'landlord_pressure': round(landlord_pressure, 3),
                'transit_pressure': round(transit_pressure, 3),
                'service_pressure': round(service_pressure, 3),
            }
            district['derived_summary'] = {
                'resident_count': len(residents),
                'active_workers': district_working[district_id],
                'avg_hourly_wage': district['average_hourly_wage'],
                'avg_housing_burden': district['average_housing_burden'],
                'employment_pressure': district['employment_pressure'],
                'household_pressure_index': district['household_pressure'],
                'service_access_score': district['service_access_score'],
                'transit_reliability': district['transit_reliability'],
                'social_support_score': district['social_support_score'],
                'resident_stress_index': round(district_stress, 3),
                'institution_pressures': {
                    'employer': round(employer_pressure, 3),
                    'landlord': round(landlord_pressure, 3),
                    'transit': round(transit_pressure, 3),
                    'service_access': round(service_pressure, 3),
                    'utilization_pressure': round(avg_utilization_pressure, 3),
                },
                'pressure_index': district['pressure_index'],
                'pressure_drivers': AuraliteRuntimeService._pressure_drivers(district),
                'state_phase': district['state_phase'],
                'evolution_hook': {
                    'next_update_window': 'weekly',
                    'risk': 'elevated' if pressure_index >= 0.62 else 'stable',
                },
            }
        AuraliteRuntimeService._apply_neighborhood_ripple(district_lookup)

    @staticmethod
    def _apply_neighborhood_ripple(district_lookup: dict):
        ripple_cache = {}
        for district_id, district in district_lookup.items():
            neighbors = [
                district_lookup[n_id]
                for n_id in AuraliteRuntimeService.DISTRICT_NEIGHBORS.get(district_id, [])
                if n_id in district_lookup
            ]
            if not neighbors:
                continue
            neighbor_pressure = sum(n.get('pressure_index', 0.0) for n in neighbors) / len(neighbors)
            local_pressure = float(district.get('pressure_index', 0.0))
            pressure_gap = neighbor_pressure - local_pressure
            social_vulnerability = 1.0 - float(district.get('social_support_score', 0.5))
            service_vulnerability = 1.0 - float(district.get('service_access_score', 0.5))
            vulnerability = min(1.0, (social_vulnerability * 0.55) + (service_vulnerability * 0.45))
            ripple_effect = max(-0.05, min(0.05, pressure_gap * 0.16 * (0.35 + vulnerability)))
            ripple_cache[district_id] = {
                'neighbor_pressure': round(neighbor_pressure, 3),
                'pressure_gap': round(pressure_gap, 3),
                'vulnerability': round(vulnerability, 3),
                'ripple_effect': round(ripple_effect, 3),
                'neighbor_ids': [neighbor['district_id'] for neighbor in neighbors],
            }

        for district_id, ripple in ripple_cache.items():
            district = district_lookup[district_id]
            adjusted_pressure = max(0.0, min(1.0, float(district.get('pressure_index', 0.0)) + ripple['ripple_effect']))
            district['pressure_index'] = round(adjusted_pressure, 3)
            district.setdefault('derived_summary', {})
            district['derived_summary']['ripple_context'] = {
                'neighbor_ids': ripple['neighbor_ids'],
                'neighbor_pressure': ripple['neighbor_pressure'],
                'pressure_gap': ripple['pressure_gap'],
                'vulnerability': ripple['vulnerability'],
                'ripple_effect': ripple['ripple_effect'],
                'note': (
                    'Nearby pressure and local support/service vulnerability produced a bounded district spillover adjustment.'
                ),
            }
            district['derived_summary']['pressure_drivers'] = AuraliteRuntimeService._pressure_drivers(district)

    @staticmethod
    def _pressure_drivers(district: dict) -> list[str]:
        drivers = []
        if district.get('household_pressure', 0) >= 0.58:
            drivers.append('Household budgets are heavily strained by rent-to-income burden.')
        if district.get('employment_pressure', 0) >= 0.22:
            drivers.append('Employment mismatch is reducing income stability.')
        if district.get('service_access_score', 1) <= 0.55:
            drivers.append('Healthcare/service access is lagging household needs.')
        if district.get('transit_reliability', 1) <= 0.58:
            drivers.append('Transit reliability is amplifying commute friction.')
        if district.get('social_support_score', 1) <= 0.45:
            drivers.append('Local support ties are thin, so stress travels quickly between households.')
        institution_summary = district.get('institution_summary', {})
        if institution_summary.get('landlord_pressure', 0) >= 0.62:
            drivers.append('Landlord-side pressure is accelerating household instability.')
        if institution_summary.get('employer_pressure', 0) >= 0.62:
            drivers.append('Employer-side pressure is undermining job quality and predictability.')
        ripple = ((district.get('derived_summary') or {}).get('ripple_context') or {}).get('ripple_effect', 0.0)
        if abs(ripple) >= 0.015:
            direction = 'upward' if ripple > 0 else 'downward'
            drivers.append(f'Neighborhood spillover is creating a {direction} pressure adjustment this tick.')
        if not drivers:
            drivers.append('Pressure remains distributed with no single dominant driver.')
        return drivers

    @staticmethod
    def _build_propagation_state(
        world_state: dict,
        previous_district_snapshot: dict,
        previous_person_snapshot: dict,
        previous_household_snapshot: dict,
    ):
        persons = world_state.get('persons', [])
        households = world_state.get('households', [])
        districts = world_state.get('districts', [])
        person_by_id = {person['person_id']: person for person in persons}
        household_by_id = {household['household_id']: household for household in households}

        district_events = []
        district_impacts: dict[str, list[dict]] = {}
        for district in districts:
            district_id = district['district_id']
            previous = previous_district_snapshot.get(district_id, {})
            pressure_delta = round(float(district.get('pressure_index', 0.0)) - float(previous.get('pressure_index', 0.0)), 3)
            service_delta = round(float(district.get('service_access_score', 0.0)) - float(previous.get('service_access_score', 0.0)), 3)
            social_delta = round(float(district.get('social_support_score', 0.0)) - float(previous.get('social_support_score', 0.0)), 3)
            ripple_context = (district.get('derived_summary') or {}).get('ripple_context', {})
            ripple_effect = float(ripple_context.get('ripple_effect', 0.0))
            if abs(pressure_delta) < 0.012 and abs(ripple_effect) < 0.012:
                continue

            base_strength = max(abs(pressure_delta), abs(ripple_effect))
            pressure_sign = 1 if pressure_delta >= 0 else -1
            for target_id in ripple_context.get('neighbor_ids', []):
                target = next((item for item in districts if item.get('district_id') == target_id), None)
                if not target:
                    continue
                target_modifier = (
                    (1.0 - float(target.get('social_support_score', 0.5))) * 0.52
                    + (1.0 - float(target.get('service_access_score', 0.5))) * 0.48
                )
                impact = round(min(0.06, base_strength * (0.24 + target_modifier * 0.26)) * pressure_sign, 3)
                district_events.append({
                    'event_type': 'district_neighbor_ripple',
                    'source_district_id': district_id,
                    'target_district_id': target_id,
                    'impact_pressure': impact,
                    'service_delta': service_delta,
                    'social_delta': social_delta,
                    'driver': 'pressure_and_support_spillover',
                })
                district_impacts.setdefault(target_id, []).append({
                    'from': district_id,
                    'impact_pressure': impact,
                })

        social_events = []
        household_incoming: dict[str, list[dict]] = {}
        resident_incoming: dict[str, list[dict]] = {}
        for person in persons:
            current_stress = float((person.get('state_summary') or {}).get('stress', 0.0))
            previous_stress = previous_person_snapshot.get(person['person_id'], current_stress)
            stress_delta = round(current_stress - previous_stress, 3)
            if abs(stress_delta) < 0.025:
                continue
            for tie in person.get('social_ties', []):
                tied_person_id = tie.get('person_id')
                tied_person = person_by_id.get(tied_person_id)
                if not tied_person:
                    continue
                tie_type = tie.get('tie_type', 'district_local')
                tie_weight = 0.5 if tie_type == 'household' else 0.34 if tie_type == 'coworker' else 0.24
                support_buffer = float((tied_person.get('social_context') or {}).get('support_index', 0.5))
                service_buffer = float(tied_person.get('service_access_score', 0.5))
                propagation = round(stress_delta * tie_weight * (1.12 - (support_buffer * 0.55 + service_buffer * 0.45)), 3)
                if abs(propagation) < 0.012:
                    continue
                social_events.append({
                    'event_type': 'social_stress_propagation',
                    'source_person_id': person['person_id'],
                    'target_person_id': tied_person_id,
                    'tie_type': tie_type,
                    'stress_shift': propagation,
                })
                resident_incoming.setdefault(tied_person_id, []).append({
                    'from_person_id': person['person_id'],
                    'tie_type': tie_type,
                    'stress_shift': propagation,
                })
                household_incoming.setdefault(tied_person['household_id'], []).append({
                    'from_person_id': person['person_id'],
                    'tie_type': tie_type,
                    'stress_shift': propagation,
                })

        world_state['propagation_state'] = {
            'schema_version': 'm09-ripple-scaffold-v1',
            'last_updated_at': world_state.get('world', {}).get('current_time'),
            'district_neighbor_events': district_events[-40:],
            'social_events': social_events[-60:],
            'district_recent_impacts': {k: v[-6:] for k, v in district_impacts.items()},
            'resident_recent_impacts': {k: v[-5:] for k, v in resident_incoming.items()},
            'household_recent_impacts': {k: v[-8:] for k, v in household_incoming.items()},
            'notes': [
                'Lightweight propagation scaffold; bounded effects only.',
                'Designed for explainability and future event-system expansion.',
            ],
        }

        for district in districts:
            district_id = district['district_id']
            impacts = district_impacts.get(district_id, [])
            incoming_pressure = round(sum(item['impact_pressure'] for item in impacts), 3)
            propagation_adjustment = round(max(-0.03, min(0.03, incoming_pressure * 0.35)), 3)
            if propagation_adjustment:
                adjusted_pressure = max(
                    0.0,
                    min(1.0, float(district.get('pressure_index', 0.0)) + propagation_adjustment),
                )
                district['pressure_index'] = round(adjusted_pressure, 3)
                district['state_phase'] = AuraliteRuntimeService._phase_for_pressure(
                    adjusted_pressure,
                    float(district.get('current_activity_level', 0.0)),
                )
                district.setdefault('derived_summary', {})
                district['derived_summary']['pressure_drivers'] = AuraliteRuntimeService._pressure_drivers(district)
            district.setdefault('derived_summary', {})
            district['derived_summary']['propagation_context'] = {
                'incoming_neighbor_pressure': incoming_pressure,
                'applied_neighbor_pressure_adjustment': propagation_adjustment,
                'incoming_sources': impacts[-4:],
                'recent_neighbor_event_count': len([event for event in district_events if event['target_district_id'] == district_id]),
            }

        for person in persons:
            impacts = resident_incoming.get(person['person_id'], [])
            incoming_stress = round(sum(item['stress_shift'] for item in impacts), 3)
            stress_adjustment = round(max(-0.045, min(0.045, incoming_stress * 0.22)), 3)
            if stress_adjustment:
                state_summary = person.setdefault('state_summary', {})
                adjusted_stress = max(0.0, min(1.0, float(state_summary.get('stress', 0.0)) + stress_adjustment))
                state_summary['stress'] = round(adjusted_stress, 3)
                social_context = person.setdefault('social_context', {})
                adjusted_strain = max(0.0, min(1.0, float(social_context.get('strain_index', 0.0)) + max(0.0, stress_adjustment * 0.4)))
                social_context['strain_index'] = round(adjusted_strain, 3)
                state_summary['social_strain_index'] = round(adjusted_strain, 3)
            person.setdefault('derived_summary', {})
            person['derived_summary']['propagation_context'] = {
                'incoming_social_stress': incoming_stress,
                'applied_social_stress_adjustment': stress_adjustment,
                'incoming_social_edges': impacts[-3:],
                'recent_social_event_count': len(impacts),
            }

        for household in households:
            hh_id = household['household_id']
            impacts = household_incoming.get(hh_id, [])
            current_stress = float((household.get('context') or {}).get('stress_index', household.get('pressure_index', 0.0)))
            previous_stress = previous_household_snapshot.get(hh_id, current_stress)
            incoming_stress = round(sum(item['stress_shift'] for item in impacts), 3)
            stress_adjustment = round(max(-0.04, min(0.04, incoming_stress * 0.2)), 3)
            if stress_adjustment:
                context = household.setdefault('context', {})
                adjusted_stress = max(0.0, min(1.0, float(context.get('stress_index', current_stress)) + stress_adjustment))
                context['stress_index'] = round(adjusted_stress, 3)
                adjusted_pressure = max(0.0, min(1.0, float(household.get('pressure_index', 0.0)) + max(0.0, stress_adjustment * 0.45)))
                household['pressure_index'] = round(adjusted_pressure, 3)
                social_context = household.setdefault('social_context', {})
                local_strain = max(0.0, min(1.0, float(social_context.get('local_strain_index', adjusted_pressure)) + max(0.0, stress_adjustment * 0.35)))
                social_context['local_strain_index'] = round(local_strain, 3)
            household.setdefault('derived_summary', {})
            household['derived_summary']['propagation_context'] = {
                'incoming_social_stress': incoming_stress,
                'applied_social_stress_adjustment': stress_adjustment,
                'stress_delta': round(current_stress - previous_stress, 3),
                'incoming_social_edges': impacts[-4:],
                'recent_social_event_count': len(impacts),
            }

    @staticmethod
    def _update_city_metrics(world_state: dict, hour: int):
        persons = world_state.get('persons', [])
        households = world_state.get('households', [])
        employed = [p for p in persons if p.get('employment_status') == 'employed']

        world_state['city']['world_metrics'] = {
            'hour': hour,
            'active_residents': sum(1 for p in persons if p['current_activity'] not in ['home', 'return_home', 'sleep_recovery']),
            'employment_rate': round(len(employed) / max(1, len(persons)), 3),
            'avg_hourly_wage': round(sum(p.get('hourly_wage', 0.0) for p in employed) / max(1, len(employed)), 2),
            'avg_housing_burden': round(sum(h.get('housing_cost_burden', 0.0) for h in households) / max(1, len(households)), 3),
            'household_pressure_index': round(sum(h.get('pressure_index', 0.0) for h in households) / max(1, len(households)), 3),
            'service_access_score': round(sum(p.get('service_access_score', 0.5) for p in persons) / max(1, len(persons)), 3),
            'social_support_score': round(sum((p.get('social_context') or {}).get('support_index', 0.5) for p in persons) / max(1, len(persons)), 3),
            'district_state_overview': {
                'stressed': sum(1 for d in world_state.get('districts', []) if d.get('pressure_index', 0.0) >= 0.62),
                'stabilizing': sum(1 for d in world_state.get('districts', []) if d.get('state_phase') == 'stabilizing'),
            },
        }

    @staticmethod
    def _phase_for_pressure(pressure_index: float, activity_level: float) -> str:
        if pressure_index >= 0.72:
            return 'strained'
        if pressure_index >= 0.58:
            return 'stabilizing' if activity_level > 0.65 else 'tightening'
        return 'steady'

    @staticmethod
    def _institution_pressure(institution: dict, default: float = 0.3) -> float:
        if not institution:
            return default
        return max(0.0, min(1.0, float(institution.get('pressure_index', default))))

    @staticmethod
    def _institution_access(institution: dict, fallback: float = 0.55) -> float:
        if not institution:
            return fallback
        return max(0.05, min(1.0, float(institution.get('access_score', fallback))))

    @staticmethod
    def _build_institution_load_context(persons: list[dict], households: list[dict], institutions: list[dict]) -> dict:
        loads: dict[str, float] = {}
        for person in persons:
            for key in ('employer_id', 'transit_service_id', 'service_provider_id'):
                institution_id = person.get(key)
                if institution_id:
                    loads[institution_id] = loads.get(institution_id, 0.0) + 1.0
        for household in households:
            landlord_id = household.get('landlord_id')
            if landlord_id:
                loads[landlord_id] = loads.get(landlord_id, 0.0) + 1.0

        context = {}
        for institution in institutions:
            institution_id = institution.get('institution_id')
            if not institution_id:
                continue
            load_count = loads.get(institution_id, 0.0)
            capacity = max(1.0, float(institution.get('capacity', 1.0)))
            utilization = load_count / capacity
            utilization_pressure = max(0.0, min(1.0, utilization - 1.0))
            context[institution_id] = {
                'linked_count': int(load_count),
                'capacity': int(capacity),
                'utilization': round(utilization, 3),
                'utilization_pressure': round(utilization_pressure, 3),
            }
        return context

    @staticmethod
    def _average_pressure(institutions: list[dict], institution_type: str | None = None, include_types: set[str] | None = None) -> float:
        if include_types:
            scoped = [i for i in institutions if i.get('institution_type') in include_types]
        elif institution_type:
            scoped = [i for i in institutions if i.get('institution_type') == institution_type]
        else:
            scoped = institutions
        if not scoped:
            return 0.0
        return sum(max(0.0, min(1.0, i.get('pressure_index', 0.0))) for i in scoped) / len(scoped)
