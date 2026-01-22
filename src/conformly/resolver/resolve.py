from ..constraints import Constraint
from ..specs import FieldSpec, ModelSpec
from ..types import FieldKind
from .field import ResolvedField
from .model import ResolvedModel
from .semantics import FieldSemantics, NumericSemantic
from .semantics.numeric import Range


def resolve_model(spec: ModelSpec) -> ResolvedModel: ...


def resolve_field(field_spec: FieldSpec) -> ResolvedField: ...


def create_field_semantic(field_spec: FieldSpec) -> FieldSemantics:
    t = field_spec.type

    if t is int:
        return NumericSemantic(
            kind=FieldKind.INTEGER,
            valid_range=find_valid_numeric_ranges(
                field_spec.type, field_spec.constraints
            ),
            invalid_range=find_invalid_numeric_ranges(
                field_spec.type, field_spec.constraints
            ),
        )

    elif t is float:
        return NumericSemantic(
            kind=FieldKind.FLOAT,
            valid_range=find_valid_numeric_ranges(
                field_spec.type, field_spec.constraints
            ),
            invalid_range=find_invalid_numeric_ranges(
                field_spec.type, field_spec.constraints
            ),
        )

    else:
        raise ValueError


def find_valid_numeric_ranges(
    field_type: type, constraints: list[Constraint]
) -> Range: ...


def find_invalid_numeric_ranges(
    field_type: type, constraints: list[Constraint]
) -> Range: ...
