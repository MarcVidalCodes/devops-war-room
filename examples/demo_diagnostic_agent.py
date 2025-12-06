"""
Demo script for DiagnosticAgent (AI-powered).

This demonstrates the first AI component in the system.
DiagnosticAgent uses Ollama (local LLM) to analyze alerts and provide root cause analysis.

Prerequisites:
1. Install Ollama (https://ollama.com)
2. Pull models: `ollama pull llama3` and `ollama pull nomic-embed-text`
3. Have alerts firing (run continuous_traffic.sh)
"""

import os
import logging
import requests
from src.agents.diagnostic_agent import DiagnosticAgent
from src.agents.triage_agent import TriageAgent
from src.integrations.prometheus_client import PrometheusClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def check_ollama():
    """Check if Ollama is running and models are available."""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = [m['name'] for m in response.json().get('models', [])]
            print(f"✓ Ollama is running (Found models: {', '.join(models)})")
            
            required_models = ['llama3', 'nomic-embed-text']
            missing = [m for m in required_models if not any(m in installed for installed in models)]
            
            if missing:
                print(f"⚠️  Missing models: {', '.join(missing)}")
                print(f"   Run: ollama pull {' '.join(missing)}")
                return False
            return True
    except:
        print("❌ ERROR: Ollama is not running!")
        print("   Please start Ollama app or run 'ollama serve'")
        return False
    return False


def main():
    print("\n" + "=" * 70)
    print("🤖 DiagnosticAgent Demo - AI-Powered Root Cause Analysis")
    print("=" * 70)
    print()
    print("This agent uses Ollama (Local AI) to analyze production incidents.")
    print()
    print("Prerequisites:")
    print("  1. Install Ollama")
    print("  2. Run: ollama pull llama3")
    print("  3. Run: ollama pull nomic-embed-text")
    print()
    print("=" * 70)
    print()
    
    # Check for Ollama
    if not check_ollama():
        return
    
    # Initialize agents
    prometheus_client = PrometheusClient("http://localhost:9090")
    triage_agent = TriageAgent("http://localhost:9090")
    diagnostic_agent = DiagnosticAgent(model="llama3", temperature=0.1)
    
    # Check Prometheus health
    if not prometheus_client.is_healthy():
        logger.error("Prometheus is not healthy!")
        return
    
    logger.info("✓ Prometheus is healthy")
    
    # Get firing alerts
    alerts = prometheus_client.get_firing_alerts()
    
    if not alerts:
        print("\n⚠️  No alerts currently firing.")
        print("Run: bash examples/continuous_traffic.sh")
        print("Wait 30-60 seconds, then run this script again.")
        return
    
    print(f"\n🔍 Found {len(alerts)} firing alert(s)")
    print("\n" + "=" * 70)
    print()
    
    # Limit to first 2 alerts for demo
    alerts_to_analyze = alerts[:2]
    
    # Process each alert
    for i, alert in enumerate(alerts_to_analyze, 1):
        alert_name = alert["labels"]["alertname"]
        severity = alert["labels"].get("severity", "unknown")
        
        print(f"{'=' * 70}")
        print(f"Alert {i}/{len(alerts_to_analyze)}: {alert_name} ({severity})")
        print(f"{'=' * 70}\n")
        
        # Step 1: Triage (gather metrics)
        print("📊 Step 1: Triaging (gathering metrics)...")
        triage_report = triage_agent.investigate_alert(alert)
        print(f"   ✓ Collected {len(triage_report['metrics'])} metrics")
        print()
        
        # Step 2: AI Diagnosis
        print("🤖 Step 2: AI Diagnosis (calling Ollama)...")
        diagnosis = diagnostic_agent.diagnose(
            alert_info=triage_report["alert_info"],
            triage_report=triage_report
        )
        print(f"   ✓ Analysis complete (model: {diagnosis['model_used']})")
        print()
        
        # Display results
        print("=" * 70)
        print("AI DIAGNOSIS RESULTS")
        print("=" * 70)
        print()
        
        print(f"🎯 ROOT CAUSE:")
        print(f"   {diagnosis['diagnosis']}")
        print()
        
        print(f"📈 EVIDENCE:")
        print(f"   {diagnosis['evidence']}")
        print()
        
        print(f"💡 RECOMMENDATIONS:")
        for j, rec in enumerate(diagnosis['recommendations'], 1):
            print(f"   {j}. {rec}")
        if not diagnosis['recommendations']:
            print("   (None provided)")
        print()
        
        print(f"🎚️  CONFIDENCE: {diagnosis['confidence'].upper()}")
        print()
        
        print("=" * 70)
        print()
        
        # Show raw LLM response (optional)
        # show_raw = input("Show full LLM response? (y/n): ").strip().lower()
        show_raw = 'n'
        if show_raw == 'y':
            print()
            print("=" * 70)
            print("FULL LLM RESPONSE")
            print("=" * 70)
            print()
            print(diagnosis['raw_response'])
            print()
            print("=" * 70)
            print()
    
    print()
    print("=" * 70)
    print(f"✅ AI Analysis complete! Analyzed {len(alerts_to_analyze)} alert(s)")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
