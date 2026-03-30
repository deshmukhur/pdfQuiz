# Stock Market Analysis Platform

Real-time stock market scanner and analysis platform for **Indian markets (NSE/BSE)** powered by Fyers API, featuring 40+ technical indicators, 20+ candlestick pattern detection, composite scoring engine, and a professional Angular dashboard.

---

## Features

- **Real-time Tick Data** — Connects to Fyers WebSocket for live market data
- **1-Minute OHLCV Bars** — Constructs minute bars from tick-level data
- **40+ Technical Indicators** — RSI, MACD, EMA, SMA, Bollinger Bands, Supertrend, ADX, ATR, VWAP, OBV, Stochastic, CCI, Williams %R, MFI, Parabolic SAR, Pivot Points, Fibonacci Retracements, and more
- **20+ Candlestick Patterns** — Doji, Hammer, Engulfing, Morning/Evening Star, Three White Soldiers, Head & Shoulders, Double Top/Bottom, Triangles, Wedges, and more
- **Composite Scoring Engine** — Generates scores from -100 to +100 combining trend (30%), momentum (25%), volume (20%), patterns (15%), and support/resistance (10%)
- **Signal Classification** — STRONG_BUY, BUY, WEAK_BUY, NEUTRAL, WEAK_SELL, SELL, STRONG_SELL
- **Automated Scanner** — APScheduler runs every 60 seconds during market hours (09:15–15:30 IST)
- **WebSocket Broadcasting** — Real-time ranked results pushed to Angular dashboard
- **Backtesting Module** — Win/loss tracking, profit factor, expectancy metrics
- **News Sentiment** — RSS feeds (ET, Moneycontrol, LiveMint) with VADER sentiment analysis
- **Fundamental Data** — Scrapes Screener.in for PE, PB, EPS, ROE, D/E, market cap, holdings
- **Professional Dashboard** — Dark-themed Angular 17+ UI with TradingView-style charting

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), PostgreSQL |
| Frontend | Angular 17+, Angular Material, Lightweight Charts |
| Data | Fyers API v3, pandas, pandas-ta |
| Scheduling | APScheduler (AsyncIO) |
| Sentiment | VADER (local, free) |
| WebSocket | FastAPI native WebSocket |
| Infrastructure | Docker, Docker Compose, Nginx |

---

## Project Structure

```
stock-platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Environment configuration
│   │   ├── database.py             # Async SQLAlchemy engine & session
│   │   ├── fyers_client.py         # Fyers API wrapper & WebSocket
│   │   ├── minute_bar_builder.py   # Tick → 1-min OHLCV bar construction
│   │   ├── indicator_engine.py     # 40+ technical indicators
│   │   ├── pattern_engine.py       # 20+ candlestick patterns
│   │   ├── scoring_engine.py       # Composite scoring (-100 to +100)
│   │   ├── scanner.py              # APScheduler scan job
│   │   ├── backtest_engine.py      # Backtesting module
│   │   ├── news_fetcher.py         # RSS + VADER sentiment
│   │   ├── fundamental_fetcher.py  # Screener.in scraper
│   │   ├── websocket_manager.py    # WebSocket broadcast manager
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── base.py
│   │   │   ├── instruments.py
│   │   │   ├── ohlcv.py
│   │   │   ├── indicator_snapshots.py
│   │   │   ├── signals.py
│   │   │   ├── backtest.py
│   │   │   ├── news.py
│   │   │   └── fundamentals.py
│   │   └── routers/                # FastAPI API routers
│   │       ├── instruments.py
│   │       ├── candles.py
│   │       ├── dashboard.py
│   │       ├── signals.py
│   │       ├── backtest.py
│   │       ├── news.py
│   │       ├── fundamental.py
│   │       ├── auth.py
│   │       ├── websocket.py
│   │       └── optionchain.py
│   ├── migrations/                 # Alembic database migrations
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/         # Shared UI components
│   │   │   │   ├── market-status-bar/
│   │   │   │   ├── instrument-table/
│   │   │   │   ├── trading-chart/
│   │   │   │   ├── indicator-panel/
│   │   │   │   ├── signal-badge/
│   │   │   │   ├── news-ticker/
│   │   │   │   └── pattern-annotation/
│   │   │   ├── pages/              # Route pages
│   │   │   │   ├── dashboard/
│   │   │   │   ├── chart/
│   │   │   │   ├── backtest/
│   │   │   │   ├── news/
│   │   │   │   ├── fundamentals/
│   │   │   │   ├── settings/
│   │   │   │   └── auth/
│   │   │   ├── services/           # Angular services
│   │   │   └── models/             # TypeScript interfaces
│   │   ├── environments/
│   │   └── styles.scss
│   ├── package.json
│   ├── angular.json
│   ├── tsconfig.json
│   └── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── start.sh                        # Linux/Mac startup script
├── start.bat                       # Windows startup script
├── .gitignore
└── README.md
```

