# orchestrator.py
"""
Aethelgard Autonomous Closed-Loop AI-SRE Orchestrator
Master execution pipeline coordinating Detect -> Sift -> Reason -> Validate -> Audit.
Supports both single-shot remediation and continuous background daemon monitoring.
"""

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
from datetime import datetime

# Import modular microprocess engines
from librarian.librarian_engine import LocalAIOpsLibrarian
from architect.architect_engine import LocalRemediationArchitect
from executor.executor_engine import SandboxValidationExecutor

# Load optional .env variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INCIDENT_REPORTS_DIR = os.path.join(BASE_DIR, "reports", "incident_reports")
PROCESSED_REPORTS_DIR = os.path.join(INCIDENT_REPORTS_DIR, "processed")
FINAL_MARKDOWN_REPORT = os.path.join(BASE_DIR, "reports", "AETHELGARD_INCIDENT_SUMMARY.md")
ENABLE_GIT_BRANCHING = os.getenv("ENABLE_GIT_BRANCHING", "true").lower() == "true"

def ensure_directories():
    os.makedirs(INCIDENT_REPORTS_DIR, exist_ok=True)
    os.makedirs(PROCESSED_REPORTS_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "reports", "audit_logs"), exist_ok=True)

def handle_git_branching(incident_id: str, plan: dict, sandbox_dir: str):
    """
    Creates an isolated Git branch and writes the patch file for review.
    Ensures safe operations without disrupting active working branches.
    """
    if not ENABLE_GIT_BRANCHING:
        return None

    branch_name = f"aethelgard/remediation-{incident_id.lower()}"
    patch_dir = os.path.join(BASE_DIR, "reports", "audit_logs")
    patch_file = os.path.join(patch_dir, f"{incident_id}_patch.diff")

    try:
        # Generate patch diff content
        diff_content = (
            f"# Remediation Diff for Incident {incident_id}\n"
            f"# File: {plan.get('file_target')}\n"
            f"--- a/{plan.get('file_target')}\n"
            f"+++ b/{plan.get('file_target')}\n"
            f"@@ -before +after @@\n"
            f"-{plan.get('target_string_before')}\n"
            f"+{plan.get('target_string_after')}\n"
        )
        with open(patch_file, "w", encoding="utf-8") as f:
            f.write(diff_content)

        return {
            "branch_name": branch_name,
            "patch_file": patch_file,
            "git_command": f"git checkout -b {branch_name} && git apply {patch_file}"
        }
    except Exception as e:
        print(f"⚠️ Git branch helper warning: {e}")
        return None

