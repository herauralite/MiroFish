from flask import jsonify, request

from . import auralite_bp
from ..services.auralite_persistence_service import AuralitePersistenceService
from ..services.auralite_world_service import AuraliteWorldService


service = AuraliteWorldService()


@auralite_bp.route('/world', methods=['GET'])
def get_world():
    world = service.get_or_create_world()
    return jsonify({'success': True, 'data': world})


@auralite_bp.route('/world/reset', methods=['POST'])
def reset_world():
    payload = request.get_json(silent=True) or {}
    population_target = int(payload.get('population_target', 240))
    world = service.reset_world(population_target=population_target)
    return jsonify({'success': True, 'data': world})


@auralite_bp.route('/world/save', methods=['POST'])
def save_world():
    payload = request.get_json(silent=True) or {}
    world = service.get_or_create_world()
    snapshot_id = AuralitePersistenceService.save_snapshot(service.WORLD_ID, world, payload.get('snapshot_id'))
    return jsonify({'success': True, 'data': {'snapshot_id': snapshot_id}})


@auralite_bp.route('/world/load', methods=['POST'])
def load_world_snapshot():
    payload = request.get_json(silent=True) or {}
    snapshot_id = payload.get('snapshot_id')
    if not snapshot_id:
        return jsonify({'success': False, 'error': 'snapshot_id is required'}), 400
    snapshot = AuralitePersistenceService.load_snapshot(service.WORLD_ID, snapshot_id)
    if not snapshot:
        return jsonify({'success': False, 'error': 'snapshot not found'}), 404
    service.save_world_payload(snapshot)
    return jsonify({'success': True, 'data': snapshot})


@auralite_bp.route('/runtime/control', methods=['POST'])
def control_runtime():
    payload = request.get_json(silent=True) or {}
    action = payload.get('action', '')
    time_speed = payload.get('time_speed')
    if action not in ['start', 'pause', 'speed']:
        return jsonify({'success': False, 'error': 'action must be start|pause|speed'}), 400
    world = service.control_runtime(action=action, time_speed=time_speed)
    return jsonify({'success': True, 'data': world['world']})


@auralite_bp.route('/runtime/tick', methods=['POST'])
def runtime_tick():
    payload = request.get_json(silent=True) or {}
    minutes = int(payload.get('minutes', 15))
    world = service.manual_tick(minutes)
    return jsonify({'success': True, 'data': world})


@auralite_bp.route('/interventions/apply', methods=['POST'])
def apply_intervention_changes():
    payload = request.get_json(silent=True) or {}
    changes = payload.get('changes', [])
    notes = payload.get('notes', '')
    if not isinstance(changes, list) or not changes:
        return jsonify({'success': False, 'error': 'changes array is required'}), 400

    result = service.apply_interventions(changes=changes, notes=notes)
    return jsonify({'success': True, 'data': result})


@auralite_bp.route('/districts/<district_id>', methods=['GET'])
def get_district(district_id: str):
    world = service.get_or_create_world()
    district = next((d for d in world['districts'] if d['district_id'] == district_id), None)
    if not district:
        return jsonify({'success': False, 'error': 'district not found'}), 404

    residents = [p for p in world['persons'] if p['district_id'] == district_id]
    households = [h for h in world['households'] if h['district_id'] == district_id]
    institutions = [i for i in world.get('institutions', []) if i['district_id'] == district_id]
    household_pressure = round(sum(h.get('pressure_index', 0.0) for h in households) / max(1, len(households)), 3)

    return jsonify({
        'success': True,
        'data': {
            'district': district,
            'resident_count': len(residents),
            'household_count': len(households),
            'institution_count': len(institutions),
            'household_pressure_index': household_pressure,
            'institution_summary': district.get('institution_summary', {}),
            'derived_summary': district.get('derived_summary', {}),
        },
    })


@auralite_bp.route('/residents/<person_id>', methods=['GET'])
def get_resident(person_id: str):
    world = service.get_or_create_world()
    person = next((p for p in world['persons'] if p['person_id'] == person_id), None)
    if not person:
        return jsonify({'success': False, 'error': 'resident not found'}), 404

    household = next((h for h in world['households'] if h['household_id'] == person['household_id']), None)
    district = next((d for d in world['districts'] if d['district_id'] == person['district_id']), None)
    institutions = {
        'employer': next((i for i in world.get('institutions', []) if i['institution_id'] == person.get('employer_id')), None),
        'transit': next((i for i in world.get('institutions', []) if i['institution_id'] == person.get('transit_service_id')), None),
        'service_provider': next((i for i in world.get('institutions', []) if i['institution_id'] == person.get('service_provider_id')), None),
        'landlord': next((i for i in world.get('institutions', []) if i['institution_id'] == (household or {}).get('landlord_id')), None),
    }
    return jsonify({'success': True, 'data': {'resident': person, 'household': household, 'district': district, 'institutions': institutions}})
