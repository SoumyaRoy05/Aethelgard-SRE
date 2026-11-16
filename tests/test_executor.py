# tests/test_executor.py
"""Unit tests for Sandbox Executor patch application and port discovery."""

import os
import tempfile
import pytest
from executor.executor_engine import SandboxValidationExecutor

def test_find_free_port():
    executor = SandboxValidationExecutor()
    port = executor._find_free_port(start_port=8080, max_port=8099)
    assert 8080 <= port <= 8099

def test_apply_patch_exact_match(tmp_path):
    sandbox_app = tmp_path / "app"
    sandbox_app.mkdir()
    target_file = sandbox_app / "sample.py"
    target_file.write_text("def run():\n    time.sleep(1.2)\n", encoding="utf-8")

    executor = SandboxValidationExecutor(sandbox_dir=str(tmp_path))
    plan = {
        "file_target": "target_service/app/sample.py",
        "target_string_before": "time.sleep(1.2)",
        "target_string_after": "await asyncio.sleep(0.01)"
    }

    success = executor.apply_targeted_string_patch(plan)
    assert success is True
    assert "await asyncio.sleep(0.01)" in target_file.read_text(encoding="utf-8")

def test_apply_patch_fuzzy_indent_match(tmp_path):
    sandbox_app = tmp_path / "app"
    sandbox_app.mkdir()
    target_file = sandbox_app / "sample.py"
    target_file.write_text("        if condition:\n            time.sleep(1.2)\n", encoding="utf-8")

    executor = SandboxValidationExecutor(sandbox_dir=str(tmp_path))
    plan = {
        "file_target": "target_service/app/sample.py",
        # Snippet provided with less indent
        "target_string_before": "if condition:\n    time.sleep(1.2)",
        "target_string_after": "if condition:\n    await asyncio.sleep(0.01)"
    }

    success = executor.apply_targeted_string_patch(plan)
    assert success is True
    content = target_file.read_text(encoding="utf-8")
    assert "await asyncio.sleep(0.01)" in content

