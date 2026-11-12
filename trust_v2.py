"""
trust_v2.py — P11 Trust hardening layer (V2)

Function:
    A layer over trust.py (v1.0.0, frozen). It does not rewrite the
    primitive. Every per-observation decay is computed by P10 via
    weight_v2.leighton_weight (which itself delegates to the frozen
    weight.leighton_weight), and the v1 "latest observation wins" rule
    is still served by trust.calculate_lambda. This layer adds strict
    input validation, weighted fusion over all observations with
    optional confidence, and a diagnostic that explains a fused λ.
    Pure math: no file I/O, no database, no crypto, no clock reads, no
    persistent state. λ is returned, never stored.

    Gaps in v1 closed here:
      - NaN/inf in reference_time, timestamp or value passed validation
        and returned NaN (or 1.0 for reference_time = inf).
      - Two observations sharing the latest timestamp with different
        values gave an order-dependent λ, breaking SPEC §1
        ("same evidence and parameters must reproduce the same λ").
      - A non-list observations argument (e.g. a string) or a non-dict
        observation produced a misleading "missing 'timestamp'" error.
      - The weight-layer import path was resolved against the current
        working directory, not this file.

Public API:
    1. calculate_lambda        — weighted fusion over all observations
    2. calculate_lambda_latest — v1 rule (latest wins), hardened
    3. explain_lambda          — diagnostic breakdown of a fused λ

Layer:    P11 — Trust
Depends:  trust.py (P11 v1.0.0), weight_v2.py (P10 v1.1.0)
Consumed: P14 Leighton Engine, P15 HAL
Version:  1.1.0
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
"""

import math
import os
import sys

_WEIGHT_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "weight-layer")
)
if _WEIGHT_DIR not in sys.path:
    sys.path.insert(0, _WEIGHT_DIR)

import weight_v2  # noqa: E402

import trust  # noqa: E402

NEUTRAL = weight_v2.NEUTRAL
DEFAULT_CONFIDENCE = 1.0


# ---------------------------------------------------------------------------
# 1. _is_number (internal)
#    True for a real int or float. bool is rejected, as in P10 V2.
# ---------------------------------------------------------------------------
def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ---------------------------------------------------------------------------
# 2. _check_finite (internal)
#    Raises TypeError for a non-number, ValueError for NaN/inf. The
#    name is used in the message so the caller can find the bad field.
# ---------------------------------------------------------------------------
def _check_finite(name, value):
    if not _is_number(value):
        raise TypeError(name + " must be a number")
    if not math.isfinite(value):
        raise ValueError(name + " must be finite (got " + repr(value) + ")")


# ---------------------------------------------------------------------------
# 3. _validate (internal)
#    Validates k, reference_time and every observation, and returns a
#    normalised list of (index, timestamp, value, confidence) tuples.
#    k is checked first and always (even for an empty list), matching
#    v1. k bounds come from P10 V2 by probing it at neutral, so the
#    rule lives in one place. Every value must be positive (P10's
#    domain), checked for all observations so both fusion rules agree.
# ---------------------------------------------------------------------------
def _validate(observations, k, reference_time):
    if k is None:
        raise ValueError("k (decay constant) must be provided explicitly")
    weight_v2.leighton_weight(NEUTRAL, 0.0, k)

    _check_finite("reference_time", reference_time)

    if not isinstance(observations, (list, tuple)):
        raise TypeError("observations must be a list or tuple of dicts")

    rows = []
    for i, obs in enumerate(observations):
        where = "observations[" + str(i) + "]"
        if not isinstance(obs, dict):
            raise TypeError(where + " must be a dict")
        if "timestamp" not in obs:
            raise ValueError(where + " missing 'timestamp'")
        if "value" not in obs:
            raise ValueError(where + " missing 'value'")

        ts = obs["timestamp"]
        value = obs["value"]
        confidence = obs.get("confidence", DEFAULT_CONFIDENCE)

        _check_finite(where + ".timestamp", ts)
        _check_finite(where + ".value", value)
        _check_finite(where + ".confidence", confidence)
        if value <= 0:
            raise ValueError(where + ".value must be positive (got " + repr(value) + ")")
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(
                where + ".confidence must be in [0, 1] (got " + repr(confidence) + ")"
            )
        if ts > reference_time:
            raise ValueError(
                "reference_time must be >= latest observation timestamp ("
                + where + ".timestamp=" + repr(ts) + ")"
            )
        rows.append((i, ts, value, confidence))
    return rows


