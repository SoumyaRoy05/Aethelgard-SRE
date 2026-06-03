# architect/architect_engine.py

# Import requests to programmatically interact with the local air-gapped Ollama HTTP inference endpoint port.
import requests
# Import json to decode data payloads and validate structured schema parameters.
import json

# Local web destination address where the background Ollama processing service handles inference.
OLLAMA_API_URL = "http://localhost:11434/api/generate"
# The specific quantized programming instruction model downloaded onto our workstation disk array.
MODEL_NAME = "qwen2.5-coder:7b"

class LocalRemediationArchitect:
    def __init__(self):
        # Establish core server connectivity address coordinates.
        self.url = OLLAMA_API_URL
        # Map our active AI targeting framework designation variable string.
        self.model = MODEL_NAME

    def generate_remediation_plan(self, incident_context_json, context_code_snippet):
        """
        Pipes structured anomaly metrics and retrieved code snippets directly to the local 
        LLM to derive an explainable root cause and output a strict, parseable string patch.
        """
        # Construct a strict structural system prompt ensuring formatting determinism and preventing markdown dialogue.
        system_prompt = (
            "You are a Senior Principal Site Reliability Engineer and Production Software Architect.\n"
            "Analyze the provided live incident context JSON and retrieved source code context.\n"
            "Identify the concurrency bug causing the latency spike and formulate a remediation string fix.\n"
            "CRITICAL: You must return ONLY a structured JSON block following the schema exactly.\n"
            "Do NOT wrap code inside markdown blocks. Do NOT output conversational text explanation outside the schema.\n\n"
            "TARGET JSON OUTPUT FORMAT SCHEMA:\n"
            "{\n"
            '  "root_cause": "Detailed technical explanation of the concurrency thread-locking issue found",\n'
            '  "file_target": "Exact file path requiring code refactoring adjustment",\n'
            '  "target_string_before": "The precise block of code or line to be replaced, matching whitespaces exactly",\n'
            '  "target_string_after": "The precise new code line string to write over that location instead"\n'
            "}"
        )

        # Assemble the input data package string payload injecting the live SRE incident footprint profiles.
        user_prompt = (
            f"=== LIVE METRIC OUTAGE CONTEXT ===\n{json.dumps(incident_context_json, indent=2)}\n\n"
            f"=== SEMANTICALLY MATCHING CODE SOURCED ===\n{context_code_snippet}\n\n"
            f"Execute analysis and output the schema JSON payload directly now."
        )

        # Configure the HTTP request parameters targeting our background intelligence engine.
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "format": "json" # Enforce strict local JSON model response outputs.
        }

        try:
            # Dispatch the execution configuration weights block to our local offline network port link.
            response = requests.post(self.url, json=payload, timeout=60.0)
            # Check for network response state errors before proceeding with string dissection.
            response.raise_for_status()
            # Extract output frame text blocks cleanly from the HTTP frame data matrix.
            result_data = response.json()
            # Convert raw text representations directly back into active Python dictionary nodes.
            structured_plan = json.loads(result_data.get("response", "{}"))
            return structured_plan
        except Exception as e:
            # Fallback error recovery handling payload map returned if inference fails or times out.
            return {
                "root_cause": f"Inference pipeline execution error encountered: {str(e)}",
                "file_target": None,
                "target_string_before": None,
                "target_string_after": None
            }