# sentinel/sentinel_engine.py
"""
Aethelgard Sentinel Engine
Continuous real-time observability and statistical anomaly detection layer.
Computes rolling Z-Scores across time-series latency pings and captures incident traces.
"""

import os
import sys
import time
import json
import signal
import requests
import numpy as np
from collections import deque
from datetime import datetime

# Load optional .env variables if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- SYSTEM CONFIGURATION (ENVIRONMENT OVERRIDABLE) ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_URL = os.getenv("TARGET_SERVICE_URL", "http://127.0.0.1:8000/health")
WINDOW_SIZE = int(os.getenv("SENTINEL_WINDOW_SIZE", "20"))
Z_SCORE_THRESHOLD = float(os.getenv("SENTINEL_Z_SCORE_THRESHOLD", "3.0"))
POLL_INTERVAL = float(os.getenv("SENTINEL_POLL_INTERVAL_SECONDS", "1.0"))
INCIDENT_REPORT_DIR = os.path.join(BASE_DIR, "reports", "incident_reports")

class PolishedSentinel:
    def __init__(self, target_url=TARGET_URL, window_size=WINDOW_SIZE, threshold=Z_SCORE_THRESHOLD):
        self.target_url = target_url
        self.window_size = window_size
        self.threshold = threshold
        self.latency_window = deque(maxlen=self.window_size)
        self.is_incident_active = False
        self.running = True

        os.makedirs(INCIDENT_REPORT_DIR, exist_ok=True)

        # Wire graceful shutdown handlers
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🛡️  Aethelgard Sentinel Engine Initialized.")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📊 Target: {self.target_url} | Window: {self.window_size} | Threshold: {self.threshold}σ")

    def _handle_exit(self, signum, frame):
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🛑 Sentinel shutting down cleanly...")
        self.running = False
        sys.exit(0)

    def fetch_telemetry(self):
        """
        Polls target microservice and returns (latency_ms, network_status, server_status).
        Enforces defensive timeouts to handle hung/frozen threads without stalling the sentinel.
        """
        try:
            start_time = time.time()
            response = requests.get(self.target_url, timeout=3.0)
            latency_ms = (time.time() - start_time) * 1000

            server_reported_status = "UNKNOWN"
            try:
                data = response.json()
                server_reported_status = data.get("status", "UNKNOWN")
            except Exception:
                pass

            return latency_ms, "OK", server_reported_status

        except requests.exceptions.Timeout:
            # SRE Practice: Artificial ceiling to trip statistical anomaly math on hung threads
            return 3000.0, "TIMEOUT_ERROR", "DEGRADED"
        except requests.exceptions.ConnectionError:
            return None, "CONNECTION_FAILURE", "OFFLINE"
        except Exception as e:
            return None, f"ERROR: {str(e)}", "UNKNOWN"

    def analyze_anomalies(self, current_latency):
        """
        Calculates rolling Z-Score: (current - mean) / std_dev.
        Includes guards against cold-start and zero standard deviation.
        """
        if len(self.latency_window) < self.window_size:
            print(f"⏳ Ingesting baseline telemetry... [{len(self.latency_window)}/{self.window_size} samples collected]")
            return False, 0.0, 0.0, 0.0

        samples = np.array(self.latency_window)
        mean_baseline = float(np.mean(samples))
        std_dev_baseline = float(np.std(samples))

        # Avoid division by zero on perfectly uniform latency
        if std_dev_baseline == 0:
            std_dev_baseline = 0.001

        z_score = (current_latency - mean_baseline) / std_dev_baseline
        is_anomaly = abs(z_score) > self.threshold

        return is_anomaly, z_score, mean_baseline, std_dev_baseline

    def trigger_investigator(self, latency, z_score, mean, std_dev, error_type, server_status):
        """
        Deduplicates alerts and persists structured incident payload into reports/incident_reports/.
        """
        if self.is_incident_active:
            return

        self.is_incident_active = True
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        samples = list(self.latency_window)
        p50 = float(np.percentile(samples, 50)) if samples else 0.0
        p95 = float(np.percentile(samples, 95)) if samples else 0.0
        p99 = float(np.percentile(samples, 99)) if samples else 0.0

        incident_context = {
            "incident_id": f"INC_{timestamp_str}",
            "timestamp": datetime.now().isoformat(),
            "target_endpoint": self.target_url,
            "metrics": {
                "observed_latency_ms": round(latency, 2),
                "baseline_mean_ms": round(mean, 2),
                "baseline_std_dev_ms": round(std_dev, 4),
                "calculated_z_score": round(z_score, 2),
                "threshold_sigma": self.threshold,
                "percentiles": {
                    "p50_ms": round(p50, 2),
                    "p95_ms": round(p95, 2),
                    "p99_ms": round(p99, 2)
                }
            },
            "infrastructure_context": {
                "network_status": error_type,
                "server_reported_health": server_status
            },
            "recent_latency_samples": [round(x, 2) for x in samples]
        }

        report_filename = f"incident_{timestamp_str}.json"
        report_path = os.path.join(INCIDENT_REPORT_DIR, report_filename)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(incident_context, f, indent=4)

        print("\n" + "!" * 70)
        print(f"🚨 ANOMALY DETECTED AND VERIFIED (Z-Score: {z_score:.2f}σ > {self.threshold}σ)")
        print(f"📈 Latency Spiked: {latency:.2f}ms (Baseline Mean: {mean:.2f}ms | p99: {p99:.2f}ms)")
        print(f"📁 Incident context persisted: {report_path}")
        print("!" * 70 + "\n")

    def run_observability_loop(self):
        """Main non-blocking polling and evaluation loop."""
        print("🟢 Continuous observability active. Monitoring health telemetry...")

        while self.running:
            latency, network_status, server_status = self.fetch_telemetry()

            if latency is not None:
                is_anomaly, z_score, mean, std_dev = self.analyze_anomalies(latency)
                status_icon = "🚨" if is_anomaly else "🟢"

                # Check for recovery back into acceptable bounds
                if not is_anomaly and self.is_incident_active:
                    print(f"\n✅ RECOVERY: Telemetry normalized back within acceptable thresholds.\n")
                    self.is_incident_active = False

                if len(self.latency_window) >= self.window_size:
                    print(f"{status_icon} Latency: {latency:.2f}ms | Z-Score: {z_score:+.2f}σ | Rolling Mean: {mean:.2f}ms")

                if is_anomaly:
                    self.trigger_investigator(latency, z_score, mean, std_dev, network_status, server_status)

                self.latency_window.append(latency)
            else:
                print(f"❌ Connection failure to {self.target_url}. Retrying...")
                if not self.is_incident_active:
                    self.trigger_investigator(3000.0, 99.9, 0.0, 0.0, network_status, server_status)

            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    sentinel = PolishedSentinel()
    sentinel.run_observability_loop()
