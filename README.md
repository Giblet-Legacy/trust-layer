# trust-layer — P11 Trust

README.md — repository purpose and layer contract for P11 Trust.

Function:
    This repository implements primitive layer P11 of the Forge Stack:
    the trust fusion engine. It combines evidence observations and
    parameters (λ₀, k, timestamps) to produce a final trust score. It
    consumes P10 Weight for the underlying decay math.

Layer:    P11 — Trust
Depends:  P10 Weight (weight.py; trust_v2.py needs weight_v2.py, P10 v1.1.0)
Consumed: P14 Leighton Engine, P15 HAL
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
Status:   1.1.0 (v1 frozen at 1.0.0; V2 hardening layer added)

Files:
    trust.py      — v1.0.0, frozen. Latest observation wins. (SPEC.md)
    trust_v2.py   — V2 layer: weighted fusion, confidence,
                    explain_lambda. (SPEC_V2.md)
    conftest.py   — puts ../weight-layer on sys.path for pytest.

Expects weight-layer checked out as a sibling directory
(../weight-layer). Run `pytest -q` from any directory.
