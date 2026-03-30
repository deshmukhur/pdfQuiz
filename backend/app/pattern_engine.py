"""Candlestick pattern detection engine.

Detects all single, double, and triple candlestick patterns plus multi-bar
chart patterns. Each pattern returns direction (bullish/bearish) and
confidence (low/medium/high). Volume confirmation is applied as a multiplier.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

TOLERANCE = 0.001  # 0.1% tolerance for comparisons


def detect_all_patterns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect all candlestick and chart patterns on the most recent candles.

    Args:
        df: OHLCV DataFrame sorted by time ascending. Needs at least 5 rows.

    Returns:
        List of detected pattern dicts with keys: name, direction, confidence, index.
    """
    if df is None or len(df) < 3:
        return []

    patterns: List[Dict[str, Any]] = []
    o = df["open"].astype(float).values
    h = df["high"].astype(float).values
    l = df["low"].astype(float).values
    c = df["close"].astype(float).values
    v = df["volume"].astype(float).values if "volume" in df.columns else np.ones(len(df))

    # Volume average for confirmation
    vol_avg = np.mean(v[-20:]) if len(v) >= 20 else np.mean(v)

    # Helper functions
    def body(i: int) -> float:
        return abs(c[i] - o[i])

    def upper_shadow(i: int) -> float:
        return h[i] - max(o[i], c[i])

    def lower_shadow(i: int) -> float:
        return min(o[i], c[i]) - l[i]

    def total_range(i: int) -> float:
        return h[i] - l[i]

    def is_bullish(i: int) -> bool:
        return c[i] > o[i]

    def is_bearish(i: int) -> bool:
        return c[i] < o[i]

    def is_doji(i: int) -> bool:
        tr = total_range(i)
        return tr > 0 and body(i) / tr < 0.10

    def in_downtrend(end_idx: int, lookback: int = 3) -> bool:
        start = max(0, end_idx - lookback)
        if start >= end_idx:
            return False
        return c[start] > c[end_idx]

    def in_uptrend(end_idx: int, lookback: int = 3) -> bool:
        start = max(0, end_idx - lookback)
        if start >= end_idx:
            return False
        return c[start] < c[end_idx]

    def vol_confirm(i: int) -> str:
        if vol_avg == 0:
            return "medium"
        ratio = v[i] / vol_avg
        if ratio >= 2.0:
            return "high"
        elif ratio >= 1.0:
            return "medium"
        return "low"

    idx = len(o) - 1  # most recent candle index
    if idx < 0:
        return []

    # ─── SINGLE CANDLESTICK PATTERNS ────────────────────────────────

    # Marubozu
    if total_range(idx) > 0:
        us_ratio = upper_shadow(idx) / total_range(idx)
        ls_ratio = lower_shadow(idx) / total_range(idx)
        if us_ratio < TOLERANCE and ls_ratio < TOLERANCE:
            if is_bullish(idx):
                patterns.append({"name": "Bullish Marubozu", "direction": "bullish", "confidence": vol_confirm(idx)})
            else:
                patterns.append({"name": "Bearish Marubozu", "direction": "bearish", "confidence": vol_confirm(idx)})

    # Hammer
    if total_range(idx) > 0 and body(idx) > 0:
        if lower_shadow(idx) >= 2 * body(idx) and upper_shadow(idx) <= body(idx) * 0.3:
            if in_downtrend(idx):
                patterns.append({"name": "Hammer", "direction": "bullish", "confidence": vol_confirm(idx)})

    # Hanging Man
    if total_range(idx) > 0 and body(idx) > 0:
        if lower_shadow(idx) >= 2 * body(idx) and upper_shadow(idx) <= body(idx) * 0.3:
            if in_uptrend(idx):
                patterns.append({"name": "Hanging Man", "direction": "bearish", "confidence": vol_confirm(idx)})

    # Inverted Hammer
    if total_range(idx) > 0 and body(idx) > 0:
        if upper_shadow(idx) >= 2 * body(idx) and lower_shadow(idx) <= body(idx) * 0.3:
            if in_downtrend(idx):
                patterns.append({"name": "Inverted Hammer", "direction": "bullish", "confidence": "low"})

    # Shooting Star
    if total_range(idx) > 0 and body(idx) > 0:
        if upper_shadow(idx) >= 2 * body(idx) and lower_shadow(idx) <= body(idx) * 0.3:
            if in_uptrend(idx):
                patterns.append({"name": "Shooting Star", "direction": "bearish", "confidence": vol_confirm(idx)})

    # Doji variants
    if is_doji(idx) and total_range(idx) > 0:
        us = upper_shadow(idx)
        ls = lower_shadow(idx)
        tr = total_range(idx)

        if ls > 0.6 * tr and us < 0.1 * tr:
            # Dragonfly Doji
            direction = "bullish" if in_downtrend(idx) else "neutral"
            patterns.append({"name": "Dragonfly Doji", "direction": direction, "confidence": "medium"})
        elif us > 0.6 * tr and ls < 0.1 * tr:
            # Gravestone Doji
            direction = "bearish" if in_uptrend(idx) else "neutral"
            patterns.append({"name": "Gravestone Doji", "direction": direction, "confidence": "medium"})
        elif us > 0.3 * tr and ls > 0.3 * tr:
            patterns.append({"name": "Long-Legged Doji", "direction": "neutral", "confidence": "low"})
        else:
            patterns.append({"name": "Doji", "direction": "neutral", "confidence": "low"})

    # Spinning Top
    if total_range(idx) > 0 and not is_doji(idx):
        b = body(idx)
        tr = total_range(idx)
        if 0.10 <= b / tr <= 0.35 and upper_shadow(idx) > b and lower_shadow(idx) > b:
            patterns.append({"name": "Spinning Top", "direction": "neutral", "confidence": "low"})

    # Belt Hold
    if total_range(idx) > 0 and body(idx) > 0.6 * total_range(idx):
        if is_bullish(idx) and lower_shadow(idx) < TOLERANCE * total_range(idx) and in_downtrend(idx):
            patterns.append({"name": "Belt Hold Bullish", "direction": "bullish", "confidence": "medium"})
        elif is_bearish(idx) and upper_shadow(idx) < TOLERANCE * total_range(idx) and in_uptrend(idx):
            patterns.append({"name": "Belt Hold Bearish", "direction": "bearish", "confidence": "medium"})

    # ─── DOUBLE CANDLESTICK PATTERNS ────────────────────────────────

    if idx >= 1:
        prev = idx - 1

        # Bullish Engulfing
        if is_bearish(prev) and is_bullish(idx):
            if o[idx] <= c[prev] and c[idx] >= o[prev]:
                if body(idx) > body(prev) and in_downtrend(prev):
                    conf = "high" if v[idx] > vol_avg * 1.5 else vol_confirm(idx)
                    patterns.append({"name": "Bullish Engulfing", "direction": "bullish", "confidence": conf})

        # Bearish Engulfing
        if is_bullish(prev) and is_bearish(idx):
            if o[idx] >= c[prev] and c[idx] <= o[prev]:
                if body(idx) > body(prev) and in_uptrend(prev):
                    conf = "high" if v[idx] > vol_avg * 1.5 else vol_confirm(idx)
                    patterns.append({"name": "Bearish Engulfing", "direction": "bearish", "confidence": conf})

        # Bullish Harami
        if is_bearish(prev) and is_bullish(idx):
            if body(idx) < body(prev) and c[idx] < o[prev] and o[idx] > c[prev]:
                if in_downtrend(prev):
                    patterns.append({"name": "Bullish Harami", "direction": "bullish", "confidence": "medium"})

        # Bearish Harami
        if is_bullish(prev) and is_bearish(idx):
            if body(idx) < body(prev) and c[idx] > o[prev] and o[idx] < c[prev]:
                if in_uptrend(prev):
                    patterns.append({"name": "Bearish Harami", "direction": "bearish", "confidence": "medium"})

        # Harami Cross
        if is_doji(idx):
            if is_bearish(prev) and max(o[idx], c[idx]) < o[prev] and min(o[idx], c[idx]) > c[prev]:
                if in_downtrend(prev):
                    patterns.append({"name": "Bullish Harami Cross", "direction": "bullish", "confidence": "high"})
            elif is_bullish(prev) and max(o[idx], c[idx]) < c[prev] and min(o[idx], c[idx]) > o[prev]:
                if in_uptrend(prev):
                    patterns.append({"name": "Bearish Harami Cross", "direction": "bearish", "confidence": "high"})

        # Piercing Line
        if is_bearish(prev) and is_bullish(idx):
            midpoint = (o[prev] + c[prev]) / 2
            if o[idx] < l[prev] and c[idx] > midpoint and c[idx] < o[prev]:
                if in_downtrend(prev):
                    patterns.append({"name": "Piercing Line", "direction": "bullish", "confidence": vol_confirm(idx)})

        # Dark Cloud Cover
        if is_bullish(prev) and is_bearish(idx):
            midpoint = (o[prev] + c[prev]) / 2
            if o[idx] > h[prev] and c[idx] < midpoint and c[idx] > o[prev]:
                if in_uptrend(prev):
                    patterns.append({"name": "Dark Cloud Cover", "direction": "bearish", "confidence": vol_confirm(idx)})

        # Tweezer Top
        if abs(h[prev] - h[idx]) / max(h[prev], 0.01) < 0.002:
            if is_bullish(prev) and is_bearish(idx) and in_uptrend(prev):
                patterns.append({"name": "Tweezer Top", "direction": "bearish", "confidence": "medium"})

        # Tweezer Bottom
        if abs(l[prev] - l[idx]) / max(l[prev], 0.01) < 0.002:
            if is_bearish(prev) and is_bullish(idx) and in_downtrend(prev):
                patterns.append({"name": "Tweezer Bottom", "direction": "bullish", "confidence": "medium"})

        # Kicker Bullish
        if is_bearish(prev) and is_bullish(idx):
            gap = (o[idx] - o[prev]) / max(o[prev], 0.01) * 100
            if gap >= 1.0:
                patterns.append({"name": "Kicker Bullish", "direction": "bullish", "confidence": "high"})

        # Kicker Bearish
        if is_bullish(prev) and is_bearish(idx):
            gap = (o[prev] - o[idx]) / max(o[prev], 0.01) * 100
            if gap >= 1.0:
                patterns.append({"name": "Kicker Bearish", "direction": "bearish", "confidence": "high"})

    # ─── TRIPLE CANDLESTICK PATTERNS ────────────────────────────────

    if idx >= 2:
        i0, i1, i2 = idx - 2, idx - 1, idx

        # Morning Star
        if is_bearish(i0) and body(i0) > 0.5 * total_range(i0):
            if body(i1) < body(i0) * 0.3:
                if is_bullish(i2) and c[i2] > (o[i0] + c[i0]) / 2:
                    if in_downtrend(i0):
                        patterns.append({"name": "Morning Star", "direction": "bullish", "confidence": vol_confirm(i2)})

        # Evening Star
        if is_bullish(i0) and body(i0) > 0.5 * total_range(i0):
            if body(i1) < body(i0) * 0.3:
                if is_bearish(i2) and c[i2] < (o[i0] + c[i0]) / 2:
                    if in_uptrend(i0):
                        patterns.append({"name": "Evening Star", "direction": "bearish", "confidence": vol_confirm(i2)})

        # Morning Doji Star
        if is_bearish(i0) and is_doji(i1) and is_bullish(i2):
            if c[i2] > (o[i0] + c[i0]) / 2 and in_downtrend(i0):
                patterns.append({"name": "Morning Doji Star", "direction": "bullish", "confidence": "high"})

        # Evening Doji Star
        if is_bullish(i0) and is_doji(i1) and is_bearish(i2):
            if c[i2] < (o[i0] + c[i0]) / 2 and in_uptrend(i0):
                patterns.append({"name": "Evening Doji Star", "direction": "bearish", "confidence": "high"})

        # Three White Soldiers
        if all(is_bullish(j) for j in [i0, i1, i2]):
            if c[i1] > c[i0] and c[i2] > c[i1]:
                if o[i1] > o[i0] and o[i2] > o[i1]:
                    if all(body(j) > 0.5 * total_range(j) for j in [i0, i1, i2]):
                        patterns.append({"name": "Three White Soldiers", "direction": "bullish", "confidence": "high"})

        # Three Black Crows
        if all(is_bearish(j) for j in [i0, i1, i2]):
            if c[i1] < c[i0] and c[i2] < c[i1]:
                if o[i1] < o[i0] and o[i2] < o[i1]:
                    if all(body(j) > 0.5 * total_range(j) for j in [i0, i1, i2]):
                        patterns.append({"name": "Three Black Crows", "direction": "bearish", "confidence": "high"})

        # Three Inside Up
        if is_bearish(i0) and is_bullish(i1):
            if body(i1) < body(i0) and c[i1] < o[i0] and o[i1] > c[i0]:
                if is_bullish(i2) and c[i2] > o[i0]:
                    patterns.append({"name": "Three Inside Up", "direction": "bullish", "confidence": "high"})

        # Three Inside Down
        if is_bullish(i0) and is_bearish(i1):
            if body(i1) < body(i0) and c[i1] > o[i0] and o[i1] < c[i0]:
                if is_bearish(i2) and c[i2] < o[i0]:
                    patterns.append({"name": "Three Inside Down", "direction": "bearish", "confidence": "high"})

        # Abandoned Baby Bullish
        if is_bearish(i0) and is_doji(i1) and is_bullish(i2):
            if h[i1] < l[i0] and l[i1] > 0 and l[i2] > h[i1]:
                patterns.append({"name": "Abandoned Baby Bullish", "direction": "bullish", "confidence": "high"})

        # Abandoned Baby Bearish
        if is_bullish(i0) and is_doji(i1) and is_bearish(i2):
            if l[i1] > h[i0] and h[i2] < l[i1]:
                patterns.append({"name": "Abandoned Baby Bearish", "direction": "bearish", "confidence": "high"})

        # Advance Block
        if all(is_bullish(j) for j in [i0, i1, i2]):
            if body(i1) < body(i0) and body(i2) < body(i1):
                if upper_shadow(i2) > upper_shadow(i1) > upper_shadow(i0):
                    patterns.append({"name": "Advance Block", "direction": "bearish", "confidence": "medium"})

    # ─── MULTI-BAR CHART PATTERNS ───────────────────────────────────

    if len(df) >= 20:
        chart_patterns = _detect_chart_patterns(h, l, c, v)
        patterns.extend(chart_patterns)

    return patterns


