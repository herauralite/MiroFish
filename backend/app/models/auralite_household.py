from dataclasses import dataclass


@dataclass
class AuraliteHousehold:
    household_id: str
    district_id: str
    home_location_id: str
    member_ids: list[str]
    household_type: str

    def to_dict(self) -> dict:
        return {
            "household_id": self.household_id,
            "district_id": self.district_id,
            "home_location_id": self.home_location_id,
            "member_ids": self.member_ids,
            "household_type": self.household_type,
        }
