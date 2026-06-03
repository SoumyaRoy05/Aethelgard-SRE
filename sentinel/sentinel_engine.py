# sentinel/sentinel_engine.py

# Import requests to handle HTTP polling handshakes against the application endpoints.
import requests
# Import time to compute performance durations and regulate loop frequencies.
import time
# Import numpy as our core data science math engine to handle sliding standard deviations.
import numpy as np
# Import os to manage pathing and file verification abstractions.
import os
# Import json to serialize structured incident telemetry frames into machine-parseable data.
import json
# Import deque to act as our self-cleaning sliding memory array window.
from collections import deque
# Import datetime to attach precise, human-auditable timestamps to system errors.
from datetime import datetime

# --- SYSTEM CONFIGURATION TUNING KNOBS ---
# The target destination route we are monitoring, pointing to our local FastAPI microservice.
TARGET_URL = "http://127.0.0.1:8000/health"
# The size of our data queue. The Sentinel looks back at the last 20 pings to calculate what is "normal".
WINDOW_SIZE = 20
# Sensitivity matrix boundary. A Z-score exceeding 3.0 represents an extreme 3-sigma anomaly (99.7% confidence).
Z_SCORE_THRESHOLD = 3.0

# Dynamic path resolution to find the master project root path regardless of execution origin shell.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCIDENT_REPORT_DIR = os.path.join(BASE_DIR, "reports", "incident_reports")

