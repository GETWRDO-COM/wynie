from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime
import asyncio

from polygon_client import PolygonClient
from finnhub_client import FinnhubClient
from screener_engine import run_screener
from screener_registry import REGISTRY as SCREENER_REGISTRY

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

POLYGON_KEY = os.environ.get('POLYGON_API_KEY', '')
FINNHUB_KEY = os.environ.get('FINNHUB_API_KEY', '')
poly_client = PolygonClient(POLYGON_KEY) if POLYGON_KEY else None
finn_client = FinnhubClient(FINNHUB_KEY) if FINNHUB_KEY else None

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ---------------- Settings ----------------
class SettingsBody(BaseModel):
    polygon: Optional[str] = None
    finnhub: Optional[str] = None

@api_router.get('/settings')
async def get_settings():
    return { 'polygon': bool(POLYGON_KEY), 'finnhub': bool(FINNHUB_KEY) }

@api_router.post('/settings')
async def update_settings(body: SettingsBody):
    global POLYGON_KEY, FINNHUB_KEY, poly_client, finn_client
    if body.polygon is not None:
        POLYGON_KEY = body.polygon
        poly_client = PolygonClient(POLYGON_KEY)
    if body.finnhub is not None:
        FINNHUB_KEY = body.finnhub
        finn_client = FinnhubClient(FINNHUB_KEY)
    # persist to .env
    env_path = ROOT_DIR / '.env'
    try:
        lines: List[str] = []
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.read().splitlines()
        def upsert(lines, key, val):
            for i, ln in enumerate(lines):
                if ln.startswith(f"{key}="):
                    lines[i] = f"{key}=\"{val}\""; return
            lines.append(f"{key}=\"{val}\"")
        if body.polygon is not None:
            upsert(lines, 'POLYGON_API_KEY', POLYGON_KEY)
        if body.finnhub is not None:
            upsert(lines, 'FINNHUB_API_KEY', FINNHUB_KEY)
        with open(env_path, 'w') as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        logging.warning('Failed to persist keys to .env: %s', e)
    return { 'ok': True }

# ---------------- Columns schema & presets ----------------
COLUMN_SCHEMA: List[Dict[str, Any]] = [
    {"id": "logo", "label": "Logo", "category": "General", "type": "image", "source": "provider"},
    {"id": "symbol", "label": "Symbol", "category": "General", "type": "string", "source": "provider"},
    {"id": "description", "label": "Description", "category": "General", "type": "string", "source": "provider"},
    {"id": "sector", "label": "Sector", "category": "Sector & Industry", "type": "string", "source": "provider"},
    {"id": "industry", "label": "Industry", "category": "Sector & Industry", "type": "string", "source": "provider"},
    {"id": "last", "label": "Last", "category": "Price & Volume", "type": "number", "source": "provider"},
    {"id": "changePct", "label": "% Chg", "category": "Price & Volume", "type": "number", "source": "computed"},
    {"id": "volume", "label": "Vol", "category": "Price & Volume", "type": "number", "source": "provider"},
    {"id": "avgVol20d", "label": "AvgVol20d", "category": "Price & Volume", "type": "number", "source": "computed"},
    {"id": "runRate20d", "label": "RunRate20d", "category": "Price & Volume", "type": "number", "source": "computed"},
    {"id": "relVol", "label": "RelVol", "category": "Price & Volume", "type": "number", "source": "computed"},
    {"id": "pct_to_hi52", "label": "% to 52w High", "category": "Price & Volume", "type": "number", "source": "computed"},
    {"id": "pct_above_lo52", "label": "% above 52w Low", "category": "Price & Volume", "type": "number", "source": "computed"},
    {"id": "sma20", "label": "SMA20", "category": "Technicals", "type": "number", "source": "computed"},
    {"id": "sma50", "label": "SMA50", "category": "Technicals", "type": "number", "source": "computed"},
    {"id": "sma200", "label": "SMA200", "category": "Technicals", "type": "number", "source": "computed"},
    {"id": "ema8", "label": "EMA8", "category": "Technicals", "type": "number", "source": "computed"},
    {"id": "ema21", "label": "EMA21", "category": "Technicals", "type": "number", "source": "computed"},
    {"id": "ema50", "label": "EMA50", "category": "Technicals", "type": "number", "source": "computed"},
    {"id": "rsi14", "label": "RSI(14)", "category": "Technicals", "type": "number", "source": "computed"},
    {"id": "atr14", "label": "ATR(14)", "category": "Technicals", "type": "number", "source": "computed"},
    {"id": "RS", "label": "RS", "category": "Proprietary Ratings", "type": "number", "source": "computed"},
    {"id": "AS", "label": "AS", "category": "Proprietary Ratings", "type": "number", "source": "computed"},
]

@api_router.get("/columns/schema")
async def get_columns_schema():
    cats: Dict[str, List[Dict[str, Any]]] = {}
    for c in COLUMN_SCHEMA:
        cats.setdefault(c["category"], []).append(c)
    return {"categories": [{"name": k, "columns": v} for k, v in cats.items()]}

class PresetBody(BaseModel):
    name: str
    columns: List[str]

@api_router.get("/columns/presets")
async def get_column_presets():
    docs = await db.column_presets.find().to_list(200)
    return {d["name"]: d["columns"] for d in docs}

