"""
Three-segment divergence detection module
(S1 + S2 + S3, with hierarchical recursive extension).
====================================================

This is the single canonical implementation of the trading framework's core
"three-segment structure / co-directional force comparison / divergence
identification" logic. All upper-layer applications (plot_kline.py /
app.py / main.py and any future extensions) must import this module.

Axiomatic principles
--------------------
1. Slice the MACD histogram (hist) series into consecutive segments by
   the sign of each bar (positive vs. negative).
2. Segments shorter than `min_bars` bars are treated as "noise" and
   merged into adjacent opposite-direction segments; adjacent
   same-direction segments are then coalesced. With min_bars=0 this
   step is a no-op.
3. On the merged segment sequence, scan with a "co-directional /
   opposite / co-directional" three-segment window for divergence.

Hierarchical extension
----------------------
Base structure: P₁ = S1 + S2 + S3. Treat P₁ as a composite segment:
  - P₁.sign  = S1.sign (= S3.sign)
  - P₁.area  = S1.area + S3.area      (S2 is opposite-direction; excluded)
  - P₁.span  from S1.start to S3.end

On a longer sequence we can construct P₁ + S4 + S5
(where S4 is opposite, S5 is co-directional), and apply the same
three-segment divergence test → Level-2 divergence.
By induction: P₂ = P₁+S4+S5 can extend to P₂+S6+S7 → Level 3, and so on.

A k-th-level structure consists of 2k+1 raw segments: k co-directional
+ k opposite (k-1 internal + the rightmost one being opposite). More
precisely: k co-directional segments alternating with (k-1) opposite
segments, plus the final co-directional segment → 2k+1 segments
total. When testing "P + S(2k) + S(2k+1)" as a base three-segment
candidate, P is composed of the first 2k-1 segments.

Trigger conditions (identical to the base level):
  a. (rightmost co-directional segment).area / P_k.area  <  ratio_threshold
  b. Bullish: rightmost segment's low < min(lows of all P-internal
     co-directional segments)
     Bearish: rightmost segment's high > max(highs of all P-internal
     co-directional segments)

Opposite-barrier rule
---------------------
A triggered opposite-direction divergence "destroys" any same-direction
high-level structure that crosses its trigger point. Formally:
  A divergence D is rejected iff there exists a surviving
  opposite divergence D' satisfying
    (a) D'.s3_end ∈ (D.s1_start, D.s3_end) (D's trigger point
        falls strictly within D's open span), and
    (b) D''s highest level at the same terminal position
        (kind, s3_start, s3_end) > 1.

Intuition: s3_end is the "trigger point" of a divergence (the moment
the reversal takes effect). Once that moment lies inside the
co-directional structure you are trying to build, the two ends of the
structure belong to two different mechanisms — one before and one
after the trend switch — and must not be merged into a single P.

Semantics of (b): two adjacent same-level L1 reversed divergences
(e.g. an S1+S2+S3 bullish-L1 immediately followed by an S2+S3+S4
bearish-L1) are geometrically symmetric with "L1 shielded by L≥2":
the former's trigger point also lies strictly within the latter's
open span. But L1+L1 is the canonical "twin-reversal" signal of a
market turn (downside force decay → bounce → bounce force decay →
re-reversal), and both should be kept. The only formal feature that
distinguishes the two cases is level: L≥2 is a trend-level signal
entitled to "veto" any co-directional structure crossing its
trigger point; L1 divergences are peers and never shield each other.

The "highest level at the same terminal position" is consistent with
_dedupe_same_terminal: during structural extension a terminal may
trigger both L1 and L≥n simultaneously, and dedupe treats them as the
strongest representation of the same divergence; barrier judgment
likewise uses the highest level to determine barrier strength, keeping
the two semantics aligned.

This is a recursive definition: D' may itself be rejected by a
deeper-nested opposite divergence, in which case D' is no longer a
valid barrier. Processing in ascending order of s3_end (earliest
trigger decided first), one linear pass converges.

Note: condition (a) is strictly stronger than "opposite span fully
contained" — if D'.span ⊆ D.span, then D'.s3_end necessarily lies in
(D.s1_start, D.s3_end]. When D' starts before D (the two overlap but
neither contains the other), condition (a) still captures it
correctly, which is exactly the first-fix scenario.

L1 as the shielded party still participates: L1's single
opposite-direction S2 segment can itself serve as the S_last of
some L≥2 opposite divergence, whose trigger point s3_end equals
L1.S2.end and falls strictly within L1's open interval
(S1.start, S3.end). In that case L1's S1 and S3 belong to two
different mechanisms — one before and one after the trend switch
— and the rule shields L1 accordingly.

Public API (still a single function):
    find_three_segment_divergences(hist, low, high,
                                   min_bars=0,
                                   ratio_threshold=0.5,
                                   max_level=1,
                                   block_by_opposite=True)

Parameter `max_level`:
    1 (default)  Detect base three-segment only (fully backward-
                 compatible with historical behavior).
    2, 3, ...    Also detect higher-level extensions.
    None         Exhaust all possible levels (until segments are
                 insufficient).

Parameter `block_by_opposite`:
    True (default)  Apply the opposite-barrier rule (the user's
                    preferred semantics).
    False           Skip filtering; return all raw candidates (for
                    debugging / reproducing legacy behavior).

Each returned record has a 'level' field indicating the level at
which the divergence was triggered (1 = base).
"""
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Internal: raw segmentation
# ─────────────────────────────────────────────────────────────────────────────
def find_hist_segments(hist_series):
    """
    Slice the hist series into consecutive segments by sign.
    Returns list[dict], each dict:
        { 'sign': 'pos'|'neg', 'start': int, 'end': int,
          'area': float, 'bars': int }
    where start / end are inclusive integer indices.
    """
    values = hist_series.values
    n = len(values)
    segments = []
    i = 0
    while i < n:
        v = values[i]
        if np.isnan(v):
            i += 1
            continue
        sign = 'neg' if v < 0 else 'pos'
        j = i
        while j < n and not np.isnan(values[j]) and (
            (values[j] < 0  and sign == 'neg') or
            (values[j] >= 0 and sign == 'pos')
        ):
            j += 1
        area = float(np.nansum(np.abs(values[i:j])))
        segments.append({
            'sign':  sign,
            'start': i,
            'end':   j - 1,
            'area':  area,
            'bars':  j - i,
        })
        i = j
    return segments


