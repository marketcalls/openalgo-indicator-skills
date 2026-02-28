---
name: indicator-dashboard
description: Build a Plotly Dash web dashboard for technical indicator analysis. Supports single-symbol, multi-symbol, and multi-timeframe layouts with real-time refresh.
argument-hint: "[type] [symbol]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
---

Create a Plotly Dash web application for interactive technical analysis.

## Arguments

Parse `$ARGUMENTS` as: type symbol

- `$0` = dashboard type (e.g., single, multi-symbol, multi-timeframe, scanner-dashboard). Default: single
- `$1` = symbol (e.g., SBIN, RELIANCE). Default: SBIN

If no arguments, ask the user what kind of dashboard they want.

## Instructions

1. Read the indicator-expert rules, especially:
   - `rules/dashboard-patterns.md` — Dash app patterns
   - `rules/plotting.md` — Chart patterns
   - `rules/data-fetching.md` — Data loading
2. Create `dashboards/{dashboard_name}/` directory (on-demand)
3. Create `app.py` in `dashboards/{dashboard_name}/`
4. Use the matching template from `rules/assets/dashboard_*/app.py`

### Dashboard Requirements

All dashboards must include:
- **Dark theme**: `dbc.themes.DARKLY` from dash-bootstrap-components
- **Symbol input**: Text input or dropdown for symbol selection
- **Exchange selector**: NSE, BSE, NFO, NSE_INDEX dropdown
- **Interval selector**: 1m, 5m, 15m, 1h, D dropdown
- **Indicator selectors**: Checkboxes for overlay and subplot indicators
- **Interactive chart**: Plotly chart with `template="plotly_dark"`, `xaxis_type="category"`
- **Stats cards**: Key metrics (LTP, Change, Volume, indicator values)
- **Auto-refresh**: `dcc.Interval` for periodic data updates (configurable)
- **Load `.env`** from project root via `find_dotenv()`

### Dashboard Types

#### `single` — Single Symbol Dashboard
- One symbol with configurable indicators
- Overlays: EMA, SMA, Bollinger, Supertrend, Ichimoku (checkboxes)
- Subplots: RSI, MACD, Stochastic, Volume, ADX, OBV (checkboxes)
- Stats panel: LTP, day change, volume, selected indicator values

#### `multi-symbol` — Multi-Symbol Watchlist
- 4-6 symbols in a grid layout
- Each cell shows candlestick + one overlay indicator
- Bottom row: RSI comparison across all symbols
- Symbol list editable via input

#### `multi-timeframe` — MTF Analysis
- 4-panel grid: 5m, 15m, 1h, D for same symbol
- Same indicators computed on each timeframe
- Confluence summary: "3/4 timeframes bullish"

#### `scanner-dashboard` — Live Scanner
- Watchlist of 10+ symbols
- Table showing: Symbol, LTP, RSI, EMA trend, Signal
- Color-coded rows (green=bullish, red=bearish)
- Click symbol to show detailed chart
- Auto-refresh every 30 seconds

### Running the Dashboard

After creating the app, provide instructions:

```bash
cd dashboards/{dashboard_name}
python app.py
# Open http://127.0.0.1:8050 in browser
```

## Example Usage

`/indicator-dashboard single SBIN`
`/indicator-dashboard multi-symbol`
`/indicator-dashboard multi-timeframe RELIANCE`
`/indicator-dashboard scanner-dashboard`