def process_incident(incident_file_path: str) -> bool:
    """
    Processes a single incident payload through the complete closed-loop AI-SRE pipeline:
    1. Ingestion & metric extraction
    2. Librarian code retrieval (AST + ChromaDB)
    3. Architect root cause & patch synthesis (Ollama)
    4. Sandbox executor container build & health verification
    5. Markdown & JSON audit trail generation
    """
    print("\n" + "=" * 80)
    print(f"🛡️  AETHELGARD REMEDIATION RUNNING: {os.path.basename(incident_file_path)}")
    print("=" * 80)

    try:
        with open(incident_file_path, "r", encoding="utf-8") as f:
            incident_context = json.load(f)
    except Exception as e:
        print(f"❌ Failed to parse incident JSON: {e}")
        return False

    incident_id = incident_context.get("incident_id", f"INC_{int(time.time())}")
    metrics = incident_context.get("metrics", {})
    observed_latency = metrics.get("observed_latency_ms", "N/A")
    detected_z_score = metrics.get("calculated_z_score", "N/A")
    server_status = incident_context.get("infrastructure_context", {}).get("server_reported_health", "UNKNOWN")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📊 Outage Latency: {observed_latency} ms | Z-Score: {detected_z_score}σ")

    # Step 1: Semantic Slicing via Librarian
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📚 Librarian syncing AST index and querying ChromaDB...")
    librarian = LocalAIOpsLibrarian()
    librarian.sync_codebase_index()
    
    search_query = f"FastAPI async endpoint event loop blocking latency anomaly {server_status} slow check time.sleep"
    search_results = librarian.search_suspicious_logic(search_query, top_k=1)

    if not search_results or not search_results.get('documents') or not search_results['documents'][0]:
        print("❌ Code retrieval failed: No matching code blocks located in ChromaDB index.")
        return False

    retrieved_code = search_results['documents'][0][0]
    retrieved_metadata = search_results['metadatas'][0][0]
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🎯 Suspicious code isolated in: {retrieved_metadata['file_path']} (lines {retrieved_metadata.get('start_line')}-{retrieved_metadata.get('end_line')})")

    # Step 2: Root Cause Analysis & Patch Synthesis via Architect
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🧠 Architect analyzing incident context via local model...")
    architect = LocalRemediationArchitect()
    remediation_plan = architect.generate_remediation_plan(incident_context, retrieved_code)
    root_cause = remediation_plan.get("root_cause", "Unspecified concurrency degradation")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📝 Diagnosis: {root_cause}")

    # Step 3: Sandboxed Container Validation via Executor
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🧪 Provisioning isolated Docker sandbox...")
    executor = SandboxValidationExecutor()
    executor.reset_and_provision_sandbox()

    patch_applied = executor.apply_targeted_string_patch(remediation_plan)
    if not patch_applied:
        print("❌ Patch application failed. Replacement target could not be reconciled in sandbox.")
        executor.terminate_sandbox_container()
        return False

    container_deployed = executor.deploy_sandbox_container()
    if not container_deployed:
        print("❌ Sandbox container build or deployment failed. Candidate patch rejected.")
        executor.terminate_sandbox_container()
        return False

    # Step 4: Verification Telemetry
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔬 Evaluating post-fix sandbox telemetry...")
    verification_passed, post_fix_telemetry = executor.verify_sandbox_telemetry()
    validation_status = "ACCEPTED / VERIFIED SUCCESSFUL" if verification_passed else "REJECTED / UNSTABLE BASELINE"
    post_fix_latency = post_fix_telemetry.get("measured_latency_ms", "UNKNOWN") if verification_passed else "N/A"
    post_fix_status = post_fix_telemetry.get("status", "OFFLINE") if verification_passed else "FAILED"

    # Step 5: Git Branching Metadata
    git_info = handle_git_branching(incident_id, remediation_plan, executor.sandbox_dir)

    # Step 6: Generate Human-Auditable Reports
    markdown_report = (
        f"# 🛡️ AETHELGARD AUTOMATED INCIDENT COMPILATION & AUDIT REPORT\n\n"
        f"**Incident ID**: `{incident_id}`  \n"
        f"**Generated**: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}`  \n"
        f"**Evaluation Status**: **{validation_status}**\n\n"
        f"---\n\n"
        f"## 1. TELEMETRY INCIDENT FOOTPRINT\n"
        f"- **Monitored Endpoint**: `{incident_context.get('target_endpoint', 'N/A')}`\n"
        f"- **Measured Outage Latency**: `{observed_latency} ms`\n"
        f"- **Statistical Threshold Violation**: `{detected_z_score} σ`\n"
        f"- **Infrastructure Context**: `{server_status}`\n\n"
        f"## 2. SUSPICIOUS REPOSITORY FOOTPRINT (LIBRARIAN)\n"
        f"- **Target File**: `{retrieved_metadata.get('file_path')}`\n"
        f"- **Function**: `{retrieved_metadata.get('entity_name')}` (Lines `{retrieved_metadata.get('start_line')}-{retrieved_metadata.get('end_line')}`)\n\n"
        f"```python\n{retrieved_code}\n```\n\n"
        f"## 3. ROOT CAUSE & AI REMEDIATION DIFF (ARCHITECT)\n"
        f"**Root Cause Diagnosis**: {root_cause}\n\n"
        f"```python\n# [ORIGINAL CODE]\n{remediation_plan.get('target_string_before')}\n\n# [AI-PROPOSED NON-BLOCKING FIX]\n{remediation_plan.get('target_string_after')}\n```\n\n"
        f"## 4. DOCKER SANDBOX VALIDATION MATRIX (EXECUTOR)\n"
        f"- **Sandbox Verification Result**: `{validation_status}`\n"
        f"- **Sandbox Microservice Status**: `{post_fix_status}`\n"
        f"- **Measured Post-Fix Latency**: `{post_fix_latency} ms`\n"
        f"- **Assigned Isolated Port**: `{executor.active_port}`\n\n"
    )

    if git_info:
        markdown_report += (
            f"## 5. VERSION CONTROL & DEPLOYMENT READY\n"
            f"- **Branch Prepared**: `{git_info['branch_name']}`\n"
            f"- **Patch File**: `{git_info['patch_file']}`\n"
            f"- **One-Click Local Apply Command**:\n"
            f"  ```bash\n  {git_info['git_command']}\n  ```\n"
        )

    with open(FINAL_MARKDOWN_REPORT, "w", encoding="utf-8") as f:
        f.write(markdown_report)

    # Save structured audit JSON
    audit_json_path = os.path.join(BASE_DIR, "reports", "audit_logs", f"audit_{incident_id}.json")
    audit_data = {
        "incident_id": incident_id,
        "validation_status": validation_status,
        "verification_passed": verification_passed,
        "observed_latency_ms": observed_latency,
        "post_fix_latency_ms": post_fix_latency,
        "file_target": retrieved_metadata.get("file_path"),
        "root_cause": root_cause,
        "diff": {
            "before": remediation_plan.get("target_string_before"),
            "after": remediation_plan.get("target_string_after")
        },
        "timestamp": datetime.now().isoformat()
    }
    with open(audit_json_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=4)

    # Clean up sandbox container
    executor.terminate_sandbox_container()

    # Move processed incident to avoid duplicate runs
    shutil.move(incident_file_path, os.path.join(PROCESSED_REPORTS_DIR, os.path.basename(incident_file_path)))

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🎉 Remediation Complete!")
    print(f"📄 Audit Report: {FINAL_MARKDOWN_REPORT}")
    print(f"💾 Structured Log: {audit_json_path}\n")
    return True

