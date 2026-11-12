"""
test_trust.py — P11 Trust test suite

Function:
    Executable expression of SPEC.md. Written before trust.py per
    build discipline.

Layer:    P11 — Trust
Spec:     SPEC.md v1.0.0
Licence:  MSL-1.0
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath('../weight-layer'))

import trust

def test_empty_observations_returns_neutral():
    assert trust.calculate_lambda([], k=0.1, reference_time=100.0) == 1.0

def test_single_obs_at_reference_time():
    obs = [{"timestamp": 100.0, "value": 0.6}]
    assert trust.calculate_lambda(obs, k=0.1, reference_time=100.0) == pytest.approx(0.6)

def test_single_obs_decays_forward():
    obs = [{"timestamp": 0.0, "value": 2.0}]
    lam = trust.calculate_lambda(obs, k=0.1, reference_time=100.0)
    assert 1.0 < lam < 2.0

def test_single_obs_rises_toward_neutral():
    obs = [{"timestamp": 0.0, "value": 0.2}]
    lam = trust.calculate_lambda(obs, k=0.1, reference_time=100.0)
    assert 0.2 < lam < 1.0

def test_multiple_obs_uses_most_recent():
    obs = [
        {"timestamp": 0.0, "value": 2.0},
        {"timestamp": 50.0, "value": 0.8},
    ]
    lam = trust.calculate_lambda(obs, k=0.1, reference_time=50.0)
    assert lam == pytest.approx(0.8)

def test_multiple_obs_unsorted_input():
    obs = [
        {"timestamp": 50.0, "value": 0.8},
        {"timestamp": 0.0, "value": 2.0},
    ]
    lam = trust.calculate_lambda(obs, k=0.1, reference_time=50.0)
    assert lam == pytest.approx(0.8)

def test_k_required():
    obs = [{"timestamp": 0.0, "value": 1.0}]
    with pytest.raises(ValueError):
        trust.calculate_lambda(obs, k=None, reference_time=10.0)

def test_k_must_be_positive():
    obs = [{"timestamp": 0.0, "value": 1.0}]
    with pytest.raises(ValueError):
        trust.calculate_lambda(obs, k=0.0, reference_time=10.0)
    with pytest.raises(ValueError):
        trust.calculate_lambda(obs, k=-0.1, reference_time=10.0)

def test_reference_time_before_latest():
    obs = [{"timestamp": 100.0, "value": 1.0}]
    with pytest.raises(ValueError):
        trust.calculate_lambda(obs, k=0.1, reference_time=50.0)

def test_missing_timestamp():
    obs = [{"value": 1.0}]
    with pytest.raises(ValueError):
        trust.calculate_lambda(obs, k=0.1, reference_time=100.0)

def test_missing_value():
    obs = [{"timestamp": 0.0}]
    with pytest.raises(ValueError):
        trust.calculate_lambda(obs, k=0.1, reference_time=100.0)
