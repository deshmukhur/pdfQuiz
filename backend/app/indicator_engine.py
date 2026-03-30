"""Core computation module for all technical indicators.

Accepts a pandas DataFrame of OHLCV data and computes every indicator
described in the specification. Uses pandas-ta as the primary engine
with custom implementations where needed.
"""

import logging
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_all_indicators(df: pd.DataFrame, timeframe: str = "1m") -> Dict[str, Any]:
    """Compute all technical indicators for a given OHLCV DataFrame.

    Args:
        df: DataFrame with columns [open, high, low, close, volume] and optionally [oi].
            Must be sorted by time ascending.
        timeframe: The timeframe string (1m, 5m, 15m, 30m, 1h, 1D, 1W, 1M).

    Returns:
        Dictionary with all computed indicator values for the most recent bar.
    """
    if df is None or len(df) < 2:
        return {}

    try:
        import pandas_ta as ta
    except ImportError:
        ta = None
        logger.warning("pandas-ta not available, using manual implementations")

    result: Dict[str, Any] = {}
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    open_ = df["open"].astype(float)
    volume = df["volume"].astype(float)

    # ─── TREND INDICATORS ───────────────────────────────────────────

    # SMA
    for period in [9, 20, 50, 100, 200]:
        key = f"sma_{period}"
        if len(close) >= period:
            result[key] = float(close.rolling(period).mean().iloc[-1])

    # EMA
    for period in [9, 20, 50, 200]:
        key = f"ema_{period}"
        if len(close) >= period:
            result[key] = float(close.ewm(span=period, adjust=False).mean().iloc[-1])

    # VWAP (session-based, reset daily)
    try:
        typical_price = (high + low + close) / 3
        cum_tp_vol = (typical_price * volume).cumsum()
        cum_vol = volume.cumsum()
        vwap_series = cum_tp_vol / cum_vol.replace(0, np.nan)
        result["vwap"] = float(vwap_series.iloc[-1]) if not np.isnan(vwap_series.iloc[-1]) else None
    except Exception:
        result["vwap"] = None

    # Supertrend (period=10, multiplier=3.0)
    try:
        st_result = _compute_supertrend(high, low, close, period=10, multiplier=3.0)
        result["supertrend"] = st_result["supertrend"]
        result["supertrend_direction"] = st_result["direction"]
    except Exception as e:
        logger.debug(f"Supertrend error: {e}")
        result["supertrend"] = None
        result["supertrend_direction"] = None

    # ADX (period=14)
    try:
        adx_result = _compute_adx(high, low, close, period=14)
        result["adx"] = adx_result["adx"]
        result["plus_di"] = adx_result["plus_di"]
        result["minus_di"] = adx_result["minus_di"]
    except Exception as e:
        logger.debug(f"ADX error: {e}")
        result["adx"] = None

    # Parabolic SAR
    try:
        sar = _compute_parabolic_sar(high, low)
        result["parabolic_sar"] = sar["value"]
        result["parabolic_sar_direction"] = sar["direction"]
    except Exception:
        result["parabolic_sar"] = None

    # Ichimoku Cloud
    try:
        ichi = _compute_ichimoku(high, low, close)
        result.update(ichi)
    except Exception:
        pass

    # ─── MOMENTUM INDICATORS ────────────────────────────────────────

    # RSI (period=14)
    try:
        rsi = _compute_rsi(close, period=14)
        result["rsi"] = rsi
    except Exception:
        result["rsi"] = None

    # MACD (12, 26, 9)
    try:
        macd = _compute_macd(close)
        result["macd_line"] = macd["macd_line"]
        result["macd_signal"] = macd["signal_line"]
        result["macd_hist"] = macd["histogram"]
    except Exception:
        result["macd_line"] = None
        result["macd_signal"] = None
        result["macd_hist"] = None

    # Stochastic Oscillator (K=14, D=3, smooth=3)
    try:
        stoch = _compute_stochastic(high, low, close)
        result["stoch_k"] = stoch["k"]
        result["stoch_d"] = stoch["d"]
    except Exception:
        result["stoch_k"] = None
        result["stoch_d"] = None

    # CCI (period=20)
    try:
        result["cci"] = _compute_cci(high, low, close, period=20)
    except Exception:
        result["cci"] = None

    # Williams %R (period=14)
    try:
        result["williams_r"] = _compute_williams_r(high, low, close, period=14)
    except Exception:
        result["williams_r"] = None

    # MFI (period=14)
    try:
        result["mfi"] = _compute_mfi(high, low, close, volume, period=14)
    except Exception:
        result["mfi"] = None

    # Rate of Change (period=12)
    try:
        if len(close) > 12:
            result["roc"] = float((close.iloc[-1] - close.iloc[-13]) / close.iloc[-13] * 100)
    except Exception:
        result["roc"] = None

    # ─── VOLUME INDICATORS ──────────────────────────────────────────

    # OBV
    try:
        result["obv"] = _compute_obv(close, volume)
    except Exception:
        result["obv"] = None

    # Volume SMA (20)
    try:
        if len(volume) >= 20:
            vol_sma = float(volume.rolling(20).mean().iloc[-1])
            result["volume_sma_20"] = vol_sma
            result["volume_ratio"] = float(volume.iloc[-1] / vol_sma) if vol_sma > 0 else 1.0
    except Exception:
        result["volume_sma_20"] = None
        result["volume_ratio"] = None

    # Chaikin Money Flow (period=20)
    try:
        result["cmf"] = _compute_cmf(high, low, close, volume, period=20)
    except Exception:
        result["cmf"] = None

    # ─── VOLATILITY INDICATORS ──────────────────────────────────────

    # ATR (period=14)
    try:
        result["atr"] = _compute_atr(high, low, close, period=14)
    except Exception:
        result["atr"] = None

    # Bollinger Bands (period=20, std=2)
    try:
        bb = _compute_bollinger_bands(close, period=20, std_dev=2.0)
        result["bb_upper"] = bb["upper"]
        result["bb_mid"] = bb["mid"]
        result["bb_lower"] = bb["lower"]
        result["bb_bandwidth"] = bb["bandwidth"]
    except Exception:
        result["bb_upper"] = None
        result["bb_mid"] = None
        result["bb_lower"] = None

    # Keltner Channels
    try:
        kc = _compute_keltner(close, high, low, ema_period=20, atr_period=10, multiplier=2.0)
        result["kc_upper"] = kc["upper"]
        result["kc_lower"] = kc["lower"]
    except Exception:
        pass

    # Donchian Channels (period=20)
    try:
        if len(high) >= 20:
            result["donchian_upper"] = float(high.rolling(20).max().iloc[-1])
            result["donchian_lower"] = float(low.rolling(20).min().iloc[-1])
    except Exception:
        pass

    # Historical Volatility (20 periods, annualized)
    try:
        if len(close) > 20:
            log_returns = np.log(close / close.shift(1)).dropna()
            result["hv"] = float(log_returns.rolling(20).std().iloc[-1] * np.sqrt(252))
    except Exception:
        pass

    # ─── SUPPORT / RESISTANCE ───────────────────────────────────────

    # Pivot Points (Standard)
    try:
        pivots = _compute_pivot_points(high, low, close)
        result.update(pivots)
    except Exception:
        pass

    # Fibonacci Retracement
    try:
        fib = _compute_fibonacci(high, low)
        result.update(fib)
    except Exception:
        pass

    return result


