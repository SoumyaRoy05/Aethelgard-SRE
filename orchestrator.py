# orchestrator.py

# Import json to read configuration streams and export audit reports onto developer terminals.
import json
# Import os to manage unified configuration and coordinate relative workspace boundaries.
import os
# Import datetime to format permanent, human-auditable incident timestamps.
from datetime import datetime

# Reference separate internal microprocess engines safely via explicit package subfolder dot mapping.
from librarian.librarian_engine import LocalAIOpsLibrarian
from architect.architect_engine import LocalRemediationArchitect
from executor.executor_engine import SandboxValidationExecutor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INCIDENT_REPORTS_DIR = os.path.join(BASE_DIR, "reports", "incident_reports")
FINAL_MARKDOWN_REPORT = os.path.join(BASE_DIR, "reports", "AETHELGARD_INCIDENT_SUMMARY.md")

def run_remediation_orchestrator():
    print("\n" + "="*80)
    print(f"🛡️  AETHELGARD CLOSED-LOOP AI SRE ORCHESTRATOR IS AWAKE AND LISTENING  🛡️")
    print("="*80)

    if not os.path.exists(INCIDENT_REPORTS_DIR) or not os.listdir(INCIDENT_REPORTS_DIR):
        print(f"[{datetime.now()}] 🟩 Status Normal: No incident payloads found. Loop resting.")
        return

    incident_files = [os.path.join(INCIDENT_REPORTS_DIR, f) for f in os.listdir(INCIDENT_REPORTS_DIR) if f.endswith(".json")]
    if not incident_files:
        return
        
    latest_incident_path = max(incident_files, key=os.path.getmtime)
    with open(latest_incident_path, "r", encoding="utf-8") as f:
        incident_context = json.load(f)

    observed_latency = incident_context["metrics"]["observed_latency_ms"]
    detected_z_score = incident_context["metrics"]["calculated_z_score"]
    server_health_reported = incident_context["infrastructure_context"]["server_reported_health"]
    
    print(f"[{datetime.now()}] 📑 Processing: {latest_incident_path}")

    # Step 1: Query local vector engine
    librarian = LocalAIOpsLibrarian()
    librarian.sync_codebase_index()
    search_query = f"FastAPI async endpoint event loop blocking latency anomaly {server_health_reported} slow check"
    search_results = librarian.search_suspicious_logic(search_query, top_k=1)

    if not search_results or not search_results['documents'] or not search_results['documents'][0]:
        print("❌ Code retrieval matrix execution fault.")
        return
        
    retrieved_code = search_results['documents'][0][0]
    retrieved_metadata = search_results['metadatas'][0][0]

    # Step 2: Query Model Architect 
    architect = LocalRemediationArchitect()
    remediation_plan = architect.generate_remediation_plan(incident_context, retrieved_code)
    print(f"[{datetime.now()}] 📝 Root Cause Isolated: {remediation_plan.get('root_cause')}")

    # Step 3: Container Workspace Sandbox Execution
    executor = SandboxValidationExecutor()
    executor.reset_and_provision_sandbox()
    
    if not executor.apply_targeted_string_patch(remediation_plan):
        print("❌ Patch layout formatting string mismatch. Aborting execution loops.")
        return

    if not executor.deploy_sandbox_container():
        print("❌ Sandbox cluster build error. Patch rejected.")
        return

    # Step 4: Verification telemetry evaluation
    verification_passed, post_fix_telemetry_data = executor.verify_sandbox_telemetry()
    validation_status = "ACCEPTED / VERIFIED SUCCESSFUL" if verification_passed else "REJECTED / UNSTABLE BASELINE"
    post_fix_latency = post_fix_telemetry_data.get("latency_ms", "UNKNOWN") if verification_passed else "N/A"
    post_fix_status = post_fix_telemetry_data.get("status", "OFFLINE") if verification_passed else "CRITICAL_ERROR"

    # Step 5: Format human verification report
    markdown_report_content = (
        f"# 🛡️ AETHELGARD AUTOMATED INCIDENT COMPILATION & AUDIT REPORT\n\n"
        f"**Algorithmic Evaluation Status**: {validation_status}\n\n"
        f"## 1. INITIAL TELEMETRY INCIDENT TRACE\n"
        f"- **Unique Outage ID**: {incident_context.get('incident_id', 'INC_UNKNOWN')}\n"
        f"- **Measured Outage Latency**: `{observed_latency} ms`\n"
        f"- **Statistical Threshold Violation**: `{detected_z_score} σ`\n\n"
        f"## 2. REPO FOOTPRINT DETECTED BY LIBRARIAN\n"
        f"- **Target File Address**: `{retrieved_metadata['file_path']}`\n"
        f"```python\n{retrieved_code}\n```\n\n"
        f"## 3. PROPOSED FIX DIFF STRING BY AI ARCHITECT\n"
        f"```python\n# BEFORE\n{remediation_plan.get('target_string_before')}\n\n# AFTER\n{remediation_plan.get('target_string_after')}\n```\n\n"
        f"## 4. DOCKER SANDBOX VALIDATION MATRIX\n"
        f"- **Sandboxed Microservice Health Status**: `{post_fix_status}`\n"
        f"- **Measured Post-Fix Sandbox Latency**: `{post_fix_latency} ms`\n"
    )

    with open(FINAL_MARKDOWN_REPORT, "w", encoding="utf-8") as f:
        f.write(markdown_report_content)

    executor.terminate_sandbox_container()
    print(f"[{datetime.now()}] 🎉 Report written safely to workspace: '{FINAL_MARKDOWN_REPORT}'\n")

if __name__ == "__main__":
    run_remediation_orchestrator()