# ---------------------------------------------------------------------------
# 4. _fuse (internal)
#    Core of weighted fusion. For each observation i:
#        Δtᵢ  = reference_time − timestampᵢ
#        λᵢ   = leighton_weight(valueᵢ, Δtᵢ, k)        (P10 V2)
#        fᵢ   = e^(−k Δtᵢ)                            (fraction remaining)
#        wᵢ   = confidenceᵢ × fᵢ
#    λ = 1.00 + Σ wᵢ (λᵢ − 1.00) / Σ wᵢ
#    Returns (lambda, per-observation rows, total_weight, fallback),
#    where fallback names why neutral was returned, or None.
# ---------------------------------------------------------------------------
def _fuse(observations, k, reference_time):
    rows = _validate(observations, k, reference_time)
    if not rows:
        return NEUTRAL, [], 0.0, "empty"

    detail = []
    total_weight = 0.0
    weighted_distance = 0.0
    for i, ts, value, confidence in rows:
        dt = reference_time - ts
        try:
            lam_i = weight_v2.leighton_weight(value, dt, k)
        except (TypeError, ValueError) as exc:
            raise type(exc)("observations[" + str(i) + "]: " + str(exc)) from exc
        fraction = math.exp(-k * dt)
        w = confidence * fraction
        total_weight += w
        weighted_distance += w * (lam_i - NEUTRAL)
        detail.append({
            "index": i,
            "timestamp": ts,
            "value": value,
            "confidence": confidence,
            "delta_t": dt,
            "lambda_at_reference": lam_i,
            "fraction_remaining": fraction,
            "weight": w,
        })

    if total_weight == 0.0:
        fallback = "no_confidence" if all(r[3] == 0.0 for r in rows) else "fully_decayed"
        lam = NEUTRAL
    else:
        fallback = None
        lam = NEUTRAL + weighted_distance / total_weight

    for d in detail:
        share = d["weight"] / total_weight if total_weight else 0.0
        d["share"] = share
        d["contribution"] = share * (d["lambda_at_reference"] - NEUTRAL)

    return lam, detail, total_weight, fallback


# ---------------------------------------------------------------------------
# 5. calculate_lambda
#    Weighted fusion over every observation (see _fuse). Each
#    observation may carry an optional "confidence" in [0, 1]
#    (default 1.0). Order-independent. Returns 1.00 (neutral) for an
#    empty list, when every confidence is 0, or when all evidence has
#    decayed past float precision.
# ---------------------------------------------------------------------------
def calculate_lambda(observations, k, reference_time):
    lam, _, _, _ = _fuse(observations, k, reference_time)
    return lam


# ---------------------------------------------------------------------------
# 6. calculate_lambda_latest
#    The v1 fusion rule (latest observation wins, decay forward) with
#    V2 validation. Rejects ambiguous evidence: two or more
#    observations at the latest timestamp with different values. The
#    λ itself is computed by the frozen trust.calculate_lambda.
#    "confidence" is validated but ignored by this rule.
# ---------------------------------------------------------------------------
def calculate_lambda_latest(observations, k, reference_time):
    rows = _validate(observations, k, reference_time)
    if not rows:
        return NEUTRAL

    latest_ts = max(r[1] for r in rows)
    latest_values = {r[2] for r in rows if r[1] == latest_ts}
    if len(latest_values) > 1:
        raise ValueError(
            "ambiguous evidence: multiple observations at latest timestamp "
            + repr(latest_ts) + " with different values " + repr(sorted(latest_values))
        )
    try:
        return trust.calculate_lambda(list(observations), k, reference_time)
    except (TypeError, ValueError) as exc:
        raise type(exc)("latest observation: " + str(exc)) from exc


# ---------------------------------------------------------------------------
# 7. explain_lambda
#    Diagnostic for one weighted fusion. Returns a dict with the inputs,
#    the fused λ, total weight, the reason for any neutral fallback, the
#    per-observation decay breakdown (sorted newest first) and a
#    plain-English summary. Pure: builds and returns data, prints
#    nothing.
# ---------------------------------------------------------------------------
def explain_lambda(observations, k, reference_time):
    lam, detail, total_weight, fallback = _fuse(observations, k, reference_time)
    detail.sort(key=lambda d: (-d["timestamp"], d["index"]))
    half_life = math.log(2) / k

    if fallback == "empty":
        summary = "No observations; lambda is neutral (1.00)."
    elif fallback == "no_confidence":
        summary = "Every observation has confidence 0; lambda is neutral (1.00)."
    elif fallback == "fully_decayed":
        summary = (
            "All evidence has decayed beyond float precision; lambda is neutral (1.00)."
        )
    else:
        top = max(detail, key=lambda d: d["share"])
        summary = (
            "Fused " + str(len(detail)) + " observation(s) at reference_time="
            + format(reference_time, ".6g") + " with k=" + format(k, ".6g")
            + " (half-life " + format(half_life, ".6g") + "). lambda="
            + format(lam, ".6g") + ". Largest share: observations["
            + str(top["index"]) + "] at t=" + format(top["timestamp"], ".6g")
            + " (" + format(top["share"] * 100, ".4g") + "%)."
        )

    return {
        "lambda": lam,
        "k": k,
        "reference_time": reference_time,
        "neutral": NEUTRAL,
        "half_life": half_life,
        "observation_count": len(detail),
        "total_weight": total_weight,
        "fallback": fallback,
        "observations": detail,
        "summary": summary,
    }
