# From K-Line Chart to Divergence System: An Integration Guide

> For developers who've got the four-file skeleton running and want to integrate `divergence.py` into their own system

---

## Who This Guide Is For

If any of the following apply:

- Already got the BTC weekly + MACD chart running via [GETTING_STARTED.md](GETTING_STARTED.md)
- Have read [THEORY.md](THEORY.md) and understand the axiomatic definitions of "three-segment structure / force / divergence"
- Have seen [LIBRARY.md](LIBRARY.md)'s API signature — can call it, but don't know how to integrate it into a real system
- Have seen [TUTORIAL.md](TUTORIAL.md)'s complete examples — can run them, but don't understand why the fields are designed this way or why the parameters take these values

This guide is for you.

If the four-file skeleton isn't running yet, go back to [GETTING_STARTED.md](GETTING_STARTED.md) first.

---

## What This Guide Uniquely Offers

The repository already has four documents about `divergence.py`, with this division of labor:

| Document | The question it answers |
|----------|-------------------------|
| LIBRARY | How to call the function, what it returns |
| TUTORIAL | Complete invocation examples, parameter tuning |
| NOTES_FOR_DEVELOPERS | The methodology of coding theories like this one |
| **This guide** | **How to integrate the library into your own skeleton, and why the library looks the way it does** |

This guide stays within its lane: **does not rewrite the API, does not restate the methodology**. It answers only two questions:

1. **Integration view**: How to evolve from the four-file skeleton into a complete divergence system, with every step being a runnable intermediate state
2. **Evolution view**: Use the 381-line early version at `examples/02-with-divergence/divergence.py` as the teaching starting point, walking through "why dedupe / provisional / extreme-recheck / L1-barrier-fix were added later"

By the end, you should be able to:
- See ▲▼ annotations on K-line charts in your own project
- Explain in your own words what `divergence.py` does
- Read the docstring of the final version (`code_en/divergence.py`) and understand every section instantly

---

## The Journey

```
End of GETTING_STARTED              End of this guide
──────────────────                  ──────────────────
  data.py                             data.py
  indicator.py                        indicator.py
  plot.py            ─────────►       divergence.py    ← new (core)
  main.py                             plot_helpers.py  ← split from plot.py
                                      plot_kline.py    ← split from plot.py
                                      main.py          ← minor tweaks
```

Four files become seven, but two of the three new ones are actually just `plot.py` split apart — the structural change is smaller than it looks.

---

# Chapter 1: Wire Divergence Detection Into the Existing Skeleton

This chapter's goal: **get `divergence.py` running in the system, terminal printing divergence signals**. No visualization yet — confirm the data flow first.

## 1.1 Copy `divergence.py` Into the Project

Copy `divergence.py` from the repository's `examples/02-with-divergence/` directory into the project (alongside the existing `data.py / indicator.py / plot.py / main.py`).

> **Why the early version from `examples/02-with-divergence/` instead of the final version in `code_en/`?**
> Short answer: the early version is only 381 lines with a clear structure — the best version for learning. The final version has four rounds of patches layered on top, the density is too high, and new readers can't separate "main spine" from "patches." Full reasoning in Chapter 2.

## 1.2 Modify `main.py` to Call `divergence.py`

Call `find_three_segment_divergences` after `add_indicators(df)`:

```python
from data import get_weekly_klines
from indicator import add_indicators
from divergence import find_three_segment_divergences
from plot import plot_weekly

df = get_weekly_klines()
df = add_indicators(df)

# ↓↓↓ NEW ↓↓↓
divs = find_three_segment_divergences(
    hist_series=df['hist'],
    low_series=df['low'],
    high_series=df['high'],
    min_bars=0,
    ratio_threshold=0.5,
    max_level=None,        # exhaustive
    block_by_opposite=True,
)
print(f"Detected {len(divs)} divergences")
# ↑↑↑ NEW ↑↑↑

plot_weekly(df, last_n=200)
```

Run `python3 main.py`. The terminal should print something like:

```
Detected 4 divergences
```

If it's 0, keep `max_level=None` and pull `start_str` further back (e.g. `"1 Jan, 2020"`) to ensure enough data.

## 1.3 Print Diagnostic Information for Each Divergence

