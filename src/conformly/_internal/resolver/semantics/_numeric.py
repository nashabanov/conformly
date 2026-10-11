from fractions import Fraction
import math


def integer_multiple_step(divisor: int | float) -> int:
    """Integer multiples of a decimal rational are multiples of its numerator."""
    return Fraction(str(divisor)).numerator


def is_float_multiple(value: float, divisor: float) -> bool:
    """Accept a quotient within 1e-9 of an integer, without relative tolerance."""
    quotient = value / divisor
    return math.isfinite(quotient) and math.isclose(
        quotient, round(quotient), rel_tol=0.0, abs_tol=1e-9
    )
