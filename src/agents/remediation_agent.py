import logging
from typing import Dict, Any
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


class RemediationPlan(BaseModel):
    action_type: str = Field(
        description="Type of action: 'code_change', 'terminal_command', or 'manual_step'"
    )
    description: str = Field(description="Short description of what this fix does")
    content: str = Field(description="The actual code snippet, command, or instruction")
    file_path: str = Field(
        description="Path to the file to modify (if applicable)", default=""
    )
    risk_level: str = Field(description="Risk level: 'low', 'medium', 'high'")


class RemediationAgent:
    def __init__(self, model: str = "llama3", temperature: float = 0.1):
        self.llm = ChatOllama(model=model, temperature=temperature)
        self.logger = logger

        # Define the parser
        self.parser = JsonOutputParser(pydantic_object=RemediationPlan)

        # Define the prompt
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert Site Reliability Engineer and Python Developer.
            Your goal is to fix production incidents based on a diagnosis.

            You must output your response in valid JSON format matching the requested schema.
            Do not include any text outside the JSON object.

            IMPORTANT GUIDELINES:
            1. Return ONLY a SINGLE JSON object (not a list, not wrapped in 'actions').
            2. Choose the SINGLE BEST action to resolve the issue immediately.
            3. Ensure valid JSON syntax: use double quotes for strings, escape newlines with \\n, and DO NOT use triple quotes.

            For 'code_change':
            - Provide the EXACT code snippet to replace or insert.
            - Specify the file path if known (infer from context).

            For 'terminal_command':
            - Provide the exact shell command.

            For 'manual_step':
            - Provide clear instructions.
            """,
                ),
                (
                    "human",
                    """
            Here is the incident context:
            
            ALERT: {alert_name}
            DIAGNOSIS: {diagnosis}
            ROOT CAUSE: {root_cause}
            
            TRIAGE CONTEXT:
            {triage_context}
            
            Generate a remediation plan.
            {format_instructions}
            """,
                ),
            ]
        )

        # self.chain = self.prompt | self.llm | self.parser
        # Split chain to debug raw output
        self.chain = self.prompt | self.llm

    def propose_fix(self, diagnosis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a remediation plan based on the diagnosis.
        """
        self.logger.info(
            f"Generating remediation plan for: {diagnosis_result.get('diagnosis', 'Unknown issue')}"
        )

        try:
            # Extract relevant info
            alert_name = diagnosis_result.get("alert_info", {}).get(
                "alertname", "Unknown"
            )
            diagnosis = diagnosis_result.get("diagnosis", "")
            # Sometimes diagnosis result structure varies, let's be robust
            root_cause = diagnosis_result.get("root_cause", diagnosis)

            # Format triage context for the prompt
            triage_context = str(diagnosis_result.get("triage_report", {}))

            llm_response = self.chain.invoke(
                {
                    "alert_name": alert_name,
                    "diagnosis": diagnosis,
                    "root_cause": root_cause,
                    "triage_context": triage_context,
                    "format_instructions": self.parser.get_format_instructions(),
                }
            )

            self.logger.info(f"Raw LLM response: {llm_response.content}")

            try:
                response = self.parser.parse(llm_response.content)
                self.logger.info(
                    f"Remediation plan generated successfully. Response keys: {response.keys()}"
                )
                self.logger.info(f"Full response: {response}")
                return response
            except Exception as parse_error:
                self.logger.error(f"Failed to parse JSON: {parse_error}")
                # Fallback: try to extract JSON from markdown block
                import re

                json_match = re.search(
                    r"```json\n(.*?)\n```", llm_response.content, re.DOTALL
                )
                if json_match:
                    try:
                        import json

                        response = json.loads(json_match.group(1))
                        return response
                    except Exception:
                        pass
                raise parse_error

        except Exception as e:
            self.logger.error(f"Failed to generate remediation plan: {e}")
            return {
                "action_type": "manual_step",
                "description": "Failed to generate automated fix",
                "content": "Please investigate manually. AI generation failed.",
                "risk_level": "high",
            }
