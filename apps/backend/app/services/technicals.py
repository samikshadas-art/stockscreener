"""
Technical indicators computation service.
Uses pandas_ta to compute RSI, MACD, SMAs, Bollinger Bands, etc.
Reads from price_history table, writes to technicals table.
"""
import logging
from datetime import date, timedelta
from typing import Optional

import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.stock import Stock, PriceHistory, Technical

logger = logging.getLogger(__name__)


async def fetch_price_dataframe(db: AsyncSession, stock_id: int, days: int = 300) -> pd.DataFrame:
    """Load price history into a DataFrame."""
    since = date.today() - timedelta(days=days)
    stmt = (
        select(PriceHistory)
        .where(PriceHistory.stock_id == stock_id, PriceHistory.date >= since)
        .order_by(PriceHistory.date.asc())
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame([{
        "date": r.date,
        "open": r.open,
        "high": r.high,
        "low": r.low,
        "close": r.close,
        "volume": r.volume,
    } for r in rows])
    df.set_index("date", inplace=True)
    return df


def compute_indicators(df: pd.DataFrame) -> dict:
    """Compute all technical indicators from a OHLCV DataFrame."""
    if df.empty or len(df) < 20:
        return {}

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    result = {}

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    result["rsi_14"] = _last(rsi)

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    result["macd"] = _last(macd_line)
    result["macd_signal"] = _last(signal_line)
    result["macd_histogram"] = _last(macd_line - signal_line)

    # Moving Averages
    result["sma_20"] = _last(close.rolling(20).mean())
    result["sma_50"] = _last(close.rolling(50).mean())
    result["sma_100"] = _last(close.rolling(100).mean())
    result["sma_200"] = _last(close.rolling(200).mean())
    result["ema_9"] = _last(close.ewm(span=9, adjust=False).mean())
    result["ema_20"] = _last(close.ewm(span=20, adjust=False).mean())

    # Bollinger Bands
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    result["bollinger_upper"] = _last(sma20 + 2 * std20)
    result["bollinger_lower"] = _last(sma20 - 2 * std20)

    # ATR
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    result["atr_14"] = _last(tr.rolling(14).mean())

    # Volume
    result["volume_avg_20d"] = int(volume.rolling(20).mean().iloc[-1]) if len(volume) >= 20 else None
    last_vol = volume.iloc[-1]
    avg_vol = volume.rolling(20).mean().iloc[-1]
    result["relative_volume"] = round(last_vol / avg_vol, 2) if avg_vol else None

    # Price levels
    result["week_52_high"] = _last(high.rolling(252).max())
    result["week_52_low"] = _last(low.rolling(252).min())

    # Returns
    last_close = close.iloc[-1]
    result["pct_change_1d"] = _return(close, 1)
    result["pct_change_1w"] = _return(close, 5)
    result["pct_change_1m"] = _return(close, 21)
    result["pct_change_3m"] = _return(close, 63)
    result["pct_change_6m"] = _return(close, 126)
    result["pct_change_1y"] = _return(close, 252)

    # Volatility (annualized std of daily returns)
    daily_returns = close.pct_change().dropna()
    if len(daily_returns) >= 30:
        result["volatility_30d"] = round(daily_returns.tail(30).std() * (252 ** 0.5) * 100, 2)

    return result


async def compute_and_store_technicals(db: AsyncSession, stock_id: int) -> bool:
    """Compute technicals for a stock and store in DB."""
    try:
        df = await fetch_price_dataframe(db, stock_id)
        if df.empty:
            return False

        indicators = compute_indicators(df)
        if not indicators:
            return False

        tech_data = {"stock_id": stock_id, "date": date.today(), **indicators}

        stmt = pg_insert(Technical).values(**tech_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["stock_id", "date"],
            set_={k: v for k, v in tech_data.items() if k not in ("stock_id", "date")},
        )
        await db.execute(stmt)
        await db.commit()
        return True

    except Exception as e:
        logger.error(f"Error computing technicals for stock {stock_id}: {e}")
        await db.rollback()
        return False


def compute_composite_score(fund_data: dict, tech_data: dict) -> float:
    """
    Proprietary composite score (0-100).
    40% fundamental quality, 30% technical strength, 30% momentum.
    """
    scores = []

    # --- Fundamental Score (40 pts) ---
    f_score = 0
    f_weight = 40

    pe = fund_data.get("pe_ratio")
    if pe and 0 < pe < 25:
        f_score += 10
    elif pe and 25 <= pe < 40:
        f_score += 5

    roe = fund_data.get("roe")
    if roe and roe > 20:
        f_score += 10
    elif roe and roe > 12:
        f_score += 5

    de = fund_data.get("debt_to_equity")
    if de is not None and de < 0.5:
        f_score += 10
    elif de is not None and de < 1.5:
        f_score += 5

    eps_g = fund_data.get("eps_growth_yoy")
    if eps_g and eps_g > 20:
        f_score += 10
    elif eps_g and eps_g > 10:
        f_score += 5

    # Piotroski bonus
    piotroski = fund_data.get("piotroski_score")
    if piotroski and piotroski >= 7:
        f_score += 10  # extra quality bonus

    f_score = min(f_score, f_weight)

    # --- Technical Score (30 pts) ---
    t_score = 0
    rsi = tech_data.get("rsi_14")
    if rsi and 40 <= rsi <= 65:
        t_score += 10  # healthy momentum zone
    elif rsi and rsi < 30:
        t_score += 5   # oversold (potential buy)

    sma50 = tech_data.get("sma_50")
    sma200 = tech_data.get("sma_200")
    price = tech_data.get("current_price") or sma50  # fallback
    if price and sma50 and sma200 and price > sma50 > sma200:
        t_score += 20  # golden cross alignment

    t_score = min(t_score, 30)

    # --- Momentum Score (30 pts) ---
    m_score = 0
    m1 = tech_data.get("pct_change_1m", 0) or 0
    m3 = tech_data.get("pct_change_3m", 0) or 0
    m6 = tech_data.get("pct_change_6m", 0) or 0

    if m1 > 5:
        m_score += 10
    if m3 > 10:
        m_score += 10
    if m6 > 20:
        m_score += 10

    m_score = min(m_score, 30)

    total = f_score + t_score + m_score
    return min(round(total, 1), 100)


def _last(series: pd.Series) -> Optional[float]:
    if series.empty or pd.isna(series.iloc[-1]):
        return None
    return round(float(series.iloc[-1]), 4)


def _return(close: pd.Series, periods: int) -> Optional[float]:
    if len(close) <= periods:
        return None
    try:
        ret = ((close.iloc[-1] / close.iloc[-(periods + 1)]) - 1) * 100
        return round(ret, 2)
    except Exception:
        return None
