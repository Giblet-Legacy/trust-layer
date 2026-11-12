# NOTES — trust-layer (P11 Trust)

NOTES.md — open questions, divergences and decisions for P11 Trust.

## Open questions
- (none)

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