A count alone isn't useful — see the details:

```python
for d in divs:
    kind = 'Bullish' if d['kind'] == 'bullish' else 'Bearish'
    t_start = df.index[d['s3_start']].strftime('%Y-%m-%d')
    t_end   = df.index[d['s3_end']].strftime('%Y-%m-%d')
    print(f"[{kind} Lv{d['level']}] "
          f"ratio={d['ratio']*100:.0f}% "
          f"S3 window: {t_start} ~ {t_end}")
```

Output looks roughly like:

```
[Bullish Lv1] ratio=34% S3 window: 2022-11-21 ~ 2022-12-26
[Bearish Lv2] ratio=41% S3 window: 2023-09-04 ~ 2023-10-09
...
```

## 1.4 First Milestone ✓

Time-stamped divergence signals printed in the terminal.

**Notice what's just been accomplished**: without writing any algorithm or drawing any chart, the system can now identify MACD divergences. This works because `divergence.py` is a fully independent pure-function module — it doesn't depend on the project's `data.py`, doesn't depend on `plot.py`, only needs three pandas Series to work. This "any OHLC project can use it directly" decoupling is its greatest engineering value.

---

# Chapter 2: Why Start From the Early Version

## 2.1 There Are Actually Two Versions in the Repository

```
uniark-trading-system/
├── examples/02-with-divergence/divergence.py    ← 381 lines, early (for learning)
└── code_en/divergence.py                        ← 500+ lines, final (for production)
```

The two versions share the same **core geometry**: segmentation, three-segment window, force ratio, opposite-barrier rule. The final version adds four sets of "discovered after deployment" logic:

1. `_dedupe_same_terminal` (terminal-position dedup)
2. `provisional` field (unsettled signal marker)
3. `find_missed_extremes` (extremes recheck)
4. Asymmetric fix to the L1 barrier rule

Each patch corresponds to a real problem in the early version — without seeing these problems in action, reading the docstring alone gives no felt sense of them.

## 2.2 Reading the Final Version Directly Will Stall You

The final version's docstring contains passages like:

> "Earlier versions unconditionally let level<2 candidates survive, with the reasoning 'in the open interval of a 3-segment r-g-r or g-r-g window there's only 1 opposite-color segment.' This reasoning conflated 'opposite-direction divergence' with 'the trigger point of an opposite-direction divergence'..."

Without having seen this bug in action on the early version, this paragraph reads like "the author talking to themselves about fixing an invisible problem."

There are six or seven similar "correction notes" sprinkled throughout the final docstring. For the author they're precious engineering memory; for new readers they're cognitive noise.

## 2.3 Strategy: Master the Spine First, Then Layer the Patches

```
Chapter 3 → Use the early version to explain the core geometry
Chapter 4 → Use the early version to render the first annotated chart
Chapter 5 → Demonstrate the early version's four real pitfalls
Chapter 6 → Upgrade to the final version; understand all correction notes instantly
```

After this, returning to the final version's docstring, all the "self-talk" passages turn into "ah, so that's what it's about."

## 2.4 A Warning

**The early version is fine to learn from, but not for production.**

Chapter 5 will demonstrate the early version's four real problems — each can cause misjudgments in live trading. After learning, switch to the final version. Do not put the early version into a strategy.

---

# Chapter 3: Understanding the Early Version's Core Geometry

This chapter's goal: **being able to explain in your own words what `divergence.py` is doing**.

If you've already mastered THEORY and LIBRARY, you can skip to Chapter 4 — but at least skim 3.5's milestone self-test.

## 3.1 Layer 1: Cut `hist` Into Segments

`find_hist_segments(hist_series)` does something minimal — cut by the sign of `hist` values:

```
hist:  + + + + - - - + + - - - - +
       └─ S1 ─┘└ S2 ┘└S3┘└─ S4 ─┘└ S5...
       pos     neg   pos  neg     pos
```

Each segment is a dict: `{'sign': 'pos'|'neg', 'start': int, 'end': int, 'area': float, 'bars': int}`.

