"""Backtesting module for evaluating generated signals against historical data.

Checks whether stop loss or targets were hit for each signal and computes
win rate, profit factor, expectancy, and per-indicator breakdowns.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def run_backtest(
    db_session: AsyncSession,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    signal_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Run backtest on historical signals.

    Args:
        db_session: Async database session.
        from_date: ISO date string for start of period.
        to_date: ISO date string for end of period.
        signal_type: Filter by signal type (BUY/SELL).

    Returns:
        Backtest report with metrics and breakdowns.
    """
    # Fetch open signals
    where_clauses = ["status = 'OPEN'"]
    params: Dict[str, Any] = {}

    if from_date:
        where_clauses.append("signal_time >= :from_date")
        params["from_date"] = from_date
    if to_date:
        where_clauses.append("signal_time <= :to_date")
        params["to_date"] = to_date
    if signal_type:
        where_clauses.append("signal_type = :signal_type")
        params["signal_type"] = signal_type

    where = " AND ".join(where_clauses)
    query = text(f"""
        SELECT id, symbol, signal_time, signal_type, entry_price,
               stop_loss, target_1, target_2, target_3, confidence_score, reasoning
        FROM signals
        WHERE {where}
        ORDER BY signal_time
    """)

    result = await db_session.execute(query, params)
    signals = result.fetchall()

    wins = 0
    losses = 0
    neutrals = 0
    total_profit_pct = 0.0
    total_loss_pct = 0.0
    results_list: List[Dict[str, Any]] = []

    for sig in signals:
        sig_id, symbol, signal_time, sig_type, entry_price, sl, t1, t2, t3, confidence, reasoning = sig

        if not entry_price or entry_price == 0:
            continue

        # Get subsequent candles after signal
        candle_query = text("""
            SELECT timestamp, high, low, close
            FROM ohlcv_1min
            WHERE symbol = :symbol AND timestamp > :signal_time
            ORDER BY timestamp
            LIMIT 375
        """)
        candle_result = await db_session.execute(candle_query, {
            "symbol": symbol,
            "signal_time": signal_time,
        })
        candles = candle_result.fetchall()

        if not candles:
            continue

        entry = float(entry_price)
        stop = float(sl) if sl else None
        target = float(t1) if t1 else None

        bt_result = "NEUTRAL"
        exit_price = float(candles[-1][3])  # last candle close
        exit_time = candles[-1][0]
        pnl_pct = 0.0

        for candle in candles:
            ts, high, low, close = candle
            high, low, close = float(high), float(low), float(close)

            if sig_type == "BUY":
                # Check stop loss first
                if stop and low <= stop:
                    bt_result = "LOSS"
                    exit_price = stop
                    exit_time = ts
                    pnl_pct = (stop - entry) / entry * 100
                    break
                # Check target
                if target and high >= target:
                    bt_result = "WIN"
                    exit_price = target
                    exit_time = ts
                    pnl_pct = (target - entry) / entry * 100
                    break
            elif sig_type == "SELL":
                if stop and high >= stop:
                    bt_result = "LOSS"
                    exit_price = stop
                    exit_time = ts
                    pnl_pct = (entry - stop) / entry * 100
                    break
                if target and low <= target:
                    bt_result = "WIN"
                    exit_price = target
                    exit_time = ts
                    pnl_pct = (entry - target) / entry * 100
                    break

        if bt_result == "NEUTRAL":
            pnl_pct = (exit_price - entry) / entry * 100 if sig_type == "BUY" else (entry - exit_price) / entry * 100

        # Update signal status
        try:
            update_query = text("""
                UPDATE signals SET status = 'CLOSED', exit_price = :exit_price,
                    exit_time = :exit_time, pnl_percent = :pnl_pct
                WHERE id = :sig_id
            """)
            await db_session.execute(update_query, {
                "exit_price": exit_price,
                "exit_time": exit_time,
                "pnl_pct": round(pnl_pct, 4),
                "sig_id": sig_id,
            })

            # Insert backtest result
            bt_insert = text("""
                INSERT INTO backtest_results (signal_id, symbol, entry_price, exit_price,
                    stop_loss, target, entry_time, exit_time, result, pnl_percent, holding_period_minutes)
                VALUES (:sig_id, :symbol, :entry, :exit_price, :sl, :target,
                    :entry_time, :exit_time, :result, :pnl, :holding)
            """)
            holding_minutes = 0
            if exit_time and signal_time:
                try:
                    holding_minutes = int((exit_time - signal_time).total_seconds() / 60)
                except Exception:
                    pass

            await db_session.execute(bt_insert, {
                "sig_id": sig_id,
                "symbol": symbol,
                "entry": entry,
                "exit_price": exit_price,
                "sl": stop,
                "target": target,
                "entry_time": signal_time,
                "exit_time": exit_time,
                "result": bt_result,
                "pnl": round(pnl_pct, 4),
                "holding": holding_minutes,
            })
        except Exception as e:
            logger.error(f"Error updating backtest for signal {sig_id}: {e}")

        if bt_result == "WIN":
            wins += 1
            total_profit_pct += pnl_pct
        elif bt_result == "LOSS":
            losses += 1
            total_loss_pct += abs(pnl_pct)
        else:
            neutrals += 1
            if pnl_pct > 0:
                total_profit_pct += pnl_pct
            else:
                total_loss_pct += abs(pnl_pct)

        results_list.append({
            "signal_id": sig_id,
            "symbol": symbol,
            "signal_type": sig_type,
            "entry_price": entry,
            "exit_price": exit_price,
            "result": bt_result,
            "pnl_percent": round(pnl_pct, 4),
            "holding_minutes": holding_minutes if exit_time and signal_time else 0,
        })

    try:
        await db_session.commit()
    except Exception:
        pass

    total = wins + losses + neutrals
    win_rate = (wins / total * 100) if total > 0 else 0
    avg_profit = total_profit_pct / max(wins, 1)
    avg_loss = total_loss_pct / max(losses, 1)
    profit_factor = total_profit_pct / max(total_loss_pct, 0.001)
    loss_rate = 100 - win_rate
    expectancy = (win_rate / 100 * avg_profit) - (loss_rate / 100 * avg_loss)

    return {
        "total_signals": total,
        "wins": wins,
        "losses": losses,
        "neutrals": neutrals,
        "win_rate": round(win_rate, 2),
        "avg_profit_pct": round(avg_profit, 4),
        "avg_loss_pct": round(avg_loss, 4),
        "profit_factor": round(profit_factor, 4),
        "expectancy": round(expectancy, 4),
        "total_profit_pct": round(total_profit_pct, 4),
        "total_loss_pct": round(total_loss_pct, 4),
        "results": results_list,
    }


