"""
Data ingestion service using yfinance.
Handles fetching, normalizing, and storing stock data.
"""
import asyncio
import logging
from datetime import date, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.stock import Stock, Fundamental, Technical, PriceHistory

logger = logging.getLogger(__name__)

# NSE suffix for yfinance
EXCHANGE_SUFFIX = {
    "NSE": ".NS",
    "BSE": ".BO",
    "NYSE": "",
    "NASDAQ": "",
}

# NIFTY 500 sample (add more as needed)
NSE_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
    "LT", "ASIANPAINT", "AXISBANK", "MARUTI", "TITAN",
    "SUNPHARMA", "WIPRO", "ULTRACEMCO", "HCLTECH", "BAJFINANCE",
    "NESTLEIND", "POWERGRID", "NTPC", "TECHM", "BAJAJFINSV",
    "ONGC", "ADANIENT", "ADANIPORTS", "JSWSTEEL", "TATASTEEL",
    "TATAMOTORS", "M&M", "DIVISLAB", "DRREDDY", "CIPLA",
    "COALINDIA", "GRASIM", "HINDALCO", "BPCL", "IOC",
    "EICHERMOT", "UPL", "SHREECEM", "INDUSINDBK", "BRITANNIA",
    "APOLLOHOSP", "HDFCLIFE", "SBILIFE", "PIDILITIND", "DABUR",
]

US_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "BRK-B", "JPM", "JNJ",
    "V", "PG", "UNH", "HD", "MA",
    "DIS", "PYPL", "BAC", "ADBE", "CRM",
    "NFLX", "XOM", "INTC", "VZ", "CSCO",
    "PFE", "KO", "PEP", "T", "WMT",
]


def _yf_symbol(symbol: str, exchange: str) -> str:
    suffix = EXCHANGE_SUFFIX.get(exchange, "")
    return f"{symbol}{suffix}"


def _categorize_market_cap(market_cap: Optional[float], currency: str = "INR") -> str:
    if not market_cap:
        return "unknown"
    # INR thresholds (in crores → convert from absolute)
    if currency == "INR":
        crores = market_cap / 1e7
        if crores >= 20000:
            return "large"
        elif crores >= 5000:
            return "mid"
        elif crores >= 500:
            return "small"
        return "micro"
    else:
        # USD billions
        billions = market_cap / 1e9
        if billions >= 10:
            return "large"
        elif billions >= 2:
            return "mid"
        elif billions >= 0.3:
            return "small"
        return "micro"


async def fetch_and_upsert_stock(
    db: AsyncSession,
    symbol: str,
    exchange: str,
    currency: str = "INR",
) -> Optional[Stock]:
    """Fetch stock info from yfinance and upsert into stocks table."""
    yf_sym = _yf_symbol(symbol, exchange)
    try:
        ticker = yf.Ticker(yf_sym)
        info = ticker.info

        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            logger.warning(f"No data found for {yf_sym}")
            return None

        stock_data = {
            "symbol": symbol,
            "exchange": exchange,
            "name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "currency": info.get("currency", currency),
            "country": info.get("country", "IN" if exchange in ("NSE", "BSE") else "US"),
            "website": info.get("website"),
            "description": (info.get("longBusinessSummary") or "")[:1000],
            "market_cap_category": _categorize_market_cap(
                info.get("marketCap"), info.get("currency", currency)
            ),
            "is_active": True,
        }

        # Upsert stock
        stmt = pg_insert(Stock).values(**stock_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "exchange"],
            set_={k: v for k, v in stock_data.items() if k not in ("symbol", "exchange")},
        ).returning(Stock.id)
        result = await db.execute(stmt)
        stock_id = result.scalar()
        await db.commit()

        logger.info(f"Upserted stock {symbol} ({exchange}) → id={stock_id}")
        return stock_id

    except Exception as e:
        logger.error(f"Error fetching {yf_sym}: {e}")
        await db.rollback()
        return None


async def fetch_and_upsert_fundamentals(
    db: AsyncSession,
    stock_id: int,
    symbol: str,
    exchange: str,
) -> bool:
    """Fetch fundamentals from yfinance and upsert."""
    yf_sym = _yf_symbol(symbol, exchange)
    try:
        ticker = yf.Ticker(yf_sym)
        info = ticker.info
        today = date.today()

        fund_data = {
            "stock_id": stock_id,
            "date": today,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "roe": _pct(info.get("returnOnEquity")),
            "roa": _pct(info.get("returnOnAssets")),
            "net_margin": _pct(info.get("profitMargins")),
            "operating_margin": _pct(info.get("operatingMargins")),
            "gross_margin": _pct(info.get("grossMargins")),
            "eps": info.get("trailingEps"),
            "eps_growth_yoy": _pct(info.get("earningsGrowth")),
            "revenue_growth_yoy": _pct(info.get("revenueGrowth")),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "dividend_yield": _pct(info.get("dividendYield")),
            "payout_ratio": _pct(info.get("payoutRatio")),
            "beta": info.get("beta"),
        }

        stmt = pg_insert(Fundamental).values(**fund_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["stock_id", "date"],
            set_={k: v for k, v in fund_data.items() if k not in ("stock_id", "date")},
        )
        await db.execute(stmt)
        await db.commit()
        return True

    except Exception as e:
        logger.error(f"Error fetching fundamentals for {yf_sym}: {e}")
        await db.rollback()
        return False


async def fetch_and_store_price_history(
    db: AsyncSession,
    stock_id: int,
    symbol: str,
    exchange: str,
    days: int = 365,
) -> int:
    """Download OHLCV history and bulk-insert into price_history."""
    yf_sym = _yf_symbol(symbol, exchange)
    try:
        end = date.today()
        start = end - timedelta(days=days)
        df = yf.download(yf_sym, start=start, end=end, progress=False, auto_adjust=True)

        if df.empty:
            return 0

        rows = []
        for idx, row in df.iterrows():
            rows.append({
                "stock_id": stock_id,
                "date": idx.date(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "adj_close": float(row["Close"]),
                "volume": int(row["Volume"]),
            })

        if rows:
            stmt = pg_insert(PriceHistory).values(rows)
            stmt = stmt.on_conflict_do_nothing()
            await db.execute(stmt)
            await db.commit()

        return len(rows)

    except Exception as e:
        logger.error(f"Error fetching price history for {yf_sym}: {e}")
        await db.rollback()
        return 0


def _pct(value) -> Optional[float]:
    """Convert decimal to percentage (0.18 → 18.0)."""
    if value is None:
        return None
    return round(float(value) * 100, 2)


async def get_live_price(symbol: str, exchange: str) -> Optional[dict]:
    """Get current price from yfinance (for WebSocket / fallback)."""
    yf_sym = _yf_symbol(symbol, exchange)
    try:
        ticker = yf.Ticker(yf_sym)
        info = ticker.info
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
        change = None
        change_pct = None
        if price and prev_close:
            change = round(price - prev_close, 2)
            change_pct = round((change / prev_close) * 100, 4)

        return {
            "symbol": symbol,
            "exchange": exchange,
            "price": price,
            "change": change,
            "change_pct": change_pct,
            "volume": info.get("regularMarketVolume"),
            "day_high": info.get("dayHigh"),
            "day_low": info.get("dayLow"),
        }
    except Exception as e:
        logger.error(f"Live price error for {yf_sym}: {e}")
        return None