**This step is the foundation of the axiomatic skeleton.** As NOTES_FOR_DEVELOPERS discusses: the hardest part of coding Chan theory — "what is one segment of a trend" — this project bottoms out by using "hist sign flip." In exchange we get: zero ambiguity, mechanically determinable segments.

## 3.2 Layer 2: Three-Segment Window Scan

Slide a length-3 window across the segment sequence, looking at `S1, S2, S3`:

- **Sign constraint**: S1 and S3 same direction, S2 opposite
- **Force decay**: `S3.area / S1.area < ratio_threshold` (default 0.5)
- **Price new high/low**: bullish divergence requires the lowest price within S3 < the lowest within S1; bearish, vice versa

All three satisfied → one L1 divergence.

Where does the magic number `ratio_threshold=0.5` come from? It's the project author's empirical value on crypto weekly/daily timeframes. Stricter on daily: 0.3–0.4. Noisier on 4h and below: 0.6–0.7. It's not an axiom — it's an engineering parameter.

## 3.3 Layer 3: Hierarchical Extension (The Cleverest Step in the System)

Treat `P1 = S1 + S2 + S3` as a **composite segment**:

- `P1.sign = S1.sign` (= S3.sign too)
- `P1.area = S1.area + S3.area` (S2 is opposite, not counted)
- `P1.span` runs from S1.start to S3.end

Then apply the **same three-segment divergence rule** on `P1 + S4 + S5`:

- Sign constraint: P1 and S5 same direction (both = S1.sign), S4 opposite ✓
- Force decay: `S5.area / P1.area < 0.5`
- Price new high/low: extreme within S5 vs **union of extremes from all same-direction segments inside P (S1 and S3)**

Satisfied → an L2 divergence. Similarly L3 = `P2 + S6 + S7`, with P2 = P1 + S4 + S5.

**Why this step is clever**: it unifies "basic three-segment divergence" and "trend-level divergence" into a single piece of code. Without this abstraction, you'd either write two independent detection paths (maintenance nightmare) or give up on trend-level signals (too weak alone).

In code, this corresponds to `_scan_levels`, which enumerates all levels via `2k+1`-segment windows.

## 3.4 Layer 4: The Opposite Barrier

This is the hardest step, and the most intellectually deep part of the system.

**Geometric definition**: a level-k≥2 divergence D is rejected iff there exists an opposite-direction divergence D' whose `s3_end` strictly falls inside D's open interval `(s1_start, s3_end)`.

**Intuition**: `s3_end` is the divergence's "trigger point" — the bar on which the reversal becomes effective. Once this instant falls inside a same-direction structure being built, the two ends of the structure belong to different mechanisms ("before the trend switch" and "after"), and shouldn't be merged into a single P.

**Example**:

```
Time ────────────────────────────────────────►

        ↓ D's s1_start                       ↓ D's s3_end
        ├──────────────────────────────────┤   ← D (a same-direction L2 divergence's span)
                    ↑ D's s3_end
                    (an opposite-direction L1's trigger point,
                     strictly inside D's open interval)
```

D wants to claim "from s1_start to s3_end is a continuous downtrend structure" — but an opposite reversal signal D' already occurred in between. The downtrends on either side don't belong to the same wave — D must be rejected.

In code: `_filter_by_opposite_barriers`, sorted by `s3_end` ascending (earlier triggers settled first), a single linear scan converges.

## 3.5 Second Milestone ✓

Without looking at code or docs, sketch the following on a whiteboard:

1. A hist sequence cut into 7 segments, with L1, L2, L3 candidate windows marked
2. A scenario where an L2 divergence gets rejected by an opposite L1 barrier

If you can't draw them, go back to 3.3 and 3.4. These two sections are the spine of the system — without passing here, everything later floats.

---

# Chapter 4: Render Divergences Onto the Chart

This chapter's goal: **see red ▲ (bullish) and green ▼ (bearish) markers on the K-line chart**.

## 4.1 Why Split `plot.py`

Chapter 1 produced divergence data, but only in flat printout form. To draw them on the chart, the current 40-line `plot.py` is no longer enough — we need:

