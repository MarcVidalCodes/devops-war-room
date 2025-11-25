"""
Demo script for MonitorAgent.

This shows how to run the MonitorAgent and trigger alerts to see it in action.

Usage:
    Terminal 1: python examples/demo_monitor_agent.py
    Terminal 2: bash examples/trigger_alerts.sh
"""

from src.agents.monitor_agent import MonitorAgent


def main():
    print("\n" + "=" * 60)
    print("MonitorAgent Demo")
    print("=" * 60)
    print("\nThis agent will monitor Prometheus for firing alerts.")
    print("To trigger alerts, run in another terminal:")
    print("  bash examples/trigger_alerts.sh")
    print("\nPress Ctrl+C to stop the agent\n")
    print("=" * 60 + "\n")

    # Create and start agent
    agent = MonitorAgent(
        prometheus_url="http://localhost:9090",
        check_interval=10,  # Check every 10 seconds for demo (faster than production 30s)
    )

    agent.start()


if __name__ == "__main__":
    main()