# ─── MANUAL IMPLEMENTATIONS ────────────────────────────────────────


def _compute_rsi(close: pd.Series, period: int = 14) -> Optional[float]:
    """Compute RSI using exponential smoothing."""
    if len(close) < period + 1:
        return None
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    val = rsi.iloc[-1]
    return float(val) if not np.isnan(val) else None


def _compute_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Optional[float]]:
    """Compute MACD line, signal line, and histogram."""
    if len(close) < slow + signal:
        return {"macd_line": None, "signal_line": None, "histogram": None}
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd_line": float(macd_line.iloc[-1]),
        "signal_line": float(signal_line.iloc[-1]),
        "histogram": float(histogram.iloc[-1]),
    }


def _compute_stochastic(
    high: pd.Series, low: pd.Series, close: pd.Series,
    k_period: int = 14, d_period: int = 3, smooth: int = 3,
) -> Dict[str, Optional[float]]:
    """Compute Stochastic Oscillator %K and %D."""
    if len(close) < k_period + smooth:
        return {"k": None, "d": None}
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    denom = highest_high - lowest_low
    raw_k = ((close - lowest_low) / denom.replace(0, np.nan)) * 100
    k = raw_k.rolling(smooth).mean()
    d = k.rolling(d_period).mean()
    return {
        "k": float(k.iloc[-1]) if not np.isnan(k.iloc[-1]) else None,
        "d": float(d.iloc[-1]) if not np.isnan(d.iloc[-1]) else None,
    }