- Draw triangles on the MACD panel positioned per divergence
- Compute text offsets (so labels don't overlap hist bars)
- Auto-expand ylim (so markers don't get clipped)

Stuffing this visual logic into `plot.py` would make it unmaintainable. So split into two files:

```
plot_helpers.py  ← divergence annotation logic (how to draw ▲▼ and text)
plot_kline.py    ← main plotting entry (K-line + MACD + calls helpers)
```

`plot.py` is now retired.

## 4.2 `plot_helpers.py` Minimal Skeleton

The repository's `plot_helpers.py` is 150+ lines — handling arrows, text, ylim expansion, double triangles, etc. For the learning stage, implement the simplest version first:

```python
"""
plot_helpers.py (learning version)
Plotting helpers: annotate divergences on the MACD panel.
"""

COLOR_BULLISH = '#ff3344'  # red: bullish divergence
COLOR_BEARISH = '#22aa44'  # green: bearish divergence

def annotate_divergences(macd_ax, df, divergences):
    """Draw triangles + force-ratio text on the hist of the MACD panel."""
    if not divergences:
        return

    y_min, y_max = macd_ax.get_ylim()
    y_range = y_max - y_min

    for d in divergences:
        s3_start, s3_end = d['s3_start'], d['s3_end']
        x_mid = (s3_start + s3_end) / 2

        # extremum within the hist segment (anchors the arrow)
        hist_segment = df['hist'].iloc[s3_start:s3_end + 1]
        if d['kind'] == 'bullish':
            y_anchor = hist_segment.min()
            y_marker = y_anchor - y_range * 0.05  # below the red bar
            marker = '^'
            color = COLOR_BULLISH
        else:
            y_anchor = hist_segment.max()
            y_marker = y_anchor + y_range * 0.05  # above the green bar
            marker = 'v'
            color = COLOR_BEARISH

        macd_ax.scatter([x_mid], [y_marker], marker=marker,
                        s=80, color=color, edgecolors='white',
                        linewidths=0.6, zorder=5)

        # force-ratio text (on the opposite side of the zero axis)
        text_y = y_range * 0.1 if d['kind'] == 'bearish' else -y_range * 0.1
        label = f"L{d['level']} {d['ratio']*100:.0f}%" if d['level'] >= 2 \
                else f"{d['ratio']*100:.0f}%"
        macd_ax.text(x_mid, text_y, label,
                     fontsize=7, color=color, ha='center', va='center')
```

These 30 lines implement the core visual of the repository version. After learning Chapters 5 and 6, you can go back and study how the repo version handles double triangles, the `?` suffix on provisional signals, ylim expansion, etc.

## 4.3 `plot_kline.py` Replaces the Original `plot.py`

The original `plot.py` calls `mpf.plot` directly, with no way to add things after the chart is drawn. Need to switch to `returnfig=True` to grab the figure and axes:

```python
"""
plot_kline.py
Unified entry for K-line + MACD + divergence annotations.
"""
import mplfinance as mpf
from plot_helpers import annotate_divergences


def get_macd_colors(hist):
    return ['g' if v >= 0 else 'r' for v in hist]


def plot_with_divergences(df, divergences,
                          title='BTCUSDT Weekly',
                          last_n=200):
    df_plot = df.tail(last_n)
    # After slicing, the divergence indices need to be offset
    offset = len(df) - len(df_plot)
    divs_plot = [
        {**d,
         's1_start': d['s1_start'] - offset,
         's1_end':   d['s1_end']   - offset,
         's3_start': d['s3_start'] - offset,
         's3_end':   d['s3_end']   - offset}
        for d in divergences
        if d['s3_start'] >= offset   # filter out those outside the window
    ]

    macd_colors = get_macd_colors(df_plot['hist'])
    apds = [
        mpf.make_addplot(df_plot['macd'],   panel=2, color='#1f77b4'),
        mpf.make_addplot(df_plot['signal'], panel=2, color='#ff7f0e'),
        mpf.make_addplot(df_plot['hist'],   panel=2,
                         type='bar', color=macd_colors),
    ]

    fig, axes = mpf.plot(
        df_plot, type='candle', style='charles',
        title=title, ylabel='Price', volume=True,
        mav=(7, 25, 99), addplot=apds,
        panel_ratios=(4, 1, 2), figsize=(14, 10),
        returnfig=True,
    )

    # Grab the MACD panel (panel=2 corresponds to a specific axes index
    # per mplfinance's convention)
    macd_ax = axes[-2]   # second-to-last is the MACD primary axis
                         # (last is its twin)
    annotate_divergences(macd_ax, df_plot, divs_plot)

    import matplotlib.pyplot as plt
    plt.show()
```

**Note the `offset` shift**: after `tail(last_n)`, the new df re-indexes from 0, but the indices in `divergences` are based on the original df. They must be shifted.

## 4.4 Update `main.py`

```python
from data import get_weekly_klines
from indicator import add_indicators
from divergence import find_three_segment_divergences
from plot_kline import plot_with_divergences


if __name__ == "__main__":
    df = get_weekly_klines()
    df = add_indicators(df)
    divs = find_three_segment_divergences(
        df['hist'], df['low'], df['high'],
        max_level=None, block_by_opposite=True,
    )
    plot_with_divergences(df, divs, last_n=200)
```

## 4.5 Third Milestone ✓

Run `python3 main.py`. Red ▲ and green ▼ markers appear on the chart, with text like `L2 41%` below them.

Congratulations — the system can now visualize divergence signals. This is a simplified version of what the repository main screenshots show.

---

# Chapter 5: The Early Version's Four Real Pitfalls

**This chapter is the core of the guide.** Each section is a reproducible phenomenon → problem analysis → the final version's patch.

By the end of this chapter, you'll realize: every cryptic "correction note" in the final docstring corresponds to a phenomenon you've now seen with your own eyes.

## 5.1 Pitfall 1: Duplicate Annotations at the Same Terminal Position

### Phenomenon

Set `max_level=None` and run on BTC weekly. Look carefully at the chart — at certain positions, **two percentage labels stack on top of each other**: an `L2 38%` and a `42%`, squeezed together.

Why? The same terminal segment S_last can simultaneously satisfy multiple level conditions:

- L2 trigger: S5 vs P(S1+S3) ratio = 38%
- L1 trigger: S5 vs S3 ratio = 42% (taking the nearest S3 as the new S1 and looking again)

The early `find_three_segment_divergences` returns both, and the plotting layer stacks both labels on the same K-line.

### Why It's a Problem

Visually crowded and hard to read. More importantly, **the two signals actually represent the same divergence** viewed at different scales. In backtesting they'd be double-counted.

### The Final Version's Patch: `_dedupe_same_terminal`

The final version adds a dedup function: for same `kind` and same `(s3_start, s3_end)`, keep only the highest `level`. The rule: **trend-level divergence outranks three-segment divergence**.

If the merged-away lower level *also* independently held (meaning force decay holds at multiple scales at this terminal), the surviving record gets tagged with `same_terminal_l1=True`. The UI draws double triangles to indicate "stronger signal."

### Do You Need to Patch?

If only using `max_level=1`, **this problem doesn't occur**, no patch needed.

If enabling `max_level>=2`, **must patch**. Minimal implementation:

```python
def dedupe_same_terminal(divs):
    """Same kind, same terminal position: keep the highest-level record."""
    by_key = {}
    for d in divs:
        key = (d['kind'], d['s3_start'], d['s3_end'])
        if key not in by_key or d['level'] > by_key[key]['level']:
            by_key[key] = d
    return list(by_key.values())
```

Caller adds one line after `find_three_segment_divergences`:

```python
divs = find_three_segment_divergences(...)
divs = dedupe_same_terminal(divs)   # ← new
```

Or just use the final version's `_dedupe_same_terminal` — it additionally maintains the `same_terminal_l1` field for a better UI.

## 5.2 Pitfall 2: Unsettled Signals at the End

### Phenomenon

Pull the **latest** data (`end_str=None`, data extends to the present moment). Note the ratio of the last divergence printed.

Run again a day or a few hours later — you'll see:

```
Yesterday: [Bullish Lv1] ratio=34% S3 window: 2026-05-15 ~ 2026-05-22
Today:     [Bullish Lv1] ratio=37% S3 window: 2026-05-15 ~ 2026-05-29
```

S3's window extended, ratio changed.

### Why It's a Problem

The last `hist` segment hasn't "sealed" yet — as long as hist hasn't flipped sign back, S_last keeps extending. This means:

- The ratio is a **snapshot** — next K-line in, it'll change
- If ratio hasn't reached 0.5 but "feels close," that's subjective judgment, not an axiom
- **In backtesting, mistakenly using such unsettled signals as confirmed signals introduces lookahead bias** — what you "saw at time t" and what you "could actually have decided on at time t" are two different things

### The Final Version's Patch: `provisional` Field

Every record in the final version has an extra `provisional` field:

- `provisional=False`: S_last has sealed (opposite-sign hist has appeared after it), signal confirmed
- `provisional=True`: S_last extends to the data's end, signal unsettled

The UI displays provisional signals in blue with a `?` suffix (see the "Visual Encoding" table in README). For backtesting, filter in one line:

```python
confirmed = [d for d in divs if not d['provisional']]
```

### Do You Need to Patch?

**If doing live monitoring or backtesting, must patch.** If only viewing historical charts (end_str is a past date), no — the terminal segment in historical data is always sealed.

Minimal patch:

```python
def mark_provisional(divs, hist_series):
    """Tag signals whose terminal segment extends to series end."""
    n = len(hist_series)
    for d in divs:
        d['provisional'] = (d['s3_end'] == n - 1)
    return divs
```

This is a crude approximation — the final version uses "whether the terminal segment's hist has begun to reverse" as a stricter test. Recommended: use the final version's implementation.

## 5.3 Pitfall 3: Extremes Missed Because Momentum Leads Price

### Phenomenon

Find a real market segment where the true price top (or bottom) falls *after* hist has already flipped sign. For example:

```
Price:  ↗↗↗↗↗ peak ↘     ← real top is here
hist:   + + + ─ ─ ─ ─    ← hist already flipped to negative
                ↑
                this bar's hist=negative, classified into the "negative segment" by find_hist_segments
                but the true price high is one bar above it
```

When `find_three_segment_divergences` runs, **this real top gets missed** — it doesn't fall inside any `pos` segment, and the standard three-segment bearish scan can't see it.

### Why It's a Problem

This is an intrinsic property of MACD — it's a momentum indicator, and **momentum turning points lead price turning points**. NOTES_FOR_DEVELOPERS pitfall #5 discusses this in detail.

Consequence: a portion of real extreme divergences gets missed. How much depends on the market — low miss rate on crypto weekly, significantly higher on 4h and below.

### The Final Version's Patch: `find_missed_extremes`

The final version adds an independent recheck function for "price extremes that appear after hist flips sign." How it works (simplified):

- Scan each same-direction hist segment
- Check the few opposite-direction hist bars on either side of the segment for prices "more extreme than the segment's own"
- If found, generate a `level=0` "extreme divergence" record (using level=0 to distinguish from standard three-segment divergences)

The final version's entry function calls both `find_three_segment_divergences` and `find_missed_extremes` and merges the results.

### Do You Need to Patch?

**If your trading system depends on "never missing a real top/bottom," must patch.** In that case, switch directly to the final version — don't roll your own. This patch has many edge cases ("how far to scan on either side," "what price threshold") and rolling your own usually makes it worse.

If you can accept "standard three-segment divergence misses some extremes, but those it does catch are structurally clear" — no patch needed, the early version is fine.

## 5.4 Pitfall 4: The L1 Barrier Bug (Logic Error)

### Phenomenon

This pitfall is the most subtle — requires constructing specific data to reliably reproduce. Simplified:

```
Opposite L2:  ────D'────D'.s3_end────
                                ↓ trigger inside the L1 below's open interval
Same-direction L1:  ──D.s1_start────────────────D.s3_end──
```

Lines 287-303 of the early `_filter_by_opposite_barriers`:

```python
if d['level'] < 2:
    survivors.append(d)
    continue
```

Meaning: L1 candidates **unconditionally survive**, never subject to barrier rejection.

But in the example above: the opposite L2's trigger point (D'.s3_end) does strictly fall inside the same-direction L1's open interval (D.s1_start, D.s3_end) — by the axiom, this L1 should be blocked (its S1 and S3 lie on opposite sides of a trend switch). **The early version retains this L1 that should have been blocked.**

### Why It's a Problem

The early version's reasoning conflated two concepts. Original: "in the open interval of a 3-segment r-g-r or g-r-g there's only 1 opposite-color segment, can't make up an opposite-direction divergence's trigger point."

This reasoning only holds if the "opposite divergence fits entirely inside the L1 open interval" — but the barrier rule doesn't require "opposite divergence fits inside," it requires "opposite divergence's **trigger point** is inside the open interval." The single opposite segment (S2) inside an L1 can absolutely serve as the S_last of some **higher-level opposite divergence** (L≥2), whose trigger point is exactly that S2's end, strictly inside the L1's open interval.

Real-world impact: at trend-switching positions, an L1 signal that should have been blocked continues to display, giving readers the false impression "still the same wave of trend."

### The Final Version's Patch: Asymmetric L1 Treatment

The final version splits the barrier rule along two directions:

- **L1 as the blocked party**: participates in barrier judgments. When an opposite L≥2's trigger falls inside the L1's open interval, the L1 is blocked.
- **L1 as the blocker**: does NOT constitute a barrier. Two adjacent same-level L1s (e.g. an S1+S2+S3 bullish immediately followed by an S2+S3+S4 bearish) are the canonical double-signal of market reversal. Geometrically they must "cross" each other's open intervals — letting L1s mutually block would destroy both.

This asymmetric design **isn't a correction of the axiom**, but an application-layer filter on top of the axiom — explicitly declaring "an L1's opposite trigger isn't strong enough to reject a same-direction structure spanning it."

In code, this corresponds to the final version's `max_level_at` precomputation (judging barrier qualification by "the maximum level reached at the same terminal position").

### Do You Need to Patch?

**The probability of hitting this bug in live trading isn't high, but when you do, it's a false signal.** Recommendation: switch to the final version.

If insisting on patching the early version, minimal change:

```python
def _filter_by_opposite_barriers(divs):
    # Precompute max level reached at each (kind, s3_start, s3_end)
    max_level_at = {}
    for d in divs:
        key = (d['kind'], d['s3_start'], d['s3_end'])
        max_level_at[key] = max(max_level_at.get(key, 0), d['level'])

    sorted_divs = sorted(divs, key=lambda d: (d['s3_end'], d['level']))
    survivors = []
    for d in sorted_divs:
        # No longer unconditionally retain L1 — all levels participate in barrier judgment
        blocked = False
        for s in survivors:
            if s['kind'] == d['kind']:
                continue
            s_key = (s['kind'], s['s3_start'], s['s3_end'])
            # The blocker at that position must have reached level > 1
            if max_level_at.get(s_key, 0) <= 1:
                continue
            if d['s1_start'] < s['s3_end'] < d['s3_end']:
                blocked = True
                break
        if not blocked:
            survivors.append(d)
    return survivors
```

This 18-line block is the most non-trivial piece of algorithmic logic in the project. Understanding why these 18 lines are written this way means truly grasping the opposite-barrier rule — not just being able to call the API.

## 5.5 Fifth Milestone ✓

After reading all four pitfalls, close the document and self-test:

1. Without looking at code, explain in your own words what `_dedupe_same_terminal` does and why it's needed
2. Explain lookahead bias and why the `provisional` field prevents it
3. Explain the concrete manifestation of "momentum leads price" on MACD
4. Sketch on a whiteboard a scenario where an L1 should be blocked by an opposite L2

Passing all four → proceed to Chapter 6.

---

# Chapter 6: Upgrade to the Final Version

## 6.1 Swap the File

Copy `divergence.py` from the repository's `code_en/` directory and replace the version previously copied from `examples/02-with-divergence/` in your project.

The API is fully backward-compatible — `find_three_segment_divergences(...)` calls need no changes. The new fields are **additive**; old code that doesn't read these fields works exactly as before.

## 6.2 What You Can Now Read

Open the final version's docstring. You'll find:

- "L1 also accepts barrier judgment (as the blocked party)" — you saw this phenomenon in 5.4, instant understanding
- "Triggering an opposite divergence = the start of the next same-direction structure" axiomatic phrasing — you've sketched this in 3.4, instant understanding
- "Barrier strength judged by 'maximum level at the same terminal position'" — the minimal patch in 5.4 uses exactly this, instant understanding
- The `same_terminal_l1` field description — you saw the double-annotation phenomenon in 5.1, instant understanding

The final version's docstring is no longer "the author talking to themselves" — it's now **an engineering log you can fully follow**.

## 6.3 Using the New Fields

The two most-used new fields:

```python
# Filter unsettled signals during backtesting
confirmed = [d for d in divs if not d.get('provisional', False)]

# Draw double triangles for "multi-scale resonance" in UI
for d in divs:
    if d.get('same_terminal_l1'):
        draw_double_triangle(...)
    else:
        draw_single_triangle(...)
```

## 6.4 Sixth Milestone ✓

Fully explain every paragraph of the final version's docstring. This is the marker of truly "understanding the library" — a step above "knowing how to call the API."

---

# Chapter 7: After Crossing the Threshold

## 7.1 What Else This Project Can Add

By engineering difficulty:

| Difficulty | Task | Files involved |
|------------|------|----------------|
| ★ | Multi-symbol support (parameterize symbol) | `data.py` |
| ★ | Multiple data sources fallback (Binance → Hyperliquid → ...) | `data.py` |
| ★★ | Multi-timeframe support (daily / 4h / 1h) | `data.py` + `plot_kline.py` |
| ★★ | Unit tests (`indicator.py` + `divergence.py`) | new `tests/` |
| ★★★ | Batch scanner (find signals across N symbols × M timeframes) | new `scanner.py` |
| ★★★ | Multi-timeframe drill-down (click a high-timeframe segment to enter low-timeframe) | introduce `navigation.py` |
| ★★★★ | Web UI or desktop UI | introduce `app.py` or `main.py` (Tk) |
| ★★★★★ | Backtest framework | a whole new module |

## 7.2 On Multi-Timeframe Drill-Down

The repository's `navigation.py` implements "click a weekly segment → enter the 3-Day view → click again → enter daily → ... → 15m" pyramid drill-down. This is the core interaction shown in README's screenshots.

Core idea: dynamically compute segment count from the current chart's K-line count using `segment_count = floor(N_next / BARS_PER_SEGMENT_TARGET) + 1`. See `compute_segment_count` and `compute_subranges` in `navigation.py`.

**Not expanded here** — it's drifted from "divergence system" into UI/UX territory, no longer an algorithmic problem. If your project doesn't need this interaction, skip.

## 7.3 On UI

- **Desktop UI** (`main.py` Tk version): cross-platform, single-file distributable, good for local tools
- **Web UI** (`app.py` Flask version): browser-accessible, mobile-friendly, good for sharing

Both **share the same algorithm and data layer** — that's the dividend of layered design. If you want a third UI in the future (e.g. Streamlit), `divergence.py` won't change by a single line.

**Not expanded here either** — which one to pick depends entirely on the deployment scenario, and the repository has complete implementations of both for reference.

## 7.4 The Hard Part Isn't in the Code

By now you have a system that can mark divergence signals on K-line charts. But this is not the same as "a profitable system."

As both the README disclaimer and NOTES_FOR_DEVELOPERS Section 7 emphasize: **half the difficulty of coding theories like this is technical; the other half is statistical validation and live-trading decision-making**.

Specifically, the questions that actually determine profit and loss:

- Which timeframe's divergence signals are worth trading?
- How to size positions? How to stop when divergence fails?
- After slippage + fees + taxes, what's left?
- Compared to the buy-and-hold passive baseline, is the alpha significant?
- Which assets suit this framework? Which don't?

These require **statistical backtesting on historical data** to answer — they can't be derived from axiomatization. This project's visualization tools can **assist** these observations, but **don't replace** them.

---

## Closing Note

You've now traversed all four stages: from "reader of theory" → "owner of K-line chart" → "owner of complete divergence system" → "true reader of the library."

This guide ends here. Two directions forward:

- **Toward engineering depth**: tests, scanners, backtest frameworks, your own UI
- **Toward decision depth**: use these tools to repeatedly validate on historical data, form your own trading intuition

Neither path is easy, but the hardest "hands-on + understanding" threshold has already been crossed.

The rest is up to you.

Wishing you all the best.
