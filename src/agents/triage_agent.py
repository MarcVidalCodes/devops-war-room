import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from src.integrations.prometheus_client import PrometheusClient


class TriageAgent:
    """
    Agent that investigates alerts by querying Prometheus for additional context.

    When an alert fires, this agent gathers relevant metrics to understand:
    - What's happening (error rates, latencies, resource usage)
    - Which services/endpoints are affected
    - Time-series data to show trends

    This data is then packaged for later analysis by AI agents.
    """

    def __init__(
        self, prometheus_url: str = "http://localhost:9090", timeout: int = 10
    ):
        """
        Initialize the TriageAgent.

        Args:
            prometheus_url: URL of Prometheus server
            timeout: Request timeout in seconds
        """
        self.client = PrometheusClient(prometheus_url, timeout)
        self.logger = logging.getLogger(__name__)

        # Define investigation queries for each alert type
        self.investigation_queries = {
            "HighErrorRate": [
                ("error_rate_by_endpoint", "rate(http_errors_5xx_total[5m])"),
                ("total_request_rate", "rate(http_requests_total[5m])"),
                (
                    "error_percentage",
                    "(rate(http_errors_5xx_total[5m]) / rate(http_requests_total[5m])) * 100",
                ),
            ],
            "SlowRequests": [
                (
                    "p50_latency",
                    "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
                ),
                (
                    "p95_latency",
                    "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                ),
                (
                    "p99_latency",
                    "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
                ),
                ("request_rate_by_endpoint", "rate(http_requests_total[5m])"),
            ],
            "DatabasePoolExhaustion": [
                ("current_pool_usage", "db_connection_pool_usage"),
                ("pool_usage_5m_avg", "avg_over_time(db_connection_pool_usage[5m])"),
                (
                    "checkout_request_rate",
                    'rate(http_requests_total{endpoint="api.checkout"}[5m])',
                ),
            ],
            "MemoryLeak": [
                ("current_leaked_objects", "memory_leak_objects"),
                ("leak_growth_rate", "rate(memory_leak_objects[10m])"),
                (
                    "cart_request_rate",
                    'rate(http_requests_total{endpoint="api.add_to_cart"}[5m])',
                ),
            ],
            "InventoryRaceCondition": [
                ("race_condition_rate", "rate(inventory_race_conditions_total[5m])"),
                (
                    "inventory_update_rate",
                    'rate(http_requests_total{endpoint="api.update_inventory"}[5m])',
                ),
                (
                    "race_condition_percentage",
                    '(rate(inventory_race_conditions_total[5m]) / rate(http_requests_total{endpoint="api.update_inventory"}[5m])) * 100',
                ),
            ],
        }

    def investigate_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Investigate a firing alert by gathering relevant metrics.

        Args:
            alert: Alert object from Prometheus with labels, annotations, etc.

        Returns:
            Dictionary containing:
            - alert_info: Original alert details
            - metrics: Current metric values
            - time_series: Historical data for trend analysis
            - investigation_summary: Human-readable summary
        """
        alert_name = alert["labels"]["alertname"]

        self.logger.info(f"Investigating alert: {alert_name}")

        # Gather current metric values
        metrics = self._query_current_metrics(alert_name)

        # Gather time-series data (last 15 minutes)
        time_series = self._query_time_series(alert_name)

        # Create investigation report
        report = {
            "alert_info": {
                "name": alert_name,
                "severity": alert["labels"].get("severity", "unknown"),
                "summary": alert["annotations"].get("summary", ""),
                "description": alert["annotations"].get("description", ""),
                "started_at": alert.get("activeAt", ""),
                "current_value": alert.get("value", ""),
            },
            "metrics": metrics,
            "time_series": time_series,
            "investigation_summary": self._generate_summary(alert_name, metrics),
            "investigated_at": datetime.utcnow().isoformat(),
        }

        return report

    def _query_current_metrics(self, alert_name: str) -> Dict[str, Any]:
        """
        Query current metric values relevant to the alert.

        Args:
            alert_name: Name of the alert being investigated

        Returns:
            Dictionary of metric names to their current values
        """
        metrics = {}

        if alert_name not in self.investigation_queries:
            self.logger.warning(
                f"No investigation queries defined for alert: {alert_name}"
            )
            return metrics

        for metric_name, query in self.investigation_queries[alert_name]:
            try:
                data = self.client.query(query)
                result = data.get("result", [])
                metrics[metric_name] = self._parse_query_result(result)
            except Exception as e:
                self.logger.error(f"Error querying {metric_name}: {e}")
                metrics[metric_name] = {"error": str(e)}

        return metrics

    def _query_time_series(
        self, alert_name: str, duration_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Query time-series data for trend analysis.

        Args:
            alert_name: Name of the alert being investigated
            duration_minutes: How far back to look (default: 15 minutes)

        Returns:
            Dictionary of metric names to their time-series data
        """
        time_series = {}

        if alert_name not in self.investigation_queries:
            return time_series

        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=duration_minutes)

        for metric_name, query in self.investigation_queries[alert_name]:
            try:
                data = self.client.query_range(
                    promql=query,
                    start=start_time,
                    end=end_time,
                    step="30s",  # Data point every 30 seconds
                )
                result = data.get("result", [])
                time_series[metric_name] = self._parse_range_result(result)
            except Exception as e:
                self.logger.error(f"Error querying time series for {metric_name}: {e}")
                time_series[metric_name] = {"error": str(e)}

        return time_series

    def _parse_query_result(self, result: List[Dict[str, Any]]) -> Any:
        """
        Parse instant query result into simplified format.

        Args:
            result: Query result from Prometheus

        Returns:
            Parsed result (value or list of values with labels)
        """
        if not result:
            return None

        if len(result) == 1:
            # Single value
            return {
                "value": float(result[0]["value"][1]),
                "labels": result[0]["metric"],
            }
        else:
            # Multiple values (e.g., per endpoint)
            return [
                {
                    "value": float(item["value"][1]),
                    "labels": item["metric"],
                }
                for item in result
            ]

    def _parse_range_result(self, result: List[Dict[str, Any]]) -> Any:
        """
        Parse range query result into simplified format.

        Args:
            result: Range query result from Prometheus

        Returns:
            Parsed time-series data
        """
        if not result:
            return None

        if len(result) == 1:
            # Single time series
            return {
                "labels": result[0]["metric"],
                "values": [
                    {"timestamp": val[0], "value": float(val[1])}
                    for val in result[0]["values"]
                ],
            }
        else:
            # Multiple time series (e.g., per endpoint)
            return [
                {
                    "labels": item["metric"],
                    "values": [
                        {"timestamp": val[0], "value": float(val[1])}
                        for val in item["values"]
                    ],
                }
                for item in result
            ]

    def _generate_summary(self, alert_name: str, metrics: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of findings.

        Args:
            alert_name: Name of the alert
            metrics: Current metric values

        Returns:
            Human-readable summary string
        """
        summary_parts = [f"Investigation findings for {alert_name}:"]

        for metric_name, metric_data in metrics.items():
            if isinstance(metric_data, dict) and "error" in metric_data:
                summary_parts.append(
                    f"  - {metric_name}: Error - {metric_data['error']}"
                )
            elif isinstance(metric_data, dict) and "value" in metric_data:
                summary_parts.append(f"  - {metric_name}: {metric_data['value']:.4f}")
            elif isinstance(metric_data, list):
                summary_parts.append(
                    f"  - {metric_name}: {len(metric_data)} data points"
                )

        return "\n".join(summary_parts)

    def investigate_multiple_alerts(
        self, alerts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Investigate multiple alerts in batch.

        Args:
            alerts: List of alert objects

        Returns:
            List of investigation reports
        """
        reports = []

        for alert in alerts:
            try:
                report = self.investigate_alert(alert)
                reports.append(report)
            except Exception as e:
                self.logger.error(
                    f"Error investigating alert {alert.get('labels', {}).get('alertname', 'unknown')}: {e}"
                )
                reports.append(
                    {
                        "alert_info": {
                            "name": alert.get("labels", {}).get("alertname", "unknown")
                        },
                        "error": str(e),
                    }
                )

        return reports
