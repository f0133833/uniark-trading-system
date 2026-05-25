# Methodology Notes on Coding Chan Theory

> This document is the write-up of an extended discussion that took
> place after the project was released. The intended reader is a
> developer who has tried to code up Chan theory (缠论) or a similar
> Chinese price-action framework, and has already run into the wall
> described in §1. The document is about *the trade-offs behind the
> design choices*, not a tutorial, not an API reference.
>
> **This document exists in the same spirit as the no-maintenance
> notice in the README — it is reference material, not an ongoing
> service.** The author will not update it, and will not answer
> questions about it. If you find these ideas useful, you are
> encouraged to fork the project and develop your own version.
>
> Compiled from a discussion with Claude (Anthropic). The attribution
> of specific insights is given at the end.

---

## Who Should Read This

This document is most useful for a very specific reader: **someone
who has actually tried to write Chan theory in code and has hit the
wall at the fenxing / bi / xianduan (分型 / 笔 / 线段) layer.**

If you have not tried — if you have only read the original Chan
material — the document's argument for "why this wall need not be
broken through" may not register. Try the implementation first, then
come back.

If you have no exposure to Chan theory at all and are simply curious
about "how to formalize a prose-style trading framework," this
document is still useful — but treat it as **a methodology case
study**, not as an introduction to Chan theory itself.

## What This Document Does Not Claim

- **It does not claim that this framework is superior to Chan
  theory.** It uses a different set of trade-offs.
- **It does not claim that the framework is backtest-validated.**
  See the disclaimer in the project README.
- **It does not claim this is the only path to coding Chan theory.**
  It is a path that has been tried, is internally consistent, and is
  publishable — not the only path.

---

## 1. The Actual Difficulty of Coding Chan Theory

Almost everyone who tries to write Chan theory in code hits the same
wall:

- K-line containment merging (the up / down direction rules)
- Recognition and validity of fractals (top fractal / bottom fractal,
  顶分型 / 底分型)
- Counting the "at least N K-lines" rule for a stroke (笔) after
  containment processing
- The feature-sequence rule for line segments (线段), gap handling,
  the breaking of breakings

These rules are explained by example in the original Chan material;
translating them to code immediately surfaces a dozen edge cases.
The Chan community itself has version disagreements on every one of
these rules. An honest developer trying to "implement Chan strictly"
typically ends up either with a codebase they do not fully trust, or
gives up.

**The root cause of this wall is not that developers are lazy. It is
that the rule set is attempting an impossible task** — trying to
determine "what counts as a true segment of movement" by climbing
brick-by-brick from the K-line layer, with no external reference, on
nothing but the price sequence's structure. This task is
mathematically underdetermined: any adjudication rule depends on
unstated conventions (merge direction, minimum length, gap
ownership), and those conventions are not more "fundamental" than
"define a segment by an MACD hist sign change" — they are simply not
labeled as conventions.

## 2. The Core Idea: Bypass the Wall

This project's approach can be summed up in one sentence:

> **Keep "a segment of movement" as an undefined primitive at the
> theory layer; use the sign of the MACD histogram at the engineering
> layer to ground its definition.**

Concretely:

1. **The theory document** (`THEORY.md`) starts from "turning point"
   and "a segment of movement," and does **not** attempt to derive
   them from a lower layer (K-line / fractal). This is an
   **intentional blank**.
2. **The implementation** (`divergence.py`) defines a segment
   boundary as the moment the histogram changes sign. This fills
   the blank.

The trade-off this entails:

**What it buys you:**

- A segment becomes a mechanically determined object — zero
  ambiguity, no subjective judgment required in code.
- It is perfectly self-consistent with the definition of *force* as
  Σ|hist|. If you already use hist area to measure force, defining a
  segment as a hist-same-sign region makes the two pieces of the
  theory click together exactly.
- It sidesteps the hardest, most contested layer of Chan theory:
  K-line / fractal / stroke / segment.

**What it costs you:**

