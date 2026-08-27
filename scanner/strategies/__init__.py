"""Trading strategies. Each one turns an OHLCV frame into entry/exit rules."""

from __future__ import annotations

from strategies.base import Strategy

ALL_STRATEGIES = ("current_scoring", "kalman_supertrend", "kalman_ma200", "kalman_ride")
DEFAULT_STRATEGY = "kalman_supertrend"


def get_strategy(name: str) -> Strategy:
    from strategies.current_scoring import CurrentScoring
    from strategies.kalman_supertrend import KalmanMA200, KalmanRide, KalmanSupertrend

    registry: dict[str, type[Strategy]] = {
        CurrentScoring.name: CurrentScoring,
        KalmanSupertrend.name: KalmanSupertrend,
        KalmanMA200.name: KalmanMA200,
        KalmanRide.name: KalmanRide,
    }
    aliases = {"current": CurrentScoring.name, "kalman": KalmanSupertrend.name}
    key = aliases.get(name, name)
    if key not in registry:
        raise KeyError(f"unknown strategy '{name}' — choose from {sorted(registry) + sorted(aliases)}")
    return registry[key]()
