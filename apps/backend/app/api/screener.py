import secrets
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.redis import cache_get, cache_set, make_screener_cache_key
from app.core.config import settings
from app.models.screener import Screener
from app.schemas.screener import (
    ScreenerRunRequest, ScreenerRunResponse, ScreenerResultRow,
    SaveScreenerRequest, ScreenerResponse,
)
from app.services.screener import run_screener, build_screener_row

router = APIRouter(prefix="/screener", tags=["Screener"])


@router.post("/run", response_model=ScreenerRunResponse)
async def run_screener_endpoint(
    req: ScreenerRunRequest,
    db: AsyncSession = Depends(get_db),
):
    """Execute a screener query with dynamic filters."""
    cache_key = make_screener_cache_key(
        [f.model_dump() for f in req.filters],
        req.logic, req.exchange, req.sort_by, req.sort_order,
        req.page, req.per_page,
    )

    # Check cache
    cached = await cache_get(cache_key)
    if cached:
        return ScreenerRunResponse(**cached)

    total, rows = await run_screener(db, req)

    results = []
    for row in rows:
        stock, fund, tech = row[0], row[1], row[2]
        flat = build_screener_row(stock, fund, tech)
        results.append(ScreenerResultRow(**flat))

    response = ScreenerRunResponse(
        total=total,
        page=req.page,
        per_page=req.per_page,
        total_pages=(total + req.per_page - 1) // req.per_page,
        results=results,
    )

    # Cache the result
    await cache_set(cache_key, response.model_dump(), ttl=settings.CACHE_TTL_SCREENER)
    return response


@router.get("/saved", response_model=list[ScreenerResponse])
async def list_saved_screeners(db: AsyncSession = Depends(get_db)):
    """List all saved screeners (for current user — auth simplified for MVP)."""
    result = await db.execute(select(Screener).order_by(Screener.created_at.desc()))
    return result.scalars().all()


@router.post("/saved", response_model=ScreenerResponse, status_code=status.HTTP_201_CREATED)
async def save_screener(
    req: SaveScreenerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Save a named screener."""
    screener = Screener(
        name=req.name,
        description=req.description,
        filters=[f.model_dump() for f in req.filters],
        logic=req.logic,
        columns=req.columns,
        is_public=req.is_public,
        share_token=secrets.token_urlsafe(16) if req.is_public else None,
    )
    db.add(screener)
    await db.commit()
    await db.refresh(screener)
    return screener


@router.get("/saved/{screener_id}", response_model=ScreenerResponse)
async def get_saved_screener(
    screener_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Screener).where(Screener.id == screener_id))
    screener = result.scalar_one_or_none()
    if not screener:
        raise HTTPException(status_code=404, detail="Screener not found")
    return screener


@router.put("/saved/{screener_id}", response_model=ScreenerResponse)
async def update_screener(
    screener_id: uuid.UUID,
    req: SaveScreenerRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Screener).where(Screener.id == screener_id))
    screener = result.scalar_one_or_none()
    if not screener:
        raise HTTPException(status_code=404, detail="Screener not found")

    screener.name = req.name
    screener.description = req.description
    screener.filters = [f.model_dump() for f in req.filters]
    screener.logic = req.logic
    screener.columns = req.columns
    screener.is_public = req.is_public
    if req.is_public and not screener.share_token:
        screener.share_token = secrets.token_urlsafe(16)

    await db.commit()
    await db.refresh(screener)
    return screener


@router.delete("/saved/{screener_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_screener(
    screener_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Screener).where(Screener.id == screener_id))
    screener = result.scalar_one_or_none()
    if not screener:
        raise HTTPException(status_code=404, detail="Screener not found")
    await db.delete(screener)
    await db.commit()


@router.get("/share/{token}", response_model=ScreenerResponse)
async def get_shared_screener(token: str, db: AsyncSession = Depends(get_db)):
    """Public endpoint — view a shared screener by token."""
    result = await db.execute(
        select(Screener).where(Screener.share_token == token, Screener.is_public == True)
    )
    screener = result.scalar_one_or_none()
    if not screener:
        raise HTTPException(status_code=404, detail="Screener not found or not public")
    return screener
