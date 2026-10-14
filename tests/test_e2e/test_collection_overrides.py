"""Overrides reach every generated model inside a collection."""

from dataclasses import make_dataclass
from typing import Annotated, TypedDict

import pytest

from conformly import MaxItems, MinItems, MinLength, V, case, cases, path


@pytest.fixture(params=["dataclass", "typeddict", "pydantic", "attrs"])
def collection_override_model(request, container_kind):
    def model(name, fields):
        if request.param == "dataclass":
            return make_dataclass(name, list(fields.items()))
        if request.param == "typeddict":
            return TypedDict(name, fields)
        if request.param == "pydantic":
            pydantic = pytest.importorskip("pydantic")
            return pydantic.create_model(
                name, **{key: (value, ...) for key, value in fields.items()}
            )
        attrs = pytest.importorskip("attrs")
        return attrs.make_class(
            name, {key: attrs.field(type=value) for key, value in fields.items()}
        )

    child = model("OverrideChild", {"name": Annotated[str, MinLength(3)], "label": str})
    container = list[child] if container_kind == "list" else dict[str, child]
    return model(
        "OverrideParent",
        {
            "children": Annotated[container, MinItems(2), MaxItems(2)],
            "others": Annotated[container, MinItems(2), MaxItems(2)],
            "title": Annotated[str, MinLength(3)],
        },
    )


@pytest.fixture(params=["list", "dict"])
def container_kind(request):
    return request.param


@pytest.mark.parametrize("api", [case, cases])
@pytest.mark.parametrize("value", ["SENTINEL", None])
@pytest.mark.parametrize("mode", ["valid", "unrelated", "nested", "missing", "size"])
def test_collection_model_overrides(
    collection_override_model, container_kind, api, value, mode
):
    kwargs = {
        "seed": 0,
        "overrides": [
            path("children.name").set(value),
            path("children.label").set("child-label"),
            path("others.name").set("OTHER"),
        ],
    }
    if mode != "valid":
        kwargs["valid"] = False
        kwargs["target"] = {
            "unrelated": path("title").violate(V.TOO_SHORT),
            "nested": path("children.name").violate(V.TOO_SHORT),
            "missing": path("children.name").violate(V.MISSING_FIELD),
            "size": path("children").violate(V.TOO_MANY_ITEMS),
        }[mode]
    result = api(collection_override_model, **kwargs)
    payloads = result if api is cases else [result]
    for payload in payloads:
        children = payload["children"]
        others = payload["others"]
        if container_kind == "dict":
            children = list(children.values())
            others = list(others.values())
        assert len(children) == (3 if mode == "size" else 2)
        assert all(child["label"] == "child-label" for child in children)
        assert all(child["name"] == "OTHER" for child in others)
        if mode == "nested":
            assert sum(child.get("name") == value for child in children) == 1
            assert (
                sum(
                    isinstance(child.get("name"), str) and len(child["name"]) < 3
                    for child in children
                )
                == 1
            )
        elif mode == "missing":
            assert sum("name" not in child for child in children) == 1
            assert all(child["name"] == value for child in children if "name" in child)
        else:
            assert all(child["name"] == value for child in children)
        assert (len(payload["title"]) < 3) == (mode == "unrelated")
