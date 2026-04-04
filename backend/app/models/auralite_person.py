from dataclasses import dataclass, field


@dataclass
class AuralitePerson:
    person_id: str
    name: str
    age: int
    district_id: str
    household_id: str
    occupation: str
    home_location_id: str
    work_location_id: str | None
    current_location_id: str
    current_activity: str
    routine_type: str
    employment_status: str = "employed"
    hourly_wage: float = 0.0
    housing_burden_share: float = 0.0
    shift_window: str = "day"
    employer_id: str | None = None
    transit_service_id: str | None = None
    service_provider_id: str | None = None
    service_access_score: float = 0.5
    social_ties: list[dict] = field(default_factory=list)
    social_context: dict = field(default_factory=dict)
    state_summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "person_id": self.person_id,
            "name": self.name,
            "age": self.age,
            "district_id": self.district_id,
            "household_id": self.household_id,
            "occupation": self.occupation,
            "home_location_id": self.home_location_id,
            "work_location_id": self.work_location_id,
            "current_location_id": self.current_location_id,
            "current_activity": self.current_activity,
            "routine_type": self.routine_type,
            "employment_status": self.employment_status,
            "hourly_wage": self.hourly_wage,
            "housing_burden_share": self.housing_burden_share,
            "shift_window": self.shift_window,
            "employer_id": self.employer_id,
            "transit_service_id": self.transit_service_id,
            "service_provider_id": self.service_provider_id,
            "service_access_score": self.service_access_score,
            "social_ties": self.social_ties,
            "social_context": self.social_context,
            "state_summary": self.state_summary,
        }
