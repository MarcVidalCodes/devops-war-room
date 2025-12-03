"""
Diagnostic Agent - AI-powered root cause analysis.

This agent uses Large Language Models (Gemini) to analyze alert data
and triage metrics to determine the most likely root cause of incidents.

This is where AI enters the system - everything before this was traditional automation.
"""

import logging
import os
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate


class DiagnosticAgent:
    """
    AI agent that performs root cause analysis on production incidents.

    Takes alert information and triage data from TriageAgent,
    uses an LLM to reason about the problem, and generates:
    - Root cause hypothesis
    - Supporting evidence
    - Recommended next steps

    This is the first "intelligent" agent - it uses LLM reasoning
    rather than just rules or queries.
    """

    def __init__(
        self,
        model: str = "models/gemini-2.5-flash",
        temperature: float = 0.1,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the DiagnosticAgent.

        Args:
            model: Google Gemini model to use (models/gemini-2.5-flash, models/gemini-2.5-pro, etc.)
            temperature: LLM temperature (0.0 = deterministic, 1.0 = creative)
                        Use low temperature for diagnostic work
            api_key: Google API key (if not set, reads from GOOGLE_API_KEY env var)
        """
        self.logger = logging.getLogger(__name__)

        # Initialize LLM (Gemini)
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=api_key or os.getenv("GOOGLE_API_KEY"),
        )

        # Diagnostic prompt template
        self.diagnostic_prompt = PromptTemplate(
            template="""You are an expert DevOps engineer analyzing a production incident.

ALERT INFORMATION:
- Alert Name: {alert_name}
- Severity: {severity}
- Summary: {summary}
- Description: {description}
- Started At: {started_at}

CURRENT METRICS:
{metrics_summary}

YOUR TASK:
Analyze this incident and provide:

1. ROOT CAUSE HYPOTHESIS
   - What is the most likely cause of this alert?
   - Be specific and technical

2. SUPPORTING EVIDENCE
   - What metrics/data support this hypothesis?
   - What patterns do you see?

3. RECOMMENDED ACTIONS
   - What should be done immediately?
   - What should be investigated further?

4. CONFIDENCE LEVEL
   - How confident are you in this diagnosis? (High/Medium/Low)
   - What additional data would increase confidence?

Be concise but thorough. Focus on actionable insights.""",
            input_variables=[
                "alert_name",
                "severity",
                "summary",
                "description",
                "started_at",
                "metrics_summary",
            ],
        )

    def diagnose(
        self, alert_info: Dict[str, Any], triage_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform AI-powered diagnosis of an incident.

        Args:
            alert_info: Basic alert information (name, severity, etc.)
            triage_report: Detailed metrics from TriageAgent

        Returns:
            Dictionary containing:
            - diagnosis: LLM's root cause analysis
            - confidence: Confidence level (high/medium/low)
            - recommendations: List of recommended actions
            - raw_response: Full LLM response text
        """
        try:
            # Format metrics for LLM consumption
            metrics_summary = self._format_metrics(triage_report.get("metrics", {}))

            # Create prompt
            prompt_text = self.diagnostic_prompt.format(
                alert_name=alert_info.get("name", "Unknown"),
                severity=alert_info.get("severity", "Unknown"),
                summary=alert_info.get("summary", "No summary available"),
                description=alert_info.get("description", "No description available"),
                started_at=alert_info.get("started_at", "Unknown"),
                metrics_summary=metrics_summary,
            )

            self.logger.info(f"Diagnosing alert: {alert_info.get('name', 'Unknown')}")

            # Invoke LLM
            response = self.llm.invoke(prompt_text)
            diagnosis_text = response.content

            # Parse response
            parsed = self._parse_diagnosis(diagnosis_text)

            return {
                "alert_name": alert_info.get("name", "Unknown"),
                "diagnosis": parsed.get("root_cause", "Unable to determine"),
                "evidence": parsed.get("evidence", "No evidence provided"),
                "recommendations": parsed.get("recommendations", []),
                "confidence": parsed.get("confidence", "medium"),
                "raw_response": diagnosis_text,
                "model_used": self.llm.model,
            }

        except Exception as e:
            self.logger.error(f"Error during diagnosis: {e}")
            return {
                "alert_name": alert_info.get("name", "Unknown"),
                "error": str(e),
                "diagnosis": "Error occurred during AI analysis",
                "confidence": "none",
            }

    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """
        Format triage metrics into human-readable text for LLM.

        Args:
            metrics: Metrics dictionary from TriageAgent

        Returns:
            Formatted string
        """
        lines = []

        for metric_name, metric_data in metrics.items():
            if isinstance(metric_data, dict):
                if "error" in metric_data:
                    lines.append(f"- {metric_name}: ERROR - {metric_data['error']}")
                elif "value" in metric_data:
                    lines.append(f"- {metric_name}: {metric_data['value']:.4f}")
            elif isinstance(metric_data, list):
                lines.append(f"- {metric_name}:")
                for item in metric_data[:5]:  # Limit to first 5 items
                    if isinstance(item, dict):
                        labels = item.get("labels", {})
                        value = item.get("value", 0)
                        endpoint = labels.get("endpoint", "N/A")
                        lines.append(f"    • {endpoint}: {value:.4f}")
                if len(metric_data) > 5:
                    lines.append(f"    • ... and {len(metric_data) - 5} more")

        return "\n".join(lines) if lines else "No metrics available"

    def _parse_diagnosis(self, diagnosis_text: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured format.

        This is a simple parser - could be enhanced with more sophisticated
        extraction or by using LLM with structured output.

        Args:
            diagnosis_text: Raw LLM response

        Returns:
            Parsed diagnosis dictionary
        """
        result = {
            "root_cause": "",
            "evidence": "",
            "recommendations": [],
            "confidence": "medium",
        }

        lines = diagnosis_text.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()

            # Detect sections
            if "ROOT CAUSE" in line.upper():
                current_section = "root_cause"
                continue
            elif "EVIDENCE" in line.upper() or "SUPPORTING" in line.upper():
                current_section = "evidence"
                continue
            elif "RECOMMEND" in line.upper() or "ACTION" in line.upper():
                current_section = "recommendations"
                continue
            elif "CONFIDENCE" in line.upper():
                current_section = "confidence"
                continue

            # Parse content
            if current_section == "root_cause" and line:
                if line.startswith("-") or line.startswith("•"):
                    result["root_cause"] += line[1:].strip() + " "
                elif result["root_cause"] and not line.startswith("#"):
                    result["root_cause"] += line + " "

            elif current_section == "evidence" and line:
                if line.startswith("-") or line.startswith("•"):
                    result["evidence"] += line[1:].strip() + " "
                elif result["evidence"] and not line.startswith("#"):
                    result["evidence"] += line + " "

            elif current_section == "recommendations" and line:
                if line.startswith("-") or line.startswith("•") or line[0].isdigit():
                    # Remove bullet/number
                    clean_line = line.lstrip("-•0123456789. ").strip()
                    if clean_line:
                        result["recommendations"].append(clean_line)

            elif current_section == "confidence" and line:
                line_lower = line.lower()
                if "high" in line_lower:
                    result["confidence"] = "high"
                elif "low" in line_lower:
                    result["confidence"] = "low"
                elif "medium" in line_lower:
                    result["confidence"] = "medium"

        # Fallback: if parsing failed, use entire text as root cause
        if not result["root_cause"].strip():
            result["root_cause"] = diagnosis_text[:500]  # First 500 chars

        return result

    def diagnose_multiple(
        self, investigations: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Diagnose multiple alerts in batch.

        Args:
            investigations: List of investigation reports from TriageAgent

        Returns:
            List of diagnosis results
        """
        results = []

        for investigation in investigations:
            alert_info = investigation.get("alert_info", {})
            diagnosis = self.diagnose(alert_info, investigation)
            results.append(diagnosis)

        return results
