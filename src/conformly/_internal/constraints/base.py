from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Constraint:
    """Marker base class for constraints"""