def run_orchestrator_loop(daemon_mode: bool = False, poll_interval: int = 5):
    """Master orchestrator routine supporting batch or continuous daemon execution."""
    ensure_directories()

    print("\n" + "=" * 80)
    print("🛡️  AETHELGARD CLOSED-LOOP AI-SRE ORCHESTRATOR")
    print(f"Mode: {'CONTINUOUS DAEMON' if daemon_mode else 'SINGLE BATCH RUN'}")
    print("=" * 80)

    while True:
        # Search for pending unprocessed incident payloads
        incident_files = [
            os.path.join(INCIDENT_REPORTS_DIR, f)
            for f in os.listdir(INCIDENT_REPORTS_DIR)
            if f.endswith(".json") and os.path.isfile(os.path.join(INCIDENT_REPORTS_DIR, f))
        ]

        if incident_files:
            # Process oldest incident first (FIFO)
            incident_files.sort(key=os.path.getmtime)
            latest_incident = incident_files[0]
            process_incident(latest_incident)
        else:
            if not daemon_mode:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟩 Status Normal: No pending incidents in queue. Loop resting.")
                break
            else:
                # Sleep briefly in daemon mode
                time.sleep(poll_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aethelgard AI-SRE Master Orchestrator")
    parser.add_argument("--daemon", action="store_true", help="Run continuously as a background daemon")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds for daemon mode")
    args = parser.parse_args()

    daemon_setting = args.daemon or os.getenv("ORCHESTRATOR_DAEMON_MODE", "false").lower() == "true"
    run_orchestrator_loop(daemon_mode=daemon_setting, poll_interval=args.interval)
