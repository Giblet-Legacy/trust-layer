"""
test_trust_v2.py — P11 Trust V2 test suite

Function:
    Executable expression of SPEC_V2.md. Covers weighted fusion,
    confidence weighting, the hardened latest-wins rule, explain_lambda,
    and every v1 gap that V2 closes. Path setup is in conftest.py.

Layer:    P11 — Trust
Spec:     SPEC_V2.md v1.1.0
Licence:  MSL-1.0
"""

import math

import pytest

import trust
import trust_v2

NAN = float("nan")
INF = float("inf")


# ---------------------------------------------------------------------------
# 1. obs (helper)
#    Builds one observation dict; "confidence" is set only if given.
# ---------------------------------------------------------------------------
def obs(ts, value, confidence=None):
    d = {"timestamp": ts, "value": value}
    if confidence is not None:
        d["confidence"] = confidence
    return d


# --- 1. calculate_lambda: weighted fusion ---------------------------------

def test_empty_returns_neutral():
    assert trust_v2.calculate_lambda([], k=0.1, reference_time=100.0) == 1.0


def test_single_obs_matches_v1():
    o = [obs(0.0, 2.0)]
    assert trust_v2.calculate_lambda(o, 0.1, 30.0) == pytest.approx(
        trust.calculate_lambda(o, 0.1, 30.0)
    )


def test_fusion_formula():
    o = [obs(0.0, 2.0), obs(10.0, 0.5)]
    k, ref = 0.1, 20.0
    l1 = 1 + (2.0 - 1) * math.exp(-k * 20)
    l2 = 1 + (0.5 - 1) * math.exp(-k * 10)
    w1, w2 = math.exp(-k * 20), math.exp(-k * 10)
    expected = 1 + (w1 * (l1 - 1) + w2 * (l2 - 1)) / (w1 + w2)
    assert trust_v2.calculate_lambda(o, k, ref) == pytest.approx(expected)


def test_fusion_is_order_independent():
    o = [obs(0.0, 2.0), obs(10.0, 0.5), obs(5.0, 1.3)]
    a = trust_v2.calculate_lambda(o, 0.1, 20.0)
    b = trust_v2.calculate_lambda(list(reversed(o)), 0.1, 20.0)
    assert a == b


def test_fusion_uses_all_observations():
    o = [obs(0.0, 2.0), obs(50.0, 0.8)]
    fused = trust_v2.calculate_lambda(o, 0.01, 50.0)
    latest = trust_v2.calculate_lambda_latest(o, 0.01, 50.0)
    assert latest == pytest.approx(0.8)
    assert fused > latest


def test_fresher_evidence_dominates():
    o = [obs(0.0, 0.2), obs(100.0, 1.5)]
    assert trust_v2.calculate_lambda(o, 0.1, 100.0) == pytest.approx(1.5, abs=1e-3)


def test_identical_values_same_time_no_shift():
    o = [obs(10.0, 1.4), obs(10.0, 1.4)]
    assert trust_v2.calculate_lambda(o, 0.1, 10.0) == pytest.approx(1.4)


def test_duplicate_timestamps_averaged():
    o = [obs(5.0, 2.0), obs(5.0, 0.5)]
    assert trust_v2.calculate_lambda(o, 0.1, 5.0) == pytest.approx(1.25)


def test_result_stays_within_value_range():
    o = [obs(0.0, 0.3), obs(3.0, 1.7), obs(6.0, 1.1)]
    lam = trust_v2.calculate_lambda(o, 0.05, 6.0)
    assert 0.3 <= lam <= 1.7


def test_tuple_input_accepted():
    o = (obs(0.0, 2.0),)
    assert trust_v2.calculate_lambda(o, 0.1, 0.0) == pytest.approx(2.0)


# --- 2. confidence weighting ----------------------------------------------

def test_default_confidence_is_one():
    a = trust_v2.calculate_lambda([obs(0.0, 2.0), obs(0.0, 0.5)], 0.1, 0.0)
    b = trust_v2.calculate_lambda([obs(0.0, 2.0, 1.0), obs(0.0, 0.5, 1.0)], 0.1, 0.0)
    assert a == b