---

## Prerequisites

- **Python** 3.11 or higher
- **Node.js** 20+ and npm
- **PostgreSQL** 16+ (or use Docker)
- **Fyers Trading Account** with API access enabled

---

## Quick Start (Local Development)

### 1. Clone / Extract

```bash
unzip stock-platform.zip
cd stock-platform
```

### 2. Set Up PostgreSQL

**Option A: Docker (recommended)**
```bash
docker run -d --name trading-db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=trading_platform \
  -p 5432:5432 \
  postgres:16-alpine
```

**Option B: Existing PostgreSQL**
```bash
psql -U postgres -c "CREATE DATABASE trading_platform;"
psql -U postgres -c "CREATE USER \"user\" WITH PASSWORD 'password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE trading_platform TO \"user\";"
```

### 3. Configure Environment

```bash
cd backend
cp .env.example .env
# Edit .env with your Fyers API credentials and database URL
```

Your `.env` should contain:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/trading_platform
FYERS_CLIENT_ID=your_client_id
FYERS_SECRET=your_secret_key
FYERS_REDIRECT_URI=http://127.0.0.1:8000/api/auth/fyers/callback
```

### 4. Start Everything (One Command)

**Linux / macOS:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```cmd
start.bat
```

### 5. Or Start Manually

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
mkdir -p logs
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend (separate terminal):**
```bash
cd frontend
npm install
npx ng serve --host 0.0.0.0 --port 4200
```

### 6. Access

| URL | Service |
|-----|---------|
| http://localhost:4200 | Angular Dashboard |
| http://localhost:8000 | FastAPI Backend |
| http://localhost:8000/docs | Swagger API Documentation |

---

## Quick Start (Docker Compose)

```bash
cd stock-platform

# Copy and edit environment file
cp backend/.env.example backend/.env
# Edit backend/.env — update DATABASE_URL host from localhost to db:
# DATABASE_URL=postgresql+asyncpg://user:password@db:5432/trading_platform

docker-compose up --build
```

Access the dashboard at **http://localhost:4200**.

---

## Fyers Authentication

1. Navigate to **http://localhost:4200/auth**
2. Click **"Login with Fyers"** — this opens the Fyers OAuth2 login page
3. Log in with your Fyers credentials
4. After successful login, you'll be redirected back and the access token will be stored
5. The scanner will automatically start receiving tick data

**Alternative:** You can manually paste an access token on the Auth page.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/instruments` | List all active instruments |
| GET | `/api/candles` | Fetch OHLCV candles (symbol, timeframe, limit) |
| GET | `/api/dashboard/latest` | Get latest ranked scan results |
| GET | `/api/signals` | List trading signals with filters |
| POST | `/api/signals/{id}/close` | Manually close a signal |
| GET | `/api/backtest/report` | Get backtest performance report |
| POST | `/api/backtest/run` | Run backtest on open signals |
| GET | `/api/news` | List news articles with sentiment |
| GET | `/api/fundamental` | Get fundamental data for equities |
| GET | `/api/auth/fyers/url` | Get Fyers OAuth2 login URL |
| GET | `/api/auth/fyers/callback` | OAuth2 callback handler |
| GET | `/api/auth/fyers/status` | Check authentication status |
| GET | `/api/optionchain` | Fetch option chain with OI and Greeks |
| WS | `/ws` | Dashboard scan results (WebSocket) |
| WS | `/ws/chart` | Real-time chart tick data (WebSocket) |

---

## Dashboard Pages

