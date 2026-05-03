import secrets
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.portfolio import Portfolio, Holding, Watchlist, WatchlistItem
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse, PortfolioPerformance,
    HoldingCreate, HoldingUpdate,
    WatchlistCreate, WatchlistItemAdd,
)
from app.services.portfolio import get_portfolio_performance

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


# ─── Portfolios ─────────────────────────────────────────────────────────────

@router.get("", response_model=list[PortfolioResponse])
async def list_portfolios(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Portfolio).order_by(Portfolio.created_at.desc()))
    portfolios = result.scalars().all()
    out = []
    for p in portfolios:
        h_count = await db.execute(
            select(Holding).where(Holding.portfolio_id == p.id)
        )
        out.append(PortfolioResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            benchmark=p.benchmark,
            currency=p.currency,
            is_public=p.is_public,
            share_token=p.share_token,
            holding_count=len(h_count.scalars().all()),
        ))
    return out


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(req: PortfolioCreate, db: AsyncSession = Depends(get_db)):
    portfolio = Portfolio(
        name=req.name,
        description=req.description,
        benchmark=req.benchmark,
        currency=req.currency,
        is_public=req.is_public,
        share_token=secrets.token_urlsafe(16) if req.is_public else None,
        # In MVP: no user_id enforcement; add auth later
        user_id=uuid.uuid4(),  # placeholder
    )
    db.add(portfolio)
    await db.commit()
    await db.refresh(portfolio)
    return PortfolioResponse(
        id=portfolio.id, name=portfolio.name, description=portfolio.description,
        benchmark=portfolio.benchmark, currency=portfolio.currency,
        is_public=portfolio.is_public, share_token=portfolio.share_token,
        holding_count=0,
    )


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(portfolio_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    h = await db.execute(select(Holding).where(Holding.portfolio_id == p.id))
    return PortfolioResponse(
        id=p.id, name=p.name, description=p.description,
        benchmark=p.benchmark, currency=p.currency,
        is_public=p.is_public, share_token=p.share_token,
        holding_count=len(h.scalars().all()),
    )


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: uuid.UUID, req: PortfolioUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if req.name is not None:
        p.name = req.name
    if req.description is not None:
        p.description = req.description
    if req.benchmark is not None:
        p.benchmark = req.benchmark
    if req.is_public is not None:
        p.is_public = req.is_public
        if req.is_public and not p.share_token:
            p.share_token = secrets.token_urlsafe(16)
    await db.commit()
    await db.refresh(p)
    h = await db.execute(select(Holding).where(Holding.portfolio_id == p.id))
    return PortfolioResponse(
        id=p.id, name=p.name, description=p.description,
        benchmark=p.benchmark, currency=p.currency,
        is_public=p.is_public, share_token=p.share_token,
        holding_count=len(h.scalars().all()),
    )


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(portfolio_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    await db.delete(p)
    await db.commit()


@router.get("/{portfolio_id}/performance")
async def get_performance(portfolio_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Full P&L with per-holding breakdown, allocation, and live prices."""
    perf = await get_portfolio_performance(db, portfolio_id)
    if not perf:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return perf


# ─── Holdings ───────────────────────────────────────────────────────────────

@router.post("/{portfolio_id}/holdings", status_code=status.HTTP_201_CREATED)
async def add_holding(
    portfolio_id: uuid.UUID,
    req: HoldingCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Portfolio not found")

    holding = Holding(
        portfolio_id=portfolio_id,
        stock_id=req.stock_id,
        quantity=req.quantity,
        avg_buy_price=req.avg_buy_price,
        buy_date=req.buy_date,
        notes=req.notes,
    )
    db.add(holding)
    await db.commit()
    await db.refresh(holding)
    return {"id": holding.id, "message": "Holding added"}


@router.put("/{portfolio_id}/holdings/{holding_id}")
async def update_holding(
    portfolio_id: uuid.UUID,
    holding_id: int,
    req: HoldingUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Holding).where(Holding.id == holding_id, Holding.portfolio_id == portfolio_id)
    )
    holding = result.scalar_one_or_none()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")

    if req.quantity is not None:
        holding.quantity = req.quantity
    if req.avg_buy_price is not None:
        holding.avg_buy_price = req.avg_buy_price
    if req.buy_date is not None:
        holding.buy_date = req.buy_date
    if req.notes is not None:
        holding.notes = req.notes

    await db.commit()
    return {"message": "Holding updated"}


@router.delete("/{portfolio_id}/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holding(
    portfolio_id: uuid.UUID,
    holding_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Holding).where(Holding.id == holding_id, Holding.portfolio_id == portfolio_id)
    )
    holding = result.scalar_one_or_none()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    await db.delete(holding)
    await db.commit()


# ─── Public Share ────────────────────────────────────────────────────────────

@router.get("/share/{token}")
async def get_shared_portfolio(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Portfolio).where(Portfolio.share_token == token, Portfolio.is_public == True)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found or not public")
    perf = await get_portfolio_performance(db, p.id)
    return perf
