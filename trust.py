"""
trust.py — P11 Trust primitive layer

Function:
    The fusion engine. Combines evidence observations and parameters
    into a final trust score. Pure math over given inputs.

Public API:
    1. calculate_lambda — Compute current λ from observations.

Layer:    P11 — Trust
Depends:  P10 Weight (weight.py)
Consumed: P14 Leighton Engine, P15 HAL
Version:  1.0.0 (on freeze; 0.0.0-dev until then)
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import os
import sys

sys.path.insert(0, os.path.abspath('../weight-layer'))
import weight

# ---------------------------------------------------------------------------
# 1. calculate_lambda
#    Picks the most recent observation, treats its value as λ₀ at its
#    timestamp, and decays forward to reference_time.
# ---------------------------------------------------------------------------
def calculate_lambda(observations, k, reference_time):
    if k is None:
        raise ValueError("k (decay constant) must be provided and positive")
    if k <= 0:
        raise ValueError("k (decay constant) must be provided and positive")

    if not observations:
        return 1.0

    for obs in observations:
        if "timestamp" not in obs:
            raise ValueError("observation missing 'timestamp'")
        if "value" not in obs:
            raise ValueError("observation missing 'value'")

    latest = max(observations, key=lambda o: o["timestamp"])
    latest_time = latest["timestamp"]
    lambda_zero = latest["value"]

    if reference_time < latest_time:
        raise ValueError("reference_time must be >= latest observation timestamp")

    delta_t = reference_time - latest_time
    return weight.leighton_weight(lambda_zero, delta_t, k)
