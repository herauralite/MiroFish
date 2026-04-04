from dataclasses import dataclass, field


@dataclass
class AuraliteInterventionRecord:
    intervention_id: str
    applied_at: str
    change_count: int
    notes: str = ""
    effects: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "intervention_id": self.intervention_id,
            "applied_at": self.applied_at,
            "change_count": self.change_count,
            "notes": self.notes,
            "effects": self.effects,
        }
