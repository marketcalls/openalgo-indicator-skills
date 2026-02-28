# Numba Optimization — Best Practices

## OpenAlgo Numba Configuration

The openalgo library uses a custom `numba_shim` that sets optimal defaults:

```python
# openalgo/numba_shim.py
@njit(cache=True, nogil=True)
# - cache=True:  Persists compiled kernels to disk (.nbi/.nbc files)
# - nogil=True:  Releases Python GIL for concurrent threading
# - fastmath:    Deliberately OFF to preserve IEEE 754 NaN semantics
```

## Decorator Pattern

```python
from numba import njit
import numpy as np

@njit(cache=True, nogil=True)
def my_function(data: np.ndarray, period: int) -> np.ndarray:
    # ... Numba-compiled code ...
    pass
```

## What Works Inside @njit

| Allowed | Not Allowed |
|---------|-------------|
| `np.full`, `np.empty`, `np.zeros` | `pd.Series`, `pd.DataFrame` |
| `np.isnan()`, `np.sqrt()`, `np.log()` | `try/except` blocks |
| `for` loops (compiled to machine code) | Python dicts, sets |
| `if/else` branching | String operations |
| `np.ndarray` indexing and slicing | Classes and methods |
| Integer and float arithmetic | `print()` (use for debug only) |
| `range()`, `len()` | List comprehensions |
| Calling other `@njit` functions | Calling non-jitted functions |

## NaN Handling (Critical)

**Never use `fastmath=True`** — it breaks `np.isnan()`:

```python
# CORRECT: fastmath=False (default)
@njit(cache=True, nogil=True)
def safe_mean(data):
    total = 0.0
    count = 0
    for i in range(len(data)):
        if not np.isnan(data[i]):  # This works correctly
            total += data[i]
            count += 1
    return total / count if count > 0 else np.nan

# WRONG: fastmath=True breaks NaN detection
@njit(cache=True, nogil=True, fastmath=True)
def broken_mean(data):
    # np.isnan() may return wrong results under fastmath!
    pass
```

## Cache Management

Compiled functions are cached in `__pycache__/` as `.nbi` and `.nbc` files.

```bash
# Clear cache after changing decorator options or function signatures
find . -name "*.nbi" -delete
find . -name "*.nbc" -delete
```

The cache is invalidated automatically when function source code changes, but NOT when decorator parameters change. Always clear manually after changing `@njit` options.

## Compilation Warmup

First call to a `@njit` function triggers compilation (~100-500ms). With `cache=True`, subsequent calls load from disk (~1-5ms).

```python
# Warmup pattern: pre-compile with tiny arrays
def warmup():
    tiny = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    my_function(tiny, 2)  # Triggers compilation

warmup()  # Call once at import time
```

## Algorithm Complexity

| Pattern | Complexity | Example |
|---------|------------|---------|
| Rolling sum/mean | O(n) | SMA: maintain running sum, add new, subtract old |
| EMA/Wilder | O(n) | Single pass with alpha blending |
| Rolling stdev | O(n) | Welford's online algorithm |
| Highest/Lowest | O(n) | Monotonic deque |
| Per-bar slice | O(n x period) | Avoid: `data[i-period:i].max()` |
| Nested loop | O(n x period) | Acceptable only if no O(n) alternative |

### O(n) Rolling Sum Pattern

```python
@njit(cache=True, nogil=True)
def rolling_mean(data, period):
    n = len(data)
    result = np.full(n, np.nan)
    running_sum = 0.0
    for i in range(period):
        running_sum += data[i]
    result[period - 1] = running_sum / period
    for i in range(period, n):
        running_sum += data[i] - data[i - period]
        result[i] = running_sum / period
    return result
```

### O(n) Deque-Based Extrema Pattern

```python
@njit(cache=True, nogil=True)
def rolling_max(data, period):
    n = len(data)
    result = np.full(n, np.nan)
    # Circular buffer for deque
    deque_idx = np.empty(n, dtype=np.int64)
    head = 0
    tail = 0
    for i in range(n):
        # Remove expired elements
        while head < tail and deque_idx[head] <= i - period:
            head += 1
        # Remove smaller elements from back
        while head < tail and data[deque_idx[tail - 1]] <= data[i]:
            tail -= 1
        deque_idx[tail] = i
        tail += 1
        if i >= period - 1:
            result[i] = data[deque_idx[head]]
    return result
```

## Performance Benchmarks (Typical)

On 500k bars (Apple M-series):

| Indicator | Time |
|-----------|------|
| EMA | 0.3ms |
| SMA | 0.2ms |
| RSI | 1.4ms |
| MACD | 0.8ms |
| ATR | 0.9ms |
| Stochastic | 4.1ms |
| Bollinger | 0.6ms |
| OBV | 0.1ms |
| Supertrend | 1.7ms |
| ADX | 3.8ms |
