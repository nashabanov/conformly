import math
import re

from _models import (
    Article,
    BlogPost,
    CreateUserRequest,
    OrderItem,
    Product,
    Transaction,
    User,
)
import pytest

from conformly import (
    case,
    cases,
)


class TestUserModel:
    @pytest.mark.parametrize("seed", [0, 1, -1])
    def test_generate_valid_user(self, seed: int) -> None:
        user = case(User, valid=True, seed=seed)
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
    @pytest.mark.parametrize("seed", [0, 1, -1])
    def test_generate_valid_post(self, seed: int) -> None:
        post = case(BlogPost, valid=True, seed=seed)
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
    @pytest.mark.parametrize("seed", [0, 1, -1])
    def test_generate_valid_product(self, seed: int) -> None:
        product = case(Product, valid=True, seed=seed)
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
    @pytest.mark.parametrize("seed", [0, 1, -1])
    def test_generate_valid_signup_request(self, seed: int) -> None:
        req = case(CreateUserRequest, valid=True, seed=seed)
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
        requests = cases(CreateUserRequest, valid=True, count=3, seed=0)
        assert len(requests) == 3
        for req in requests:
            assert 18 <= req["age"] <= 120
            assert len(req["password"]) >= 8


class TestOrderItem:
    @pytest.mark.parametrize("seed", [0, 1, -1])
    def test_generate_valid_order_item(self, seed: int) -> None:
        item = case(OrderItem, valid=True, seed=seed)
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
        items = cases(OrderItem, valid=True, count=3, seed=0)
        assert len(items) == 3
        for item in items:
            assert item["product_id"] > 0
            assert item["quantity"] >= 1


class TestTransaction:
    @pytest.mark.parametrize("seed", [0, 1, -1])
    def test_generate_valid_transaction(self, seed: int) -> None:
        tx = case(Transaction, valid=True, seed=seed)
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
        transactions = cases(Transaction, valid=True, count=3, seed=0)
        assert len(transactions) == 3
        for tx in transactions:
            assert 0 < tx["amount"] <= 1_000_000


class TestArticle:
    @pytest.mark.parametrize("seed", [0, 1, -1])
    def test_generate_valid_article(self, seed: int) -> None:
        article = case(Article, valid=True, seed=seed)
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
    @pytest.mark.parametrize("seed", [0, 1, -1])
    def test_api_validation_happy_path(self, seed: int) -> None:
        req = case(CreateUserRequest, valid=True, seed=seed)
        assert 18 <= req["age"] <= 120, "Age must be 18-120"
        assert len(req["password"]) >= 8, "Password too short"
        assert "@" in req["email"], "Invalid email"

    @pytest.mark.parametrize("seed", [0, 1, -1])
    def test_api_validation_sad_path(self, seed: int) -> None:
        invalid_req = case(
            CreateUserRequest,
            valid=False,
            strategy="random",
            seed=seed,
        )

        assert not (
            18 <= invalid_req["age"] <= 120
            and len(invalid_req["password"]) >= 8
            and re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", invalid_req["email"])
            and 3 <= len(invalid_req["nickname"]) <= 30
        )

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

    @pytest.mark.parametrize("seed", [0, 1, -1])
    def test_database_insert_compliance(self, seed: int) -> None:
        user = case(User, valid=True, seed=seed)
        assert 3 <= len(user["username"]) <= 255, "username length"
        assert len(user["full_name"]) <= 100, "full_name length"
        assert "@" in user["email"], "invalid email"


class TestRandomInvalidGeneration:
    @pytest.mark.parametrize("seed", [0, 1, -1])
    def test_fuzz_user_model(self, seed: int) -> None:
        user = case(User, valid=False, strategy="random", seed=seed)

        assert (
            len(user["username"]) < 3
            or not 2 <= len(user["full_name"]) <= 100
            or not re.match(
                r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user["email"]
            )
            or len(user["bio"]) > 500
        )

    @pytest.mark.parametrize("seed", [0, 1, -1])
    def test_fuzz_product_model(self, seed: int) -> None:
        product = case(Product, valid=False, strategy="random", seed=seed)
        max_int64 = 2**63 - 1

        assert (
            not re.match(r"^[A-Z0-9]{8}$", product["sku"])
            or not 1 <= len(product["name"]) <= 100
            or product["price"] <= 0
            or product["stock"] < 0
            or product["stock"] > max_int64
            or not 0 <= product["discount"] <= 100
        )