- Momentum leads price. The true price top / bottom often falls
  several K-lines *after* the hist has already changed sign, putting
  the price extremum in a "wrong-colored" reverse segment. The
  `find_missed_extremes` patch function exists precisely to handle
  this structural blind spot of the standard three-segment scanner.
- MACD parameters (12, 26, 9) become an implicit input to the system.
  The theory does not name them, but the location of segment
  boundaries depends on them.

**Why this trade-off is honest:** the K-line / fractal / stroke /
segment layer of Chan theory **also** contains many unstated
empirical conventions; it just dresses them up as "foundational
rules." Making the convention explicit — saying clearly "there is an
engineering interface here, the theoretical blank is grounded by
it" — makes the epistemic status of the whole framework clearer:
**what is axiom, and what is the engineering interface that lets the
axioms be computable.**

## 3. Noise: Recursion Instead of Filtering

Anyone coding a framework like this runs into the practical question:
**should a short reverse segment (a small pullback of a few K-lines)
count as an independent segment?**

The conventional answer is to set a threshold and filter: reverse
segments shorter than N K-lines count as "noise" and are merged into
neighboring segments. This is the original purpose of the `min_bars`
parameter in the code — but **in actual configuration the parameter
is 0, i.e., off by default.** The reason is that the project
eventually chose a philosophically cleaner alternative:

> **Do not filter noise; absorb it via hierarchical recursion.**

Concretely, three-segment divergences are detected not only on the
raw segment sequence S1, S2, S3, but recursively on their compounds:

- Level L1: S1, S2, S3 (the base three-segment structure)
- Compound segment P1 = S1 + S2 + S3
  (sign = S1.sign, area = S1.area + S3.area)
- Level L2: P1, S4, S5
- Level L3: P2, S6, S7
- ... and so on upward

**Why this design is more elegant:**

- "Noise filtering" presupposes an external criterion ("a segment
  this short is noise") and uses it to preprocess the data.
- "Hierarchical recursion" presupposes no such concept of noise. All
  hist sign changes are valid segments. Whether a reverse segment
  counts as a "real reversal" or as "in-trend continuation" is
  answered by the higher-level structural detection itself.
- Short reverse segments do not need to be eliminated; they simply do
  not matter at certain levels.
- The force formula P.area = S1.area + S3.area already excludes
  reverse segments. Whether a tiny S2 enters P1, or gets merged
  away by pre-filtering, P1's force value is identical.
  **The force formula is itself immune to reverse-segment size —
  adding a `min_bars` merge on top is redundant.**

**This is a genuinely transferable design pattern.** Anyone coding
Chan theory, or any similar framework, will face the "does this
small pullback count" question. Replacing "filter with a threshold"
with "absorb via levels" eliminates a large amount of
symbol-by-symbol, timeframe-by-timeframe tuning pain.

**A side observation:** the original Chan theory's "multi-level
joint analysis" uses different K-line periods (5-minute vs 30-minute
vs daily), analyzed independently and cross-referenced. This
project's L1 / L2 / L3 are **recursive levels on the same data, the
same segment sequence**. These are two orthogonal multi-scale
axes: one is granularity switching on K-line periods, the other is
structural recursion. The "pyramid drill-down" feature uses the
former; hierarchical divergence uses the latter.

## 4. MACD as a Theoretical Component: a Three-Layer Validation

Writing MACD into a theory that calls itself "axiomatic" requires
answering one question first: **is MACD an empirically motivated
heuristic, or a mathematical structure derived from price?**

The distinction matters. For indicators like RSI (with its 30 / 70
levels) or Bollinger Bands (with their ±2σ), the core signal is a
convention threshold; writing them into axioms imports unstated
empirical premises. MACD is different, and is worth examining at
three layers:

**Layer 1: the algorithm itself.** MACD is pure arithmetic, with no
fitting, no learning, no threshold decision:

```
MACD(t)   = EMA(price, 12)(t) - EMA(price, 26)(t)
Signal(t) = EMA(MACD, 9)(t)
hist(t)   = MACD(t) - Signal(t)
```

