# tests/test_architect.py
"""Unit tests for Architect LLM JSON extraction and fallback rules."""

import pytest
from architect.architect_engine import LocalRemediationArchitect

def test_json_extraction_raw():
    architect = LocalRemediationArchitect()
    raw = '{"root_cause": "Blocking IO", "file_target": "main.py", "target_string_before": "a", "target_string_after": "b"}'
    parsed = architect._extract_clean_json(raw)
    assert parsed["root_cause"] == "Blocking IO"
    assert parsed["file_target"] == "main.py"

def test_json_extraction_markdown_fence():
    architect = LocalRemediationArchitect()
    raw = (
        "Here is the remediation analysis:\n```json\n"
        '{\n  "root_cause": "Event loop blocked by sleep",\n  "file_target": "target_service/app/main.py",\n'
        '  "target_string_before": "time.sleep(1.2)",\n  "target_string_after": "await asyncio.sleep(0.01)"\n}\n'
        "```\nHope this helps!"
    )
    parsed = architect._extract_clean_json(raw)
    assert "Event loop blocked" in parsed["root_cause"]
    assert parsed["target_string_before"] == "time.sleep(1.2)"

def test_fallback_remediator_blocking_io():
    architect = LocalRemediationArchitect()
    context = {"infrastructure_context": {"server_reported_health": "DEGRADED"}}
    snippet = 'if incident == "BLOCKING_IO":\n    time.sleep(1.2)'
    
    plan = architect._build_deterministic_fallback_plan(context, snippet)
    assert "time.sleep" in plan["target_string_before"]
    assert "asyncio.sleep" in plan["target_string_after"]
    assert plan["file_target"] == "target_service/app/main.py"

