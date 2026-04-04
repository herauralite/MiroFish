from dataclasses import dataclass, field


@dataclass
class AuraliteHousehold:
    household_id: str
    district_id: str
    home_location_id: str
    member_ids: list[str]
    household_type: str
    monthly_income: float = 0.0
    monthly_rent: float = 0.0
    housing_cost_burden: float = 0.0
    pressure_level: str = "stable"
    pressure_index: float = 0.0
    landlord_id: str | None = None
    eviction_risk: float = 0.0
    context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "household_id": self.household_id,
            "district_id": self.district_id,
            "home_location_id": self.home_location_id,
            "member_ids": self.member_ids,
            "household_type": self.household_type,
            "monthly_income": self.monthly_income,
            "monthly_rent": self.monthly_rent,
            "housing_cost_burden": self.housing_cost_burden,
            "pressure_level": self.pressure_level,
            "pressure_index": self.pressure_index,
            "landlord_id": self.landlord_id,
            "eviction_risk": self.eviction_risk,
            "context": self.context,
        }
