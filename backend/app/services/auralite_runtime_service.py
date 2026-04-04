from datetime import datetime, timedelta


class AuraliteRuntimeService:
    @staticmethod
    def tick(world_state: dict, elapsed_minutes: int):
        current_time = datetime.fromisoformat(world_state['world']['current_time'])
        current_time += timedelta(minutes=elapsed_minutes)
        world_state['world']['current_time'] = current_time.isoformat()
        world_state['world']['updated_at'] = datetime.utcnow().isoformat()

        hour = current_time.hour
        locations = {loc['location_id']: loc for loc in world_state['locations']}
        district_activity = {d['district_id']: 0 for d in world_state['districts']}

        for person in world_state['persons']:
            if 7 <= hour < 9:
                target = person['work_location_id'] or person['home_location_id']
                activity = 'commute'
            elif 9 <= hour < 17:
                target = person['work_location_id'] or person['home_location_id']
                activity = 'work' if person['work_location_id'] else 'local_errands'
            elif 17 <= hour < 21:
                target = person['home_location_id']
                activity = 'return_home'
            else:
                target = person['home_location_id']
                activity = 'home'

            if person['routine_type'] == 'shift' and (hour >= 20 or hour < 2):
                target = person['work_location_id'] or person['home_location_id']
                activity = 'night_shift'
            elif person['routine_type'] == 'local' and 12 <= hour < 15:
                leisure = [l for l in world_state['locations'] if l['district_id'] == person['district_id'] and l['type'] == 'leisure']
                if leisure:
                    target = leisure[0]['location_id']
                    activity = 'leisure'

            person['current_location_id'] = target
            person['current_activity'] = activity
            district_activity[person['district_id']] += 1

        total = max(1, len(world_state['persons']))
        for district in world_state['districts']:
            raw = district_activity[district['district_id']] / total
            peak_bonus = 0.15 if district['activity_profile'].get('peak_hour') == hour else 0.0
            district['current_activity_level'] = round(min(1.0, raw * 5 + peak_bonus), 3)

        world_state['city']['world_metrics'] = {
            'active_residents': sum(1 for p in world_state['persons'] if p['current_activity'] not in ['home', 'return_home']),
            'hour': hour,
        }
        return world_state
