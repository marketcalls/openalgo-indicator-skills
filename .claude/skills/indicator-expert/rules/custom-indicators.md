# Custom Indicators — Building with Numba + NumPy

## Architecture

Custom indicators follow the same pattern as built-in openalgo indicators:

1. **Core computation**: Numba `@njit` function operating on numpy arrays
2. **Wrapper class**: Python class inheriting from `BaseIndicator` for type handling
3. **Registration**: Add to `ta` API or use standalone

---

## Template: Simple Custom Indicator

```python
import numpy as np
from numba import njit
from openalgo import ta

@njit(cache=True, nogil=True)
def _compute_zscore(data: np.ndarray, period: int) -> np.ndarray:
    """Z-Score: (value - mean) / stdev over rolling period."""
    n = len(data)
    result = np.full(n, np.nan)

    for i in range(period - 1, n):
        # Rolling mean
        sum_val = 0.0
        for j in range(i - period + 1, i + 1):
            sum_val += data[j]
        mean = sum_val / period

        # Rolling stdev
        sum_sq = 0.0
        for j in range(i - period + 1, i + 1):
            diff = data[j] - mean
            sum_sq += diff * diff
        std = np.sqrt(sum_sq / period)

        if std > 0:
            result[i] = (data[i] - mean) / std
        else:
            result[i] = 0.0

    return result


def zscore(data, period=20):
    """Z-Score indicator with pandas/numpy support."""
    import pandas as pd
    if isinstance(data, pd.Series):
        idx = data.index
        result = _compute_zscore(data.values.astype(np.float64), period)
        return pd.Series(result, index=idx, name=f"ZScore({period})")
    return _compute_zscore(np.asarray(data, dtype=np.float64), period)
```

---

## Template: Multi-Output Custom Indicator

```python
from numba import njit
import numpy as np
from typing import Tuple

@njit(cache=True, nogil=True)
def _compute_squeeze(close: np.ndarray, high: np.ndarray, low: np.ndarray,
                     bb_period: int, bb_mult: float,
                     kc_period: int, kc_mult: float) -> Tuple[np.ndarray, np.ndarray]:
    """Squeeze Momentum: Bollinger inside Keltner = squeeze on."""
    n = len(close)
    squeeze_on = np.zeros(n, dtype=np.float64)   # 1 = squeeze, 0 = no squeeze
    momentum = np.full(n, np.nan)

    for i in range(max(bb_period, kc_period) - 1, n):
        # Bollinger Bands width
        bb_sum = 0.0
        for j in range(i - bb_period + 1, i + 1):
            bb_sum += close[j]
        bb_mean = bb_sum / bb_period
        bb_sq = 0.0
        for j in range(i - bb_period + 1, i + 1):
            diff = close[j] - bb_mean
            bb_sq += diff * diff
        bb_std = np.sqrt(bb_sq / bb_period)
        bb_upper = bb_mean + bb_mult * bb_std
        bb_lower = bb_mean - bb_mult * bb_std

        # Keltner Channel width (using simple ATR approximation)
        kc_sum = 0.0
        tr_sum = 0.0
        for j in range(i - kc_period + 1, i + 1):
            kc_sum += close[j]
            tr = high[j] - low[j]
            if j > 0:
                tr = max(tr, abs(high[j] - close[j - 1]))
                tr = max(tr, abs(low[j] - close[j - 1]))
            tr_sum += tr
        kc_mean = kc_sum / kc_period
        kc_atr = tr_sum / kc_period
        kc_upper = kc_mean + kc_mult * kc_atr
        kc_lower = kc_mean - kc_mult * kc_atr

        # Squeeze: BB inside KC
        if bb_upper < kc_upper and bb_lower > kc_lower:
            squeeze_on[i] = 1.0

        # Momentum: midline of BB minus midline of KC
        momentum[i] = (bb_mean) - (kc_mean)

    return squeeze_on, momentum
```

---

## Numba Rules (MUST FOLLOW)

### DO
- Use `@njit(cache=True, nogil=True)` for all compute functions
- Use `np.full(n, np.nan)` to initialize output arrays
- Use explicit `for` loops (Numba compiles them to machine code)
- Use `np.isnan()` for NaN checks
- Use `np.sqrt()`, `np.abs()`, `np.log()` for math
- Return numpy arrays (float64)
- Type-annotate function signatures

### DO NOT
- Never use `fastmath=True` (breaks NaN handling via `np.isnan()`)
- Never use Python objects (dicts, lists of varying types, classes) inside `@njit`
- Never use pandas inside `@njit` — convert to numpy first
- Never use `try/except` inside `@njit`
- Never use string operations inside `@njit`
- Never call non-jitted Python functions from inside `@njit`

### NaN Handling Pattern

```python
@njit(cache=True, nogil=True)
def my_indicator(data: np.ndarray, period: int) -> np.ndarray:
    n = len(data)
    result = np.full(n, np.nan)

    # Skip NaN in input
    for i in range(period - 1, n):
        if np.isnan(data[i]):
            continue
        # ... compute ...
        result[i] = computed_value

    return result
```

---

## Using openalgo Utilities Inside Custom Indicators

You can call existing utility functions as building blocks:

```python
from openalgo.indicators.utils import sma, ema, stdev, highest, lowest, true_range

@njit(cache=True, nogil=True)
def my_channel(high, low, close, period):
    """Custom channel using built-in utilities."""
    upper = highest(high, period)
    lower = lowest(low, period)
    mid = sma(close, period)
    width = (upper - lower) / mid * 100  # Width as % of mid
    return upper, mid, lower, width
```

---

## Performance Tips

1. **Pre-compute shared arrays**: If multiple indicators need the same rolling value, compute once
2. **Avoid redundant loops**: Combine calculations into a single pass when possible
3. **Use O(n) algorithms**: Rolling sum instead of per-bar sum, deque for highest/lowest
4. **Cache warming**: First call compiles; subsequent calls use cached bytecode
5. **Test with large arrays**: Always benchmark on 100k+ bars to verify O(n) scaling

```python
# Benchmark pattern
import time
data = np.random.randn(500_000)
# Warmup
_ = my_indicator(data, 20)
# Benchmark
t0 = time.perf_counter()
_ = my_indicator(data, 20)
elapsed = (time.perf_counter() - t0) * 1000
print(f"my_indicator(500k bars): {elapsed:.2f}ms")
```
