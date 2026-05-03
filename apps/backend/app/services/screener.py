"""
Screener Engine — dynamically builds SQL from filter conditions.
Supports AND/OR logic, all fundamental + technical + price parameters.
"""
from typing import Any
from sqlalchemy import and_, or_, select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import Stock, Fundamental, Technical
from app.schemas.screener import FilterCondition, ScreenerRunRequest, ScreenerResultRow


# Map filter field names → (table alias, column name)
FIELD_MAP: dict[str, tuple[str, str]] = {
    # Fundamentals
    "market_cap":         ("f", "market_cap"),
    "pe_ratio":           ("f", "pe_ratio"),
    "forward_pe":         ("f", "forward_pe"),
    "pb_ratio":           ("f", "pb_ratio"),
    "ev_ebitda":          ("f", "ev_ebitda"),
    "price_to_sales":     ("f", "price_to_sales"),
    "roe":                ("f", "roe"),
    "roce":               ("f", "roce"),
    "roa":                ("f", "roa"),
    "net_margin":         ("f", "net_margin"),
    "operating_margin":   ("f", "operating_margin"),
    "debt_to_equity":     ("f", "debt_to_equity"),
    "current_ratio":      ("f", "current_ratio"),
    "eps":                ("f", "eps"),
    "eps_growth_yoy":     ("f", "eps_growth_yoy"),
    "revenue_growth_yoy": ("f", "revenue_growth_yoy"),
    "dividend_yield":     ("f", "dividend_yield"),
    "piotroski_score":    ("f", "piotroski_score"),
    "altman_z_score":     ("f", "altman_z_score"),
    "composite_score":    ("f", "composite_score"),
    # Technicals
    "rsi_14":             ("t", "rsi_14"),
    "macd":               ("t", "macd"),
    "macd_signal":        ("t", "macd_signal"),
    "sma_20":             ("t", "sma_20"),
    "sma_50":             ("t", "sma_50"),
    "sma_100":            ("t", "sma_100"),
    "sma_200":            ("t", "sma_200"),
    "ema_20":             ("t", "ema_20"),
    "week_52_high":       ("t", "week_52_high"),
    "week_52_low":        ("t", "week_52_low"),
    "pct_change_1d":      ("t", "pct_change_1d"),
    "pct_change_1w":      ("t", "pct_change_1w"),
    "pct_change_1m":      ("t", "pct_change_1m"),
    "pct_change_3m":      ("t", "pct_change_3m"),
    "pct_change_6m":      ("t", "pct_change_6m"),
    "pct_change_1y":      ("t", "pct_change_1y"),
    "volatility_30d":     ("t", "volatility_30d"),
    "beta":               ("t", "beta"),
    "relative_volume":    ("t", "relative_volume"),
    "atr_14":             ("t", "atr_14"),
}

SORTABLE_COLS = {
    "market_cap": Fundamental.market_cap,
    "pe_ratio": Fundamental.pe_ratio,
    "roe": Fundamental.roe,
    "composite_score": Fundamental.composite_score,
    "rsi_14": Technical.rsi_14,
    "pct_change_1d": Technical.pct_change_1d,
    "pct_change_1m": Technical.pct_change_1m,
    "pct_change_1y": Technical.pct_change_1y,
    "name": Stock.name,
    "symbol": Stock.symbol,
}


def _apply_operator(column, operator: str, value: Any):
    if operator == "gt":
        return column > value
    elif operator == "lt":
        return column < value
    elif operator == "gte":
        return column >= value
    elif operator == "lte":
        return column <= value
    elif operator == "eq":
        return column == value
    elif operator == "neq":
        return column != value
    elif operator == "between":
        lo, hi = value[0], value[1]
        return and_(column >= lo, column <= hi)
    elif operator == "in":
        return column.in_(value)
    raise ValueError(f"Unknown operator: {operator}")


def _get_column(table_alias: str, col_name: str):
    if table_alias == "f":
        return getattr(Fundamental, col_name)
    elif table_alias == "t":
        return getattr(Technical, col_name)
    raise ValueError(f"Unknown table alias: {table_alias}")


