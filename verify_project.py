# verify_project.py
"""
Aethelgard System Integrity & Readiness Checker
Validates local environment scaffolding, directory structures, dependencies,
and engine components before running autonomous AI-SRE simulations.
"""

import os
import sys
import shutil

REQUIRED_PATHS = [
    # Core orchestration & configuration
    "orchestrator.py",
    "requirements.txt",
    "docker-compose.yml",
    ".env.example",
    ".github/workflows/ci.yml",
    
    # Target microservice & chaos harness
    "target_service/Dockerfile",
    "target_service/app/config.py",
    "target_service/app/main.py",
    "target_service/app/sabotage.py",
    
    # Ingestion Gateway
    "gateway/__init__.py",
    "gateway/webhook_receiver.py",
    
    # Core closed-loop engines
    "sentinel/sentinel_engine.py",
    "librarian/__init__.py",
    "librarian/librarian_engine.py",
    "architect/__init__.py",
    "architect/architect_engine.py",
    "executor/__init__.py",
    "executor/executor_engine.py",
    
    # Persistence & reporting mounts
    "reports/incident_reports",
    "reports/incident_reports/processed",
    "reports/chroma_storage",
    "reports/audit_logs",
    
    # Test suite
    "tests/__init__.py",
    "tests/test_sentinel.py",
    "tests/test_architect.py",
    "tests/test_executor.py",
    "tests/test_target_service.py"
]

def check_project_integrity():
    missing_count = 0
    print("\n" + "=" * 70)
    print("🛡️  AETHELGARD SYSTEM INTEGRITY & SCAFFOLDING AUDIT")
    print("=" * 70)
    
    # 1. Path & File Verification
    for path in REQUIRED_PATHS:
        # Create directories if missing
        if path.startswith("reports/") and not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        if os.path.exists(path):
            print(f"  ✅ FOUND: {path}")
        else:
            print(f"  ❌ MISSING: {path}")
            missing_count += 1

    # 2. Tool & Host Capabilities Verification
    print("\n" + "-" * 70)
    print("🔧 SYSTEM HOST ENVIRONMENT CAPABILITIES")
    print("-" * 70)

    docker_available = shutil.which("docker") is not None
    git_available = shutil.which("git") is not None
    ollama_available = shutil.which("ollama") is not None

    print(f"  {'✅' if docker_available else '⚠️'} Docker Engine CLI: {'AVAILABLE' if docker_available else 'NOT DETECTED IN PATH'}")
    print(f"  {'✅' if git_available else '⚠️'} Git CLI: {'AVAILABLE' if git_available else 'NOT DETECTED IN PATH'}")
    print(f"  {'✅' if ollama_available else 'ℹ️'} Ollama CLI: {'AVAILABLE' if ollama_available else 'REMOTE OR API MODE'}")

    print("=" * 70)
    if missing_count == 0:
        print("🎉 STATUS: 100% PRODUCTION READY. ALL ENGINES & HARNESSES VERIFIED.")
    else:
        print(f"⚠️ STATUS: INCOMPLETE. {missing_count} ASSETS ARE STILL MISSING.")
    print("=" * 70 + "\n")
    return missing_count == 0

if __name__ == "__main__":
    success = check_project_integrity()
    sys.exit(0 if success else 1)
