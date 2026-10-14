"""Validity of supplied data is the caller's responsibility, unlike generated data."""

from dataclasses import field, make_dataclass
from typing import Annotated, NotRequired, Required, TypedDict

import pytest

from conformly import GreaterOrEqual, V, case, cases, path
from conformly.exceptions import PlanningError


class Partial(TypedDict, total=False):
    optional: int
    required: Required[int]
    nullable: NotRequired[int | None]


class InheritedPartial(Partial):
    other: NotRequired[int]
    # Postponed annotations can leave __required_keys__ inaccurate.
    explicitly_required: "Required[int]"
    explicitly_optional: "NotRequired[int]"


@pytest.mark.parametrize("model", [Partial, InheritedPartial])
@pytest.mark.parametrize("seed", [0, 7, -1])
@pytest.mark.parametrize("api", [case, cases])
def test_notrequired_is_independent_of_nullable(model, seed, api, capsys):
    result = api(model, seed=seed)
    payloads = result if api is cases else [result]
    for payload in payloads:
        assert isinstance(payload["required"], int)
        for name in ("optional", "other", "explicitly_optional", "explicitly_required"):
            if name in payload:
                assert isinstance(payload[name], int)
        assert payload.get("nullable") is None or isinstance(payload["nullable"], int)
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("model", [Partial, InheritedPartial])
def test_typeddict_structural_violations_only_remove_required_keys(model):
    required = {"required"}
    if model is InheritedPartial:
        required.add("explicitly_required")
    expected_keys = set(model.__annotations__)
    missing = set()
    extra_seen = False
    for payload in cases(
        model,
        valid=False,
        seed=0,
        strategy="all_violations",
        allow_structural_violations=True,
    ):
        absent = expected_keys - payload.keys()
        extra = payload.keys() - expected_keys
        if absent:
            assert len(absent) == 1 and absent <= required
            assert not extra
            missing.update(absent)
        else:
            assert len(extra) == 1
            extra_seen = True
        for key in payload.keys() & expected_keys - {"nullable"}:
            assert isinstance(payload[key], int)
    assert missing == required
    assert extra_seen
    with pytest.raises(PlanningError):
        case(model, valid=False, target=path("optional").violate(V.MISSING_FIELD))


@pytest.mark.parametrize("extra", [None, "ignore", "allow", "forbid"])
def test_pydantic_structural_policy(extra):
    pydantic = pytest.importorskip("pydantic")
    model = pydantic.create_model(
        "StructuralPolicy",
        __config__=pydantic.ConfigDict(extra=extra),
        required=(int, ...),
        nullable=(int | None, ...),
        defaulted=(int, 5),
        optional=(int | None, None),
    )
    missing = set()
    extra_seen = False
    for payload in cases(
        model,
        valid=False,
        seed=0,
        strategy="all_violations",
        allow_structural_violations=True,
    ):
        absent = {"required", "nullable", "defaulted", "optional"} - payload.keys()
        with pytest.raises(pydantic.ValidationError):
            model.model_validate(payload)
        if absent:
            assert absent <= {"required", "nullable"} and len(absent) == 1
            missing.update(absent)
        else:
            assert extra == "forbid"
            extra_seen = True
    assert missing == {"required", "nullable"}
    assert extra_seen == (extra == "forbid")
    for name in ("defaulted", "optional"):
        with pytest.raises(PlanningError):
            case(model, valid=False, target=path(name).violate(V.MISSING_FIELD))


def test_nested_pydantic_models_keep_their_own_extra_policy():
    pydantic = pytest.importorskip("pydantic")
    child = pydantic.create_model(
        "ForbidChild", __config__=pydantic.ConfigDict(extra="forbid"), value=(int, ...)
    )
    parent = pydantic.create_model(
        "AllowParent", __config__=pydantic.ConfigDict(extra="allow"), child=(child, ...)
    )
    extra_payloads = []
    for payload in cases(
        parent,
        valid=False,
        seed=0,
        strategy="all_violations",
        allow_structural_violations=True,
    ):
        with pytest.raises(pydantic.ValidationError):
            parent.model_validate(payload)
        assert set(payload) <= {"child"}
        if "child" in payload and set(payload["child"]) - {"value"}:
            extra_payloads.append(payload)
    assert extra_payloads