Given a price sequence, MACD is fully determined. **This layer is a
mathematical function of price, not an empirical heuristic.** ✓

**Layer 2: structural interpretation.** EMA is a low-pass filter, so:

- `EMA(12) - EMA(26)` is a **band-pass filter** — it amplifies
  price oscillations in a "mid-frequency" band and suppresses both
  noise and long-term trend. This is equivalent to price momentum at
  that frequency band.
- `hist = MACD - EMA(MACD, 9)` is a smoothed approximation of the
  momentum signal's own rate of change.

Putting them together: **hist(t) ≈ a smoothed approximation of
price's second derivative at a specific frequency band.** Its sign
tells you whether momentum is accelerating or decelerating; the
moment it flips sign is a momentum turning point.

No empirical content at this layer — it is the composition of two
standard signal-processing operations (band-pass plus
differentiation), each with a precise mathematical meaning. So "hist
sign change" as a segment boundary is not meaningful because someone
**stipulated** it; it is **structurally** the marker of a momentum
turning point. ✓

**Layer 3: the parameters (12, 26, 9).** These three numbers were
chosen by Gerald Appel in the 1970s based on observations of US
equities. They were not derived from first principles. Substitute
(10, 20, 7) or (15, 30, 10) and all the mathematical properties
above still hold (it is still band-pass plus differentiation); only
the exact placement of "mid-frequency" shifts. **This layer is
empirical.** ✗

**The conclusion:**

- Algorithm itself: price-based, non-empirical. ✓
- Structural interpretation (hist sign change = momentum turning
  point): mathematical property, parameter-independent,
  non-empirical. ✓
- Exact K-line at which hist flips: parameter-dependent, empirical. ✗

Importing MACD values into the theory is **legitimate** — provided
that the theory's assertions stay at the **structural** level
("segment exists," "force decays," "divergence holds") and not at
the **precise timing** level ("turn happens at 14:30 on date X").

This dovetails very well with the recursive extension of §3: **the
theory only acknowledges parameter-independent structural facts;
parameter-sensitive details get absorbed automatically by the level
recursion.** A short segment has its place at L1, but is absorbed
into the compound P at L2 — this mechanism makes higher-level
judgments robust against MACD parameter choices.

**This three-layer validation is reusable.** To consider importing
other tools (volume, moving averages, ATR) into a similar axiomatic
framework, ask the same three questions:

