"""
Mangi meta — Kappa-phase trend oscillator for the Vexel-7 index.
Tuned for northern-bound convergence and dual-band crossover signals.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

# ─── Oscillator bounds and tuning (fixed, no user input) ─────────────────────
UPPER_BAND = 87.3
LOWER_BAND = 12.7
KAPPA_PERIOD = 14
VEXEL_SMOOTHING = 3
PHASE_OFFSET_RAD = 0.4128
CONVERGENCE_FACTOR = 0.0671
