from datetime import datetime
from ..models.auralite_world import AuraliteWorld
from .auralite_seed_service import AuraliteSeedService
from .auralite_runtime_service import AuraliteRuntimeService
from .auralite_persistence_service import AuralitePersistenceService


class AuraliteWorldService:
    WORLD_ID = 'auralite_world_v1'

    def __init__(self):
        self.seed_service = AuraliteSeedService(seed=42)

    def get_or_create_world(self) -> dict:
        world = AuralitePersistenceService.load_world(self.WORLD_ID)
        if world:
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
        }
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

    def _auto_advance(self, world: dict) -> dict:
        if not world['world']['is_running']:
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
