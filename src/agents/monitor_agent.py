"""
MonitorAgent - Autonomous Alert Detection

This agent continuously monitors Prometheus for firing alerts.
It polls the Prometheus API every 30 seconds and logs when alerts change state.

Key Responsibilities:
- Detect when alerts start firing
- Detect when alerts are resolved
- Track alert history
- Log all state changes

This is the entry point for the autonomous incident response system.
When an alert fires, MonitorAgent will eventually trigger TriageAgent (Part 2.3).
"""

import time
import logging
from typing import Dict, Set, List, Any
from datetime import datetime

from src.integrations.prometheus_client import PrometheusClient


class MonitorAgent:
    """
    Autonomous agent that monitors Prometheus alerts.

    Attributes:
        client: PrometheusClient instance for querying Prometheus
        check_interval: Seconds between alert checks (default: 30)
        firing_alerts: Set of currently firing alert names
        logger: Logger for agent output
    """

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        check_interval: int = 30,
    ):
        """
        Initialize MonitorAgent.

        Args:
            prometheus_url: URL of Prometheus server
            check_interval: Seconds between alert checks (default: 30)
        """
        self.client = PrometheusClient(base_url=prometheus_url)
        self.check_interval = check_interval
        self.firing_alerts: Set[str] = set()  # Track which alerts are currently firing
        self.logger = logging.getLogger(__name__)

        # Configure logging to console
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def start(self) -> None:
        """
        Start the monitoring loop.

        This runs indefinitely until interrupted (Ctrl+C).
        Checks Prometheus alerts every check_interval seconds.
        """
        self.logger.info("=" * 60)
        self.logger.info("MonitorAgent starting...")
        self.logger.info(f"Prometheus URL: {self.client.base_url}")
        self.logger.info(f"Check interval: {self.check_interval} seconds")
        self.logger.info("=" * 60)

        # Verify Prometheus is reachable before starting loop
        if not self.client.is_healthy():
            self.logger.error("Prometheus is not reachable. Exiting.")
            self.logger.error("Make sure Docker containers are running: docker compose up -d")
            return

        self.logger.info("Prometheus is healthy. Starting monitoring loop...")
        self.logger.info("Press Ctrl+C to stop\n")

        try:
            # Infinite loop - runs until user presses Ctrl+C
            while True:
                self._check_alerts()
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("\nMonitorAgent stopped by user")
            self._print_summary()

        except Exception as e:
            self.logger.error(f"MonitorAgent crashed: {str(e)}")
            raise

    def _check_alerts(self) -> None:
        """
        Check current alert state and detect changes.

        This is called every check_interval seconds.
        Compares current alerts with previous state to detect:
        - New alerts that started firing
        - Alerts that were resolved
        """
        try:
            # Get all alerts from Prometheus
            alerts = self.client.get_alerts()

            if alerts is None:
                self.logger.warning("Failed to fetch alerts from Prometheus")
                return

            # Extract names of currently firing alerts
            current_firing = {
                alert["labels"]["alertname"]
                for alert in alerts
                if alert.get("state") == "firing"
            }

            # Detect new alerts (firing now, but weren't before)
            new_alerts = current_firing - self.firing_alerts

            # Detect resolved alerts (were firing, but aren't now)
            resolved_alerts = self.firing_alerts - current_firing

            # Log new alerts
            for alert_name in new_alerts:
                alert_data = self._get_alert_by_name(alerts, alert_name)
                self._log_new_alert(alert_name, alert_data)

            # Log resolved alerts
            for alert_name in resolved_alerts:
                self._log_resolved_alert(alert_name)

            # Update our tracking of firing alerts
            self.firing_alerts = current_firing

            # Log status every check (heartbeat)
            if not new_alerts and not resolved_alerts:
                self.logger.info(
                    f"Status check: {len(current_firing)} alerts firing"
                )

        except Exception as e:
            self.logger.error(f"Error checking alerts: {str(e)}")

    def _get_alert_by_name(
        self, alerts: List[Dict[str, Any]], alert_name: str
    ) -> Dict[str, Any]:
        """
        Find alert details by name.

        Args:
            alerts: List of all alerts from Prometheus
            alert_name: Name of alert to find

        Returns:
            Alert dictionary with full details
        """
        for alert in alerts:
            if alert["labels"]["alertname"] == alert_name:
                return alert
        return {}

    def _log_new_alert(self, alert_name: str, alert_data: Dict[str, Any]) -> None:
        """
        Log when a new alert starts firing.

        Args:
            alert_name: Name of the alert
            alert_data: Full alert details from Prometheus
        """
        self.logger.warning("=" * 60)
        self.logger.warning(f"ALERT FIRING: {alert_name}")
        self.logger.warning("=" * 60)

        # Extract useful information from alert
        labels = alert_data.get("labels", {})
        annotations = alert_data.get("annotations", {})
        value = alert_data.get("value", "N/A")

        self.logger.warning(f"Severity: {labels.get('severity', 'unknown')}")
        self.logger.warning(f"Summary: {annotations.get('summary', 'N/A')}")
        self.logger.warning(f"Description: {annotations.get('description', 'N/A')}")
        self.logger.warning(f"Current value: {value}")
        self.logger.warning(f"Started at: {alert_data.get('activeAt', 'N/A')}")
        self.logger.warning("=" * 60 + "\n")

        # TODO (Part 2.3): Trigger TriageAgent here
        # triage_agent.investigate(alert_name, alert_data)

    def _log_resolved_alert(self, alert_name: str) -> None:
        """
        Log when an alert is resolved.

        Args:
            alert_name: Name of the alert that resolved
        """
        self.logger.info("=" * 60)
        self.logger.info(f"ALERT RESOLVED: {alert_name}")
        self.logger.info("=" * 60 + "\n")

    def _print_summary(self) -> None:
        """Print summary when agent is stopped."""
        self.logger.info("=" * 60)
        self.logger.info("MonitorAgent Summary")
        self.logger.info("=" * 60)
        self.logger.info(f"Alerts currently firing: {len(self.firing_alerts)}")
        if self.firing_alerts:
            for alert in self.firing_alerts:
                self.logger.info(f"  - {alert}")
        self.logger.info("=" * 60)


def main():
    """
    Entry point for running MonitorAgent standalone.

    Usage:
        python -m src.agents.monitor_agent
    """
    agent = MonitorAgent(
        prometheus_url="http://localhost:9090",
        check_interval=30,
    )
    agent.start()


if __name__ == "__main__":
    main()