# ─────────────────────────────────────────────────────────────────────────────
# Internal: noise merging (no-op when min_bars=0)
# ─────────────────────────────────────────────────────────────────────────────
def _merge_short_segments(segs, noise_sign, host_sign, min_bars):
    """
    Merge any noise_sign segment shorter than min_bars into the adjacent
    host_sign segment. Prefer merging into the left neighbor; fall back
    to the right if the left is unavailable. After merging, adjacent
    same-sign segments are automatically coalesced. Repeat until stable.

    When min_bars<=0, `bars < min_bars` is never true → returns a deep copy.
    """
    result = [dict(s) for s in segs]
    changed = True
    while changed:
        changed = False
        new_result = []
        skip = set()
        for i, seg in enumerate(result):
            if i in skip:
                continue
            if seg['sign'] == noise_sign and seg['bars'] < min_bars:
                left  = new_result[-1]   if new_result          else None
                right = result[i + 1]    if i + 1 < len(result) else None
                if left is not None and left['sign'] == host_sign:
                    left['end']   = seg['end']
                    left['area'] += seg['area']
                    left['bars'] += seg['bars']
                    changed = True
                elif right is not None and right['sign'] == host_sign:
                    rc = dict(right)
                    rc['start']  = seg['start']
                    rc['area']  += seg['area']
                    rc['bars']  += seg['bars']
                    new_result.append(rc)
                    skip.add(i + 1)
                    changed = True
                else:
                    new_result.append(seg)
            else:
                new_result.append(seg)
        result = new_result
        merged = []
        for seg in result:
            if merged and merged[-1]['sign'] == seg['sign']:
                merged[-1]['end']   = seg['end']
                merged[-1]['area'] += seg['area']
                merged[-1]['bars'] += seg['bars']
                changed = True
            else:
                merged.append(seg)
        result = merged
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Internal: hierarchical scan
# ─────────────────────────────────────────────────────────────────────────────
def _scan_levels(segs, p_sign, low_series, high_series,
                 ratio_threshold, max_level, kind, min_bars):
    """
    Scan levels 1..max_level for divergences on `segs` (a strictly
    sign-alternating sequence).

    A k-th-level structure occupies 2k+1 segments:
      - Co-directional segments at offsets 0, 2, 4, ..., 2k-2 (k total)
      - Opposite-direction segments at offsets 1, 3, ..., 2k-1 (k total)
      - The final co-directional segment at offset 2k
        (i.e. S_{2k+1} = "S5/S7/...", denoted S_last below)

    k=1: classic S1 + S2 + S3
    k=2: P₁(S1,S2,S3) + S4 + S5
    k=3: P₂(S1..S5) + S6 + S7
    """
    results = []
    if not segs:
        return results

    upper = max_level if max_level is not None else len(segs)

    for k in range(1, upper + 1):
        window = 2 * k + 1
        if window > len(segs):
            break

        for i in range(len(segs) - window + 1):
            # Check that segs[i:i+window] is strictly sign-alternating.
            block = segs[i:i + window]
            if block[0]['sign'] != p_sign:
                continue
            ok = True
            for j, s in enumerate(block):
                expected = p_sign if (j % 2 == 0) else (
                    'pos' if p_sign == 'neg' else 'neg'
                )
                if s['sign'] != expected:
                    ok = False
                    break
            if not ok:
                # After the merge step, adjacent same-sign segments
                # cannot occur. We still verify explicitly as a safeguard.
                continue

            same_sign_segs = [block[2 * j] for j in range(k)]   # 0,2,...,2k-2
            S_mid_last     = block[2 * k - 1]                   # second-to-last (opposite)
            S_last         = block[2 * k]                       # last (co-directional)

            # min_bars filtering applies only to Level 1 (base three-segment).
            # Higher-level P is composite, so its bar count is naturally
            # large; the internal opposite segments are already guaranteed
            # not to be too short by the merge step above.
            if k == 1 and min(
                same_sign_segs[0]['bars'], S_mid_last['bars'], S_last['bars']
            ) < min_bars:
                continue

            # Area-ratio test: S_last.area / P.area
            P_area = sum(s['area'] for s in same_sign_segs)
            if P_area <= 0:
                continue
            ratio = S_last['area'] / P_area
            if ratio >= ratio_threshold:
                continue

            # New-low / new-high test
            if kind == 'bullish':
                p_low      = min(low_series.iloc[s['start']:s['end'] + 1].min()
                                 for s in same_sign_segs)
                s_last_low = low_series.iloc[S_last['start']:S_last['end'] + 1].min()
                if s_last_low >= p_low:
                    continue
            else:  # bearish
                p_high      = max(high_series.iloc[s['start']:s['end'] + 1].max()
                                  for s in same_sign_segs)
                s_last_high = high_series.iloc[S_last['start']:S_last['end'] + 1].max()
                if s_last_high <= p_high:
                    continue

            # Composite P's span / total bar count (includes internal
            # opposite segments)
            P_start = block[0]['start']
            P_end   = block[2 * k - 2]['end']   # tail of the third-from-last segment
            P_bars  = sum(block[j]['bars'] for j in range(0, 2 * k - 1))

            results.append({
                'kind':     kind,
                'level':    k,
                # s1_*: P's span (at level=1, identical to S1)
                's1_start': P_start,
                's1_end':   P_end,
                # s3_*: the final co-directional segment
                # (at level=1: S3; at level=2: S5)
                's3_start': S_last['start'],
                's3_end':   S_last['end'],
                's1_area':  P_area,
                's3_area':  S_last['area'],
                's1_bars':  P_bars,
                's2_bars':  S_mid_last['bars'],
                's3_bars':  S_last['bars'],
                'ratio':    ratio,
            })

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Internal: opposite-barrier filtering
# ─────────────────────────────────────────────────────────────────────────────
def _filter_by_opposite_barriers(divs):
    """
    Apply the opposite-barrier rule: a divergence D is rejected iff
    there exists a surviving opposite divergence D' satisfying
    (a) D'.s3_end ∈ (D.s1_start, D.s3_end) (trigger point lies strictly
    in D's open span), and (b) D''s highest level at the same terminal
    position (kind, s3_start, s3_end) > 1 (the barrier must be a
    trend-level L≥2 divergence, or share a terminal with an L≥2
    candidate).

    Implementation: process candidates in ascending order of s3_end. Any
    opposite D' that can shield D must satisfy D'.s3_end < D.s3_end
    (it triggered earlier), so by the time we process the earlier-
    triggering candidate, all possible inner barriers are already
    determined. One linear pass suffices.

    L1 as the shielded party still participates
    -------------------------------------------
    An earlier version let level<2 candidates survive unconditionally,
    on the grounds that "a 3-segment r-g-r or g-r-g block has only 1
    opposite-color segment in its open interval, which cannot host an
    opposite divergence". That reasoning conflates "opposite
    divergence" with "the trigger point of an opposite divergence".
    L1's single opposite S2 segment can itself serve as the S_last of
    some L≥2 opposite divergence, and its endpoint is precisely
    that divergence's trigger point s3_end, falling strictly within
    L1's open interval (S1.start, S3.end). This is exactly the case
    the barrier rule is meant to catch: L1's two ends S1 and S3
    belong to two different mechanisms — one before and one after the
    trend switch — and must not be merged into a single P.

    L1 does not act as the barrier
    ------------------------------
    Two adjacent same-level L1 reversed divergences (e.g. an S1+S2+S3
    bullish-L1 immediately followed by an S2+S3+S4 bearish-L1) are the
    canonical "twin-reversal" signal of a market turn and both should
    be kept. This configuration is geometrically symmetric with
    "L1 shielded by L≥2" — the only formal feature distinguishing them
    is level. Condition (b) therefore restricts the barrier to L≥2
    divergences.

    Barrier strength is judged by the "highest level at the terminal"
    -----------------------------------------------------------------
    During structural extension, the same terminal position
    (kind, s3_start, s3_end) may simultaneously trigger both L1 and L≥n
    divergences. The downstream _dedupe_same_terminal treats these
    candidates as different representations of the same divergence and
    keeps only the highest-level record. Barrier judgment here follows
    the same principle: barrier strength is determined by "the highest
    level reached at this position among the raw candidates", not by
    the level of any specific record. So even if the higher-level
    candidate is itself shielded by another barrier, the L1 candidate
    surviving at the same terminal still acts as a barrier at the full
    (highest) strength; conversely, a pure L1 (no higher-level
    candidate at the same terminal) still does not constitute a
    barrier.
    """
    if not divs:
        return divs

    # Pre-compute the highest level reached at each (kind, s3_start, s3_end)
    # terminal position among the raw candidates. Barrier strength is judged
    # from this map, consistent with _dedupe_same_terminal's semantics:
    # multi-level candidates at the same terminal are treated as different
    # representations of the same divergence, judged by the strongest one.
    max_level_at = {}
    for d in divs:
        key = (d['kind'], d['s3_start'], d['s3_end'])
        if d['level'] > max_level_at.get(key, 0):
            max_level_at[key] = d['level']

    # Sort by trigger point (s3_end) ascending; for ties, by level
    # ascending (only for stable ordering)
    sorted_divs = sorted(
        divs,
        key=lambda d: (d['s3_end'], d['level']),
    )

    survivors = []
    for d in sorted_divs:
        blocked = False
        for s in survivors:
            if s['kind'] == d['kind']:
                continue   # Same direction — does not constitute a barrier
            s_key = (s['kind'], s['s3_start'], s['s3_end'])
            if max_level_at.get(s_key, 0) <= 1:
                continue   # Highest level at this terminal is not > 1
                           # → does not constitute a barrier
            # Does s's trigger point lie strictly inside d's open span?
            if d['s1_start'] < s['s3_end'] < d['s3_end']:
                blocked = True
                break

        if not blocked:
            survivors.append(d)

    return survivors