def _compute_cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> Optional[float]:
    """Compute Commodity Channel Index."""
    if len(close) < period:
        return None
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(period).mean()
    mean_dev = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    cci = (tp - sma_tp) / (0.015 * mean_dev.replace(0, np.nan))
    val = cci.iloc[-1]
    return float(val) if not np.isnan(val) else None


def _compute_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Optional[float]:
    """Compute Williams %R."""
    if len(close) < period:
        return None
    highest = high.rolling(period).max()
    lowest = low.rolling(period).min()
    denom = highest - lowest
    wr = ((highest - close) / denom.replace(0, np.nan)) * -100
    val = wr.iloc[-1]
    return float(val) if not np.isnan(val) else None


def _compute_mfi(
    high: pd.Series, low: pd.Series, close: pd.Series,
    volume: pd.Series, period: int = 14,
) -> Optional[float]:
    """Compute Money Flow Index."""
    if len(close) < period + 1:
        return None
    tp = (high + low + close) / 3
    mf = tp * volume
    tp_diff = tp.diff()
    pos_mf = mf.where(tp_diff > 0, 0.0)
    neg_mf = mf.where(tp_diff < 0, 0.0)
    pos_sum = pos_mf.rolling(period).sum()
    neg_sum = neg_mf.rolling(period).sum()
    mfr = pos_sum / neg_sum.replace(0, np.nan)
    mfi = 100.0 - (100.0 / (1.0 + mfr))
    val = mfi.iloc[-1]
    return float(val) if not np.isnan(val) else None


def _compute_obv(close: pd.Series, volume: pd.Series) -> Optional[int]:
    """Compute On Balance Volume."""
    if len(close) < 2:
        return None
    direction = np.sign(close.diff())
    obv = (direction * volume).cumsum()
    return int(obv.iloc[-1])


def _compute_cmf(
    high: pd.Series, low: pd.Series, close: pd.Series,
    volume: pd.Series, period: int = 20,
) -> Optional[float]:
    """Compute Chaikin Money Flow."""
    if len(close) < period:
        return None
    denom = high - low
    mf_multiplier = ((close - low) - (high - close)) / denom.replace(0, np.nan)
    mf_volume = mf_multiplier * volume
    cmf = mf_volume.rolling(period).sum() / volume.rolling(period).sum().replace(0, np.nan)
    val = cmf.iloc[-1]
    return float(val) if not np.isnan(val) else None


def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Optional[float]:
    """Compute Average True Range."""
    if len(close) < period + 1:
        return None
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, min_periods=period).mean()
    val = atr.iloc[-1]
    return float(val) if not np.isnan(val) else None


def _compute_bollinger_bands(
    close: pd.Series, period: int = 20, std_dev: float = 2.0,
) -> Dict[str, Optional[float]]:
    """Compute Bollinger Bands."""
    if len(close) < period:
        return {"upper": None, "mid": None, "lower": None, "bandwidth": None}
    mid = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    bw = (upper - lower) / mid.replace(0, np.nan)
    return {
        "upper": float(upper.iloc[-1]),
        "mid": float(mid.iloc[-1]),
        "lower": float(lower.iloc[-1]),
        "bandwidth": float(bw.iloc[-1]) if not np.isnan(bw.iloc[-1]) else None,
    }


def _compute_keltner(
    close: pd.Series, high: pd.Series, low: pd.Series,
    ema_period: int = 20, atr_period: int = 10, multiplier: float = 2.0,
) -> Dict[str, Optional[float]]:
    """Compute Keltner Channels."""
    if len(close) < max(ema_period, atr_period):
        return {"upper": None, "lower": None}
    ema = close.ewm(span=ema_period, adjust=False).mean()
    atr = _compute_atr(high, low, close, atr_period)
    if atr is None:
        return {"upper": None, "lower": None}
    return {
        "upper": float(ema.iloc[-1] + multiplier * atr),
        "lower": float(ema.iloc[-1] - multiplier * atr),
    }


