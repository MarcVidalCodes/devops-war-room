"""
Demo script for Prometheus API client.

This script shows you how to use the PrometheusClient to query Prometheus.
This is NOT an automated test - it's a learning tool / manual verification script.

Run this after starting your Docker containers to see the client in action.

Usage:
    python -m src.integrations.demo_prometheus_client
"""

from src.integrations.prometheus_client import PrometheusClient


def main():
    print("=" * 60)
    print("Prometheus API Client - Demo")
    print("=" * 60)

    # Initialize client (change URL if Prometheus is on different host/port)
    client = PrometheusClient(base_url="http://localhost:9090")

    # Test 1: Check if Prometheus is healthy
    print("\n1. Checking Prometheus health...")
    if client.is_healthy():
        print("Prometheus is healthy!")
    else:
        print("Prometheus is not reachable. Make sure Docker containers are running.")
        print("   Run: docker compose up -d")
        return

    # Test 2: Get all alerts
    print("\n2. Fetching all alerts...")
    try:
        alerts = client.get_alerts()
        print(f"Found {len(alerts)} alerts")

        for alert in alerts:
            state = alert.get("state")
            alertname = alert.get("labels", {}).get("alertname")
            print(f"  - {alertname}: {state}")

    except Exception as e:
        print(f"Error fetching alerts: {e}")

    # Test 3: Get only firing alerts
    print("\n3. Fetching FIRING alerts...")
    try:
        firing_alerts = client.get_firing_alerts()
        if firing_alerts:
            print(f"WARNING: {len(firing_alerts)} alerts are firing!")
            for alert in firing_alerts:
                alertname = alert.get("labels", {}).get("alertname")
                summary = alert.get("annotations", {}).get("summary")
                print(f"  - {alertname}: {summary}")
        else:
            print("No alerts firing (system is healthy)")

    except Exception as e:
        print(f"Error fetching firing alerts: {e}")

    # Test 4: Execute instant PromQL query
    print("\n4. Executing instant PromQL query...")
    print("   Query: http_requests_total")
    try:
        result = client.query("http_requests_total")
        print(f"   Result type: {result.get('resultType')}")
        print(f"   Number of series: {len(result.get('result', []))}")

        # Show first 3 results
        for i, series in enumerate(result.get("result", [])[:3]):
            metric = series.get("metric", {})
            endpoint = metric.get("endpoint", "unknown")
            method = metric.get("method", "unknown")
            status = metric.get("status", "unknown")
            value = series.get("value", [None, "0"])[1]
            print(f"   [{i+1}] {endpoint} {method} {status} = {value} total requests")

    except Exception as e:
        print(f"Error executing query: {e}")

    # Test 5: Execute range query
    print("\n5. Executing range PromQL query...")
    print("   Query: http_errors_5xx_total (last 5 minutes)")
    try:
        from datetime import datetime, timedelta

        result = client.query_range(
            "http_errors_5xx_total", start=datetime.now() - timedelta(minutes=5)
        )

        print(f"   Result type: {result.get('resultType')}")
        num_series = len(result.get("result", []))
        print(f"   Number of series: {num_series}")

        if num_series > 0:
            series = result.get("result", [])[0]
            values = series.get("values", [])
            print(f"   Data points: {len(values)}")
            if values:
                first_value = values[0]
                last_value = values[-1]
                print(f"   First: {first_value}")
                print(f"   Last:  {last_value}")

    except Exception as e:
        print(f"Error executing range query: {e}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
