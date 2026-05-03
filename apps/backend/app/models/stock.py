from datetime import date, datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, Float,
    ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    exchange = Column(String(10), nullable=False)  # NSE, BSE, NYSE, NASDAQ
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap_category = Column(String(20))  # large, mid, small, micro
    currency = Column(String(5), default="INR")
    country = Column(String(10), default="IN")
    is_active = Column(Boolean, default=True)
    logo_url = Column(String(500))
    website = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (UniqueConstraint("symbol", "exchange", name="uq_symbol_exchange"),)

    fundamentals = relationship("Fundamental", back_populates="stock", cascade="all, delete-orphan")
    technicals = relationship("Technical", back_populates="stock", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="stock", cascade="all, delete-orphan")
    holdings = relationship("Holding", back_populates="stock")
    watchlist_items = relationship("WatchlistItem", back_populates="stock")
    alerts = relationship("Alert", back_populates="stock")


class Fundamental(Base):
    __tablename__ = "fundamentals"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date, nullable=False)

    # Valuation
    market_cap = Column(BigInteger)
    pe_ratio = Column(Float)
    forward_pe = Column(Float)
    pb_ratio = Column(Float)
    ev_ebitda = Column(Float)
    price_to_sales = Column(Float)

    # Profitability
    roe = Column(Float)
    roce = Column(Float)
    roa = Column(Float)
    net_margin = Column(Float)
    operating_margin = Column(Float)
    gross_margin = Column(Float)

    # Growth
    eps = Column(Float)
    eps_growth_yoy = Column(Float)
    revenue_growth_yoy = Column(Float)
    earnings_growth_qoq = Column(Float)

    # Financial Health
    debt_to_equity = Column(Float)
    current_ratio = Column(Float)
    quick_ratio = Column(Float)
    interest_coverage = Column(Float)

    # Dividends
    dividend_yield = Column(Float)
    payout_ratio = Column(Float)

    # Quality Scores
    piotroski_score = Column(SmallInteger)
    altman_z_score = Column(Float)
    composite_score = Column(Float)  # 0-100 proprietary score

    __table_args__ = (UniqueConstraint("stock_id", "date", name="uq_fundamental_stock_date"),)

    stock = relationship("Stock", back_populates="fundamentals")


class Technical(Base):
    __tablename__ = "technicals"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date, nullable=False)

    # Momentum
    rsi_14 = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)

    # Moving Averages
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    sma_100 = Column(Float)
    sma_200 = Column(Float)
    ema_9 = Column(Float)
    ema_20 = Column(Float)

    # Volume
    volume_avg_20d = Column(BigInteger)
    relative_volume = Column(Float)

    # Price levels
    week_52_high = Column(Float)
    week_52_low = Column(Float)
    atr_14 = Column(Float)        # Average True Range
    bollinger_upper = Column(Float)
    bollinger_lower = Column(Float)

    # Returns
    pct_change_1d = Column(Float)
    pct_change_1w = Column(Float)
    pct_change_1m = Column(Float)
    pct_change_3m = Column(Float)
    pct_change_6m = Column(Float)
    pct_change_1y = Column(Float)
    pct_change_ytd = Column(Float)

    # Volatility
    volatility_30d = Column(Float)
    beta = Column(Float)

    __table_args__ = (UniqueConstraint("stock_id", "date", name="uq_technical_stock_date"),)

    stock = relationship("Stock", back_populates="technicals")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    adj_close = Column(Float)
    volume = Column(BigInteger)

    __table_args__ = (UniqueConstraint("stock_id", "date", name="uq_price_stock_date"),)

    stock = relationship("Stock", back_populates="price_history")
