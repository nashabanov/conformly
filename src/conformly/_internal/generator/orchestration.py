from typing import Any

from ._errors import generation_error
from .context import GenerationContext
from .registry import choose_mismatch_kind, get_generator

from conformly._internal.planner import PlannedTask
from conformly._internal.planner.model import CollectionTarget
from conformly._internal.resolver import (
    ResolvedField,
    ResolvedModel,
    create_minimal_semantic,
)
from conformly._internal.resolver.semantics import (
    DictSemantic,
    FieldSemantics,
    ListSemantic,
    ObjectSemantic,
    TupleSemantic,
)
from conformly._internal.tracer import Tracer, ValueSource
from conformly._internal.types import UNSET, FieldKind, FieldPath, ViolationType


def generate_valid(
    ctx: GenerationContext,
    model: ResolvedModel,
    overrides: dict[FieldPath, Any] | None = None,
) -> dict[str, Any]:
    return {
        field.name: generate_field(ctx, field, None, overrides)
        for field in model.fields
    }


def generate_invalid(
    ctx: GenerationContext,
    model: ResolvedModel,
    task: PlannedTask,
    overrides: dict[FieldPath, Any] | None = None,
    tracer: Tracer | None = None,
) -> dict[str, Any]:
    if tracer:
        tracer.set_seed(ctx.seed)
    return _built_dict_with_violations(
        ctx=ctx,
        model=model,
        target_path=task.path,
        depth=0,
        violations=task.allowed_violations,
        overrides=overrides,
        tracer=tracer,
        collection_target=task.collection_target,
        collection_steps=task.collection_steps,
    )


