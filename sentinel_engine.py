# --- IMPORTS ---
import requests            # Standard library to make HTTP network calls (pinging our server).
import time                # Used to measure how long a request takes, and to pause our loop.
import numpy as np         # The math engine. We use this to calculate statistics like Standard Deviation.
from collections import deque # A "Double-Ended Queue". It's a list that automatically deletes its oldest item when full.
from datetime import datetime # Used to print exact timestamps in our logs so we know when an error occurred.

# --- CONFIGURATION (THE KNOBS AND DIALS) ---

# This is the exact URL of the Docker container we want to protect. 
# /health is a standard endpoint used to check if a server is alive.
TARGET_URL = "http://localhost:8000/health"

# STATISTICAL SETTINGS:
# WINDOW_SIZE is our "Memory". We will only look at the last 20 requests to calculate what is "normal".
# If the server naturally slows down over the day, the rolling window adapts to the new normal.
WINDOW_SIZE = 20        

# Z_SCORE_THRESHOLD is our "Sensitivity". 
# In statistics, a Z-Score of 3.0 means the data point is 3 standard deviations away from the average.
# This represents a 99.7% confidence that this is an extreme anomaly, drastically reducing false alarms.
Z_SCORE_THRESHOLD = 3.0 


# --- THE MAIN SYSTEM ---
class Sentinel:
    def __init__(self):
        # We initialize our memory. By setting maxlen=WINDOW_SIZE, if we add a 21st item, 
        # the 1st item is automatically forgotten. This keeps our memory fresh and efficient.
        self.latency_window = deque(maxlen=WINDOW_SIZE)
        
        # Print startup messages so the operator knows the system is booting up.
        print(f"[{datetime.now()}] 🛡️  Aethelgard Sentinel initialized.")
        print(f"[{datetime.now()}] 📊 Gathering baseline data (need {WINDOW_SIZE} pings)...")

    def fetch_metrics(self):
        """
        Action: Pings the target server and measures the exact time it takes to reply.
        Returns: The round-trip latency in milliseconds (ms), or a fallback value if it crashes.
        """
        try:
            # Record the exact microsecond before we send the request.
            start_time = time.time()
            
            # Send an HTTP GET request to our FastAPI server. 
            # timeout=5 means if the server doesn't reply in 5 seconds, we give up.
            response = requests.get(TARGET_URL, timeout=5)
            
            # Record the exact microsecond the reply arrives.
            end_time = time.time()
            
            # Subtract start from end to get total seconds, then multiply by 1000 for milliseconds.
            latency_ms = (end_time - start_time) * 1000
            return latency_ms
            
        # Error Handling: What if the Docker container is completely turned off?
        except requests.exceptions.ConnectionError:
            print("❌ Connection Failed! Is the Docker container running?")
            return None
            
        # Error Handling: What if the server is frozen and ignores us for 5 seconds?
        except requests.exceptions.Timeout:
            print("❌ TIMEOUT! Server is completely stuck.")
            # Return a massive artificial number (5000ms) to guarantee the math detects an anomaly.
            return 5000.0 

    def analyze(self, current_latency):
        """
        The Brain: Compares the current speed against the historical memory to find statistical outliers.
        Returns: A boolean (True if anomaly, False if normal) and the calculated Z-Score.
        """
        # Rule 1: Don't guess if you don't have enough data. 
        # If we haven't collected 20 pings yet, just return False (no anomaly).
        if len(self.latency_window) < WINDOW_SIZE:
            return False, 0.0

        # Rule 2: Calculate the "Normal" state.
        # np.mean calculates the average of our last 20 pings.
        mean = np.mean(self.latency_window)       
        
        # np.std calculates the Standard Deviation (how much the pings naturally bounce around).
        std_dev = np.std(self.latency_window)     

        # Edge Case Protection: If the server is perfectly fast every single time, std_dev becomes 0.
        # We can't divide by zero in math, so we set a tiny baseline jitter.
        if std_dev == 0: 
            std_dev = 0.001

        # Rule 3: Calculate the Z-Score.
        # Formula: (Current Speed - Average Speed) / Jitter
        # This tells us exactly how many "deviations" away from normal this current ping is.
        z_score = (current_latency - mean) / std_dev

        # Rule 4: Make a decision.
        # We use abs() to check absolute value (in case it's extremely fast or extremely slow).
        # If the score is higher than our threshold (3.0), we flag it as an anomaly.
        is_anomaly = abs(z_score) > Z_SCORE_THRESHOLD
        
        # Return our final decision and the mathematical proof (the score).
        return is_anomaly, z_score

    def run(self):
        """
        The Infinite Loop: This keeps the Sentinel running forever until we press Ctrl+C.
        """
        print("🟢 Monitoring started...")
        
        # Run endlessly.
        while True:
            # Step 1: Get the current speed.
            latency = self.fetch_metrics()
            
            # Step 2: If we successfully got a latency number, analyze it.
            if latency is not None:
                is_anomaly, z_score = self.analyze(latency)
                
                # Visual UI for the terminal: Green circle for good, Red siren for bad.
                status_icon = "🟢"
                if is_anomaly:
                    status_icon = "🚨"
                
                # Print a clean, formatted log line showing the live stats.
                # .2f forces the numbers to only show two decimal places.
                print(f"{status_icon} Latency: {latency:.2f}ms | Z-Score: {z_score:.2f}")

                # Step 3: If the math proves an anomaly exists, trigger the alarm.
                if is_anomaly:
                    self.trigger_alert(latency, z_score)
                
                # Step 4: Add this new ping to our memory so the rolling average updates.
                self.latency_window.append(latency)

            # Step 5: Wait exactly 1 second before pinging the server again so we don't accidentally DDoS it.
            time.sleep(1)

    def trigger_alert(self, latency, z_score):
        """
        The Action Center: This function is called ONLY when an anomaly is proven.
        In Phase 3, this is where we will write the code to wake up the AI Agent.
        """
        print("\n" + "!"*50) # Prints a big red banner to make sure the operator sees it.
        print(f"🔥 ANOMALY DETECTED! (Severity: {z_score:.2f}σ)") # Prints a message indicating the anomaly.
        print(f"   Metric: Latency spiked to {latency:.2f}ms") # Prints the latency value.
        print(f"   Action: Initiating Protocol Aethelgard...") # Prints a message indicating the next steps (which we will implement in Phase 3).
        print("!"*50 + "\n") # Prints the closing banner.
        
        # Pause the script for 2 seconds. 
        # This stops the terminal from infinitely spamming the error message while the AI starts working.
        time.sleep(2) 

# --- EXECUTION ---
# This standard Python line ensures the script only runs if executed directly 
# (e.g., 'python sentinel_engine.py'), not if it gets imported by another file.
if __name__ == "__main__":
    # Create an instance of our Sentinel class and start the infinite run() loop.
    bot = Sentinel()
    bot.run()