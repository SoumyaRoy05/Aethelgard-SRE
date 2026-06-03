# target_service/app/sabotage.py

# Import the APIRouter module from FastAPI to cleanly isolate and modularize our route configuration.
from fastapi import APIRouter
# Import our centralized system state dictionary so we can programmatically inject simulated failures.
from app.config import system_state

# Instantiate the routing controller specifically tasked with managing our simulated architecture exploits.
# By separating this from main.py, we follow enterprise-grade decoupled software design principles.
router = APIRouter()

# Register a POST endpoint to simulate a developer pushing a synchronous blocking I/O error into production.
@router.post("/sabotage/blocking-io")
def sabotage_blocking_io():
    # Update the core system state flag to alert the monitoring loop that performance is compromised.
    system_state["status"] = "DEGRADED"
    # Specify the exact incident signature as BLOCKING_IO so the health check path triggers the specific bug.
    system_state["incident_type"] = "BLOCKING_IO"
    # Return a structured JSON acknowledgement frame back to the testing harness or administrative operator.
    return {"message": "SYSTEM COMPROMISED: Blocking I/O Incident Triggered"}

# Register a POST endpoint to simulate an unoptimized computational loop choking the machine's processor resources.
@router.post("/sabotage/cpu-bound")
def sabotage_cpu_bound():
    # Flag the overall service status state as compromised/degraded in system memory.
    system_state["status"] = "DEGRADED"
    # Configure the active incident parameter to point directly to our mathematical processing stress vector.
    system_state["incident_type"] = "CPU_BOUND"
    # Send an explicit JSON confirmation back to the orchestrator indicating the CPU execution fault is hot.
    return {"message": "SYSTEM COMPROMISED: CPU Starvation Incident Triggered"}

# Register a POST endpoint representing the administrative recovery action designed to clear active alerts.
@router.post("/fix")
def fix_system():
    # Gracefully restore the global operational state condition back to its pristine "HEALTHY" baseline.
    system_state["status"] = "HEALTHY"
    # Wipe the active incident context completely clear so the processing paths return to normal speeds.
    system_state["incident_type"] = None
    # Provide an auditable JSON response payload confirming successful structural health restoration.
    return {"message": "SYSTEM RESTORED: All operations normal"}