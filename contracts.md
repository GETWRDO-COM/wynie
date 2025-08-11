# API Contracts and Integration Plan

This document defines the backend API contracts, mocked data to be replaced, and the plan to integrate the frontend and backend. All backend routes are prefixed with `/api` per ingress rules.

## A) API Contracts

1) Health
- GET /api/ — { message: string }

2) Market Data
- GET /api/marketdata/symbols/search?q=TSLA&limit=25
  - Response: { items: [{ symbol, name, exchange, locale, currency, sector?, industry?, logoUrl? }] }
- GET /api/marketdata/bars?symbol=AAPL&interval=1D&from=2024-01-01&to=2025-08-11
  - interval: 1,5,15,60,1D,1W
  - Response: { symbol, bars: [{ t: epoch_sec, o, h, l, c, v }] }
- GET /api/marketdata/quotes?symbols=AAPL,MSFT
  - Response: { quotes: [{ symbol, last, changePct, volume, prevClose, prePct?, postPct? }] }
- GET /api/marketdata/logo?symbol=AAPL
  - Response: { symbol, logoUrl }

3) Watchlists
- GET /api/watchlists
  - Response: [{ id, name, symbols: string[], createdAt, updatedAt }]
- POST /api/watchlists { name, symbols? }
  - Response: { id, name, symbols: [] }
- PUT /api/watchlists/{id} { name?, symbols? }
- DELETE /api/watchlists/{id}

4) Columns
- GET /api/columns/schema
  - Response: { categories: [{ name, columns: [{ id, label, category, type, formatter?, source: 'provider'|'computed' }] }] }
- GET /api/columns/presets
  - Response: { [name: string]: string[] }
- POST /api/columns/presets { name, columns: string[] }
- DELETE /api/columns/presets/{name}

5) Screeners
- POST /api/screeners/run
  - Body: { filters: [{ field, op, value }], sort?: { key, dir }, page?: { limit, cursor? } }
  - Response: { rows: any[], nextCursor?: string }

6) Ratings (RS/AS)
- POST /api/ratings/compute { symbols: string[], rsWindowDays: number, asShortDays: number, asLongDays: number }
  - Response: { RS: { [symbol]: number }, AS: { [symbol]: number } }

7) Drawings/Layout (TradingView)
- GET /api/chart/{symbol}/drawings — { drawings: any[] }
- POST /api/chart/{symbol}/drawings { drawings: any[] }
- GET /api/chart/layout — { layout: any }
- POST /api/chart/layout { layout: any }

8) TV Datafeed (frontend adapter calls these)
- GET /api/tv/search?q=&limit=
- GET /api/tv/resolve?symbol=
- GET /api/tv/bars?symbol=&resolution=1,5,15,60,D,W&from=&to=
- WS (phase 2): /api/ws/quotes?symbols=

## B) What is mocked today
- Universe (50 US symbols), candles, RS/AS, all columns, screener logic, drawings persistence — stored in localStorage via `src/mock/mock.js`.
- Frontend renders from mock registry; Column Settings and presets are local only.

## C) Backend v1 Implementation Scope
- Polygon adapter (REST) using API Key in backend/.env.
- Endpoints implemented now: marketdata symbols search, bars, quotes (snapshot-first, fallbacks), logo, watchlists CRUD, columns schema, columns presets (Mongo), ratings compute (server-side), screener (basic ops).
- No WebSocket in v1 (phase 2).

## D) Frontend ↔ Backend Integration Plan
1. Add a data service on frontend that reads REACT_APP_BACKEND_URL and calls:
   - /api/marketdata/bars for chart data
   - /api/marketdata/symbols/search for typeahead
   - /api/marketdata/quotes to populate table fields (last, change, volume, pre/post)
   - /api/columns/schema to build column manager dynamically
   - /api/columns/presets for save/load
   - /api/watchlists for persistence
   - /api/ratings/compute when RS/AS params change
2. Replace mock.js usage progressively and keep fallback mode if backend unavailable.
3. Add a TradingView datafeed adapter that maps TV methods to our endpoints; swap SVG chart to TV once package is provided.

## E) Notes
- All backend URLs keep /api prefix.
- Mongo uses MONGO_URL only.
- Keys are stored in backend/.env (POLYGON_API_KEY).