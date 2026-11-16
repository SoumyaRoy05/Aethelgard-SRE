# target_service/app/config.py
"""
Aethelgard Target Microservice - Runtime State Configuration
Tracks runtime system performance state, active chaos experiments, and mock dependencies.
"""

system_state = {
    # System health baseline: "HEALTHY" or "DEGRADED"
    "status": "HEALTHY",
    
    # Active chaos incident signature: None, "BLOCKING_IO", "CPU_BOUND", "MEMORY_LEAK", "POOL_EXHAUSTION"
    "incident_type": None,
    
    # Track when the current incident was injected
    "incident_start_epoch": None,
    
    # In-memory memory leak buffer for simulation
    "leak_buffer": [],
    
    # Mock database connection pool state
    "db_pool_available": 10,
    "db_pool_max": 10
}