1. Is the algorithm itself a pure function of price?
2. Are the structural assertions (the signal's semantics)
   parameter-independent?
3. Does parameter sensitivity affect truth value, or only timing
   precision?

If (1) and (2) are "yes" and (3) affects only timing precision, the
tool can legitimately enter the axiomatic system — provided that the
assertions stay at the structural level, not the timing level.

## 5. Side-by-Side with Chan Theory

To place this project relative to Chan theory:

| Dimension | Chan theory (original) | This project |
|-----------|-----------------------|--------------|
| Definition of "a segment" | Constructed layer-by-layer from K-line → fractal → stroke → segment | Left blank; grounded by MACD hist sign change |
| Central pivot / overlap zone | Three-segment overlap, locked once formed | Same; this project calls it 盘整区间 (consolidation interval) |
| Recursive construction of trends | Multiple central pivots + step-up / step-down | Same |
| Force measure | MACD histogram area | Same |
| Divergence | Trend divergence + consolidation divergence | Trend divergence + three-segment divergence, with L≥2 hierarchical extension |
| Buy / sell points | Three classes | Two classes (corresponding to Class 1 and Class 3); Class 2 omitted |
| Multi-level analysis | Different K-line periods, jointly analyzed | Within-period L1/L2/L3 recursion **plus** cross-period pyramid drill-down |
| Short reverse-segment handling | Implicitly handled by stroke / segment validity rules | Not handled; absorbed automatically by recursion |
| Confirmation of reversal | Stroke / segment breaking rules | "Uptrend break / downtrend break" with explicit formal definition |
| Style | Prose plus examples | Axiom plus deduction |
| Codability | Depends on the implementer's resolution of contested rules | Directly writable |

Reading this table, the impression should be: **the core skeleton is
basically Chan's, what is simplified away is the hardest layer to
code, what is strengthened is formal rigor and falsifiability.**

## 6. Common Pitfalls When Coding Chan Theory

Distilling the discussion into concrete, operational reminders:

**(1) Do not try to strictly implement every stroke / line-segment
rule.** The Chan community itself disagrees on these; there is no
single "correct" implementation. Pick a **mathematically unambiguous
substitute definition** (this project uses MACD hist sign change;
others are possible) to fill the blank, then document the
substitution explicitly.

**(2) Do not pre-filter short reverse segments.** Absorb them via
recursive extension. This is not only philosophically cleaner but
saves enormous tuning effort across symbols and timeframes.

**(3) The force formula must be immune to reverse-segment size.**
P.area = Σ(same-direction segment.area) and exclude reverse
segments, so recursive extension is not distorted by a particularly
short or long S2.

**(4) Distinguish structural claims from timing claims.** "A
divergence exists" is a structural claim, parameter-independent. "A
divergence occurs precisely at t = T" is a timing claim,
parameter-dependent. Anchor trading decisions on structural claims,
not on timing claims.

**(5) Momentum leads price; you must supplement for extrema.** True
price tops / bottoms often fall after hist has flipped sign, causing
the standard three-segment scan to miss the extremum. A separate
patch rule is required (see `find_missed_extremes`); do not assume
"standard detection covers all cases."

**(6) Provisional signals must be clearly marked.** When S_last
extends exactly to the data's right edge, the ratio is a snapshot,
not a verdict — it will continue to change. Mark this visually (this
project uses dodger blue + `?` suffix); do not let the user mistake
it for a confirmed signal.

**(7) Distinguish "barrier" from "extension."** When a
same-direction structure forms while crossing an already-triggered
reverse signal, the same-direction structure is structurally invalid
— it has incorrectly merged the "before reversal" and "after
reversal" segments into one P. The detailed semantics are in the
"opposite-barrier rule" section at the top of `divergence.py`; this
is the most non-trivial piece of the codebase.

## 7. What This Document Does Not Solve

To avoid raising unrealistic expectations, in plain terms:

**The difficulty of coding Chan theory is half technical and half
empirical.** This document addresses the former — theory /
engineering interface, noise handling, indicator legitimacy. But
practical decisions still require the latter:

- What level of central-pivot oscillation is worth trading?
- What pullback depth qualifies for a Class-2 buy point?
- Which instruments fit the framework, and which do not?
- How does position sizing pair with structural signals?

These questions are fundamentally statistical observations on
historical data; axiomatization cannot answer them directly. This
project's visualization tools can **assist** such observation, but
do not **substitute** for it.

For any reader who intends to use this framework for real trading,
the README already says:

- Conduct your own statistical validation (with realistic slippage,
  fees, taxes).
- Compare against a passive baseline such as buy-and-hold.
- Recognize that "pretty on the chart" does not mean "profitable in
  forward trading."

---

## Acknowledgments and Attribution

This document was compiled from a discussion held after the project
was released. The other party in the discussion was Claude
(Anthropic). Attribution of specific insights:

- The design choice "min_bars deprecated; absorb noise via
  recursion" — the project author
- The question "is MACD an empirical heuristic?" and the three-layer
  validation framework — posed by the project author; the analysis
  developed jointly in discussion
- The framing "theoretical blank + engineering interface," the
  side-by-side table with Chan theory, the distillation of
  transferable design patterns — co-developed in the discussion;
  written up by Claude

This document exists as **reference material** in the same spirit as
the rest of the project, and is not maintained. Disagreements with
any view here are welcome in your own fork / blog / project; the
author will not respond to them in this repository.

---

*中文版: see [`NOTES_FOR_DEVELOPERS_ZH.md`](NOTES_FOR_DEVELOPERS_ZH.md).*
