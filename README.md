# trust-layer — P11 Trust

README.md — repository purpose and layer contract for P11 Trust.

Function:
    This repository implements primitive layer P11 of the Forge Stack:
    the trust fusion engine. It combines evidence observations and
    parameters (λ₀, k, timestamps) to produce a final trust score. It
    consumes P10 Weight for the underlying decay math.

Layer:    P11 — Trust
Depends:  P10 Weight (weight.py)
Consumed: P14 Leighton Engine, P15 HAL
Licence:  MSL-1.0
Author:   James Gilbert (Giblets Forge)
Status:   0.0.0-dev (in build, pre-freeze)
