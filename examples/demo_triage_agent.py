"""
Demo script for TriageAgent.

This demonstrates how TriageAgent investigates alerts by querying
Prometheus for additional context and metrics.
"""

import logging
from src.agents.triage_agent import TriageAgent
from src.integrations.prometheus_client import PrometheusClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("TriageAgent Demo")
    print("=" * 60)
    print()
    print("This agent investigates firing alerts by gathering")
    print("additional metrics and context from Prometheus.")
    print()
    print("To see it in action:")
    print("  1. Make sure alerts are firing (run continuous_traffic.sh)")
    print("  2. This script will investigate each alert")
    print()
    print("=" * 60)
    print()
    
    # Initialize agents
    prometheus_client = PrometheusClient("http://localhost:9090")
    triage_agent = TriageAgent("http://localhost:9090")
    
    # Check Prometheus health
    if not prometheus_client.is_healthy():
        logger.error("Prometheus is not healthy!")
        return
    
    logger.info("Prometheus is healthy")
    
    # Get current firing alerts
    alerts = prometheus_client.get_firing_alerts()
    
    if not alerts:
        print("\n⚠️  No alerts currently firing.")
        print("Run: bash examples/continuous_traffic.sh")
        print("Wait 30-60 seconds, then run this script again.")
        return
    
    print(f"\n🔍 Found {len(alerts)} firing alert(s)\n")
    
    # Investigate each alert
    for i, alert in enumerate(alerts, 1):
        alert_name = alert["labels"]["alertname"]
        severity = alert["labels"].get("severity", "unknown")
        
        print(f"\n{'=' * 60}")
        print(f"Alert {i}/{len(alerts)}: {alert_name} ({severity})")
        print(f"{'=' * 60}\n")
        
        # Run investigation
        report = triage_agent.investigate_alert(alert)
        
        # Display findings
        print("📊 Investigation Report:")
        print(f"  Alert: {report['alert_info']['name']}")
        print(f"  Severity: {report['alert_info']['severity']}")
        print(f"  Summary: {report['alert_info']['summary']}")
        print(f"  Description: {report['alert_info']['description']}")
        print()
        
        print("📈 Current Metrics:")
        for metric_name, metric_data in report['metrics'].items():
            if isinstance(metric_data, dict) and "error" in metric_data:
                print(f"  ❌ {metric_name}: Error - {metric_data['error']}")
            elif isinstance(metric_data, dict) and "value" in metric_data:
                print(f"  ✓ {metric_name}: {metric_data['value']:.4f}")
            elif isinstance(metric_data, list):
                print(f"  ✓ {metric_name}:")
                for item in metric_data[:3]:  # Show first 3
                    endpoint = item['labels'].get('endpoint', 'N/A')
                    value = item['value']
                    print(f"      - {endpoint}: {value:.4f}")
                if len(metric_data) > 3:
                    print(f"      ... and {len(metric_data) - 3} more")
        print()
        
        print("⏱️  Time Series Data:")
        for metric_name, ts_data in report['time_series'].items():
            if isinstance(ts_data, dict) and "error" in ts_data:
                print(f"  ❌ {metric_name}: Error - {ts_data['error']}")
            elif isinstance(ts_data, dict) and "values" in ts_data:
                print(f"  ✓ {metric_name}: {len(ts_data['values'])} data points over 15 minutes")
            elif isinstance(ts_data, list):
                total_points = sum(len(item['values']) for item in ts_data)
                print(f"  ✓ {metric_name}: {total_points} data points across {len(ts_data)} series")
        print()
        
        print("Summary:")
        print(report['investigation_summary'])
    
    print(f"\n{'=' * 60}")
    print(f"Investigation complete! Analyzed {len(alerts)} alert(s)")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
