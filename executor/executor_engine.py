# executor/executor_engine.py
"""
Aethelgard Sandbox Validation Executor Engine
Creates hermetic, isolated test environments to validate candidate AI code patches.
Applies surgical patches with CRLF/LF normalization, builds a Docker sandbox container
on an isolated ephemeral port, and evaluates health telemetry before human sign-off.
"""

import os
import shutil
import socket
import requests
import time
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTION_SRC_DIR = os.getenv("TARGET_SERVICE_DIR", os.path.join(BASE_DIR, "target_service"))
SANDBOX_DIR = os.getenv("SANDBOX_WORKSPACE_DIR", os.path.join(BASE_DIR, "sandbox_workspace"))
SANDBOX_IMAGE_NAME = "aethelgard-sandbox:latest"
SANDBOX_CONTAINER_NAME = "aethelgard-sandbox-container"

class SandboxValidationExecutor:
    def __init__(self, prod_dir=PRODUCTION_SRC_DIR, sandbox_dir=SANDBOX_DIR):
        self.prod_dir = prod_dir
        self.sandbox_dir = sandbox_dir
        self.active_port = self._find_free_port(start_port=8080)

    def _find_free_port(self, start_port=8080, max_port=8099) -> int:
        """
        Scans for an available local TCP port to prevent collision with production
        services running on port 8000 or other local processes.
        """
        for port in range(start_port, max_port + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                result = s.connect_ex(("127.0.0.1", port))
                if result != 0:
                    return port
        return 8080

    def reset_and_provision_sandbox(self):
        """
        Tears down lingering containers and clones a clean, pristine replica of target_service.
        """
        self.terminate_sandbox_container()
        if os.path.exists(self.sandbox_dir):
            try:
                shutil.rmtree(self.sandbox_dir)
            except Exception:
                pass
        shutil.copytree(self.prod_dir, self.sandbox_dir)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📦 Isolated sandbox workspace provisioned.")

    def apply_targeted_string_patch(self, plan_json: dict) -> bool:
        """
        Applies the code mutation using a resilient two-tier replacement strategy:
        1. Exact character match (with CRLF/LF normalization)
        2. Whitespace-flexible fuzzy block match (ignoring indentation drift)
        """
        file_target = plan_json.get("file_target")
        string_before = plan_json.get("target_string_before")
        string_after = plan_json.get("target_string_after")

        if not file_target or not string_before or not string_after:
            print("❌ Invalid patch payload: missing target file or replacement strings.")
            return False

        # Resolve relative target file inside sandbox
        filename = os.path.basename(file_target)
        sandbox_file_path = os.path.join(self.sandbox_dir, "app", filename)
        if not os.path.exists(sandbox_file_path):
            sandbox_file_path = os.path.join(self.sandbox_dir, filename)
            if not os.path.exists(sandbox_file_path):
                print(f"❌ Target file not found in sandbox: {filename}")
                return False

        with open(sandbox_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        # Tier 1: Strict normalization (standardize on \n)
        norm_content = file_content.replace("\r\n", "\n")
        norm_before = string_before.replace("\r\n", "\n").strip()
        norm_after = string_after.replace("\r\n", "\n").strip()

        if norm_before in norm_content:
            updated_content = norm_content.replace(norm_before, norm_after, 1)
            with open(sandbox_file_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(updated_content)
            print(f"✅ Patch applied cleanly via Tier 1 (Exact Match): {filename}")
            return True

        # Tier 2: Whitespace-tolerant line block match
        before_lines = [l.strip() for l in norm_before.split("\n") if l.strip()]
        content_lines = norm_content.split("\n")

        for i in range(len(content_lines) - len(before_lines) + 1):
            slice_stripped = [content_lines[i + j].strip() for j in range(len(before_lines))]
            if slice_stripped == before_lines:
                # Detect base indentation of the matched block
                base_indent = content_lines[i][:len(content_lines[i]) - len(content_lines[i].lstrip())]
                after_indented = "\n".join(base_indent + l.lstrip() for l in norm_after.split("\n"))
                
                # Replace the slice
                new_lines = content_lines[:i] + [after_indented] + content_lines[i + len(before_lines):]
                with open(sandbox_file_path, "w", encoding="utf-8", newline="\n") as f:
                    f.write("\n".join(new_lines))
                print(f"✅ Patch applied cleanly via Tier 2 (Fuzzy Indent Match): {filename}")
                return True

        print(f"❌ String before match failed: target snippet not found in {filename}.")
        return False

    def deploy_sandbox_container(self) -> bool:
        """
        Builds the sandboxed Docker image and starts a container mapped to the free ephemeral port.
        """
        try:
            self.terminate_sandbox_container()

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🐳 Building sandbox container '{SANDBOX_IMAGE_NAME}'...")
            subprocess.run(
                ["docker", "build", "-t", SANDBOX_IMAGE_NAME, "."],
                cwd=self.sandbox_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Running sandbox container on port {self.active_port}:8000...")
            subprocess.run(
                [
                    "docker", "run", "-d",
                    "-p", f"{self.active_port}:8000",
                    "--name", SANDBOX_CONTAINER_NAME,
                    SANDBOX_IMAGE_NAME
                ],
                cwd=self.sandbox_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )

            # Give container ASGI worker time to bind
            time.sleep(3.0)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker build or run error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected container error: {e}")
            return False

    def verify_sandbox_telemetry(self, max_retries=5) -> tuple[bool, dict]:
        """
        Probes the sandbox health endpoint to verify latency normalization.
        Pass criteria: HTTP 200 and latency < 2000ms.
        """
        sandbox_url = f"http://127.0.0.1:{self.active_port}/health"

        for attempt in range(1, max_retries + 1):
            try:
                start_time = time.time()
                response = requests.get(sandbox_url, timeout=3.0)
                elapsed_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    data["measured_latency_ms"] = round(elapsed_ms, 2)
                    
                    # Latency check: Must be normalized well below the 1200ms anomaly mark
                    if elapsed_ms < 1000.0:
                        print(f"✅ Sandbox Telemetry Verified: {elapsed_ms:.2f}ms (< 1000ms threshold).")
                        return True, data
                    else:
                        print(f"⚠️ Sandbox latency still degraded: {elapsed_ms:.2f}ms.")
                        return False, data

            except Exception:
                time.sleep(1.0)

        print("❌ Sandbox health check verification timed out.")
        return False, {"status": "TIMEOUT", "error": "No response from sandbox container"}

    def terminate_sandbox_container(self):
        """
        Tears down the running sandbox container cleanly.
        """
        try:
            subprocess.run(
                ["docker", "rm", "-f", SANDBOX_CONTAINER_NAME],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

if __name__ == "__main__":
    executor = SandboxValidationExecutor()
    print(f"Sandbox executor ready. Assigned free port: {executor.active_port}")
