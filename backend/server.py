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
from screener_engine import run_screener
from screener_registry import REGISTRY as SCREENER_REGISTRY

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

# ------------------- ROUTES -------------------
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

# Screener metadata
@api_router.get("/screeners/filters")
async def screener_filters():
    # Group by category for UI
    cats: Dict[str, List[Dict[str, Any]]] = {}
    for c in SCREENER_REGISTRY:
        cats.setdefault(c["category"], []).append(c)
    return {"categories": [{"name": k, "fields": v} for k, v in cats.items()]}

# Screener run
class Filter(BaseModel):
    field: Optional[str] = None
    op: Optional[str] = None
    value: Optional[Any] = None
    logic: Optional[str] = None
    filters: Optional[List['Filter']] = None

Filter.model_rebuild()

class ScreenerBody(BaseModel):
    symbols: List[str]
    filters: Optional[Any] = None  # can be list or group
    sort: Optional[Dict[str, str]] = None

@api_router.post("/screeners/run")
async def run_screener_endpoint(body: ScreenerBody):
    if not poly_client:
        return {"rows": []}
    syms = [s.strip().upper() for s in body.symbols if s.strip()]
    rows = run_screener(poly_client, syms, body.filters or [], body.sort)
    return {"rows": rows}

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
    # default daily
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

@api_router.get("/marketdata/quotes")
async def get_quotes(symbols: str):
    if not poly_client:
        return {"quotes": []}
    syms = [s.strip().upper() for s in symbols.split(',') if s.strip()]
    data = poly_client.get_quotes_snapshot(syms)
    return {"quotes": data}

# Streaming quotes (polling fallback)
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