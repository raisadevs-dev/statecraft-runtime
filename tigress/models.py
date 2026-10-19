from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any


class EventType(str, Enum):
    SUPPORTIVE_ADVICE = "SUPPORTIVE_ADVICE"
    REASONABLE_REQUEST = "REASONABLE_REQUEST"
    UNJUSTIFIED_RESTRICTION = "UNJUSTIFIED_RESTRICTION"
    DISRESPECT = "DISRESPECT"
    HONEST_MISTAKE = "HONEST_MISTAKE"
    REPEATED_HARM = "REPEATED_HARM"
    GENUINE_APOLOGY = "GENUINE_APOLOGY"
    ACCOUNTABILITY_WITH_CHANGE = "ACCOUNTABILITY_WITH_CHANGE"
    BOUNDARY_RESPECTED = "BOUNDARY_RESPECTED"
    UNCLEAR = "UNCLEAR"


@dataclass
class CharacterState:
    trust: float = 0.75
    emotional_safety: float = 0.80
    autonomy: float = 0.85
    hurt: float = 0.10
    openness: float = 0.90
    defensiveness: float = 0.15
    interaction_count: int = 0
    harmful_pattern_count: int = 0
    accountable_change_count: int = 0

    def clamp(self) -> None:
        for name in (
            "trust", "emotional_safety", "autonomy", "hurt",
            "openness", "defensiveness"
        ):
            setattr(self, name, max(0.0, min(1.0, float(getattr(self, name)))))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CharacterState":
        allowed = cls.__dataclass_fields__.keys()
        state = cls(**{k: v for k, v in data.items() if k in allowed})
        state.clamp()
        return state


@dataclass
class Event:
    event_type: EventType
    description: str = ""
    evidence_strength: float = 0.6
    context_known: bool = True
    other_person_respected_boundary: bool = False

    def __post_init__(self) -> None:
        self.evidence_strength = max(0.0, min(1.0, float(self.evidence_strength)))
