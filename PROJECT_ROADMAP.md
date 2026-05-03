# Stock Screener + Portfolio Dashboard — Complete Build Roadmap

> **Goal:** A production-ready equity analysis and screening platform for Indian (NSE/BSE) and US (NYSE/NASDAQ) markets, built by a solo developer, designed to scale.

---

## Table of Contents

1. [Tech Stack Decisions](#1-tech-stack-decisions)
2. [System Architecture](#2-system-architecture)
3. [Database Schema Design](#3-database-schema-design)
4. [API Design](#4-api-design)
5. [Frontend Component Structure](#5-frontend-component-structure)
6. [Data Pipeline Strategy](#6-data-pipeline-strategy)
7. [Phase-by-Phase Build Plan](#7-phase-by-phase-build-plan)
8. [Deployment Plan](#8-deployment-plan)
9. [Codebase Folder Structure](#9-codebase-folder-structure)

---

## 1. Tech Stack Decisions

### Frontend
| Layer | Choice | Why |
|---|---|---|
| Framework | **Next.js 14 (App Router)** | SSR + SSG + API routes in one; great SEO; fast cold loads |
| Language | **TypeScript** | Type safety across frontend + backend contracts |
| Styling | **Tailwind CSS + shadcn/ui** | Dark mode first; fast to build; accessible components |
| Charts | **Recharts + TradingView Lightweight Charts** | Recharts for dashboards; TradingView for OHLC candlesticks |
| State | **Zustand** | Simple, performant global state for filters/portfolio |
| Data fetching | **TanStack Query (React Query)** | Caching, background refetch, pagination out of the box |
| Tables | **TanStack Table** | Virtualized, sortable, filterable — essential for screener |

### Backend
| Layer | Choice | Why |
|---|---|---|
| Runtime | **Python 3.11 + FastAPI** | Async, fast, great for finance libs (yfinance, pandas, numpy) |
| ORM | **SQLAlchemy 2.0 + Alembic** | Async support; Alembic for migrations |
| Cache | **Redis (Upstash)** | TTL-based caching for market data; pub/sub for live prices |
| Task Queue | **Celery + Redis** | Background data refresh jobs, scheduled tasks |
| WebSocket | **FastAPI WebSockets** | Live price streaming to frontend |
| Auth | **Supabase Auth (or Auth.js)** | Social login + JWT; avoid building auth from scratch |

### Database
| Layer | Choice | Why |
|---|---|---|
| Primary DB | **PostgreSQL (Supabase)** | JSONB support; great for semi-structured financial data |
| Time-series | **TimescaleDB extension** | Efficient OHLC storage and queries; built on PostgreSQL |
| Search | **PostgreSQL full-text** | Symbol/company name search without extra infra |

### Data Sources
| Source | Use Case |
|---|---|
| **yfinance** | US stocks — free, reliable for EOD + basic fundamentals |
| **NSE India unofficial API** | NSE-listed stocks, live prices during market hours |
| **Alpha Vantage** | Backup fundamental data; technicals |
| **Twelve Data** | Reliable real-time feed (freemium) |
| **Yahoo Finance API** | Global coverage fallback |

### Infrastructure
| Layer | Choice |
|---|---|
| Frontend hosting | Vercel (zero-config Next.js) |
| Backend hosting | Railway.app (FastAPI + Celery + Redis) |
| Database | Supabase (PostgreSQL + Auth + Realtime) |
| Cache | Upstash Redis (serverless, pay-per-request) |
| CDN | Vercel Edge Network |

---

## 2. System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                            │
│  Next.js 14 (Vercel)                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Screener   │  │  Portfolio   │  │  Shared Public Link  │  │
│  │  Page       │  │  Dashboard   │  │  (read-only view)    │  │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼────────────────┼─────────────────────┼──────────────┘
          │  REST / WS     │                      │
┌─────────▼────────────────▼──────────────────────▼──────────────┐
│                      API GATEWAY LAYER                          │
│  FastAPI (Railway)                                              │
│  ┌─────────────┐  ┌────────────┐  ┌──────────┐  ┌──────────┐  │
│  │ /screener   │  │ /portfolio │  │ /stocks  │  │ /share   │  │
│  │ endpoints   │  │ endpoints  │  │ endpoints│  │ endpoints│  │
│  └──────┬──────┘  └─────┬──────┘  └────┬─────┘  └──────────┘  │
└─────────┼───────────────┼──────────────┼────────────────────────┘
          │               │              │
┌─────────▼───────────────▼──────────────▼────────────────────────┐
│                      SERVICE LAYER                               │
│  ┌──────────────┐  ┌─────────────────┐  ┌───────────────────┐   │
│  │ Screener     │  │ Portfolio       │  │ Price Feed        │   │
│  │ Engine       │  │ Service         │  │ Service (WS)      │   │
│  └──────┬───────┘  └────────┬────────┘  └─────────┬─────────┘   │
└─────────┼───────────────────┼─────────────────────┼─────────────┘
          │                   │                      │
┌─────────▼───────────────────▼──────────────────────▼────────────┐
│                       DATA LAYER                                 │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐  │
│  │ PostgreSQL   │  │ Redis Cache   │  │ Celery Workers       │  │
│  │ (Supabase)   │  │ (Upstash)     │  │ (Data Refresh Jobs)  │  │
│  └──────────────┘  └───────────────┘  └──────┬───────────────┘  │
└──────────────────────────────────────────────┼──────────────────┘
                                               │
┌──────────────────────────────────────────────▼──────────────────┐
│                   EXTERNAL DATA SOURCES                          │
│  yfinance │ NSE API │ Alpha Vantage │ Twelve Data │ Yahoo Finance │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema Design

### Core Tables

```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Stocks master list
CREATE TABLE stocks (
  id SERIAL PRIMARY KEY,
  symbol TEXT NOT NULL,           -- e.g. RELIANCE, AAPL
  exchange TEXT NOT NULL,         -- NSE, BSE, NYSE, NASDAQ
  name TEXT NOT NULL,
  sector TEXT,
  industry TEXT,
  market_cap_category TEXT,       -- large/mid/small/micro cap
  currency TEXT DEFAULT 'INR',
  is_active BOOLEAN DEFAULT TRUE,
  UNIQUE(symbol, exchange)
);

-- Fundamental snapshots (daily refresh)
CREATE TABLE fundamentals (
  id SERIAL PRIMARY KEY,
  stock_id INT REFERENCES stocks(id),
  date DATE NOT NULL,
  market_cap BIGINT,
  pe_ratio NUMERIC,
  forward_pe NUMERIC,
  pb_ratio NUMERIC,
  ev_ebitda NUMERIC,
  roe NUMERIC,
  roce NUMERIC,
  debt_to_equity NUMERIC,
  eps NUMERIC,
  eps_growth_yoy NUMERIC,
  revenue_growth_yoy NUMERIC,
  dividend_yield NUMERIC,
  piotroski_score SMALLINT,
  altman_z_score NUMERIC,
  composite_score NUMERIC,       -- derived quality score
  UNIQUE(stock_id, date)
);

-- OHLCV price data (TimescaleDB hypertable)
CREATE TABLE price_history (
  time TIMESTAMPTZ NOT NULL,
  stock_id INT REFERENCES stocks(id),
  open NUMERIC,
  high NUMERIC,
  low NUMERIC,
  close NUMERIC,
  volume BIGINT,
  PRIMARY KEY (stock_id, time)
);
SELECT create_hypertable('price_history', 'time');

-- Technical indicators (daily refresh)
CREATE TABLE technicals (
  id SERIAL PRIMARY KEY,
  stock_id INT REFERENCES stocks(id),
  date DATE NOT NULL,
  rsi_14 NUMERIC,
  macd NUMERIC,
  macd_signal NUMERIC,
  macd_histogram NUMERIC,
  sma_20 NUMERIC,
  sma_50 NUMERIC,
  sma_100 NUMERIC,
  sma_200 NUMERIC,
  ema_20 NUMERIC,
  volume_avg_20d BIGINT,
  week_52_high NUMERIC,
  week_52_low NUMERIC,
  pct_change_1d NUMERIC,
  pct_change_1w NUMERIC,
  pct_change_1m NUMERIC,
  pct_change_1y NUMERIC,
  volatility_30d NUMERIC,
  UNIQUE(stock_id, date)
);

-- Saved screeners
CREATE TABLE screeners (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  description TEXT,
  filters JSONB NOT NULL,         -- array of filter conditions
  logic TEXT DEFAULT 'AND',       -- AND | OR
  columns JSONB,                  -- visible columns config
  is_public BOOLEAN DEFAULT FALSE,
  share_token TEXT UNIQUE,        -- for public link
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Portfolios
CREATE TABLE portfolios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  benchmark TEXT DEFAULT 'NIFTY50', -- NIFTY50 | SP500
  is_public BOOLEAN DEFAULT FALSE,
  share_token TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Portfolio holdings
CREATE TABLE holdings (
  id SERIAL PRIMARY KEY,
  portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
  stock_id INT REFERENCES stocks(id),
  quantity NUMERIC NOT NULL,
  avg_buy_price NUMERIC NOT NULL,
  buy_date DATE,
  notes TEXT
);

-- Watchlists
CREATE TABLE watchlists (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE watchlist_items (
  id SERIAL PRIMARY KEY,
  watchlist_id UUID REFERENCES watchlists(id) ON DELETE CASCADE,
  stock_id INT REFERENCES stocks(id),
  added_at TIMESTAMPTZ DEFAULT NOW()
);

-- Price/indicator alerts
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  stock_id INT REFERENCES stocks(id),
  alert_type TEXT NOT NULL,       -- price_above | price_below | rsi_above | rsi_below | etc.
  threshold NUMERIC NOT NULL,
  is_triggered BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  triggered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. API Design

### Base URL: `https://api.yourapp.com/v1`

---

### 4.1 Screener Endpoints

```
POST   /screener/run
GET    /screener/saved
POST   /screener/saved
PUT    /screener/saved/{id}
DELETE /screener/saved/{id}
GET    /screener/share/{token}
POST   /screener/saved/{id}/share
```

**POST /screener/run — Sample Request:**
```json
{
  "filters": [
    { "field": "pe_ratio", "operator": "lt", "value": 20 },
    { "field": "roe", "operator": "gt", "value": 15 },
    { "field": "market_cap", "operator": "gt", "value": 5000000000 },
    { "field": "rsi_14", "operator": "between", "value": [30, 70] }
  ],
  "logic": "AND",
  "exchange": ["NSE", "BSE"],
  "sort_by": "market_cap",
  "sort_order": "desc",
  "page": 1,
  "per_page": 50,
  "columns": ["symbol", "name", "market_cap", "pe_ratio", "roe", "rsi_14"]
}
```

**POST /screener/run — Sample Response:**
```json
{
  "total": 134,
  "page": 1,
  "per_page": 50,
  "results": [
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "name": "Reliance Industries Ltd",
      "price": 2874.50,
      "pct_change_1d": 1.23,
      "market_cap": 1940000000000,
      "pe_ratio": 17.4,
      "roe": 18.2,
      "rsi_14": 54.3,
      "composite_score": 72
    }
  ]
}
```

---

### 4.2 Stock Detail Endpoints

```
GET /stocks/search?q=reliance&exchange=NSE
GET /stocks/{symbol}/overview
GET /stocks/{symbol}/fundamentals
GET /stocks/{symbol}/technicals
GET /stocks/{symbol}/price-history?interval=1d&from=2024-01-01&to=2025-01-01
GET /stocks/{symbol}/peers
```

---

### 4.3 Portfolio Endpoints

```
GET    /portfolio
POST   /portfolio
GET    /portfolio/{id}
PUT    /portfolio/{id}
DELETE /portfolio/{id}
POST   /portfolio/{id}/holdings
PUT    /portfolio/{id}/holdings/{holding_id}
DELETE /portfolio/{id}/holdings/{holding_id}
GET    /portfolio/{id}/performance
GET    /portfolio/{id}/analysis
GET    /portfolio/share/{token}
POST   /portfolio/{id}/share
```

**GET /portfolio/{id}/performance — Sample Response:**
```json
{
  "portfolio_id": "uuid",
  "total_invested": 500000,
  "current_value": 672000,
  "total_gain": 172000,
  "total_gain_pct": 34.4,
  "today_gain": 3200,
  "today_gain_pct": 0.48,
  "xirr": 18.7,
  "benchmark_return_pct": 22.1,
  "alpha": 12.3,
  "holdings": [
    {
      "symbol": "RELIANCE",
      "quantity": 50,
      "avg_buy_price": 2400,
      "current_price": 2874.5,
      "invested": 120000,
      "current_value": 143725,
      "gain": 23725,
      "gain_pct": 19.77,
      "weight_pct": 21.4
    }
  ]
}
```

---

### 4.4 WebSocket — Live Prices

```
WS /ws/prices?symbols=RELIANCE,TCS,AAPL
```

**Message format:**
```json
{
  "type": "price_update",
  "data": {
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "price": 2876.30,
    "change": 1.80,
    "change_pct": 0.063,
    "volume": 3482910,
    "timestamp": "2025-01-15T10:32:14Z"
  }
}
```

---

## 5. Frontend Component Structure

```
src/
├── app/                              # Next.js App Router
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── screener/
│   │   ├── page.tsx                  # Main screener page
│   │   └── [id]/page.tsx             # Saved screener detail
│   ├── portfolio/
│   │   ├── page.tsx                  # Portfolio list
│   │   └── [id]/page.tsx             # Portfolio dashboard
│   ├── stocks/
│   │   └── [symbol]/page.tsx         # Stock detail page
│   ├── share/
│   │   ├── screener/[token]/page.tsx # Public screener view
│   │   └── portfolio/[token]/page.tsx# Public portfolio view
│   ├── watchlist/page.tsx
│   └── layout.tsx
│
├── components/
│   ├── screener/
│   │   ├── FilterPanel.tsx           # Sticky left filter panel
│   │   ├── FilterRow.tsx             # Single filter condition row
│   │   ├── FilterBuilder.tsx         # Add/remove/combine filters
│   │   ├── ScreenerTable.tsx         # TanStack Table with virtualization
│   │   ├── ColumnSelector.tsx        # Show/hide columns
│   │   ├── SaveScreenerModal.tsx
│   │   └── ShareModal.tsx
│   │
│   ├── portfolio/
│   │   ├── PortfolioSummaryCard.tsx  # P&L summary at top
│   │   ├── HoldingsTable.tsx         # Holdings list
│   │   ├── AddHoldingModal.tsx
│   │   ├── PerformanceChart.tsx      # Portfolio growth line chart
│   │   ├── AllocationPieChart.tsx    # Sector / cap breakdown
│   │   ├── GainLossBar.tsx           # Per-holding visual
│   │   └── BenchmarkComparison.tsx
│   │
│   ├── stocks/
│   │   ├── StockHeader.tsx           # Price + badge + quick stats
│   │   ├── PriceChart.tsx            # TradingView candlestick
│   │   ├── FundamentalsTable.tsx
│   │   ├── TechnicalsPanel.tsx
│   │   ├── PeersTable.tsx
│   │   └── CompositeScoreMeter.tsx
│   │
│   ├── common/
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   ├── StockSearch.tsx           # Command palette style
│   │   ├── MetricBadge.tsx
│   │   ├── ChangeIndicator.tsx       # Green/red % change pill
│   │   ├── LivePriceTicker.tsx
│   │   └── ThemeToggle.tsx
│   │
│   └── ui/                           # shadcn/ui base components
│
├── hooks/
│   ├── useScreener.ts                # Screener state + API calls
│   ├── useLivePrices.ts              # WebSocket price hook
│   ├── usePortfolio.ts               # Portfolio CRUD + perf
│   └── useStockSearch.ts
│
├── lib/
│   ├── api.ts                        # Typed API client (fetch wrapper)
│   ├── websocket.ts                  # WS connection manager
│   ├── formatters.ts                 # Currency, %, large numbers
│   ├── screenerConfig.ts             # All filter field definitions
│   └── constants.ts
│
└── store/
    ├── screenerStore.ts              # Zustand: filters, results
    ├── portfolioStore.ts
    └── uiStore.ts                    # Dark mode, sidebar state
```

---

## 6. Data Pipeline Strategy

### 6.1 Data Refresh Schedule

| Data Type | Frequency | Method |
|---|---|---|
| Live prices (market hours) | Every 15 sec | WebSocket / polling NSE/Yahoo |
| OHLCV daily candles | Daily, post-market close | Celery scheduled task |
| Fundamentals | Weekly (or earnings event) | Celery + yfinance |
| Technical indicators | Daily, computed after OHLCV refresh | Celery + pandas-ta |
| Composite score | Daily, after all above | Derived computation |

### 6.2 Caching Strategy

```
Request → Redis Cache (TTL check)
  ├── HIT  → Return cached JSON (< 5ms)
  └── MISS → DB Query → Compute → Cache → Return

TTL Rules:
  Live price:         15 seconds
  Technical snapshot: 1 hour (during market), 24 hours (off hours)
  Fundamentals:       24 hours
  Screener results:   30 seconds (dynamic filters)
  Stock overview:     1 hour
```

### 6.3 Rate Limiting & Fallback Chain

```
Primary: yfinance (free, 2000 req/hour)
  ↓ (if rate limited or error)
Secondary: Alpha Vantage (500 req/day free)
  ↓ (if rate limited)
Tertiary: Twelve Data (800 req/day free)
  ↓ (if all fail)
Fallback: Serve last known cached value + flag as stale
```

### 6.4 Celery Task Design

```python
# Scheduled Tasks
@celery.task
def refresh_eod_prices():
    # Triggered: daily 4:30 PM IST / 6:30 PM EST
    # Fetches OHLCV for all active stocks, inserts into price_history

@celery.task
def compute_technicals():
    # Triggered: after refresh_eod_prices completes
    # Uses pandas-ta to compute RSI, MACD, SMAs, etc.

@celery.task
def refresh_fundamentals():
    # Triggered: every Sunday 2 AM IST
    # Updates P/E, P/B, ROE, ROCE, etc. via yfinance

@celery.task
def compute_composite_scores():
    # Triggered: after fundamentals refresh
    # Weighted scoring: fundamentals 40%, technicals 30%, momentum 30%
```

---

## 7. Phase-by-Phase Build Plan

---

### PHASE 0 — Setup & Scaffolding (Week 1)

**Goal:** Get dev environment and repo structure working end-to-end.

1. Create GitHub monorepo: `stock-screener/`
   - `apps/frontend/` — Next.js
   - `apps/backend/` — FastAPI
   - `packages/shared-types/` — TypeScript interfaces shared between frontend/backend

2. **Backend setup**
   - Init FastAPI project with `uv` or `poetry`
   - Configure PostgreSQL via Supabase (create project, get connection string)
   - Install TimescaleDB extension on Supabase
   - Set up SQLAlchemy + Alembic, write initial migration for all tables
   - Configure Redis via Upstash (get REST URL)
   - Set up Celery with Redis broker

3. **Frontend setup**
   - Init Next.js 14 with TypeScript, Tailwind, ESLint
   - Install shadcn/ui, configure dark mode as default
   - Install TanStack Query, TanStack Table, Zustand
   - Set up API client in `lib/api.ts`

4. **Auth setup**
   - Configure Supabase Auth on backend
   - Wire Auth.js (next-auth) on frontend with Supabase provider
   - Create protected route middleware

5. **CI/CD**
   - GitHub Actions: lint + typecheck on PR
   - Deploy frontend to Vercel (connect GitHub repo)
   - Deploy backend to Railway (Dockerfile)

---

### PHASE 1 — Data Layer & Stock Universe (Week 2)

**Goal:** Populate DB with a working stock universe and price data.

1. **Seed stock master list**
   - Script to pull NSE stock list (NIFTY 500 initially)
   - Script to pull NASDAQ-100 + S&P 500 stocks via yfinance
   - Run `insert_stocks.py` → populate `stocks` table

2. **Historical price data**
   - Write Celery task `backfill_price_history(symbol, days=365)`
   - Run for all seeded stocks
   - Verify TimescaleDB hypertable is performing well

3. **Fundamentals seeder**
   - `backfill_fundamentals.py` using yfinance `Ticker.info`
   - Map yfinance fields to your schema columns

4. **Technical indicators computation**
   - Install `pandas-ta`
   - Write `compute_technicals(stock_id, date)` — outputs RSI, MACD, SMAs, etc.
   - Run for all stocks

5. **Composite Score algorithm**
   - Define scoring rubric:
     - Fundamental score: weighted P/E, ROE, D/E, EPS growth
     - Technical score: RSI positioning, SMA alignment (price > 50 DMA > 200 DMA = bullish)
     - Momentum score: 1M, 3M, 6M return percentile rank
     - Piotroski score contribution
   - Normalize to 0–100 scale
   - Write and run `compute_composite_scores()`

6. **Verify data quality**
   - Write a quick audit script checking for nulls, outliers, data gaps

---

### PHASE 2 — Screener Engine (Week 3)

**Goal:** Core screener API working with all filter types.

1. **Define screener filter schema**
   - Create `screenerConfig.ts` with all filter definitions:
     ```typescript
     { field: 'pe_ratio', label: 'P/E Ratio', category: 'Fundamental',
       type: 'number', operators: ['lt', 'gt', 'between', 'eq'] }
     ```
   - Cover all ~40+ parameters from the requirements

2. **Backend: Screener engine**
   - `POST /screener/run` takes filter array, dynamically builds SQL
   - Use SQLAlchemy's query builder (not raw SQL) for safety
   - Support AND/OR logic at group level
   - Pagination + sorting on any column
   - Results cached in Redis for 30 seconds (same filter hash = same cache key)

3. **Backend: Save/load screeners**
   - CRUD endpoints for `screeners` table
   - Filters stored as JSONB → can replay any saved screener

4. **Frontend: Filter Panel**
   - Sticky left panel (like Tickertape)
   - Category grouping (Fundamental, Technical, Price, Quality)
   - Add filter → choose field → choose operator → enter value
   - Multiple filters with AND/OR toggle
   - "Run Screener" triggers API call

5. **Frontend: Screener Table**
   - TanStack Table with column sorting
   - Virtualized rows (react-virtual) for 500+ results without lag
   - Sticky first column (symbol)
   - Column show/hide selector
   - Click row → navigate to stock detail page

6. **Save & Share**
   - Save screener modal (name + optional description)
   - Generate `share_token` (nanoid) on save if `is_public = true`
   - Public view at `/share/screener/{token}` — read-only, no auth required

---

### PHASE 3 — Stock Detail Page (Week 4)

**Goal:** Rich individual stock page.

1. **Stock overview API** — one endpoint returns all key stats
2. **Price chart** — integrate `lightweight-charts` (TradingView open source)
   - Toggle between 1D, 1W, 1M, 3M, 1Y, 5Y
   - Overlay SMAs (20, 50, 200)
3. **Fundamentals panel** — table layout comparing current vs industry avg
4. **Technicals panel** — RSI gauge, MACD chart, MA alignment indicator
5. **Peers comparison** — show P/E, ROE, Market Cap vs sector peers
6. **Composite Score** — circular meter (0–100) with breakdown tooltip
7. **Add to watchlist** button, **Add to portfolio** button

---

### PHASE 4 — Portfolio Dashboard (Week 5)

**Goal:** Full portfolio tracking with performance analytics.

1. **Add holdings manually**
   - Modal: search stock, quantity, avg buy price, date
   - `POST /portfolio/{id}/holdings`

2. **Live portfolio valuation**
   - Backend computes current value using latest price from DB
   - Calculates gain/loss per holding and total

3. **Performance chart**
   - Reconstruct historical portfolio value day-by-day using `price_history`
   - Compare vs NIFTY 50 or S&P 500 benchmark
   - Line chart with Recharts

4. **Allocation breakdowns**
   - Sector allocation pie chart
   - Market cap category breakdown (large/mid/small)
   - Geographic split (India vs US)

5. **Key metrics**
   - XIRR (use numpy-financial on backend)
   - Sharpe ratio
   - Max drawdown

6. **Share portfolio** — same token-based mechanism as screeners

---

### PHASE 5 — Live Prices & WebSocket (Week 6)

**Goal:** Near-real-time price updates during market hours.

1. **Backend WebSocket endpoint**
   - `/ws/prices?symbols=RELIANCE,TCS`
   - Accepts symbol list, streams price updates every 15 seconds

2. **Price fetcher service**
   - During NSE market hours (9:15 AM – 3:30 PM IST): poll NSE unofficial API
   - During NYSE hours (9:30 AM – 4:00 PM EST): poll Yahoo Finance / Twelve Data
   - Outside hours: serve last close price (no WebSocket needed)

3. **Frontend WebSocket hook**
   - `useLivePrices(symbols)` — connects WS, returns `{ [symbol]: PriceData }`
   - Auto-reconnect on disconnect
   - Graceful fallback: if WS fails, show stale price + "Delayed" badge

4. **Live ticker component**
   - Navbar ticker strip with animated price changes (green flash up, red flash down)
   - Screener table cells update live without page refresh
   - Portfolio dashboard P&L updates in real time

---

### PHASE 6 — Watchlist & Alerts (Week 7)

**Goal:** Engagement features that bring users back.

1. **Watchlist**
   - Create / rename / delete watchlists
   - Add stocks from screener, stock page, or search
   - Watchlist view: mini table with live prices + 1D change

2. **Alerts**
   - Price alerts: above/below threshold
   - Indicator alerts: RSI overbought/oversold, MACD crossover, Price vs SMA
   - Storage in `alerts` table
   - Celery task checks alerts every 15 minutes against latest data
   - Trigger: email via Resend.com (free tier) or in-app notification

---

### PHASE 7 — Polish, Performance & Testing (Week 8)

**Goal:** Production hardening before launch.

1. **Frontend performance**
   - Lighthouse audit — target 90+ score
   - Lazy load heavy components (charts, large tables)
   - Prefetch stock data on hover (Next.js link prefetch)
   - API response compression (gzip)

2. **Backend performance**
   - Add DB indexes: `stocks(symbol, exchange)`, `fundamentals(stock_id, date)`, etc.
   - Analyze slow queries with `EXPLAIN ANALYZE`
   - Ensure screener query < 200ms for 5000+ stock universe

3. **Error handling**
   - Backend: structured error responses with error codes
   - Frontend: React Error Boundaries, toast notifications
   - Data staleness indicators when live feed is unavailable

4. **Testing**
   - Backend: pytest for screener engine, portfolio math, API contracts
   - Frontend: Vitest + Testing Library for critical components
   - E2E: Playwright for screener filter → result → stock detail flow

5. **Security**
   - Rate limiting on API (slowapi)
   - Input validation (Pydantic strict mode)
   - CORS configured correctly
   - Auth middleware on all protected routes
   - Share tokens: validate they belong to correct resource

---

## 8. Deployment Plan

### Development
```
Local: docker-compose up
  - PostgreSQL + TimescaleDB
  - Redis
  - FastAPI (hot reload)
  - Next.js (hot reload)
  - Celery worker + Celery beat (scheduler)
```

### Staging → Production

| Service | Platform | Config |
|---|---|---|
| Frontend | Vercel | Auto-deploy from `main` branch |
| Backend API | Railway | Dockerfile, auto-deploy |
| Celery Worker | Railway | Separate service, same Docker image |
| Celery Beat | Railway | Separate service (scheduler) |
| PostgreSQL | Supabase | Managed, daily backups |
| Redis | Upstash | Serverless, pay-per-request |

### Environment Variables

```bash
# Backend
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=rediss://...
ALPHA_VANTAGE_KEY=...
TWELVE_DATA_KEY=...
SUPABASE_JWT_SECRET=...
CELERY_BROKER_URL=rediss://...

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourapp.com
NEXT_PUBLIC_WS_URL=wss://api.yourapp.com
NEXTAUTH_SECRET=...
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
```

### Monitoring (free tier)
- **Sentry** — error tracking (frontend + backend)
- **Railway metrics** — CPU/memory dashboards
- **Upstash console** — Redis hit rate
- **Supabase dashboard** — DB query performance

---

## 9. Codebase Folder Structure

```
stock-screener/
├── apps/
│   ├── frontend/                   # Next.js 14
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── lib/
│   │   │   └── store/
│   │   ├── public/
│   │   ├── next.config.ts
│   │   ├── tailwind.config.ts
│   │   └── package.json
│   │
│   └── backend/                    # FastAPI
│       ├── app/
│       │   ├── api/               # Route handlers
│       │   │   ├── screener.py
│       │   │   ├── portfolio.py
│       │   │   ├── stocks.py
│       │   │   ├── watchlist.py
│       │   │   └── alerts.py
│       │   ├── core/
│       │   │   ├── config.py      # Settings (pydantic-settings)
│       │   │   ├── database.py    # SQLAlchemy async engine
│       │   │   ├── redis.py       # Redis client
│       │   │   └── security.py    # JWT validation
│       │   ├── models/            # SQLAlchemy ORM models
│       │   ├── schemas/           # Pydantic request/response models
│       │   ├── services/
│       │   │   ├── screener.py    # Filter → SQL engine
│       │   │   ├── portfolio.py   # P&L, XIRR, allocation
│       │   │   ├── price_feed.py  # Live price fetching
│       │   │   └── scoring.py     # Composite score computation
│       │   ├── tasks/             # Celery tasks
│       │   │   ├── prices.py
│       │   │   ├── fundamentals.py
│       │   │   ├── technicals.py
│       │   │   └── alerts.py
│       │   ├── ws/                # WebSocket handlers
│       │   └── main.py
│       ├── alembic/               # Migrations
│       ├── scripts/               # Seed scripts
│       ├── tests/
│       ├── Dockerfile
│       └── pyproject.toml
│
├── docker-compose.yml             # Local dev
├── .github/
│   └── workflows/
│       └── ci.yml
└── README.md
```

---

## Summary: Milestone Timeline

| Week | Milestone |
|---|---|
| 1 | Repo setup, DB schema live, CI/CD pipelines, auth working |
| 2 | Stock universe seeded, price history backfilled, technicals computed |
| 3 | Screener API + frontend filter panel + results table |
| 4 | Stock detail page with charts, fundamentals, and composite score |
| 5 | Portfolio dashboard with performance analytics and share links |
| 6 | Live WebSocket prices, real-time portfolio P&L |
| 7 | Watchlist + price/indicator alerts |
| 8 | Performance tuning, testing, security hardening, launch |

---

*Built to scale: mutual funds, AI insights, and social features can be added as separate modules without changing the core architecture.*
