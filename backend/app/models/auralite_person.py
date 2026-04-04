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
            "state_summary": self.state_summary,
        }
