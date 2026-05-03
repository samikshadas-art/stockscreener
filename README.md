# StockScreener — Production-Ready Equity Analysis Platform

Full-stack stock screener + portfolio dashboard for **Indian (NSE/BSE)** and **US (NYSE/NASDAQ)** markets.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, TanStack Query/Table, Zustand, Recharts |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Database | PostgreSQL 16 + TimescaleDB |
| Cache | Redis 7 |
| Task Queue | Celery + Celery Beat |
| Data Sources | yfinance, Alpha Vantage, Twelve Data |
| Deployment | Vercel (frontend) + Railway (backend) + Supabase (DB) |

## Quick Start (Local Dev)

### Prerequisites
- Docker + Docker Compose
- Python 3.11+
- Node.js 20+

### 1. Clone & configure

```bash
git clone https://github.com/yourname/stock-screener.git
cd stock-screener

# Backend env
cp apps/backend/.env.example apps/backend/.env

# Frontend env
cp apps/frontend/.env.local.example apps/frontend/.env.local
```

### 2. Start infrastructure

```bash
docker compose up db redis -d
```

### 3. Run database migrations

```bash
cd apps/backend
pip install -e ".[dev]"
alembic upgrade head
```

### 4. Seed initial stock data

```bash
# Seed 20 NSE stocks (takes ~3 min due to yfinance rate limits)
python scripts/seed_stocks.py --exchange NSE --limit 20

# Also seed US stocks
python scripts/seed_stocks.py --exchange NYSE --limit 10
```

### 5. Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

### 6. Start the frontend

```bash
cd apps/frontend
npm install
npm run dev
```

Open http://localhost:3000 — you're live!

---

## Or use Docker Compose (all services)

```bash
docker compose up --build
```

This starts: PostgreSQL, Redis, FastAPI, Celery worker, Celery Beat scheduler, and Next.js.

---

## API Docs

FastAPI auto-generates interactive docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Key Endpoints

```
POST /v1/screener/run          — Run screener with dynamic filters
GET  /v1/stocks/search?q=      — Search stocks by symbol or name
GET  /v1/stocks/{symbol}/overview
GET  /v1/stocks/{symbol}/price-history
GET  /v1/portfolio             — List portfolios
POST /v1/portfolio             — Create portfolio
GET  /v1/portfolio/{id}/performance
POST /v1/portfolio/{id}/holdings

WS   /ws/prices?symbols=       — Live price WebSocket
```

---

## Screener Filter Parameters

**Fundamental:** market_cap, pe_ratio, forward_pe, pb_ratio, ev_ebitda, roe, roce, roa, net_margin, operating_margin, debt_to_equity, current_ratio, eps, eps_growth_yoy, revenue_growth_yoy, dividend_yield

**Technical:** rsi_14, macd, macd_signal, sma_20, sma_50, sma_100, sma_200, ema_20, beta, relative_volume, volatility_30d, atr_14

**Price:** pct_change_1d, pct_change_1w, pct_change_1m, pct_change_3m, pct_change_6m, pct_change_1y

**Quality:** piotroski_score, altman_z_score, composite_score

---

## Deployment

### Frontend → Vercel
```bash
cd apps/frontend
vercel --prod
```

### Backend → Railway
1. Push to GitHub
2. Connect Railway to your repo
3. Set env vars from `.env.example`
4. Railway auto-deploys on push

### Database → Supabase
1. Create a Supabase project
2. Enable TimescaleDB extension in SQL editor
3. Update `DATABASE_URL` to your Supabase connection string
4. Run `alembic upgrade head`

---

## Project Structure

```
stock-screener/
├── apps/
│   ├── backend/          # FastAPI
│   │   ├── app/
│   │   │   ├── api/      # Route handlers
│   │   │   ├── core/     # Config, DB, Redis, Security
│   │   │   ├── models/   # SQLAlchemy ORM models
│   │   │   ├── schemas/  # Pydantic request/response
│   │   │   ├── services/ # Business logic
│   │   │   ├── tasks/    # Celery tasks
│   │   │   └── ws/       # WebSocket handlers
│   │   ├── alembic/      # Migrations
│   │   └── scripts/      # Seed scripts
│   └── frontend/         # Next.js 14
│       └── src/
│           ├── app/      # Pages (App Router)
│           ├── components/
│           ├── hooks/
│           ├── lib/      # API client, formatters, screenerConfig
│           └── store/    # Zustand state
├── docker-compose.yml
└── README.md
```

---

## Roadmap

- [x] Phase 0 — Scaffolding & setup
- [x] Phase 1 — Data layer & stock universe
- [x] Phase 2 — Screener engine (40+ filters)
- [x] Phase 3 — Stock detail page
- [x] Phase 4 — Portfolio dashboard
- [ ] Phase 5 — Live WebSocket prices
- [ ] Phase 6 — Watchlist & alerts
- [ ] Phase 7 — Polish, testing, hardening
- [ ] Phase 8 — AI insights & mutual funds

---

Built with ❤️ as a lean fintech tool that scales.