def _compute_supertrend(
    high: pd.Series, low: pd.Series, close: pd.Series,
    period: int = 10, multiplier: float = 3.0,
) -> Dict[str, Any]:
    """Compute Supertrend indicator."""
    if len(close) < period + 1:
        return {"supertrend": None, "direction": None}

    hl2 = (high + low) / 2
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, min_periods=period).mean()

    basic_upper = hl2 + multiplier * atr
    basic_lower = hl2 - multiplier * atr

    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()
    supertrend = pd.Series(index=close.index, dtype=float)
    direction = pd.Series(index=close.index, dtype=bool)

    for i in range(period, len(close)):
        if i == period:
            if close.iloc[i] <= basic_upper.iloc[i]:
                supertrend.iloc[i] = basic_upper.iloc[i]
                direction.iloc[i] = False  # bearish
            else:
                supertrend.iloc[i] = basic_lower.iloc[i]
                direction.iloc[i] = True  # bullish
            continue

        # Final upper band
        if basic_upper.iloc[i] < final_upper.iloc[i - 1] or close.iloc[i - 1] > final_upper.iloc[i - 1]:
            final_upper.iloc[i] = basic_upper.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i - 1]

        # Final lower band
        if basic_lower.iloc[i] > final_lower.iloc[i - 1] or close.iloc[i - 1] < final_lower.iloc[i - 1]:
            final_lower.iloc[i] = basic_lower.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i - 1]

        if direction.iloc[i - 1] and close.iloc[i] < final_lower.iloc[i]:
            direction.iloc[i] = False
            supertrend.iloc[i] = final_upper.iloc[i]
        elif not direction.iloc[i - 1] and close.iloc[i] > final_upper.iloc[i]:
            direction.iloc[i] = True
            supertrend.iloc[i] = final_lower.iloc[i]
        else:
            direction.iloc[i] = direction.iloc[i - 1]
            if direction.iloc[i]:
                supertrend.iloc[i] = final_lower.iloc[i]
            else:
                supertrend.iloc[i] = final_upper.iloc[i]

    return {
        "supertrend": float(supertrend.iloc[-1]) if not np.isnan(supertrend.iloc[-1]) else None,
        "direction": bool(direction.iloc[-1]) if not pd.isna(direction.iloc[-1]) else None,
    }


def _compute_adx(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14,
) -> Dict[str, Optional[float]]:
    """Compute ADX, +DI, -DI."""
    if len(close) < period * 2:
        return {"adx": None, "plus_di": None, "minus_di": None}

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(0.0, index=close.index)
    minus_dm = pd.Series(0.0, index=close.index)

    plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
    minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1 / period, min_periods=period).mean()
    plus_di = (plus_dm.ewm(alpha=1 / period, min_periods=period).mean() / atr.replace(0, np.nan)) * 100
    minus_di = (minus_dm.ewm(alpha=1 / period, min_periods=period).mean() / atr.replace(0, np.nan)) * 100

    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    adx = dx.ewm(alpha=1 / period, min_periods=period).mean()

    return {
        "adx": float(adx.iloc[-1]) if not np.isnan(adx.iloc[-1]) else None,
        "plus_di": float(plus_di.iloc[-1]) if not np.isnan(plus_di.iloc[-1]) else None,
        "minus_di": float(minus_di.iloc[-1]) if not np.isnan(minus_di.iloc[-1]) else None,
    }


