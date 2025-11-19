from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from flask import Response

http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

http_errors_5xx = Counter("http_errors_5xx", "Total 5xx errors", ["endpoint"])

db_connection_pool_usage = Gauge(
    "db_connection_pool_usage", "Current database connection pool usage"
)

memory_leak_objects = Gauge("memory_leak_objects", "Number of leaked objects in memory")

inventory_race_conditions = Counter(
    "inventory_race_conditions", "Number of inventory race condition occurrences"
)


def metrics_endpoint():
    return Response(generate_latest(REGISTRY), mimetype="text/plain")
