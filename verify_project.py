import os
import sys

REQUIRED_PATHS = [
    "orchestrator.py",
    "requirements.txt",
    "target_service/Dockerfile",
    "target_service/app/config.py",
    "target_service/app/main.py",
    "target_service/app/sabotage.py",
    "sentinel/sentinel_engine.py",
    "librarian/__init__.py",
    "librarian/librarian_engine.py",
    "architect/__init__.py",
    "architect/architect_engine.py",
    "executor/__init__.py",
    "executor/executor_engine.py",
    "reports/incident_reports",
    "reports/chroma_storage"
]

def check_project_integrity():
    missing_count = 0
    print("=" * 60)
    print("🛡️ AETHELGARD SYSTEM INTEGRITY CHECK")
    print("=" * 60)
    
    for path in REQUIRED_PATHS:
        if os.path.exists(path):
            print(f"✅ FOUND: {path}")
        else:
            print(f"❌ MISSING: {path}")
            missing_count += 1
            
    print("=" * 60)
    if missing_count == 0:
        print("🎉 STATUS: 100% COMPLETE. READY FOR LIVE CHAOS DRILL SIMULATION.")
    else:
        print(f"⚠️ STATUS: INCOMPLETE. {missing_count} FILES OR FOLDERS ARE STILL MISSING.")
    print("=" * 60)

if __name__ == "__main__":
    check_project_integrity()