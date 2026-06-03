# target_service/app/main.py

# Import the root FastAPI web application instance to instantiate our core cloud routing server framework.
from fastapi import FastAPI
# Import the standard asyncio library to manage our non-blocking concurrency operations and timing waits.
import asyncio
# Import the native time engine to explicitly trigger synchronous thread locks and capture latency traces.
import time
# Import the random generator to inject slight, non-deterministic latency noise into our normal mock DB calls.
import random
# Pull our global system status dictionary tracking structural performance health into scope.
from app.config import system_state
# Pull our modular administrative sabotage router containing our attack control paths into scope.
from app.sabotage import router as sabotage_router

# Initialize the master FastAPI engine application stack decorated with an auditable corporate project title.
app = FastAPI(title="Aethelgard Target Service")

# Include the external sabotage router sub-routes natively into our core microservice network mapping.
app.include_router(sabotage_router)

# Expose an asynchronous GET gateway representing the target service's heart-rate monitoring telemetry path.
@app.get("/health")
async def health_check():
    # Simulate normal database P99 latency jitter by picking a random time slice between 20ms and 50ms.
    base_latency = random.uniform(0.02, 0.05)

    # Inspect the global memory model to evaluate if an SRE incident simulation has been activated.
    if system_state["status"] == "DEGRADED":
        
        # CONDITION A: Evaluate if the active performance regression vector represents a Blocking I/O fault.
        if system_state["incident_type"] == "BLOCKING_IO":
            # EXPLOIT POINT: Invoke a synchronous time.sleep call which forcefully hijacks the single async thread.
            # This starves the event loop entirely; no other active web connections can resolve while this executes.
            time.sleep(1.2)
            
        # CONDITION B: Evaluate if the performance anomaly represents a thread-locking intense math operation.
        elif system_state["incident_type"] == "CPU_BOUND":
            # Capture the exact epoch timestamp microsecond right before entering the core execution loop.
            start_time = time.time()
            # Construct a hard spin loop designed to completely lock up the thread execution state for 1.2 seconds.
            while time.time() - start_time < 1.2:
                # Force continuous computation of a synthetic list comprehension to spike processor saturation metrics.
                _ = [x**2 for x in range(5000)]
                
    # PERFORMANCE SAFE PATH: Execute a non-blocking asynchronous wait command to process our simulated database query delay.
    # This releases control back to the event loop pool, allowing the app to process thousands of concurrent pings.
    await asyncio.sleep(base_latency)
    
    # Return a clean, production-grade JSON dictionary response frame mapping our active health telemetry structure.
    return {
        "status": system_state["status"],
        "incident": system_state["incident_type"],
        "latency_ms": round(base_latency * 1000, 2)
    }