def test_confidence_weights_mean():
    o = [obs(0.0, 2.0, 0.75), obs(0.0, 0.5, 0.25)]
    assert trust_v2.calculate_lambda(o, 0.1, 0.0) == pytest.approx(0.75 * 2.0 + 0.25 * 0.5)


def test_zero_confidence_excluded():
    o = [obs(0.0, 2.0, 0.0), obs(0.0, 0.5, 1.0)]
    assert trust_v2.calculate_lambda(o, 0.1, 0.0) == pytest.approx(0.5)


def test_all_zero_confidence_returns_neutral():
    o = [obs(0.0, 2.0, 0.0), obs(1.0, 0.5, 0.0)]
    assert trust_v2.calculate_lambda(o, 0.1, 1.0) == 1.0


@pytest.mark.parametrize("c", [-0.1, 1.1, NAN, INF])
def test_confidence_out_of_range(c):
    with pytest.raises(ValueError):
        trust_v2.calculate_lambda([obs(0.0, 2.0, c)], 0.1, 1.0)


@pytest.mark.parametrize("c", ["high", True, None])
def test_confidence_wrong_type(c):
    o = obs(0.0, 2.0)
    o["confidence"] = c
    with pytest.raises(TypeError):
        trust_v2.calculate_lambda([o], 0.1, 1.0)


# --- 3. fully decayed evidence ---------------------------------------------

def test_fully_decayed_returns_neutral():
    o = [obs(0.0, 2.0)]
    assert trust_v2.calculate_lambda(o, 1e9, 1e6) == 1.0
    assert trust_v2.explain_lambda(o, 1e9, 1e6)["fallback"] == "fully_decayed"


# --- 4. validation (v1 gaps) ----------------------------------------------

def test_k_required():
    with pytest.raises(ValueError):
        trust_v2.calculate_lambda([obs(0.0, 1.0)], None, 10.0)


def test_k_checked_even_when_empty():
    with pytest.raises(ValueError):
        trust_v2.calculate_lambda([], 0.0, 10.0)


@pytest.mark.parametrize("k", [0.0, -0.1, NAN, INF, 1e-12, 1e12])
def test_k_invalid(k):
    with pytest.raises(ValueError):
        trust_v2.calculate_lambda([obs(0.0, 1.0)], k, 10.0)


def test_k_bool_rejected():
    with pytest.raises(TypeError):
        trust_v2.calculate_lambda([obs(0.0, 1.0)], True, 10.0)


@pytest.mark.parametrize("ref", [NAN, INF, -INF])
def test_reference_time_non_finite(ref):
    with pytest.raises(ValueError):
        trust_v2.calculate_lambda([obs(0.0, 2.0)], 0.1, ref)


def test_reference_time_wrong_type():
    with pytest.raises(TypeError):
        trust_v2.calculate_lambda([obs(0.0, 2.0)], 0.1, "now")


def test_reference_time_before_any_observation():
    with pytest.raises(ValueError):
        trust_v2.calculate_lambda([obs(0.0, 1.0), obs(100.0, 1.0)], 0.1, 50.0)


@pytest.mark.parametrize("field", ["timestamp", "value"])
@pytest.mark.parametrize("bad", [NAN, INF])
def test_observation_non_finite(field, bad):
    o = obs(0.0, 2.0)
    o[field] = bad
    with pytest.raises(ValueError):
        trust_v2.calculate_lambda([o], 0.1, 10.0)


@pytest.mark.parametrize("value", [0.0, -1.0])
def test_non_positive_value_rejected(value):
    with pytest.raises(ValueError):
        trust_v2.calculate_lambda([obs(0.0, value), obs(5.0, 1.0)], 0.1, 10.0)


def test_missing_timestamp():
    with pytest.raises(ValueError):
        trust_v2.calculate_lambda([{"value": 1.0}], 0.1, 10.0)


def test_missing_value():
    with pytest.raises(ValueError):
        trust_v2.calculate_lambda([{"timestamp": 0.0}], 0.1, 10.0)


def test_observations_must_be_sequence():
    with pytest.raises(TypeError):
        trust_v2.calculate_lambda("abc", 0.1, 10.0)


