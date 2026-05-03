import asyncio
import logging
from sqlalchemy import select
from app.tasks.celery_app import celery_app
from app.models.stock import Stock
from app.services.technicals import compute_and_store_technicals

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.technicals.compute_all_technicals", bind=True)
def compute_all_technicals(self, exchanges: list[str] = None):
    """Compute technical indicators for all active stocks."""
    from app.core.database import AsyncSessionLocal

    async def _run():
        async with AsyncSessionLocal() as db:
            stmt = select(Stock).where(Stock.is_active == True)
            if exchanges:
                stmt = stmt.where(Stock.exchange.in_(exchanges))
            result = await db.execute(stmt)
            stocks = result.scalars().all()

            logger.info(f"Computing technicals for {len(stocks)} stocks")
            for stock in stocks:
                ok = await compute_and_store_technicals(db, stock.id)
                logger.debug(f"  {stock.symbol}: {'ok' if ok else 'skipped'}")

    asyncio.get_event_loop().run_until_complete(_run())
    logger.info("Technicals computation complete")
