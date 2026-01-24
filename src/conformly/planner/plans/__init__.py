from .boolean import BooleanGeneration, BooleanViolation
from .numeric import NumericGeneration, NumericViolation
from .object import ObjectGeneration, ObjectViolation
from .string import StringGeneration, StringViolation

GenerationPlan = (
    NumericGeneration | StringGeneration | ObjectGeneration | BooleanGeneration
)
ViolationPlan = NumericViolation | StringViolation | ObjectViolation | BooleanViolation


__all__ = ["GenerationPlan", "ViolationPlan"]
