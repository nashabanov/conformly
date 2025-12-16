from typing import Literal

STRING_CONSTRAINTS = frozenset({"min_length", "max_length", "pattern"})

NUMERIC_CONSTRAINTS = frozenset({"gt", "ge", "lt", "le"})


ALLOWED_CONSTRAINT_TYPE = STRING_CONSTRAINTS | NUMERIC_CONSTRAINTS

# only for type hints
ConstraintType = Literal[
    "min_length",
    "max_length",
    "pattern",
    "gt",
    "ge",
    "lt",
    "le",
]
