import random
from typing import Any

from dataspec.generator.registry import get_generator
from dataspec.specs import FieldSpec, ModelSpec

# TODO: доделать работу int/float
# TODO: расширить логику работы invalid на разные стратегии:
# 1. возврат нарушений по случайному полю
# 2. приоритезация полей по constraints, если есть заданное кол-во
# 3. нарушения для полей default (пока не думал насчет релизации)
# 4. нарушения обязательности полей (вопрос на этом ли уровне или ниже,
# работа на текущем логична, но повышает цикломатическую сложность значительно)


def generate(
    model_spec: ModelSpec, valid: bool = True
) -> dict[str, Any] | list[dict[str, Any]]:
    if valid:
        return generate_valid(model_spec)

    return [
        generate_invalid(model_spec, i)
        for i, field in enumerate(model_spec.fields)
        if len(field.constraints) >= 1
    ]


def generate_valid(model_spec: ModelSpec) -> dict[str, Any]:
    return {
        field.name: generate_field(field, valid=True) for field in model_spec.fields
    }


def generate_invalid(model_spec: ModelSpec, field_index: int) -> dict[str, Any]:
    return {
        field.name: (
            generate_field(field, valid=False)
            if i == field_index and len(field.constraints) >= 1
            else generate_field(field, valid=True)
        )
        for i, field in enumerate(model_spec.fields)
    }


def generate_field(field_spec: FieldSpec, valid: bool) -> Any:
    if field_spec.is_optional():
        return None
    # if not field_spec.is_optional() and not valid:
    # return None
    if field_spec.has_default():
        return field_spec.default

    if field_spec.type is bool:
        return random.choice([True, False])

    return get_generator(field_spec).generate_value(field_spec.constraints, valid)
