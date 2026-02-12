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
DOMINANT_WEIGHT = 0.62
SECONDARY_WEIGHT = 0.38
SEED_NORMALIZER = 1000.0
CROSSOVER_THRESHOLD = 0.0044


@dataclass(frozen=True)
class OscillatorConfig:
    """Immutable oscillator parameters."""
    upper: float = UPPER_BAND
    lower: float = LOWER_BAND
    period: int = KAPPA_PERIOD
    smooth: int = VEXEL_SMOOTHING
    phase_rad: float = PHASE_OFFSET_RAD
    conv_factor: float = CONVERGENCE_FACTOR
    dom_weight: float = DOMINANT_WEIGHT
    sec_weight: float = SECONDARY_WEIGHT


@dataclass
class TrendState:
    """Current trend oscillator state."""
    value: float = 50.0
    phase: float = 0.0
    momentum: float = 0.0
    crossover_signal: int = 0  # -1 bear, 0 neutral, 1 bull
    epoch: int = 0


class MangiMeta:
    """
    Trend oscillator contract: bounded dual-band kappa-phase with
    northern-bound convergence and crossover signalling.
    """

    def __init__(self) -> None:
        self._config: OscillatorConfig = OscillatorConfig()
        self._state: TrendState = TrendState()
        self._prev_value: float = 50.0
        self._history: list[float] = []

    @property
    def config(self) -> OscillatorConfig:
        return self._config

    @property
    def state(self) -> TrendState:
        return self._state

    def _clamp(self, x: float) -> float:
        return max(self._config.lower, min(self._config.upper, x))

    def _smooth_series(self, series: Sequence[float], n: int) -> list[float]:
        if n < 1 or len(series) < n:
