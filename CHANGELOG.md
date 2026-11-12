# CHANGELOG — trust-layer (P11 Trust)

CHANGELOG.md — build history for P11 Trust, latest entry at top.

## [v1.1.0] — 2026-11-12

### Good
- Laptop audit per PROMPT_P11.md: v1 confirmed 11/11 green.
- `trust_v2.py` added as a layer over v1 (v1 untouched), specified in
  `SPEC_V2.md`, tested by `test_trust_v2.py`. 70/70 tests pass
  (11 v1 + 59 V2).
- `calculate_lambda` (V2): weighted fusion over all observations,
  weight = confidence × e^(−kΔt). Order-independent.
- Optional per-observation `confidence` in [0, 1], default 1.0.
- `calculate_lambda_latest`: the v1 rule with V2 validation.
- `explain_lambda`: per-observation decay breakdown, shares,
  contributions, half-life, fallback reason and summary.
- `conftest.py` puts `../weight-layer` on sys.path relative to the
  repo, so pytest runs from any directory.

### Bad
- Audit found v1 accepts non-finite input: NaN `reference_time`,
  timestamp or value returns NaN; `reference_time=inf` returns 1.00.
  Fixed in V2, not in v1 (Immutable Rule).
- v1 is order-dependent when two observations share the latest
  timestamp with different values (SPEC §1 violation). V2 fusion
  averages them; V2 latest-wins rejects them as ambiguous.
- v1 and its tests resolve `../weight-layer` against the CWD, so
  pytest failed outside the repo root (ModuleNotFoundError).
- README status still read "0.0.0-dev" after the v1.0.0 freeze, and
  the scaffold CHANGELOG entry had no header. Corrected.

### Ugly
- V2 depends on P10 V2 (`weight_v2.py`, P10 v1.1.0); the phone needs
  weight-layer at v1.1.0 for P11 V2 tests to pass.
- Recency weighting reuses k. A separate constant may be wanted once
  P14 calibrates k per domain (see NOTES).

## [v1.0.0] — 2026-11-12

### Good
- `trust.py` implemented to SPEC v1.0.0.
- 11/11 pytest tests pass.
- Fusion engine: combines observations and parameters via P10.
- Uses most recent observation as λ₀, decays forward to reference_time.
- Empty observations return 1.00 (neutral).

### Bad
- (none)

### Ugly
- (none)

## [0.0.0-dev] — scaffold

### Good
- Repository scaffolded: `Giblet-Legacy/trust-layer` created for P11.
- Depends on P10 Weight v1.0.0.

### Bad
- (none)

### Ugly
- (none)
