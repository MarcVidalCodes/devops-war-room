"""
Full system demonstration of the Agentic DevOps War Room.

This script demonstrates the complete incident response pipeline:
1. System health checks
2. Traffic generation to trigger alerts
3. AI agent pipeline (Triage, Diagnosis, Remediation)
4. Human-in-the-loop approval and knowledge base learning

Usage:
    python examples/full_demo.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from examples.utils.preflight import run_preflight_checks
from examples.utils.traffic_gen import generate_traffic_until_alert
from examples.utils.ui import print_header, print_section, print_success, print_error
from src.agents.triage_agent import TriageAgent
from src.agents.diagnostic_agent import DiagnosticAgent
from src.agents.remediation_agent import RemediationAgent
from src.agents.knowledge_base import IncidentKnowledgeBase
from src.integrations.prometheus_client import PrometheusClient


def main():
    print_header("Agentic DevOps War Room - Full System Demo")
    
    print_section("Phase 1: System Health Check")
    if not run_preflight_checks():
        print_error("Prerequisites not met. Exiting.")
        print("\nPlease ensure:")
        print("  - Docker containers are running (docker-compose up)")
        print("  - Ollama is running (ollama serve)")
        print("  - Required models are installed (ollama pull llama3 && ollama pull nomic-embed-text)")
        sys.exit(1)
    print_success("All systems ready")
    
    print_section("Phase 2: Traffic Generation")
    alert = generate_traffic_until_alert(
        app_url="http://localhost:5001",
        prometheus_url="http://localhost:9090",
        duration_sec=60
    )
    
    if not alert:
        print_error("No alerts fired within timeout period.")
        print("\nTry:")
        print("  - Running for longer duration")
        print("  - Checking alert rules in monitoring/alerts.yml")
        print("  - Verifying application is generating errors")
        sys.exit(1)
    
    alert_name = alert['labels']['alertname']
    print_success(f"Alert detected: {alert_name}")
    
    print_section("Phase 3: AI Agent Pipeline")
    
    try:
        prom_client = PrometheusClient("http://localhost:9090")
        triage_agent = TriageAgent("http://localhost:9090")
        diagnostic_agent = DiagnosticAgent(model="llama3")
        remediation_agent = RemediationAgent(model="llama3")
        kb = IncidentKnowledgeBase()
    except Exception as e:
        print_error(f"Failed to initialize agents: {e}")
        sys.exit(1)
    
    print("\nStep 1: Triage")
    print("  Running diagnostic queries...")
    triage_report = triage_agent.investigate_alert(alert)
    print_success("Metrics collected")
    
    print("\nStep 2: Diagnosis")
    print("  Querying knowledge base...")
    print("  Analyzing with AI model...")
    diagnosis = diagnostic_agent.diagnose(
        alert_info=triage_report["alert_info"],
        triage_report=triage_report
    )
    print_success(f"Diagnosis complete (confidence: {diagnosis['confidence']})")
    print(f"  Root cause: {diagnosis['diagnosis'][:80]}...")
    
    print("\nStep 3: Remediation")
    print("  Generating remediation plan...")
    diagnosis_context = {
        "alert_info": triage_report["alert_info"],
        "triage_report": triage_report,
        "diagnosis": diagnosis["diagnosis"],
        "root_cause": diagnosis["diagnosis"]
    }
    plan = remediation_agent.propose_fix(diagnosis_context)
    print_success("Remediation plan generated")
    
    print("\n" + "=" * 70)
    print("REMEDIATION PLAN")
    print("=" * 70)
    print(f"Action Type: {plan['action_type'].upper()}")
    print(f"Risk Level:  {plan['risk_level'].upper()}")
    print(f"Description: {plan['description']}")
    if plan.get('file_path'):
        print(f"Target File: {plan['file_path']}")
    print("=" * 70)
    
    print_section("Phase 4: Human Approval & Knowledge Base Learning")
    
    if diagnosis["confidence"] == "high":
        choice = input("\nApply this fix? (y/n): ").strip().lower()
        
        if choice == 'y':
            print("  Applying fix (simulation)...")
            print_success("Fix applied successfully")
            
            kb.add_incident(
                alert_name=triage_report["alert_info"]["name"],
                diagnosis=diagnosis["diagnosis"],
                root_cause=diagnosis["diagnosis"],
                fix=plan["description"]
            )
            print_success("Incident saved to knowledge base")
        else:
            print("  Fix not applied")
    
    else:
        print(f"\nConfidence level: {diagnosis['confidence']}")
        print("Manual investigation recommended.")
        input("\nPress Enter after investigating and resolving the issue...")
        
        resolved = input("Did you resolve the issue? (y/n): ").strip().lower()
        
        if resolved == 'y':
            print("\nPlease provide details for the knowledge base:")
            root_cause = input("  Actual root cause: ")
            fix_applied = input("  Fix that was applied: ")
            
            if root_cause and fix_applied:
                kb.add_incident(
                    alert_name=triage_report["alert_info"]["name"],
                    diagnosis=root_cause,
                    root_cause=root_cause,
                    fix=fix_applied
                )
                print_success("Incident saved to knowledge base")
                print("\nThe system will use this information for similar future incidents.")
            else:
                print("  Skipped (no details provided)")
    
    print_section("Demo Complete")
    
    try:
        kb_size = len(kb.table.search().to_list())
        print(f"Knowledge base now contains {kb_size} incident(s)")
        print("\nRun this demo again to see how the system learns from past incidents.")
    except:
        pass


if __name__ == "__main__":
    main()
