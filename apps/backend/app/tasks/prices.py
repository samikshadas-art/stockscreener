import asyncio
import logging
from sqlalchemy import select
from app.tasks.celery_app import celery_app
from app.models.stock import Stock
from app.services.data_ingestion import fetch_and_store_price_history

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.prices.refresh_eod_prices", bind=True, max_retries=3)
def refresh_eod_prices(self, exchanges: list[str] = None):
    """Fetch and store latest EOD prices for all active stocks."""
    from app.core.database import AsyncSessionLocal

    async def _run():
        async with AsyncSessionLocal() as db:
            stmt = select(Stock).where(Stock.is_active == True)
            if exchanges:
                stmt = stmt.where(Stock.exchange.in_(exchanges))
            result = await db.execute(stmt)
            stocks = result.scalars().all()

            logger.info(f"Refreshing prices for {len(stocks)} stocks")
            for stock in stocks:
                count = await fetch_and_store_price_history(
                    db, stock.id, stock.symbol, stock.exchange, days=5
                )
                logger.debug(f"  {stock.symbol}: {count} rows")

    asyncio.get_event_loop().run_until_complete(_run())
    logger.info("EOD price refresh complete")
