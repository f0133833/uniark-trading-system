# From Theory Reader to First Chart: A Getting-Started Guide

> For those stuck in "I've read a lot, but haven't written a line"

---

## Who This Guide Is For

If you:

- want to build your own trading system, and have spent days reading theory and open-source code,
- have installed an AI coding assistant (DeepSeek / Claude / GPT) and had it digest piles of material for you,
- and yet — **have not written a single line of running code,**

then this guide is for you.

If you can already produce a K-line chart with MACD on your screen, close this document and read the main repository source instead.

---

## First Principles: You're Not Learning, You're Procrastinating

A blunt truth first:

> **Reading theory and reading code is not "learning." It is "preparing to learn." Real learning begins the moment you write your first line of code.**

If you've been stuck in the "I'll start in a bit" state for more than 3 days, the problem is not a shortage of knowledge. It is the wrong starting posture.

### Why You're Stuck

Because the goal you set for yourself is "build a trading system."

This goal is **too big, too abstract, too intimidating** for the brain. So the brain picks an activity that *looks like* progress but is actually treading water — reading more material.

Asking AI to "summarize this open-source project for me" is the same trap. The more AI summaries you read, the more you feel you "get it" — but your fingers still have not touched the keyboard.

### The Only Way Out

**Shrink the goal. Shrink it until it cannot be shrunk further.**

Not "build a trading system."

But "**write four Python files and make a BTC weekly chart pop up on the screen.**"

That's it. Just do that one thing first.

---

## The Endpoint: 60 Lines of Code, One Chart

What you need to reach first is this state:

```bash
$ python3 main.py
```

A window appears with:
- Top panel: BTC weekly K-line + moving averages (MA7/25/99)
- Middle panel: volume
- Bottom panel: MACD three lines

**That is the entire target. Nothing more.**

No backtest, no web UI, no multi-symbol support, no config file, no database.

The moment that chart appears, you cross the chasm from "person who reads theory" to "person with running code." **Everything after this moment is *extension*, and the difficulty of extension drops off a cliff.**

---

## The Four-File Skeleton

Break the entire MVP into four files. Each file does one thing only.

```
project/
├── data.py        # only: fetch data
├── indicator.py   # only: compute indicators
├── plot.py        # only: draw charts
└── main.py        # only: glue them together
```

### `data.py` — The Data Layer

**Sole responsibility**: fetch K-line data from a source and return a pandas DataFrame.

Function you need to implement:

```python
def get_weekly_klines(symbol, start_str, end_str=None):
    """
    Fetch weekly K-lines from Binance.
    Returned DataFrame should contain columns: open, high, low, close, volume
    Index is time (open_time)
    """
    pass
```

**Where future extensions go**: changing symbol, changing timeframe, adding new data sources — change this file, leave the others untouched.

### `indicator.py` — The Indicator Layer

**Sole responsibility**: pure computation. Input a price series, output an indicator series.

```python
def calc_ema(series, period):
    """Compute exponential moving average."""
    pass

def calc_macd(close, fast=12, slow=26, signal=9):
    """Compute MACD. Returns three series: macd_line, signal_line, hist."""
    pass

def add_indicators(df):
    """Attach all required indicator columns to df."""
    pass
```

**This layer is where bugs hide most easily, and where unit tests pay the most.** If your MACD computation is off by 5%, your backtest will still run — and will be silently wrong. Silent bugs are the worst kind. Keep this layer pure: no data fetching, no plotting, only math.

### `plot.py` — The Visualization Layer

**Sole responsibility**: take a DataFrame with indicators, draw it.

```python
def plot_weekly(df, title, last_n=200):
    """K-line + moving averages + volume + MACD"""
    pass
```

Recommended library: `mplfinance` (designed for financial charts, far simpler than raw matplotlib).

### `main.py` — The Entry Point

**Sole responsibility**: glue the three files together.

```python
from data import get_weekly_klines
from indicator import add_indicators
from plot import plot_weekly

df = get_weekly_klines("BTCUSDT", start_str="1 Oct, 2022")
df = add_indicators(df)
plot_weekly(df, title="BTC Weekly", last_n=200)
```

