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
    pressure_index: float = 0.0
    employment_rate: float = 0.0
    average_hourly_wage: float = 0.0
    average_housing_burden: float = 0.0
    state_phase: str = "steady"
    derived_summary: dict = field(default_factory=dict)

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
            "pressure_index": self.pressure_index,
            "employment_rate": self.employment_rate,
            "average_hourly_wage": self.average_hourly_wage,
            "average_housing_burden": self.average_housing_burden,
            "state_phase": self.state_phase,
            "derived_summary": self.derived_summary,
        }
