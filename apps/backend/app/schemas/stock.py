from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class StockBase(BaseModel):
    symbol: str
    exchange: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap_category: Optional[str] = None
    currency: str = "INR"
    country: str = "IN"


class StockSearchResult(BaseModel):
    id: int
    symbol: str
    exchange: str
    name: str
    sector: Optional[str] = None
    currency: str
    logo_url: Optional[str] = None

    model_config = {"from_attributes": True}


class StockOverview(BaseModel):
    id: int
    symbol: str
    exchange: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap_category: Optional[str] = None
    currency: str
    description: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None

    # Latest price data
    current_price: Optional[float] = None
    pct_change_1d: Optional[float] = None
    volume: Optional[int] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None

    # Fundamentals
    market_cap: Optional[int] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    dividend_yield: Optional[float] = None
    composite_score: Optional[float] = None

    # Technicals
    rsi_14: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None

    model_config = {"from_attributes": True}


class PricePoint(BaseModel):
    date: date
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[int]

    model_config = {"from_attributes": True}


class PriceHistoryResponse(BaseModel):
    symbol: str
    exchange: str
    interval: str
    data: list[PricePoint]
