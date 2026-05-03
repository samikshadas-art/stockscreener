import asyncio
import logging
from sqlalchemy import select
from app.tasks.celery_app import celery_app
from app.models.stock import Stock
from app.services.data_ingestion import fetch_and_upsert_fundamentals
from app.services.technicals import compute_composite_score

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.fundamentals.refresh_all_fundamentals", bind=True)
def refresh_all_fundamentals(self):
    """Weekly: refresh fundamentals for all stocks + recompute composite score."""
    from app.core.database import AsyncSessionLocal

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Stock).where(Stock.is_active == True))
            stocks = result.scalars().all()

            logger.info(f"Refreshing fundamentals for {len(stocks)} stocks")
            for stock in stocks:
                ok = await fetch_and_upsert_fundamentals(
                    db, stock.id, stock.symbol, stock.exchange
                )
                logger.debug(f"  {stock.symbol}: {'ok' if ok else 'failed'}")

    asyncio.get_event_loop().run_until_complete(_run())
    logger.info("Fundamentals refresh complete")
