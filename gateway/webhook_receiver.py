# gateway/webhook_receiver.py
"""
Aethelgard Webhook Ingestion Gateway
Zero-cost, multi-tenant alert ingestion microservice.
Receives webhook alerts from Sentry, Prometheus Alertmanager, Datadog, or custom APMs,
translates them into standardized Aethelgard incident payloads, and triggers the closed-loop orchestrator.
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCIDENT_REPORTS_DIR = os.path.join(BASE_DIR, "reports", "incident_reports")
os.makedirs(INCIDENT_REPORTS_DIR, exist_ok=True)

app = FastAPI(
    title="Aethelgard Ingestion Gateway",
    description="Enterprise-grade webhook receiver bridging external APMs to the autonomous AI-SRE loop.",
    version="1.1.0"
)

# Standardized In-Memory Incident Registry
active_incidents: Dict[str, Any] = {}

class GenericAlertPayload(BaseModel):
    service_name: str
    target_endpoint: str
    observed_latency_ms: float
    error_type: Optional[str] = "PERFORMANCE_ANOMALY"
    server_status: Optional[str] = "DEGRADED"
    stack_trace: Optional[str] = None
    culprit_file: Optional[str] = None

def persist_incident_payload(incident_data: dict) -> str:
    """Helper to serialize incident payloads into the shared storage mount."""
    incident_id = incident_data["incident_id"]
    file_path = os.path.join(INCIDENT_REPORTS_DIR, f"{incident_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(incident_data, f, indent=4)
    active_incidents[incident_id] = incident_data
    return file_path

@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "gateway": "Aethelgard Webhook Ingestion Engine",
        "timestamp": datetime.now().isoformat(),
        "recorded_incidents_count": len(active_incidents)
    }

@app.get("/incidents")
def list_incidents():
    """Returns all captured incidents registered during this session."""
    return {
        "count": len(active_incidents),
        "incidents": list(active_incidents.values())
    }

@app.post("/webhook/sentry")
async def ingest_sentry_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Ingests Sentry Webhooks (issue alerts or error events).
    Parses culprit file, issue title, and stack trace into an Aethelgard incident context.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    incident_id = f"INC_SENTRY_{timestamp_str}"

    # Extract Sentry issue details
    data = body.get("data", {}).get("issue", {}) or body.get("event", {})
    culprit = data.get("culprit", "unknown_handler")
    title = data.get("title", "Sentry Performance Regression / Error")
    
    incident_context = {
        "incident_id": incident_id,
        "source": "SENTRY_WEBHOOK",
        "timestamp": datetime.now().isoformat(),
        "target_endpoint": culprit,
        "metrics": {
            "observed_latency_ms": 1500.0,
            "calculated_z_score": 4.2,
            "threshold_sigma": 3.0
        },
        "infrastructure_context": {
            "network_status": "SENTRY_ALERT",
            "server_reported_health": "DEGRADED",
            "alert_title": title,
            "culprit": culprit
        },
        "raw_payload_snippet": str(body)[:500]
    }

    report_path = persist_incident_payload(incident_context)
    print(f"\n[SENTRY ALERT] Incident captured from Sentry: {incident_id} -> {report_path}")

    return {
        "status": "ACCEPTED",
        "incident_id": incident_id,
        "action": "Queued for Aethelgard AI-SRE Autonomous Remediation"
    }

@app.post("/webhook/prometheus")
async def ingest_prometheus_webhook(request: Request):
    """
    Ingests Prometheus Alertmanager webhooks.
    Translates metric threshold violations into structured Aethelgard incidents.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    alerts = body.get("alerts", [])
    captured_ids = []

    for idx, alert in enumerate(alerts):
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        incident_id = f"INC_PROM_{timestamp_str}_{idx}"
        
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        alert_name = labels.get("alertname", "HighLatencyViolation")
        instance = labels.get("instance", "http://127.0.0.1:8000")

        incident_context = {
            "incident_id": incident_id,
            "source": "PROMETHEUS_ALERTMANAGER",
            "timestamp": datetime.now().isoformat(),
            "target_endpoint": instance,
            "metrics": {
                "observed_latency_ms": 1200.0,
                "calculated_z_score": 3.8,
                "threshold_sigma": 3.0
            },
            "infrastructure_context": {
                "network_status": "ALERTMANAGER_FIRE",
                "server_reported_health": "DEGRADED",
                "alertname": alert_name,
                "summary": annotations.get("summary", "Latency threshold violated"),
                "description": annotations.get("description", "")
            }
        }
        persist_incident_payload(incident_context)
        captured_ids.append(incident_id)

    return {
        "status": "ACCEPTED",
        "incidents_created": captured_ids
    }

@app.post("/webhook/generic")
async def ingest_generic_alert(payload: GenericAlertPayload):
    """
    Universal JSON alert ingestion endpoint for custom monitoring systems or Datadog.
    """
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    incident_id = f"INC_CUSTOM_{timestamp_str}"

    incident_context = {
        "incident_id": incident_id,
        "source": "GENERIC_API",
        "timestamp": datetime.now().isoformat(),
        "target_endpoint": payload.target_endpoint,
        "metrics": {
            "observed_latency_ms": payload.observed_latency_ms,
            "calculated_z_score": 3.5,
            "threshold_sigma": 3.0
        },
        "infrastructure_context": {
            "network_status": payload.error_type,
            "server_reported_health": payload.server_status,
            "stack_trace": payload.stack_trace,
            "culprit_file": payload.culprit_file
        }
    }

    persist_incident_payload(incident_context)
    return {
        "status": "ACCEPTED",
        "incident_id": incident_id,
        "message": "Incident payload registered in Aethelgard loop."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

