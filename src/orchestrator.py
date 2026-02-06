"""
Orchestrator - Coordinates all agents in the incident response pipeline.

Runs continuously, monitoring for alerts and processing them through
the full agent pipeline: Prometheus -> Triage -> Diagnostic -> Remediation.
"""

import time
import logging
from typing import Dict, Any, Set, List
from src.integrations.prometheus_client import PrometheusClient
from src.agents.triage_agent import TriageAgent
from src.agents.diagnostic_agent import DiagnosticAgent
from src.agents.remediation_agent import RemediationAgent

logger = logging.getLogger(__name__)


class WarRoomOrchestrator:
    """
    Main orchestrator that coordinates all agents.
    
    Runs a continuous loop that:
    1. Polls Prometheus for firing alerts
    2. Triages each new alert to gather metrics
    3. Diagnoses the root cause using AI
    4. Proposes remediation steps
    """

    def __init__(
        self,
        prometheus_url: str = "http://prometheus:9090",
        check_interval: int = 30
    ):
        """
        Initialize the orchestrator with all agents.
        
        Args:
            prometheus_url: URL for Prometheus API
            check_interval: Seconds to wait between alert checks
        """
        self.check_interval = check_interval
        self.processed_alerts: Set[str] = set()
        
        # Initialize Prometheus client and agents
        logger.info("Initializing agents...")
        self.prom_client = PrometheusClient(prometheus_url)
        self.triage = TriageAgent(prometheus_url=prometheus_url)
        self.diagnostic = DiagnosticAgent(model="llama3", temperature=0.1)
        self.remediation = RemediationAgent(model="llama3", temperature=0.1)
        
        logger.info("War Room Orchestrator initialized")

    def run(self):
        """
        Main execution loop.
        
        Continuously monitors for alerts and processes them through
        the full pipeline. Handles deduplication to avoid processing
        the same alert multiple times.
        """
        logger.info("Starting War Room Orchestrator")
        logger.info(f"Check interval: {self.check_interval}s")
        
        while True:
            try:
                alerts = self._get_firing_alerts()
                
                if alerts:
                    logger.info(f"Found {len(alerts)} active alert(s)")
                    
                    for alert in alerts:
                        alert_id = self._get_alert_id(alert)
                        
                        # Skip if already processed
                        if alert_id in self.processed_alerts:
                            continue
                        
                        # Mark as processed
                        self.processed_alerts.add(alert_id)
                        
                        # Process through pipeline
                        self._handle_alert(alert)
                else:
                    logger.info("No active alerts")
                
                # Clean up old processed alerts periodically
                if len(self.processed_alerts) > 100:
                    self.processed_alerts.clear()
                    logger.info("Cleared processed alerts cache")
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Shutting down War Room Orchestrator")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(30)

    def _get_firing_alerts(self) -> List[Dict[str, Any]]:
        """
        Query Prometheus directly for firing alerts.
        
        Returns:
            List of firing alerts with their metadata
        """
        try:
            response = self.prom_client.query('ALERTS{alertstate="firing"}')
            
            if response.get('status') != 'success':
                logger.error(f"Failed to query alerts: {response}")
                return []
            
            result = response.get('data', {}).get('result', [])
            
            alerts = []
            for item in result:
                metric = item.get('metric', {})
                alert_name = metric.get('alertname', 'Unknown')
                
                # Build alert dict in Prometheus alert format
                alert = {
                    'labels': metric,
                    'annotations': metric,  # Simplified - in real Prometheus alerts come with annotations
                    'startsAt': None,  # Would be in Prometheus alertmanager
                    'fingerprint': metric.get('alertname', '') + str(hash(str(metric)))
                }
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error querying Prometheus for alerts: {e}")
            return []

    def _get_alert_id(self, alert: Dict[str, Any]) -> str:
        """
        Generate a unique identifier for an alert.
        
        Uses fingerprint if available, otherwise constructs from alert name.
        """
        if "fingerprint" in alert:
            return alert["fingerprint"]
        
        alert_name = alert.get("labels", {}).get("alertname", "unknown")
        return alert_name

    def _handle_alert(self, alert: Dict[str, Any]):
        """
        Process a single alert through the full pipeline.
        
        Args:
            alert: Alert dictionary from Prometheus
        """
        alert_name = alert.get("labels", {}).get("alertname", "Unknown")
        logger.info(f"Processing alert: {alert_name}")
        
        try:
            # Stage 1: Triage
            logger.info("Running triage investigation...")
            triage_report = self.triage.investigate_alert(alert)
            
            if triage_report:
                logger.info(f"Triage complete. Summary: {triage_report.get('summary', 'N/A')}")
            else:
                logger.warning("Triage returned no data")
                return
            
            # Stage 2: Diagnosis
            logger.info("Running AI diagnosis...")
            
            # Format alert info for diagnostic agent
            alert_info = {
                "name": alert_name,
                "severity": alert.get("labels", {}).get("severity", "unknown"),
                "summary": alert.get("annotations", {}).get("summary", ""),
                "description": alert.get("annotations", {}).get("description", ""),
                "started_at": alert.get("startsAt", "unknown")
            }
            
            diagnosis = self.diagnostic.diagnose(alert_info, triage_report)
            
            if diagnosis:
                root_cause = diagnosis.get("diagnosis", "Unknown")
                confidence = diagnosis.get("confidence", "medium")
                logger.info(f"Diagnosis: {root_cause}")
                logger.info(f"Confidence: {confidence}")
                
                # Check if human review required
                if diagnosis.get("requires_human_review"):
                    logger.warning("Low confidence with no historical data - escalating to human review")
                    logger.info(f"Recommendations: {diagnosis.get('recommendations', [])}")
                    logger.info(f"Completed processing alert: {alert_name} (escalated)")
                    logger.info("-" * 60)
                    return
            else:
                logger.warning("Diagnosis returned no data")
                return
            
            # Stage 3: Remediation
            logger.info("Generating remediation plan...")
            
            # Format diagnosis for remediation agent
            diagnosis_for_remediation = {
                "alert_info": {"alertname": alert_name},
                "diagnosis": diagnosis.get("diagnosis", "Unknown"),
                "root_cause": diagnosis.get("diagnosis", "Unknown"),
                "triage_report": triage_report
            }
            
            remediation = self.remediation.propose_fix(diagnosis_for_remediation)
            
            if remediation:
                action = remediation.get("action_type", "N/A")
                risk = remediation.get("risk_level", "N/A")
                logger.info(f"Remediation action: {action}")
                logger.info(f"Risk level: {risk}")
                
                # Stage 4: Execution decision
                self._decide_execution(remediation)
            else:
                logger.warning("Remediation returned no data")
            
            logger.info(f"Completed processing alert: {alert_name}")
            logger.info("-" * 60)
            
        except Exception as e:
            logger.error(f"Error processing alert {alert_name}: {e}", exc_info=True)

    def _decide_execution(self, remediation: Dict[str, Any]):
        """
        Decide whether to execute remediation automatically or require approval.
        
        Currently just logs the decision. In production, this would:
        - Auto-execute low-risk fixes
        - Send high-risk fixes to approval queue
        - Integrate with PagerDuty/Slack for human review
        
        Args:
            remediation: Remediation plan from RemediationAgent
        """
        risk_level = remediation.get("risk_level", "high")
        
        if risk_level == "low":
            logger.info("Low risk remediation - could auto-execute")
            # In production: self.executor.execute(remediation)
        elif risk_level == "medium":
            logger.warning("Medium risk - recommend manual review before execution")
            # In production: self.approval_queue.add(remediation)
        else:
            logger.warning("High risk - requires human approval")
            # In production: self.pagerduty.alert(remediation)


def main():
    """Entry point for the orchestrator."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    orchestrator = WarRoomOrchestrator(
        prometheus_url="http://prometheus:9090",
        check_interval=30
    )
    
    orchestrator.run()


if __name__ == "__main__":
    main()
