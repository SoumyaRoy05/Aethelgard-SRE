# target_service/app/main.py
"""
Aethelgard Monitored Target Service (FastAPI)
Simulates a real-world microservice with realistic telemetry jitter, Prometheus metrics,
and chaos-induced performance anomalies.
"""

from fastapi import FastAPI, Response
import asyncio
import time
import random
try:
    from .config import system_state
    from .sabotage import router as sabotage_router
except (ImportError, ValueError):
    try:
        from target_service.app.config import system_state
        from target_service.app.sabotage import router as sabotage_router
    except ImportError:
        from app.config import system_state
        from app.sabotage import router as sabotage_router

app = FastAPI(
    title="Aethelgard Production Target Service",
    description="Simulated mission-critical microservice monitored by Aethelgard AI-SRE.",
    version="1.1.0"
)

# Mount chaos testing subroutes
app.include_router(sabotage_router)

# Request counters for telemetry
request_metrics = {
    "total_requests": 0,
    "degraded_requests": 0,
    "start_time": time.time()
}

@app.get("/health")
async def health_check():
    """
    Primary heart-rate telemetry endpoint probed continuously by Aethelgard Sentinel.
    Normal latency jitter: 20ms - 50ms (simulating downstream DB query latency).
    """
    request_metrics["total_requests"] += 1
    base_latency = random.uniform(0.02, 0.05)
    start_eval = time.time()

    # Detect if service is under active chaos sabotage
    if system_state["status"] == "DEGRADED":
        request_metrics["degraded_requests"] += 1
        incident = system_state["incident_type"]

        if incident == "BLOCKING_IO":
            # BUG: Synchronous time.sleep forcefully hijacks the single async event loop thread
            time.sleep(1.2)

        elif incident == "CPU_BOUND":
            # BUG: Intense unoptimized CPU spin loop locking the thread for 1.2s
            spin_start = time.time()
            while time.time() - spin_start < 1.2:
                _ = [x**2 for x in range(5000)]

        elif incident == "POOL_EXHAUSTION":
            # BUG: Simulated pool exhaustion backoff
            await asyncio.sleep(1.0)

        elif incident == "MEMORY_LEAK":
            # Fast allocation and slight GC pause
            system_state["leak_buffer"].append(b"A" * 1024 * 512)
            time.sleep(0.3)

    # Standard non-blocking asynchronous processing wait
    await asyncio.sleep(base_latency)
    total_elapsed_ms = (time.time() - start_eval) * 1000

    return {
        "status": system_state["status"],
        "incident": system_state["incident_type"],
        "latency_ms": round(total_elapsed_ms, 2),
        "db_pool_status": f"{system_state['db_pool_available']}/{system_state['db_pool_max']}"
    }

@app.get("/metrics")
def prometheus_metrics():
    """
    Standard text-format Prometheus metrics endpoint for zero-cost observability scraping.
    """
    uptime = time.time() - request_metrics["start_time"]
    status_numeric = 1 if system_state["status"] == "HEALTHY" else 0
    
    metrics_payload = (
        "# HELP service_up Whether the service is healthy (1) or degraded (0)\n"
        "# TYPE service_up gauge\n"
        f"service_up {status_numeric}\n\n"
        "# HELP http_requests_total Total number of HTTP requests processed\n"
        "# TYPE http_requests_total counter\n"
        f"http_requests_total {request_metrics['total_requests']}\n\n"
        "# HELP http_requests_degraded_total Number of degraded or throttled requests\n"
        "# TYPE http_requests_degraded_total counter\n"
        f"http_requests_degraded_total {request_metrics['degraded_requests']}\n\n"
        "# HELP service_uptime_seconds Total service uptime in seconds\n"
        "# TYPE service_uptime_seconds gauge\n"
        f"service_uptime_seconds {uptime:.2f}\n"
    )
    return Response(content=metrics_payload, media_type="text/plain")

@app.get("/")
def index():
    return {
        "service": "Aethelgard Target Microservice",
        "status": system_state["status"],
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "status": "/status",
            "sabotage": ["/sabotage/blocking-io", "/sabotage/cpu-bound", "/sabotage/memory-leak", "/fix"]
        }
    }
