from _models import Order

from conformly import (
    case,
)


class TestListGeneration:
    def test_list_of_strings_length_and_type(self):
        result = case(Order, valid=True)

        assert isinstance(result["tags"], list)
        assert 1 <= len(result["tags"]) <= 3
        assert all(isinstance(t, str) for t in result["tags"])

    def test_list_with_constraints_enforced(self):
        result = case(Order, valid=True)

        assert all(len(code) >= 5 for code in result["codes"])

    def test_list_of_models_generates_nested_dicts(self):
        result = case(Order, valid=True)

        assert isinstance(result["items"], list)
        assert len(result["items"]) >= 1
        for item in result["items"]:
            assert isinstance(item, dict)
            assert "sku" in item and "price" in item
            assert item["price"] >= 0

    def test_list_of_primitives_without_constraints(self):
        result = case(Order, valid=True)

        assert isinstance(result["flags"], list)
        assert all(isinstance(f, bool) for f in result["flags"])

    def test_tags_are_unique_strings(self):
        result = case(Order, valid=True)

        tags = result["tags"]

        assert isinstance(tags, list)
        assert 1 <= len(tags) <= 3
        assert all(isinstance(t, str) for t in tags)

        assert len(tags) == len(set(tags))

    def test_codes_constraints_enforced(self):
        result = case(Order, valid=True)

        codes = result["codes"]

        assert isinstance(codes, list)
        assert 1 <= len(codes) <= 6

        for code in codes:
            assert isinstance(code, str)
            assert len(code) >= 5

    # Collision-driven structural uniqueness coverage belongs to issue #97.
    def test_items_are_unique_and_valid(self):
        result = case(Order, valid=True)

        items = result["items"]

        assert isinstance(items, list)
        assert len(items) >= 1

        for item in items:
            assert isinstance(item, dict)
            assert "sku" in item and "price" in item
            assert isinstance(item["sku"], str)
            assert item["price"] >= 0

        assert len(items) == len({repr(i) for i in items})

    def test_items_duplicate_violation(self):
        # Exact-length duplicate handling is tracked in issue #98.
        result = case(Order, valid=False, strategy="items::duplicate", seed=0)

        items = result["items"]

        assert len(items) >= 2
        assert any(item in items[:i] for i, item in enumerate(items))

    def test_codes_length_violation(self):
        result = case(Order, valid=False, strategy="codes")

        codes = result["codes"]

        assert len(codes) > 6 or len(codes) == 0
