"""
One-time seed script: populate stocks + backfill 1 year of price history
+ compute fundamentals + technicals for all seeded stocks.

Usage:
  cd apps/backend
  python scripts/seed_stocks.py --exchange NSE --limit 20
"""
import asyncio
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.services.data_ingestion import (
    NSE_SYMBOLS, US_SYMBOLS,
    fetch_and_upsert_stock,
    fetch_and_upsert_fundamentals,
    fetch_and_store_price_history,
)
from app.services.technicals import compute_and_store_technicals

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


async def seed(exchange: str, limit: int):
    if exchange in ("NSE", "BSE"):
        symbols = [(s, exchange, "INR") for s in NSE_SYMBOLS[:limit]]
    else:
        symbols = [(s, exchange, "USD") for s in US_SYMBOLS[:limit]]

    logger.info(f"Seeding {len(symbols)} stocks for {exchange}")

    async with AsyncSessionLocal() as db:
        for symbol, exch, currency in symbols:
            logger.info(f"Processing {symbol} ({exch})...")

            # 1. Upsert stock master
            stock_id = await fetch_and_upsert_stock(db, symbol, exch, currency)
            if not stock_id:
                logger.warning(f"  Skipping {symbol} — no data")
                continue

            # 2. Fundamentals
            ok = await fetch_and_upsert_fundamentals(db, stock_id, symbol, exch)
            logger.info(f"  Fundamentals: {'✓' if ok else '✗'}")

            # 3. Price history (1 year)
            count = await fetch_and_store_price_history(db, stock_id, symbol, exch, days=365)
            logger.info(f"  Price history: {count} rows")

            # 4. Technical indicators
            ok = await compute_and_store_technicals(db, stock_id)
            logger.info(f"  Technicals: {'✓' if ok else '✗'}")

            # Rate limiting: avoid hitting yfinance too fast
            await asyncio.sleep(1.0)

    logger.info("Seeding complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed stock data")
    parser.add_argument("--exchange", default="NSE", choices=["NSE", "BSE", "NYSE", "NASDAQ"])
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    asyncio.run(seed(args.exchange, args.limit))
