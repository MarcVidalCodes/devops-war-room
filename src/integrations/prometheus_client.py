"""
Prometheus API Client

This module provides a Python interface to query Prometheus's HTTP API.
Agents will use this to programmatically fetch alerts and metrics.

Prometheus API Documentation: https://prometheus.io/docs/prometheus/latest/querying/api/
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class PrometheusClient:
    """
    Client for interacting with Prometheus HTTP API.

    Attributes:
        base_url: Prometheus server URL (e.g., 'http://prometheus:9090')
        timeout: HTTP request timeout in seconds
    """

    def __init__(self, base_url: str = "http://localhost:9090", timeout: int = 10):
        """
        Initialize Prometheus client.

        Args:
            base_url: URL of Prometheus server (default: http://localhost:9090)
            timeout: Request timeout in seconds (default: 10)
        """
        self.base_url = base_url.rstrip("/")  # Remove trailing slash if present
        self.timeout = timeout

    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        Get all current alerts from Prometheus.

        Returns a list of alerts with their state (inactive, pending, firing).
        MonitorAgent will use this to detect when alerts fire.

        Returns:
            List of alert dictionaries with keys:
            - state: 'inactive', 'pending', or 'firing'
            - labels: Alert labels (alertname, severity, etc.)
            - annotations: Human-readable descriptions
            - activeAt: When alert started firing
            - value: Current metric value that triggered alert

        Example response:
            [
                {
                    "state": "firing",
                    "labels": {
                        "alertname": "HighErrorRate",
                        "severity": "critical"
                    },
                    "annotations": {
                        "summary": "Error rate above threshold"
                    },
                    "activeAt": "2025-11-19T10:30:00Z",
                    "value": "0.08"
                }
            ]
        """
        url = f"{self.base_url}/api/v1/alerts"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()  # Raise exception for 4xx/5xx status codes

            data = response.json()

            # Prometheus API wraps results in {'status': 'success', 'data': {...}}
            if data.get("status") == "success":
                return data.get("data", {}).get("alerts", [])
            else:
                raise Exception(f"Prometheus API error: {data}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch alerts from Prometheus: {e}")

    def query(self, promql: str) -> Dict[str, Any]:
        """
        Execute a PromQL query at the current time (instant query).

        Use this when you want the current value of a metric.
        Example: "What's the error rate RIGHT NOW?"

        Args:
            promql: PromQL query string (e.g., 'rate(http_requests_total[5m])')

        Returns:
            Query result with 'resultType' and 'result' keys.
            Result type can be:
            - 'vector': Instant vector (most common)
            - 'matrix': Range vector
            - 'scalar': Single number
            - 'string': String value

        Example:
            client.query('rate(http_requests_total[5m])')
            Returns:
            {
                'resultType': 'vector',
                'result': [
                    {
                        'metric': {'endpoint': '/products', 'method': 'GET'},
                        'value': [1732017600, '12.5']  # [timestamp, value]
                    }
                ]
            }
        """
        url = f"{self.base_url}/api/v1/query"
        params = {"query": promql}

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if data.get("status") == "success":
                return data.get("data", {})
            else:
                error_msg = data.get("error", "Unknown error")
                raise Exception(f"PromQL query failed: {error_msg}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to execute PromQL query: {e}")

    def query_range(
        self,
        promql: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        step: str = "15s",
    ) -> Dict[str, Any]:
        """
        Execute a PromQL query over a time range (range query).

        Use this when you want historical data over a period.
        Example: "What was the error rate over the last hour?"

        Args:
            promql: PromQL query string
            start: Start time (default: 1 hour ago)
            end: End time (default: now)
            step: Query resolution (default: 15s - matches scrape interval)

        Returns:
            Query result with time series data.

        Example:
            client.query_range(
                'rate(http_requests_total[5m])',
                start=datetime.now() - timedelta(hours=1)
            )
            Returns:
            {
                'resultType': 'matrix',
                'result': [
                    {
                        'metric': {'endpoint': '/products'},
                        'values': [
                            [1732014000, '10.2'],  # [timestamp, value]
                            [1732014015, '11.5'],
                            [1732014030, '12.1'],
                            ...
                        ]
                    }
                ]
            }
        """
        url = f"{self.base_url}/api/v1/query_range"

        # Default to last 1 hour if not specified
        if end is None:
            end = datetime.now()
        if start is None:
            start = end - timedelta(hours=1)

        # Convert datetime to Unix timestamp
        params = {
            "query": promql,
            "start": int(start.timestamp()),
            "end": int(end.timestamp()),
            "step": step,
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if data.get("status") == "success":
                return data.get("data", {})
            else:
                error_msg = data.get("error", "Unknown error")
                raise Exception(f"PromQL range query failed: {error_msg}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to execute PromQL range query: {e}")

    def get_firing_alerts(self) -> List[Dict[str, Any]]:
        """
        Get only alerts that are currently firing.

        Convenience method that filters get_alerts() to only firing alerts.
        MonitorAgent will primarily use this.

        Returns:
            List of firing alerts (empty list if no alerts firing)
        """
        all_alerts = self.get_alerts()
        return [alert for alert in all_alerts if alert.get("state") == "firing"]

    def is_healthy(self) -> bool:
        """
        Check if Prometheus server is reachable and healthy.

        Returns:
            True if Prometheus is healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/-/healthy"
            response = requests.get(url, timeout=self.timeout)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
