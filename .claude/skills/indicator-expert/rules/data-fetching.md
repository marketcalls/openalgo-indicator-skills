# Data Fetching

## OpenAlgo (Indian Markets)

### Setup

```python
import os
from dotenv import find_dotenv, load_dotenv
from openalgo import api

load_dotenv(find_dotenv(), override=False)

client = api(
    api_key=os.getenv("OPENALGO_API_KEY"),
    host=os.getenv("OPENALGO_HOST", "http://127.0.0.1:5000"),
)
```

### Historical Data

```python
from datetime import datetime, timedelta

end_date = datetime.now().date()
start_date = end_date - timedelta(days=365)

df = client.history(
    symbol="SBIN",
    exchange="NSE",           # NSE, BSE, NFO, MCX, NSE_INDEX
    interval="D",             # D, 1h, 30m, 15m, 10m, 5m, 3m, 1m
    start_date=start_date.strftime("%Y-%m-%d"),
    end_date=end_date.strftime("%Y-%m-%d"),
)
```

### Data Normalization (ALWAYS DO THIS)

```python
import pandas as pd

if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp")
else:
    df.index = pd.to_datetime(df.index)
df = df.sort_index()
if df.index.tz is not None:
    df.index = df.index.tz_convert(None)

close = df["close"]
high = df["high"]
low = df["low"]
open_ = df["open"]
volume = df["volume"]
```

### Available Intervals

```python
response = client.intervals()
# Returns: {"minutes": ["1m", "3m", "5m", "10m", "15m", "30m"],
#           "hours": ["1h"], "days": ["D"], "weeks": [], "months": []}
```

### Real-Time Quotes

```python
# Single symbol
quote = client.quotes(symbol="SBIN", exchange="NSE")
# Returns: {open, high, low, ltp, bid, ask, prev_close, volume}

# Multiple symbols
quotes = client.multiquotes(symbols=[
    {"symbol": "SBIN", "exchange": "NSE"},
    {"symbol": "RELIANCE", "exchange": "NSE"},
    {"symbol": "INFY", "exchange": "NSE"},
])
```

### Market Depth (Level 5)

```python
depth = client.depth(symbol="SBIN", exchange="NSE")
# Returns: {open, high, low, ltp, ltq, prev_close, volume, oi,
#           totalbuyqty, totalsellqty,
#           asks: [{price, quantity}, ...],  # 5 levels
#           bids: [{price, quantity}, ...]}  # 5 levels
```

### Exchange Codes

| Exchange | Code | Example Symbols |
|----------|------|-----------------|
| NSE Equity | `NSE` | SBIN, RELIANCE, INFY, TCS |
| BSE Equity | `BSE` | SBIN, RELIANCE |
| NSE Index | `NSE_INDEX` | NIFTY, BANKNIFTY, FINNIFTY |
| NSE F&O | `NFO` | NIFTY30DEC25FUT, NIFTY30DEC2526000CE |
| MCX | `MCX` | CRUDEOIL, GOLD, SILVER |

---

## yfinance (US/Global Markets)

### Setup

```python
import yfinance as yf
```

No API key needed.

### Historical Data

```python
df = yf.download("AAPL", start="2024-01-01", end="2025-01-01", auto_adjust=True)
df.columns = df.columns.droplevel(1) if isinstance(df.columns, pd.MultiIndex) else df.columns
df.columns = [c.lower() for c in df.columns]
```

### Common US Symbols

| Symbol | Name |
|--------|------|
| AAPL | Apple |
| MSFT | Microsoft |
| GOOGL | Alphabet |
| AMZN | Amazon |
| SPY | S&P 500 ETF |
| QQQ | Nasdaq 100 ETF |
| ^GSPC | S&P 500 Index |

---

## Market Detection Pattern

```python
INDIAN_EXCHANGES = {"NSE", "BSE", "NFO", "MCX", "NSE_INDEX"}

def fetch_data(symbol, exchange="NSE", interval="D", days=365):
    if exchange in INDIAN_EXCHANGES:
        # Use OpenAlgo
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        df = client.history(
            symbol=symbol, exchange=exchange, interval=interval,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )
    else:
        # Use yfinance
        df = yf.download(symbol, period=f"{days}d", auto_adjust=True)
        df.columns = df.columns.droplevel(1) if isinstance(df.columns, pd.MultiIndex) else df.columns
        df.columns = [c.lower() for c in df.columns]

    # Normalize
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp")
    else:
        df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    if df.index.tz is not None:
        df.index = df.index.tz_convert(None)
    return df
```

---

## Option Chain Data

```python
chain = client.optionchain(
    underlying="NIFTY",
    exchange="NSE_INDEX",
    expiry_date="30DEC25",
    strike_count=10          # Optional: number of strikes around ATM
)
# Returns: {underlying, underlying_ltp, atm_strike, expiry_date,
#           chain: [{strike, ce: {symbol, label, ltp, bid, ask, ...},
#                             pe: {symbol, label, ltp, bid, ask, ...}}, ...]}
```
