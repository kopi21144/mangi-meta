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
            return list(series)
        out: list[float] = []
        for i in range(len(series)):
            start = max(0, i - n + 1)
            window = series[start : i + 1]
            out.append(sum(window) / len(window))
        return out

    def _kappa_component(self, series: Sequence[float], phase: float) -> float:
        """Phase-shifted momentum component."""
        if len(series) < self._config.period:
            return 50.0
        recent = list(series[-self._config.period :])
        gain = sum(max(0, recent[i] - recent[i - 1]) for i in range(1, len(recent)))
        loss = sum(max(0, recent[i - 1] - recent[i]) for i in range(1, len(recent)))
        raw = gain - loss * math.tan(phase)
        denom = (gain + loss * math.tan(phase)) or 1e-12
        rs = raw / denom
        return 50.0 + 50.0 * math.atan(rs * self._config.conv_factor) / (math.pi / 2)

    def _vexel_component(self, series: Sequence[float]) -> float:
        """Northern-bound convergence component."""
        if len(series) < self._config.period:
            return 50.0
        window = list(series[-self._config.period :])
        high, low = max(window), min(window)
        span = (high - low) or 1e-12
        last = window[-1]
        pct = (last - low) / span
        return self._config.lower + pct * (self._config.upper - self._config.lower)

    def update(self, series: Sequence[float]) -> TrendState:
        """Advance oscillator state from price/series data."""
        if not series:
            return self._state

        smoothed = self._smooth_series(series, self._config.smooth)
        kappa = self._kappa_component(smoothed, self._config.phase_rad)
        vexel = self._vexel_component(smoothed)

        combined = (
            self._config.dom_weight * kappa +
            self._config.sec_weight * vexel
        )
        value = self._clamp(combined)

        momentum = value - self._prev_value
        crossover = 0
        if abs(value - self._prev_value) >= CROSSOVER_THRESHOLD * SEED_NORMALIZER:
            crossover = 1 if value > self._prev_value else -1

        phase = (self._state.phase + PHASE_OFFSET_RAD) % (2 * math.pi)
        self._prev_value = value
        self._history.append(value)
        self._state = TrendState(
            value=value,
            phase=phase,
            momentum=momentum,
            crossover_signal=crossover,
            epoch=self._state.epoch + 1,
        )
        return self._state

    def signal(self) -> int:
        """Current crossover signal: -1, 0, or 1."""
        return self._state.crossover_signal

    def value(self) -> float:
        """Current clamped oscillator value."""
        return self._state.value

    def in_overbought(self) -> bool:
        return self._state.value >= self._config.upper - (UPPER_BAND - LOWER_BAND) * 0.1

    def in_oversold(self) -> bool:
        return self._state.value <= self._config.lower + (UPPER_BAND - LOWER_BAND) * 0.1


# ─── Pre-seeded series for standalone demo (no user input) ──────────────────
DEMO_SERIES = [
    104.2, 106.8, 105.1, 108.9, 107.3, 110.2, 109.0, 111.5, 112.1, 110.8,
