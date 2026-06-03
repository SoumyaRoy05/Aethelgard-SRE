# target_service/app/config.py

# A global dictionary configuration instance acting as an in-memory operational database.
system_state = {
    # Tracks the overall health status of the microservice. Can be "HEALTHY" or "DEGRADED".
    "status": "HEALTHY",
    
    # A multiplier tracking the severity of system degradation. Used to adjust processing delays.
    "degradation_factor": 0.0,
    
    # Stores the specific identifier of the active SRE incident scenario: "BLOCKING_IO" or "CPU_BOUND".
    "incident_type": None
}