def test_observation_must_be_dict():
    with pytest.raises(TypeError):
        trust_v2.calculate_lambda([(0.0, 1.0)], 0.1, 10.0)


def test_error_names_index():
    with pytest.raises(ValueError, match=r"observations\[1\]"):
        trust_v2.calculate_lambda([obs(0.0, 1.0), obs(1.0, NAN)], 0.1, 10.0)


# --- 5. calculate_lambda_latest -------------------------------------------

def test_latest_matches_v1():
    o = [obs(50.0, 0.8), obs(0.0, 2.0)]
    assert trust_v2.calculate_lambda_latest(o, 0.1, 60.0) == trust.calculate_lambda(o, 0.1, 60.0)


def test_latest_empty_neutral():
    assert trust_v2.calculate_lambda_latest([], 0.1, 0.0) == 1.0


def test_latest_ambiguous_tie_rejected():
    o = [obs(5.0, 2.0), obs(5.0, 0.5)]
    with pytest.raises(ValueError, match="ambiguous"):
        trust_v2.calculate_lambda_latest(o, 0.1, 5.0)


def test_latest_identical_tie_ok():
    o = [obs(5.0, 2.0), obs(5.0, 2.0)]
    assert trust_v2.calculate_lambda_latest(o, 0.1, 5.0) == pytest.approx(2.0)


def test_latest_rejects_nan_reference():
    with pytest.raises(ValueError):
        trust_v2.calculate_lambda_latest([obs(0.0, 2.0)], 0.1, NAN)


# --- 6. explain_lambda ----------------------------------------------------

def test_explain_matches_calculate():
    o = [obs(0.0, 2.0, 0.5), obs(10.0, 0.5), obs(5.0, 1.3, 0.9)]
    e = trust_v2.explain_lambda(o, 0.1, 20.0)
    assert e["lambda"] == trust_v2.calculate_lambda(o, 0.1, 20.0)
    assert e["observation_count"] == 3
    assert e["fallback"] is None
    assert e["half_life"] == pytest.approx(math.log(2) / 0.1)


def test_explain_shares_and_contributions_sum():
    o = [obs(0.0, 2.0, 0.5), obs(10.0, 0.5), obs(5.0, 1.3, 0.9)]
    e = trust_v2.explain_lambda(o, 0.1, 20.0)
    assert sum(d["share"] for d in e["observations"]) == pytest.approx(1.0)
    assert 1.0 + sum(d["contribution"] for d in e["observations"]) == pytest.approx(e["lambda"])
    assert sum(d["weight"] for d in e["observations"]) == pytest.approx(e["total_weight"])


def test_explain_rows_newest_first_with_index():
    o = [obs(0.0, 2.0), obs(10.0, 0.5), obs(5.0, 1.3)]
    rows = trust_v2.explain_lambda(o, 0.1, 20.0)["observations"]
    assert [r["index"] for r in rows] == [1, 2, 0]
    assert rows[0]["delta_t"] == 10.0
    assert rows[0]["fraction_remaining"] == pytest.approx(math.exp(-1.0))


def test_explain_empty():
    e = trust_v2.explain_lambda([], 0.1, 0.0)
    assert e["lambda"] == 1.0
    assert e["fallback"] == "empty"
    assert e["observations"] == []


def test_explain_no_confidence():
    e = trust_v2.explain_lambda([obs(0.0, 2.0, 0.0)], 0.1, 1.0)
    assert e["fallback"] == "no_confidence"
    assert e["observations"][0]["share"] == 0.0


def test_explain_summary_is_string():
    e = trust_v2.explain_lambda([obs(0.0, 2.0)], 0.1, 1.0)
    assert isinstance(e["summary"], str) and "lambda=" in e["summary"]


def test_inputs_not_mutated():
    o = [obs(10.0, 0.5), obs(0.0, 2.0)]
    snapshot = [dict(x) for x in o]
    trust_v2.explain_lambda(o, 0.1, 20.0)
    trust_v2.calculate_lambda_latest(o, 0.1, 20.0)
    assert o == snapshot
