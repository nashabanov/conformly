from dataclasses import dataclass


@dataclass(frozen=True)
class Constraint:
    """Marker base class for constraints"""
