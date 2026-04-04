from dataclasses import dataclass, field


@dataclass
class AuraliteCity:
    city_id: str
    name: str
    district_ids: list[str]
    population_count: int
    world_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "city_id": self.city_id,
            "name": self.name,
            "district_ids": self.district_ids,
            "population_count": self.population_count,
            "world_metrics": self.world_metrics,
        }