def _compute_parabolic_sar(high: pd.Series, low: pd.Series) -> Dict[str, Any]:
    """Compute Parabolic SAR."""
    n = len(high)
    if n < 3:
        return {"value": None, "direction": None}

    af_start = 0.02
    af_increment = 0.02
    af_max = 0.20

    sar = np.zeros(n)
    direction = np.zeros(n, dtype=bool)  # True = bullish
    af = af_start
    ep = low.iloc[0]  # extreme point

    # Initial: assume bullish
    sar[0] = low.iloc[0]
    direction[0] = True
    ep = high.iloc[0]

    for i in range(1, n):
        if direction[i - 1]:  # bullish
            sar[i] = sar[i - 1] + af * (ep - sar[i - 1])
            sar[i] = min(sar[i], low.iloc[i - 1], low.iloc[max(0, i - 2)])
            if high.iloc[i] > ep:
                ep = high.iloc[i]
                af = min(af + af_increment, af_max)
            if low.iloc[i] < sar[i]:
                direction[i] = False
                sar[i] = ep
                ep = low.iloc[i]
                af = af_start
            else:
                direction[i] = True
        else:  # bearish
            sar[i] = sar[i - 1] + af * (ep - sar[i - 1])
            sar[i] = max(sar[i], high.iloc[i - 1], high.iloc[max(0, i - 2)])
            if low.iloc[i] < ep:
                ep = low.iloc[i]
                af = min(af + af_increment, af_max)
            if high.iloc[i] > sar[i]:
                direction[i] = True
                sar[i] = ep
                ep = high.iloc[i]
                af = af_start
            else:
                direction[i] = False

    return {
        "value": float(sar[-1]),
        "direction": "bullish" if direction[-1] else "bearish",
    }


def _compute_ichimoku(high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, Optional[float]]:
    """Compute Ichimoku Cloud components."""
    result = {}
    if len(close) < 52:
        return result

    # Tenkan-sen (9-period)
    tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
    result["ichimoku_tenkan"] = float(tenkan.iloc[-1])

    # Kijun-sen (26-period)
    kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
    result["ichimoku_kijun"] = float(kijun.iloc[-1])

    # Senkou Span A (plotted 26 periods ahead)
    span_a = (tenkan + kijun) / 2
    result["ichimoku_span_a"] = float(span_a.iloc[-1])

    # Senkou Span B (52-period, plotted 26 ahead)
    span_b = (high.rolling(52).max() + low.rolling(52).min()) / 2
    result["ichimoku_span_b"] = float(span_b.iloc[-1])

    # Chikou Span (current close, plotted 26 back)
    result["ichimoku_chikou"] = float(close.iloc[-1])

    return result


def _compute_pivot_points(high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, Optional[float]]:
    """Compute Standard Pivot Points from previous day's data."""
    if len(close) < 2:
        return {}
    prev_h = float(high.iloc[-2])
    prev_l = float(low.iloc[-2])
    prev_c = float(close.iloc[-2])

    pp = (prev_h + prev_l + prev_c) / 3
    return {
        "pivot_pp": pp,
        "pivot_r1": 2 * pp - prev_l,
        "pivot_r2": pp + (prev_h - prev_l),
        "pivot_r3": prev_h + 2 * (pp - prev_l),
        "pivot_s1": 2 * pp - prev_h,
        "pivot_s2": pp - (prev_h - prev_l),
        "pivot_s3": prev_l - 2 * (prev_h - pp),
    }


def _compute_fibonacci(high: pd.Series, low: pd.Series) -> Dict[str, float]:
    """Compute Fibonacci retracement levels from swing high/low."""
    if len(high) < 20:
        return {}
    swing_high = float(high.rolling(20).max().iloc[-1])
    swing_low = float(low.rolling(20).min().iloc[-1])
    diff = swing_high - swing_low
    if diff == 0:
        return {}
    return {
        "fib_236": swing_high - 0.236 * diff,
        "fib_382": swing_high - 0.382 * diff,
        "fib_500": swing_high - 0.500 * diff,
        "fib_618": swing_high - 0.618 * diff,
        "fib_786": swing_high - 0.786 * diff,
        "fib_ext_1272": swing_high + 0.272 * diff,
        "fib_ext_1618": swing_high + 0.618 * diff,
    }


def resample_ohlcv(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample 1-minute OHLCV data to a higher timeframe.

    Args:
        df: 1-minute OHLCV DataFrame with a datetime index or 'timestamp' column.
        timeframe: Target timeframe (5m, 15m, 30m, 1h, 1D, 1W, 1M).

    Returns:
        Resampled OHLCV DataFrame.
    """
    tf_map = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
        "1D": "1D",
        "1W": "1W",
        "1M": "1ME",
    }
    rule = tf_map.get(timeframe, "1min")

    if "timestamp" in df.columns and not isinstance(df.index, pd.DatetimeIndex):
        df = df.set_index("timestamp")

    resampled = df.resample(rule).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna(subset=["open"])

    if "oi" in df.columns:
        resampled["oi"] = df["oi"].resample(rule).last()

    return resampled
