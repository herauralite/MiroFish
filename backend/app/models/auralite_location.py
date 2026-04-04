from dataclasses import dataclass


@dataclass
class AuraliteLocation:
    location_id: str
    district_id: str
    name: str
    type: str
    capacity: int
    x: float
    y: float

    def to_dict(self) -> dict:
        return {
            "location_id": self.location_id,
            "district_id": self.district_id,
            "name": self.name,
            "type": self.type,
            "capacity": self.capacity,
            "x": self.x,
            "y": self.y,
        }
