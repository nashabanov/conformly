from typing import NotRequired, TypedDict

import pytest

from conformly._internal.parser.adapters.typeddict import (
    parse,
    parse_fields,
    resolve_type,
    supports,
)
from conformly._internal.types.constants import UNSET
from conformly.exceptions import ResolutionError


class User(TypedDict):
    id: int
    name: str


class PartialUser(TypedDict):
    id: int
    name: NotRequired[str]


class NotATypedDict:
    x: int


# ====== TESTS FOR supports() ======


def test_supports_typeddict():
    assert supports(User) is True


def test_supports_non_typeddict():
    assert supports(NotATypedDict) is False


# ====== TESTS FOR supports() ======


def test_parse_typeddict_basic():
    spec = parse(User)

    assert spec.name == "User"
    assert spec.type == "typeddict"
    assert len(spec.fields) == 2

    field_names = {f.name for f in spec.fields}
    assert field_names == {"id", "name"}


def test_parse_raises_on_invalid_model():
    with pytest.raises(ResolutionError) as e:
        parse(NotATypedDict)

    assert e.value.context["code"] == "unsupported_model_type"


# ====== TESTS FOR parse_fields() ======


def test_parse_fields_required():
    fields = parse_fields(User)

    defaults = {f.name: f.default for f in fields}

    assert defaults["id"] is UNSET
    assert defaults["name"] is UNSET


def test_parse_fields_optional():
    fields = parse_fields(PartialUser)

    defaults = {f.name: f.default for f in fields}

    assert defaults["id"] is UNSET
    assert defaults["name"] is None


# ====== EXTRA TESTS ======


def test_resolve_type_returns_correct_type():
    hints = {"id": int}

    assert resolve_type(hints, "id") is int


def test_parse_is_cached():
    spec1 = parse(User)
    spec2 = parse(User)

    assert spec1 is spec2
