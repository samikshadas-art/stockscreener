from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
import uuid


class FilterCondition(BaseModel):
    field: str
    operator: Literal["gt", "lt", "gte", "lte", "eq", "neq", "between", "in"]
    value: Any
    # 'between' uses value as [min, max]; 'in' uses value as list


class ScreenerRunRequest(BaseModel):
    filters: list[FilterCondition] = Field(default_factory=list)
    logic: Literal["AND", "OR"] = "AND"
    exchange: list[str] = Field(default_factory=lambda: ["NSE", "BSE", "NYSE", "NASDAQ"])
    sort_by: str = "market_cap"
    sort_order: Literal["asc", "desc"] = "desc"
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=200)
    columns: Optional[list[str]] = None


class ScreenerResultRow(BaseModel):
    id: int
    symbol: str
    exchange: str
    name: str
    sector: Optional[str] = None
    market_cap_category: Optional[str] = None
    currency: str

    current_price: Optional[float] = None
    pct_change_1d: Optional[float] = None

    # Fundamentals
    market_cap: Optional[int] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    pb_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    roe: Optional[float] = None
    roce: Optional[float] = None
    debt_to_equity: Optional[float] = None
    eps: Optional[float] = None
    eps_growth_yoy: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    dividend_yield: Optional[float] = None
    piotroski_score: Optional[int] = None
    composite_score: Optional[float] = None

    # Technicals
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    pct_change_1w: Optional[float] = None
    pct_change_1m: Optional[float] = None
    pct_change_1y: Optional[float] = None
    volatility_30d: Optional[float] = None
    beta: Optional[float] = None

    model_config = {"from_attributes": True}


class ScreenerRunResponse(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    results: list[ScreenerResultRow]


class SaveScreenerRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    filters: list[FilterCondition]
    logic: Literal["AND", "OR"] = "AND"
    columns: Optional[list[str]] = None
    is_public: bool = False


class ScreenerResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    filters: list[FilterCondition]
    logic: str
    columns: Optional[list[str]]
    is_public: bool
    share_token: Optional[str]

    model_config = {"from_attributes": True}