### Dashboard (`/dashboard`)
- Real-time ranked instrument table sorted by composite score
- Filter by signal type (All, Buys, Sells, Strong Only)
- Stats cards showing counts by signal category
- News ticker with sentiment indicators
- Click any symbol to open the chart page

### Chart (`/chart/:symbol`)
- TradingView-style candlestick chart using Lightweight Charts
- Multiple timeframes: 1m, 5m, 15m, 1H, 1D
- Real-time tick updates via WebSocket
- Volume histogram overlay
- Indicator panel with score breakdown, key indicators, entry/targets
- Detected candlestick patterns

### Backtest (`/backtest`)
- Run backtests on historical signals
- Win rate, profit factor, expectancy metrics
- Detailed results table with P&L per trade
- Filter by date range and signal type

### News (`/news`)
- Aggregated news from ET, Moneycontrol, LiveMint RSS feeds
- VADER sentiment scoring with visual indicators
- Filter by symbol
- Related symbols extraction

### Fundamentals (`/fundamentals`)
- PE ratio, PB ratio, EPS, ROE, Debt/Equity
- Market cap, promoter holdings
- Sortable table with search
- Data updated weekly from Screener.in

### Settings (`/settings`)
- Connection status (Fyers, WebSocket)
- Scanner configuration (interval, min score, min volume ratio)
- Notification preferences
- Display preferences

### Auth (`/auth`)
- Fyers OAuth2 login flow
- Manual token input option
- Connection status indicator

---

## Scoring Engine

The composite score ranges from **-100 to +100** and combines:

| Category | Weight | Signals |
|----------|--------|---------|
| Trend | 30% | EMA alignment, Supertrend, ADX, Parabolic SAR |
| Momentum | 25% | RSI, MACD, Stochastic, CCI, Williams %R |
| Volume | 20% | OBV trend, CMF, MFI, Volume ratio |
| Patterns | 15% | Bullish/bearish candlestick patterns with confidence |
| Support/Resistance | 10% | Pivot points, Fibonacci levels, Bollinger Bands |

### Signal Classification

| Score Range | Signal |
|-------------|--------|
| 70 to 100 | STRONG_BUY |
| 40 to 69 | BUY |
| 10 to 39 | WEAK_BUY |
| -10 to 10 | NEUTRAL |
| -40 to -10 | WEAK_SELL |
| -70 to -40 | SELL |
| -100 to -70 | STRONG_SELL |

---

## Market Hours

The scanner operates during Indian market hours:
- **Trading:** Monday–Friday, 09:15–15:30 IST
- **NSE Holidays:** Automatically excluded (2025–2026 calendar built-in)
- **Scan Interval:** Every 60 seconds (configurable)

---

## Configuration

All configuration is via environment variables in `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `FYERS_CLIENT_ID` | — | Your Fyers API client ID |
| `FYERS_SECRET` | — | Your Fyers API secret key |
| `FYERS_REDIRECT_URI` | `http://127.0.0.1:8000/api/auth/fyers/callback` | OAuth redirect URI |
| `NEWSAPI_KEY` | — | Optional NewsAPI.org key |
| `SECRET_KEY` | — | Application secret key |
| `ENVIRONMENT` | `development` | Environment mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `SCAN_INTERVAL_SECONDS` | `60` | Scanner interval in seconds |

---

## Troubleshooting

### Database connection refused
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432
# Or start with Docker
docker start trading-db
```

### Fyers authentication fails
- Ensure `FYERS_CLIENT_ID` and `FYERS_SECRET` are correct in `.env`
- Verify the redirect URI matches exactly in your Fyers app settings
- Try using the manual token input on the Auth page

### Frontend build errors
```bash
cd frontend
rm -rf node_modules
npm install
```

### Scanner not producing results
- Check you're within market hours (09:15–15:30 IST, Mon–Fri)
- Verify Fyers authentication is active (check Auth page)
- Check backend logs: `tail -f backend/logs/app.log`

---

## License

This project is for personal/educational use. The Fyers API is subject to Fyers' terms of service.

---

## Disclaimer

This software is for educational and informational purposes only. It does not constitute financial advice. Trading in the stock market involves risk. The authors are not responsible for any financial losses incurred through the use of this software.
