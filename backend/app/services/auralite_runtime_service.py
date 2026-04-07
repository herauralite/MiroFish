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
        persons_by_id = {p['person_id']: p for p in world_state.get('persons', [])}
        institutions_by_id = {i['institution_id']: i for i in world_state.get('institutions', [])}
        household_member_profiles = {}
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
            household_context = household.get('context') or {}
            household_shared_strain = float(household_context.get('stress_index', household.get('pressure_index', 0.0)))
            household_memory_fragility = float((household.get('adaptation_state') or {}).get('fragility_index', 0.0))
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
            failed_assistance_events = int(adaptation.get('failed_assistance_events', 0))
            instability_episodes = int(adaptation.get('instability_episodes', 0))
            stability_streak = int(adaptation.get('stability_streak', 0))
            support_erosion_index = float(adaptation.get('support_erosion_index', 0.0))
            resilience_reserve = float(adaptation.get('resilience_reserve', 0.0))
            recovery_debt = float(adaptation.get('recovery_debt', 0.0))
            fragility_index = float(adaptation.get('fragility_index', 0.0))
            scarcity_streak = scarcity_streak + 1 if person['state_summary']['service_scarcity'] >= 0.46 else max(0, scarcity_streak - 1)
            housing_streak = housing_streak + 1 if landlord_profile['housing_instability'] >= 0.46 else max(0, housing_streak - 1)
            commute_streak = commute_streak + 1 if transit_profile['commute_friction'] >= 0.42 else max(0, commute_streak - 1)
            job_streak = job_streak + 1 if employer_profile['job_quality_pressure'] >= 0.44 else max(0, job_streak - 1)
            support_buffer_streak = support_buffer_streak + 1 if service_profile['support_buffer'] >= 0.6 else max(0, support_buffer_streak - 1)
            failed_assistance_events = (
                min(24, failed_assistance_events + 1)
                if (
                    person['service_access_score'] <= 0.42
                    and (
                        service_profile['support_buffer'] <= 0.54
                        or person['state_summary']['service_scarcity'] >= 0.46
                    )
                )
                else max(0, failed_assistance_events - 1)
            )
            unstable_signal = (
                person['state_summary']['service_scarcity'] >= 0.48
                or person['state_summary']['job_quality_pressure'] >= 0.5
                or person['state_summary']['housing_instability_pressure'] >= 0.5
                or household_shared_strain >= 0.58
            )
            instability_episodes = instability_episodes + 1 if unstable_signal else max(0, instability_episodes - 1)
            stable_signal = (
                person['state_summary']['service_scarcity'] <= 0.24
                and person['state_summary']['job_quality_pressure'] <= 0.26
                and household_shared_strain <= 0.46
                and service_profile['support_buffer'] >= 0.52
            )
            stability_streak = min(36, stability_streak + 1) if stable_signal else max(0, stability_streak - 2)
            support_erosion_index = max(
                0.0,
                min(
                    1.0,
                    (support_erosion_index * 0.82)
                    + max(0.0, 0.54 - service_profile['support_buffer']) * 0.2
                    + max(0.0, 0.52 - person['service_access_score']) * 0.18
                    + max(0.0, household_memory_fragility - 0.5) * 0.12
                    - max(0.0, service_profile['support_buffer'] - 0.6) * 0.18,
                ),
            )
            adaptation_drag = (
                min(0.16, scarcity_streak * 0.012)
                + min(0.14, housing_streak * 0.011)
                + min(0.12, commute_streak * 0.009)
                + min(0.12, job_streak * 0.009)
                - min(0.15, support_buffer_streak * 0.012)
                + min(0.12, failed_assistance_events * 0.006)
                + min(0.14, instability_episodes * 0.005)
                + min(0.12, support_erosion_index * 0.22)
            )
            resilience_reserve = max(
                0.0,
                min(
                    1.0,
                    (resilience_reserve * 0.82)
                    + min(0.2, stability_streak * 0.008)
                    + min(0.16, support_buffer_streak * 0.007)
                    - max(0.0, adaptation_drag) * 0.18
                    - max(0.0, support_erosion_index - 0.4) * 0.12,
                ),
            )
            recovery_debt = max(
                0.0,
                min(
                    1.0,
                    (recovery_debt * 0.84)
                    + max(0.0, adaptation_drag) * 0.22
                    + min(0.14, failed_assistance_events * 0.004)
                    + max(0.0, household_shared_strain - 0.52) * 0.2
                    - max(0.0, resilience_reserve - 0.42) * 0.16,
                ),
            )
            fragility_index = max(
                0.0,
                min(
                    1.0,
                    (fragility_index * 0.76)
                    + max(0.0, support_erosion_index - 0.46) * 0.24
                    + max(0.0, recovery_debt - 0.4) * 0.26
                    + max(0.0, instability_episodes - 2) * 0.02
                    - max(0.0, resilience_reserve - 0.5) * 0.28,
                ),
            )
            service_responsiveness_drag = max(0.0, support_erosion_index * 0.12 + recovery_debt * 0.1 + fragility_index * 0.08)
            service_resilience_credit = max(0.0, resilience_reserve * 0.1 + min(0.08, stability_streak * 0.003))
            person['service_access_score'] = round(
                max(0.05, min(1.0, person['service_access_score'] - max(0.0, adaptation_drag * 0.36) - service_responsiveness_drag + service_resilience_credit)),
                3,
            )
            adaptation_support = max(0.0, min(0.2, support_buffer_streak * 0.01))
            person['state_summary']['adaptation_drag'] = round(adaptation_drag, 3)
            person['state_summary']['adaptation_support'] = round(adaptation_support, 3)
            person['state_summary']['support_erosion_index'] = round(support_erosion_index, 3)
            person['state_summary']['resilience_reserve'] = round(resilience_reserve, 3)
            person['state_summary']['recovery_debt'] = round(recovery_debt, 3)
            person['state_summary']['fragility_index'] = round(fragility_index, 3)
            adaptation.update({
                'service_scarcity_streak': scarcity_streak,
                'housing_instability_streak': housing_streak,
                'commute_friction_streak': commute_streak,
                'job_quality_streak': job_streak,
                'support_buffer_streak': support_buffer_streak,
                'adaptation_drag': round(adaptation_drag, 3),
                'adaptation_support': round(adaptation_support, 3),
                'failed_assistance_events': failed_assistance_events,
                'instability_episodes': instability_episodes,
                'stability_streak': stability_streak,
                'support_erosion_index': round(support_erosion_index, 3),
                'resilience_reserve': round(resilience_reserve, 3),
                'recovery_debt': round(recovery_debt, 3),
                'fragility_index': round(fragility_index, 3),
            })
            person['social_context'] = person.get('social_context', {})
            tie_dynamics = AuraliteRuntimeService._evolve_social_ties_for_person(
                person=person,
                persons_by_id=persons_by_id,
                household_shared_strain=household_shared_strain,
                fragility_index=fragility_index,
            )
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
                    + tie_dynamics['support_credit'] * 0.24,
                    - tie_dynamics['capacity_drag'] * 0.18,
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
                    + max(0.0, fragility_index * 0.2)
                    + tie_dynamics['strain_penalty'] * 0.2
                    - (support_index * 0.2),
                ),
            )
            person['social_context']['support_index'] = round(support_index, 3)
            person['social_context']['strain_index'] = round(strain_index, 3)
            person['social_context']['support_capacity_index'] = round(tie_dynamics['capacity_index'], 3)
            person['social_context']['relationship_usefulness_index'] = round(tie_dynamics['usefulness_index'], 3)
            person['social_context']['support_fatigue_index'] = round(tie_dynamics['fatigue_index'], 3)
            person['social_context']['failed_support_attempts'] = int(tie_dynamics['failed_attempts'])
            person['social_context']['tie_rebuild_readiness'] = round(tie_dynamics['rebuild_ready_share'], 3)
            person['state_summary']['social_support_index'] = round(support_index, 3)
            person['state_summary']['social_strain_index'] = round(strain_index, 3)
            person['state_summary']['support_capacity_index'] = round(tie_dynamics['capacity_index'], 3)
            person['state_summary']['relationship_usefulness_index'] = round(tie_dynamics['usefulness_index'], 3)
            person['state_summary']['support_fatigue_index'] = round(tie_dynamics['fatigue_index'], 3)
            person['state_summary']['tie_rebuild_readiness'] = round(tie_dynamics['rebuild_ready_share'], 3)

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
                    + max(0.0, fragility_index * 0.16)
                    + max(0.0, household_shared_strain - 0.56) * 0.12
                    - support_index * 0.16
                    - adaptation_support * 0.16
                    - min(0.08, resilience_reserve * 0.12)
                    + (0.16 if person.get('employment_status') != 'employed' else 0.0),
                ),
                3,
            )
            person['state_summary']['reversal_risk'] = round(
                max(
                    0.0,
                    min(
                        1.0,
                        (fragility_index * 0.46)
                        + max(0.0, recovery_debt - resilience_reserve) * 0.3
                        + max(0.0, household_shared_strain - 0.55) * 0.24
                        - min(0.2, stability_streak * 0.006),
                    ),
                ),
                3,
            )
            person['state_summary']['recovery_readiness'] = round(
                max(
                    0.0,
                    min(
                        1.0,
                        (resilience_reserve * 0.52)
                        + (person['service_access_score'] * 0.24)
                        + (support_index * 0.2)
                        - (fragility_index * 0.36)
                        - (recovery_debt * 0.28),
                    ),
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
            household_member_profiles.setdefault(person['household_id'], []).append({
                'person_id': person.get('person_id'),
                'fragility_index': fragility_index,
                'resilience_reserve': resilience_reserve,
                'recovery_debt': recovery_debt,
                'stress': float(person.get('state_summary', {}).get('stress', 0.0)),
                'support_fatigue_index': tie_dynamics['fatigue_index'],
            })

        AuraliteRuntimeService._update_households(
            world_state=world_state,
            household_service_access=household_service_access,
            household_employment=household_employment,
            household_social_support=household_social_support,
            household_job_quality=household_job_quality,
            household_commute_friction=household_commute_friction,
            household_housing_instability=household_housing_instability,
            household_member_profiles=household_member_profiles,
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
    def _evolve_social_ties_for_person(
        person: dict,
        persons_by_id: dict,
        household_shared_strain: float,
        fragility_index: float,
    ) -> dict:
        ties = person.get('social_ties', [])
        if not ties:
            return {
                'support_credit': 0.0,
                'strain_penalty': 0.0,
                'capacity_index': 0.0,
                'usefulness_index': 0.0,
                'fatigue_index': 0.0,
                'failed_attempts': 0,
            }
        demand = max(
            0.0,
            min(
                1.0,
                float((person.get('state_summary') or {}).get('stress', 0.0)) * 0.52
                + max(0.0, 0.56 - float(person.get('service_access_score', 0.5))) * 0.36
                + max(0.0, household_shared_strain - 0.52) * 0.24
                + max(0.0, fragility_index - 0.45) * 0.24,
            ),
        )
        support_credit = 0.0
        strain_penalty = 0.0
        capacity_sum = 0.0
        usefulness_sum = 0.0
        fatigue_sum = 0.0
        failed_attempts = 0
        rebuild_ready_count = 0
        for tie in ties:
            tie_type = tie.get('tie_type', 'district_local')
            baseline_usefulness = 0.64 if tie_type == 'household' else 0.56 if tie_type == 'coworker' else 0.5
            baseline_capacity = 0.68 if tie_type == 'household' else 0.58 if tie_type == 'coworker' else 0.5
            usefulness = float(tie.get('support_usefulness', baseline_usefulness))
            capacity = float(tie.get('support_capacity', baseline_capacity))
            fatigue = float(tie.get('support_fatigue', 0.12))
            failed_attempt_memory = float(tie.get('failed_support_memory', 0.0))
            low_strain_window = int(tie.get('low_strain_window_ticks', 0))
            tied = persons_by_id.get(tie.get('person_id'))
            tied_support = float((tied or {}).get('social_context', {}).get('support_index', 0.5))
            tied_stress = float((tied or {}).get('state_summary', {}).get('stress', 0.0))
            available = max(0.0, min(1.0, usefulness * capacity * (1.0 - fatigue * 0.9) * (0.58 + tied_support * 0.42)))
            mismatch = max(0.0, demand - available)
            low_strain_signal = demand <= 0.46 and tied_stress <= 0.56 and mismatch <= 0.12
            low_strain_window = min(12, low_strain_window + 1) if low_strain_signal else max(0, low_strain_window - 2)
            if mismatch >= 0.18:
                tie['failed_support_attempts'] = int(tie.get('failed_support_attempts', 0)) + 1
                tie['support_fatigue'] = round(min(1.0, fatigue * 0.8 + mismatch * 0.42 + max(0.0, tied_stress - 0.6) * 0.2 + min(0.14, failed_attempt_memory * 0.22)), 3)
                tie['support_usefulness'] = round(max(0.08, usefulness * 0.76 - mismatch * 0.15), 3)
                tie['support_capacity'] = round(max(0.08, capacity * 0.78 - mismatch * 0.16), 3)
                failed_attempts += 1
                tie['recovery_condition'] = 'erosion'
            else:
                tie['successful_support_ticks'] = int(tie.get('successful_support_ticks', 0)) + 1
                support_relief = max(0.0, available - demand)
                fatigue_decay = (
                    min(0.08, support_relief * 0.12 + low_strain_window * 0.01)
                    if low_strain_window >= 2 and demand <= 0.5
                    else min(0.03, support_relief * 0.06)
                )
                next_fatigue = max(0.0, fatigue * 0.88 - fatigue_decay)
                can_rebuild_usefulness = low_strain_window >= 2 and next_fatigue <= 0.56
                can_rebuild_capacity = (
                    low_strain_window >= 4
                    and next_fatigue <= 0.42
                    and demand <= 0.48
                    and failed_attempt_memory <= 0.54
                )
                tie['support_fatigue'] = round(next_fatigue, 3)
                tie['support_usefulness'] = round(
                    min(1.0, usefulness * 0.91 + (min(0.06, support_relief * 0.09) if can_rebuild_usefulness else 0.0)),
                    3,
                )
                tie['support_capacity'] = round(
                    min(1.0, capacity * 0.93 + (min(0.05, support_relief * 0.08) if can_rebuild_capacity else 0.0)),
                    3,
                )
                tie['recovery_condition'] = 'stabilizing' if can_rebuild_capacity else 'conditional_rebuild' if can_rebuild_usefulness else 'stalled_rebuild'
                if can_rebuild_usefulness:
                    rebuild_ready_count += 1
            failed_count = int(tie.get('failed_support_attempts', 0))
            if low_strain_window >= 4 and failed_count > 0 and mismatch < 0.12:
                tie['failed_support_attempts'] = max(0, failed_count - 1)
            tie['support_signal'] = round(available, 3)
            tie['strain_transfer_memory'] = round(
                max(
                    0.0,
                    min(
                        1.0,
                        float(tie.get('strain_transfer_memory', 0.0)) * 0.82
                        + mismatch * 0.24
                        + max(0.0, tied_stress - 0.58) * 0.18,
                    ),
                ),
                3,
            )
            failed_attempt_memory = max(
                0.0,
                min(
                    1.0,
                    failed_attempt_memory * 0.88
                    + min(0.18, int(tie.get('failed_support_attempts', 0)) * 0.018)
                    + mismatch * 0.2
                    - (0.05 if low_strain_window >= 5 and mismatch <= 0.08 else 0.0),
                ),
            )
            tie['failed_support_memory'] = round(failed_attempt_memory, 3)
            tie['low_strain_window_ticks'] = low_strain_window
            effective_signal = max(0.0, available - max(0.0, failed_attempt_memory - 0.36) * 0.24)
            support_credit += max(0.0, effective_signal - demand * 0.54)
            strain_penalty += mismatch + max(0.0, tie['strain_transfer_memory'] - 0.46) * 0.24
            capacity_sum += float(tie.get('support_capacity', capacity))
            usefulness_sum += float(tie.get('support_usefulness', usefulness))
            fatigue_sum += float(tie.get('support_fatigue', fatigue))
        tie_count = max(1, len(ties))
        capacity_index = capacity_sum / tie_count
        usefulness_index = usefulness_sum / tie_count
        fatigue_index = fatigue_sum / tie_count
        return {
            'support_credit': round(support_credit / tie_count, 3),
            'strain_penalty': round(strain_penalty / tie_count, 3),
            'capacity_drag': round(max(0.0, 0.56 - capacity_index), 3),
            'capacity_index': round(capacity_index, 3),
            'usefulness_index': round(usefulness_index, 3),
            'fatigue_index': round(fatigue_index, 3),
            'failed_attempts': int(failed_attempts),
            'rebuild_ready_share': round(rebuild_ready_count / tie_count, 3),
        }

    @staticmethod
    def _update_households(
        world_state: dict,
        household_service_access: dict,
        household_employment: dict,
        household_social_support: dict,
        household_job_quality: dict,
        household_commute_friction: dict,
        household_housing_instability: dict,
        household_member_profiles: dict,
        intervention_aftermath: dict,
    ):
        district_lookup = {d.get('district_id'): d for d in world_state.get('districts', [])}
        district_institution_queue_burden: dict[str, float] = {}
        for institution in world_state.get('institutions', []):
            district_id = institution.get('district_id')
            if not district_id:
                continue
            arc = institution.get('arc_state') or {}
            queue_burden = max(
                0.0,
                min(
                    1.0,
                    (float(arc.get('service_backlog', 0.0)) * 0.54)
                    + (float(arc.get('overload_fatigue', 0.0)) * 0.3)
                    + max(0.0, 0.58 - float(arc.get('responsiveness_index', 0.5))) * 0.24,
                ),
            )
            district_institution_queue_burden.setdefault(district_id, []).append(queue_burden)
        district_institution_queue_burden = {
            district_id: (sum(values) / max(1, len(values)))
            for district_id, values in district_institution_queue_burden.items()
        }
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
            failed_assistance_events = int(adaptation.get('failed_assistance_events', 0))
            instability_episodes = int(adaptation.get('instability_episodes', 0))
            stability_streak = int(adaptation.get('stability_streak', 0))
            support_erosion_index = float(adaptation.get('support_erosion_index', 0.0))
            resilience_reserve = float(adaptation.get('resilience_reserve', 0.0))
            recovery_debt = float(adaptation.get('recovery_debt', 0.0))
            fragility_index = float(adaptation.get('fragility_index', 0.0))
            asymmetry_persistence = float(adaptation.get('asymmetry_persistence', 0.0))
            queue_burden_streak = int(adaptation.get('institution_queue_burden_streak', 0))
            queue_relief_streak = int(adaptation.get('institution_queue_relief_streak', 0))
            queue_scar_memory = float(adaptation.get('institution_queue_scar_memory', 0.0))
            service_rebound_reserve = float(adaptation.get('service_rebound_reserve', 0.0))
            durable_relief_streak = int(adaptation.get('durable_relief_streak', 0))
            relief_interruption_count = int(adaptation.get('relief_interruption_count', 0))
            nominal_relief_lag = float(adaptation.get('nominal_relief_lag', 0.0))
            assistance_trust_index = float(adaptation.get('assistance_trust_index', 0.5))
            responsiveness_memory = float(adaptation.get('responsiveness_memory', 0.0))
            scarcity_streak = scarcity_streak + 1 if service_access <= 0.5 else max(0, scarcity_streak - 1)
            housing_streak = housing_streak + 1 if housing_instability_pressure >= 0.45 else max(0, housing_streak - 1)
            commute_streak = commute_streak + 1 if commute_friction >= 0.42 else max(0, commute_streak - 1)
            job_streak = job_streak + 1 if job_quality_pressure >= 0.4 else max(0, job_streak - 1)
            support_streak = support_streak + 1 if social_support >= 0.58 else max(0, support_streak - 1)
            failed_assistance_events = (
                min(20, failed_assistance_events + 1)
                if service_access <= 0.46 and social_support <= 0.5
                else max(0, failed_assistance_events - 1)
            )
            unstable_signal = (
                service_access <= 0.48
                or housing_instability_pressure >= 0.48
                or job_quality_pressure >= 0.46
                or pressure >= 0.62
            )
            instability_episodes = min(24, instability_episodes + 1) if unstable_signal else max(0, instability_episodes - 1)
            stable_signal = (
                service_access >= 0.58
                and social_support >= 0.56
                and job_quality_pressure <= 0.28
                and housing_instability_pressure <= 0.3
            )
            stability_streak = min(36, stability_streak + 1) if stable_signal else max(0, stability_streak - 2)
            support_erosion_index = max(
                0.0,
                min(
                    1.0,
                    (support_erosion_index * 0.84)
                    + max(0.0, 0.54 - social_support) * 0.24
                    + max(0.0, 0.52 - service_access) * 0.16
                    - max(0.0, social_support - 0.62) * 0.18,
                ),
            )
            household_adaptation_drag = (
                min(0.2, scarcity_streak * 0.014)
                + min(0.2, housing_streak * 0.013)
                + min(0.14, commute_streak * 0.009)
                + min(0.14, job_streak * 0.01)
                - min(0.18, support_streak * 0.012)
                + min(0.14, failed_assistance_events * 0.007)
                + min(0.1, support_erosion_index * 0.22)
            )
            resilience_reserve = max(
                0.0,
                min(
                    1.0,
                    (resilience_reserve * 0.82)
                    + min(0.24, stability_streak * 0.009)
                    + min(0.16, support_streak * 0.008)
                    - max(0.0, household_adaptation_drag) * 0.16
                    - max(0.0, support_erosion_index - 0.45) * 0.14,
                ),
            )
            recovery_debt = max(
                0.0,
                min(
                    1.0,
                    (recovery_debt * 0.84)
                    + max(0.0, household_adaptation_drag) * 0.24
                    + max(0.0, pressure - 0.54) * 0.18
                    + min(0.12, failed_assistance_events * 0.005)
                    - max(0.0, resilience_reserve - 0.46) * 0.2,
                ),
            )
            fragility_index = max(
                0.0,
                min(
                    1.0,
                    (fragility_index * 0.78)
                    + max(0.0, support_erosion_index - 0.44) * 0.24
                    + max(0.0, recovery_debt - 0.42) * 0.28
                    + max(0.0, instability_episodes - 3) * 0.018
                    - max(0.0, resilience_reserve - 0.5) * 0.26,
                ),
            )
            institution_queue_burden = float(
                district_institution_queue_burden.get(household.get('district_id'), 0.0)
            )
            prior_queue_relief_streak = queue_relief_streak
            queue_burden_streak = (
                min(28, queue_burden_streak + 1)
                if institution_queue_burden >= 0.42
                else max(0, queue_burden_streak - 2)
            )
            queue_relief_streak = (
                min(28, queue_relief_streak + 1)
                if institution_queue_burden <= 0.26 and service_access >= 0.56
                else max(0, queue_relief_streak - 1)
            )
            queue_scar_memory = max(
                0.0,
                min(
                    1.0,
                    (queue_scar_memory * 0.88)
                    + min(0.22, queue_burden_streak * 0.012)
                    + max(0.0, institution_queue_burden - 0.34) * 0.24
                    + max(0.0, pressure - 0.58) * 0.14
                    - min(0.18, queue_relief_streak * 0.01)
                    - max(0.0, service_access - 0.64) * 0.12,
                ),
            )
            service_rebound_reserve = max(
                0.0,
                min(
                    1.0,
                    (service_rebound_reserve * 0.84)
                    + min(0.2, queue_relief_streak * 0.01)
                    + max(0.0, social_support - 0.58) * 0.14
                    + max(0.0, resilience_reserve - 0.52) * 0.14
                    - max(0.0, queue_scar_memory - 0.36) * 0.2
                    - max(0.0, institution_queue_burden - 0.38) * 0.24,
                ),
            )
            nominal_relief_signal = (
                service_access >= 0.56
                and institution_queue_burden <= 0.34
                and float((household.get('context') or {}).get('stress_index', pressure)) <= 0.62
            )
            durable_relief_signal = (
                nominal_relief_signal
                and queue_scar_memory <= 0.46
                and social_support >= 0.56
                and recovery_debt <= 0.58
            )
            interrupted_relief = (
                prior_queue_relief_streak >= 2
                and queue_relief_streak <= 1
                and institution_queue_burden >= 0.36
            )
            relief_interruption_count = min(24, relief_interruption_count + 1) if interrupted_relief else max(0, relief_interruption_count - 1)
            durable_relief_streak = (
                min(36, durable_relief_streak + 1)
                if durable_relief_signal
                else max(0, durable_relief_streak - (2 if interrupted_relief else 1))
            )
            nominal_relief_lag = max(
                0.0,
                min(
                    1.0,
                    (nominal_relief_lag * 0.82)
                    + (0.06 if nominal_relief_signal and not durable_relief_signal else 0.0)
                    + min(0.14, relief_interruption_count * 0.01)
                    + max(0.0, queue_scar_memory - 0.34) * 0.2
                    + max(0.0, recovery_debt - 0.5) * 0.18
                    - min(0.16, durable_relief_streak * 0.012)
                    - max(0.0, service_rebound_reserve - 0.42) * 0.14,
                ),
            )
            assistance_trust_index = max(
                0.0,
                min(
                    1.0,
                    (assistance_trust_index * 0.86)
                    + (0.012 if durable_relief_signal else 0.0)
                    + (0.008 if stable_signal else 0.0)
                    - min(0.08, failed_assistance_events * 0.003)
                    - min(0.08, relief_interruption_count * 0.004)
                    - max(0.0, nominal_relief_lag - 0.28) * 0.16
                    - max(0.0, queue_scar_memory - 0.34) * 0.14,
                ),
            )
            responsiveness_memory = max(
                0.0,
                min(
                    1.0,
                    (responsiveness_memory * 0.82)
                    + max(0.0, 0.54 - assistance_trust_index) * 0.28
                    + max(0.0, queue_scar_memory - 0.34) * 0.22
                    + max(0.0, nominal_relief_lag - 0.26) * 0.18
                    - (0.03 if stable_signal and assistance_trust_index >= 0.54 else 0.0),
                ),
            )
            service_rebound_reserve = max(
                0.0,
                min(
                    1.0,
                    service_rebound_reserve
                    - max(0.0, nominal_relief_lag - 0.28) * 0.22
                    - min(0.08, relief_interruption_count * 0.006),
                ),
            )

            housing_instability = min(
                1.0,
                (rent_share * 0.62) + (pressure * 0.34) + (household.get('eviction_risk', 0.0) * 0.32) + (housing_instability_pressure * 0.3),
            )
            member_profiles = household_member_profiles.get(hh_id, [])
            fragile_member_share = (
                sum(1 for row in member_profiles if float(row.get('fragility_index', 0.0)) >= 0.56)
                / max(1, len(member_profiles))
            )
            buffered_member_share = (
                sum(
                    1
                    for row in member_profiles
                    if float(row.get('resilience_reserve', 0.0)) >= 0.52
                    and float(row.get('recovery_debt', 0.0)) <= 0.5
                )
                / max(1, len(member_profiles))
            )
            member_support_fatigue = (
                sum(float(row.get('support_fatigue_index', 0.0)) for row in member_profiles)
                / max(1, len(member_profiles))
            )
            buffered_effective_share = buffered_member_share * max(0.0, 1.0 - max(0.0, member_support_fatigue - 0.34) * 1.6)
            asymmetry_strain = max(
                0.0,
                min(
                    1.0,
                    (fragile_member_share * 0.62)
                    + max(0.0, member_support_fatigue - 0.36) * 0.45
                    + max(0.0, asymmetry_persistence - 0.32) * 0.32
                    - (buffered_effective_share * 0.34),
                ),
            )
            asymmetry_persistence = max(
                0.0,
                min(
                    1.0,
                    (asymmetry_persistence * 0.88)
                    + max(0.0, asymmetry_strain - 0.44) * 0.28
                    + max(0.0, member_support_fatigue - 0.42) * 0.22
                    - (0.03 if stable_signal and member_support_fatigue <= 0.36 else 0.0),
                ),
            )
            asymmetry_drag = max(0.0, asymmetry_persistence - 0.36)
            stable_recovery_window = stability_streak >= 4 and member_support_fatigue <= 0.42 and asymmetry_persistence <= 0.5
            resilience_reserve = max(
                0.0,
                min(
                    1.0,
                    resilience_reserve
                    - min(0.08, asymmetry_drag * 0.14)
                    + (0.018 if stable_recovery_window else 0.0),
                ),
            )
            recovery_debt = max(
                0.0,
                min(
                    1.0,
                    recovery_debt
                    + min(0.12, asymmetry_drag * 0.18)
                    + max(0.0, queue_scar_memory - 0.34) * 0.14
                    + max(0.0, nominal_relief_lag - 0.26) * 0.16
                    - (0.015 if stable_recovery_window else 0.0),
                ),
            )
            fragility_index = max(
                0.0,
                min(
                    1.0,
                    fragility_index
                    + min(0.12, asymmetry_drag * 0.2)
                    - (0.012 if stable_recovery_window else 0.0),
                ),
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
                + (asymmetry_strain * 0.18),
                + min(0.12, asymmetry_drag * 0.2),
                + (intervention_aftermath.get('household_strain', 0.0) * 0.08),
                + (district_shock * 0.14),
                + max(0.0, institution_queue_burden - 0.34) * 0.18,
                + max(0.0, queue_scar_memory - 0.38) * 0.14,
                + max(0.0, nominal_relief_lag - 0.3) * 0.18,
                + max(0.0, responsiveness_memory - 0.36) * 0.14,
                + max(0.0, 0.5 - assistance_trust_index) * 0.16,
            )
            household_hardship_index = min(
                1.0,
                (housing_instability * 0.36)
                + (employment_instability * 0.24)
                + (job_quality_pressure * 0.16)
                + ((1.0 - service_access) * 0.14)
                + (commute_friction * 0.1)
                + max(0.0, household_adaptation_drag * 0.18)
                + max(0.0, fragility_index * 0.2)
                + max(0.0, asymmetry_strain * 0.14)
                + min(0.1, asymmetry_drag * 0.16)
                + (district_shock * 0.08)
                + max(0.0, institution_queue_burden - 0.3) * 0.2
                + max(0.0, queue_scar_memory - 0.34) * 0.16
                + max(0.0, responsiveness_memory - 0.34) * 0.14
                + max(0.0, 0.48 - assistance_trust_index) * 0.16
                - (social_support * 0.12)
                - min(0.08, resilience_reserve * 0.12),
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
                    + min(0.1, asymmetry_drag * 0.2)
                    + max(0.0, institution_queue_burden - 0.34) * 0.16
                    + max(0.0, queue_scar_memory - 0.36) * 0.16
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
                        + (asymmetry_strain * 0.15)
                        + ((1.0 - social_support) * 0.17),
                    ),
                    3,
                ),
                'support_fatigue_index': round(
                    max(
                        0.0,
                        min(
                            1.0,
                            (float(household['social_context'].get('support_fatigue_index', member_support_fatigue)) * 0.62)
                            + (member_support_fatigue * 0.38)
                            - (0.02 if stable_recovery_window else 0.0),
                        ),
                    ),
                    3,
                ),
                'durable_recovery_window': bool(stable_recovery_window),
                'assistance_trust_index': round(assistance_trust_index, 3),
                'responsiveness_memory': round(responsiveness_memory, 3),
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
                'institution_queue_burden': round(institution_queue_burden, 3),
                'institution_queue_scar_memory': round(queue_scar_memory, 3),
                'service_rebound_reserve': round(service_rebound_reserve, 3),
                'durable_relief_streak': durable_relief_streak,
                'relief_interruption_count': relief_interruption_count,
                'nominal_relief_lag': round(nominal_relief_lag, 3),
                'assistance_trust_index': round(assistance_trust_index, 3),
                'responsiveness_memory': round(responsiveness_memory, 3),
                'institution_queue_burden_streak': queue_burden_streak,
                'institution_queue_relief_streak': queue_relief_streak,
                'support_erosion_index': round(support_erosion_index, 3),
                'resilience_reserve': round(resilience_reserve, 3),
                'recovery_debt': round(recovery_debt, 3),
                'fragility_index': round(fragility_index, 3),
                'fragile_member_share': round(fragile_member_share, 3),
                'buffered_member_share': round(buffered_member_share, 3),
                'buffered_effective_share': round(buffered_effective_share, 3),
                'member_support_fatigue': round(member_support_fatigue, 3),
                'asymmetry_strain_index': round(asymmetry_strain, 3),
                'asymmetry_persistence': round(asymmetry_persistence, 3),
                'durable_recovery_window': bool(stable_recovery_window),
            })
            adaptation.update({
                'service_scarcity_streak': scarcity_streak,
                'housing_instability_streak': housing_streak,
                'commute_friction_streak': commute_streak,
                'job_quality_streak': job_streak,
                'support_buffer_streak': support_streak,
                'adaptation_drag': round(household_adaptation_drag, 3),
                'hardship_cluster_weight': round(hardship_cluster_weight, 3),
                'failed_assistance_events': failed_assistance_events,
                'instability_episodes': instability_episodes,
                'stability_streak': stability_streak,
                'support_erosion_index': round(support_erosion_index, 3),
                'resilience_reserve': round(resilience_reserve, 3),
                'recovery_debt': round(recovery_debt, 3),
                'fragility_index': round(fragility_index, 3),
                'asymmetry_persistence': round(asymmetry_persistence, 3),
                'institution_queue_burden_streak': queue_burden_streak,
                'institution_queue_relief_streak': queue_relief_streak,
                'institution_queue_scar_memory': round(queue_scar_memory, 3),
                'service_rebound_reserve': round(service_rebound_reserve, 3),
                'durable_relief_streak': durable_relief_streak,
                'relief_interruption_count': relief_interruption_count,
                'nominal_relief_lag': round(nominal_relief_lag, 3),
                'assistance_trust_index': round(assistance_trust_index, 3),
                'responsiveness_memory': round(responsiveness_memory, 3),
                'durable_recovery_window': bool(stable_recovery_window),
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
            backlog = float(arc.get('service_backlog', max(0.0, utilization - 0.86)))
            overload_streak = int(arc.get('overload_streak', 0))
            responsiveness = float(arc.get('responsiveness_index', 0.5))
            clearance_momentum = float(arc.get('clearance_momentum', 0.0))
            overload_fatigue = float(arc.get('overload_fatigue', 0.0))
            partial_recovery_index = float(arc.get('partial_recovery_index', 0.0))
            recovery_gate_index = float(arc.get('recovery_gate_index', 0.5))
            sustained_relief_streak = int(arc.get('sustained_relief_streak', 0))
            backlog_relapse_events = int(arc.get('backlog_relapse_events', 0))
            recovery_lag_memory = float(arc.get('recovery_lag_memory', 0.0))
            if pressure_delta >= 0.01:
                stress_streak += 1
                recovery_streak = max(0, recovery_streak - 1)
            elif pressure_delta <= -0.01:
                recovery_streak += 1
                stress_streak = max(0, stress_streak - 1)
            else:
                stress_streak = max(0, stress_streak - 1)
                recovery_streak = max(0, recovery_streak - 1)
            overload_streak = overload_streak + 1 if utilization >= 1.0 else max(0, overload_streak - 1)
            overload_fatigue = max(
                0.0,
                min(
                    1.0,
                    (overload_fatigue * 0.84)
                    + overload * 0.28
                    + max(0.0, utilization - 0.95) * 0.24
                    + max(0.0, overload_streak - 2) * 0.03
                    - (0.04 if recovery_streak >= 3 else 0.0),
                ),
            )
            recovery_gate_index = max(
                0.0,
                min(
                    1.0,
                    (recovery_gate_index * 0.78)
                    + max(0.0, next_access - 0.56) * 0.24
                    + max(0.0, 0.64 - next_pressure) * 0.2
                    + (0.05 if recovery_streak >= 3 else 0.0)
                    - max(0.0, overload_fatigue - 0.4) * 0.24
                    - max(0.0, district_pressure - 0.58) * 0.1,
                ),
            )
            recovery_prerequisites_met = (
                recovery_gate_index >= 0.44
                and overload_fatigue <= 0.62
                and district_pressure <= 0.72
                and backlog <= 0.54
                and sustained_relief_streak >= 2
            )
            clearance_momentum = max(
                0.0,
                min(
                    1.0,
                    (clearance_momentum * 0.72)
                    + (0.08 if recovery_prerequisites_met else 0.0)
                    + max(0.0, next_access - 0.58) * 0.2
                    - max(0.0, overload_fatigue - 0.44) * 0.3
                    - max(0.0, utilization - 0.96) * 0.18,
                ),
            )
            backlog = max(
                0.0,
                min(
                    1.0,
                    (backlog * 0.78)
                    + max(0.0, utilization - 0.84) * 0.42
                    + overload * 0.45
                    + max(0.0, district_pressure - 0.56) * 0.16
                    - max(0.0, next_access - 0.62) * 0.22
                    - (clearance_momentum * 0.26)
                    - (0.05 if recovery_streak >= 3 and recovery_prerequisites_met else 0.0),
                ),
            )
            if backlog <= 0.46 and overload_fatigue <= 0.56 and next_access >= 0.56:
                sustained_relief_streak = min(28, sustained_relief_streak + 1)
            else:
                sustained_relief_streak = max(0, sustained_relief_streak - 1)
            relapse_trigger = backlog >= 0.52 and sustained_relief_streak >= 2
            backlog_relapse_events = min(24, backlog_relapse_events + 1) if relapse_trigger else max(0, backlog_relapse_events - 1)
            recovery_lag_memory = max(
                0.0,
                min(
                    1.0,
                    (recovery_lag_memory * 0.82)
                    + (0.06 if next_access >= 0.56 and backlog >= 0.48 else 0.0)
                    + min(0.18, backlog_relapse_events * 0.012)
                    + max(0.0, overload_fatigue - 0.42) * 0.2
                    - min(0.16, sustained_relief_streak * 0.014),
                ),
            )
            partial_recovery_index = max(
                0.0,
                min(
                    1.0,
                    (partial_recovery_index * 0.8)
                    + max(0.0, next_access - 0.54) * 0.22
                    + max(0.0, 0.6 - next_pressure) * 0.2
                    + (0.04 if recovery_prerequisites_met else 0.0)
                    - max(0.0, backlog - 0.36) * 0.24
                    - max(0.0, overload_fatigue - 0.46) * 0.22,
                    - max(0.0, recovery_lag_memory - 0.3) * 0.2,
                ),
            )
            responsiveness = max(
                0.05,
                min(
                    1.0,
                    (responsiveness * 0.74)
                    + max(0.0, next_access - 0.5) * 0.24
                    + (0.06 if recovery_streak >= 2 and recovery_prerequisites_met else 0.0)
                    + partial_recovery_index * 0.08
                    - max(0.0, backlog - 0.45) * 0.32
                    - max(0.0, overload_streak - 2) * 0.03,
                    - max(0.0, overload_fatigue - 0.4) * 0.24,
                    - max(0.0, recovery_lag_memory - 0.3) * 0.2,
                ),
            )
            institution['pressure_index'] = round(next_pressure, 3)
            institution['access_score'] = round(next_access, 3)
            institution['arc_state'] = {
                'effective_pressure': round(next_pressure, 3),
                'effective_access': round(next_access, 3),
                'pressure_delta': round(pressure_delta, 3),
                'stress_streak': stress_streak,
                'recovery_streak': recovery_streak,
                'overload_streak': overload_streak,
                'utilization': round(utilization, 3),
                'utilization_pressure': round(overload, 3),
                'service_backlog': round(backlog, 3),
                'responsiveness_index': round(responsiveness, 3),
                'clearance_momentum': round(clearance_momentum, 3),
                'overload_fatigue': round(overload_fatigue, 3),
                'partial_recovery_index': round(partial_recovery_index, 3),
                'recovery_gate_index': round(recovery_gate_index, 3),
                'recovery_prerequisites_met': bool(recovery_prerequisites_met),
                'sustained_relief_streak': sustained_relief_streak,
                'backlog_relapse_events': backlog_relapse_events,
                'recovery_lag_memory': round(recovery_lag_memory, 3),
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
            district_social_fatigue = (
                sum(float((p.get('social_context') or {}).get('support_fatigue_index', 0.0)) for p in residents)
                / resident_count
            )
            district_relationship_usefulness = (
                sum(float((p.get('social_context') or {}).get('relationship_usefulness_index', 0.0)) for p in residents)
                / resident_count
            )
            district_household_asymmetry = (
                sum(float((h.get('context') or {}).get('asymmetry_strain_index', 0.0)) for h in district_households)
                / max(1, len(district_households))
            )
            district_support_erosion = (
                sum(float((h.get('adaptation_state') or {}).get('support_erosion_index', 0.0)) for h in district_households)
                / max(1, len(district_households))
            )
            district_asymmetry_persistence = (
                sum(float((h.get('context') or {}).get('asymmetry_persistence', 0.0)) for h in district_households)
                / max(1, len(district_households))
            )
            district_recovery_debt = (
                sum(float((h.get('adaptation_state') or {}).get('recovery_debt', 0.0)) for h in district_households)
                / max(1, len(district_households))
            )
            network_fragility = max(
                0.0,
                min(
                    1.0,
                    (district_social_fatigue * 0.32)
                    + max(0.0, 0.56 - district_relationship_usefulness) * 0.44
                    + (district_household_asymmetry * 0.22)
                    + (district_support_erosion * 0.24),
                ),
            )
            network_resilience = max(
                0.0,
                min(
                    1.0,
                    (district_relationship_usefulness * 0.38)
                    + max(0.0, 1.0 - district_social_fatigue) * 0.26
                    + max(0.0, 1.0 - district_household_asymmetry) * 0.18
                    + max(0.0, 1.0 - district_support_erosion) * 0.18,
                ),
            )
            district_aftershock = AuraliteRuntimeService._aftermath_for_district(
                intervention_aftermath,
                district_id,
                'district_pressure',
            )
            average_service_backlog = (
                sum(float((inst.get('arc_state') or {}).get('service_backlog', 0.0)) for inst in district_institutions)
                / max(1, len(district_institutions))
            )
            responsiveness_drag = (
                sum(max(0.0, 0.62 - float((inst.get('arc_state') or {}).get('responsiveness_index', 0.5))) for inst in district_institutions)
                / max(1, len(district_institutions))
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
                + max(0.0, average_service_backlog - 0.35) * 0.18
                + max(0.0, responsiveness_drag - 0.06) * 0.2
                + max(0.0, network_fragility - 0.42) * 0.24
                + max(0.0, district_asymmetry_persistence - 0.46) * 0.16
                + max(0.0, district_recovery_debt - 0.44) * 0.12
                - min(0.08, institution_buffer * 0.1),
                - min(0.08, network_resilience * 0.1),
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
            fragile_recovery_memory = float(arc_state.get('fragile_recovery_memory', 0.0))
            prior_shallow_recovery_risk = float(arc_state.get('shallow_recovery_risk', 0.0))
            durable_support_ticks = int(arc_state.get('durable_support_ticks', 0))
            topology_drag_memory = float(arc_state.get('topology_drag_memory', 0.0))
            topology_support_memory = float(arc_state.get('topology_support_memory', 0.0))
            spillover_scar_memory = float(arc_state.get('spillover_scar_memory', 0.0))
            containment_capacity = float(arc_state.get('containment_capacity', 0.5))
            ripple_context = ((district.get('derived_summary') or {}).get('ripple_context') or {})
            stressed_cluster_share = float(ripple_context.get('stressed_cluster_share', 0.0))
            recovery_cluster_share = float(ripple_context.get('recovery_cluster_share', 0.0))
            cluster_amplification = float(ripple_context.get('cluster_amplification', 0.0))
            containment_weakness = float(ripple_context.get('containment_weakness', 0.0))
            neighborhood_cluster_drag = max(
                0.0,
                min(
                    1.0,
                    (stressed_cluster_share * 0.56)
                    + max(0.0, cluster_amplification - 0.1) * 0.34
                    - (recovery_cluster_share * 0.24),
                ),
            )
            topology_drag_pressure = max(
                0.0,
                min(
                    1.0,
                    (stressed_cluster_share * 0.62)
                    + max(0.0, cluster_amplification - 0.08) * 0.28
                    - (recovery_cluster_share * 0.2),
                ),
            )
            spillover_scar_memory = max(
                0.0,
                min(
                    1.0,
                    (spillover_scar_memory * 0.88)
                    + max(0.0, neighborhood_cluster_drag - 0.42) * 0.2
                    + max(0.0, containment_weakness - 0.44) * 0.16
                    + max(0.0, topology_drag_pressure - 0.46) * 0.14
                    + (0.03 if sustained_pressure_ticks >= 3 else 0.0)
                    - max(0.0, recovery_cluster_share - 0.4) * 0.1,
                ),
            )
            topology_support_pressure = max(
                0.0,
                min(
                    1.0,
                    (recovery_cluster_share * 0.58)
                    + max(0.0, 0.42 - cluster_amplification) * 0.16
                    - (stressed_cluster_share * 0.22),
                ),
            )
            topology_drag_memory = max(
                0.0,
                min(
                    1.0,
                    (topology_drag_memory * 0.86)
                    + (topology_drag_pressure * 0.14),
                ),
            )
            topology_support_memory = max(
                0.0,
                min(
                    1.0,
                    (topology_support_memory * 0.84)
                    + (topology_support_pressure * 0.16),
                ),
            )
            containment_capacity = max(
                0.0,
                min(
                    1.0,
                    (containment_capacity * 0.84)
                    + max(0.0, topology_support_memory - 0.46) * 0.22
                    + max(0.0, recovery_cluster_share - 0.34) * 0.12
                    + max(0.0, 0.12 - containment_weakness) * 0.12
                    - max(0.0, containment_weakness - 0.44) * 0.22
                    - max(0.0, neighborhood_cluster_drag - 0.46) * 0.2
                    - max(0.0, spillover_scar_memory - 0.46) * 0.22,
                ),
            )
            topology_memory_drag = max(0.0, topology_drag_memory - (topology_support_memory * 0.72))
            topology_relapse_bias = max(
                0.0,
                min(
                    1.0,
                    (topology_memory_drag * 0.72)
                    + max(0.0, neighborhood_cluster_drag - 0.42) * 0.24
                    + max(0.0, fragile_recovery_memory - 0.5) * 0.2,
                ),
            )
            topology_support_alignment = max(
                0.0,
                min(
                    1.0,
                    (topology_support_memory * 0.62)
                    + (recovery_cluster_share * 0.24)
                    + max(0.0, 0.62 - topology_drag_memory) * 0.12
                    - max(0.0, topology_memory_drag - 0.2) * 0.24,
                ),
            )
            support_alignment_gap = max(0.0, topology_support_alignment - topology_relapse_bias)
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
                + min(0.12, network_resilience * 0.14)
                - min(0.12, max(0.0, institution_drift) * 0.16)
                - min(0.12, hardship_cluster * 0.1)
                - min(0.12, network_fragility * 0.12)
                - min(0.1, max(0.0, average_service_backlog - 0.34) * 0.24)
                - min(0.1, district_asymmetry_persistence * 0.14)
                - min(0.1, topology_memory_drag * 0.16)
            )
            cumulative_stress_load = max(
                0.0,
                min(
                    1.0,
                    (cumulative_stress_load * 0.84)
                    + max(0.0, pressure_index - 0.54) * 0.22
                    + max(0.0, hardship_cluster - 0.52) * 0.2
                    + max(0.0, institution_drift) * 0.18
                    + max(0.0, network_fragility - 0.46) * 0.22
                    + max(0.0, district_recovery_debt - 0.44) * 0.18
                    + max(0.0, average_service_backlog - 0.38) * 0.14
                    + max(0.0, neighborhood_cluster_drag - 0.44) * 0.12
                    + max(0.0, topology_memory_drag - 0.2) * 0.12
                    + (0.03 if sustained_pressure_ticks >= 3 else 0.0)
                    - min(0.06, local_recovery_context * 0.06),
                ),
            )
            recovery_gate = max(
                0.0,
                min(
                    1.0,
                    (1.0 - max(0.0, pressure_index - 0.5)) * 0.24
                    + (1.0 - max(0.0, cumulative_stress_load - 0.5)) * 0.16
                    + max(0.0, network_resilience - 0.48) * 0.3
                    - max(0.0, network_fragility - 0.48) * 0.24
                    - max(0.0, average_service_backlog - 0.34) * 0.26
                    - max(0.0, responsiveness_drag - 0.05) * 0.3
                    - max(0.0, district_asymmetry_persistence - 0.42) * 0.22
                    - max(0.0, district_recovery_debt - 0.42) * 0.2
                    - max(0.0, neighborhood_cluster_drag - 0.46) * 0.12
                    - max(0.0, topology_memory_drag - 0.24) * 0.14
                    + (0.08 if sustained_recovery_ticks >= 5 else 0.0),
                ),
            )
            if (
                recovery_gate >= 0.5
                and local_recovery_context >= 0.48
                and cumulative_stress_load <= 0.64
                and fragile_recovery_memory <= 0.6
                and neighborhood_cluster_drag <= 0.6
                and topology_memory_drag <= 0.52
            ):
                support_tick_gain = (
                    1
                    if (
                        neighborhood_cluster_drag <= 0.44
                        and topology_memory_drag <= 0.38
                        and topology_support_alignment >= 0.42
                        and support_alignment_gap >= 0.06
                    )
                    else 0
                )
                durable_support_ticks = min(12, durable_support_ticks + support_tick_gain)
            else:
                durable_support_ticks = max(
                    0,
                    durable_support_ticks - (
                        3
                        if (
                            topology_relapse_bias >= 0.52
                            or neighborhood_cluster_drag >= 0.6
                            or topology_memory_drag >= 0.54
                        )
                        else 2
                        if (
                            fragile_recovery_memory >= 0.58
                            or cumulative_stress_load >= 0.62
                            or neighborhood_cluster_drag >= 0.56
                            or topology_memory_drag >= 0.48
                        )
                        else 1
                    ),
                )
            if support_alignment_gap < 0.02:
                durable_support_ticks = max(0, durable_support_ticks - 1)
            if topology_relapse_bias >= 0.48 and durable_support_ticks <= 4:
                durable_support_ticks = max(0, durable_support_ticks - 1)
            fragile_recovery_floor = min(
                0.35,
                max(0.0, cumulative_stress_load - 0.34) * 0.18
                + max(0.0, average_service_backlog - 0.2) * 0.14
                + max(0.0, district_recovery_debt - 0.3) * 0.12,
            )
            fragile_recovery_memory = max(
                fragile_recovery_floor,
                min(
                    1.0,
                    (fragile_recovery_memory * 0.86)
                    + max(0.0, cumulative_stress_load - 0.5) * 0.2
                    + max(0.0, network_fragility - 0.46) * 0.18
                    + max(0.0, average_service_backlog - 0.36) * 0.15
                    + max(0.0, district_recovery_debt - 0.4) * 0.14
                    + max(0.0, prior_shallow_recovery_risk - 0.46) * 0.24
                    + max(0.0, neighborhood_cluster_drag - 0.42) * 0.16
                    + max(0.0, topology_memory_drag - 0.18) * 0.16
                    + max(0.0, topology_relapse_bias - 0.42) * 0.14
                    - max(0.0, recovery_gate - 0.56) * 0.1
                    - max(0.0, support_alignment_gap - 0.08) * 0.08
                    - (0.02 if durable_support_ticks >= 6 and local_recovery_context >= 0.56 and recovery_cluster_share >= 0.34 else 0.0),
                ),
            )
            recovery_durability = max(
                0.0,
                min(
                    1.0,
                    (recovery_durability * 0.84)
                    + max(0.0, local_recovery_context - 0.54) * 0.13
                    + max(0.0, recovery_gate - 0.56) * 0.18
                    + (0.016 if sustained_recovery_ticks >= 6 and recovery_gate >= 0.56 else 0.0)
                    + (
                        0.02
                        if (
                            durable_support_ticks >= 8
                            and fragile_recovery_memory <= 0.46
                            and neighborhood_cluster_drag <= 0.44
                            and topology_memory_drag <= 0.34
                            and support_alignment_gap >= 0.1
                        )
                        else 0.0
                    )
                    + (0.016 if durable_support_ticks >= 10 and support_alignment_gap >= 0.12 else 0.0)
                    + max(0.0, topology_support_alignment - 0.52) * 0.08
                    - max(0.0, pressure_index - 0.55) * 0.18
                    - max(0.0, hardship_cluster - 0.56) * 0.14
                    - max(0.0, cumulative_stress_load - 0.56) * 0.14,
                    - max(0.0, fragile_recovery_memory - 0.44) * 0.24
                    - max(0.0, neighborhood_cluster_drag - 0.4) * 0.2
                    - max(0.0, topology_memory_drag - 0.22) * 0.22
                    - max(0.0, topology_relapse_bias - 0.44) * 0.12
                    - max(0.0, 0.08 - support_alignment_gap) * 0.2
                    + max(0.0, network_resilience - 0.5) * 0.14
                    - max(0.0, network_fragility - 0.5) * 0.16
                    - (0.02 if durable_support_ticks <= 1 and fragile_recovery_memory >= 0.54 else 0.0),
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
                    + max(0.0, fragile_recovery_memory - 0.42) * 0.018
                ),
            )
            shallow_recovery_risk = max(
                0.0,
                min(
                    1.0,
                    max(0.0, 0.58 - recovery_durability)
                    + max(0.0, hardship_cluster - 0.5) * 0.45
                    + max(0.0, cumulative_stress_load - 0.52) * 0.38
                    + max(0.0, average_service_backlog - 0.36) * 0.32
                    + max(0.0, district_asymmetry_persistence - 0.44) * 0.24
                    + max(0.0, fragile_recovery_memory - 0.44) * 0.36
                    - max(0.0, local_recovery_context - 0.56) * 0.35,
                    - max(0.0, recovery_gate - 0.58) * 0.24,
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
                'network_fragility': round(network_fragility, 3),
                'network_resilience': round(network_resilience, 3),
                'recovery_gate_index': round(recovery_gate, 3),
                'fragile_recovery_memory': round(fragile_recovery_memory, 3),
                'durable_support_ticks': durable_support_ticks,
                'topology_drag_memory': round(topology_drag_memory, 3),
                'topology_support_memory': round(topology_support_memory, 3),
                'topology_relapse_bias': round(topology_relapse_bias, 3),
                'topology_support_alignment': round(topology_support_alignment, 3),
                'topology_support_alignment_gap': round(support_alignment_gap, 3),
                'spillover_scar_memory': round(spillover_scar_memory, 3),
                'containment_capacity': round(containment_capacity, 3),
            }
            district['institution_summary'] = {
                'employers': sum(1 for i in district_institutions if i.get('institution_type') == 'employer'),
                'landlords': sum(1 for i in district_institutions if i.get('institution_type') == 'landlord'),
                'transit_services': sum(1 for i in district_institutions if i.get('institution_type') == 'transit'),
                'care_services': len(service_institutions),
                'service_capacity': service_capacity,
                'institution_stress': round(institution_stress, 3),
                'utilization_pressure': round(avg_utilization_pressure, 3),
                'service_backlog': round(average_service_backlog, 3),
                'responsiveness_drag': round(responsiveness_drag, 3),
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
                'service_backlog': round(average_service_backlog, 3),
                'responsiveness_drag': round(responsiveness_drag, 3),
                'network_fragility': round(network_fragility, 3),
                'network_resilience': round(network_resilience, 3),
                'asymmetry_persistence': round(district_asymmetry_persistence, 3),
                'recovery_debt_index': round(district_recovery_debt, 3),
                'recovery_gate_index': round(recovery_gate, 3),
                'fragile_recovery_memory': round(fragile_recovery_memory, 3),
                'spillover_scar_memory': round(spillover_scar_memory, 3),
                'containment_capacity': round(containment_capacity, 3),
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
                'network_fragility': round(network_fragility, 3),
                'network_resilience': round(network_resilience, 3),
                'institution_drift': round(institution_drift, 3),
                'resilience_buffer': round(institution_buffer, 3),
                'cumulative_stress_load': round(cumulative_stress_load, 3),
                'recovery_durability': round(recovery_durability, 3),
                'shallow_recovery_risk': round(shallow_recovery_risk, 3),
                'asymmetry_persistence': round(district_asymmetry_persistence, 3),
                'recovery_debt_index': round(district_recovery_debt, 3),
                'recovery_gate_index': round(recovery_gate, 3),
                'fragile_recovery_memory': round(fragile_recovery_memory, 3),
                'durable_support_ticks': durable_support_ticks,
                'topology_relapse_bias': round(topology_relapse_bias, 3),
                'topology_support_alignment': round(topology_support_alignment, 3),
                'topology_support_alignment_gap': round(support_alignment_gap, 3),
                'spillover_scar_memory': round(spillover_scar_memory, 3),
                'containment_capacity': round(containment_capacity, 3),
                'service_backlog': round(average_service_backlog, 3),
                'responsiveness_drag': round(responsiveness_drag, 3),
                'decline_lock': bool(next_phase in {'tightening', 'strained'} and phase_momentum >= 0.25),
                'recovery_lock': bool(next_phase in {'stabilizing', 'recovering'} and inflection_score >= 0.2 and recovery_durability >= 0.45),
                'neighborhood_cluster_drag': round(neighborhood_cluster_drag, 3),
                'last_turning_signal': (
                    'decline_risk'
                    if phase_momentum >= 0.25
                    else 'recovery_candidate'
                    if inflection_score >= 0.2
                    else 'mixed'
                ),
                'tipping_thresholds': AuraliteRuntimeService._district_tipping_thresholds(
                    phase=next_phase,
                    pressure_index=pressure_index,
                    phase_momentum=phase_momentum,
                    inflection_score=inflection_score,
                    shallow_recovery_risk=shallow_recovery_risk,
                    recovery_durability=recovery_durability,
                    hardship_cluster=hardship_cluster,
                    contagion_pressure=float((((district.get('derived_summary') or {}).get('ripple_context') or {}).get('contagion_pressure', 0.0))),
                    incoming_neighbor_pressure=float((((district.get('derived_summary') or {}).get('ripple_context') or {}).get('incoming_neighbor_pressure', 0.0))),
                ),
                'momentum_management': AuraliteRuntimeService._district_momentum_management(
                    phase=next_phase,
                    phase_momentum=phase_momentum,
                    inflection_score=inflection_score,
                    recovery_durability=recovery_durability,
                    shallow_recovery_risk=shallow_recovery_risk,
                    cumulative_stress_load=cumulative_stress_load,
                    hardship_cluster=hardship_cluster,
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
            containment_weakness = max(
                0.0,
                min(
                    1.0,
                    max(0.0, float((district.get('arc_state') or {}).get('network_fragility', 0.0)) - 0.42) * 0.52
                    + max(0.0, float((district.get('arc_state') or {}).get('service_backlog', 0.0)) - 0.34) * 0.46
                    + max(0.0, float((district.get('arc_state') or {}).get('responsiveness_drag', 0.0)) - 0.06) * 0.52
                    + max(0.0, float((district.get('arc_state') or {}).get('asymmetry_persistence', 0.0)) - 0.4) * 0.38
                    + max(0.0, float((district.get('arc_state') or {}).get('fragile_recovery_memory', 0.0)) - 0.42) * 0.48,
                ),
            )
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
                min(
                    0.06,
                    base_gap_effect
                    + decline_spread
                    - recovery_spread
                    + stabilization_drag
                    + cluster_amplification
                    + min(0.024, containment_weakness * 0.03),
                ),
            )
            containment_capacity = max(
                0.0,
                min(
                    1.0,
                    float(district.get('service_access_score', 0.5)) * 0.5
                    + float(district.get('social_support_score', 0.5)) * 0.5
                    + max(0.0, float((district.get('arc_state') or {}).get('recovery_durability', 0.0)) - 0.45) * 0.5,
                    - min(0.25, containment_weakness * 0.42),
                ),
            )
            containment_adjustment = max(0.72, 1.0 - containment_capacity * 0.34)
            ripple_effect = round(ripple_effect * containment_adjustment, 3)
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
                'containment_capacity': round(containment_capacity, 3),
                'containment_adjustment': round(containment_adjustment, 3),
                'containment_weakness': round(containment_weakness, 3),
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
                'containment_capacity': ripple['containment_capacity'],
                'containment_adjustment': ripple['containment_adjustment'],
                'containment_weakness': ripple['containment_weakness'],
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
        previous_propagation = world_state.get('propagation_state') or {}
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
                target_network_fragility = float((target.get('arc_state') or {}).get('network_fragility', 0.0))
                target_network_resilience = float((target.get('arc_state') or {}).get('network_resilience', 0.0))
                target_modifier += max(0.0, target_network_fragility - 0.42) * 0.28
                target_modifier -= max(0.0, target_network_resilience - 0.52) * 0.18
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
                tie_usefulness = float(tie.get('support_usefulness', 0.58))
                tie_capacity = float(tie.get('support_capacity', 0.56))
                tie_fatigue = float(tie.get('support_fatigue', 0.12))
                tie_memory = float(tie.get('strain_transfer_memory', 0.0))
                propagation_factor = (
                    tie_weight
                    * (1.1 - (support_buffer * 0.5 + service_buffer * 0.45))
                    * (0.78 + max(0.0, 1.0 - tie_capacity) * 0.32)
                    * (0.84 + tie_fatigue * 0.4 + max(0.0, tie_memory - 0.4) * 0.28)
                    * (0.86 + max(0.0, 0.62 - tie_usefulness) * 0.36)
                )
                propagation = round(stress_delta * propagation_factor, 3)
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
                    'tie_usefulness': round(tie_usefulness, 3),
                    'tie_capacity': round(tie_capacity, 3),
                    'tie_fatigue': round(tie_fatigue, 3),
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
            'continuation_rollup': {
                'total_district_events': int(previous_propagation.get('continuation_rollup', {}).get('total_district_events', 0)) + len(district_events),
                'total_social_events': int(previous_propagation.get('continuation_rollup', {}).get('total_social_events', 0)) + len(social_events),
                'ticks_with_neighbor_pressure': (
                    int(previous_propagation.get('continuation_rollup', {}).get('ticks_with_neighbor_pressure', 0)) + 1
                    if district_events
                    else max(0, int(previous_propagation.get('continuation_rollup', {}).get('ticks_with_neighbor_pressure', 0)) - 1)
                ),
                'ticks_with_social_propagation': (
                    int(previous_propagation.get('continuation_rollup', {}).get('ticks_with_social_propagation', 0)) + 1
                    if social_events
                    else max(0, int(previous_propagation.get('continuation_rollup', {}).get('ticks_with_social_propagation', 0)) - 1)
                ),
                'max_tick_neighbor_impact': round(
                    max(
                        float(previous_propagation.get('continuation_rollup', {}).get('max_tick_neighbor_impact', 0.0)),
                        max((abs(event.get('impact_pressure', 0.0)) for event in district_events), default=0.0),
                    ),
                    3,
                ),
                'max_tick_social_stress': round(
                    max(
                        float(previous_propagation.get('continuation_rollup', {}).get('max_tick_social_stress', 0.0)),
                        max((abs(event.get('stress_shift', 0.0)) for event in social_events), default=0.0),
                    ),
                    3,
                ),
            },
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
        average_backlog = (
            sum(float((inst.get('arc_state') or {}).get('service_backlog', 0.0)) for inst in world_state.get('institutions', []))
            / max(1, len(world_state.get('institutions', [])))
        )
        delayed_recovery_pressure = (
            sum(max(0.0, float((district.get('arc_state') or {}).get('shallow_recovery_risk', 0.0)) - 0.5) for district in districts)
            / max(1, len(districts))
        )
        person_memory_debt_index = (
            sum(float((person.get('adaptation_state') or {}).get('recovery_debt', 0.0)) for person in persons)
            / max(1, len(persons))
        )
        household_stability_reserve = (
            sum(float((household.get('adaptation_state') or {}).get('resilience_reserve', 0.0)) for household in households)
            / max(1, len(households))
        )
        household_queue_scar_index = (
            sum(float((household.get('adaptation_state') or {}).get('institution_queue_scar_memory', 0.0)) for household in households)
            / max(1, len(households))
        )
        household_service_rebound_index = (
            sum(float((household.get('adaptation_state') or {}).get('service_rebound_reserve', 0.0)) for household in households)
            / max(1, len(households))
        )
        household_relief_interruption_index = (
            sum(float((household.get('adaptation_state') or {}).get('relief_interruption_count', 0.0)) for household in households)
            / max(1, len(households))
        )
        household_assistance_trust_index = (
            sum(float((household.get('adaptation_state') or {}).get('assistance_trust_index', 0.5)) for household in households)
            / max(1, len(households))
        )
        household_responsiveness_memory_index = (
            sum(float((household.get('adaptation_state') or {}).get('responsiveness_memory', 0.0)) for household in households)
            / max(1, len(households))
        )
        household_recovery_lag_index = (
            sum(float((household.get('adaptation_state') or {}).get('nominal_relief_lag', 0.0)) for household in households)
            / max(1, len(households))
        )
        institution_fatigue_index = (
            sum(float((inst.get('arc_state') or {}).get('overload_fatigue', 0.0)) for inst in world_state.get('institutions', []))
            / max(1, len(world_state.get('institutions', [])))
        )
        institution_recovery_lag_index = (
            sum(float((inst.get('arc_state') or {}).get('recovery_lag_memory', 0.0)) for inst in world_state.get('institutions', []))
            / max(1, len(world_state.get('institutions', [])))
        )
        social_network_fatigue_index = (
            sum(float((person.get('social_context') or {}).get('support_fatigue_index', 0.0)) for person in persons)
            / max(1, len(persons))
        )
        relationship_usefulness_index = (
            sum(float((person.get('social_context') or {}).get('relationship_usefulness_index', 0.0)) for person in persons)
            / max(1, len(persons))
        )
        fragile_recovery_index = (
            sum(float((district.get('arc_state') or {}).get('shallow_recovery_risk', 0.0)) for district in districts)
            / max(1, len(districts))
        )
        district_durability_index = (
            sum(float((district.get('arc_state') or {}).get('recovery_durability', 0.0)) for district in districts)
            / max(1, len(districts))
        )
        district_recovery_gate_index = (
            sum(float((district.get('arc_state') or {}).get('recovery_gate_index', 0.0)) for district in districts)
            / max(1, len(districts))
        )
        district_fragile_memory_index = (
            sum(float((district.get('arc_state') or {}).get('fragile_recovery_memory', 0.0)) for district in districts)
            / max(1, len(districts))
        )
        district_cumulative_stress_index = (
            sum(float((district.get('arc_state') or {}).get('cumulative_stress_load', 0.0)) for district in districts)
            / max(1, len(districts))
        )
        district_containment_weakness_index = (
            sum(float(((district.get('derived_summary') or {}).get('ripple_context') or {}).get('containment_weakness', 0.0)) for district in districts)
            / max(1, len(districts))
        )
        local_recovery_share = (
            sum(
                1
                for district in districts
                if district.get('state_phase') in {'stabilizing', 'recovering'}
                and float((district.get('arc_state') or {}).get('recovery_durability', 0.0)) >= 0.45
            )
            / max(1, len(districts))
        )
        clustered_fragility_pressure = AuraliteRuntimeService._clustered_fragility_pressure(districts)
        clustered_resilience_support = AuraliteRuntimeService._clustered_resilience_support(districts)
        topology_shape_summary = AuraliteRuntimeService._topology_shape_summary(districts)
        topology_corridor_weakness = float(topology_shape_summary.get('topology_corridor_weakness', 0.0))
        topology_ring_containment = float(topology_shape_summary.get('topology_ring_containment', 0.0))
        topology_cluster_support_span = float(topology_shape_summary.get('topology_cluster_support_span', 0.0))
        topology_bridge_instability = float(topology_shape_summary.get('topology_bridge_instability', 0.0))
        clustered_drag_dominance = max(
            0.0,
            min(
                1.0,
                clustered_fragility_pressure
                - (clustered_resilience_support * 0.82)
                + max(0.0, topology_corridor_weakness - 0.3) * 0.16
                + max(0.0, topology_ring_containment - 0.34) * 0.12,
                + max(0.0, topology_bridge_instability - 0.32) * 0.08,
            ),
        )
        previous_split = ((((world_state.get('city') or {}).get('world_metrics') or {}).get('local_vs_broad_pressure_split') or {}))
        prior_drag_persistence_ticks = int(previous_split.get('topology_drag_persistence_ticks', 0))
        prior_support_persistence_ticks = int(previous_split.get('topology_support_persistence_ticks', 0))
        prior_persistent_cluster_drag = float(previous_split.get('persistent_cluster_drag', 0.0))
        prior_persistent_cluster_support = float(previous_split.get('persistent_cluster_support', 0.0))
        drag_persistence_ticks = min(
            24,
            prior_drag_persistence_ticks + (2 if clustered_drag_dominance >= 0.26 else 1)
            if clustered_drag_dominance >= 0.16
            else max(0, prior_drag_persistence_ticks - 2),
        )
        if topology_corridor_weakness >= 0.42 or topology_ring_containment >= 0.44:
            drag_persistence_ticks = min(24, drag_persistence_ticks + 1)
        support_signal = max(0.0, clustered_resilience_support - max(0.0, clustered_fragility_pressure - 0.22))
        support_alignment_signal = max(
            0.0,
            min(
                1.0,
                support_signal
                - max(0.0, clustered_drag_dominance - 0.12) * 0.34
                - max(0.0, district_containment_weakness_index - 0.3) * 0.12
                - max(0.0, district_fragile_memory_index - 0.48) * 0.18
                - max(0.0, topology_corridor_weakness - 0.36) * 0.18
                - max(0.0, topology_ring_containment - 0.38) * 0.12
                - max(0.0, topology_bridge_instability - 0.34) * 0.08
                + max(0.0, topology_cluster_support_span - 0.24) * 0.22,
            ),
        )
        support_persistence_ticks = min(
            24,
            prior_support_persistence_ticks + (2 if support_alignment_signal >= 0.24 else 1)
            if support_alignment_signal >= 0.1
            else max(0, prior_support_persistence_ticks - 3),
        )
        drag_soak_intensity = max(
            0.0,
            min(
                1.0,
                (clustered_drag_dominance * 0.58)
                + max(0.0, drag_persistence_ticks - 5) * 0.018
                + max(0.0, district_containment_weakness_index - 0.3) * 0.22
                + max(0.0, district_cumulative_stress_index - 0.5) * 0.22
                + max(0.0, topology_corridor_weakness - 0.32) * 0.28
                + max(0.0, topology_ring_containment - 0.34) * 0.24
                + max(0.0, topology_bridge_instability - 0.3) * 0.1
                - (clustered_resilience_support * 0.18),
            ),
        )
        support_soak_intensity = max(
            0.0,
            min(
                1.0,
                (support_alignment_signal * 0.56)
                + max(0.0, support_persistence_ticks - 6) * 0.016
                + max(0.0, district_recovery_gate_index - 0.46) * 0.18
                + max(0.0, district_durability_index - 0.46) * 0.14
                + max(0.0, topology_cluster_support_span - 0.26) * 0.22
                - max(0.0, topology_corridor_weakness - 0.36) * 0.22
                - max(0.0, drag_soak_intensity - 0.24) * 0.24,
            ),
        )
        persistent_cluster_drag = max(
            0.0,
            min(
                1.0,
                (prior_persistent_cluster_drag * 0.88)
                + (clustered_drag_dominance * 0.12)
                + (drag_soak_intensity * 0.1)
                + max(0.0, drag_persistence_ticks - 5) * 0.012,
                + max(0.0, topology_corridor_weakness - 0.32) * 0.14
                + max(0.0, topology_ring_containment - 0.34) * 0.12,
            ),
        )
        persistent_cluster_support = max(
            0.0,
            min(
                1.0,
                (prior_persistent_cluster_support * 0.86)
                + (support_alignment_signal * 0.14)
                + (support_soak_intensity * 0.08)
                + max(0.0, support_persistence_ticks - 6) * 0.01,
                + max(0.0, topology_cluster_support_span - 0.28) * 0.1
                - max(0.0, topology_corridor_weakness - 0.36) * 0.08,
            ),
        )
        topology_persistence_balance = max(
            0.0,
            min(
                1.0,
                persistent_cluster_drag - (persistent_cluster_support * 0.86),
            ),
        )
        uneven_recovery_penalty = max(0.0, local_recovery_share - 0.45) * max(0.0, clustered_fragility_pressure - 0.32)
        gate_durability_sync = max(
            0.0,
            min(
                1.0,
                (district_durability_index * 0.58)
                + (district_recovery_gate_index * 0.42)
                - (district_fragile_memory_index * 0.62),
            ),
        )
        district_pressures = sorted(
            [float(district.get('pressure_index', 0.0)) for district in districts],
            reverse=True,
        )
        top_slice_count = max(1, min(2, len(district_pressures)))
        citywide_pressure_avg = sum(district_pressures) / max(1, len(district_pressures))
        top_pressure_avg = sum(district_pressures[:top_slice_count]) / top_slice_count
        local_broad_divergence = max(0.0, top_pressure_avg - citywide_pressure_avg)
        broad_durability_drag = max(
            0.0,
            min(
                0.6,
                max(0.0, district_fragile_memory_index - district_durability_index) * 0.36
                + max(0.0, fragile_recovery_index - 0.52) * 0.24
                + max(0.0, local_broad_divergence - 0.08) * 0.52
                + max(0.0, average_backlog - 0.35) * 0.18,
                + max(0.0, household_recovery_lag_index - 0.26) * 0.18
                + max(0.0, institution_recovery_lag_index - 0.24) * 0.16
                + max(0.0, district_containment_weakness_index - 0.28) * 0.18
                + max(0.0, district_cumulative_stress_index - 0.5) * 0.2
                + max(0.0, clustered_fragility_pressure - 0.3) * 0.56
                + max(0.0, clustered_drag_dominance - 0.15) * 0.26
                + max(0.0, topology_persistence_balance - 0.12) * 0.36
                + max(0.0, drag_soak_intensity - 0.24) * 0.32
                + max(0.0, topology_corridor_weakness - 0.3) * 0.28
                + max(0.0, topology_ring_containment - 0.36) * 0.24
                + max(0.0, topology_bridge_instability - 0.32) * 0.08
                - max(0.0, topology_cluster_support_span - 0.34) * 0.18
                + max(0.0, household_relief_interruption_index - 2.0) * 0.015
                + uneven_recovery_penalty * 0.34,
            ),
        )
        topology_recovery_penalty = (
            max(0.0, local_recovery_share - 0.24) * max(0.0, clustered_drag_dominance - 0.12)
            + max(0.0, topology_persistence_balance - 0.16) * 0.22
            + max(0.0, drag_soak_intensity - support_soak_intensity) * 0.24
            + max(0.0, topology_corridor_weakness - 0.34) * 0.24
            + max(0.0, topology_ring_containment - 0.36) * 0.2
            + max(0.0, topology_bridge_instability - 0.34) * 0.08
            - max(0.0, topology_cluster_support_span - 0.34) * 0.14
        )
        neighborhood_regime_drag = max(
            0.0,
            min(
                1.0,
                (clustered_fragility_pressure * 0.42)
                + max(0.0, district_containment_weakness_index - 0.32) * 0.26
                + max(0.0, district_cumulative_stress_index - 0.54) * 0.24
                + max(0.0, local_broad_divergence - 0.1) * 0.28
                + max(0.0, topology_persistence_balance - 0.14) * 0.32
                + max(0.0, drag_soak_intensity - 0.26) * 0.22
                + max(0.0, topology_corridor_weakness - 0.32) * 0.26
                + max(0.0, topology_ring_containment - 0.34) * 0.22
                + max(0.0, topology_bridge_instability - 0.3) * 0.08
                - (clustered_resilience_support * 0.24),
            ),
        )
        citywide_durability_headroom = max(
            0.0,
            min(
                1.0,
                (district_durability_index * 0.74)
                + (gate_durability_sync * 0.22)
                + (clustered_resilience_support * 0.1)
                + (persistent_cluster_support * 0.08)
                + (support_soak_intensity * 0.08)
                + (topology_cluster_support_span * 0.08)
                - (broad_durability_drag * 1.14)
                - max(0.0, clustered_fragility_pressure - 0.34) * 0.16
                - max(0.0, persistent_cluster_drag - 0.24) * 0.16
                - max(0.0, drag_soak_intensity - 0.22) * 0.16
                - max(0.0, topology_corridor_weakness - 0.34) * 0.2
                - max(0.0, topology_ring_containment - 0.36) * 0.16
                - max(0.0, topology_bridge_instability - 0.34) * 0.06
                - topology_recovery_penalty * 0.72
                - neighborhood_regime_drag * 0.18,
            ),
        )
        local_vs_broad_split = {
            'top_district_pressure_avg': round(top_pressure_avg, 3),
            'citywide_pressure_avg': round(citywide_pressure_avg, 3),
            'spread_gap': round(
                top_pressure_avg - citywide_pressure_avg,
                3,
            ) if district_pressures else 0.0,
            'local_recovery_share': round(local_recovery_share, 3),
            'broad_durability_drag': round(broad_durability_drag, 3),
            'citywide_durability_headroom': round(citywide_durability_headroom, 3),
            'clustered_fragility_pressure': round(clustered_fragility_pressure, 3),
            'district_containment_weakness_index': round(district_containment_weakness_index, 3),
            'district_cumulative_stress_index': round(district_cumulative_stress_index, 3),
            'gate_durability_sync': round(gate_durability_sync, 3),
            'uneven_recovery_penalty': round(uneven_recovery_penalty, 3),
            'clustered_resilience_support': round(clustered_resilience_support, 3),
            'clustered_drag_dominance': round(clustered_drag_dominance, 3),
            'topology_recovery_penalty': round(topology_recovery_penalty, 3),
            'neighborhood_regime_drag': round(neighborhood_regime_drag, 3),
            'topology_drag_persistence_ticks': drag_persistence_ticks,
            'topology_support_persistence_ticks': support_persistence_ticks,
            'topology_drag_soak_intensity': round(drag_soak_intensity, 3),
            'topology_support_soak_intensity': round(support_soak_intensity, 3),
            'topology_support_alignment_signal': round(support_alignment_signal, 3),
            'persistent_cluster_drag': round(persistent_cluster_drag, 3),
            'persistent_cluster_support': round(persistent_cluster_support, 3),
            'topology_persistence_balance': round(topology_persistence_balance, 3),
            'topology_corridor_weakness': round(topology_corridor_weakness, 3),
            'topology_ring_containment': round(topology_ring_containment, 3),
            'topology_cluster_support_span': round(topology_cluster_support_span, 3),
            'topology_bridge_instability': round(topology_bridge_instability, 3),
            'household_recovery_lag_index': round(household_recovery_lag_index, 3),
            'institution_recovery_lag_index': round(institution_recovery_lag_index, 3),
            'household_relief_interruption_index': round(household_relief_interruption_index, 3),
            'household_assistance_trust_index': round(household_assistance_trust_index, 3),
            'household_responsiveness_memory_index': round(household_responsiveness_memory_index, 3),
        }
        prior_long_horizon = ((((world_state.get('city') or {}).get('world_metrics') or {}).get('long_horizon_divergence_state') or {}))
        local_bridge_streak = int(prior_long_horizon.get('local_stabilization_bridge_streak', 0))
        broad_regime_drag_streak = int(prior_long_horizon.get('broad_regime_drag_streak', 0))
        corridor_partial_reconnect_streak = int(prior_long_horizon.get('corridor_partial_reconnect_streak', 0))
        delayed_deterioration_risk = float(prior_long_horizon.get('delayed_deterioration_risk', 0.0))
        local_bridge_condition = local_recovery_share >= 0.3 and citywide_durability_headroom <= 0.38
        broad_drag_condition = neighborhood_regime_drag >= 0.34 or broad_durability_drag >= 0.28
        corridor_partial_reconnect_condition = (
            support_alignment_signal >= 0.2
            and clustered_drag_dominance >= 0.22
            and citywide_durability_headroom <= 0.42
        )
        local_bridge_streak = min(40, local_bridge_streak + 1) if local_bridge_condition else max(0, local_bridge_streak - 1)
        broad_regime_drag_streak = min(40, broad_regime_drag_streak + 1) if broad_drag_condition else max(0, broad_regime_drag_streak - 2)
        corridor_partial_reconnect_streak = (
            min(40, corridor_partial_reconnect_streak + 1)
            if corridor_partial_reconnect_condition
            else max(0, corridor_partial_reconnect_streak - 2)
        )
        delayed_deterioration_risk = max(
            0.0,
            min(
                1.0,
                delayed_deterioration_risk * 0.84
                + max(0.0, local_bridge_streak - 2) * 0.022
                + max(0.0, broad_regime_drag_streak - 1) * 0.018
                + max(0.0, persistent_cluster_drag - 0.24) * 0.24
                + max(0.0, topology_persistence_balance - 0.16) * 0.16
                - max(0.0, corridor_partial_reconnect_streak - 3) * 0.014
                - max(0.0, citywide_durability_headroom - 0.48) * 0.18,
            ),
        )
        long_horizon_divergence_state = {
            'local_stabilization_bridge_streak': local_bridge_streak,
            'broad_regime_drag_streak': broad_regime_drag_streak,
            'corridor_partial_reconnect_streak': corridor_partial_reconnect_streak,
            'delayed_deterioration_risk': round(delayed_deterioration_risk, 3),
            'local_stabilization_without_city_recovery': bool(local_bridge_streak >= 3 and citywide_durability_headroom <= 0.42),
            'corridor_partial_reconnect_without_broad_lift': bool(corridor_partial_reconnect_streak >= 2 and broad_regime_drag_streak >= 2),
        }
        regime_state = AuraliteRuntimeService._city_regime_state(
            world_state=world_state,
            districts=districts,
            local_vs_broad_split=local_vs_broad_split,
        )
        latest_intervention = ((world_state.get('intervention_state') or {}).get('history') or [])
        latest_effects = (((latest_intervention[-1] if latest_intervention else {}).get('effects') or {}).get('applied') or [])
        intervention_side_effect_load = sum(
            len(effect.get('side_effects', []))
            for effect in latest_effects
            if isinstance(effect, dict)
        )
        causal_diagnostics = AuraliteRuntimeService._city_causal_diagnostics(
            world_state=world_state,
            districts=districts,
            backlog_index=average_backlog,
            delayed_recovery_pressure=delayed_recovery_pressure,
        )

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
            'causal_diagnostics': causal_diagnostics,
            'service_backlog_index': round(average_backlog, 3),
            'delayed_recovery_pressure': round(delayed_recovery_pressure, 3),
            'person_memory_debt_index': round(person_memory_debt_index, 3),
            'household_stability_reserve_index': round(household_stability_reserve, 3),
            'household_queue_scar_index': round(household_queue_scar_index, 3),
            'household_service_rebound_index': round(household_service_rebound_index, 3),
            'household_recovery_lag_index': round(household_recovery_lag_index, 3),
            'household_relief_interruption_index': round(household_relief_interruption_index, 3),
            'household_assistance_trust_index': round(household_assistance_trust_index, 3),
            'household_responsiveness_memory_index': round(household_responsiveness_memory_index, 3),
            'institution_fatigue_index': round(institution_fatigue_index, 3),
            'institution_recovery_lag_index': round(institution_recovery_lag_index, 3),
            'social_network_fatigue_index': round(social_network_fatigue_index, 3),
            'relationship_usefulness_index': round(relationship_usefulness_index, 3),
            'fragile_recovery_index': round(fragile_recovery_index, 3),
            'district_recovery_durability_index': round(district_durability_index, 3),
            'district_recovery_gate_index': round(district_recovery_gate_index, 3),
            'district_fragile_memory_index': round(district_fragile_memory_index, 3),
            'district_cumulative_stress_index': round(district_cumulative_stress_index, 3),
            'district_containment_weakness_index': round(district_containment_weakness_index, 3),
            'clustered_fragility_pressure': round(clustered_fragility_pressure, 3),
            'clustered_resilience_support': round(clustered_resilience_support, 3),
            'local_vs_broad_pressure_split': local_vs_broad_split,
            'long_horizon_divergence_state': long_horizon_divergence_state,
            'intervention_side_effect_load': int(intervention_side_effect_load),
        }
        world_state['city']['regime_state'] = regime_state

    @staticmethod
    def _clustered_fragility_pressure(districts: list[dict]) -> float:
        if not districts:
            return 0.0

        district_by_id = {district.get('district_id'): district for district in districts if district.get('district_id')}
        fragile_nodes = set()
        node_pressure = {}
        for district in districts:
            district_id = district.get('district_id')
            if not district_id:
                continue
            arc = district.get('arc_state') or {}
            ripple = (district.get('derived_summary') or {}).get('ripple_context') or {}
            fragile_memory = float(arc.get('fragile_recovery_memory', 0.0))
            shallow_risk = float(arc.get('shallow_recovery_risk', 0.0))
            containment_weakness = float(ripple.get('containment_weakness', 0.0))
            cumulative_stress = float(arc.get('cumulative_stress_load', 0.0))
            fragility_score = max(
                0.0,
                min(
                    1.0,
                    (fragile_memory * 0.44)
                    + (shallow_risk * 0.34)
                    + (containment_weakness * 0.12)
                    + (cumulative_stress * 0.1),
                ),
            )
            node_pressure[district_id] = fragility_score
            if fragility_score >= 0.5:
                fragile_nodes.add(district_id)

        if not fragile_nodes:
            return 0.0

        visited = set()
        component_scores: list[float] = []
        for district_id in fragile_nodes:
            if district_id in visited:
                continue
            stack = [district_id]
            component = []
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.append(current)
                for neighbor in AuraliteRuntimeService.DISTRICT_NEIGHBORS.get(current, []):
                    if neighbor in fragile_nodes and neighbor in district_by_id and neighbor not in visited:
                        stack.append(neighbor)
            if component:
                component_avg = sum(node_pressure[d_id] for d_id in component) / len(component)
                cluster_multiplier = 1.0 + min(0.6, (len(component) - 1) * 0.16)
                component_scores.append(component_avg * cluster_multiplier)

        base_pressure = (sum(component_scores) / max(1, len(districts))) * 1.2
        return max(0.0, min(1.0, base_pressure))

    @staticmethod
    def _clustered_resilience_support(districts: list[dict]) -> float:
        if not districts:
            return 0.0
        district_by_id = {district.get('district_id'): district for district in districts if district.get('district_id')}
        resilient_nodes = set()
        node_support = {}
        for district in districts:
            district_id = district.get('district_id')
            if not district_id:
                continue
            arc = district.get('arc_state') or {}
            ripple = (district.get('derived_summary') or {}).get('ripple_context') or {}
            durability = float(arc.get('recovery_durability', 0.0))
            gate = float(arc.get('recovery_gate_index', 0.0))
            fragile_memory = float(arc.get('fragile_recovery_memory', 0.0))
            recovery_cluster = float(ripple.get('recovery_cluster_share', 0.0))
            support_score = max(
                0.0,
                min(
                    1.0,
                    (durability * 0.46)
                    + (gate * 0.26)
                    + (recovery_cluster * 0.2)
                    - (max(0.0, fragile_memory - 0.4) * 0.28),
                ),
            )
            node_support[district_id] = support_score
            if support_score >= 0.48:
                resilient_nodes.add(district_id)
        if not resilient_nodes:
            return 0.0

        visited = set()
        component_scores: list[float] = []
        for district_id in resilient_nodes:
            if district_id in visited:
                continue
            stack = [district_id]
            component = []
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.append(current)
                for neighbor in AuraliteRuntimeService.DISTRICT_NEIGHBORS.get(current, []):
                    if neighbor in resilient_nodes and neighbor in district_by_id and neighbor not in visited:
                        stack.append(neighbor)
            if component:
                component_avg = sum(node_support[d_id] for d_id in component) / len(component)
                cluster_multiplier = 1.0 + min(0.42, (len(component) - 1) * 0.11)
                component_scores.append(component_avg * cluster_multiplier)

        base_support = (sum(component_scores) / max(1, len(districts))) * 0.94
        return max(0.0, min(1.0, base_support))

    @staticmethod
    def _topology_shape_summary(districts: list[dict]) -> dict:
        if not districts:
            return {
                'topology_corridor_weakness': 0.0,
                'topology_ring_containment': 0.0,
                'topology_cluster_support_span': 0.0,
                'topology_bridge_instability': 0.0,
            }

        district_by_id = {district.get('district_id'): district for district in districts if district.get('district_id')}
        if not district_by_id:
            return {
                'topology_corridor_weakness': 0.0,
                'topology_ring_containment': 0.0,
                'topology_cluster_support_span': 0.0,
                'topology_bridge_instability': 0.0,
            }

        fragile_nodes: set[str] = set()
        resilient_nodes: set[str] = set()
        for district_id, district in district_by_id.items():
            arc = district.get('arc_state') or {}
            ripple = (district.get('derived_summary') or {}).get('ripple_context') or {}
            fragility_signal = (
                float(arc.get('fragile_recovery_memory', 0.0)) * 0.54
                + float(ripple.get('stressed_cluster_share', 0.0)) * 0.3
                + float(arc.get('cumulative_stress_load', 0.0)) * 0.16
            )
            support_signal = (
                float(arc.get('recovery_durability', 0.0)) * 0.54
                + float(arc.get('recovery_gate_index', 0.0)) * 0.24
                + float(ripple.get('recovery_cluster_share', 0.0)) * 0.22
            )
            if fragility_signal >= 0.54:
                fragile_nodes.add(district_id)
            if support_signal >= 0.5:
                resilient_nodes.add(district_id)

        weak_boundary_sum = 0.0
        boundary_count = 0
        for district_id in fragile_nodes:
            neighbors = AuraliteRuntimeService.DISTRICT_NEIGHBORS.get(district_id, [])
            if not neighbors:
                continue
            weak_link_score = 0.0
            for neighbor_id in neighbors:
                if neighbor_id not in district_by_id:
                    continue
                neighbor_arc = district_by_id[neighbor_id].get('arc_state') or {}
                neighbor_ripple = (district_by_id[neighbor_id].get('derived_summary') or {}).get('ripple_context') or {}
                neighbor_support = (
                    float(neighbor_arc.get('recovery_durability', 0.0)) * 0.58
                    + float(neighbor_ripple.get('recovery_cluster_share', 0.0)) * 0.22
                    + float(neighbor_arc.get('topology_support_alignment', 0.0)) * 0.2
                )
                weak_link_score += max(0.0, 0.62 - neighbor_support)
                if neighbor_id in fragile_nodes:
                    weak_link_score += 0.16
            weak_boundary_sum += min(1.0, weak_link_score / max(1, len(neighbors)))
            boundary_count += 1
        topology_corridor_weakness = weak_boundary_sum / max(1, boundary_count)

        ring_total = 0.0
        ring_count = 0
        for district_id in fragile_nodes:
            neighbors = [n for n in AuraliteRuntimeService.DISTRICT_NEIGHBORS.get(district_id, []) if n in district_by_id]
            if len(neighbors) < 2:
                continue
            weak_neighbor_pressure = sum(
                max(
                    0.0,
                    0.56 - float((district_by_id[neighbor_id].get('arc_state') or {}).get('topology_support_alignment', 0.0)),
                )
                + (0.14 if neighbor_id in fragile_nodes else 0.0)
                for neighbor_id in neighbors
            )
            ring_total += min(1.0, weak_neighbor_pressure / len(neighbors))
            ring_count += 1
        topology_ring_containment = ring_total / max(1, ring_count)

        support_span_total = 0.0
        support_span_count = 0
        for district_id in resilient_nodes:
            neighbors = [n for n in AuraliteRuntimeService.DISTRICT_NEIGHBORS.get(district_id, []) if n in district_by_id]
            if not neighbors:
                continue
            supportive_neighbors = sum(
                1
                for neighbor_id in neighbors
                if (
                    neighbor_id in resilient_nodes
                    and float((district_by_id[neighbor_id].get('arc_state') or {}).get('topology_support_alignment', 0.0)) >= 0.44
                )
            )
            support_span_total += supportive_neighbors / len(neighbors)
            support_span_count += 1
        topology_cluster_support_span = min(1.0, (support_span_total / max(1, support_span_count)) * 0.9)
        bridge_instability_total = 0.0
        bridge_count = 0
        for district_id in fragile_nodes:
            neighbors = [n for n in AuraliteRuntimeService.DISTRICT_NEIGHBORS.get(district_id, []) if n in district_by_id]
            if not neighbors:
                continue
            fragile_neighbor_share = (
                sum(1 for neighbor_id in neighbors if neighbor_id in fragile_nodes) / len(neighbors)
            )
            for neighbor_id in neighbors:
                if neighbor_id not in resilient_nodes:
                    continue
                fragile_arc = district_by_id[district_id].get('arc_state') or {}
                resilient_arc = district_by_id[neighbor_id].get('arc_state') or {}
                fragile_ripple = (district_by_id[district_id].get('derived_summary') or {}).get('ripple_context') or {}
                fragile_pressure = (
                    float(fragile_arc.get('fragile_recovery_memory', 0.0)) * 0.54
                    + float(fragile_ripple.get('stressed_cluster_share', 0.0)) * 0.26
                    + float(fragile_arc.get('topology_relapse_bias', 0.0)) * 0.2
                )
                resilient_buffer = (
                    float(resilient_arc.get('recovery_durability', 0.0)) * 0.6
                    + float(resilient_arc.get('topology_support_alignment', 0.0)) * 0.4
                )
                bridge_instability_total += max(
                    0.0,
                    (fragile_pressure - resilient_buffer * 0.84)
                    * (0.58 + fragile_neighbor_share * 0.42),
                )
                bridge_count += 1
        topology_bridge_instability = bridge_instability_total / max(1, bridge_count)

        return {
            'topology_corridor_weakness': round(max(0.0, min(1.0, topology_corridor_weakness)), 3),
            'topology_ring_containment': round(max(0.0, min(1.0, topology_ring_containment)), 3),
            'topology_cluster_support_span': round(max(0.0, min(1.0, topology_cluster_support_span)), 3),
            'topology_bridge_instability': round(max(0.0, min(1.0, topology_bridge_instability)), 3),
        }

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
    def _city_regime_state(world_state: dict, districts: list[dict], local_vs_broad_split: dict | None = None) -> dict:
        if not districts:
            return {'phase': 'mixed_transition', 'confidence': 0.0, 'signals': {}, 'regime_shift_candidate': False}
        local_vs_broad_split = local_vs_broad_split or {}
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
        clustered_fragility_pressure = float(local_vs_broad_split.get('clustered_fragility_pressure', 0.0))
        clustered_resilience_support = float(local_vs_broad_split.get('clustered_resilience_support', 0.0))
        clustered_drag_dominance = float(local_vs_broad_split.get('clustered_drag_dominance', 0.0))
        gate_durability_sync = float(local_vs_broad_split.get('gate_durability_sync', 0.0))
        city_headroom = float(local_vs_broad_split.get('citywide_durability_headroom', 0.0))
        broad_drag = float(local_vs_broad_split.get('broad_durability_drag', 0.0))
        local_recovery_share = float(local_vs_broad_split.get('local_recovery_share', 0.0))
        spread_gap = float(local_vs_broad_split.get('spread_gap', 0.0))
        uneven_recovery_penalty = float(local_vs_broad_split.get('uneven_recovery_penalty', 0.0))
        topology_recovery_penalty = float(local_vs_broad_split.get('topology_recovery_penalty', 0.0))
        neighborhood_regime_drag = float(local_vs_broad_split.get('neighborhood_regime_drag', 0.0))
        topology_drag_persistence_ticks = int(local_vs_broad_split.get('topology_drag_persistence_ticks', 0))
        topology_support_persistence_ticks = int(local_vs_broad_split.get('topology_support_persistence_ticks', 0))
        topology_drag_soak_intensity = float(local_vs_broad_split.get('topology_drag_soak_intensity', 0.0))
        topology_support_soak_intensity = float(local_vs_broad_split.get('topology_support_soak_intensity', 0.0))
        topology_support_alignment_signal = float(local_vs_broad_split.get('topology_support_alignment_signal', 0.0))
        persistent_cluster_drag = float(local_vs_broad_split.get('persistent_cluster_drag', 0.0))
        persistent_cluster_support = float(local_vs_broad_split.get('persistent_cluster_support', 0.0))
        topology_persistence_balance = float(local_vs_broad_split.get('topology_persistence_balance', 0.0))
        topology_corridor_weakness = float(local_vs_broad_split.get('topology_corridor_weakness', 0.0))
        topology_ring_containment = float(local_vs_broad_split.get('topology_ring_containment', 0.0))
        topology_cluster_support_span = float(local_vs_broad_split.get('topology_cluster_support_span', 0.0))
        topology_bridge_instability = float(local_vs_broad_split.get('topology_bridge_instability', 0.0))

        clustered_recovery_advantage = max(
            0.0,
            min(
                1.0,
                (clustered_resilience_support * 0.58)
                + max(0.0, gate_durability_sync - 0.46) * 0.24
                + max(0.0, topology_support_soak_intensity - 0.28) * 0.26
                - (clustered_fragility_pressure * 0.46)
                - max(0.0, spread_gap - 0.1) * 0.18,
                - max(0.0, topology_persistence_balance - 0.18) * 0.22,
                - max(0.0, topology_drag_soak_intensity - 0.3) * 0.26,
            ),
        )
        if (
            stressed_share >= 0.5
            and (
                avg_pressure >= 0.6
                or clustered_decline >= 0.38
                or clustered_drag_dominance >= 0.22
                or neighborhood_regime_drag >= 0.32
                or topology_drag_persistence_ticks >= 5
                or topology_drag_soak_intensity >= 0.42
                or topology_corridor_weakness >= 0.42
                or topology_ring_containment >= 0.44
                or topology_bridge_instability >= 0.36
            )
        ):
            phase = 'clustered_decline'
        elif (
            stress_cycle >= 0.6
            and (
                avg_momentum >= 0.08
                or broad_drag >= 0.3
                or topology_recovery_penalty >= 0.08
                or topology_persistence_balance >= 0.2
                or topology_drag_soak_intensity >= 0.4
                or topology_bridge_instability >= 0.34
            )
        ):
            phase = 'broad_strain'
        elif (
            recovering_share >= 0.52
            and recovery_durability >= 0.5
            and shallow_recovery <= 0.5
            and clustered_recovery_advantage >= 0.16
            and city_headroom >= 0.34
            and topology_support_soak_intensity >= 0.28
            and topology_support_alignment_signal >= 0.16
            and topology_drag_soak_intensity <= 0.34
            and topology_corridor_weakness <= 0.4
            and topology_bridge_instability <= 0.3
        ):
            phase = 'stabilizing'
        elif recovering_share >= 0.42 and (shallow_recovery > 0.5 or clustered_drag_dominance >= 0.16):
            phase = 'fragile_recovery'
        else:
            phase = 'mixed_transition'
        regime_shift_candidate = (
            abs(avg_momentum) >= 0.1
            or abs(stressed_share - recovering_share) >= 0.25
            or abs(clustered_decline - clustered_recovery) >= 0.22
            or abs(clustered_drag_dominance - clustered_recovery_advantage) >= 0.18
        )
        tipping_thresholds = AuraliteRuntimeService._city_tipping_thresholds(
            phase=phase,
            stressed_share=stressed_share,
            recovering_share=recovering_share,
            avg_pressure=avg_pressure,
            avg_momentum=avg_momentum,
            stress_cycle=stress_cycle,
            recovery_durability=recovery_durability,
            shallow_recovery=shallow_recovery,
            clustered_decline=clustered_decline,
            clustered_recovery=clustered_recovery,
        )
        confidence = min(
            1.0,
            max(
                0.2,
                abs(stressed_share - recovering_share) * 0.7
                + abs(avg_momentum) * 0.9
                + max(clustered_decline, clustered_recovery) * 0.45
                + abs(stress_cycle - recovery_durability) * 0.5,
                + max(0.0, clustered_drag_dominance - clustered_recovery_advantage) * 0.36
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
            'clustered_fragility_pressure': round(clustered_fragility_pressure, 3),
            'clustered_resilience_support': round(clustered_resilience_support, 3),
            'clustered_drag_dominance': round(clustered_drag_dominance, 3),
            'clustered_recovery_advantage': round(clustered_recovery_advantage, 3),
            'citywide_durability_headroom': round(city_headroom, 3),
            'broad_durability_drag': round(broad_drag, 3),
            'local_recovery_share': round(local_recovery_share, 3),
            'spread_gap': round(spread_gap, 3),
            'uneven_recovery_penalty': round(uneven_recovery_penalty, 3),
            'topology_recovery_penalty': round(topology_recovery_penalty, 3),
            'neighborhood_regime_drag': round(neighborhood_regime_drag, 3),
            'topology_drag_persistence_ticks': topology_drag_persistence_ticks,
            'topology_support_persistence_ticks': topology_support_persistence_ticks,
            'topology_drag_soak_intensity': round(topology_drag_soak_intensity, 3),
            'topology_support_soak_intensity': round(topology_support_soak_intensity, 3),
            'topology_support_alignment_signal': round(topology_support_alignment_signal, 3),
            'persistent_cluster_drag': round(persistent_cluster_drag, 3),
            'persistent_cluster_support': round(persistent_cluster_support, 3),
            'topology_persistence_balance': round(topology_persistence_balance, 3),
            'topology_corridor_weakness': round(topology_corridor_weakness, 3),
            'topology_ring_containment': round(topology_ring_containment, 3),
            'topology_cluster_support_span': round(topology_cluster_support_span, 3),
            'topology_bridge_instability': round(topology_bridge_instability, 3),
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
        leverage_points = AuraliteRuntimeService._district_leverage_points(
            world_state=world_state,
            districts=districts,
            lead_lag=lead_lag,
        )
        lever_relevance = AuraliteRuntimeService._intervention_lever_relevance(
            world_state=world_state,
            phase=phase,
            signals=signals,
            lead_lag=lead_lag,
            recovery_spread_state=recovery_spread_state,
            intervention_regime_effect=intervention_regime_effect,
        )
        momentum_management = AuraliteRuntimeService._momentum_management_signals(
            phase=phase,
            signals=signals,
            recovery_spread_state=recovery_spread_state,
            districts=districts,
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
            'tipping_thresholds': tipping_thresholds,
            'interpretation': interpretation,
            'lead_lag_districts': lead_lag,
            'leverage_points': leverage_points,
            'recovery_spread_state': recovery_spread_state,
            'intervention_regime_effect': intervention_regime_effect,
            'intervention_lever_relevance': lever_relevance,
            'momentum_management': momentum_management,
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
    def _bounded_score(value: float) -> float:
        return round(max(0.0, min(1.0, float(value))), 3)

    @staticmethod
    def _city_tipping_thresholds(
        phase: str,
        stressed_share: float,
        recovering_share: float,
        avg_pressure: float,
        avg_momentum: float,
        stress_cycle: float,
        recovery_durability: float,
        shallow_recovery: float,
        clustered_decline: float,
        clustered_recovery: float,
    ) -> dict:
        regime_tipping_risk = AuraliteRuntimeService._bounded_score(
            (stressed_share * 0.28)
            + max(0.0, avg_pressure - 0.54) * 0.9
            + max(0.0, avg_momentum) * 0.65
            + max(0.0, stress_cycle - recovery_durability) * 0.7
            + max(0.0, clustered_decline - clustered_recovery) * 0.4
        )
        fragile_relapse_risk = AuraliteRuntimeService._bounded_score(
            max(0.0, shallow_recovery - 0.5) * 0.72
            + max(0.0, stress_cycle - 0.56) * 0.48
            + max(0.0, clustered_decline - 0.34) * 0.4
            - max(0.0, recovery_durability - 0.54) * 0.45
        )
        clustered_escalation_risk = AuraliteRuntimeService._bounded_score(
            max(0.0, clustered_decline - 0.3) * 0.8
            + max(0.0, stress_cycle - 0.55) * 0.6
            + max(0.0, avg_pressure - 0.56) * 0.5
            + max(0.0, avg_momentum) * 0.35
        )
        proximity = max(regime_tipping_risk, fragile_relapse_risk, clustered_escalation_risk)
        band = 'low'
        if proximity >= 0.67:
            band = 'high'
        elif proximity >= 0.45:
            band = 'medium'
        return {
            'phase_context': phase,
            'overall_proximity': round(proximity, 3),
            'proximity_band': band,
            'city_regime_tipping_risk': regime_tipping_risk,
            'fragile_recovery_relapse_risk': fragile_relapse_risk,
            'clustered_strain_escalation_risk': clustered_escalation_risk,
            'balance_snapshot': {
                'stressed_share': round(stressed_share, 3),
                'recovering_share': round(recovering_share, 3),
            },
        }

    @staticmethod
    def _district_tipping_thresholds(
        phase: str,
        pressure_index: float,
        phase_momentum: float,
        inflection_score: float,
        shallow_recovery_risk: float,
        recovery_durability: float,
        hardship_cluster: float,
        contagion_pressure: float,
        incoming_neighbor_pressure: float,
    ) -> dict:
        district_tipping_risk = AuraliteRuntimeService._bounded_score(
            max(0.0, pressure_index - 0.52) * 0.75
            + max(0.0, phase_momentum) * 0.55
            + max(0.0, hardship_cluster - 0.5) * 0.5
            + max(0.0, contagion_pressure) * 0.45
        )
        relapse_risk = AuraliteRuntimeService._bounded_score(
            max(0.0, shallow_recovery_risk - 0.5) * 0.72
            + max(0.0, phase_momentum) * 0.3
            + max(0.0, incoming_neighbor_pressure) * 6.0
            - max(0.0, recovery_durability - 0.52) * 0.45
            - max(0.0, inflection_score) * 0.22
        )
        escalation_risk = AuraliteRuntimeService._bounded_score(
            max(0.0, contagion_pressure) * 0.6
            + max(0.0, incoming_neighbor_pressure) * 6.5
            + max(0.0, hardship_cluster - 0.52) * 0.44
        )
        return {
            'phase_context': phase,
            'district_tipping_risk': district_tipping_risk,
            'fragile_recovery_relapse_risk': relapse_risk,
            'clustered_strain_escalation_risk': escalation_risk,
            'overall_proximity': round(max(district_tipping_risk, relapse_risk, escalation_risk), 3),
        }

    @staticmethod
    def _district_leverage_points(world_state: dict, districts: list[dict], lead_lag: dict) -> dict:
        by_id = {d.get('district_id'): d for d in districts}
        decline_leaders = []
        recovery_seeds = []
        fragile_bridges = []
        intervention_sensitive = []
        active_aftermath = world_state.get('intervention_state', {}).get('active_aftermath', []) or []
        targeted_counts = {}
        for row in active_aftermath:
            district_id = row.get('district_id')
            if not district_id:
                continue
            targeted_counts[district_id] = targeted_counts.get(district_id, 0) + 1

        for row in lead_lag.get('decline_leaders', []) or []:
            district = by_id.get(row.get('district_id'), {})
            ripple = ((district.get('derived_summary') or {}).get('ripple_context') or {})
            leverage_score = AuraliteRuntimeService._bounded_score(
                float(row.get('score', 0.0)) * 0.5
                + max(0.0, float(ripple.get('contagion_vector', 0.0))) * 0.35
                + max(0.0, float((district.get('arc_state') or {}).get('cumulative_stress_load', 0.0)) - 0.54) * 0.35
            )
            decline_leaders.append({
                'district_id': row.get('district_id'),
                'name': row.get('name'),
                'leverage_score': leverage_score,
                'why': 'Decline momentum is transmitting into neighboring districts.',
            })

        for row in lead_lag.get('recovery_leaders', []) or []:
            district = by_id.get(row.get('district_id'), {})
            ripple = ((district.get('derived_summary') or {}).get('ripple_context') or {})
            leverage_score = AuraliteRuntimeService._bounded_score(
                float(row.get('score', 0.0)) * 0.48
                + max(0.0, float(ripple.get('recovery_vector', 0.0))) * 0.42
                + max(0.0, float((district.get('arc_state') or {}).get('recovery_durability', 0.0)) - 0.46) * 0.32
            )
            recovery_seeds.append({
                'district_id': row.get('district_id'),
                'name': row.get('name'),
                'leverage_score': leverage_score,
                'why': 'Recovery conditions appear able to diffuse into adjacent zones.',
            })

        for district in districts:
            ripple = ((district.get('derived_summary') or {}).get('ripple_context') or {})
            contagion = abs(float(ripple.get('contagion_vector', 0.0)))
            recovery = abs(float(ripple.get('recovery_vector', 0.0)))
            incoming = abs(float(ripple.get('incoming_neighbor_pressure', 0.0)))
            if incoming >= 0.016 and contagion >= 0.12 and recovery >= 0.08:
                score = AuraliteRuntimeService._bounded_score(contagion * 0.45 + recovery * 0.25 + incoming * 9.0)
                fragile_bridges.append({
                    'district_id': district.get('district_id'),
                    'name': district.get('name'),
                    'leverage_score': score,
                    'why': 'District is bridging stressed and recovering clusters.',
                })

            if targeted_counts.get(district.get('district_id'), 0) > 0:
                score = AuraliteRuntimeService._bounded_score(
                    min(0.75, targeted_counts.get(district.get('district_id'), 0) * 0.18)
                    + max(0.0, float((district.get('arc_state') or {}).get('phase_momentum', 0.0))) * 0.24
                    + max(0.0, float((district.get('arc_state') or {}).get('inflection_score', 0.0))) * 0.2
                )
                intervention_sensitive.append({
                    'district_id': district.get('district_id'),
                    'name': district.get('name'),
                    'leverage_score': score,
                    'why': 'District has active intervention aftermath and regime-sensitive movement.',
                })

        sorter = lambda rows: sorted(rows, key=lambda x: (-float(x.get('leverage_score', 0.0)), str(x.get('district_id', ''))))[:4]
        return {
            'high_impact_decline_leaders': sorter(decline_leaders),
            'high_impact_recovery_seeds': sorter(recovery_seeds),
            'fragile_bridge_districts': sorter(fragile_bridges),
            'intervention_sensitive_districts': sorter(intervention_sensitive),
        }

    @staticmethod
    def _intervention_lever_relevance(
        world_state: dict,
        phase: str,
        signals: dict,
        lead_lag: dict,
        recovery_spread_state: dict,
        intervention_regime_effect: dict,
    ) -> dict:
        available = (world_state.get('intervention_state') or {}).get('available_levers') or []
        stressed_share = float(signals.get('stressed_share', 0.0))
        avg_pressure = float(signals.get('avg_pressure', 0.0))
        avg_drift = float(signals.get('avg_institution_drift', 0.0))
        shallow = float(signals.get('shallow_recovery_risk', 0.0))
        effect_signal = intervention_regime_effect.get('signal', 'no_active_intervention_signal')
        lane = recovery_spread_state.get('lane', 'mixed')
        local_only = effect_signal in {'local_pocket_shift_only', 'failing_to_influence_regime'}

        def classify(score: float, local_bias: bool = False) -> str:
            if local_bias and score < 0.62:
                return 'likely_local_only'
            if score >= 0.68:
                return 'high_relevance'
            if score >= 0.42:
                return 'medium_relevance'
            return 'low_relevance'

        lever_rows = {}
        if 'rebalance_housing_pressure' in available:
            score = AuraliteRuntimeService._bounded_score(stressed_share * 0.42 + max(0.0, avg_pressure - 0.54) * 0.75 + max(0.0, shallow - 0.5) * 0.35)
            lever_rows['rebalance_housing_pressure'] = {
                'relevance': classify(score, local_bias=local_only),
                'score': score,
                'evidence': [
                    f"stressed_share={stressed_share:.2f}",
                    f"avg_pressure={avg_pressure:.2f}",
                    f"shallow_recovery_risk={shallow:.2f}",
                ],
            }
        if 'boost_transit_service' in available:
            decline_count = len(lead_lag.get('decline_leaders', []) or [])
            score = AuraliteRuntimeService._bounded_score(max(0.0, avg_drift) * 0.42 + min(0.5, decline_count * 0.08) + (0.16 if phase in {'clustered_decline', 'broad_strain'} else 0.05))
            lever_rows['boost_transit_service'] = {
                'relevance': classify(score, local_bias=local_only and lane in {'stalled', 'mixed'}),
                'score': score,
                'evidence': [
                    f"institution_drift={avg_drift:.2f}",
                    f"decline_leaders={decline_count}",
                    f"phase={phase}",
                ],
            }
        if 'expand_service_access' in available:
            score = AuraliteRuntimeService._bounded_score(max(0.0, avg_pressure - 0.5) * 0.35 + max(0.0, shallow - 0.48) * 0.4 + (0.18 if lane in {'stalled', 'reversing_under_stress'} else 0.08))
            lever_rows['expand_service_access'] = {
                'relevance': classify(score, local_bias=local_only),
                'score': score,
                'evidence': [
                    f"recovery_lane={lane}",
                    f"shallow_recovery_risk={shallow:.2f}",
                    f"effect_signal={effect_signal}",
                ],
            }
        return {
            'phase_context': phase,
            'effect_signal': effect_signal,
            'levers': lever_rows,
        }

    @staticmethod
    def _district_momentum_management(
        phase: str,
        phase_momentum: float,
        inflection_score: float,
        recovery_durability: float,
        shallow_recovery_risk: float,
        cumulative_stress_load: float,
        hardship_cluster: float,
    ) -> dict:
        if phase in {'stabilizing', 'recovering'} and recovery_durability >= 0.55 and shallow_recovery_risk <= 0.44 and inflection_score >= 0.12:
            label = 'durable_positive_momentum'
        elif phase in {'stabilizing', 'recovering'} and (shallow_recovery_risk >= 0.54 or recovery_durability <= 0.44):
            label = 'fragile_positive_momentum'
        elif phase == 'steady' and abs(phase_momentum) <= 0.08 and abs(inflection_score) <= 0.1:
            label = 'stalled_improvement'
        elif phase in {'tightening', 'strained'} and (phase_momentum >= 0.2 or cumulative_stress_load >= 0.62):
            label = 'entrenched_decline_momentum'
        else:
            label = 'mixed_transition_momentum'
        return {
            'signal': label,
            'phase_momentum': round(phase_momentum, 3),
            'inflection_score': round(inflection_score, 3),
            'recovery_durability': round(recovery_durability, 3),
            'shallow_recovery_risk': round(shallow_recovery_risk, 3),
            'cumulative_stress_load': round(cumulative_stress_load, 3),
            'hardship_cluster': round(hardship_cluster, 3),
        }

    @staticmethod
    def _momentum_management_signals(phase: str, signals: dict, recovery_spread_state: dict, districts: list[dict]) -> dict:
        buckets = {
            'durable_positive_momentum': [],
            'fragile_positive_momentum': [],
            'stalled_improvement': [],
            'entrenched_decline_momentum': [],
            'mixed_transition_momentum': [],
        }
        for district in districts:
            state = (district.get('arc_state') or {}).get('momentum_management') or {}
            signal = state.get('signal', 'mixed_transition_momentum')
            buckets.setdefault(signal, []).append({
                'district_id': district.get('district_id'),
                'name': district.get('name'),
                'phase': district.get('state_phase'),
            })
        lane = recovery_spread_state.get('lane', 'mixed')
        city_signal = 'mixed_transition_momentum'
        if phase == 'stabilizing' and lane == 'spreading' and float(signals.get('recovery_durability', 0.0)) >= 0.52:
            city_signal = 'durable_positive_momentum'
        elif phase in {'fragile_recovery', 'mixed_transition'} and float(signals.get('shallow_recovery_risk', 0.0)) >= 0.54:
            city_signal = 'fragile_positive_momentum'
        elif phase in {'clustered_decline', 'broad_strain'} and float(signals.get('avg_phase_momentum', 0.0)) >= 0.1:
            city_signal = 'entrenched_decline_momentum'
        elif lane == 'stalled':
            city_signal = 'stalled_improvement'
        return {
            'city_signal': city_signal,
            'phase_context': phase,
            'bucket_counts': {k: len(v) for k, v in buckets.items()},
            'durable_positive_districts': buckets.get('durable_positive_momentum', [])[:5],
            'fragile_positive_districts': buckets.get('fragile_positive_momentum', [])[:5],
            'stalled_improvement_districts': buckets.get('stalled_improvement', [])[:5],
            'entrenched_decline_districts': buckets.get('entrenched_decline_momentum', [])[:5],
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
        arc = (institution or {}).get('arc_state') or {}
        backlog = max(0.0, min(1.0, float(arc.get('service_backlog', 0.0))))
        fatigue = max(0.0, min(1.0, float(arc.get('overload_fatigue', 0.0))))
        responsiveness = max(0.05, min(1.0, float(arc.get('responsiveness_index', access))))

        profile = {
            'utilization': round(utilization, 3),
            'utilization_pressure': round(utilization_pressure, 3),
            'capacity_scale': round(bounded_scale, 3),
            'access_drag': max(0.0, min(1.0, (1.0 - access) + backlog * 0.24 + fatigue * 0.18 - responsiveness * 0.08)),
            'service_backlog': round(backlog, 3),
            'overload_fatigue': round(fatigue, 3),
            'responsiveness': round(responsiveness, 3),
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
    def _city_causal_diagnostics(world_state: dict, districts: list[dict], backlog_index: float, delayed_recovery_pressure: float) -> dict:
        ripple_rows = [((district.get('derived_summary') or {}).get('ripple_context') or {}) for district in districts]
        ripple_intensity = (
            sum(abs(float(row.get('ripple_effect', 0.0))) for row in ripple_rows) / max(1, len(ripple_rows))
        )
        containment = (
            sum(float(row.get('containment_capacity', 0.0)) for row in ripple_rows) / max(1, len(ripple_rows))
        )
        local_fragile_recovery = sum(
            1
            for district in districts
            if district.get('state_phase') in {'stabilizing', 'recovering'}
            and float((district.get('arc_state') or {}).get('shallow_recovery_risk', 1.0)) >= 0.52
        )
        stressed_count = sum(1 for district in districts if float(district.get('pressure_index', 0.0)) >= 0.62)
        return {
            'spillover_intensity': round(ripple_intensity, 3),
            'containment_capacity': round(containment, 3),
            'service_backlog_index': round(backlog_index, 3),
            'delayed_recovery_pressure': round(delayed_recovery_pressure, 3),
            'local_fragile_recovery_count': int(local_fragile_recovery),
            'stressed_district_count': int(stressed_count),
            'citywide_regime_recovery_blocked': bool(local_fragile_recovery > 0 and stressed_count >= 2),
            'note': 'Tracks whether local gains remain fragile under backlog, spillover, and threshold drag.',
        }

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
        interaction_bonus = 0.0
        interaction_penalty = 0.0
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
            targeted = ((record.get('effects') or {}).get('targeted_aftermath') or {})
            trace = targeted.get('interaction_trace') or {}
            interaction_bonus += float(trace.get('synergy_bonus', 0.0)) * weight
            interaction_penalty += float(trace.get('conflict_penalty', 0.0)) * weight
        amplitude = min(1.0, weighted / max(total_weight, 1.0))
        net_interaction = max(-0.25, min(0.25, (interaction_bonus - interaction_penalty) / max(total_weight, 1.0)))
        amplitude = max(0.0, min(1.0, amplitude * (1.0 + net_interaction)))
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
            'interaction_net': round(net_interaction, 3),
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
