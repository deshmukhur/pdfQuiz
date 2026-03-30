"""Scoring engine that combines indicator values and patterns into a composite score.

Score ranges from -100 (extreme sell) to +100 (extreme buy).
Weights: Trend 30%, Momentum 25%, Volume 20%, Patterns 15%, Support/Resistance 10%.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default category weights
DEFAULT_WEIGHTS = {
    "trend": 0.30,
    "momentum": 0.25,
    "volume": 0.20,
    "patterns": 0.15,
    "support_resistance": 0.10,
}

SIGNAL_THRESHOLDS = {
    "STRONG_BUY": 70,
    "BUY": 40,
    "WEAK_BUY": 10,
    "NEUTRAL_HIGH": 10,
    "NEUTRAL_LOW": -10,
    "WEAK_SELL": -10,
    "SELL": -40,
    "STRONG_SELL": -70,
}


def classify_signal(score: float) -> str:
    """Classify a score into a signal label."""
    if score >= 70:
        return "STRONG_BUY"
    elif score >= 40:
        return "BUY"
    elif score >= 10:
        return "WEAK_BUY"
    elif score >= -10:
        return "NEUTRAL"
    elif score >= -40:
        return "WEAK_SELL"
    elif score >= -70:
        return "SELL"
    else:
        return "STRONG_SELL"


def compute_score(
    indicators: Dict[str, Any],
    patterns: List[Dict[str, Any]],
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Compute composite score from indicators and patterns.

    Returns:
        Dict with keys: score, signal, stop_loss, target_1, target_2, target_3,
        reasoning, score_breakdown.
    """
    w = weights or DEFAULT_WEIGHTS
    breakdown: Dict[str, Any] = {}

    # ─── TREND SIGNALS (weight 30%) ─────────────────────────────────
    trend_signals = []

    # EMA alignment
    ema_9 = indicators.get("ema_9")
    ema_20 = indicators.get("ema_20")
    ema_50 = indicators.get("ema_50")
    ema_200 = indicators.get("ema_200")

    if all(v is not None for v in [ema_9, ema_20, ema_50, ema_200]):
        if ema_9 > ema_20 > ema_50 > ema_200:
            trend_signals.append(("EMA Alignment", 10, "Strong uptrend: EMA 9 > 20 > 50 > 200"))
        elif ema_9 < ema_20 < ema_50 < ema_200:
            trend_signals.append(("EMA Alignment", -10, "Strong downtrend: EMA 9 < 20 < 50 < 200"))
        elif ema_9 > ema_20:
            trend_signals.append(("EMA Alignment", 4, "Short-term bullish: EMA 9 > 20"))
        elif ema_9 < ema_20:
            trend_signals.append(("EMA Alignment", -4, "Short-term bearish: EMA 9 < 20"))
        else:
            trend_signals.append(("EMA Alignment", 0, "Neutral"))

    # Supertrend
    st_dir = indicators.get("supertrend_direction")
    if st_dir is not None:
        if st_dir:
            trend_signals.append(("Supertrend", 8, "Bullish supertrend"))
        else:
            trend_signals.append(("Supertrend", -8, "Bearish supertrend"))

    # ADX
    adx = indicators.get("adx")
    plus_di = indicators.get("plus_di")
    minus_di = indicators.get("minus_di")
    if adx is not None:
        if adx > 25 and plus_di is not None and minus_di is not None:
            if plus_di > minus_di:
                trend_signals.append(("ADX", 7, f"Strong bullish trend (ADX={adx:.1f})"))
            else:
                trend_signals.append(("ADX", -7, f"Strong bearish trend (ADX={adx:.1f})"))
        elif adx < 20:
            trend_signals.append(("ADX", 0, f"No trend (ADX={adx:.1f})"))
        else:
            trend_signals.append(("ADX", 2 if (plus_di or 0) > (minus_di or 0) else -2, f"Emerging trend (ADX={adx:.1f})"))

    # Parabolic SAR
    sar_dir = indicators.get("parabolic_sar_direction")
    if sar_dir is not None:
        if sar_dir == "bullish":
            trend_signals.append(("Parabolic SAR", 5, "SAR below price (bullish)"))
        else:
            trend_signals.append(("Parabolic SAR", -5, "SAR above price (bearish)"))

    trend_avg = _avg_signals(trend_signals)
    breakdown["trend"] = {"score": trend_avg, "signals": [(s[0], s[1], s[2]) for s in trend_signals]}

    # ─── MOMENTUM SIGNALS (weight 25%) ──────────────────────────────
    momentum_signals = []

    # RSI
    rsi = indicators.get("rsi")
    if rsi is not None:
        if rsi < 30:
            momentum_signals.append(("RSI", 8, f"Oversold (RSI={rsi:.1f})"))
        elif rsi < 40:
            momentum_signals.append(("RSI", 4, f"Approaching oversold (RSI={rsi:.1f})"))
        elif rsi > 70:
            momentum_signals.append(("RSI", -8, f"Overbought (RSI={rsi:.1f})"))
        elif rsi > 60:
            momentum_signals.append(("RSI", -4, f"Approaching overbought (RSI={rsi:.1f})"))
        else:
            momentum_signals.append(("RSI", 0, f"Neutral (RSI={rsi:.1f})"))

    # MACD
    macd_line = indicators.get("macd_line")
    macd_signal = indicators.get("macd_signal")
    macd_hist = indicators.get("macd_hist")
    if all(v is not None for v in [macd_line, macd_signal, macd_hist]):
        if macd_line > macd_signal and macd_hist > 0:
            momentum_signals.append(("MACD", 8, "MACD bullish crossover, histogram positive"))
        elif macd_line > macd_signal:
            momentum_signals.append(("MACD", 4, "MACD above signal"))
        elif macd_line < macd_signal and macd_hist < 0:
            momentum_signals.append(("MACD", -8, "MACD bearish crossover, histogram negative"))
        elif macd_line < macd_signal:
            momentum_signals.append(("MACD", -4, "MACD below signal"))
        else:
            momentum_signals.append(("MACD", 0, "MACD neutral"))

    # Stochastic
    stoch_k = indicators.get("stoch_k")
    stoch_d = indicators.get("stoch_d")
    if stoch_k is not None and stoch_d is not None:
        if stoch_k < 20 and stoch_k > stoch_d:
            momentum_signals.append(("Stochastic", 7, "Oversold with bullish crossover"))
        elif stoch_k < 20:
            momentum_signals.append(("Stochastic", 5, "Oversold"))
        elif stoch_k > 80 and stoch_k < stoch_d:
            momentum_signals.append(("Stochastic", -7, "Overbought with bearish crossover"))
        elif stoch_k > 80:
            momentum_signals.append(("Stochastic", -5, "Overbought"))
        else:
            momentum_signals.append(("Stochastic", 0, "Neutral"))

    # CCI
    cci = indicators.get("cci")
    if cci is not None:
        if cci > 100:
            momentum_signals.append(("CCI", -5, f"Strongly trending up (CCI={cci:.1f})"))
        elif cci < -100:
            momentum_signals.append(("CCI", 5, f"Strongly trending down (CCI={cci:.1f})"))
        else:
            momentum_signals.append(("CCI", 0, f"Neutral (CCI={cci:.1f})"))

    # Williams %R
    wr = indicators.get("williams_r")
    if wr is not None:
        if wr > -20:
            momentum_signals.append(("Williams %R", -5, f"Overbought (W%R={wr:.1f})"))
        elif wr < -80:
            momentum_signals.append(("Williams %R", 5, f"Oversold (W%R={wr:.1f})"))
        else:
            momentum_signals.append(("Williams %R", 0, f"Neutral (W%R={wr:.1f})"))

    momentum_avg = _avg_signals(momentum_signals)
    breakdown["momentum"] = {"score": momentum_avg, "signals": [(s[0], s[1], s[2]) for s in momentum_signals]}

    # ─── VOLUME SIGNALS (weight 20%) ────────────────────────────────
    volume_signals = []

    # OBV trend
    obv = indicators.get("obv")
    if obv is not None:
        if obv > 0:
            volume_signals.append(("OBV", 5, "Positive OBV (accumulation)"))
        else:
            volume_signals.append(("OBV", -5, "Negative OBV (distribution)"))

    # CMF
    cmf = indicators.get("cmf")
    if cmf is not None:
        if cmf > 0.1:
            volume_signals.append(("CMF", 7, f"Strong buying pressure (CMF={cmf:.3f})"))
        elif cmf > 0:
            volume_signals.append(("CMF", 3, f"Mild buying pressure (CMF={cmf:.3f})"))
        elif cmf < -0.1:
            volume_signals.append(("CMF", -7, f"Strong selling pressure (CMF={cmf:.3f})"))
        elif cmf < 0:
            volume_signals.append(("CMF", -3, f"Mild selling pressure (CMF={cmf:.3f})"))

    # MFI
    mfi = indicators.get("mfi")
    if mfi is not None:
        if mfi < 20:
            volume_signals.append(("MFI", 7, f"MFI oversold ({mfi:.1f})"))
        elif mfi > 80:
            volume_signals.append(("MFI", -7, f"MFI overbought ({mfi:.1f})"))
        else:
            volume_signals.append(("MFI", 0, f"MFI neutral ({mfi:.1f})"))

    # Volume ratio
    vol_ratio = indicators.get("volume_ratio")
    if vol_ratio is not None:
        if vol_ratio >= 2.0:
            volume_signals.append(("Volume", 6, f"High volume ({vol_ratio:.1f}x avg)"))
        elif vol_ratio >= 1.5:
            volume_signals.append(("Volume", 3, f"Above average volume ({vol_ratio:.1f}x)"))
        elif vol_ratio < 0.5:
            volume_signals.append(("Volume", -2, f"Very low volume ({vol_ratio:.1f}x avg)"))

    volume_avg = _avg_signals(volume_signals)
    breakdown["volume"] = {"score": volume_avg, "signals": [(s[0], s[1], s[2]) for s in volume_signals]}

    # ─── PATTERN SIGNALS (weight 15%) ───────────────────────────────
    pattern_signals = []
    confidence_multiplier = {"high": 1.0, "medium": 0.7, "low": 0.4}

    for p in patterns:
        name = p.get("name", "")
        direction = p.get("direction", "neutral")
        confidence = p.get("confidence", "medium")
        mult = confidence_multiplier.get(confidence, 0.7)

        if direction == "bullish":
            base = 8 if confidence == "high" else 5
            score_val = base * mult
            pattern_signals.append((name, score_val, f"Bullish pattern ({confidence} confidence)"))
        elif direction == "bearish":
            base = -8 if confidence == "high" else -5
            score_val = base * mult
            pattern_signals.append((name, score_val, f"Bearish pattern ({confidence} confidence)"))
        else:
            pattern_signals.append((name, 0, f"Neutral pattern"))

    pattern_avg = _avg_signals(pattern_signals) if pattern_signals else 0
    breakdown["patterns"] = {"score": pattern_avg, "signals": [(s[0], s[1], s[2]) for s in pattern_signals]}

    # ─── SUPPORT/RESISTANCE (weight 10%) ────────────────────────────
    sr_signals = []

    # Price near pivot support
    pivot_s1 = indicators.get("pivot_s1")
    pivot_r1 = indicators.get("pivot_r1")
    close_price = indicators.get("ema_9")  # proxy for current price

    if close_price and pivot_s1:
        dist_s1 = (close_price - pivot_s1) / close_price * 100
        if 0 < dist_s1 < 1.0:
            sr_signals.append(("Pivot S1", 6, f"Price near support S1 ({dist_s1:.2f}% above)"))

    if close_price and pivot_r1:
        dist_r1 = (pivot_r1 - close_price) / close_price * 100
        if 0 < dist_r1 < 1.0:
            sr_signals.append(("Pivot R1", -4, f"Price near resistance R1 ({dist_r1:.2f}% below)"))

    # Fibonacci support
    fib_618 = indicators.get("fib_618")
    if close_price and fib_618:
        dist_fib = abs(close_price - fib_618) / close_price * 100
        if dist_fib < 1.0:
            sr_signals.append(("Fib 61.8%", 5, "Price at golden ratio retracement"))

    # Bollinger Band position
    bb_upper = indicators.get("bb_upper")
    bb_lower = indicators.get("bb_lower")
    if close_price and bb_upper and bb_lower:
        if close_price >= bb_upper:
            sr_signals.append(("Bollinger Upper", -5, "Price at upper Bollinger Band"))
        elif close_price <= bb_lower:
            sr_signals.append(("Bollinger Lower", 5, "Price at lower Bollinger Band"))

    sr_avg = _avg_signals(sr_signals) if sr_signals else 0
    breakdown["support_resistance"] = {"score": sr_avg, "signals": [(s[0], s[1], s[2]) for s in sr_signals]}

    # ─── COMPOSITE SCORE ────────────────────────────────────────────
    total_score = (
        trend_avg * w["trend"]
        + momentum_avg * w["momentum"]
        + volume_avg * w["volume"]
        + pattern_avg * w["patterns"]
        + sr_avg * w["support_resistance"]
    ) * 10  # Scale to -100..+100 range

    total_score = max(-100, min(100, total_score))
    signal = classify_signal(total_score)

    # ─── STOP LOSS & TARGETS ────────────────────────────────────────
    atr = indicators.get("atr")
    entry_price = close_price or 0

    stop_loss = None
    target_1 = None
    target_2 = None
    target_3 = None

    if atr and entry_price:
        if total_score > 0:  # Buy signal
            stop_loss = entry_price - 1.5 * atr
            # Use strong support if closer
            if pivot_s1 and pivot_s1 > stop_loss and pivot_s1 < entry_price:
                stop_loss = pivot_s1
            target_1 = entry_price + 1.0 * atr
            target_2 = entry_price + 2.0 * atr
            target_3 = pivot_r1 if pivot_r1 and pivot_r1 > target_2 else entry_price + 3.0 * atr
        elif total_score < 0:  # Sell signal
            stop_loss = entry_price + 1.5 * atr
            if pivot_r1 and pivot_r1 < stop_loss and pivot_r1 > entry_price:
                stop_loss = pivot_r1
            target_1 = entry_price - 1.0 * atr
            target_2 = entry_price - 2.0 * atr
            target_3 = pivot_s1 if pivot_s1 and pivot_s1 < target_2 else entry_price - 3.0 * atr

    # Risk-reward filter
    rr_valid = True
    if total_score > 0 and stop_loss and target_1:
        risk = entry_price - stop_loss
        reward = target_1 - entry_price
        if risk > 0:
            rr_ratio = reward / risk
            if rr_ratio < 1.5:
                rr_valid = False

    # Key reasoning summary
    top_reasons = []
    for cat_name, cat_data in breakdown.items():
        for sig in cat_data.get("signals", []):
            if abs(sig[1]) >= 5:
                top_reasons.append(sig[2])

    return {
        "score": round(total_score, 2),
        "signal": signal,
        "stop_loss": round(stop_loss, 2) if stop_loss else None,
        "target_1": round(target_1, 2) if target_1 else None,
        "target_2": round(target_2, 2) if target_2 else None,
        "target_3": round(target_3, 2) if target_3 else None,
        "entry_price": round(entry_price, 2) if entry_price else None,
        "risk_reward_valid": rr_valid,
        "reasoning": {
            "summary": "; ".join(top_reasons[:5]) if top_reasons else "No strong signals",
            "details": top_reasons,
        },
        "score_breakdown": breakdown,
        "detected_patterns": [p["name"] for p in patterns],
    }


def _avg_signals(signals: List[tuple]) -> float:
    """Average the signal values in a list of (name, value, reason) tuples."""
    if not signals:
        return 0.0
    return sum(s[1] for s in signals) / len(signals)