def _detect_chart_patterns(
    h: np.ndarray, l: np.ndarray, c: np.ndarray, v: np.ndarray,
) -> List[Dict[str, Any]]:
    """Detect multi-bar chart patterns like triangles, head-and-shoulders, etc."""
    patterns = []
    n = len(c)
    if n < 20:
        return patterns

    # Use recent 50 bars for pattern detection
    lookback = min(50, n)
    recent_h = h[-lookback:]
    recent_l = l[-lookback:]
    recent_c = c[-lookback:]

    # Find local peaks and troughs (simple zigzag)
    peaks = []
    troughs = []
    for i in range(2, len(recent_c) - 2):
        if recent_h[i] >= recent_h[i - 1] and recent_h[i] >= recent_h[i - 2] and \
           recent_h[i] >= recent_h[i + 1] and recent_h[i] >= recent_h[i + 2]:
            peaks.append((i, recent_h[i]))
        if recent_l[i] <= recent_l[i - 1] and recent_l[i] <= recent_l[i - 2] and \
           recent_l[i] <= recent_l[i + 1] and recent_l[i] <= recent_l[i + 2]:
            troughs.append((i, recent_l[i]))

    # Double Top
    if len(peaks) >= 2:
        p1, p2 = peaks[-2], peaks[-1]
        if abs(p1[1] - p2[1]) / max(p1[1], 0.01) < 0.02:  # tops within 2%
            if p2[0] - p1[0] >= 5:
                patterns.append({"name": "Double Top", "direction": "bearish", "confidence": "medium"})

    # Double Bottom
    if len(troughs) >= 2:
        t1, t2 = troughs[-2], troughs[-1]
        if abs(t1[1] - t2[1]) / max(t1[1], 0.01) < 0.02:
            if t2[0] - t1[0] >= 5:
                patterns.append({"name": "Double Bottom", "direction": "bullish", "confidence": "medium"})

    # Head and Shoulders
    if len(peaks) >= 3 and len(troughs) >= 2:
        left, head, right = peaks[-3], peaks[-2], peaks[-1]
        if head[1] > left[1] and head[1] > right[1]:
            if abs(left[1] - right[1]) / max(left[1], 0.01) < 0.05:
                patterns.append({"name": "Head and Shoulders", "direction": "bearish", "confidence": "high"})

    # Inverse Head and Shoulders
    if len(troughs) >= 3 and len(peaks) >= 2:
        left, head, right = troughs[-3], troughs[-2], troughs[-1]
        if head[1] < left[1] and head[1] < right[1]:
            if abs(left[1] - right[1]) / max(left[1], 0.01) < 0.05:
                patterns.append({"name": "Inverse Head and Shoulders", "direction": "bullish", "confidence": "high"})

    # Ascending Triangle (higher lows, flat highs)
    if len(peaks) >= 2 and len(troughs) >= 2:
        flat_highs = abs(peaks[-1][1] - peaks[-2][1]) / max(peaks[-1][1], 0.01) < 0.01
        rising_lows = troughs[-1][1] > troughs[-2][1]
        if flat_highs and rising_lows:
            patterns.append({"name": "Ascending Triangle", "direction": "bullish", "confidence": "medium"})

    # Descending Triangle
    if len(peaks) >= 2 and len(troughs) >= 2:
        falling_highs = peaks[-1][1] < peaks[-2][1]
        flat_lows = abs(troughs[-1][1] - troughs[-2][1]) / max(troughs[-1][1], 0.01) < 0.01
        if falling_highs and flat_lows:
            patterns.append({"name": "Descending Triangle", "direction": "bearish", "confidence": "medium"})

    # Symmetrical Triangle
    if len(peaks) >= 2 and len(troughs) >= 2:
        lower_highs = peaks[-1][1] < peaks[-2][1]
        higher_lows = troughs[-1][1] > troughs[-2][1]
        if lower_highs and higher_lows:
            patterns.append({"name": "Symmetrical Triangle", "direction": "neutral", "confidence": "medium"})

    # Rising Wedge
    if len(peaks) >= 2 and len(troughs) >= 2:
        if peaks[-1][1] > peaks[-2][1] and troughs[-1][1] > troughs[-2][1]:
            high_slope = peaks[-1][1] - peaks[-2][1]
            low_slope = troughs[-1][1] - troughs[-2][1]
            if high_slope < low_slope:  # converging
                patterns.append({"name": "Rising Wedge", "direction": "bearish", "confidence": "medium"})

    # Falling Wedge
    if len(peaks) >= 2 and len(troughs) >= 2:
        if peaks[-1][1] < peaks[-2][1] and troughs[-1][1] < troughs[-2][1]:
            high_slope = abs(peaks[-1][1] - peaks[-2][1])
            low_slope = abs(troughs[-1][1] - troughs[-2][1])
            if high_slope > low_slope:
                patterns.append({"name": "Falling Wedge", "direction": "bullish", "confidence": "medium"})

    return patterns
