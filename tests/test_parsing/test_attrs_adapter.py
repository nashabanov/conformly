import pytest

pytest.importorskip("attrs", reason="attrs adapter requires 'attrs' package")
pytest.importorskip("attr", reason="attrs adapter requires 'attrs' package")

import attrs

from conformly._internal.parser.adapters.attrs import supports


@attrs.define
class DummyAttrs:
    x: int


class NotAttrs:
    pass


def test_supports_attrs() -> None:
    assert supports(DummyAttrs)


def test_supports_not_attrs() -> None:
    assert not supports(NotAttrs)


def test_supports_int() -> None:
    assert not supports(int)


def test_supports_legacy_attrs() -> None:
    import attr

    @attr.s
    class LegacyAttrs:
        x: int

    assert supports(LegacyAttrs)
