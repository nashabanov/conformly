from typing import Literal

STRING_CONSTRAINTS = frozenset({"min_length", "max_length", "pattern"})

NUMERIC_CONSTRAINTS = frozenset({"gt", "ge", "lt", "le", "multiple_of"})

COLLECTION_CONSTRAINTS = frozenset({"min_items", "max_items", "unique_items"})


ALLOWED_CONSTRAINT_TYPE = (
    STRING_CONSTRAINTS | NUMERIC_CONSTRAINTS | COLLECTION_CONSTRAINTS
)

ConstraintType = Literal[
    "min_length",
    "max_length",
    "pattern",
    "gt",
    "ge",
    "lt",
    "le",
    "multiple_of",
    "min_items",
    "max_items",
    "unique_items",
]
