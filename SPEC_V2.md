# SPEC V2 — trust-layer (P11 Trust)

SPEC_V2.md — the specification for the P11 Trust V2 hardening layer.

Function:
    This document specifies `trust_v2.py`, a layer over the frozen
    `trust.py` (SPEC 1.0.0). It adds weighted fusion over all
    observations, optional per-observation confidence, a hardened form
    of the v1 "latest wins" rule, and a diagnostic. SPEC.md remains
    authoritative for v1; nothing here changes v1 behaviour.

Layer:     P11 — Trust
Depends:   trust.py (P11 v1.0.0), weight_v2.py (P10 v1.1.0)
Consumed:  P14 Leighton Engine, P15 HAL
Version:   SPEC_V2 1.1.0
Licence:   MSL-1.0
Author:    James Gilbert (Giblets Forge)

## 1. The Weighted Fusion Rule

Each observation i has a timestamp tᵢ, a value vᵢ > 0 and an optional
confidence cᵢ ∈ [0, 1] (default 1.0). At reference time T with decay
constant k:

    Δtᵢ = T − tᵢ
    λᵢ  = 1.00 + (vᵢ − 1.00) × e^(−k Δtᵢ)     (P10 V2 leighton_weight)
    wᵢ  = cᵢ × e^(−k Δtᵢ)
    λ   = 1.00 + Σ wᵢ (λᵢ − 1.00) / Σ wᵢ

Fresher, more confident evidence carries more weight. When observations
are far apart relative to the half-life (ln 2 / k), the result
converges on the v1 rule. The result is independent of list order
(SPEC §1 reproducibility). It lies within [min vᵢ, max vᵢ] ∪ {1.00}.

Neutral (1.00) is returned when:
- the list is empty (`fallback = "empty"`),
- every confidence is 0 (`"no_confidence"`),
- Σ wᵢ underflows to 0, so all evidence has decayed beyond float
  precision (`"fully_decayed"`).

## 2. Validation (all functions)

Checked in this order; the first failure raises.

1. k is None → ValueError.
2. k is validated by P10 V2: non-number or bool → TypeError; NaN/inf,
   ≤ 0, or outside [K_MIN, K_MAX] = [1e-9, 1e9] → ValueError. k is
   checked even for an empty list.
3. reference_time: non-number or bool → TypeError; NaN/inf → ValueError.
4. observations: not a list or tuple → TypeError.
5. Each observation, with its index named in the message:
   - not a dict → TypeError;
   - missing "timestamp" or "value" → ValueError;
   - timestamp, value or confidence not a number → TypeError;
     NaN/inf → ValueError;
   - value ≤ 0 → ValueError;
   - confidence outside [0, 1] → ValueError;
   - timestamp > reference_time → ValueError.

Inputs are never mutated.

## 3. Function Contracts

### 3.1 calculate_lambda(observations, k, reference_time) -> float
Weighted fusion per §1. Note: this differs from v1 `trust.calculate_lambda`
whenever more than one observation carries weight.

### 3.2 calculate_lambda_latest(observations, k, reference_time) -> float
The v1 rule (latest observation's value as λ₀, decayed forward) after §2
validation. Computed by `trust.calculate_lambda`. Two or more
observations at the latest timestamp with different values →
ValueError ("ambiguous evidence"); identical values are allowed.
Confidence is validated but ignored. Empty list → 1.00.

### 3.3 explain_lambda(observations, k, reference_time) -> dict
Same validation and λ as 3.1. Returns:

| key | meaning |
|---|---|
| lambda | fused λ (equals 3.1) |
| k, reference_time | inputs |
| neutral | 1.00 |
| half_life | ln 2 / k |
| observation_count | number of observations |
| total_weight | Σ wᵢ |
| fallback | None, "empty", "no_confidence" or "fully_decayed" |
| observations | per-observation rows, newest first (ties by input index) |
| summary | plain-English sentence |

Each row: index (position in input), timestamp, value, confidence,
delta_t, lambda_at_reference (λᵢ), fraction_remaining (e^(−kΔtᵢ)),
weight (wᵢ), share (wᵢ / Σw, 0 when Σw = 0), contribution
(share × (λᵢ − 1.00)). Σ share = 1 and 1.00 + Σ contribution = λ when no
fallback applies.

## 4. Known Limitations (P11 V2 1.1.0)

- One k for the whole stream. Per-domain k is a P14 concern.
- Recency weight uses the same k as the value decay; there is no
  separate weighting constant.
- Still no persistence. Storage is P9's job.