class PolishedSentinel:
    def __init__(self):
        # Instantiate our sliding time-series data window. Maxlen automatically pops old entries.
        self.latency_window = deque(maxlen=WINDOW_SIZE)
        # Operational latch flag to guarantee alert deduplication and prevent file spamming.
        self.is_incident_active = False
        
        # Programmatically ensure the shared reporting workspace exists before running polls.
        os.makedirs(INCIDENT_REPORT_DIR, exist_ok=True)
        
        print(f"[{datetime.now()}] 🛡️ Aethelgard Sentinel Engine safely initialized.")
        print(f"[{datetime.now()}] 📊 Monitoring target destination: {TARGET_URL}")

    def fetch_telemetry(self):
        """
        Harvests high-frequency round-trip response metrics from the monitored microservice.
        Features robust exception boundaries to handle complete timeouts and network failure states.
        """
        try:
            # Capture microsecond precise snapshot right before launching the HTTP GET handshake.
            start_time = time.time()
            # Issue request. timeout=3.0 handles frozen threads gracefully before the sentinel hangs.
            response = requests.get(TARGET_URL, timeout=3.0)
            # Capture microsecond precise snapshot upon completion.
            end_time = time.time()
            
            # Formulate full delta calculation and convert raw seconds to milliseconds.
            latency_ms = (end_time - start_time) * 1000
            
            # Default server reporting value. Attempt to extract internal state telemetry variables.
            server_reported_status = "UNKNOWN"
            try:
                data = response.json()
                server_reported_status = data.get("status", "UNKNOWN")
            except Exception:
                pass
                
            return latency_ms, "OK", server_reported_status

        except requests.exceptions.Timeout:
            # SRE Practice: If a timeout is hit, return an artificial high ceiling value to force math anomaly flags.
            return 3000.0, "TIMEOUT_ERROR", "DEGRADED"
        except requests.exceptions.ConnectionError:
            # Handle severe crash cases where the server is completely shut off or blocked.
            return None, "CONNECTION_FAILURE", "OFFLINE"

    def analyze_anomalies(self, current_latency):
        """
        Statistical Processor Module: Calculates rolling Z-Scores across live time-series frames.
        Enforces defensive cold-start controls to prevent algorithmic error generation.
        """
        # COLD START GATEKEEPER: Do not generate statistical decisions until window density is reached.
        if len(self.latency_window) < WINDOW_SIZE:
            print(f"⏳ Ingesting baseline telemetry data... [{len(self.latency_window)}/{WINDOW_SIZE} collected]")
            return False, 0.0, 0.0, 0.0

        # Leverage numpy to extract real-time statistical distribution traits of the rolling history.
        mean_baseline = float(np.mean(self.latency_window))
        std_dev_baseline = float(np.std(self.latency_window))

        # EDGE CASE SHIELD: If standard deviation drops to zero (perfect speed), inflate slightly to evade zero-division.
        if std_dev_baseline == 0:
            std_dev_baseline = 0.001

        # Standard Anomaly Deviation formula application: (Observation - Center Point) / Variance scale
        z_score = (current_latency - mean_baseline) / std_dev_baseline
        
        # Evaluate absolute deviation scale against our target production threshold parameters.
        is_anomaly = abs(z_score) > Z_SCORE_THRESHOLD
        
        return is_anomaly, z_score, mean_baseline, std_dev_baseline

    def trigger_investigator(self, latency, z_score, mean, std_dev, error_type, server_status):
        """
        Phase 3 Investigator Integration: Captures live structural telemetry data matrices upon anomaly validation.
        Serializes comprehensive JSON context packets to act as localized RAG prompt models.
        """
        # ALERT DEDUPLICATION PROTOCOL: If this out-of-bounds incident is already cataloged, abort loop duplication.
        if self.is_incident_active:
            return

        # Activate structural incident lock tracking.
        self.is_incident_active = True
        # Formulate highly structured human-auditable file indexing string parameters.
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Assemble high-fidelity JSON payload containing all necessary context dimensions.
        incident_context = {
            "incident_id": f"INC_{timestamp_str}",
            "timestamp": datetime.now().isoformat(),
            "target_endpoint": TARGET_URL,
            "metrics": {
                "observed_latency_ms": round(latency, 2),
                "baseline_mean_ms": round(mean, 2),
                "baseline_std_dev_ms": round(std_dev, 4),
                "calculated_z_score": round(z_score, 2),
                "threshold_sigma": Z_SCORE_THRESHOLD
            },
            "infrastructure_context": {
                "network_status": error_type,
                "server_reported_health": server_status
            },
            # Map the exact trailing history buffer state so the diagnostic engine can trace the trajectory.
            "recent_latency_samples": [round(x, 2) for x in list(self.latency_window)]
        }

        # Structure filename path targets.
        report_filename = f"incident_{timestamp_str}.json"
        report_path = os.path.join(INCIDENT_REPORT_DIR, report_filename)

        # Persist structured incident dump context safely into the shared storage mount folder.
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(incident_context, f, indent=4)

        # Trigger high-visibility diagnostic warnings into the standard console execution monitor.
        print("\n" + "!" * 60)
        print(f"🔥 ANOMALY DETECTED AND VERIFIED! (Severity Scale: {z_score:.2f}σ)")
        print(f"📈 Performance Trace Spiked: {latency:.2f}ms [Baseline Expected Mean: {mean:.2f}ms]")
        print(f"🕵️‍♂️ Investigator Component Deployed: Incident footprint written to local workspace.")
        print(f"📂 Audit Target Captured: {report_path}")
        print("!" * 60 + "\n")

    def run_observability_loop(self):
        """
        Infinite Operational Scraper Loop: Orchestrates network pings, mathematical sweeps, and recovery state drops.
        """
        print("🟢 Continuous infrastructure observability state active. Press Ctrl+C to terminate.")
        
        while True:
            # Query the target service web metrics.
            latency, network_status, server_status = self.fetch_telemetry()
            
            # If the network boundary successfully returns data, evaluate statistics.
            if latency is not None:
                is_anomaly, z_score, mean, std_dev = self.analyze_anomalies(latency)
                
                # Dynamic terminal dashboard visual status indicators.
                status_icon = "🟢" if not is_anomaly else "🚨"
                
                # RECOVERY RECOGNITION BOUNDARY: If system metrics descend below sigma limits, release alert suppression.
                if not is_anomaly and self.is_incident_active:
                    print(f"\n✅ RECOVERY TRANSACTION: Telemetry normalized back within acceptable baseline sigma thresholds.\n")
                    self.is_incident_active = False

                # Format and output real-time metric traces to the terminal console panel.
                if len(self.latency_window) >= WINDOW_SIZE:
                    print(f"{status_icon} Latency: {latency:.2f}ms | Z-Score: {z_score:.2f} | Running Mean: {mean:.2f}ms")
                
                # If statistical analysis detects out-of-bounds variance, trigger the investigator dump engine.
                if is_anomaly:
                    self.trigger_investigator(latency, z_score, mean, std_dev, network_status, server_status)
                
                # Feed current operational parameters back into historical queue tracking arrays.
                self.latency_window.append(latency)
                
            else:
                # System network state dropped completely flat. Handle system-wide outage boundaries.
                print("❌ Target server connection dropped completely. Retrying telemetry harvest next frame...")
                if not self.is_incident_active:
                    self.trigger_investigator(3000.0, 99.9, 0.0, 0.0, network_status, server_status)

            # Rest the thread script execution for exactly 1.0 seconds to prevent denial-of-service traffic simulation.
            time.sleep(1.0)

if __name__ == "__main__":
    # Instantiate and spin up the complete integrated Sentinel/Investigator core monitoring suite.
    sentinel_bot = PolishedSentinel()
    sentinel_bot.run_observability_loop()