def _built_dict_with_violations(
    ctx: GenerationContext,
    model: ResolvedModel,
    target_path: FieldPath,
    depth: int,
    violations: tuple[ViolationType, ...],
    overrides: dict[FieldPath, Any] | None = None,
    tracer: Tracer | None = None,
    path_names: tuple[str, ...] = (),
    collection_target: CollectionTarget | None = None,
    collection_steps: tuple[tuple[FieldPath, CollectionTarget], ...] = (),
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    target_index = target_path[depth]
    is_leaf = depth == len(target_path) - 1
    fields = model.fields
    total_fields = len(model.fields)

    if target_index < 0 or target_index > total_fields:
        raise generation_error(
            "Path index out of bounds for model",
            code="invalid_path_index",
            model=model.name,
            total_fields=total_fields,
            target_index=target_index,
        )

    for i in range(0, target_index):
        field = fields[i]
        result[field.name] = generate_field(ctx, field, None, overrides)

    if target_index < total_fields:
        field = fields[target_index]

        if is_leaf:
            if len(violations) == 0:
                raise generation_error(
                    "Cannot generate violation: field has no constraints",
                    code="no_violation_to_generate",
                    field=field.name,
                )

            if tracer:
                tracer.set_target_path(".".join((*path_names, field.name)))
            value = generate_field(
                ctx, field, violations, overrides, tracer, collection_target
            )
            if value is not UNSET:
                result[field.name] = value

        else:
            if field.nested_model is None:
                raise generation_error(
                    "Field is not nested model",
                    code="expected_nested_model",
                    field=field.name,
                )

            nested_value = _built_dict_with_violations(
                ctx=ctx,
                model=field.nested_model,
                target_path=target_path,
                depth=depth + 1,
                violations=violations,
                overrides=overrides,
                tracer=tracer,
                path_names=(*path_names, field.name),
                collection_target=collection_target,
                collection_steps=collection_steps,
            )

            if isinstance(field.semantic, (ListSemantic, DictSemantic)):
                step = next(
                    (t for p, t in collection_steps if p == target_path[: depth + 1]),
                    None,
                )
                if step is None:
                    raise generation_error(
                        "Nested collection requires a planned target",
                        code="missing_collection_target",
                    )
                container = _generate_nested_collection(
                    ctx, field.semantic, step, nested_value
                )
                result[field.name] = container
            else:
                result[field.name] = nested_value

    else:
        key, value = _generate_extra_field_value(ctx)
        suffix = 1
        while key in result:
            key = f"extra_{suffix}"
            suffix += 1
        result[key] = value
        if tracer:
            tracer.set_target_path(".".join((*path_names, key)))
            tracer.set_violation(ViolationType.EXTRA_FIELD)
            tracer.set_value_source(ValueSource.GENERATED)
            tracer.set_generated_value(value)

    for i in range(target_index + 1, total_fields):
        field = fields[i]
        result[field.name] = generate_field(ctx, field, overrides=overrides)

    return result


def generate_field(
    ctx: GenerationContext,
    field: ResolvedField,
    violations: tuple[ViolationType, ...] | None = None,
    overrides: dict[FieldPath, Any] | None = None,
    tracer: Tracer | None = None,
    collection_target: CollectionTarget | None = None,
) -> Any:
    if violations is None:
        if overrides and field.path in overrides:
            value = overrides[field.path]
            if tracer:
                tracer.set_value_source(ValueSource.OVERRIDDEN)
                tracer.set_generated_value(value)
            return value

        if field.nullable:
            return None

        if field.default is not UNSET:
            if tracer:
                tracer.set_value_source(ValueSource.MODEL_DEFAULT)

            default = field.default
            value = default() if callable(default) else default
            if tracer:
                tracer.set_generated_value(value)
            return value

        if field.nested_model and not isinstance(
            field.semantic, (ListSemantic, DictSemantic, TupleSemantic)
        ):
            return generate_valid(ctx, field.nested_model, overrides)

    violation = _choose_violation(violations)

    if tracer:
        tracer.set_violation(violation)
        tracer.set_value_source(ValueSource.GENERATED)

    value = generate_semantic_value(
        ctx, field.semantic, field.nested_model, violations, collection_target
    )
    if tracer:
        tracer.set_generated_value(value)
    return value


def generate_semantic_value(
    ctx: GenerationContext,
    semantic: FieldSemantics,
    nested_model: ResolvedModel | None,
    violations: tuple[ViolationType, ...] | None,
    collection_target: CollectionTarget | None = None,
) -> Any:
    """Generate directly from resolved semantics, without synthetic field models."""
    violation = _choose_violation(violations)
    if violation == ViolationType.TYPE_MISMATCH:
        mismatch_kind = choose_mismatch_kind(semantic.kind)
        return get_generator(mismatch_kind).generate_value(
            ctx, create_minimal_semantic(mismatch_kind), None
        )
    if violation == ViolationType.MISSING_FIELD:
        return UNSET
    if nested_model is not None and isinstance(semantic, ObjectSemantic):
        if violation is not None:
            raise generation_error(
                "Nested model violation requires a field target",
                code="missing_nested_target",
            )
        return generate_valid(ctx, nested_model)
    from .types import dictionaries, list as lists, tuple as tuples

    if isinstance(semantic, ListSemantic):
        return lists.generate_value(ctx, semantic, violation, target=collection_target)
    if isinstance(semantic, DictSemantic):
        return dictionaries.generate_value(
            ctx, semantic, violation, target=collection_target
        )
    if isinstance(semantic, TupleSemantic):
        return tuples.generate_value(ctx, semantic, violation, target=collection_target)
    return get_generator(semantic.kind).generate_value(ctx, semantic, violation)


def _choose_violation(
    violations: tuple[ViolationType, ...] | None,
) -> ViolationType | None:
    if violations is None:
        return None

    return violations[0]


def _generate_extra_field_value(ctx: GenerationContext) -> tuple[str, Any]:
    semantic = create_minimal_semantic(FieldKind.STRING)
    value = get_generator(semantic.kind).generate_value(ctx, semantic, None)
    key = "extra"
    return (key, value)


def _generate_nested_collection(
    ctx: GenerationContext,
    semantic: ListSemantic | DictSemantic,
    target: CollectionTarget,
    nested_value: dict[str, Any],
) -> Any:
    from .types._utils import calculate_valid_collection_range, unique_collection_range
    from .types.dictionaries import _generate_dict_of_length
    from .types.list import _generate_list_of_length

    lower, upper = calculate_valid_collection_range(semantic)
    if isinstance(semantic, DictSemantic):
        lower, upper = unique_collection_range(
            lower, upper, semantic.key_semantic, collection="dict"
        )
        length = ctx.rng.randint(lower, upper)
        return _generate_dict_of_length(
            ctx, semantic, length, target=target, target_value=nested_value
        )
    length = ctx.rng.randint(lower, upper)
    result = _generate_list_of_length(ctx, semantic, length - 1)
    result.insert(target.index, nested_value)
    return result
