from dataclasses import dataclass, field


@dataclass
class AuraliteInstitution:
    institution_id: str
    district_id: str
    name: str
    institution_type: str
    capacity: int
    access_score: float = 0.5
    pressure_index: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "institution_id": self.institution_id,
            "district_id": self.district_id,
            "name": self.name,
            "institution_type": self.institution_type,
            "capacity": self.capacity,
            "access_score": self.access_score,
            "pressure_index": self.pressure_index,
            "metadata": self.metadata,
        }
