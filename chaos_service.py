# IMPORTS
from fastapi import FastAPI # Import the FastAPI framework to create our web server
import asyncio # Import asyncio to handle non-blocking asynchronous operations (the "good" way to wait)
import time # Import time to handle blocking operations (the "bad" way to wait - our bug)
import random # Import random to generate random numbers for variable latency

# This 'app' object is the core controller of our web server.
app = FastAPI() # Initialize the FastAPI application

# --- STATE MANAGEMENT ---
# We use a global dictionary to store the "health" of our system.
# In a real app, this might be a database, but a variable works for this simulation.
# "status": "HEALTHY" means the system runs normally.
# "status": "DEGRADED" means we have triggered the Chaos Monkey (the bug).
system_state = {"status": "HEALTHY", "degradation_factor": 0.0}

# --- THE HEALTH CHECK ENDPOINT ---
# @app.get defines a route. When a user visits "http://localhost:8000/health", this function runs.
# 'async def' means this function can handle many users at once (concurrency).
@app.get("/health")
async def health_check():
    # Generate a random "base latency" between 20ms and 50ms.
    # This simulates how long a normal database query takes.
    base_latency = random.uniform(0.02, 0.05)

    # Check if our system has been sabotaged.
    if system_state["status"] == "DEGRADED":
        # If sabotaged, we calculate extra fake latency.
        # We multiply the degradation factor (1.0) by a random delay (0.5 to 1.5 seconds).
        added_latency = system_state["degradation_factor"] * random.uniform(0.5, 1.5)
        
        # --- THE INTENTIONAL BUG ---
        # We use 'time.sleep()'. This is a BLOCKING call.
        # It pauses the entire CPU thread. 
        # While this is sleeping, NO OTHER USER can get a response. The server freezes.
        # Your AI Agent's job will be to find this line and fix it later.
        time.sleep(base_latency + added_latency)
        
        # Return a JSON response telling us the system is struggling.
        return {
            "status": "struggling", 
            "latency_ms": (base_latency + added_latency) * 1000
        }

    # --- THE NORMAL BEHAVIOR ---
    # If the system is HEALTHY, we use 'await asyncio.sleep()'.
    # This is a NON-BLOCKING call.
    # It tells the server "Wait here for 'base_latency' seconds, but go serve other users while you wait."
    await asyncio.sleep(base_latency)
    
    # Return a JSON response saying everything is good.
    return {"status": "healthy", "latency_ms": base_latency * 1000}

# --- THE SABOTAGE ENDPOINT ---
# This endpoint allows us to manually break the server.
# We send a POST request here to turn "status" to "DEGRADED".
@app.post("/sabotage")
async def sabotage_system():
    # Update the global state to "DEGRADED"
    system_state["status"] = "DEGRADED"
    # Set the intensity of the lag to 1.0 (100%)
    system_state["degradation_factor"] = 1.0
    # Return a confirmation message
    return {"message": "⚠️ SYSTEM COMPROMISED: Latency injected."}

# --- THE REPAIR ENDPOINT ---
# This endpoint fixes the server manually (resetting state).
@app.post("/fix")
async def fix_system():
    # Reset status to "HEALTHY"
    system_state["status"] = "HEALTHY"
    # Reset lag to 0
    system_state["degradation_factor"] = 0.0
    # Return confirmation
    return {"message": "✅ SYSTEM RESTORED: Latency normal."}

# --- ENTRY POINT ---
# This block runs only if we execute this file directly (python chaos_service.py).
if __name__ == "__main__":
    # Import uvicorn, which is the high-speed server engine that runs FastAPI.
    import uvicorn
    
    # Start the server on localhost (127.0.0.1) at port 8000.
    # 'log_level="info"' means it will print basic status messages to the terminal.
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")