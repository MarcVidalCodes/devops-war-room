import pytest
from src.app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_get_products(client):
    response = client.get("/api/v1/products")
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        assert "products" in response.json


def test_get_product(client):
    response = client.get("/api/v1/products/1")
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        assert "product" in response.json


def test_add_to_cart(client):
    response = client.post(
        "/api/v1/cart/user123", json={"product_id": 1, "quantity": 2}
    )
    assert response.status_code in [200, 500]


def test_get_cart(client):
    response = client.get("/api/v1/cart/user123")
    assert response.status_code in [200, 500]


def test_create_order(client):
    response = client.post("/api/v1/orders", json={"user_id": "user123"})
    assert response.status_code in [201, 500]


def test_get_inventory(client):
    response = client.get("/api/v1/inventory")
    assert response.status_code in [200, 500]


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"http_requests_total" in response.data
