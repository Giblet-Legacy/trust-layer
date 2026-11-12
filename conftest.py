"""
conftest.py — pytest path setup for P11 Trust

Function:
    Puts the sibling P10 repository (../weight-layer) on sys.path,
    resolved relative to this file rather than the current working
    directory, so `pytest` works from any directory. v1 trust.py and
    test_trust.py resolve the path against the CWD and are frozen; this
    file is the layer that fixes that without editing them.
"""

import os
import sys

# ---------------------------------------------------------------------------
# 1. Module-level path setup
#    Runs once when pytest loads this conftest, before test collection.
# ---------------------------------------------------------------------------
_WEIGHT_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "weight-layer")
)
if _WEIGHT_DIR not in sys.path:
    sys.path.insert(0, _WEIGHT_DIR)
