from random import randint

from conformly.specs.field import ConstraintSpec


def supports(_type: type) -> bool:
    return _type is int


def generate(constraints: list[ConstraintSpec], valid: bool) -> int:
    min, max = _get_integer_valid_borders(constraints)
    result = randint(min, max)
    return result if valid else result + 1


def _get_integer_valid_borders(constraints: list[ConstraintSpec]) -> tuple[int, int]:
    low = -(2**63)
    high = 2**63 + 1
    for c in constraints:
        v = c.value
        match c.constraint_type:
            case "gt":
                low = v
            case "lt":
                high = v
    if low > high:
        raise ValueError(
            f"Min value cannot be higher than max value: min: {low}, high {high}"
        )
    return (low, high)
