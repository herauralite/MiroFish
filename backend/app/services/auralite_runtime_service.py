from datetime import datetime, timedelta


class AuraliteRuntimeService:
    @staticmethod
    def tick(world_state: dict, elapsed_minutes: int):
        current_time = datetime.fromisoformat(world_state['world']['current_time'])
        current_time += timedelta(minutes=elapsed_minutes)
        world_state['world']['current_time'] = current_time.isoformat()
        world_state['world']['updated_at'] = datetime.utcnow().isoformat()

        hour = current_time.hour
        district_activity = {d['district_id']: 0 for d in world_state['districts']}
        district_working = {d['district_id']: 0 for d in world_state['districts']}
        district_pressure = {d['district_id']: [] for d in world_state['districts']}
        district_wages = {d['district_id']: [] for d in world_state['districts']}

        households_by_id = {h['household_id']: h for h in world_state['households']}

        for person in world_state['persons']:
            household = households_by_id.get(person['household_id'], {})
            person['housing_burden_share'] = round(
                max(person.get('housing_burden_share', 0.0), household.get('housing_cost_burden', 0.0)),
                3,
            )
            person['state_summary'] = person.get('state_summary', {})
            person['state_summary']['stress'] = round(
                min(1.0, person['housing_burden_share'] * 1.2 + (0.15 if person.get('employment_status') != 'employed' else 0.0)),
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
            district_wages[district_id].append(person.get('hourly_wage', 0.0))

        AuraliteRuntimeService._update_districts(world_state, hour, district_activity, district_working, district_pressure, district_wages)
        AuraliteRuntimeService._update_city_metrics(world_state, hour)
        return world_state

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
    def _update_districts(world_state: dict, hour: int, district_activity: dict, district_working: dict, district_pressure: dict, district_wages: dict):
        total_people = max(1, len(world_state['persons']))
        households = world_state.get('households', [])

        for district in world_state['districts']:
            district_id = district['district_id']
            residents = [p for p in world_state['persons'] if p['district_id'] == district_id]
            resident_count = max(1, len(residents))
            district_households = [h for h in households if h['district_id'] == district_id]

            raw_activity = district_activity[district_id] / total_people
            peak_bonus = 0.12 if district.get('activity_profile', {}).get('peak_hour') == hour else 0.0
            district['current_activity_level'] = round(min(1.0, raw_activity * 5 + peak_bonus), 3)

            employment_rate = sum(1 for p in residents if p.get('employment_status') == 'employed') / resident_count
            avg_wage = sum(max(0.0, p.get('hourly_wage', 0.0)) for p in residents) / resident_count
            avg_burden = sum(district_pressure[district_id]) / resident_count
            household_pressure = (
                sum(h.get('pressure_index', 0.0) for h in district_households) / max(1, len(district_households))
            )
            pressure_index = min(1.0, (avg_burden * 0.55) + (1 - employment_rate) * 0.3 + household_pressure * 0.15)

            district['employment_rate'] = round(employment_rate, 3)
            district['average_hourly_wage'] = round(avg_wage, 2)
            district['average_housing_burden'] = round(avg_burden, 3)
            district['pressure_index'] = round(pressure_index, 3)
            district['state_phase'] = AuraliteRuntimeService._phase_for_pressure(pressure_index, district['current_activity_level'])
            district['derived_summary'] = {
                'resident_count': len(residents),
                'active_workers': district_working[district_id],
                'avg_hourly_wage': district['average_hourly_wage'],
                'avg_housing_burden': district['average_housing_burden'],
                'household_pressure_index': round(household_pressure, 3),
                'pressure_index': district['pressure_index'],
                'state_phase': district['state_phase'],
                'evolution_hook': {
                    'next_update_window': 'weekly',
                    'risk': 'elevated' if pressure_index >= 0.62 else 'stable',
                },
            }

    @staticmethod
    def _update_city_metrics(world_state: dict, hour: int):
        persons = world_state['persons']
        households = world_state.get('households', [])
        employed = [p for p in persons if p.get('employment_status') == 'employed']

        world_state['city']['world_metrics'] = {
            'hour': hour,
            'active_residents': sum(1 for p in persons if p['current_activity'] not in ['home', 'return_home', 'sleep_recovery']),
            'employment_rate': round(len(employed) / max(1, len(persons)), 3),
            'avg_hourly_wage': round(sum(p.get('hourly_wage', 0.0) for p in employed) / max(1, len(employed)), 2),
            'avg_housing_burden': round(sum(h.get('housing_cost_burden', 0.0) for h in households) / max(1, len(households)), 3),
            'household_pressure_index': round(sum(h.get('pressure_index', 0.0) for h in households) / max(1, len(households)), 3),
            'district_state_overview': {
                'stressed': sum(1 for d in world_state['districts'] if d.get('pressure_index', 0.0) >= 0.62),
                'stabilizing': sum(1 for d in world_state['districts'] if d.get('state_phase') == 'stabilizing'),
            },
        }

    @staticmethod
    def _phase_for_pressure(pressure_index: float, activity_level: float) -> str:
        if pressure_index >= 0.72:
            return 'strained'
        if pressure_index >= 0.58:
            return 'stabilizing' if activity_level > 0.65 else 'tightening'
        return 'steady'
