from dataclasses import dataclass


@dataclass
class AuraliteWorld:
    world_id: str
    city_id: str
    current_time: str
    time_speed: float
    is_running: bool
    created_at: str
    updated_at: str
    seed: int = 42
    last_tick_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "world_id": self.world_id,
            "city_id": self.city_id,
            "current_time": self.current_time,
            "time_speed": self.time_speed,
            "is_running": self.is_running,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "seed": self.seed,
            "last_tick_at": self.last_tick_at,
        }
