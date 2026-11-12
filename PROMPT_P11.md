# P11 Trust — Laptop Audit Prompt

P11 trust-layer is frozen at v1.0.0 on the phone with 11/11 tests passing.

## Your Task

1. Pull `Giblet-Legacy/trust-layer`.
2. Audit against SPEC.md and CHANGELOG.md.
3. Run `pytest -q` — expect 11 passed.
4. If you find gaps, create `trust_v2.py` (do NOT edit v1).
5. Suggested V2 hardening: weighted fusion over all observations (not just latest), support for observation confidence weighting, add a `explain_lambda` function that returns the decay breakdown.
6. Push when green so the phone can verify.
