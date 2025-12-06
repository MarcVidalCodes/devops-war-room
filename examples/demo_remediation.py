"""
Demo script for RemediationAgent (Phase 4).

This demonstrates the full AI pipeline:
1. Detect Alert (Prometheus)
2. Triage (TriageAgent)
3. Diagnose (DiagnosticAgent + RAG)
4. Remediate (RemediationAgent) -> Human Approval

Prerequisites:
1. Ollama running (llama3, nomic-embed-text)
2. Alerts firing (run timed_traffic.sh)
"""

import logging
import sys
import time
from src.agents.diagnostic_agent import DiagnosticAgent
from src.agents.triage_agent import TriageAgent
from src.agents.remediation_agent import RemediationAgent
from src.integrations.prometheus_client import PrometheusClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    print("\n" + "=" * 70)
    print("🛡️  RemediationAgent Demo - Automated Fix Proposal")
    print("=" * 70)
    
    # Initialize agents
    try:
        prometheus_client = PrometheusClient("http://localhost:9090")
        triage_agent = TriageAgent("http://localhost:9090")
        diagnostic_agent = DiagnosticAgent(model="llama3")
        remediation_agent = RemediationAgent(model="llama3")
    except Exception as e:
        logger.error(f"Failed to initialize agents: {e}")
        return

    # Check for firing alerts
    alerts = prometheus_client.get_firing_alerts()
    if not alerts:
        print("\n⚠️  No alerts currently firing.")
        print("Run: bash examples/timed_traffic.sh")
        return

    print(f"\n🔍 Found {len(alerts)} firing alert(s). Analyzing the first one...\n")
    alert = alerts[0]
    alert_name = alert["labels"]["alertname"]
    
    print(f"🚨 ALERT: {alert_name}")
    print("-" * 70)

    # 1. Triage
    print("\n📊 Step 1: Triaging...")
    triage_report = triage_agent.investigate_alert(alert)
    print("   ✓ Metrics collected")

    # 2. Diagnose
    print("\n🤖 Step 2: Diagnosing (with RAG)...")
    diagnosis = diagnostic_agent.diagnose(
        alert_info=triage_report["alert_info"],
        triage_report=triage_report
    )
    print(f"   ✓ Root Cause: {diagnosis['diagnosis'][:100]}...")

    # 3. Remediate
    print("\n🛠️  Step 3: Generating Remediation Plan...")
    # Pass the full diagnosis object to the remediation agent
    # We ensure the diagnosis object has what the agent needs
    diagnosis_context = {
        "alert_info": triage_report["alert_info"],
        "triage_report": triage_report,
        "diagnosis": diagnosis["diagnosis"],
        "root_cause": diagnosis["diagnosis"] # Using diagnosis as root cause for now
    }
    
    plan = remediation_agent.propose_fix(diagnosis_context)
    
    print("\n" + "=" * 70)
    print("PROPOSED REMEDIATION PLAN")
    print("=" * 70)
    print(f"📝 Action: {plan.get('action_type', 'unknown').upper()}")
    print(f"⚠️  Risk:   {plan.get('risk_level', 'unknown').upper()}")
    print(f"📄 File:   {plan.get('file_path', 'N/A')}")
    print("-" * 70)
    print("DESCRIPTION:")
    print(plan.get('description'))
    print("-" * 70)
    print("CONTENT:")
    print(plan.get('content'))
    print("=" * 70)
    
    # Human-in-the-loop
    print("\n👤 Human Approval Required")
    choice = input("Do you want to apply this fix? (y/n): ").strip().lower()
    
    if choice == 'y':
        print("\n🚀 Applying fix... (Simulation)")
        print("   ✓ Fix applied successfully!")
        print("   ✓ Ticket updated.")
    else:
        print("\n❌ Fix rejected by user.")

if __name__ == "__main__":
    main()
