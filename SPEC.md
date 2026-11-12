# SPEC — trust-layer (P11 Trust)

SPEC.md — the complete layer specification for P11 Trust.

Function:
    This document is the authoritative specification for primitive
    layer P11 of the Forge Stack. It defines the fusion engine that
    combines observations and parameters into a final trust score.

Layer:     P11 — Trust
Depends:   P10 Weight (weight.py)
Consumed:  P14 Leighton Engine, P15 HAL
Version:   SPEC 1.0.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

## 1. The Fusion Rule

The persistent evidence is the observation stream and the complete
set of calculation parameters (λ₀, k, timestamps, reference time).
The same evidence and parameters must reproduce the same λ.

For P11 v1.0.0, fusion takes the *most recent* observation, treats
its value as λ₀ at its timestamp, and applies the Leighton Weight
decay forward to the reference time.

## 2. Function Contracts

### 2.1 calculate_lambda(observations: list[dict], k: float, reference_time: float) -> float
- Input:
  - observations: list of dicts with keys "timestamp" (float) and
    "value" (float).
  - k: decay constant, must be > 0.
  - reference_time: the current calculation time, must be >= the
    latest observation timestamp.
- Output: the current λ, a float.
- Failure:
  - ValueError if k is missing or <= 0.
  - ValueError if reference_time is earlier than the latest observation.
  - ValueError if any observation is missing timestamp or value.
- Empty list: returns 1.00 (neutral).

## 3. Known Limitations (P11 v1.0.0)

- Simple fusion: uses only the most recent observation. Weighted
  fusion over multiple observations is a P11 v2 concern.
- No persistence. P11 is pure math. Storage is P9's job.
