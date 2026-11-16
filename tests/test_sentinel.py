# tests/test_sentinel.py
"""Unit tests for Sentinel statistical anomaly detection engine."""

import pytest
import numpy as np
from sentinel.sentinel_engine import PolishedSentinel

def test_sentinel_initialization():
    sentinel = PolishedSentinel(window_size=10, threshold=3.0)
    assert sentinel.window_size == 10
    assert sentinel.threshold == 3.0
    assert len(sentinel.latency_window) == 0
    assert sentinel.is_incident_active is False

def test_cold_start_gatekeeper():
    sentinel = PolishedSentinel(window_size=5, threshold=3.0)
    # Add 4 samples (less than window size of 5)
    for sample in [30.0, 32.0, 31.0, 29.0]:
        sentinel.latency_window.append(sample)
    
    is_anomaly, z_score, mean, std_dev = sentinel.analyze_anomalies(35.0)
    assert is_anomaly is False
    assert z_score == 0.0

def test_z_score_anomaly_detection():
    sentinel = PolishedSentinel(window_size=5, threshold=3.0)
    # Baseline: ~30ms with very low variance
    for sample in [30.0, 31.0, 30.0, 30.5, 29.5]:
        sentinel.latency_window.append(sample)

    # Spike to 1200ms (clear 3-sigma anomaly)
    is_anomaly, z_score, mean, std_dev = sentinel.analyze_anomalies(1200.0)
    assert is_anomaly is True
    assert z_score > 3.0
    assert mean > 25.0 and mean < 35.0

def test_zero_variance_guard():
    sentinel = PolishedSentinel(window_size=5, threshold=3.0)
    # Exactly identical samples (std_dev = 0)
    for _ in range(5):
        sentinel.latency_window.append(25.0)

    # Should not raise ZeroDivisionError
    is_anomaly, z_score, mean, std_dev = sentinel.analyze_anomalies(25.0)
    assert is_anomaly is False
    assert std_dev > 0.0  # Guard inflated std_dev to 0.001

