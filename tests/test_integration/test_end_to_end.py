from dataclasses import dataclass, field
import math
import re
from typing import Annotated

from conformly import case, cases
from conformly.constraints import (
    GreaterOrEqual,
    GreaterThan,
    LessOrEqual,
    LessThan,
    MaxLength,
    MinLength,
    Pattern,
)


@dataclass
class User:
    """Social media user"""

    username: Annotated[str, MinLength(3)]
    full_name: Annotated[str, MinLength(2), MaxLength(100)]
    email: Annotated[
        str,
        Pattern(r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
    ]
    bio: Annotated[str, MaxLength(500)]


@dataclass
class BlogPost:
    """Blog post model"""

    title: Annotated[str, "min_length=5", "max_length=200"]
    slug: Annotated[str, "pattern=^[a-z0-9-]+$"]
    content: Annotated[str, "min_length=10"]
    views: Annotated[int, "ge=0"]
    rating: Annotated[float, "ge=0", "le=5"]


@dataclass
class Product:
    """E-commerce product"""

    sku: str = field(metadata={"pattern": r"^[A-Z0-9]{8}$"})
    name: str = field(metadata={"min_length": 1, "max_length": 100})
    price: float = field(metadata={"gt": 0})
    stock: int = field(metadata={"ge": 0})
    discount: float = field(metadata={"ge": 0, "le": 100})


@dataclass
class CreateUserRequest:
    """User registration request"""

    age: Annotated[int, GreaterOrEqual(18), LessThan(120)]
    email: Annotated[str, Pattern(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")]
    password: Annotated[str, MinLength(8), MaxLength(128)]
    nickname: Annotated[str, MinLength(3), MaxLength(30)]


@dataclass
class OrderItem:
    """Line item in an order"""

    product_id: Annotated[int, GreaterThan(0)]
    quantity: Annotated[int, GreaterOrEqual(1), LessOrEqual(1000)]
    unit_price: Annotated[float, GreaterThan(0)]


@dataclass
class Transaction:
    """Bank transfer"""

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


class TestUserModel:
    def test_generate_valid_user(self):
        for _ in range(20):
            user = case(User, valid=True)
            assert len(user["username"]) >= 3
            assert 2 <= len(user["full_name"]) <= 100
            assert re.match(
                r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user["email"]
            )
            assert len(user["bio"]) <= 500

    def test_invalid_user_short_username(self):
        invalid = case(User, valid=False, strategy="username")
        assert len(invalid["username"]) == 2

    def test_invalid_user_long_full_name(self):
        invalid = case(User, valid=False, strategy="full_name")
        n = len(invalid["full_name"])
        assert n < 2 or n > 100

    def test_multiple_users(self):
        users = cases(User, valid=True, count=5)
        assert len(users) == 5
        for user in users:
            assert len(user["username"]) >= 3


class TestBlogPostModel:
    def test_generate_valid_post(self):
        for _ in range(10):
            post = case(BlogPost, valid=True)
            assert 5 <= len(post["title"]) <= 200
            assert re.match(r"^[a-z0-9-]+$", post["slug"])
            assert len(post["content"]) >= 10
            assert post["views"] >= 0
            assert 0 <= post["rating"] <= 5

    def test_invalid_post_short_title(self):
        invalid = case(BlogPost, valid=False, strategy="title")
        assert len(invalid["title"]) == 4

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
            assert 0 <= product["discount"] <= 100

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

    def test_invalid_weak_password(self):
        invalid = case(CreateUserRequest, valid=False, strategy="password")
        assert len(invalid["password"]) == 7  # min_length=8 -> generates 7

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

    def test_invalid_short_title(self):
        invalid = case(Article, valid=False, strategy="title")
        assert len(invalid["title"]) == 4  # min_length=5 -> generates 4


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
