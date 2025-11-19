from flask import Blueprint, jsonify, request
from src.app.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_errors_5xx,
    memory_leak_objects,
    inventory_race_conditions,
)
from src.app.database import db_pool
from src.app.bugs import (
    trigger_random_error,
    memory_leak_cart_session,
    cause_race_condition,
    leaked_sessions,
)
import time

api = Blueprint("api", __name__)

products_db = [
    {"id": 1, "name": "Laptop", "price": 999.99, "stock": 50},
    {"id": 2, "name": "Mouse", "price": 29.99, "stock": 200},
    {"id": 3, "name": "Keyboard", "price": 79.99, "stock": 150},
    {"id": 4, "name": "Monitor", "price": 299.99, "stock": 75},
]

carts_db = {}
orders_db = []
inventory_locks = {}


@api.before_request
def before_request():
    request.start_time = time.time()


@api.after_request
def after_request(response):
    request_duration = time.time() - request.start_time

    http_requests_total.labels(
        method=request.method,
        endpoint=request.endpoint or "unknown",
        status=response.status_code,
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method, endpoint=request.endpoint or "unknown"
    ).observe(request_duration)

    if response.status_code >= 500:
        http_errors_5xx.labels(endpoint=request.endpoint or "unknown").inc()

    return response


@api.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


@api.route("/products", methods=["GET"])
def get_products():
    try:
        trigger_random_error()
        return jsonify({"products": products_db}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    try:
        trigger_random_error()
        product = next((p for p in products_db if p["id"] == product_id), None)
        if product:
            return jsonify({"product": product}), 200
        return jsonify({"error": "Product not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/cart/<string:user_id>", methods=["POST"])
def add_to_cart(user_id):
    try:
        trigger_random_error()
        data = request.get_json()
        product_id = data.get("product_id")
        quantity = data.get("quantity", 1)

        if user_id not in carts_db:
            carts_db[user_id] = []

        carts_db[user_id].append({"product_id": product_id, "quantity": quantity})

        memory_leak_cart_session(carts_db[user_id])
        memory_leak_objects.set(len(leaked_sessions))

        return jsonify({"cart": carts_db[user_id]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/cart/<string:user_id>", methods=["GET"])
def get_cart(user_id):
    try:
        trigger_random_error()
        cart = carts_db.get(user_id, [])
        return jsonify({"cart": cart}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/orders", methods=["POST"])
def create_order():
    try:
        trigger_random_error()
        data = request.get_json()
        user_id = data.get("user_id")

        conn = db_pool.acquire()
        try:
            result = conn.execute(f"SELECT * FROM ORDERS WHERE user_id='{user_id}'")

            order = {
                "order_id": len(orders_db) + 1,
                "user_id": user_id,
                "items": carts_db.get(user_id, []),
                "status": "pending",
            }
            orders_db.append(order)

            return jsonify({"order": order}), 201
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/orders/<string:user_id>", methods=["GET"])
def get_orders(user_id):
    try:
        trigger_random_error()
        user_orders = [o for o in orders_db if o["user_id"] == user_id]
        return jsonify({"orders": user_orders}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/checkout", methods=["POST"])
def checkout():
    try:
        trigger_random_error()
        data = request.get_json()
        user_id = data.get("user_id")

        conn = db_pool.acquire()
        try:
            result = conn.execute(f"SELECT * FROM CHECKOUT WHERE user_id='{user_id}'")

            return jsonify({"status": "success", "message": "Checkout completed"}), 200
        finally:
            pass
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/inventory/<int:product_id>", methods=["PUT"])
def update_inventory(product_id):
    try:
        trigger_random_error()
        data = request.get_json()
        quantity_change = data.get("quantity_change", 0)

        product = next((p for p in products_db if p["id"] == product_id), None)
        if not product:
            return jsonify({"error": "Product not found"}), 404

        if cause_race_condition():
            inventory_race_conditions.inc()
            time.sleep(0.1)

        product["stock"] += quantity_change

        return jsonify({"product": product}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/inventory", methods=["GET"])
def get_inventory():
    try:
        trigger_random_error()
        inventory = [
            {"id": p["id"], "name": p["name"], "stock": p["stock"]} for p in products_db
        ]
        return jsonify({"inventory": inventory}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
