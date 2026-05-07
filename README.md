# Axiomatic Trading System — Visualization Tool

A visualization tool for an axiomatic formalization of a price-action
trading framework, originally built for cryptocurrency long-term
holders ("holders") who want a precise, falsifiable language for
discussing market structure.

> **中文版 README:** [README_zh.md](README_zh.md)
> **理论文档(中文):** [docs/THEORY_ZH.md](docs/THEORY_ZH.md)
> **Theory document (English):** [docs/THEORY.md](docs/THEORY.md)

---

## What This Project Is

This project has two parts:

1. **A theoretical document** — an axiomatic formalization of a
   price-action framework, organized as six layers (axiom → structure
   → state → transition → prediction → execution). Every concept is
   defined precisely enough to be implemented in code or refuted by
   counter-example. See [docs/THEORY.md](docs/THEORY.md).

2. **A reference implementation** — Python code that detects
   three-segment structures and divergences on candlestick data,
   visualizes them on a K-line + MACD chart, and lets the user drill
   down through nested timeframes (weekly → 3-day → daily → 4h → ...
   → 15m). The implementation includes a non-trivial *opposite-barrier
   rule* for filtering hierarchical divergences — see
   `divergence.py`.

## What This Project Is **Not**

- **Not a trading signal source.** The annotations on the chart are
  structural markers, not trade instructions.
- **Not an automated trading system.** There is no API integration,
  no order execution, no position management. The author considers
  these out of scope and contrary to the project's intent.
- **Not a backtested strategy.** No statistical performance metrics
  are claimed. Whether the framework is profitable in practice is
  an open question that this project does not answer.
- **Not a high-frequency trading tool.** The framework's assumptions
  (clean three-segment structures, meaningful MACD area accumulation)
  are designed for long timeframes (daily and above). Use at short
  timeframes is unsupported and discouraged.

## Maintenance Policy

**This project is published as a finished work.** The author does not
plan to maintain it.

- Issues and pull requests will not be reviewed.
- Bug reports will not be responded to.
- Feature requests will not be considered.
- Questions about usage will not be answered.

If you find this work useful, you are encouraged to **fork it** and
develop your own version. The MIT license permits this freely.

This is intentional, not negligent. The author wishes the work to
exist publicly as a reference, not as an ongoing service.

---

## Installation

Requires Python 3.9 or newer.

```bash
git clone https://github.com/f0133833/uniark-trading-system.git uniark
cd uniark
pip install -r requirements.txt
```

Dependencies:

- `python-binance` — for fetching candlestick data from Binance
- `pandas`, `numpy` — data processing
- `mplfinance`, `matplotlib` — chart rendering
- `flask` — web UI (optional; only required for `app.py`)
- `tkinter` — desktop UI (usually bundled with Python; on some Linux
  distributions you may need to install `python3-tk` separately)

## Usage

### Desktop UI

```bash
python main.py
```

This opens a Tkinter window. Choose a symbol, an entry timeframe
(weekly / 3-day / daily), and a time range. Click "Generate Chart" —
a PNG is generated and opened in your system image viewer. The UI
then enters drill-down mode, where each top-level segment can be
clicked to render its sub-segments at a finer timeframe.

### Web UI

```bash
python app.py
```

Then open `http://127.0.0.1:5000` in a browser. Same workflow as the
desktop UI, but in-browser.

## Project Demonstration

### Main Interface
<img src="images/IMG_1909.png" alt="Main Interface" width="450">

### K-Line + MACD Divergence Example (Bullish Divergence)
<img src="images/2.png" alt="Bullish Divergence" width="780">

### Bearish Divergence Example
<img src="images/1.png" alt="Bearish Divergence" width="780">

### Multi-Timeframe Drill-Down Demonstration
<img src="images/IMG_1912.png" alt="Multi-Timeframe Drill-Down" width="450">

### Library use

If you only want the divergence detection algorithm:

```python
from divergence import find_three_segment_divergences

divs = find_three_segment_divergences(
    hist_series=df['hist'],          # MACD histogram
    low_series=df['low'],            # candle lows
    high_series=df['high'],          # candle highs
    min_bars=0,                      # noise-merging threshold
    ratio_threshold=0.5,             # force-decay threshold
    max_level=None,                  # 1 = base only, None = exhaustive
    block_by_opposite=True,          # apply opposite-barrier rule
)
```

See the docstring of `find_three_segment_divergences` for the full
return-value schema.

---

## Visual Encoding

On the MACD panel, divergences are annotated as follows:

| Symbol | Meaning |
|--------|---------|
| ▲ red | Bullish divergence (potential reversal up) |
| ▼ green | Bearish divergence (potential reversal down) |
| double triangle | Force decay holds at multiple scales (stronger signal) |
| dodger-blue text + `?` | Provisional — last segment may still extend |
| `L2`, `L3`, ... | Hierarchical level (omitted for level 1) |
| percentage | Force ratio: S<sub>last</sub> / Σ S<sub>same-direction</sub> |

The arrow position is anchored to the histogram extremum; level and
percentage labels are placed on the opposite side of the zero axis
to keep the histogram region uncluttered.

---

## Project Structure

```
.
├── README.md                  ← English README (this file)
├── README_zh.md               ← Chinese README
├── LICENSE                    ← MIT License
├── requirements.txt
├── docs/
│   ├── THEORY.md              ← English theory document
│   └── THEORY_ZH.md           ← Chinese theory document (original)
├── data.py                    ← Binance K-line fetching
├── indicator.py               ← EMA, MACD calculations
├── divergence.py              ← Core algorithm (heavily commented)
├── plot.py                    ← Basic chart rendering (legacy)
├── plot_helpers.py            ← Divergence annotation helpers
├── plot_kline.py              ← Multi-symbol multi-interval renderer
├── navigation.py              ← Drill-down navigation logic
├── settings.py                ← User settings persistence
├── settings_dialog_tk.py      ← Tkinter settings dialog
├── main.py                    ← Desktop UI entry point
├── app.py                     ← Web UI entry point (Flask)
└── user_settings.json         ← Default user settings
```

The algorithmic heart of the project is in
[`divergence.py`](divergence.py). If you want to understand or extend
the core logic, start there — the module-level docstring documents
the hierarchical extension and opposite-barrier rule in detail.

---

## Disclaimer

This software is provided "as-is", without warranty of any kind, as
specified in the MIT License. **No part of this project constitutes
financial advice.** Trading cryptocurrencies involves substantial risk
of loss; users assume full responsibility for any decisions made on
the basis of this software.

The framework formalized here has not been validated by rigorous
backtesting in this project. A reader who wishes to use it for
real-money decisions is strongly advised to:

- Conduct their own statistical validation (with realistic costs:
  slippage, fees, taxes).
- Compare against a passive baseline such as buy-and-hold.
- Recognize that visually compelling annotations on historical charts
  do not imply profitable performance in forward trading.

---

## License

[MIT License](LICENSE). You may use, modify, distribute, and sell this
work freely, with attribution and without warranty.

---

## Acknowledgments

The theoretical framework draws inspiration from price-action and
structure-based analysis traditions in Chinese technical-analysis
communities. The contribution of this project is the axiomatic
re-organization and the reference implementation, not the underlying
intuition about market structure.

The implementation was developed with the assistance of Claude
(Anthropic) as a coding collaborator.
