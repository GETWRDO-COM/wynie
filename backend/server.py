from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
from datetime import datetime
import asyncio

from polygon_client import PolygonClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

POLYGON_KEY = os.environ.get('POLYGON_API_KEY', '')
poly_client = PolygonClient(POLYGON_KEY) if POLYGON_KEY else None

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ------------------- MODELS -------------------
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class Watchlist(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    symbols: List[str] = []
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class WatchlistCreate(BaseModel):
    name: str
    symbols: Optional[List[str]] = []

class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    symbols: Optional[List[str]] = None

# Column schema (starter)
COLUMN_SCHEMA: List[Dict] = [
    {"id": "symbol", "label": "Symbol", "category": "General", "type": "string", "source": "provider"},
    {"id": "description", "label": "Description", "category": "General", "type": "string", "source": "provider"},
    {"id": "sector", "label": "Sector", "category": "Sector & Industry", "type": "string", "source": "provider"},
    {"id": "industry", "label": "Industry", "category": "Sector & Industry", "type": "string", "source": "provider"},
    {"id": "last", "label": "Last", "category": "Price & Volume", "type": "number", "source": "provider"},
    {"id": "changePct", "label": "% Chg", "category": "Price & Volume", "type": "number", "source": "computed"},
    {"id": "volume", "label": "Vol", "category": "Price & Volume", "type": "number", "source": "provider"},
    {"id": "avgVol20d", "label": "AvgVol20d", "category": "Price & Volume", "type": "number", "source": "computed"},
    {"id": "runRate20d", "label": "RunRate20d", "category": "Price & Volume", "type": "number", "source": "computed"},
    {"id": "sma20", "label": "SMA20", "category": "Technicals", "type": "number", "source": "computed"},
    {"id": "sma50", "label": "SMA50", "category": "Technicals", "type": "number", "source": "computed"},
    {"id": "sma200", "label": "SMA200", "category": "Technicals", "type": "number", "source": "computed"},
    {"id": "rsi14", "label": "RSI(14)", "category": "Technicals", "type": "number", "source": "computed"},
    {"id": "RS", "label": "RS", "category": "Proprietary Ratings", "type": "number", "source": "computed"},
    {"id": "AS", "label": "AS", "category": "Proprietary Ratings", "type": "number", "source": "computed"},
]

# ------------------- ROUTES -------------------
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

# Watchlists
@api_router.get("/watchlists")
async def list_watchlists():
    docs = await db.watchlists.find().to_list(200)
    result = []
    for d in docs:
        clean = {k: v for k, v in d.items() if k != "_id"}
        clean.setdefault("id", str(d.get("_id")))
        result.append(clean)
    return result

@api_router.post("/watchlists")
async def create_watchlist(body: WatchlistCreate):
    wl = Watchlist(name=body.name, symbols=body.symbols or [])
    await db.watchlists.insert_one(wl.dict())
    return wl

@api_router.put("/watchlists/{id}")
async def update_watchlist(id: str, body: WatchlistUpdate):
    patch = {k: v for k, v in body.dict().items() if v is not None}
    patch["updatedAt"] = datetime.utcnow()
    await db.watchlists.update_one({"id": id}, {"$set": patch}, upsert=False)
    doc = await db.watchlists.find_one({"id": id})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return {k: v for k, v in doc.items() if k != "_id"}

@api_router.delete("/watchlists/{id}")
async def delete_watchlist(id: str):
    await db.watchlists.delete_one({"id": id})
    return {"ok": True}

# Columns schema & presets
@api_router.get("/columns/schema")
async def get_columns_schema():
    cats: Dict[str, List[Dict]] = {}
    for c in COLUMN_SCHEMA:
        cats.setdefault(c["category"], []).append(c)
    return {"categories": [{"name": k, "columns": v} for k, v in cats.items()]}

@api_router.get("/columns/presets")
async def get_column_presets():
    docs = await db.column_presets.find().to_list(200)
    return {d["name"]: d["columns"] for d in docs}

class PresetBody(BaseModel):
    name: str
    columns: List[str]

@api_router.post("/columns/presets")
async def save_column_preset(body: PresetBody):
    await db.column_presets.update_one({"name": body.name}, {"$set": {"name": body.name, "columns": body.columns, "updatedAt": datetime.utcnow()}}, upsert=True)
    return {"ok": True}

@api_router.delete("/columns/presets/{name}")
async def delete_preset(name: str):
    await db.column_presets.delete_one({"name": name})
    return {"ok": True}

# Market data
@api_router.get("/marketdata/symbols/search")
async def symbols_search(q: str, limit: int = 25):
    if not poly_client:
        return {"items": []}
    items = poly_client.search_symbols(q, limit)
    return {"items": items}

@api_router.get("/marketdata/logo")
async def logo(symbol: str):
    if not poly_client:
        return {"symbol": symbol, "logoUrl": None}
    return {"symbol": symbol, "logoUrl": poly_client.get_logo(symbol)}

@api_router.get("/marketdata/bars")
async def get_bars(symbol: str, interval: str = "1D", fr: Optional[str] = None, to: Optional[str] = None):
    if not poly_client:
        return {"symbol": symbol, "bars": []}
    # defaults
    from datetime import date
    to = to or datetime.utcnow().date().isoformat()
    fr = fr or (datetime.utcnow().date().replace(year=datetime.utcnow().year - 1).isoformat())
    if interval in ["1","5","15","60"]:
        mult = int(interval)
        span = "minute"
    elif interval in ["1D","D"]:
        mult = 1
        span = "day"
    elif interval in ["1W","W"]:
        mult = 1
        span = "week"
    else:
        mult = 1; span = "day"
    try:
        bars = poly_client.get_bars(symbol, mult, span, fr, to)
        return {"symbol": symbol, "bars": bars}
    except Exception as e:
        # graceful degrade on 429: return empty array instead of 500
        logging.warning("bars fetch failed: %s", e)
        return {"symbol": symbol, "bars": []}

@api_router.get("/marketdata/quotes")
async def get_quotes(symbols: str):
    if not poly_client:
        return {"quotes": []}
    syms = [s.strip().upper() for s in symbols.split(',') if s.strip()]
    data = poly_client.get_quotes_snapshot(syms)
    return {"quotes": data}

# Ratings compute (server-side)
class RatingsBody(BaseModel):
    symbols: List[str]
    rsWindowDays: int = 63
    asShortDays: int = 21
    asLongDays: int = 63

@api_router.post("/ratings/compute")
async def ratings_compute(body: RatingsBody):
    if not poly_client:
        return {"RS": {}, "AS": {}}
    RS: Dict[str, float] = {}
    AS: Dict[str, float] = {}
    returns_list = []
    accel_list = []
    series = {}
    for s in body.symbols:
        try:
            bars = poly_client.get_bars(s, 1, "day", (datetime.utcnow().date().replace(year=datetime.utcnow().year - 1)).isoformat(), datetime.utcnow().date().isoformat())
            series[s] = bars
            if len(bars) < body.rsWindowDays + 2:
                returns_list.append(0.0); accel_list.append(0.0); continue
            end = bars[-1]["c"]; start = bars[-(body.rsWindowDays+1)]["c"]
            ret = (end - start) / start if start else 0.0
            returns_list.append(ret)
            s_end = bars[-1]["c"]; s_start = bars[-(body.asShortDays+1)]["c"]; l_start = bars[-(body.asLongDays+1)]["c"]
            rocS = (s_end - s_start) / s_start if s_start else 0.0
            rocL = (s_end - l_start) / l_start if l_start else 0.0
            accel_list.append(rocS - rocL)
        except Exception as e:
            logging.warning("ratings bars failed for %s: %s", s, e)
            returns_list.append(0.0)
            accel_list.append(0.0)
    def percentile(vals, v):
        if not vals: return 0
        sorted_vals = sorted(vals)
        idx = 0
        for i,x in enumerate(sorted_vals):
            if x > v: idx = i; break
        else:
            idx = len(sorted_vals)
        return round((idx/len(sorted_vals))*100)
    for i, s in enumerate(body.symbols):
        RS[s] = percentile(returns_list, returns_list[i])
        AS[s] = percentile(accel_list, accel_list[i])
    return {"RS": RS, "AS": AS}

# Screener
class Filter(BaseModel):
    field: str
    op: str
    value: float | int | str

class ScreenerBody(BaseModel):
    symbols: List[str]
    filters: List[Filter] = []
    sort: Optional[Dict[str, str]] = None

@api_router.post("/screeners/run")
async def run_screener(body: ScreenerBody):
    # Minimal screener using quotes and optional RSI from daily bars
    syms = list(dict.fromkeys([s.upper() for s in body.symbols]))
    quotes = poly_client.get_quotes_snapshot(syms)
    # map
    rows: Dict[str, Dict] = {q["symbol"]: {"symbol": q["symbol"], "last": q.get("last"), "changePct": q.get("changePct"), "volume": q.get("volume")} for q in quotes}

    # optional RSI fetch if any filter refers to rsi14
    needs_rsi = any(f.field.lower() == "rsi14" for f in body.filters)
    if needs_rsi:
        for s in syms:
            try:
                bars = poly_client.get_bars(s, 1, "day", (datetime.utcnow().date().replace(year=datetime.utcnow().year - 1)).isoformat(), datetime.utcnow().date().isoformat())
                closes = [b["c"] for b in bars]
                rsi = compute_rsi(closes, 14)
                rows[s]["rsi14"] = rsi
            except Exception:
                rows[s]["rsi14"] = None

    # apply filters
    def pass_filter(v, op, val):
        if v is None: return False
        if op in (">", "gt"): return v > val
        if op in (">=", "gte"): return v >= val
        if op in ("<", "lt"): return v < val
        if op in ("<=", "lte"): return v <= val
        if op == "between" and isinstance(val, list) and len(val)==2: return val[0] <= v <= val[1]
        return False

    out = []
    for s, r in rows.items():
        ok = True
        for f in body.filters:
            fv = r.get(f.field)
            if f.field == "rsi14" and fv is None:
                ok = False; break
            if not pass_filter(fv, f.op, f.value):
                ok = False; break
        if ok:
            out.append(r)

    if body.sort and body.sort.get("key"):
        k = body.sort["key"]; d = body.sort.get("dir", "desc")
        out.sort(key=lambda x: (x.get(k) is None, x.get(k)), reverse=(d=="desc"))

    return {"rows": out}

# util RSI
def compute_rsi(closes: List[float], n: int) -> float | None:
    if len(closes) < n + 2: return None
    gains = 0.0; losses = 0.0
    for i in range(1, n+1):
        ch = closes[i] - closes[i-1]
        gains += max(0, ch); losses += max(0, -ch)
    avgG = gains / n; avgL = losses / n
    rsis = None
    for i in range(n+1, len(closes)):
        ch = closes[i] - closes[i-1]
        gain = max(0, ch); loss = max(0, -ch)
        avgG = (avgG*(n-1) + gain)/n
        avgL = (avgL*(n-1) + loss)/n
        rs = 100 if avgL == 0 else avgG/avgL
        rsis = 100 - 100/(1+rs)
    return rsis

# Streaming quotes (fallback polling). Client connects to /api/ws/quotes?symbols=AAPL,MSFT
connections: List[WebSocket] = []

@api_router.websocket("/ws/quotes")
async def ws_quotes(ws: WebSocket):
    await ws.accept()
    connections.append(ws)
    try:
        params = ws.query_params
        symbols = params.get("symbols", "").split(",") if params else []
        symbols = [s.strip().upper() for s in symbols if s.strip()]
        # Polling fallback every 2s; in a later pass we can wire Polygon WS
        while True:
            if poly_client and symbols:
                data = poly_client.get_quotes_snapshot(symbols)
                await ws.send_json({"type": "quotes", "data": data})
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await ws.close(code=1011)
    finally:
        if ws in connections:
            connections.remove(ws)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()