# ─────────────────────────────────────────────────────────────────────────────
# Internal: terminal-segment dedupe
# (trend divergence takes precedence over base three-segment)
# ─────────────────────────────────────────────────────────────────────────────
def _dedupe_same_terminal(divs):
    """
    For records of the same kind that share the same terminal-segment
    position, keep only the highest level.

    Background: on a single S_last, divergences of multiple levels can
    co-trigger. For instance, when L2 triggers, the last 3 segments can
    also constitute an L1 candidate (S1=L2.S3, S3=L2.S5); and because
    L2's price condition S5.low < min(S1.low, S3.low) is strictly
    stronger than that L1's S5.low < S3.low, the terminal-L1's price
    condition is automatically satisfied. But the area-ratio condition
    S_last/S3 < 0.5 is independent — it does not imply, nor is it
    implied by, L2's S_last/(S1+S3) < 0.5 — the previous co-directional
    segment may be either large or small. So whether the terminal L1
    holds independently must be tested separately via S_last/S3.

    Semantically, trend divergence (L≥2) outranks three-segment
    divergence (L=1), and visually we should not stack two percentages
    on the same K-line. So for the same kind and same (s3_start,
    s3_end), we keep only the record of highest level.

    `same_terminal_l1` mark
    -----------------------
    If the merged-out records include an L1 (meaning the terminal L1
    also holds independently — S_last/(prev co-directional segment)
    is also <0.5), the surviving record is annotated with
    same_terminal_l1=True. The UI uses this field to draw a "double
    triangle", indicating "force decay holds simultaneously at
    multiple scales — a stronger signal". If L≥2 triggers but the
    terminal L1 does not (the previous segment is too small,
    S_last/prev > 0.5), then same_terminal_l1=False and a single
    triangle is drawn.
    """
    by_key = {}
    has_l1 = {}        # key -> bool, whether this key has any L1 record
    for d in divs:
        key = (d['kind'], d['s3_start'], d['s3_end'])
        if d['level'] == 1:
            has_l1[key] = True
        if key not in by_key or d['level'] > by_key[key]['level']:
            by_key[key] = d

    out = []
    for key, d in by_key.items():
        d = dict(d)   # avoid mutating the input
        # An L1 itself does not count as "L1 also present" — this mark
        # is for the surviving L≥2 records.
        d['same_terminal_l1'] = bool(has_l1.get(key, False)) and d['level'] >= 2
        out.append(d)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Public main API