async def get_backtest_report(
    db_session: AsyncSession,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    signal_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Get backtest report from already computed results."""
    where_clauses = ["1=1"]
    params: Dict[str, Any] = {}

    if from_date:
        where_clauses.append("entry_time >= :from_date")
        params["from_date"] = from_date
    if to_date:
        where_clauses.append("exit_time <= :to_date")
        params["to_date"] = to_date

    where = " AND ".join(where_clauses)
    query = text(f"""
        SELECT result, pnl_percent, holding_period_minutes, symbol
        FROM backtest_results
        WHERE {where}
        ORDER BY entry_time
    """)

    result = await db_session.execute(query, params)
    rows = result.fetchall()

    wins = sum(1 for r in rows if r[0] == "WIN")
    losses = sum(1 for r in rows if r[0] == "LOSS")
    total = len(rows)

    total_profit = sum(float(r[1]) for r in rows if float(r[1]) > 0)
    total_loss = sum(abs(float(r[1])) for r in rows if float(r[1]) < 0)

    return {
        "total_signals": total,
        "wins": wins,
        "losses": losses,
        "neutrals": total - wins - losses,
        "win_rate": round(wins / max(total, 1) * 100, 2),
        "profit_factor": round(total_profit / max(total_loss, 0.001), 4),
        "total_profit_pct": round(total_profit, 4),
        "total_loss_pct": round(total_loss, 4),
    }
