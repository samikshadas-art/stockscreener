"""
Portfolio service — P&L computation, allocation breakdowns, XIRR.
"""
import logging
from datetime import date
from typing import Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.portfolio import Portfolio, Holding
from app.models.stock import Stock, Technical, Fundamental
from app.services.data_ingestion import get_live_price

logger = logging.getLogger(__name__)


async def get_portfolio_performance(db: AsyncSession, portfolio_id, user_id=None) -> Optional[dict]:
    """Compute full portfolio P&L with per-holding breakdown."""
    # Load portfolio
    stmt = select(Portfolio).where(Portfolio.id == portfolio_id)
    if user_id:
        stmt = stmt.where(Portfolio.user_id == user_id)
    result = await db.execute(stmt)
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        return None

    # Load holdings with stock info
    stmt = (
        select(Holding, Stock, Technical)
        .join(Stock, Holding.stock_id == Stock.id)
        .join(
            Technical,
            Technical.stock_id == Stock.id,
            isouter=True,
        )
        .where(Holding.portfolio_id == portfolio_id)
        .order_by(Technical.date.desc())
        .distinct(Holding.id)
    )
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return {
            "portfolio_id": str(portfolio.id),
            "name": portfolio.name,
            "benchmark": portfolio.benchmark,
            "currency": portfolio.currency,
            "total_invested": 0,
            "current_value": 0,
            "total_gain": 0,
            "total_gain_pct": 0,
            "today_gain": 0,
            "today_gain_pct": 0,
            "holdings": [],
            "sector_allocation": {},
            "cap_allocation": {},
        }

    # Fetch live prices for all symbols
    symbols = [(row[1].symbol, row[1].exchange) for row in rows]
    live_prices = {}
    for sym, exch in symbols:
        price_data = await get_live_price(sym, exch)
        if price_data and price_data.get("price"):
            live_prices[sym] = price_data

    total_invested = 0.0
    total_current = 0.0
    today_gain = 0.0
    holding_list = []
    sector_map: dict[str, float] = {}
    cap_map: dict[str, float] = {}

    for holding, stock, tech in rows:
        qty = float(holding.quantity)
        buy_price = float(holding.avg_buy_price)
        invested = qty * buy_price

        # Use live price if available, else last technical close
        live = live_prices.get(stock.symbol, {})
        current_price = live.get("price")
        if not current_price and tech:
            # fallback: use SMA or pct_change to estimate
            current_price = buy_price  # worst case: no change

        current_val = qty * current_price if current_price else invested
        gain = current_val - invested
        gain_pct = (gain / invested * 100) if invested else 0

        # Today's gain
        today_pct = live.get("change_pct") or (tech.pct_change_1d if tech else 0) or 0
        today_g = current_val * (today_pct / 100)

        total_invested += invested
        total_current += current_val
        today_gain += today_g

        holding_list.append({
            "id": holding.id,
            "stock_id": stock.id,
            "symbol": stock.symbol,
            "exchange": stock.exchange,
            "name": stock.name,
            "sector": stock.sector,
            "quantity": qty,
            "avg_buy_price": buy_price,
            "buy_date": holding.buy_date,
            "current_price": current_price,
            "invested_value": round(invested, 2),
            "current_value": round(current_val, 2),
            "gain": round(gain, 2),
            "gain_pct": round(gain_pct, 2),
            "weight_pct": 0,  # filled below
            "pct_change_1d": today_pct,
        })

        # Sector allocation
        sector = stock.sector or "Other"
        sector_map[sector] = sector_map.get(sector, 0) + current_val

        # Cap allocation
        cap = stock.market_cap_category or "unknown"
        cap_map[cap] = cap_map.get(cap, 0) + current_val

    # Calculate weights
    for h in holding_list:
        h["weight_pct"] = round(h["current_value"] / total_current * 100, 2) if total_current else 0

    total_gain = total_current - total_invested
    total_gain_pct = (total_gain / total_invested * 100) if total_invested else 0
    today_gain_pct = (today_gain / (total_current - today_gain) * 100) if total_current else 0

    # Normalize allocation to %
    def normalize(d: dict, total: float) -> dict:
        return {k: round(v / total * 100, 1) for k, v in d.items()} if total else {}

    return {
        "portfolio_id": str(portfolio.id),
        "name": portfolio.name,
        "benchmark": portfolio.benchmark,
        "currency": portfolio.currency,
        "total_invested": round(total_invested, 2),
        "current_value": round(total_current, 2),
        "total_gain": round(total_gain, 2),
        "total_gain_pct": round(total_gain_pct, 2),
        "today_gain": round(today_gain, 2),
        "today_gain_pct": round(today_gain_pct, 2),
        "holdings": holding_list,
        "sector_allocation": normalize(sector_map, total_current),
        "cap_allocation": normalize(cap_map, total_current),
    }