# ─────────────────────────────────────────────────────────────────────────────
def find_three_segment_divergences(hist_series, low_series, high_series,
                                   min_bars=0, ratio_threshold=0.5,
                                   max_level=1, block_by_opposite=True):
    """
    Detect three-segment divergence structures on the MACD histogram
    (with hierarchical extension and opposite-barrier filtering).

    Parameters
    ----------
    hist_series       : pd.Series   MACD histogram (positive=green, negative=red)
    low_series        : pd.Series   K-line lows
    high_series       : pd.Series   K-line highs
    min_bars          : int         Minimum bar count per segment
                                    (0 = no merging, no filtering)
    ratio_threshold   : float       Area-ratio threshold (default 0.5)
    max_level         : int|None    Hierarchical extension depth.
                                    1    = base three-segment only
                                           (default, backward-compatible)
                                    2    = also detect P+S4+S5
                                    None = exhaustive
    block_by_opposite : bool        Whether to apply the opposite-barrier
                                    rule (default True). A divergence that
                                    crosses a surviving opposite divergence
                                    D' is rejected when D''s highest level
                                    at its terminal position is ≥2 (a pure
                                    L1 reversed divergence does not act as
                                    a barrier). Set to False to obtain
                                    unfiltered raw candidates.

    Returns
    -------
    list[dict], sorted ascending by (s3_start, level). Each record:
        kind     : 'bullish' | 'bearish'
        level    : Trigger level (1 = base, 2 = P+S4+S5, etc.)
        s1_start : Index where the left-side body begins
                   (at level=1, identical to S1.start)
        s1_end   : Index where the left-side body ends
        s3_start : Index where the right-side latest co-directional
                   segment begins
        s3_end   : Index where the right-side latest co-directional
                   segment ends
        s1_area  : Left-side body area (sum of co-directional members)
        s3_area  : Right-side latest co-directional segment's area
        s1_bars  : Left-side body span (total bars including internal
                   opposite segments)
        s2_bars  : Bar count of the opposite segment immediately before
                   the last co-directional segment
        s3_bars  : Bar count of the right-side latest co-directional
                   segment
        ratio    : s3_area / s1_area
        provisional : bool. True = S_last's right end equals the data's
                     last index, meaning that segment may still extend
                     (a future K-line of the same sign would extend it;
                     only a sign-flip "closes" it). The current ratio
                     and price extreme are a snapshot, not a verdict.
                     The UI uses this flag to switch colors (warning
                     the user). False = a sign-flip has already
                     occurred after S_last; S_last is settled and the
                     signal is final.
        same_terminal_l1 : bool. Only level≥2 records can be True.
                     Semantics: "at this same terminal position, L1
                     also holds independently" — i.e.
                     S_last/(previous co-directional segment) < 0.5
                     (this ratio is independent from the L≥2 ratio
                     S_last/(cumulative previous co-directional area)).
                     Indicates that force decay holds at multiple
                     scales simultaneously — a stronger signal. The
                     UI draws a double triangle when True. Records of
                     level=1 are always False.
    """
    raw_segs = find_hist_segments(hist_series)
    out = []

    # Bullish: P direction = neg
    segs_bull = _merge_short_segments(raw_segs, 'neg', 'pos', min_bars)
    out.extend(_scan_levels(segs_bull, 'neg', low_series, high_series,
                            ratio_threshold, max_level,
                            kind='bullish', min_bars=min_bars))

    # Bearish: P direction = pos
    segs_bear = _merge_short_segments(raw_segs, 'pos', 'neg', min_bars)
    out.extend(_scan_levels(segs_bear, 'pos', low_series, high_series,
                            ratio_threshold, max_level,
                            kind='bearish', min_bars=min_bars))

    # Mark "incomplete / provisional":
    # if S_last's right end equals the last index of hist, the segment
    # may still extend (future K-lines of the same sign would extend it;
    # only a sign-flip closes it). The current ratio is a snapshot, not
    # a verdict. The UI uses this flag to switch colors (dodger blue +
    # "?" suffix) to warn the user.
    last_index = len(hist_series) - 1
    for d in out:
        d['provisional'] = (d['s3_end'] == last_index)

    # Opposite-barrier filtering
    if block_by_opposite:
        out = _filter_by_opposite_barriers(out)

    # Terminal-segment dedupe: for same kind and same (s3_start,
    # s3_end), keep only the record of highest level. Trend divergence
    # (L≥2) takes precedence over three-segment divergence (L=1). We
    # dedupe AFTER barrier filtering — so that when L≥2 is rejected by
    # a barrier, the L1 at the same position can still be retained.
    # If during dedupe we find an L1 also held independently at the
    # same position, mark same_terminal_l1=True on the surviving
    # record; the UI uses this to draw a double triangle (force decay
    # at multiple scales).
    out = _dedupe_same_terminal(out)

    out.sort(key=lambda d: (d['s3_start'], d['level']))
    return out