async def run_screener(db: AsyncSession, req: ScreenerRunRequest) -> tuple[int, list]:
    """
    Execute screener query. Returns (total_count, rows).
    Joins stocks → latest fundamentals → latest technicals.
    Applies filters, sorting, pagination.
    """
    # Subquery: latest fundamental date per stock
    latest_f = (
        select(Fundamental.stock_id, func.max(Fundamental.date).label("max_date"))
        .group_by(Fundamental.stock_id)
        .subquery("latest_f")
    )

    # Subquery: latest technical date per stock
    latest_t = (
        select(Technical.stock_id, func.max(Technical.date).label("max_date"))
        .group_by(Technical.stock_id)
        .subquery("latest_t")
    )

    # Main query
    stmt = (
        select(Stock, Fundamental, Technical)
        .join(latest_f, Stock.id == latest_f.c.stock_id)
        .join(
            Fundamental,
            and_(
                Fundamental.stock_id == Stock.id,
                Fundamental.date == latest_f.c.max_date,
            ),
        )
        .join(latest_t, Stock.id == latest_t.c.stock_id, isouter=True)
        .join(
            Technical,
            and_(
                Technical.stock_id == Stock.id,
                Technical.date == latest_t.c.max_date,
            ),
            isouter=True,
        )
        .where(Stock.is_active == True)
    )

    # Exchange filter
    if req.exchange:
        stmt = stmt.where(Stock.exchange.in_(req.exchange))

    # Build filter conditions
    conditions = []
    for fc in req.filters:
        if fc.field not in FIELD_MAP:
            continue
        table_alias, col_name = FIELD_MAP[fc.field]
        col = _get_column(table_alias, col_name)
        try:
            cond = _apply_operator(col, fc.operator, fc.value)
            conditions.append(cond)
        except Exception:
            continue

    if conditions:
        combined = and_(*conditions) if req.logic == "AND" else or_(*conditions)
        stmt = stmt.where(combined)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Sorting
    sort_col = SORTABLE_COLS.get(req.sort_by, Fundamental.market_cap)
    if req.sort_order == "desc":
        stmt = stmt.order_by(sort_col.desc().nullslast())
    else:
        stmt = stmt.order_by(sort_col.asc().nullsfirst())

    # Pagination
    offset = (req.page - 1) * req.per_page
    stmt = stmt.offset(offset).limit(req.per_page)

    result = await db.execute(stmt)
    rows = result.all()

    return total, rows


def build_screener_row(stock: Stock, fund: Fundamental, tech: Technical) -> dict:
    """Flatten joined row into a flat dict for the response."""
    row = {
        "id": stock.id,
        "symbol": stock.symbol,
        "exchange": stock.exchange,
        "name": stock.name,
        "sector": stock.sector,
        "market_cap_category": stock.market_cap_category,
        "currency": stock.currency,
    }
    if fund:
        row.update({
            "market_cap": fund.market_cap,
            "pe_ratio": fund.pe_ratio,
            "forward_pe": fund.forward_pe,
            "pb_ratio": fund.pb_ratio,
            "ev_ebitda": fund.ev_ebitda,
            "roe": fund.roe,
            "roce": fund.roce,
            "debt_to_equity": fund.debt_to_equity,
            "eps": fund.eps,
            "eps_growth_yoy": fund.eps_growth_yoy,
            "revenue_growth_yoy": fund.revenue_growth_yoy,
            "dividend_yield": fund.dividend_yield,
            "piotroski_score": fund.piotroski_score,
            "composite_score": fund.composite_score,
        })
    if tech:
        row.update({
            "current_price": None,  # populated by price feed service
            "pct_change_1d": tech.pct_change_1d,
            "rsi_14": tech.rsi_14,
            "macd": tech.macd,
            "sma_20": tech.sma_20,
            "sma_50": tech.sma_50,
            "sma_200": tech.sma_200,
            "week_52_high": tech.week_52_high,
            "week_52_low": tech.week_52_low,
            "pct_change_1w": tech.pct_change_1w,
            "pct_change_1m": tech.pct_change_1m,
            "pct_change_1y": tech.pct_change_1y,
            "volatility_30d": tech.volatility_30d,
            "beta": tech.beta,
        })
    return row
