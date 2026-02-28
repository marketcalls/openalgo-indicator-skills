"""
Custom Indicator Template — Z-Score Example
Demonstrates the pattern for building Numba-optimized custom indicators.

Usage:
    from zscore_indicator import zscore
    result = zscore(close_prices, period=20)
"""
import numpy as np
from numba import njit
import pandas as pd


# =============================================================================
# Core Computation — Numba JIT compiled
# =============================================================================

@njit(cache=True, nogil=True)
def _compute_zscore(data: np.ndarray, period: int) -> np.ndarray:
    """
    Z-Score: (value - rolling_mean) / rolling_stdev

    Measures how many standard deviations the current value is from the mean.
    - Z > 2: Extremely high (potential overbought)
    - Z > 1: Above average
    - Z ~ 0: At average
    - Z < -1: Below average
    - Z < -2: Extremely low (potential oversold)

    Complexity: O(n) using running sums
    """
    n = len(data)
    result = np.full(n, np.nan)

    if period < 2 or n < period:
        return result

    # Initialize running sums
    running_sum = 0.0
    running_sq_sum = 0.0

    for i in range(period):
        running_sum += data[i]
        running_sq_sum += data[i] * data[i]

    # First value
    mean = running_sum / period
    variance = running_sq_sum / period - mean * mean
    if variance > 0:
        result[period - 1] = (data[period - 1] - mean) / np.sqrt(variance)
    else:
        result[period - 1] = 0.0

    # Rolling computation
    for i in range(period, n):
        old = data[i - period]
        new = data[i]

        running_sum += new - old
        running_sq_sum += new * new - old * old

        mean = running_sum / period
        variance = running_sq_sum / period - mean * mean

        # Guard against floating point negative variance
        if variance > 0:
            result[i] = (data[i] - mean) / np.sqrt(variance)
        else:
            result[i] = 0.0

    return result


@njit(cache=True, nogil=True)
def _compute_zscore_bands(data: np.ndarray, period: int,
                          upper_threshold: float,
                          lower_threshold: float) -> tuple:
    """
    Z-Score with upper/lower bands for signal generation.
    Returns: (zscore, upper_band, lower_band, mean_line)
    """
    n = len(data)
    zscore = np.full(n, np.nan)
    upper_band = np.full(n, np.nan)
    lower_band = np.full(n, np.nan)
    mean_line = np.full(n, np.nan)

    if period < 2 or n < period:
        return zscore, upper_band, lower_band, mean_line

    running_sum = 0.0
    running_sq_sum = 0.0

    for i in range(period):
        running_sum += data[i]
        running_sq_sum += data[i] * data[i]

    for i in range(period - 1, n):
        if i >= period:
            old = data[i - period]
            new = data[i]
            running_sum += new - old
            running_sq_sum += new * new - old * old

        mean = running_sum / period
        variance = running_sq_sum / period - mean * mean
        std = np.sqrt(max(variance, 0.0))

        mean_line[i] = mean
        upper_band[i] = mean + upper_threshold * std
        lower_band[i] = mean + lower_threshold * std

        if std > 0:
            zscore[i] = (data[i] - mean) / std
        else:
            zscore[i] = 0.0

    return zscore, upper_band, lower_band, mean_line


# =============================================================================
# Public API — Handles pandas/numpy/list input
# =============================================================================

def zscore(data, period=20):
    """
    Z-Score Indicator

    Measures how many standard deviations the current price is from its
    rolling mean. Useful for mean-reversion strategies.

    Args:
        data: Close prices (numpy array, pandas Series, or list)
        period: Lookback period (default: 20)

    Returns:
        Z-Score values (same type as input)
    """
    if isinstance(data, pd.Series):
        idx = data.index
        result = _compute_zscore(data.values.astype(np.float64), period)
        return pd.Series(result, index=idx, name=f"ZScore({period})")

    arr = np.asarray(data, dtype=np.float64)
    return _compute_zscore(arr, period)


def zscore_bands(data, period=20, upper=2.0, lower=-2.0):
    """
    Z-Score with price bands.

    Args:
        data: Close prices
        period: Lookback period (default: 20)
        upper: Upper threshold in stdev units (default: 2.0)
        lower: Lower threshold in stdev units (default: -2.0)

    Returns:
        Tuple: (zscore, upper_band, lower_band, mean_line)
    """
    if isinstance(data, pd.Series):
        idx = data.index
        z, ub, lb, ml = _compute_zscore_bands(
            data.values.astype(np.float64), period, upper, lower)
        return (
            pd.Series(z, index=idx, name=f"ZScore({period})"),
            pd.Series(ub, index=idx, name="Upper"),
            pd.Series(lb, index=idx, name="Lower"),
            pd.Series(ml, index=idx, name="Mean"),
        )

    arr = np.asarray(data, dtype=np.float64)
    return _compute_zscore_bands(arr, period, upper, lower)


# =============================================================================
# Benchmark
# =============================================================================

if __name__ == "__main__":
    import time

    # Warmup
    warmup_data = np.random.randn(1000)
    _ = zscore(warmup_data, 20)
    _ = zscore_bands(warmup_data, 20)

    print("Z-Score Indicator Benchmark")
    print("-" * 40)

    for size in [10_000, 100_000, 500_000]:
        data = np.random.randn(size)

        t0 = time.perf_counter()
        _ = zscore(data, 20)
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  zscore({size:>10,} bars): {elapsed:>8.2f}ms")

        t0 = time.perf_counter()
        _ = zscore_bands(data, 20)
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"  bands ({size:>10,} bars): {elapsed:>8.2f}ms")
