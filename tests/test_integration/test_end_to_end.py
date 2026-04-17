from dataclasses import dataclass, field
import math
import re
from typing import Annotated, Literal
import uuid

import pytest

from conformly import (
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
    MaxItems,
    MaxLength,
    MinLength,
    Pattern,
    UniqueItems,
    V,
    case,
    cases,
    path,
)
from conformly.exceptions import GenerationError, PlanningError


@dataclass
class User:
    username: Annotated[str, MinLength(3)]
    full_name: Annotated[str, MinLength(2), MaxLength(100)]
    email: Annotated[
        str,
        Pattern(r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
    ]
    bio: Annotated[str, MaxLength(500)]
    role: Literal["admin", "guest", "user"]
    is_blocked: bool


@dataclass
class BlogPost:
    title: Annotated[str, "min_length=5", "max_length=200"]
    slug: Annotated[str, "pattern=^[a-z0-9-]+$"]
    content: Annotated[str, "min_length=10"]
    views: Annotated[int, "ge=0"]
    rating: Annotated[float, "ge=0", "le=5"]


@dataclass
class Product:
    sku: str = field(metadata={"pattern": r"^[A-Z0-9]{8}$"})
    name: str = field(metadata={"min_length": 1, "max_length": 100})
    price: float = field(metadata={"gt": 0})
    stock: int = field(metadata={"ge": 0})
    discount: float = field(metadata={"ge": 0, "le": 100, "multiple_of": 5})


@dataclass
class CreateUserRequest:
    age: Annotated[int, GreaterOrEqual(18), LessThan(120)]
    email: Annotated[str, Pattern(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")]
    password: Annotated[str, MinLength(8), MaxLength(128)]
    nickname: Annotated[str, MinLength(3), MaxLength(30)]


@dataclass
class OrderItem:
    product_id: Annotated[int, GreaterThan(0)]
    quantity: Annotated[int, GreaterOrEqual(1), LessOrEqual(1000)]
    unit_price: Annotated[float, GreaterThan(0)]


@dataclass
class Transaction:
    account_id: Annotated[str, Pattern(r"^ACC[0-9]{10}$")]
    amount: Annotated[float, GreaterThan(0), LessOrEqual(1_000_000)]
    description: Annotated[str, MinLength(5), MaxLength(256)]
    reference_code: Annotated[str, Pattern(r"^[A-Z0-9]{12}$")]


@dataclass
class Article:
    title: Annotated[str, MinLength(5), MaxLength(300)]
    author: str = field(metadata={"min_length": 2, "max_length": 100})
    content: Annotated[str, "min_length=50"]
    publish_date: Annotated[int, GreaterOrEqual(0)]


@dataclass
class ProductItem:
    sku: str
    price: Annotated[float, GreaterOrEqual(0)]


@dataclass
class Order:
    items: Annotated[list[ProductItem], UniqueItems(True)]
    tags: set[str]
    codes: Annotated[list[Annotated[str, MinLength(5)]], MaxItems(6)]
    flags: list[bool]


@dataclass
class UserUUID:
    id: uuid.UUID


class TestUserModel:
    def test_generate_valid_user(self):
        for _ in range(20):
            user = case(User, valid=True)
            assert isinstance(user, dict)
            assert len(user["username"]) >= 3
            assert 2 <= len(user["full_name"]) <= 100
            assert re.match(
                r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user["email"]
            )
            assert len(user["bio"]) <= 500
            assert user["role"] in ["admin", "guest", "user"]

    def test_invalid_user_short_username(self):
        invalid = case(User, valid=False, strategy="username")
        assert len(invalid["username"]) == 2

    def test_invalid_user_long_full_name(self):
        invalid = case(User, valid=False, strategy="full_name")
        n = len(invalid["full_name"])
        assert n < 2 or n > 100

    def test_invalid_user_not_allowed_literal(self):
        invalid = case(User, valid=False, strategy="role")
        assert invalid["role"] not in ["admin", "guest", "user"]

    def test_multiple_users(self):
        users = cases(User, valid=True, count=5)
        assert len(users) == 5
        for user in users:
            assert len(user["username"]) >= 3

    def test_type_mismatching_case(self) -> None:
        invalid = case(
            User, valid=False, strategy="is_blocked", allow_type_mismatch=True
        )
        assert not isinstance(invalid["is_blocked"], bool)

    def test_type_mismatching_cases(self) -> None:
        invalid_users = cases(
            User, valid=False, strategy="all", allow_type_mismatch=True
        )
        assert len(invalid_users) == 6
        bool_case = next(
            c for c in invalid_users if c["is_blocked"] not in (True, False)
        )
        assert not isinstance(bool_case["is_blocked"], bool)

    def test_multiple_field_name(self) -> None:
        invalid_users = cases(User, valid=False, strategy="role", count=5)
        assert len(invalid_users) == 1
        for user in invalid_users:
            assert user["role"] not in ["admin", "guest", "user"]
            assert len(user["username"]) >= 3
            assert 2 <= len(user["full_name"]) <= 100
            assert re.match(
                r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user["email"]
            )
            assert len(user["bio"]) <= 500
            assert isinstance(user["is_blocked"], bool)

    def test_structural_violations(self) -> None:
        invalid_users = cases(
            User, valid=False, strategy="all", allow_structural_violations=True
        )
        assert len(invalid_users) == 7

        found_missing = False
        found_extra = False

        for user in invalid_users:
            if "is_blocked" not in user:
                found_missing = True
                assert len(user) == 5

            if "extra" in user:
                found_extra = True
                assert len(user) == 7

        assert found_missing
        assert found_extra

    def test_all_violations(self) -> None:
        invalid_users = cases(User, valid=False, strategy="all_violations")
        assert len(invalid_users) == 6

        violations_found = [False] * 6

        for user in invalid_users:
            assert isinstance(user, dict)
            violations = (
                len(user["username"]) == 2,
                len(user["full_name"]) < 2,
                len(user["full_name"]) > 100,
                user["role"] not in ["admin", "guest", "user"],
                len(user["bio"]) > 500,
                not re.match(
                    r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user["email"]
                ),
            )
            for i, v in enumerate(violations):
                if v:
                    violations_found[i] = True

        assert all(violations_found), (
            f"Not all violation types covered: {violations_found}"
        )

    def test_all_violations_with_type_mismatch(self) -> None:
        invalid_users = cases(
            User,
            valid=False,
            strategy="all_violations",
            allow_type_mismatch=True,
        )
        assert len(invalid_users) == 12

    def test_all_violations_with_structural(self) -> None:
        invalid_users = cases(
            User,
            valid=False,
            strategy="all_violations",
            allow_structural_violations=True,
        )
        assert len(invalid_users) == 13

    def test_all_violations_with_all_flags(self) -> None:
        invalid_users = cases(
            User,
            valid=False,
            strategy="all_violations",
            allow_type_mismatch=True,
            allow_structural_violations=True,
        )
        assert len(invalid_users) == 19


class TestBlogPostModel:
    def test_generate_valid_post(self):
        for _ in range(10):
            post = case(BlogPost, valid=True)
            assert 5 <= len(post["title"]) <= 200
            assert re.match(r"^[a-z0-9-]+$", post["slug"])
            assert len(post["content"]) >= 10
            assert post["views"] >= 0
            assert 0 <= post["rating"] <= 5

    def test_invalid_post_title(self):
        invalid = case(BlogPost, valid=False, strategy="title")
        assert len(invalid["title"]) < 5 or len(invalid["title"]) > 200

    def test_invalid_post_bad_rating(self):
        invalid = case(BlogPost, valid=False, strategy="rating")
        assert not (0 <= invalid["rating"] <= 5)


class TestProductModel:
    def test_generate_valid_product(self):
        for _ in range(10):
            product = case(Product, valid=True)
            assert re.match(r"^[A-Z0-9]{8}$", product["sku"])
            assert 1 <= len(product["name"]) <= 100
            assert product["price"] > 0
            assert product["stock"] >= 0
            assert 0 <= product["discount"] <= 100 and product["discount"] % 5 == 0

    def test_invalid_product_zero_price(self):
        invalid = case(Product, valid=False, strategy="price")
        assert invalid["price"] <= 0 or math.isinf(invalid["price"])

    def test_invalid_product_negative_stock(self):
        invalid = case(Product, valid=False, strategy="stock")
        MAX_INT64 = 2**63 - 1
        assert invalid["stock"] < 0 or invalid["stock"] > MAX_INT64

    def test_multiple_product_violations(self):
        invalid_products = cases(Product, valid=False, strategy="all")
        assert len(invalid_products) >= 1
        invalid_products = cases(Product, valid=False, strategy="all")
        assert len(invalid_products) >= 1

        def is_valid_product(p):
            return (
                re.match(r"^[A-Z0-9]{8}$", p["sku"])
                and 1 <= len(p["name"]) <= 100
                and p["price"] > 0
                and p["stock"] >= 0
                and 0 <= p["discount"] <= 100
                and p["discount"] % 5 == 0
            )

        assert any(not is_valid_product(p) for p in invalid_products)


class TestCreateUserRequest:
    def test_generate_valid_signup_request(self):
        for _ in range(15):
            req = case(CreateUserRequest, valid=True)
            assert 18 <= req["age"] <= 120
            assert re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", req["email"])
            assert 8 <= len(req["password"]) <= 128
            assert 3 <= len(req["nickname"]) <= 30

    def test_invalid_underage_user(self):
        invalid = case(CreateUserRequest, valid=False, strategy="age")
        assert invalid["age"] < 18 or invalid["age"] > 120

    def test_invalid_password(self):
        invalid = case(CreateUserRequest, valid=False, strategy="password")
        assert len(invalid["password"]) < 8 or len(invalid["password"]) > 120

    def test_bulk_valid_requests(self):
        requests = cases(CreateUserRequest, valid=True, count=100)
        assert len(requests) == 100
        for req in requests:
            assert 18 <= req["age"] <= 120
            assert len(req["password"]) >= 8


class TestOrderItem:
    def test_generate_valid_order_item(self):
        for _ in range(20):
            item = case(OrderItem, valid=True)
            assert item["product_id"] > 0
            assert 1 <= item["quantity"] <= 1000
            assert item["unit_price"] > 0

    def test_invalid_order_item_zero_quantity(self):
        invalid = case(OrderItem, valid=False, strategy="quantity")
        assert invalid["quantity"] < 1 or invalid["quantity"] > 1000

    def test_invalid_order_item_invalid_product_id(self):
        invalid = case(OrderItem, valid=False, strategy="product_id")
        MAX_INT64 = 2**63 - 1
        assert invalid["product_id"] <= 0 or invalid["product_id"] > MAX_INT64

    def test_bulk_orders(self):
        items = cases(OrderItem, valid=True, count=50)
        assert len(items) == 50
        for item in items:
            assert item["product_id"] > 0
            assert item["quantity"] >= 1


class TestTransaction:
    def test_generate_valid_transaction(self):
        for _ in range(15):
            tx = case(Transaction, valid=True)
            assert re.match(r"^ACC[0-9]{10}$", tx["account_id"])
            assert 0 < tx["amount"] <= 1_000_000
            assert 5 <= len(tx["description"]) <= 256
            assert re.match(r"^[A-Z0-9]{12}$", tx["reference_code"])

    def test_invalid_transaction_bad_account(self):
        invalid = case(Transaction, valid=False, strategy="account_id")
        assert not re.match(r"^ACC[0-9]{10}$", invalid["account_id"])

    def test_invalid_transaction_huge_amount(self):
        invalid = case(Transaction, valid=False, strategy="amount")
        assert invalid["amount"] > 1_000_000 or invalid["amount"] <= 0

    def test_transaction_batch(self):
        transactions = cases(Transaction, valid=True, count=20)
        assert len(transactions) == 20
        for tx in transactions:
            assert 0 < tx["amount"] <= 1_000_000


class TestArticle:
    def test_generate_valid_article(self):
        for _ in range(10):
            article = case(Article, valid=True)
            assert 5 <= len(article["title"]) <= 300
            assert 2 <= len(article["author"]) <= 100
            assert len(article["content"]) >= 50
            assert article["publish_date"] >= 0

    def test_all_valid_articles(self):
        articles = cases(Article, valid=True, count=5)
        assert len(articles) == 5
        for article in articles:
            assert 5 <= len(article["title"]) <= 300
            assert 2 <= len(article["author"]) <= 100


class TestRealWorldUsagePatterns:
    def test_api_validation_happy_path(self):
        for _ in range(50):
            req = case(CreateUserRequest, valid=True)
            assert 18 <= req["age"] <= 120, "Age must be 18-120"
            assert len(req["password"]) >= 8, "Password too short"
            assert "@" in req["email"], "Invalid email"

    def test_api_validation_sad_path(self):
        saw_invalid = False

        for _ in range(200):
            invalid_req = case(CreateUserRequest, valid=False, strategy="random")
            is_valid = (
                18 <= invalid_req["age"] <= 120
                and len(invalid_req["password"]) >= 8
                and "@" in invalid_req["email"]
                and 3 <= len(invalid_req["nickname"]) <= 30
            )
            if not is_valid:
                saw_invalid = True
                break

        assert saw_invalid

    def test_ecommerce_order_validation(self):
        valid_order = cases(OrderItem, valid=True, count=10)
        for item in valid_order:
            assert item["product_id"] > 0
            assert 1 <= item["quantity"] <= 1000
            assert item["unit_price"] > 0

        invalid_orders = cases(OrderItem, valid=False, strategy="all")

        def is_valid_item(item):
            return (
                item["product_id"] > 0
                and 1 <= item["quantity"] <= 1000
                and item["unit_price"] > 0
            )

        assert any(not is_valid_item(item) for item in invalid_orders)

    def test_database_insert_compliance(self):
        for _ in range(20):
            user = case(User, valid=True)
            assert 3 <= len(user["username"]) <= 255, "username length"
            assert len(user["full_name"]) <= 100, "full_name length"
            assert "@" in user["email"], "invalid email"


class TestFuzzTesting:
    def test_fuzz_user_model(self):
        saw_violation = False
        for _ in range(500):
            user = case(User, valid=False, strategy="random")
            violations = 0
            if len(user["username"]) < 3:
                violations += 1
            if not (2 <= len(user["full_name"]) <= 100):
                violations += 1
            if not re.match(
                r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user["email"]
            ):
                violations += 1
            if len(user["bio"]) > 500:
                violations += 1
            if violations >= 1:
                saw_violation = True
                break

        assert saw_violation

    def test_fuzz_product_model(self):
        saw_violation = False
        MAX_INT64 = 2**63 - 1

        for _ in range(500):
            product = case(Product, valid=False, strategy="random")
            violations = 0
            if not re.match(r"^[A-Z0-9]{8}$", product["sku"]):
                violations += 1
            if not (1 <= len(product["name"]) <= 100):
                violations += 1
            if not (product["price"] > 0):
                violations += 1
            if product["stock"] < 0 or product["stock"] > MAX_INT64:
                violations += 1
            if not (0 <= product["discount"] <= 100):
                violations += 1
            if violations >= 1:
                saw_violation = True
                break

        assert saw_violation


class TestViolationTypeSyntax:
    def test_specific_violation_too_short(self):
        invalid = case(User, valid=False, strategy="username::too_short")
        assert len(invalid["username"]) < 3
        assert len(invalid["email"]) > 0  # Other fields valid

    def test_specific_violation_too_long(self):
        invalid = case(User, valid=False, strategy="bio::too_long")
        assert len(invalid["bio"]) > 500
        assert len(invalid["username"]) >= 3  # Other fields valid

    def test_specific_violation_pattern_mismatch(self):
        invalid = case(User, valid=False, strategy="email::pattern_mismatch")
        assert not re.match(
            r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", invalid["email"]
        )
        assert len(invalid["username"]) >= 3

    def test_specific_violation_not_allowed_value(self):
        invalid = case(User, valid=False, strategy="role::not_allowed_value")
        assert invalid["role"] not in ["admin", "guest", "user"]

    def test_specific_violation_type_mismatch(self):
        invalid = case(
            User,
            valid=False,
            strategy="is_blocked::type_mismatch",
            allow_type_mismatch=True,
        )
        assert not isinstance(invalid["is_blocked"], bool)
        assert len(invalid["username"]) >= 3

    def test_cases_with_specific_violation(self):
        invalid_users = cases(
            User, valid=False, strategy="username::too_short", count=3
        )
        assert len(invalid_users) == 1
        for user in invalid_users:
            assert len(user["username"]) < 3

    def test_invalid_violation_type_raises(self):
        with pytest.raises(GenerationError):
            case(User, valid=False, strategy="username::invalid_violation")

    def test_incompatible_violation_type_raises(self):
        with pytest.raises(PlanningError):
            case(User, valid=False, strategy="username::below_min")

    def test_incompatible_violation_on_enum(self):
        with pytest.raises(PlanningError):
            case(User, valid=False, strategy="role::below_min")

    def test_violation_with_allow_type_mismatch(self):
        invalid = case(
            User,
            valid=False,
            strategy="is_blocked::type_mismatch",
            allow_type_mismatch=True,
        )
        assert not isinstance(invalid["is_blocked"], (bool,))

    def test_violation_with_structural_violations(self):
        invalid = case(
            User,
            valid=False,
            strategy="bio::missing_field",
        )
        assert "bio" not in invalid

    def test_deterministic_violation_selection(self):
        results = []
        for _ in range(10):
            invalid = case(User, valid=False, strategy="username::too_short")
            results.append(len(invalid["username"]))

        assert all(r < 3 for r in results)

    def test_other_fields_remain_valid(self):
        invalid = case(User, valid=False, strategy="email::pattern_mismatch")

        assert not re.match(
            r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", invalid["email"]
        )

        assert len(invalid["username"]) >= 3
        assert 2 <= len(invalid["full_name"]) <= 100
        assert invalid["role"] in ["admin", "guest", "user"]
        assert len(invalid["bio"]) <= 500
        assert isinstance(invalid["is_blocked"], bool)

    def test_case_vs_cases_with_specific_violation(self):
        case_result = case(User, valid=False, strategy="role::not_allowed_value")
        cases_result = cases(
            User, valid=False, strategy="role::not_allowed_value", count=1
        )

        assert case_result["role"] not in ["admin", "guest", "user"]
        assert cases_result[0]["role"] not in ["admin", "guest", "user"]

    def test_valid_flag_ignores_strategy(self):
        with pytest.raises(GenerationError):
            case(User, valid=True, strategy="username::too_short")

    def test_field_not_found_with_violation(self):
        with pytest.raises(PlanningError) as exc_info:
            case(User, valid=False, strategy="nonexistent::below_min")

        assert "not found" in str(exc_info.value).lower() or "Field" in str(
            exc_info.value
        )

    def test_available_violations_in_error_message(self):
        with pytest.raises(PlanningError) as exc_info:
            case(User, valid=False, strategy="username::below_min")

        error_msg = str(exc_info.value)
        assert (
            "too_short" in error_msg
            or "too_long" in error_msg
            or "pattern_mismatch" in error_msg
        )

    def test_auto_enable_structural_for_missing_field(self):
        invalid = case(
            User,
            valid=False,
            strategy="bio::missing_field",
        )
        assert "bio" not in invalid

    def test_all_violations_count_with_new_syntax(self):
        invalid_users = cases(
            User,
            valid=False,
            strategy="all_violations",
            allow_type_mismatch=True,
            allow_structural_violations=True,
        )
        assert len(invalid_users) >= 8

    def test_reproducibility_with_specific_violation(self):
        invalid1 = case(User, valid=False, strategy="username::too_short")
        invalid2 = case(User, valid=False, strategy="username::too_short")

        assert len(invalid1["username"]) < 3
        assert len(invalid2["username"]) < 3

    def test_path_selector_specific_violation(self) -> None:
        invalid = case(
            User, valid=False, strategy=path("username").violate(V.TOO_SHORT)
        )
        assert len(invalid["username"]) < 3
        assert len(invalid["email"]) > 0

    def test_path_selector_structural_violation(self) -> None:
        invalid = case(
            User,
            valid=False,
            strategy=path("bio").violate(V.MISSING_FIELD),
        )

        assert "bio" not in invalid

    def test_path_selector_structural_requires_violation(self):
        with pytest.raises(GenerationError):
            cases(
                User,
                valid=False,
                strategy=path("bio"),
                allow_structural_violations=True,
            )

    def test_path_selector_incompatible_violation(self):
        with pytest.raises(PlanningError):
            case(
                User,
                valid=False,
                strategy=path("username").violate(V.BELOW_MIN),
            )

    def test_path_selector_field_not_found(self):
        with pytest.raises(PlanningError):
            case(
                User,
                valid=False,
                strategy=path("nonexistent").violate(V.TOO_SHORT),
            )

    def test_path_selector_equals_string_syntax(self):
        invalid1 = case(
            User,
            valid=False,
            strategy="username::too_short",
        )

        invalid2 = case(
            User,
            valid=False,
            strategy=path("username").violate(V.TOO_SHORT),
        )

        assert len(invalid1["username"]) < 3
        assert len(invalid2["username"]) < 3


class TestApiErrors:
    def test_case_raises_if_strategy_all(self) -> None:
        with pytest.raises(GenerationError):
            case(User, valid=False, strategy="all")

    def test_raises_if_valid_and_not_default_strategy(self) -> None:
        with pytest.raises(GenerationError):
            case(User, valid=True, strategy="random")

        with pytest.raises(GenerationError):
            cases(User, valid=True, strategy="random")

    def test_raises_if_valid_and_type_mismatch_allowed(self) -> None:
        with pytest.raises(GenerationError):
            case(User, allow_type_mismatch=True)

        with pytest.raises(GenerationError):
            cases(User, allow_type_mismatch=True)

    @pytest.mark.parametrize("strategy", ["random", "first", "name"])
    def test_raises_if_strategy_not_all_and_structural_allowed(
        self, strategy: str
    ) -> None:
        with pytest.raises(GenerationError):
            cases(
                User, valid=False, strategy=strategy, allow_structural_violations=True
            )

    def test_raises_if_valid_and_structural_allowed(self) -> None:
        with pytest.raises(GenerationError):
            cases(User, allow_structural_violations=True)

    def test_raises_if_count_less_than_one(self) -> None:
        with pytest.raises(GenerationError):
            cases(User, count=0)


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
        result = case(Order, valid=False)

        items = result["items"]

        if len(items) > 1:
            assert len(items) != len({repr(i) for i in items})

    def test_codes_length_violation(self):
        result = case(Order, valid=False, strategy="codes")

        codes = result["codes"]

        assert len(codes) > 6 or len(codes) == 0


class TestUUIDGeneration:
    def test_valid_uuid(self):
        result = case(UserUUID, valid=True)

        assert isinstance(result["id"], str)
        parsed = uuid.UUID(result["id"])
        assert parsed.version == 4, f"Expected v4 UUID, got version {parsed.version}"
        assert result["id"] == str(parsed)

    @pytest.mark.xfail
    def test_invalid_uuid_fails_strict_parsing(self):
        result = case(UserUUID, valid=False)
        with pytest.raises(GenerationError):
            uuid.UUID(result["id"])

    def test_valid_false_respects_violation_type(self):
        result = case(UserUUID, valid=False, strategy="id::wrong_uuid_character")
        hex_clean = result["id"].replace("-", "").lower()
        assert not all(c in "0123456789abcdef" for c in hex_clean)


class TestDeterministicGeneration:
    def test_same_seed_same_output(self) -> None:
        user1 = case(User, seed=42)
        user2 = case(User, seed=42)
        assert user1 == user2

    def test_different_seed_different_output(self) -> None:
        user1 = case(User, seed=44)
        user2 = case(User, seed=125)
        assert user1 != user2

    def test_same_seed_same_list(self) -> None:
        users1 = cases(User, seed=42)
        users2 = cases(User, seed=42)
        assert users1 == users2

    def test_invalid_generation_seeding(self) -> None:
        user1 = case(User, valid=False, seed=42)
        user2 = case(User, valid=False, seed=42)
        assert user1 == user2
