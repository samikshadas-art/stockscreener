"""Initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255)),
        sa.Column("name", sa.String(100)),
        sa.Column("avatar_url", sa.String(500)),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_verified", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── stocks ───────────────────────────────────────────────────────────────
    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("exchange", sa.String(10), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100)),
        sa.Column("industry", sa.String(100)),
        sa.Column("market_cap_category", sa.String(20)),
        sa.Column("currency", sa.String(5), default="INR"),
        sa.Column("country", sa.String(10), default="IN"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("website", sa.String(255)),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.UniqueConstraint("symbol", "exchange", name="uq_symbol_exchange"),
    )
    op.create_index("ix_stocks_symbol_exchange", "stocks", ["symbol", "exchange"])

    # ── fundamentals ─────────────────────────────────────────────────────────
    op.create_table(
        "fundamentals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("market_cap", sa.BigInteger()),
        sa.Column("pe_ratio", sa.Float()),
        sa.Column("forward_pe", sa.Float()),
        sa.Column("pb_ratio", sa.Float()),
        sa.Column("ev_ebitda", sa.Float()),
        sa.Column("price_to_sales", sa.Float()),
        sa.Column("roe", sa.Float()),
        sa.Column("roce", sa.Float()),
        sa.Column("roa", sa.Float()),
        sa.Column("net_margin", sa.Float()),
        sa.Column("operating_margin", sa.Float()),
        sa.Column("gross_margin", sa.Float()),
        sa.Column("eps", sa.Float()),
        sa.Column("eps_growth_yoy", sa.Float()),
        sa.Column("revenue_growth_yoy", sa.Float()),
        sa.Column("earnings_growth_qoq", sa.Float()),
        sa.Column("debt_to_equity", sa.Float()),
        sa.Column("current_ratio", sa.Float()),
        sa.Column("quick_ratio", sa.Float()),
        sa.Column("interest_coverage", sa.Float()),
        sa.Column("dividend_yield", sa.Float()),
        sa.Column("payout_ratio", sa.Float()),
        sa.Column("piotroski_score", sa.SmallInteger()),
        sa.Column("altman_z_score", sa.Float()),
        sa.Column("composite_score", sa.Float()),
        sa.UniqueConstraint("stock_id", "date", name="uq_fundamental_stock_date"),
    )
    op.create_index("ix_fundamentals_stock_date", "fundamentals", ["stock_id", "date"])

    # ── technicals ───────────────────────────────────────────────────────────
    op.create_table(
        "technicals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("rsi_14", sa.Float()),
        sa.Column("macd", sa.Float()),
        sa.Column("macd_signal", sa.Float()),
        sa.Column("macd_histogram", sa.Float()),
        sa.Column("sma_20", sa.Float()),
        sa.Column("sma_50", sa.Float()),
        sa.Column("sma_100", sa.Float()),
        sa.Column("sma_200", sa.Float()),
        sa.Column("ema_9", sa.Float()),
        sa.Column("ema_20", sa.Float()),
        sa.Column("volume_avg_20d", sa.BigInteger()),
        sa.Column("relative_volume", sa.Float()),
        sa.Column("week_52_high", sa.Float()),
        sa.Column("week_52_low", sa.Float()),
        sa.Column("atr_14", sa.Float()),
        sa.Column("bollinger_upper", sa.Float()),
        sa.Column("bollinger_lower", sa.Float()),
        sa.Column("pct_change_1d", sa.Float()),
        sa.Column("pct_change_1w", sa.Float()),
        sa.Column("pct_change_1m", sa.Float()),
        sa.Column("pct_change_3m", sa.Float()),
        sa.Column("pct_change_6m", sa.Float()),
        sa.Column("pct_change_1y", sa.Float()),
        sa.Column("pct_change_ytd", sa.Float()),
        sa.Column("volatility_30d", sa.Float()),
        sa.Column("beta", sa.Float()),
        sa.UniqueConstraint("stock_id", "date", name="uq_technical_stock_date"),
    )
    op.create_index("ix_technicals_stock_date", "technicals", ["stock_id", "date"])

    # ── price_history ────────────────────────────────────────────────────────
    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.Float()),
        sa.Column("high", sa.Float()),
        sa.Column("low", sa.Float()),
        sa.Column("close", sa.Float()),
        sa.Column("adj_close", sa.Float()),
        sa.Column("volume", sa.BigInteger()),
        sa.UniqueConstraint("stock_id", "date", name="uq_price_stock_date"),
    )
    op.create_index("ix_price_history_stock_date", "price_history", ["stock_id", "date"])

    # ── screeners ────────────────────────────────────────────────────────────
    op.create_table(
        "screeners",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("filters", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("logic", sa.String(5), default="AND"),
        sa.Column("columns", postgresql.JSONB()),
        sa.Column("is_public", sa.Boolean(), default=False),
        sa.Column("share_token", sa.String(32), unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index("ix_screeners_share_token", "screeners", ["share_token"])

    # ── portfolios ───────────────────────────────────────────────────────────
    op.create_table(
        "portfolios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("benchmark", sa.String(20), default="NIFTY50"),
        sa.Column("currency", sa.String(5), default="INR"),
        sa.Column("is_public", sa.Boolean(), default=False),
        sa.Column("share_token", sa.String(32), unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index("ix_portfolios_share_token", "portfolios", ["share_token"])

    # ── holdings ─────────────────────────────────────────────────────────────
    op.create_table(
        "holdings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("avg_buy_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("buy_date", sa.Date()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── watchlists ───────────────────────────────────────────────────────────
    op.create_table(
        "watchlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False, default="My Watchlist"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── watchlist_items ──────────────────────────────────────────────────────
    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("watchlist_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── alerts ───────────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id"), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("threshold", sa.Float()),
        sa.Column("message", sa.Text()),
        sa.Column("is_triggered", sa.Boolean(), default=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("triggered_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("watchlist_items")
    op.drop_table("watchlists")
    op.drop_table("holdings")
    op.drop_table("portfolios")
    op.drop_table("screeners")
    op.drop_table("price_history")
    op.drop_table("technicals")
    op.drop_table("fundamentals")
    op.drop_table("stocks")
    op.drop_table("users")