@api_router.post("/columns/presets")
async def save_column_preset(body: PresetBody):
    await db.column_presets.update_one({"name": body.name}, {"$set": {"name": body.name, "columns": body.columns, "updatedAt": datetime.utcnow()}}, upsert=True)
    return {"ok": True}

@api_router.delete("/columns/presets/{name}")
async def delete_preset(name: str):
    await db.column_presets.delete_one({"name": name})
    return {"ok": True}

# ---------------- Ratings (RS/AS) ----------------
class RatingsBody(BaseModel):
    symbols: List[str]
    rsWindowDays: int = 63
    asShortDays: int = 21
    asLongDays: int = 63

@api_router.post("/ratings/compute")
async def ratings_compute(body: RatingsBody):
    if not poly_client:
        return {"RS": {}, "AS": {}}
    # compute using daily bars percentile ranks
    RS: Dict[str, float] = {}
    AS: Dict[str, float] = {}
    returns_list: List[float] = []
    accel_list: List[float] = []
    series: Dict[str, List[Dict[str, Any]]] = {}
    for s in body.symbols:
        try:
            from_date = (datetime.utcnow().date().replace(year=datetime.utcnow().year - 1)).isoformat()
            to_date = datetime.utcnow().date().isoformat()
            bars = poly_client.get_bars(s, 1, "day", from_date, to_date)
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

# ---------------- Screener registry & run & saved ----------------
@api_router.get("/screeners/filters")
async def screener_filters():
    cats: Dict[str, List[Dict[str, Any]]] = {}
    for c in SCREENER_REGISTRY:
        cats.setdefault(c["category"], []).append(c)
    return {"categories": [{"name": k, "fields": v} for k, v in cats.items()]}

class Filter(BaseModel):
    field: Optional[str] = None
    op: Optional[str] = None
    value: Optional[Any] = None
    logic: Optional[str] = None
    filters: Optional[List['Filter']] = None
Filter.model_rebuild()

class ScreenerBody(BaseModel):
    symbols: List[str]
    filters: Optional[Any] = None
    sort: Optional[Dict[str, str]] = None
    page: Optional[Dict[str, Any]] = None  # {limit: int, cursor: int}

@api_router.post("/screeners/run")
async def run_screener_endpoint(body: ScreenerBody):
    if not poly_client:
        return {"rows": [], "nextCursor": None}
    syms = [s.strip().upper() for s in body.symbols if s.strip()]
    rows = run_screener(poly_client, finn_client, syms, body.filters or [], body.sort)
    # simple offset pagination
    limit = int((body.page or {}).get('limit') or 100)
    cursor = int((body.page or {}).get('cursor') or 0)
    page_rows = rows[cursor: cursor + limit]
    next_cursor = cursor + limit if (cursor + limit) < len(rows) else None
    return {"rows": page_rows, "nextCursor": next_cursor}

# saved screeners
class ScreenerDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    symbols: List[str] = []
    filters: Any = None
    sort: Optional[Dict[str, str]] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

@api_router.get("/screeners")
async def list_screeners():
    docs = await db.screeners.find().to_list(200)
    return [{k: v for k, v in d.items() if k != '_id'} for d in docs]

@api_router.post("/screeners")
async def create_screener(body: ScreenerDoc):
    body.updatedAt = datetime.utcnow()
    await db.screeners.insert_one(body.dict())
    return body

@api_router.put("/screeners/{id}")
async def update_screener(id: str, body: Dict[str, Any]):
    body['updatedAt'] = datetime.utcnow()
    await db.screeners.update_one({"id": id}, {"$set": body}, upsert=False)
    doc = await db.screeners.find_one({"id": id})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return {k: v for k, v in doc.items() if k != '_id'}

@api_router.delete("/screeners/{id}")
async def delete_screener(id: str):
    await db.screeners.delete_one({"id": id})
    return {"ok": True}

# ---------------- Watchlists ----------------
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

# ---------------- Market data ----------------
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
    to = to or datetime.utcnow().date().isoformat()
    fr = fr or (datetime.utcnow().date().replace(year=datetime.utcnow().year - 1).isoformat())
    if interval in ["1","5","15","60"]:
        mult = int(interval); span = "minute"
    elif interval in ["1D","D"]:
        mult = 1; span = "day"
    elif interval in ["1W","W"]:
        mult = 1; span = "week"
    else:
        mult = 1; span = "day"
    try:
        bars = poly_client.get_bars(symbol, mult, span, fr, to)
        return {"symbol": symbol, "bars": bars}
    except Exception as e:
        logging.warning("bars fetch failed: %s", e)
        return {"symbol": symbol, "bars": []}

@api_router.get("/")
async def root():
    return {"message": "Hello World"}

# ---------------- Streaming quotes ----------------
@api_router.websocket("/ws/quotes")
async def ws_quotes(ws):
    await ws.accept()
    params = ws.query_params
    symbols = params.get("symbols", "").split(",") if params else []
    symbols = [s.strip().upper() for s in symbols if s.strip()]
    try:
        while True:
            if poly_client and symbols:
                data = poly_client.get_quotes_snapshot(symbols)
                await ws.send_json({"type": "quotes", "data": data})
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except Exception:
        await ws.close(code=1011)

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