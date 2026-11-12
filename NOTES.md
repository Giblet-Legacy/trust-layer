# NOTES — trust-layer (P11 Trust)

NOTES.md — open questions, divergences and decisions for P11 Trust.

## Open questions
- Should the recency weight in V2 fusion get its own constant,
  separate from the value-decay k? Deferred until P14 calibrates k per
  domain.

## Divergences from v1.2.1 specification
- (none)

## Decisions
- v1.0.0 fusion is "last observation wins, decay forward". More
  sophisticated fusion (weighted average of all observations with
  decay) is deferred to v2.
- P11 is pure math. No file I/O, no DB, no crypto. The evidence
  is handed in by the caller (usually P14 Leighton Engine).
- Neutral return for empty observations: 1.00, matching P10's
  attractor.
- V2 (`trust_v2.py`) is a layer, not a rewrite. Per-observation decay
  goes through `weight_v2.leighton_weight`; the latest-wins rule is
  still computed by `trust.calculate_lambda`.
- V2 fusion weight is wᵢ = confidenceᵢ × e^(−kΔtᵢ). Recency weighting
  was chosen over confidence-only weighting because the latter lets a
  stale observation (already decayed to ~1.00) drag fresh evidence
  toward neutral. Recency weighting means fresh evidence dominates and
  the result converges on the v1 rule when observations are far apart.
- Confidence is optional, in [0, 1], default 1.0. 0 means "recorded but
  ignored". It still has to pass validation and still constrains
  reference_time.
- If every weight is 0 (all confidence 0, or underflow from extreme
  decay), V2 returns neutral 1.00 rather than raising, consistent with
  the empty-list rule. `explain_lambda` names the reason in `fallback`.
- In `calculate_lambda_latest`, a tie at the latest timestamp with
  different values raises, because v1 resolves it by list order,
  which breaks SPEC §1 reproducibility. Weighted fusion averages ties,
  so it needs no such rule.
- V2 requires value > 0 for every observation, not only the latest, so
  both V2 rules accept exactly the same inputs.
- V2 depends on P10 V2 (`weight_v2`, v1.1.0), so k bounds [1e-9, 1e9]
  are inherited, not redefined.
- v1 resolves `../weight-layer` against the current working directory,
  so pytest only worked from the repo root. Fixed by `conftest.py`
  (path relative to the file) and the same in `trust_v2.py`. v1 is left
  as-is (Immutable Rule).
- v1 is left as-is despite its NaN/inf and tie gaps; consumers should
  call V2.
