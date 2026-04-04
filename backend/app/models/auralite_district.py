from dataclasses import dataclass, field


@dataclass
class AuraliteDistrict:
    district_id: str
    name: str
    archetype: str
    summary: str
    map_region_key: str
    population_count: int
    housing_profile: dict = field(default_factory=dict)
    activity_profile: dict = field(default_factory=dict)
    current_activity_level: float = 0.0

    def to_dict(self) -> dict:
        return {
            "district_id": self.district_id,
            "name": self.name,
            "archetype": self.archetype,
            "summary": self.summary,
            "map_region_key": self.map_region_key,
            "population_count": self.population_count,
            "housing_profile": self.housing_profile,
            "activity_profile": self.activity_profile,
            "current_activity_level": self.current_activity_level,
        }
