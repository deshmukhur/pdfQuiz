"""Initial database schema.

Revision ID: 001
Revises: None
Create Date: 2025-01-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Instruments table
    op.create_table(
        "instruments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String, unique=True, nullable=False),
        sa.Column("exchange", sa.String, nullable=False),
        sa.Column("segment", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=True),
        sa.Column("lot_size", sa.Integer, default=1),
        sa.Column("tick_size", sa.Numeric, default=0.05),
        sa.Column("expiry", sa.Date, nullable=True),
        sa.Column("strike", sa.Numeric, nullable=True),
        sa.Column("option_type", sa.String(2), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_instruments_symbol", "instruments", ["symbol"])

    # OHLCV 1-minute bars
    op.create_table(
        "ohlcv_1min",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric, nullable=False),
        sa.Column("high", sa.Numeric, nullable=False),
        sa.Column("low", sa.Numeric, nullable=False),
        sa.Column("close", sa.Numeric, nullable=False),
        sa.Column("volume", sa.BigInteger, default=0),
        sa.Column("oi", sa.BigInteger, nullable=True),
    )
    op.create_index("ix_ohlcv_1min_symbol", "ohlcv_1min", ["symbol"])
    op.create_index("ix_ohlcv_1min_symbol_timestamp", "ohlcv_1min", ["symbol", "timestamp"], unique=True)

    # Indicator snapshots
    op.create_table(
        "indicator_snapshots",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timeframe", sa.String, nullable=False),
        sa.Column("rsi", sa.Numeric, nullable=True),
        sa.Column("macd_line", sa.Numeric, nullable=True),
        sa.Column("macd_signal", sa.Numeric, nullable=True),
        sa.Column("macd_hist", sa.Numeric, nullable=True),
        sa.Column("ema_9", sa.Numeric, nullable=True),
        sa.Column("ema_20", sa.Numeric, nullable=True),
        sa.Column("ema_50", sa.Numeric, nullable=True),
        sa.Column("ema_200", sa.Numeric, nullable=True),
        sa.Column("sma_20", sa.Numeric, nullable=True),
        sa.Column("bb_upper", sa.Numeric, nullable=True),
        sa.Column("bb_lower", sa.Numeric, nullable=True),
        sa.Column("bb_mid", sa.Numeric, nullable=True),
        sa.Column("atr", sa.Numeric, nullable=True),
        sa.Column("adx", sa.Numeric, nullable=True),
        sa.Column("supertrend", sa.Numeric, nullable=True),
        sa.Column("supertrend_direction", sa.Boolean, nullable=True),
        sa.Column("obv", sa.BigInteger, nullable=True),
        sa.Column("vwap", sa.Numeric, nullable=True),
        sa.Column("stoch_k", sa.Numeric, nullable=True),
        sa.Column("stoch_d", sa.Numeric, nullable=True),
        sa.Column("cci", sa.Numeric, nullable=True),
        sa.Column("williams_r", sa.Numeric, nullable=True),
        sa.Column("mfi", sa.Numeric, nullable=True),
        sa.Column("pivot_pp", sa.Numeric, nullable=True),
        sa.Column("pivot_r1", sa.Numeric, nullable=True),
        sa.Column("pivot_r2", sa.Numeric, nullable=True),
        sa.Column("pivot_r3", sa.Numeric, nullable=True),
        sa.Column("pivot_s1", sa.Numeric, nullable=True),
        sa.Column("pivot_s2", sa.Numeric, nullable=True),
        sa.Column("pivot_s3", sa.Numeric, nullable=True),
        sa.Column("score", sa.Numeric, nullable=True),
        sa.Column("signal", sa.String, nullable=True),
        sa.Column("score_breakdown", JSONB, nullable=True),
        sa.Column("candlestick_patterns", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_indicator_snapshots_symbol", "indicator_snapshots", ["symbol"])

    # Signals
    op.create_table(
        "signals",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String, nullable=False),
        sa.Column("signal_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signal_type", sa.String, nullable=False),
        sa.Column("entry_price", sa.Numeric, nullable=False),
        sa.Column("stop_loss", sa.Numeric, nullable=True),
        sa.Column("target_1", sa.Numeric, nullable=True),
        sa.Column("target_2", sa.Numeric, nullable=True),
        sa.Column("target_3", sa.Numeric, nullable=True),
        sa.Column("confidence_score", sa.Numeric, nullable=True),
        sa.Column("reasoning", JSONB, nullable=True),
        sa.Column("status", sa.String, default="OPEN"),
        sa.Column("exit_price", sa.Numeric, nullable=True),
        sa.Column("exit_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pnl_percent", sa.Numeric, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_signals_symbol", "signals", ["symbol"])

    # Backtest results
    op.create_table(
        "backtest_results",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("signal_id", sa.BigInteger, sa.ForeignKey("signals.id"), nullable=False),
        sa.Column("symbol", sa.String, nullable=False),
        sa.Column("entry_price", sa.Numeric, nullable=False),
        sa.Column("exit_price", sa.Numeric, nullable=True),
        sa.Column("stop_loss", sa.Numeric, nullable=True),
        sa.Column("target", sa.Numeric, nullable=True),
        sa.Column("entry_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exit_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.String, nullable=True),
        sa.Column("pnl_percent", sa.Numeric, nullable=True),
        sa.Column("holding_period_minutes", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_backtest_results_symbol", "backtest_results", ["symbol"])

    # News articles
    op.create_table(
        "news_articles",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("headline", sa.Text, nullable=False),
        sa.Column("source", sa.String, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("related_symbols", ARRAY(sa.Text), nullable=True),
        sa.Column("sentiment_score", sa.Numeric, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Fundamental data
    op.create_table(
        "fundamental_data",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String, nullable=False, unique=True),
        sa.Column("pe_ratio", sa.Numeric, nullable=True),
        sa.Column("pb_ratio", sa.Numeric, nullable=True),
        sa.Column("eps", sa.Numeric, nullable=True),
        sa.Column("roe", sa.Numeric, nullable=True),
        sa.Column("debt_to_equity", sa.Numeric, nullable=True),
        sa.Column("market_cap", sa.Numeric, nullable=True),
        sa.Column("revenue_growth_yoy", sa.Numeric, nullable=True),
        sa.Column("profit_growth_yoy", sa.Numeric, nullable=True),
        sa.Column("promoter_holding", sa.Numeric, nullable=True),
        sa.Column("fii_holding", sa.Numeric, nullable=True),
        sa.Column("dii_holding", sa.Numeric, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_fundamental_data_symbol", "fundamental_data", ["symbol"])


def downgrade() -> None:
    op.drop_table("fundamental_data")
    op.drop_table("news_articles")
    op.drop_table("backtest_results")
    op.drop_table("signals")
    op.drop_table("indicator_snapshots")
    op.drop_table("ohlcv_1min")
    op.drop_table("instruments")
