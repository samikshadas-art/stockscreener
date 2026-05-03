from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class HoldingCreate(BaseModel):
    stock_id: int
    quantity: float = Field(..., gt=0)
    avg_buy_price: float = Field(..., gt=0)
    buy_date: Optional[date] = None
    notes: Optional[str] = None


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0)
    avg_buy_price: Optional[float] = Field(None, gt=0)
    buy_date: Optional[date] = None
    notes: Optional[str] = None


class HoldingPerformance(BaseModel):
    id: int
    stock_id: int
    symbol: str
    exchange: str
    name: str
    sector: Optional[str]
    quantity: float
    avg_buy_price: float
    buy_date: Optional[date]
    current_price: float
    invested_value: float
    current_value: float
    gain: float
    gain_pct: float
    weight_pct: float
    pct_change_1d: Optional[float] = None

    model_config = {"from_attributes": True}


class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    benchmark: str = "NIFTY50"
    currency: str = "INR"
    is_public: bool = False


class PortfolioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    benchmark: Optional[str] = None
    is_public: Optional[bool] = None


class PortfolioPerformance(BaseModel):
    portfolio_id: uuid.UUID
    name: str
    benchmark: str
    currency: str
    total_invested: float
    current_value: float
    total_gain: float
    total_gain_pct: float
    today_gain: float
    today_gain_pct: float
    holdings: list[HoldingPerformance]
    sector_allocation: dict[str, float]
    cap_allocation: dict[str, float]

    model_config = {"from_attributes": True}


class PortfolioResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    benchmark: str
    currency: str
    is_public: bool
    share_token: Optional[str]
    holding_count: int = 0

    model_config = {"from_attributes": True}


class WatchlistCreate(BaseModel):
    name: str = Field(default="My Watchlist", min_length=1, max_length=100)


class WatchlistItemAdd(BaseModel):
    stock_id: int


class AlertCreate(BaseModel):
    stock_id: int
    alert_type: str  # price_above | price_below | rsi_above | rsi_below | etc.
    threshold: Optional[float] = None
    message: Optional[str] = None
