"""Comprehensive automated test suite for Voltix TechStore API.

Covers:
- Workflow 1: Catalog browsing, filtering, CRUD operations.
- Workflow 2: Order checkout, stock verification/deduction, cancellation & restoration.
- Workflow 3: Customer reviews, rating recalculation.
- Workflow 4: Promo code validation and discount calculations.
- Edge cases: 400 Bad Request, 404 Not Found, 422 Validation Error, 204 No Content.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from storage.db import db


@pytest.fixture(autouse=True)
def reset_database():
    """Arrange: reset in-memory store before each test for complete test isolation."""
    db.seed_data()
    yield


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# System & Meta Tests
# =====================================================================
def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "documentation" in data
    assert data["documentation"] == "/docs"


# =====================================================================
# Workflow 1: Catalog & Products Tests
# =====================================================================
def test_list_products(client):
    res = client.get("/api/products")
    assert res.status_code == 200
    products = res.json()
    assert len(products) > 0
    # Check fields present
    first = products[0]
    assert "id" in first
    assert "title" in first
    assert "price" in first
    assert "sale_price" in first
    assert "stock" in first


def test_filter_products_by_category(client):
    res = client.get("/api/products?category=smartphones")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 2
    assert all(p["category"] == "smartphones" for p in items)


def test_search_products(client):
    res = client.get("/api/products?search=macbook")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert "macbook" in items[0]["title"].lower()


def test_filter_products_in_stock(client):
    res = client.get("/api/products?in_stock=true")
    assert res.status_code == 200
    items = res.json()
    assert all(p["stock"] > 0 for p in items)


def test_sort_products_price_asc(client):
    res = client.get("/api/products?sort_by=price_asc")
    assert res.status_code == 200
    items = res.json()
    prices = [p["sale_price"] for p in items]
    assert prices == sorted(prices)


def test_get_single_product_success(client):
    res = client.get("/api/products/1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert data["title"] == "iPhone 15 Pro"


def test_get_single_product_not_found(client):
    res = client.get("/api/products/9999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_create_product_success(client):
    new_item = {
        "title": "Sony WH-1000XM5",
        "description": "Industry Leading Wireless Noise Cancelling Headphones",
        "category": "mobile-accessories",
        "price": 399.99,
        "discount_percentage": 10.0,
        "stock": 25,
        "brand": "Sony",
        "thumbnail": "https://via.placeholder.com/300",
        "images": []
    }
    res = client.post("/api/products", json=new_item)
    assert res.status_code == 201
    created = res.json()
    assert created["id"] > 0
    assert created["title"] == "Sony WH-1000XM5"
    assert created["sale_price"] == round(399.99 * 0.9, 2)

    # Verify presence in list
    check = client.get(f"/api/products/{created['id']}")
    assert check.status_code == 200


def test_create_product_validation_error(client):
    # Invalid: price is 0 or negative
    bad_item = {
        "title": "Bad Product",
        "description": "Short",
        "category": "smartphones",
        "price": -10.0,
        "stock": 5,
        "brand": "Test"
    }
    res = client.post("/api/products", json=bad_item)
    assert res.status_code == 422


def test_update_product_partial(client):
    update_data = {"price": 1050.00, "stock": 50}
    res = client.patch("/api/products/1", json=update_data)
    assert res.status_code == 200
    updated = res.json()
    assert updated["price"] == 1050.00
    assert updated["stock"] == 50
    # Original title remains unchanged
    assert updated["title"] == "iPhone 15 Pro"


def test_update_product_not_found(client):
    res = client.patch("/api/products/9999", json={"stock": 10})
    assert res.status_code == 404


def test_delete_product_success(client):
    # 204 No Content
    res = client.delete("/api/products/1")
    assert res.status_code == 204

    # Subsequent GET returns 404
    res2 = client.get("/api/products/1")
    assert res2.status_code == 404


def test_delete_product_not_found(client):
    res = client.delete("/api/products/9999")
    assert res.status_code == 404


# =====================================================================
# Workflow 2: Reviews and Ratings Tests
# =====================================================================
def test_add_review_recalculates_rating(client):
    # iPhone 15 Pro (id=1) initially has 1 review with rating 5.0
    new_review = {
        "reviewer_name": "Maria Garcia",
        "rating": 3,
        "comment": "Good phone but a bit warm during gaming."
    }
    res = client.post("/api/products/1/reviews", json=new_review)
    assert res.status_code == 201
    created_rev = res.json()
    assert created_rev["rating"] == 3
    assert created_rev["reviewer_name"] == "Maria Garcia"

    # Fetch product to verify average rating recalculation: (5 + 3) / 2 = 4.0
    p_res = client.get("/api/products/1")
    product = p_res.json()
    assert product["rating"] == 4.0
    assert product["reviews_count"] == 2


def test_add_review_validation_error(client):
    # Rating > 5 is invalid
    bad_review = {
        "reviewer_name": "John",
        "rating": 6,
        "comment": "Super"
    }
    res = client.post("/api/products/1/reviews", json=bad_review)
    assert res.status_code == 422


def test_add_review_product_not_found(client):
    review = {
        "reviewer_name": "John Doe",
        "rating": 5,
        "comment": "Nice gadget!"
    }
    res = client.post("/api/products/9999/reviews", json=review)
    assert res.status_code == 404


# =====================================================================
# Workflow 3: Orders, Inventory Reservation & Cancellation Tests
# =====================================================================
def test_order_checkout_success_with_promo(client):
    # Check initial stock of iPhone 15 Pro (id 1) = 15
    initial_p = client.get("/api/products/1").json()
    initial_stock = initial_p["stock"]

    order_payload = {
        "customer_name": "Yersultan Temir",
        "email": "yersultan@example.com",
        "shipping_address": "Kabanbay Batyr 53, Astana",
        "items": [
            {"product_id": 1, "quantity": 2}
        ],
        "promo_code": "TECH10"
    }
    res = client.post("/api/orders", json=order_payload)
    assert res.status_code == 201
    order = res.json()

    assert order["id"] >= 1001
    assert order["customer_name"] == "Yersultan Temir"
    assert order["email"] == "yersultan@example.com"
    assert order["status"] == "confirmed"
    assert order["promo_code"] == "TECH10"

    # Math verification:
    # iPhone 15 Pro price 999 with 5% discount = 949.05 each
    # 2 items = 1898.10 subtotal
    # Promo TECH10 (10% off) = 189.81 discount
    # Subtotal after discount = 1708.29 >= 500 => free shipping ($0.0)
    assert order["discount"] > 0
    assert order["shipping"] == 0.0
    assert order["total"] == round(order["subtotal"] - order["discount"], 2)

    # Verify inventory was atomically deducted
    updated_p = client.get("/api/products/1").json()
    assert updated_p["stock"] == initial_stock - 2


def test_order_checkout_insufficient_stock_fails(client):
    # Try to order 20 units when only 15 available (within schema limit <= 50, but exceeds stock)
    order_payload = {
        "customer_name": "Buyer",
        "email": "buyer@example.com",
        "shipping_address": "Main Street 12, Almaty",
        "items": [
            {"product_id": 1, "quantity": 20}
        ]
    }
    res = client.post("/api/orders", json=order_payload)
    assert res.status_code == 400
    assert "insufficient stock" in res.json()["detail"].lower()


def test_order_checkout_invalid_promo_fails(client):
    order_payload = {
        "customer_name": "Buyer",
        "email": "buyer@example.com",
        "shipping_address": "Main Street 12, Almaty",
        "items": [
            {"product_id": 1, "quantity": 1}
        ],
        "promo_code": "NOT_A_REAL_CODE"
    }
    res = client.post("/api/orders", json=order_payload)
    assert res.status_code == 400
    assert "invalid" in res.json()["detail"].lower()


def test_order_checkout_invalid_email_fails(client):
    order_payload = {
        "customer_name": "Buyer",
        "email": "not-an-email",
        "shipping_address": "Main Street 12, Almaty",
        "items": [
            {"product_id": 1, "quantity": 1}
        ]
    }
    res = client.post("/api/orders", json=order_payload)
    assert res.status_code == 422


def test_order_cancellation_restores_stock(client):
    # Place order for 3 items
    initial_stock = client.get("/api/products/1").json()["stock"]

    order_payload = {
        "customer_name": "Test User",
        "email": "user@test.kz",
        "shipping_address": "Dostyk Ave 45",
        "items": [{"product_id": 1, "quantity": 3}]
    }
    order_res = client.post("/api/orders", json=order_payload)
    order_id = order_res.json()["id"]

    # Stock should be reduced
    assert client.get("/api/products/1").json()["stock"] == initial_stock - 3

    # Cancel the order
    cancel_res = client.post(f"/api/orders/{order_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Stock MUST be restored!
    assert client.get("/api/products/1").json()["stock"] == initial_stock

    # Cancelling again should return 400
    double_cancel = client.post(f"/api/orders/{order_id}/cancel")
    assert double_cancel.status_code == 400


# =====================================================================
# Workflow 4: Promo Code Service Tests
# =====================================================================
def test_promo_validation_valid(client):
    res = client.post("/api/promos/validate", json={"code": "TECH10", "subtotal": 200.0})
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["discount_percentage"] == 10.0
    assert data["discount_amount"] == 20.0


def test_promo_validation_invalid(client):
    res = client.post("/api/promos/validate", json={"code": "FAKECAP", "subtotal": 100.0})
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is False
    assert data["discount_amount"] == 0.0


# =====================================================================
# Frontend Compatibility Tests
# =====================================================================
def test_category_compatibility_endpoint(client):
    res = client.get("/api/products/category/smartphones")
    assert res.status_code == 200
    data = res.json()
    assert "products" in data
    assert len(data["products"]) >= 2


def test_cart_add_compatibility_endpoint(client):
    payload = {
        "userId": 1,
        "products": [{"id": 1, "quantity": 1}]
    }
    res = client.post("/api/carts/add", json=payload)
    assert res.status_code == 201
    assert res.json()["id"] >= 1001
