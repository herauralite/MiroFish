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
    DISTRICT_ARCHETYPE_MODIFIERS = {
        'finance_prestige': {'employment_sensitivity': 1.15, 'housing_sensitivity': 1.05, 'service_resilience': 1.05, 'recovery_bias': 1.08},
        'startup_speculation': {'employment_sensitivity': 1.22, 'housing_sensitivity': 1.0, 'service_resilience': 0.96, 'recovery_bias': 1.0},
        'historic_mixed_use': {'employment_sensitivity': 1.0, 'housing_sensitivity': 1.08, 'service_resilience': 1.02, 'recovery_bias': 1.05},
        'industrial_logistics': {'employment_sensitivity': 1.08, 'housing_sensitivity': 0.95, 'service_resilience': 0.9, 'recovery_bias': 0.94},
        'suburban_family': {'employment_sensitivity': 0.95, 'housing_sensitivity': 1.02, 'service_resilience': 1.12, 'recovery_bias': 1.12},
        'elite_enclave': {'employment_sensitivity': 0.8, 'housing_sensitivity': 0.82, 'service_resilience': 1.2, 'recovery_bias': 1.18},
        'transitional_stressed': {'employment_sensitivity': 1.18, 'housing_sensitivity': 1.24, 'service_resilience': 0.82, 'recovery_bias': 0.82},
        'edge_hinterland': {'employment_sensitivity': 1.08, 'housing_sensitivity': 0.92, 'service_resilience': 0.88, 'recovery_bias': 0.9},
        'education_civic': {'employment_sensitivity': 0.92, 'housing_sensitivity': 0.95, 'service_resilience': 1.14, 'recovery_bias': 1.1},
        'nightlife_vice': {'employment_sensitivity': 1.1, 'housing_sensitivity': 1.0, 'service_resilience': 0.9, 'recovery_bias': 0.92},
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
        household_job_quality = {}
        household_commute_friction = {}
        household_housing_instability = {}

        households_by_id = {h['household_id']: h for h in world_state.get('households', [])}
        institutions_by_id = {i['institution_id']: i for i in world_state.get('institutions', [])}
        institution_load_context = AuraliteRuntimeService._build_institution_load_context(
            persons=world_state.get('persons', []),
            households=world_state.get('households', []),
            institutions=world_state.get('institutions', []),
        )
        AuraliteRuntimeService._update_institutions(
            world_state=world_state,
            institution_load_context=institution_load_context,
        )
        intervention_aftermath = AuraliteRuntimeService._recent_intervention_aftermath(world_state)

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
            employer_profile = AuraliteRuntimeService._institution_effect_profile(employer, employer_load, 'employer')
            landlord_profile = AuraliteRuntimeService._institution_effect_profile(landlord, landlord_load, 'landlord')
            transit_profile = AuraliteRuntimeService._institution_effect_profile(transit_service, transit_load, 'transit')
            service_profile = AuraliteRuntimeService._institution_effect_profile(service_provider, service_load, 'service_access')
            transit_overload = transit_profile['utilization_pressure']
            service_overload = service_profile['utilization_pressure']
            landlord_overload = landlord_profile['utilization_pressure']
            employer_overload = employer_profile['utilization_pressure']

            person['housing_burden_share'] = round(
                max(person.get('housing_burden_share', 0.0), household.get('housing_cost_burden', 0.0)),
                3,
            )
            resident_aftershock = AuraliteRuntimeService._aftermath_for_district(
                intervention_aftermath,
                person.get('district_id'),
                'resident_strain',
            )
            household_aftershock = AuraliteRuntimeService._aftermath_for_district(
                intervention_aftermath,
                household.get('district_id'),
                'household_strain',
            )
            service_scarcity_drag = (service_pressure * 0.09) + service_profile['access_drag'] * 0.16 + (service_overload * 0.08)
            person['service_access_score'] = round(
                max(
                    0.05,
                    min(
                        1.0,
                        (person.get('service_access_score', 0.48) * 0.42)
                        + (service_access_anchor * 0.58)
                        - service_scarcity_drag
                        + (service_profile['support_buffer'] * 0.08),
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
            person['state_summary']['job_quality_pressure'] = round(employer_profile['job_quality_pressure'], 3)
            person['state_summary']['housing_instability_pressure'] = round(landlord_profile['housing_instability'], 3)
            person['state_summary']['commute_friction'] = round(transit_profile['commute_friction'], 3)
            person['state_summary']['support_buffer'] = round(service_profile['support_buffer'], 3)
            person['state_summary']['service_scarcity'] = round(
                min(1.0, max(0.0, service_overload * 0.65 + max(0.0, service_pressure - service_access_anchor) * 0.4)),
                3,
            )
            adaptation = person.setdefault('adaptation_state', {})
            scarcity_streak = int(adaptation.get('service_scarcity_streak', 0))
            housing_streak = int(adaptation.get('housing_instability_streak', 0))
            commute_streak = int(adaptation.get('commute_friction_streak', 0))
            job_streak = int(adaptation.get('job_quality_streak', 0))
            support_buffer_streak = int(adaptation.get('support_buffer_streak', 0))
            scarcity_streak = scarcity_streak + 1 if person['state_summary']['service_scarcity'] >= 0.46 else max(0, scarcity_streak - 1)
            housing_streak = housing_streak + 1 if landlord_profile['housing_instability'] >= 0.46 else max(0, housing_streak - 1)
            commute_streak = commute_streak + 1 if transit_profile['commute_friction'] >= 0.42 else max(0, commute_streak - 1)
            job_streak = job_streak + 1 if employer_profile['job_quality_pressure'] >= 0.44 else max(0, job_streak - 1)
            support_buffer_streak = support_buffer_streak + 1 if service_profile['support_buffer'] >= 0.6 else max(0, support_buffer_streak - 1)
            adaptation_drag = (
                min(0.16, scarcity_streak * 0.012)
                + min(0.14, housing_streak * 0.011)
                + min(0.12, commute_streak * 0.009)
                + min(0.12, job_streak * 0.009)
                - min(0.15, support_buffer_streak * 0.012)
            )
            person['service_access_score'] = round(
                max(0.05, min(1.0, person['service_access_score'] - max(0.0, adaptation_drag * 0.4))),
                3,
            )
            adaptation_support = max(0.0, min(0.2, support_buffer_streak * 0.01))
            person['state_summary']['adaptation_drag'] = round(adaptation_drag, 3)
            person['state_summary']['adaptation_support'] = round(adaptation_support, 3)
            adaptation.update({
                'service_scarcity_streak': scarcity_streak,
                'housing_instability_streak': housing_streak,
                'commute_friction_streak': commute_streak,
                'job_quality_streak': job_streak,
                'support_buffer_streak': support_buffer_streak,
                'adaptation_drag': round(adaptation_drag, 3),
                'adaptation_support': round(adaptation_support, 3),
            })
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
                    + (service_profile['support_buffer'] * 0.08)
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
                    + (employer_profile['job_quality_pressure'] * 0.07)
                    + (landlord_profile['housing_instability'] * 0.07)
                    + (transit_profile['commute_friction'] * 0.06)
                    + (intervention_aftermath['resident_strain'] * 0.1)
                    + (resident_aftershock * 0.12)
                    + (0.12 if person.get('employment_status') != 'employed' else 0.0)
                    + max(0.0, adaptation_drag * 0.24)
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
                    + transit_profile['commute_friction'] * 0.12
                    + service_pressure * 0.18
                    + service_overload * 0.08
                    + employer_profile['job_quality_pressure'] * 0.16
                    + landlord_profile['housing_instability'] * 0.19
                    + (1 - person['service_access_score']) * 0.35
                    + strain_index * 0.22
                    + (intervention_aftermath['resident_strain'] * 0.08)
                    + (household_aftershock * 0.08)
                    + max(0.0, adaptation_drag * 0.22)
                    - support_index * 0.16
                    - adaptation_support * 0.18
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
            district_pressure[district_id].append(person.get('state_summary', {}).get('stress', 0.0) * 0.35)
            district_pressure[district_id].append(max(0.0, person.get('state_summary', {}).get('adaptation_drag', 0.0)) * 0.22)
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
            household_job_quality.setdefault(person['household_id'], []).append(
                person.get('state_summary', {}).get('job_quality_pressure', 0.0),
            )
            household_commute_friction.setdefault(person['household_id'], []).append(
                person.get('state_summary', {}).get('commute_friction', 0.0),
            )
            household_housing_instability.setdefault(person['household_id'], []).append(
                person.get('state_summary', {}).get('housing_instability_pressure', 0.0),
            )

        AuraliteRuntimeService._update_households(
            world_state=world_state,
            household_service_access=household_service_access,
            household_employment=household_employment,
            household_social_support=household_social_support,
            household_job_quality=household_job_quality,
            household_commute_friction=household_commute_friction,
            household_housing_instability=household_housing_instability,
            intervention_aftermath=intervention_aftermath,
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
            intervention_aftermath,
        )
        AuraliteRuntimeService._build_propagation_state(
            world_state=world_state,
            previous_district_snapshot=previous_district_snapshot,
            previous_person_snapshot=previous_person_snapshot,
            previous_household_snapshot=previous_household_snapshot,
            intervention_aftermath=intervention_aftermath,
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
        household_job_quality: dict,
        household_commute_friction: dict,
        household_housing_instability: dict,
        intervention_aftermath: dict,
    ):
        district_lookup = {d.get('district_id'): d for d in world_state.get('districts', [])}
        for household in world_state.get('households', []):
            hh_id = household['household_id']
            member_count = max(1, len(household.get('member_ids', [])))
            employment_values = household_employment.get(hh_id, [])
            service_values = household_service_access.get(hh_id, [])
            social_values = household_social_support.get(hh_id, [])
            job_quality_values = household_job_quality.get(hh_id, [])
            commute_values = household_commute_friction.get(hh_id, [])
            housing_values = household_housing_instability.get(hh_id, [])
            employment_rate = sum(employment_values) / max(1, len(employment_values))
            service_access = sum(service_values) / max(1, len(service_values))
            social_support = sum(social_values) / max(1, len(social_values))
            job_quality_pressure = sum(job_quality_values) / max(1, len(job_quality_values))
            commute_friction = sum(commute_values) / max(1, len(commute_values))
            housing_instability_pressure = sum(housing_values) / max(1, len(housing_values))
            rent_share = household.get('housing_cost_burden', 0.0)
            pressure = household.get('pressure_index', 0.0)
            district_shock = AuraliteRuntimeService._aftermath_for_district(
                intervention_aftermath,
                household.get('district_id'),
                'household_strain',
            )
            adaptation = household.setdefault('adaptation_state', {})
            scarcity_streak = int(adaptation.get('service_scarcity_streak', 0))
            housing_streak = int(adaptation.get('housing_instability_streak', 0))
            commute_streak = int(adaptation.get('commute_friction_streak', 0))
            job_streak = int(adaptation.get('job_quality_streak', 0))
            support_streak = int(adaptation.get('support_buffer_streak', 0))
            scarcity_streak = scarcity_streak + 1 if service_access <= 0.5 else max(0, scarcity_streak - 1)
            housing_streak = housing_streak + 1 if housing_instability_pressure >= 0.45 else max(0, housing_streak - 1)
            commute_streak = commute_streak + 1 if commute_friction >= 0.42 else max(0, commute_streak - 1)
            job_streak = job_streak + 1 if job_quality_pressure >= 0.4 else max(0, job_streak - 1)
            support_streak = support_streak + 1 if social_support >= 0.58 else max(0, support_streak - 1)
            household_adaptation_drag = (
                min(0.2, scarcity_streak * 0.014)
                + min(0.2, housing_streak * 0.013)
                + min(0.14, commute_streak * 0.009)
                + min(0.14, job_streak * 0.01)
                - min(0.18, support_streak * 0.012)
            )

            housing_instability = min(
                1.0,
                (rent_share * 0.62) + (pressure * 0.34) + (household.get('eviction_risk', 0.0) * 0.32) + (housing_instability_pressure * 0.3),
            )
            employment_instability = max(0.0, min(1.0, 1.0 - employment_rate))
            stress = min(
                1.0,
                pressure * 0.5
                + housing_instability * 0.26
                + employment_instability * 0.18
                + job_quality_pressure * 0.1
                + commute_friction * 0.08
                + (1.0 - service_access) * 0.16,
                + max(0.0, household_adaptation_drag * 0.24),
                + (intervention_aftermath.get('household_strain', 0.0) * 0.08),
                + (district_shock * 0.14),
            )
            household_hardship_index = min(
                1.0,
                (housing_instability * 0.36)
                + (employment_instability * 0.24)
                + (job_quality_pressure * 0.16)
                + ((1.0 - service_access) * 0.14)
                + (commute_friction * 0.1)
                + max(0.0, household_adaptation_drag * 0.18)
                + (district_shock * 0.08)
                - (social_support * 0.12),
            )
            hardship_cluster_weight = min(
                1.0,
                max(
                    0.0,
                    (max(0.0, household_hardship_index - 0.55) * 1.3)
                    + min(0.24, max(0.0, household_adaptation_drag) * 0.9),
                ),
            )
            district_arc = (district_lookup.get(household.get('district_id')) or {}).get('arc_state', {})
            pressure_cycle_load = max(
                0.0,
                min(
                    1.0,
                    (float((household.get('context') or {}).get('pressure_cycle_load', 0.0)) * 0.8)
                    + max(0.0, household_hardship_index - 0.5) * 0.32
                    + max(0.0, float(district_arc.get('cumulative_stress_load', 0.0)) - 0.5) * 0.26
                    - max(0.0, social_support - 0.55) * 0.2,
                ),
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
                'hardship_index': round(max(0.0, household_hardship_index), 3),
                'housing_stability_index': round(max(0.0, 1.0 - housing_instability), 3),
                'employment_stability_index': round(max(0.0, 1.0 - employment_instability), 3),
                'job_quality_pressure': round(job_quality_pressure, 3),
                'commute_friction': round(commute_friction, 3),
                'housing_instability_pressure': round(housing_instability_pressure, 3),
                'adaptation_drag': round(household_adaptation_drag, 3),
                'hardship_cluster_weight': round(hardship_cluster_weight, 3),
                'pressure_cycle_load': round(pressure_cycle_load, 3),
            })
            adaptation.update({
                'service_scarcity_streak': scarcity_streak,
                'housing_instability_streak': housing_streak,
                'commute_friction_streak': commute_streak,
                'job_quality_streak': job_streak,
                'support_buffer_streak': support_streak,
                'adaptation_drag': round(household_adaptation_drag, 3),
                'hardship_cluster_weight': round(hardship_cluster_weight, 3),
            })

    @staticmethod
    def _update_institutions(world_state: dict, institution_load_context: dict):
        districts_by_id = {district['district_id']: district for district in world_state.get('districts', [])}
        for institution in world_state.get('institutions', []):
            institution_id = institution.get('institution_id')
            if not institution_id:
                continue
            load = institution_load_context.get(institution_id, {})
            arc = institution.setdefault('arc_state', {})
            prev_pressure = float(arc.get('effective_pressure', institution.get('pressure_index', 0.0)))
            prev_access = float(arc.get('effective_access', institution.get('access_score', 0.5)))
            utilization = float(load.get('utilization', 0.0))
            overload = float(load.get('utilization_pressure', 0.0))
            district = districts_by_id.get(institution.get('district_id'), {})
            district_pressure = float(district.get('pressure_index', 0.0))
            district_support = float(district.get('social_support_score', 0.5))
            institution_type = institution.get('institution_type')
            type_stress = 0.0
            type_recovery = 0.0
            type_service_impact = 0.0
            type_buffering = 0.0
            if institution_type == 'employer':
                type_stress = (district_pressure * 0.16) + (max(0.0, utilization - 0.9) * 0.22)
                type_recovery = district_support * 0.08
                type_service_impact = 0.18
                type_buffering = 0.14
            elif institution_type == 'landlord':
                type_stress = (district_pressure * 0.18) + (max(0.0, utilization - 0.92) * 0.18)
                type_recovery = max(0.0, 1.0 - district_pressure) * 0.07
                type_service_impact = 0.22
                type_buffering = 0.08
            elif institution_type == 'transit':
                type_stress = (district_pressure * 0.14) + (max(0.0, utilization - 0.88) * 0.26)
                type_recovery = district_support * 0.06
                type_service_impact = 0.2
                type_buffering = 0.12
            else:
                type_stress = (district_pressure * 0.13) + (max(0.0, utilization - 0.9) * 0.19)
                type_recovery = district_support * 0.1
                type_service_impact = 0.26
                type_buffering = 0.24
            next_pressure = max(
                0.0,
                min(
                    1.0,
                    (prev_pressure * 0.64)
                    + (float(institution.get('pressure_index', 0.35)) * 0.18)
                    + (overload * 0.14)
                    + type_stress
                    - type_recovery,
                ),
            )
            next_access = max(
                0.05,
                min(
                    1.0,
                    (prev_access * 0.66)
                    + (float(institution.get('access_score', 0.55)) * 0.22)
                    - (overload * 0.2)
                    - (next_pressure * 0.12)
                    + (type_recovery * 0.3),
                ),
            )
            pressure_delta = next_pressure - prev_pressure
            recovery_streak = int(arc.get('recovery_streak', 0))
            stress_streak = int(arc.get('stress_streak', 0))
            if pressure_delta >= 0.01:
                stress_streak += 1
                recovery_streak = max(0, recovery_streak - 1)
            elif pressure_delta <= -0.01:
                recovery_streak += 1
                stress_streak = max(0, stress_streak - 1)
            else:
                stress_streak = max(0, stress_streak - 1)
                recovery_streak = max(0, recovery_streak - 1)
            institution['pressure_index'] = round(next_pressure, 3)
            institution['access_score'] = round(next_access, 3)
            institution['arc_state'] = {
                'effective_pressure': round(next_pressure, 3),
                'effective_access': round(next_access, 3),
                'pressure_delta': round(pressure_delta, 3),
                'stress_streak': stress_streak,
                'recovery_streak': recovery_streak,
                'utilization': round(utilization, 3),
                'utilization_pressure': round(overload, 3),
                'district_pressure_context': round(district_pressure, 3),
                'drift_signal': round((next_pressure - next_access) * (0.65 + type_service_impact * 0.25), 3),
                'resilience_buffer': round(max(0.0, next_access * (0.6 + type_buffering) - next_pressure * 0.32), 3),
                'type_service_impact': round(type_service_impact, 3),
                'type_buffering': round(type_buffering, 3),
            }

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
                        'service_access': person.get('service_access_score', 0.5),
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
                'hardship': float(context.get('hardship_index', context.get('stress_index', household.get('pressure_index', 0.0)))),
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
                        'employment_instability': max(0.0, 1.0 - current['employment_stability']),
                        'housing_instability': max(0.0, 1.0 - current['housing_stability']),
                        'commute_friction': context.get('commute_friction', 0.0),
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
                ('housing', float(system_pressures.get('housing_instability', system_pressures.get('landlord_pressure', 0.0) + system_pressures.get('income_pressure', 0.0) * 0.7))),
                ('employment', float(system_pressures.get('employment_instability', system_pressures.get('employer_pressure', system_pressures.get('income_pressure', 0.0))))),
                ('transit', float(system_pressures.get('transit_pressure', 0.0))),
                ('service_access', float(system_pressures.get('service_pressure', max(0.0, 1.0 - system_pressures.get('service_access', 0.5))))),
                ('social_strain', float(system_pressures.get('social_strain', system_pressures.get('social_strain_index', 0.0)))),
                ('social_support', max(0.0, 1.0 - float(system_pressures.get('social_support', 0.5)))),
                ('commute_friction', float(system_pressures.get('commute_friction', 0.0))),
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
        intervention_aftermath: dict,
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
            institution_drift = (
                sum(float((inst.get('arc_state') or {}).get('drift_signal', 0.0)) for inst in district_institutions)
                / max(1, len(district_institutions))
            )
            institution_buffer = (
                sum(float((inst.get('arc_state') or {}).get('resilience_buffer', 0.0)) for inst in district_institutions)
                / max(1, len(district_institutions))
            )
            archetype_modifiers = AuraliteRuntimeService._district_archetype_modifiers(district.get('archetype'))
            arc_state = district.setdefault('arc_state', {})
            previous_pressure = float(arc_state.get('last_pressure_index', district.get('pressure_index', 0.0)))
            previous_effective_pressure = float(arc_state.get('effective_pressure_index', previous_pressure))
            previous_phase = arc_state.get('phase', district.get('state_phase', 'steady'))
            phase_momentum = float(arc_state.get('phase_momentum', 0.0))
            inflection_memory = float(arc_state.get('inflection_score', 0.0))
            district_stress = (
                sum(p.get('state_summary', {}).get('stress', 0.0) for p in residents) / resident_count
            )
            high_stress_share = (
                sum(1 for p in residents if float((p.get('state_summary') or {}).get('stress', 0.0)) >= 0.68) / resident_count
            )
            high_hardship_share = (
                sum(
                    1
                    for h in district_households
                    if float((h.get('context') or {}).get('hardship_index', h.get('pressure_index', 0.0))) >= 0.64
                ) / max(1, len(district_households))
            )
            adaptation_drag_cluster = (
                sum(float((h.get('adaptation_state') or {}).get('adaptation_drag', 0.0)) for h in district_households)
                / max(1, len(district_households))
            )
            hardship_cluster = min(
                1.0,
                (high_hardship_share * 0.52) + (high_stress_share * 0.34) + min(0.22, adaptation_drag_cluster * 0.65),
            )
            district_aftershock = AuraliteRuntimeService._aftermath_for_district(
                intervention_aftermath,
                district_id,
                'district_pressure',
            )

            pressure_index = min(
                1.0,
                (avg_burden * 0.4)
                + (employment_pressure * 0.22 * archetype_modifiers['employment_sensitivity'])
                + (household_pressure * 0.2)
                + ((1.0 - transit_reliability) * 0.1)
                + ((1 - service_access) * 0.1)
                + (institution_stress * 0.04)
                + (avg_utilization_pressure * 0.08)
                + (employer_pressure * 0.06)
                + (landlord_pressure * 0.1 * archetype_modifiers['housing_sensitivity'])
                + (transit_pressure * 0.05)
                + (service_pressure * 0.05 * (2.0 - archetype_modifiers['service_resilience']))
                + (district_stress * 0.08)
                + ((1.0 - social_support) * 0.1)
                + max(0.0, institution_drift * 0.08)
                + max(0.0, hardship_cluster - 0.45) * 0.16
                - min(0.08, institution_buffer * 0.1),
                + (intervention_aftermath.get('district_pressure', 0.0) * 0.06),
                + (district_aftershock * 0.14),
            )
            pressure_delta = pressure_index - previous_pressure
            rolling_pressure_delta = (
                float(arc_state.get('rolling_pressure_delta', 0.0)) * 0.62
                + (pressure_delta * 0.38)
            )
            sustained_pressure_ticks = int(arc_state.get('sustained_pressure_ticks', 0))
            sustained_recovery_ticks = int(arc_state.get('sustained_recovery_ticks', 0))
            cumulative_stress_load = float(arc_state.get('cumulative_stress_load', 0.0))
            recovery_durability = float(arc_state.get('recovery_durability', 0.0))
            if pressure_delta >= 0.01:
                sustained_pressure_ticks += 1
                sustained_recovery_ticks = max(0, sustained_recovery_ticks - 1)
            elif pressure_delta <= -0.01:
                sustained_recovery_ticks += 1
                sustained_pressure_ticks = max(0, sustained_pressure_ticks - 1)
            else:
                sustained_pressure_ticks = max(0, sustained_pressure_ticks - 1)
                sustained_recovery_ticks = max(0, sustained_recovery_ticks - 1)
            local_recovery_context = (
                (service_access * 0.35)
                + (social_support * 0.35)
                + (transit_reliability * 0.14)
                + ((1.0 - household_pressure) * 0.16)
                + min(0.12, institution_buffer * 0.2)
                - min(0.12, max(0.0, institution_drift) * 0.16)
                - min(0.12, hardship_cluster * 0.1)
            )
            cumulative_stress_load = max(
                0.0,
                min(
                    1.0,
                    (cumulative_stress_load * 0.84)
                    + max(0.0, pressure_index - 0.54) * 0.22
                    + max(0.0, hardship_cluster - 0.52) * 0.2
                    + max(0.0, institution_drift) * 0.18
                    + (0.03 if sustained_pressure_ticks >= 3 else 0.0)
                    - min(0.06, local_recovery_context * 0.06),
                ),
            )
            recovery_durability = max(
                0.0,
                min(
                    1.0,
                    (recovery_durability * 0.82)
                    + max(0.0, local_recovery_context - 0.5) * 0.26
                    + (0.026 if sustained_recovery_ticks >= 3 else 0.0)
                    - max(0.0, pressure_index - 0.55) * 0.18
                    - max(0.0, hardship_cluster - 0.56) * 0.14
                    - max(0.0, cumulative_stress_load - 0.58) * 0.12,
                ),
            )
            phase_momentum = max(
                -1.0,
                min(
                    1.0,
                    (phase_momentum * 0.62)
                    + (rolling_pressure_delta * 3.4)
                    + (max(0.0, institution_drift) * 0.14)
                    + (max(0.0, cumulative_stress_load - 0.5) * 0.12)
                    - (local_recovery_context * 0.1),
                ),
            )
            inflection_score = max(
                -1.0,
                min(
                    1.0,
                    (inflection_memory * 0.58)
                    + ((-rolling_pressure_delta) * 2.2)
                    + ((local_recovery_context - 0.5) * 0.46)
                    + (max(0.0, recovery_durability - 0.45) * 0.24)
                    - (max(0.0, hardship_cluster - 0.5) * 0.28),
                ),
            )
            effective_pressure = max(
                0.0,
                min(
                    1.0,
                    (previous_effective_pressure * 0.62)
                    + (pressure_index * 0.38)
                    + (0.016 if sustained_pressure_ticks >= 3 else 0.0)
                    - (0.016 if sustained_recovery_ticks >= 3 else 0.0),
                    + max(0.0, cumulative_stress_load - 0.56) * 0.03
                    + max(0.0, phase_momentum) * 0.015
                    - max(0.0, inflection_score) * 0.01
                    - max(0.0, recovery_durability - 0.55) * 0.018,
                ),
            )
            shallow_recovery_risk = max(
                0.0,
                min(
                    1.0,
                    max(0.0, 0.58 - recovery_durability)
                    + max(0.0, hardship_cluster - 0.5) * 0.45
                    + max(0.0, cumulative_stress_load - 0.52) * 0.38
                    - max(0.0, local_recovery_context - 0.56) * 0.35,
                ),
            )
            next_phase = AuraliteRuntimeService._phase_for_pressure(
                pressure_index=pressure_index,
                activity_level=district['current_activity_level'],
                recovery_bias=archetype_modifiers['recovery_bias'],
                effective_pressure=effective_pressure,
                trend_delta=rolling_pressure_delta,
                sustained_pressure_ticks=sustained_pressure_ticks,
                sustained_recovery_ticks=sustained_recovery_ticks,
                previous_phase=previous_phase,
                local_recovery_context=local_recovery_context,
                phase_momentum=phase_momentum,
                institution_drift=institution_drift,
                hardship_cluster=hardship_cluster,
                cumulative_stress_load=cumulative_stress_load,
                recovery_durability=recovery_durability,
                shallow_recovery_risk=shallow_recovery_risk,
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
            district['state_phase'] = next_phase
            district['arc_state'] = {
                'phase': next_phase,
                'last_pressure_index': round(pressure_index, 3),
                'effective_pressure_index': round(effective_pressure, 3),
                'pressure_delta': round(pressure_delta, 3),
                'rolling_pressure_delta': round(rolling_pressure_delta, 3),
                'sustained_pressure_ticks': sustained_pressure_ticks,
                'sustained_recovery_ticks': sustained_recovery_ticks,
                'local_recovery_context': round(local_recovery_context, 3),
                'archetype_recovery_bias': round(archetype_modifiers['recovery_bias'], 3),
            }
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
                'institution_drift': round(institution_drift, 3),
                'resilience_buffer': round(institution_buffer, 3),
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
                'intervention_aftermath_pressure': round(intervention_aftermath.get('district_pressure', 0.0), 3),
                'district_aftermath_pressure': round(district_aftershock, 3),
                'hardship_cluster': round(hardship_cluster, 3),
                'hardship_cluster_breakdown': {
                    'high_household_hardship_share': round(high_hardship_share, 3),
                    'high_resident_stress_share': round(high_stress_share, 3),
                    'adaptation_drag_cluster': round(adaptation_drag_cluster, 3),
                },
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
                'arc_state': district['arc_state'],
                'evolution_hook': {
                    'next_update_window': 'weekly',
                    'risk': 'elevated' if pressure_index >= 0.62 else 'stable',
                    'district_archetype': district.get('archetype'),
                    'recovery_bias': round(archetype_modifiers['recovery_bias'], 3),
                },
            }
            district['arc_state'].update({
                'phase_momentum': round(phase_momentum, 3),
                'inflection_score': round(inflection_score, 3),
                'hardship_cluster': round(hardship_cluster, 3),
                'institution_drift': round(institution_drift, 3),
                'resilience_buffer': round(institution_buffer, 3),
                'cumulative_stress_load': round(cumulative_stress_load, 3),
                'recovery_durability': round(recovery_durability, 3),
                'shallow_recovery_risk': round(shallow_recovery_risk, 3),
                'decline_lock': bool(next_phase in {'tightening', 'strained'} and phase_momentum >= 0.25),
                'recovery_lock': bool(next_phase in {'stabilizing', 'recovering'} and inflection_score >= 0.2 and recovery_durability >= 0.45),
                'last_turning_signal': (
                    'decline_risk'
                    if phase_momentum >= 0.25
                    else 'recovery_candidate'
                    if inflection_score >= 0.2
                    else 'mixed'
                ),
            })
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
            phase = district.get('state_phase')
            phase_multiplier = 1.12 if phase in {'tightening', 'strained'} else 0.9
            neighbor_recovery = sum(
                1 for n in neighbors if n.get('state_phase') in {'stabilizing', 'recovering'}
            ) / len(neighbors)
            neighbor_decline = sum(
                1 for n in neighbors if n.get('state_phase') in {'tightening', 'strained'}
            ) / len(neighbors)
            stressed_cluster_share = sum(
                1 for n in neighbors
                if float((n.get('arc_state') or {}).get('cumulative_stress_load', 0.0)) >= 0.56
            ) / len(neighbors)
            recovery_cluster_share = sum(
                1 for n in neighbors
                if float((n.get('arc_state') or {}).get('recovery_durability', 0.0)) >= 0.5
            ) / len(neighbors)
            contagion_vector = max(0.0, neighbor_decline - neighbor_recovery)
            recovery_vector = max(0.0, neighbor_recovery - neighbor_decline)
            base_gap_effect = pressure_gap * 0.16 * (0.35 + vulnerability) * phase_multiplier
            decline_spread = contagion_vector * (0.01 + vulnerability * 0.02 + stressed_cluster_share * 0.014)
            recovery_spread = recovery_vector * (
                0.012
                + max(0.0, float(district.get('social_support_score', 0.5)) - 0.45) * 0.03
                + max(0.0, float(district.get('service_access_score', 0.5)) - 0.45) * 0.03
                + recovery_cluster_share * 0.012
            )
            stabilization_drag = max(0.0, float((district.get('arc_state') or {}).get('hardship_cluster', 0.0)) - 0.55) * 0.012
            cluster_amplification = max(
                -0.03,
                min(
                    0.03,
                    (stressed_cluster_share - recovery_cluster_share) * 0.024
                    + (neighbor_pressure - 0.5) * 0.018,
                ),
            )
            ripple_effect = max(
                -0.06,
                min(0.06, base_gap_effect + decline_spread - recovery_spread + stabilization_drag + cluster_amplification),
            )
            ripple_cache[district_id] = {
                'neighbor_pressure': round(neighbor_pressure, 3),
                'pressure_gap': round(pressure_gap, 3),
                'vulnerability': round(vulnerability, 3),
                'ripple_effect': round(ripple_effect, 3),
                'contagion_vector': round(contagion_vector, 3),
                'recovery_vector': round(recovery_vector, 3),
                'stabilization_drag': round(stabilization_drag, 3),
                'stressed_cluster_share': round(stressed_cluster_share, 3),
                'recovery_cluster_share': round(recovery_cluster_share, 3),
                'cluster_amplification': round(cluster_amplification, 3),
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
                'contagion_vector': ripple['contagion_vector'],
                'recovery_vector': ripple['recovery_vector'],
                'stabilization_drag': ripple['stabilization_drag'],
                'stressed_cluster_share': ripple['stressed_cluster_share'],
                'recovery_cluster_share': ripple['recovery_cluster_share'],
                'cluster_amplification': ripple['cluster_amplification'],
                'note': (
                    'Nearby decline/recovery vectors and local vulnerability produced a bounded spillover adjustment.'
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
        if institution_summary.get('institution_drift', 0) >= 0.09:
            drivers.append('Institution drift is compounding pressure faster than service recovery can absorb.')
        if institution_summary.get('resilience_buffer', 0) >= 0.22:
            drivers.append('Institution resilience buffers are helping hold recovery conditions in place.')
        hardship_cluster = ((district.get('derived_summary') or {}).get('hardship_cluster', 0.0))
        if hardship_cluster >= 0.58:
            drivers.append('Hardship is concentrated across clustered households, making recovery harder to sustain.')
        arc_state = district.get('arc_state') or {}
        if float(arc_state.get('recovery_durability', 0.0)) >= 0.52 and district.get('state_phase') in {'stabilizing', 'recovering'}:
            drivers.append('Recovery durability is building through stronger support/service buffering over repeated ticks.')
        if float(arc_state.get('shallow_recovery_risk', 0.0)) >= 0.56 and district.get('state_phase') in {'stabilizing', 'recovering'}:
            drivers.append('Recovery remains shallow: cumulative hardship and stress memory still threaten reversal.')
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
        intervention_aftermath: dict,
    ):
        persons = world_state.get('persons', [])
        households = world_state.get('households', [])
        districts = world_state.get('districts', [])
        district_by_id = {district.get('district_id'): district for district in districts}
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
            contagion_vector = float(ripple_context.get('contagion_vector', 0.0))
            recovery_vector = float(ripple_context.get('recovery_vector', 0.0))
            stressed_cluster_share = float(ripple_context.get('stressed_cluster_share', 0.0))
            recovery_cluster_share = float(ripple_context.get('recovery_cluster_share', 0.0))
            if abs(pressure_delta) < 0.012 and abs(ripple_effect) < 0.012:
                continue

            base_strength = max(abs(pressure_delta), abs(ripple_effect))
            pressure_sign = 1 if pressure_delta >= 0 else -1
            for target_id in ripple_context.get('neighbor_ids', []):
                target = district_by_id.get(target_id)
                if not target:
                    continue
                target_modifier = (
                    (1.0 - float(target.get('social_support_score', 0.5))) * 0.52
                    + (1.0 - float(target.get('service_access_score', 0.5))) * 0.48
                )
                phase_factor = 1.0
                if district.get('state_phase') in {'tightening', 'strained'}:
                    phase_factor += contagion_vector * 0.25
                if district.get('state_phase') in {'stabilizing', 'recovering'}:
                    phase_factor -= recovery_vector * 0.22
                cluster_factor = 1.0 + max(-0.2, min(0.22, (stressed_cluster_share - recovery_cluster_share) * 0.4))
                impact = round(
                    min(0.06, base_strength * (0.24 + target_modifier * 0.26) * phase_factor * cluster_factor) * pressure_sign,
                    3,
                )
                if intervention_aftermath.get('social_propagation', 0.0) > 0:
                    impact = round(max(-0.08, min(0.08, impact * (1.0 + intervention_aftermath['social_propagation'] * 0.18))), 3)
                district_events.append({
                    'event_type': 'district_neighbor_ripple',
                    'source_district_id': district_id,
                    'target_district_id': target_id,
                    'impact_pressure': impact,
                    'contagion_vector': round(contagion_vector, 3),
                    'recovery_vector': round(recovery_vector, 3),
                    'service_delta': service_delta,
                    'social_delta': social_delta,
                    'stressed_cluster_share': round(stressed_cluster_share, 3),
                    'recovery_cluster_share': round(recovery_cluster_share, 3),
                    'driver': 'pressure_and_support_spillover',
                })
                district_impacts.setdefault(target_id, []).append({
                    'from': district_id,
                    'impact_pressure': impact,
                    'contagion_vector': round(contagion_vector, 3),
                    'recovery_vector': round(recovery_vector, 3),
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
                if intervention_aftermath.get('social_propagation', 0.0) > 0:
                    propagation = round(propagation * (1.0 + intervention_aftermath['social_propagation'] * 0.2), 3)
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
            'schema_version': 'm11-regime-cycle-v1',
            'last_updated_at': world_state.get('world', {}).get('current_time'),
            'district_neighbor_events': district_events[-40:],
            'social_events': social_events[-60:],
            'district_recent_impacts': {k: v[-6:] for k, v in district_impacts.items()},
            'resident_recent_impacts': {k: v[-5:] for k, v in resident_incoming.items()},
            'household_recent_impacts': {k: v[-8:] for k, v in household_incoming.items()},
            'notes': [
                'Cross-system turning and contagion scaffold; bounded effects only.',
                'Designed for explainability and future event-system expansion.',
                'Includes regime-cycle cluster signals for city-level drift detection.',
                f"Aftermath propagation multiplier: {round(1.0 + intervention_aftermath.get('social_propagation', 0.0) * 0.2, 3)}",
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
                'contagion_pressure': round(sum(max(0.0, row.get('impact_pressure', 0.0)) for row in impacts), 3),
                'recovery_pressure': round(sum(min(0.0, row.get('impact_pressure', 0.0)) for row in impacts), 3),
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
        districts = world_state.get('districts', [])
        employed = [p for p in persons if p.get('employment_status') == 'employed']
        regime_state = AuraliteRuntimeService._city_regime_state(world_state, districts)

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
                'stressed': sum(1 for d in districts if d.get('pressure_index', 0.0) >= 0.62),
                'stabilizing': sum(1 for d in districts if d.get('state_phase') == 'stabilizing'),
                'recovering': sum(1 for d in districts if d.get('state_phase') == 'recovering'),
            },
            'regime_state': regime_state,
        }
        world_state['city']['regime_state'] = regime_state

    @staticmethod
    def _phase_for_pressure(
        pressure_index: float,
        activity_level: float,
        recovery_bias: float = 1.0,
        effective_pressure: float | None = None,
        trend_delta: float = 0.0,
        sustained_pressure_ticks: int = 0,
        sustained_recovery_ticks: int = 0,
        previous_phase: str = 'steady',
        local_recovery_context: float = 0.5,
        phase_momentum: float = 0.0,
        institution_drift: float = 0.0,
        hardship_cluster: float = 0.0,
        cumulative_stress_load: float = 0.0,
        recovery_durability: float = 0.0,
        shallow_recovery_risk: float = 0.0,
    ) -> str:
        pressure_tighten = (
            0.58
            + max(-0.06, min(0.08, (1.0 - recovery_bias) * 0.12))
            + max(0.0, institution_drift) * 0.08
            + max(0.0, hardship_cluster - 0.5) * 0.06
            - max(0.0, local_recovery_context - 0.55) * 0.08
        )
        pressure_strained = (
            0.72
            + max(-0.05, min(0.07, (1.0 - recovery_bias) * 0.1))
            + max(0.0, institution_drift) * 0.09
            + max(0.0, hardship_cluster - 0.52) * 0.08
            - max(0.0, local_recovery_context - 0.58) * 0.06
        )
        effective_pressure = pressure_index if effective_pressure is None else effective_pressure
        if (
            effective_pressure >= pressure_strained
            or sustained_pressure_ticks >= 4
            or phase_momentum >= 0.36
            or cumulative_stress_load >= 0.72
        ):
            return 'strained'
        if effective_pressure >= pressure_tighten or phase_momentum >= 0.22:
            if trend_delta <= -0.01 and local_recovery_context >= 0.54 and phase_momentum <= 0.1 and shallow_recovery_risk <= 0.5:
                return 'stabilizing'
            return 'tightening'
        if effective_pressure >= max(0.5, pressure_tighten - 0.1):
            if (
                sustained_recovery_ticks >= 3
                and local_recovery_context >= 0.56
                and phase_momentum <= 0.08
                and recovery_durability >= 0.44
                and shallow_recovery_risk <= 0.54
            ):
                return 'recovering'
            if previous_phase in {'tightening', 'strained'} and trend_delta <= -0.005:
                return 'stabilizing'
        if effective_pressure >= max(0.42, pressure_tighten - 0.16) and recovery_bias >= 1.05:
            if (
                sustained_recovery_ticks >= 2
                and trend_delta <= -0.01
                and hardship_cluster <= 0.56
                and recovery_durability >= 0.48
                and shallow_recovery_risk <= 0.48
            ):
                return 'recovering'
        if (
            previous_phase == 'recovering'
            and sustained_pressure_ticks == 0
            and trend_delta <= 0.0
            and phase_momentum <= 0.1
            and shallow_recovery_risk <= 0.56
        ):
            return 'recovering'
        if previous_phase in {'tightening', 'strained'} and trend_delta < 0.0 and activity_level > 0.6 and local_recovery_context >= 0.5:
            return 'stabilizing'
        return 'steady'

    @staticmethod
    def _city_regime_state(world_state: dict, districts: list[dict]) -> dict:
        if not districts:
            return {'phase': 'mixed_transition', 'confidence': 0.0, 'signals': {}, 'regime_shift_candidate': False}
        count = len(districts)
        stressed_share = sum(1 for d in districts if d.get('state_phase') in {'tightening', 'strained'}) / count
        recovering_share = sum(1 for d in districts if d.get('state_phase') in {'stabilizing', 'recovering'}) / count
        avg_pressure = sum(float(d.get('pressure_index', 0.0)) for d in districts) / count
        avg_momentum = sum(float((d.get('arc_state') or {}).get('phase_momentum', 0.0)) for d in districts) / count
        avg_drift = sum(float((d.get('arc_state') or {}).get('institution_drift', 0.0)) for d in districts) / count
        avg_hardship = sum(float((d.get('arc_state') or {}).get('hardship_cluster', 0.0)) for d in districts) / count
        stress_cycle = sum(float((d.get('arc_state') or {}).get('cumulative_stress_load', 0.0)) for d in districts) / count
        recovery_durability = sum(float((d.get('arc_state') or {}).get('recovery_durability', 0.0)) for d in districts) / count
        shallow_recovery = sum(float((d.get('arc_state') or {}).get('shallow_recovery_risk', 0.0)) for d in districts) / count
        clustered_decline = sum(
            1 for d in districts
            if ((d.get('derived_summary') or {}).get('ripple_context') or {}).get('stressed_cluster_share', 0.0) >= 0.5
        ) / count
        clustered_recovery = sum(
            1 for d in districts
            if ((d.get('derived_summary') or {}).get('ripple_context') or {}).get('recovery_cluster_share', 0.0) >= 0.5
        ) / count
        if stressed_share >= 0.58 and (avg_pressure >= 0.62 or clustered_decline >= 0.4):
            phase = 'clustered_decline'
        elif stress_cycle >= 0.62 and avg_momentum >= 0.08:
            phase = 'broad_strain'
        elif recovering_share >= 0.52 and recovery_durability >= 0.5 and shallow_recovery <= 0.5:
            phase = 'stabilizing'
        elif recovering_share >= 0.45 and shallow_recovery > 0.52:
            phase = 'fragile_recovery'
        else:
            phase = 'mixed_transition'
        regime_shift_candidate = (
            abs(avg_momentum) >= 0.1
            or abs(stressed_share - recovering_share) >= 0.25
            or abs(clustered_decline - clustered_recovery) >= 0.22
        )
        confidence = min(
            1.0,
            max(
                0.2,
                abs(stressed_share - recovering_share) * 0.7
                + abs(avg_momentum) * 0.9
                + max(clustered_decline, clustered_recovery) * 0.45
                + abs(stress_cycle - recovery_durability) * 0.5,
            ),
        )
        signals = {
            'stressed_share': round(stressed_share, 3),
            'recovering_share': round(recovering_share, 3),
            'avg_pressure': round(avg_pressure, 3),
            'avg_phase_momentum': round(avg_momentum, 3),
            'avg_institution_drift': round(avg_drift, 3),
            'avg_hardship_cluster': round(avg_hardship, 3),
            'stress_cycle_load': round(stress_cycle, 3),
            'recovery_durability': round(recovery_durability, 3),
            'shallow_recovery_risk': round(shallow_recovery, 3),
            'clustered_decline_share': round(clustered_decline, 3),
            'clustered_recovery_share': round(clustered_recovery, 3),
        }
        recovery_spread_state = AuraliteRuntimeService._city_recovery_spread_state(districts)
        lead_lag = AuraliteRuntimeService._city_lead_lag_signals(districts, phase=phase)
        intervention_regime_effect = AuraliteRuntimeService._intervention_regime_effect_state(
            world_state=world_state,
            districts=districts,
            phase=phase,
            signals=signals,
            recovery_spread_state=recovery_spread_state,
        )
        interpretation = AuraliteRuntimeService._regime_interpretation(
            phase=phase,
            signals=signals,
            recovery_spread_state=recovery_spread_state,
            intervention_regime_effect=intervention_regime_effect,
        )
        return {
            'phase': phase,
            'confidence': round(confidence, 3),
            'regime_shift_candidate': bool(regime_shift_candidate),
            'signals': signals,
            'interpretation': interpretation,
            'lead_lag_districts': lead_lag,
            'recovery_spread_state': recovery_spread_state,
            'intervention_regime_effect': intervention_regime_effect,
        }

    @staticmethod
    def _city_lead_lag_signals(districts: list[dict], phase: str) -> dict:
        classified = []
        for district in districts:
            arc = district.get('arc_state') or {}
            ripple = ((district.get('derived_summary') or {}).get('ripple_context') or {})
            momentum = float(arc.get('phase_momentum', 0.0))
            inflection = float(arc.get('inflection_score', 0.0))
            durability = float(arc.get('recovery_durability', 0.0))
            shallow_risk = float(arc.get('shallow_recovery_risk', 0.0))
            hardship = float(arc.get('hardship_cluster', 0.0))
            contagion = float(ripple.get('contagion_vector', 0.0))
            recovery_vector = float(ripple.get('recovery_vector', 0.0))
            state_phase = district.get('state_phase', 'steady')
            score = abs(momentum) * 0.34 + abs(inflection) * 0.28 + abs(contagion - recovery_vector) * 0.2 + hardship * 0.18
            role = 'mixed_transition'
            if state_phase in {'tightening', 'strained'} and (momentum >= 0.14 or contagion >= 0.18):
                role = 'decline_leader'
            elif state_phase in {'stabilizing', 'recovering'} and inflection >= 0.14 and durability >= 0.48 and recovery_vector >= 0.12:
                role = 'recovery_leader'
            elif state_phase in {'stabilizing', 'recovering'} and (shallow_risk >= 0.56 or durability <= 0.38):
                role = 'fragile_laggard'
            elif abs(momentum) <= 0.08 and abs(inflection) <= 0.08:
                role = 'mixed_transition'
            classified.append({
                'district_id': district.get('district_id'),
                'name': district.get('name', district.get('district_id')),
                'state_phase': state_phase,
                'role': role,
                'score': round(score, 3),
                'momentum': round(momentum, 3),
                'inflection': round(inflection, 3),
                'hardship_cluster': round(hardship, 3),
                'recovery_durability': round(durability, 3),
                'shallow_recovery_risk': round(shallow_risk, 3),
            })

        def top(role: str, limit: int = 4) -> list[dict]:
            return sorted(
                [row for row in classified if row.get('role') == role],
                key=lambda row: (-float(row.get('score', 0.0)), str(row.get('district_id', ''))),
            )[:limit]

        return {
            'phase_context': phase,
            'decline_leaders': top('decline_leader'),
            'recovery_leaders': top('recovery_leader'),
            'fragile_laggards': top('fragile_laggard'),
            'mixed_transition_districts': top('mixed_transition'),
        }

    @staticmethod
    def _city_recovery_spread_state(districts: list[dict]) -> dict:
        count = max(1, len(districts))
        recovering = [d for d in districts if d.get('state_phase') in {'stabilizing', 'recovering'}]
        recovering_share = len(recovering) / count
        durability = [float((d.get('arc_state') or {}).get('recovery_durability', 0.0)) for d in recovering]
        shallow_risk = [float((d.get('arc_state') or {}).get('shallow_recovery_risk', 0.0)) for d in recovering]
        recovery_vector = [
            float((((d.get('derived_summary') or {}).get('ripple_context') or {}).get('recovery_vector', 0.0)))
            for d in recovering
        ]
        contagion_vector = [
            float((((d.get('derived_summary') or {}).get('ripple_context') or {}).get('contagion_vector', 0.0)))
            for d in recovering
        ]
        avg_durability = sum(durability) / max(1, len(durability))
        avg_shallow = sum(shallow_risk) / max(1, len(shallow_risk))
        avg_recovery_vector = sum(recovery_vector) / max(1, len(recovery_vector))
        avg_contagion = sum(contagion_vector) / max(1, len(contagion_vector))
        spread_score = (
            recovering_share * 0.38
            + max(0.0, avg_durability - 0.42) * 0.34
            + max(0.0, avg_recovery_vector - avg_contagion) * 0.28
        )
        stall_score = (
            max(0.0, avg_shallow - 0.5) * 0.4
            + max(0.0, avg_contagion - avg_recovery_vector) * 0.32
            + max(0.0, 0.46 - recovering_share) * 0.28
        )
        if spread_score >= 0.2 and avg_shallow <= 0.5 and avg_recovery_vector >= avg_contagion:
            lane = 'spreading'
        elif recovering_share <= 0.22 and avg_durability >= 0.5:
            lane = 'isolated'
        elif stall_score >= 0.16 and avg_shallow >= 0.54:
            lane = 'stalled'
        elif avg_contagion > avg_recovery_vector and avg_shallow >= 0.56:
            lane = 'reversing_under_stress'
        else:
            lane = 'mixed'
        return {
            'lane': lane,
            'recovering_share': round(recovering_share, 3),
            'avg_recovery_durability': round(avg_durability, 3),
            'avg_shallow_recovery_risk': round(avg_shallow, 3),
            'avg_recovery_vector': round(avg_recovery_vector, 3),
            'avg_contagion_vector': round(avg_contagion, 3),
            'spread_score': round(spread_score, 3),
            'stall_score': round(stall_score, 3),
        }

    @staticmethod
    def _intervention_regime_effect_state(
        world_state: dict,
        districts: list[dict],
        phase: str,
        signals: dict,
        recovery_spread_state: dict,
    ) -> dict:
        intervention_state = world_state.get('intervention_state') or {}
        history = intervention_state.get('history') or []
        active = intervention_state.get('active_aftermath') or []
        if not history and not active:
            return {
                'signal': 'no_active_intervention_signal',
                'city_trajectory_effect': 'unknown',
                'targeted_footprint_share': 0.0,
                'notes': ['No recent intervention aftermath found to evaluate city-regime steering.'],
            }
        latest = (history or [{}])[-1]
        delta = ((latest.get('effects') or {}).get('delta_summary') or {})
        targeted = {row.get('district_id') for row in active if isinstance(row, dict) and row.get('district_id')}
        footprint = len(targeted) / max(1, len(districts))
        service_gain = float(delta.get('service_access_score', 0.0))
        pressure_relief = -float(delta.get('household_pressure_index', 0.0))
        stress_district_relief = -float(delta.get('stressed_districts', 0.0))
        regime_drag = float(signals.get('stress_cycle_load', 0.0)) - float(signals.get('recovery_durability', 0.0))
        lane = recovery_spread_state.get('lane', 'mixed')
        steering_score = service_gain * 0.34 + pressure_relief * 0.38 + stress_district_relief * 0.28 + max(0.0, footprint - 0.2) * 0.15
        if phase in {'clustered_decline', 'broad_strain'} and steering_score >= 0.02:
            signal = 'bending_decline'
            trajectory = 'improving'
        elif phase in {'fragile_recovery', 'stabilizing'} and steering_score >= 0.0 and lane in {'stalled', 'isolated', 'mixed'}:
            signal = 'supporting_fragile_recovery'
            trajectory = 'holding_with_support'
        elif footprint <= 0.2 and abs(steering_score) < 0.018:
            signal = 'local_pocket_shift_only'
            trajectory = 'limited_city_impact'
        elif steering_score < -0.01 or (regime_drag >= 0.14 and lane in {'stalled', 'reversing_under_stress'}):
            signal = 'failing_to_influence_regime'
            trajectory = 'worsening'
        else:
            signal = 'mixed_regime_effect'
            trajectory = 'unclear'
        return {
            'signal': signal,
            'city_trajectory_effect': trajectory,
            'steering_score': round(steering_score, 3),
            'targeted_footprint_share': round(footprint, 3),
            'recent_delta': {
                'service_access_score': round(service_gain, 3),
                'household_pressure_index': round(float(delta.get('household_pressure_index', 0.0)), 3),
                'stressed_districts': round(float(delta.get('stressed_districts', 0.0)), 3),
            },
            'notes': [
                f"Recovery lane is {lane}; regime phase is {phase}.",
                f"Intervention footprint covers {len(targeted)} districts.",
            ],
        }

    @staticmethod
    def _regime_interpretation(
        phase: str,
        signals: dict,
        recovery_spread_state: dict,
        intervention_regime_effect: dict,
    ) -> dict:
        drivers = []
        stress_cycle = float(signals.get('stress_cycle_load', 0.0))
        durability = float(signals.get('recovery_durability', 0.0))
        shallow = float(signals.get('shallow_recovery_risk', 0.0))
        hardship = float(signals.get('avg_hardship_cluster', 0.0))
        momentum = float(signals.get('avg_phase_momentum', 0.0))
        if stress_cycle >= 0.62:
            drivers.append('Stress-cycle load is elevated across districts.')
        if hardship >= 0.56:
            drivers.append('Hardship remains clustered and slows regime improvement.')
        if durability >= 0.5:
            drivers.append('Recovery durability is present in multiple districts.')
        if shallow >= 0.54:
            drivers.append('Shallow-recovery risk is high and can trigger relapse.')
        if abs(momentum) >= 0.08:
            drivers.append('District phase momentum indicates active transition pressure.')
        spread_lane = recovery_spread_state.get('lane', 'mixed')
        if spread_lane != 'mixed':
            drivers.append(f'Recovery dynamics currently read as {spread_lane}.')
        effect_signal = intervention_regime_effect.get('signal')
        if effect_signal and effect_signal != 'no_active_intervention_signal':
            drivers.append(f'Intervention regime effect is {effect_signal}.')
        if not drivers:
            drivers.append('No single dominant citywide driver; phase is mixed by small offsets.')

        if stress_cycle - durability >= 0.14 or phase in {'clustered_decline', 'broad_strain'}:
            trajectory = 'strengthening_decline'
        elif durability - stress_cycle >= 0.12 and shallow <= 0.5 and spread_lane == 'spreading':
            trajectory = 'strengthening_recovery'
        elif abs(stress_cycle - durability) <= 0.07:
            trajectory = 'mixed'
        else:
            trajectory = 'weakening_decline'

        risk = 'clustered decline persistence'
        opportunity = 'no clear citywide opening yet'
        if trajectory in {'strengthening_decline', 'mixed'}:
            risk = 'recovery stall and reversal in fragile districts'
        if trajectory in {'strengthening_recovery', 'weakening_decline'}:
            opportunity = 'spread durable recovery from lead districts into lagging zones'

        return {
            'drivers': drivers[:4],
            'trajectory': trajectory,
            'dominant_risk': risk,
            'dominant_opportunity': opportunity,
            'phase_relevance': f"{phase} matters because citywide stress/recovery balance is currently {trajectory.replace('_', ' ')}.",
        }

    @staticmethod
    def _district_archetype_modifiers(archetype: str | None) -> dict:
        return AuraliteRuntimeService.DISTRICT_ARCHETYPE_MODIFIERS.get(
            archetype or '',
            {'employment_sensitivity': 1.0, 'housing_sensitivity': 1.0, 'service_resilience': 1.0, 'recovery_bias': 1.0},
        )

    @staticmethod
    def _institution_effect_profile(institution: dict, load_context: dict, institution_type: str) -> dict:
        pressure = AuraliteRuntimeService._institution_pressure(institution, default=0.35)
        access = AuraliteRuntimeService._institution_access(institution, fallback=0.5)
        utilization = float((load_context or {}).get('utilization', 0.0))
        utilization_pressure = float((load_context or {}).get('utilization_pressure', 0.0))
        capacity = max(1.0, float((load_context or {}).get('capacity', institution.get('capacity', 1.0) if institution else 1.0)))
        bounded_scale = min(1.0, capacity / 220.0)

        profile = {
            'utilization': round(utilization, 3),
            'utilization_pressure': round(utilization_pressure, 3),
            'capacity_scale': round(bounded_scale, 3),
            'access_drag': max(0.0, 1.0 - access),
            'job_quality_pressure': 0.0,
            'housing_instability': 0.0,
            'commute_friction': 0.0,
            'support_buffer': 0.0,
        }
        if institution_type == 'employer':
            profile['job_quality_pressure'] = min(1.0, pressure * 0.62 + utilization_pressure * 0.24 + profile['access_drag'] * 0.18)
        elif institution_type == 'landlord':
            profile['housing_instability'] = min(1.0, pressure * 0.64 + utilization_pressure * 0.2 + profile['access_drag'] * 0.18)
        elif institution_type == 'transit':
            profile['commute_friction'] = min(1.0, pressure * 0.4 + utilization_pressure * 0.42 + profile['access_drag'] * 0.28)
        else:
            profile['support_buffer'] = min(1.0, access * 0.58 + (1.0 - pressure) * 0.24 + bounded_scale * 0.18 - utilization_pressure * 0.22)
        return profile

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

    @staticmethod
    def _recent_intervention_aftermath(world_state: dict) -> dict:
        active_entries = (world_state.get('intervention_state') or {}).get('active_aftermath', [])
        history = (world_state.get('intervention_state') or {}).get('history', [])
        if not history and not active_entries:
            return {
                'district_pressure': 0.0,
                'resident_strain': 0.0,
                'household_strain': 0.0,
                'social_propagation': 0.0,
                'district_targets': {},
            }
        recent = history[-4:]
        weighted = 0.0
        total_weight = 0.0
        for idx, record in enumerate(reversed(recent), start=1):
            weight = 1.0 / idx
            delta = ((record.get('effects') or {}).get('delta_summary') or {})
            aftermath_profile = ((record.get('effects') or {}).get('aftermath_profile') or {})
            profile_amplitude = float(aftermath_profile.get('amplitude', 0.0))
            fade_per_tick = float(aftermath_profile.get('fade_per_tick', 0.12))
            decayed_profile = max(0.0, profile_amplitude * max(0.0, 1.0 - fade_per_tick * (idx - 1)))
            weighted += (
                abs(float(delta.get('household_pressure_index', 0.0))) * 0.42
                + abs(float(delta.get('service_access_score', 0.0))) * 0.34
                + abs(float(delta.get('employment_rate', 0.0))) * 0.24
                + decayed_profile * 0.5
            ) * weight
            total_weight += weight
        amplitude = min(1.0, weighted / max(total_weight, 1.0))
        targeted = {}
        for entry in active_entries[-16:]:
            if not isinstance(entry, dict):
                continue
            amplitude_entry = AuraliteRuntimeService._clamp_unit(float(entry.get('amplitude', 0.0)))
            district_id = entry.get('district_id')
            if district_id:
                targeted.setdefault(district_id, {
                    'district_pressure': 0.0,
                    'resident_strain': 0.0,
                    'household_strain': 0.0,
                })
                targeted[district_id]['district_pressure'] += amplitude_entry * 0.4
                targeted[district_id]['resident_strain'] += amplitude_entry * 0.35
                targeted[district_id]['household_strain'] += amplitude_entry * 0.38

        return {
            'district_pressure': round(amplitude * 0.8, 3),
            'resident_strain': round(amplitude * 0.65, 3),
            'household_strain': round(amplitude * 0.75, 3),
            'social_propagation': round(amplitude * 0.7, 3),
            'district_targets': {
                district_id: {
                    key: round(max(0.0, min(1.0, value)), 3)
                    for key, value in values.items()
                }
                for district_id, values in targeted.items()
            },
        }

    @staticmethod
    def _aftermath_for_district(aftermath: dict, district_id: str | None, metric: str) -> float:
        if not district_id:
            return float(aftermath.get(metric, 0.0))
        targeted = (aftermath.get('district_targets') or {}).get(district_id, {})
        return AuraliteRuntimeService._clamp_unit(
            float(aftermath.get(metric, 0.0)) * 0.4 + float(targeted.get(metric, 0.0)) * 0.6,
        )

    @staticmethod
    def _clamp_unit(value: float) -> float:
        return max(0.0, min(1.0, value))
