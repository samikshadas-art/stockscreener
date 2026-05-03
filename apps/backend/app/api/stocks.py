from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_

from app.core.database import get_db
from app.core.redis import cache_get, cache_set
from app.core.config import settings
from app.models.stock import Stock, Fundamental, Technical, PriceHistory
from app.schemas.stock import StockSearchResult, StockOverview, PriceHistoryResponse, PricePoint
from app.services.data_ingestion import get_live_price

router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get("/search", response_model=list[StockSearchResult])
async def search_stocks(
    q: str = Query(..., min_length=1),
    exchange: Optional[str] = None,
    limit: int = Query(default=10, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Full-text search on symbol and company name."""
    pattern = f"%{q.upper()}%"
    stmt = (
        select(Stock)
        .where(
            Stock.is_active == True,
            or_(
                Stock.symbol.ilike(pattern),
                Stock.name.ilike(f"%{q}%"),
            ),
        )
        .limit(limit)
    )
    if exchange:
        stmt = stmt.where(Stock.exchange == exchange.upper())

    result = await db.execute(stmt)
    stocks = result.scalars().all()
    return [StockSearchResult.model_validate(s) for s in stocks]


@router.get("/{symbol}/overview", response_model=StockOverview)
async def get_stock_overview(
    symbol: str,
    exchange: str = Query(default="NSE"),
    db: AsyncSession = Depends(get_db),
):
    """Full stock overview: info + latest fundamentals + technicals."""
    cache_key = f"stock:overview:{symbol}:{exchange}"
    cached = await cache_get(cache_key)
    if cached:
        return StockOverview(**cached)

    # Fetch stock
    result = await db.execute(
        select(Stock).where(
            Stock.symbol == symbol.upper(),
            Stock.exchange == exchange.upper(),
        )
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found on {exchange}")

    # Latest fundamentals
    f_result = await db.execute(
        select(Fundamental)
        .where(Fundamental.stock_id == stock.id)
        .order_by(Fundamental.date.desc())
        .limit(1)
    )
    fund = f_result.scalar_one_or_none()

    # Latest technicals
    t_result = await db.execute(
        select(Technical)
        .where(Technical.stock_id == stock.id)
        .order_by(Technical.date.desc())
        .limit(1)
    )
    tech = t_result.scalar_one_or_none()

    # Live price
    live = await get_live_price(symbol, exchange)

    overview = {
        "id": stock.id,
        "symbol": stock.symbol,
        "exchange": stock.exchange,
        "name": stock.name,
        "sector": stock.sector,
        "industry": stock.industry,
        "market_cap_category": stock.market_cap_category,
        "currency": stock.currency,
        "description": stock.description,
        "website": stock.website,
        "logo_url": stock.logo_url,
        "current_price": live.get("price") if live else None,
        "pct_change_1d": live.get("change_pct") if live else (tech.pct_change_1d if tech else None),
        "volume": live.get("volume") if live else None,
        "week_52_high": tech.week_52_high if tech else None,
        "week_52_low": tech.week_52_low if tech else None,
        "market_cap": fund.market_cap if fund else None,
        "pe_ratio": fund.pe_ratio if fund else None,
        "pb_ratio": fund.pb_ratio if fund else None,
        "roe": fund.roe if fund else None,
        "dividend_yield": fund.dividend_yield if fund else None,
        "composite_score": fund.composite_score if fund else None,
        "rsi_14": tech.rsi_14 if tech else None,
        "sma_50": tech.sma_50 if tech else None,
        "sma_200": tech.sma_200 if tech else None,
    }

    await cache_set(cache_key, overview, ttl=settings.CACHE_TTL_STOCK_OVERVIEW)
    return StockOverview(**overview)


@router.get("/{symbol}/price-history", response_model=PriceHistoryResponse)
async def get_price_history(
    symbol: str,
    exchange: str = Query(default="NSE"),
    interval: str = Query(default="1d"),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """OHLCV price history for charts."""
    result = await db.execute(
        select(Stock).where(
            Stock.symbol == symbol.upper(),
            Stock.exchange == exchange.upper(),
        )
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    # Default: last 1 year
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=365)

    stmt = (
        select(PriceHistory)
        .where(
            PriceHistory.stock_id == stock.id,
            PriceHistory.date >= from_date,
            PriceHistory.date <= to_date,
        )
        .order_by(PriceHistory.date.asc())
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    data = [
        PricePoint(
            date=r.date,
            open=r.open,
            high=r.high,
            low=r.low,
            close=r.close,
            volume=r.volume,
        )
        for r in rows
    ]

    return PriceHistoryResponse(
        symbol=symbol.upper(),
        exchange=exchange.upper(),
        interval=interval,
        data=data,
    )


@router.get("/{symbol}/peers", response_model=list[StockSearchResult])
async def get_peers(
    symbol: str,
    exchange: str = Query(default="NSE"),
    limit: int = Query(default=8, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Return same-sector peer stocks."""
    result = await db.execute(
        select(Stock).where(
            Stock.symbol == symbol.upper(),
            Stock.exchange == exchange.upper(),
        )
    )
    stock = result.scalar_one_or_none()
    if not stock or not stock.sector:
        return []

    peers_result = await db.execute(
        select(Stock)
        .where(
            Stock.sector == stock.sector,
            Stock.exchange == exchange.upper(),
            Stock.id != stock.id,
            Stock.is_active == True,
        )
        .limit(limit)
    )
    return [StockSearchResult.model_validate(s) for s in peers_result.scalars().all()]
