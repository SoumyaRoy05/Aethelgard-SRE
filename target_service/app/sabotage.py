# target_service/app/sabotage.py
"""
Chaos Engineering Harness for Aethelgard Target Microservice.
Exposes endpoints to simulate real-world microservice runtime regressions.
"""

import time
from fastapi import APIRouter

try:
    from .config import system_state
except (ImportError, ValueError):
    try:
        from target_service.app.config import system_state
    except ImportError:
        from app.config import system_state

router = APIRouter(tags=["Chaos Engineering"])

@router.get("/status")
def get_service_status():
    """Returns current internal diagnostics and active incident state."""
    return {
        "status": system_state["status"],
        "incident_type": system_state["incident_type"],
        "db_pool_available": system_state["db_pool_available"],
        "memory_leak_chunks": len(system_state["leak_buffer"]),
        "timestamp": time.time()
    }

@router.post("/sabotage/blocking-io")
def sabotage_blocking_io():
    """
    Simulates a synchronous blocking I/O call (e.g. time.sleep or synchronous requests.get)
    inside an async route handler. This starves the single-threaded asyncio event loop.
    """
    system_state["status"] = "DEGRADED"
    system_state["incident_type"] = "BLOCKING_IO"
    system_state["incident_start_epoch"] = time.time()
    return {
        "message": "SYSTEM COMPROMISED: Blocking I/O Incident Triggered",
        "incident_type": "BLOCKING_IO",
        "description": "Synchronous sleep injected into async event loop"
    }

@router.post("/sabotage/cpu-bound")
def sabotage_cpu_bound():
    """
    Simulates an unoptimized, heavy CPU-bound computation blocking the event loop.
    """
    system_state["status"] = "DEGRADED"
    system_state["incident_type"] = "CPU_BOUND"
    system_state["incident_start_epoch"] = time.time()
    return {
        "message": "SYSTEM COMPROMISED: CPU Starvation Incident Triggered",
        "incident_type": "CPU_BOUND",
        "description": "Intense computational spin-loop locking thread"
    }

@router.post("/sabotage/memory-leak")
def sabotage_memory_leak():
    """
    Simulates a rapid memory leak by appending synthetic byte arrays to a global buffer.
    """
    system_state["status"] = "DEGRADED"
    system_state["incident_type"] = "MEMORY_LEAK"
    system_state["incident_start_epoch"] = time.time()
    # Allocate 10MB into memory buffer
    system_state["leak_buffer"].append(b"X" * (10 * 1024 * 1024))
    return {
        "message": "SYSTEM COMPROMISED: Memory Leak Injected",
        "incident_type": "MEMORY_LEAK",
        "buffer_chunks": len(system_state["leak_buffer"])
    }

@router.post("/sabotage/pool-exhaustion")
def sabotage_pool_exhaustion():
    """
    Simulates database connection pool exhaustion.
    """
    system_state["status"] = "DEGRADED"
    system_state["incident_type"] = "POOL_EXHAUSTION"
    system_state["incident_start_epoch"] = time.time()
    system_state["db_pool_available"] = 0
    return {
        "message": "SYSTEM COMPROMISED: DB Connection Pool Exhausted",
        "incident_type": "POOL_EXHAUSTION",
        "db_pool_available": 0
    }

@router.post("/fix")
def fix_system():
    """
    Restores the target microservice back to the healthy operational baseline.
    """
    system_state["status"] = "HEALTHY"
    system_state["incident_type"] = None
    system_state["incident_start_epoch"] = None
    system_state["leak_buffer"].clear()
    system_state["db_pool_available"] = system_state["db_pool_max"]
    return {
        "message": "SYSTEM RESTORED: All operations normalized to baseline",
        "status": "HEALTHY"
    }