@pytest.fixture(params=["dataclass", "pydantic", "attrs"])
def default_policy_model(request):
    calls = []

    def factory():
        calls.append(1)
        return -2  # User-supplied factories are not validated either.

    def nullable_factory():
        raise AssertionError("Nullable priority must bypass the factory")

    number = Annotated[int, GreaterOrEqual(10)]
    nullable = Annotated[int | None, GreaterOrEqual(10)]
    if request.param == "dataclass":
        model = make_dataclass(
            "DataclassDefaults",
            [
                ("target", number),
                ("value", number, field(default=-1)),
                ("nullable", nullable, field(default=20)),
                ("factory", number, field(default_factory=factory)),
                ("nullable_factory", nullable, field(default_factory=nullable_factory)),
            ],
        )
    elif request.param == "attrs":
        attrs = pytest.importorskip("attrs")
        model = attrs.make_class(
            "AttrsDefaults",
            {
                "target": attrs.field(type=number),
                "value": attrs.field(type=number, default=-1),
                "nullable": attrs.field(type=nullable, default=20),
                "factory": attrs.field(type=number, factory=factory),
                "nullable_factory": attrs.field(
                    type=nullable, factory=nullable_factory
                ),
            },
        )
    else:
        pydantic = pytest.importorskip("pydantic")
        model = pydantic.create_model(
            "PydanticDefaults",
            **{
                "target": (int, pydantic.Field(ge=10)),
                "value": (int, pydantic.Field(default=-1, ge=10)),
                "nullable": (int | None, pydantic.Field(default=20, ge=10)),
                "factory": (int, pydantic.Field(default_factory=factory, ge=10)),
                "nullable_factory": (
                    int | None,
                    pydantic.Field(default_factory=nullable_factory, ge=10),
                ),
            },
        )
    return model, calls


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize("invalid", [False, True])
def test_nullable_defaults_and_unchecked_factory_policy(
    default_policy_model, api, invalid
):
    model, calls = default_policy_model
    kwargs = {"seed": 0, "valid": not invalid}
    if invalid:
        kwargs["target"] = path("target").violate(V.BELOW_MIN)
    elif api is cases:
        kwargs["count"] = 3
    result = api(model, **kwargs)
    payloads = result if api is cases else [result]
    for payload in payloads:
        assert payload["value"] == -1
        assert payload["factory"] == -2
        assert payload["nullable"] is None
        assert payload["nullable_factory"] is None
        assert payload["target"] < 10 if invalid else payload["target"] >= 10
    assert len(calls) == len(payloads)


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize("invalid", [False, True])
def test_unchecked_overrides_win_unless_targeted(default_policy_model, api, invalid):
    model, calls = default_policy_model
    kwargs = {
        "seed": 0,
        "valid": not invalid,
        "overrides": [
            path("target").set(100),
            path("value").set(-9),
            path("nullable").set(-9),
            path("factory").set(-9),
        ],
    }
    if invalid:
        kwargs["target"] = path("target").violate(V.BELOW_MIN)
    result = api(model, **kwargs)
    payloads = result if api is cases else [result]
    for payload in payloads:
        assert payload["value"] == payload["nullable"] == payload["factory"] == -9
        assert payload["nullable_factory"] is None
        assert payload["target"] < 10 if invalid else payload["target"] == 100
    assert not calls


def test_invalid_generation_bypasses_nullable_and_model_default(default_policy_model):
    model, calls = default_policy_model
    for name in ("value", "nullable", "nullable_factory"):
        payload = case(
            model, valid=False, seed=0, target=path(name).violate(V.BELOW_MIN)
        )
        assert isinstance(payload[name], int) and payload[name] < 10
    assert len(calls) == 3


@pytest.mark.parametrize("adapter", ["dataclass", "attrs"])
def test_defaulted_fields_are_not_missing_field_targets(adapter):
    if adapter == "dataclass":
        model = make_dataclass(
            "StructuralDataclass",
            [
                ("required", int),
                ("defaulted", int, field(default=5)),
            ],
        )
    else:
        attrs = pytest.importorskip("attrs")
        model = attrs.make_class(
            "StructuralAttrs",
            {
                "required": attrs.field(type=int),
                "defaulted": attrs.field(type=int, default=5),
            },
        )
    payloads = cases(
        model,
        valid=False,
        seed=0,
        strategy="all_violations",
        allow_structural_violations=True,
    )
    assert any("required" not in payload for payload in payloads)
    assert any(set(payload) - {"required", "defaulted"} for payload in payloads)
    assert all(payload["defaulted"] == 5 for payload in payloads)
    with pytest.raises(PlanningError):
        case(model, valid=False, target=path("defaulted").violate(V.MISSING_FIELD))