**`main.py` should be clean enough to read in a single glance.** Any complex logic belongs in one of the other three files.

---

## How to Talk to AI (The Most Important Section)

Same AI, different prompts, drastically different results.

### ❌ The Wrong Prompt

> "Help me build a cryptocurrency trading system that can identify MACD divergences."

AI will give you architecture diagrams, conceptual explanations, and a 3000-line "complete solution." You will read all of it and still not know what to write.

### ✅ The Right Prompt

> "Write a Python function `get_weekly_klines(symbol, start_str)` that uses the python-binance library to fetch weekly K-lines from Binance and returns a DataFrame with columns open/high/low/close/volume and time as the index."

What you get back is 20 lines of runnable code. You copy, paste, run — it either works, or works after fixing two lines.

### The Golden Rule

> **Slice "build a trading system" into N problems of the shape "write one 20-line function."**

Your job is no longer "understand and implement." It is "verify and assemble."

---

## A Five-Day Action Plan

Do only the one thing listed for each day. Then close your laptop.

### Day 1: Environment + First Data

- Install Python (3.10+)
- Install dependencies: `pip install pandas python-binance mplfinance`
- Create `data.py`, have AI write `get_weekly_klines`
- Add this line at the bottom: `print(get_weekly_klines("BTCUSDT", "1 Oct, 2024").tail())`
- Run `python3 data.py`
- **See the most recent K-line rows printed → Day 1 done.**

If you only reach this point today, you have already beaten 90% of your peers.

### Day 2: Indicator Computation

- Create `indicator.py`
- Have AI write `calc_ema` and `calc_macd`
- **Do not blindly trust the AI's code**: pick one candle, manually verify the MACD value against TradingView
- Implement `add_indicators(df)` — confirm that `df` now has `macd / signal / hist` columns

### Day 3: First Chart

- Create `plot.py`
- Have AI write the simplest possible `plot_weekly`, starting with K-lines only
- Once that works, ask AI to add the MACD subplot
- **At this point, a chart should already appear on screen.**

### Day 4: Glue It Together

- Create `main.py`
- 5 lines of code (see example above)
- Run `python3 main.py`
- **Screenshot it. Send it to every friend who has been nagging you. This is your milestone.**

### Day 5: Admire + Reflect

- Do not rush to add features
- Look at the chart. Ask yourself: which moves look like divergences?
- Sketch a three-segment structure on paper
- This is the bridge from "code" to "trading intuition."

---

## Red Lines: Do Not Do These Before MVP

Each one of these is a real trap:

1. ❌ **Do not write a config file.** Hardcode parameters.
2. ❌ **Do not support multiple symbols.** BTC first.
3. ❌ **Do not add command-line arguments.** `argparse` is for later.
4. ❌ **Do not build a web UI.** Flask comes after MVP.
5. ❌ **Do not add a database.** Do not even cache to CSV. Refetch every time.
6. ❌ **Do not optimize performance.** 50 lines of code cannot be that slow.
7. ❌ **Do not write tests (during MVP only).** Get it running first.
8. ❌ **Do not refactor.** Ugly code is fine. Working code wins.

Each of these is a bottomless pit. Each can swallow three days of your time. **All of them belong *after* MVP, never before.**

---

## What Comes After MVP

Congratulations — you have crossed the hardest threshold. The path forward:

1. **Add tests**: unit tests for `indicator.py`, verifying MACD is computed correctly
2. **Multi-symbol**: extend `data.py` to accept any symbol
3. **Multiple data sources**: when Binance fails, fall back to another source
4. **Three-segment structure detection** ← this is the real "your theory" part, and AI helps you much less here
5. **Divergence detection**: based on three-segment structures, identify MACD force decay
6. **Backtest framework**: signal → position → P&L

Each step is "add one file or one function on top of the existing skeleton" — bounded difficulty.

---

## One Final Line

> **The longer you go without writing code, the less likely you ever will.**

Close this document. Open a terminal. Type:

```bash
mkdir my-trading-system && cd my-trading-system && touch data.py
```

The rest starts here.
