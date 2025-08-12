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
from alerts import Alert, AlertCreate, Notification

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

# ---------------- Alerts & Notifications ----------------
@api_router.get('/alerts')
async def list_alerts(symbol: Optional[str] = None):
    q = {"symbol": symbol} if symbol else {}
    docs = await db.alerts.find(q).to_list(1000)
    return [{k: v for k, v in d.items() if k != '_id'} for d in docs]

@api_router.post('/alerts')
async def create_alert(body: AlertCreate):
    a = Alert(symbol=body.symbol.upper(), type=body.type, value=body.value, note=body.note)
    await db.alerts.insert_one(a.dict())
    return a

@api_router.delete('/alerts/{id}')
async def delete_alert(id: str):
    await db.alerts.delete_one({"id": id})
    return {"ok": True}

@api_router.get('/notifications')
async def list_notifications(limit: int = 50):
    docs = await db.notifications.find().sort("createdAt", -1).limit(limit).to_list(limit)
    return [{k: v for k, v in d.items() if k != '_id'} for d in docs]

# WS for notifications
notif_clients: List[WebSocket] = []
@api_router.websocket('/ws/notifications')
async def ws_notifications(ws: WebSocket):
    await ws.accept()
    notif_clients.append(ws)
    try:
        while True:
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        pass
    finally:
        if ws in notif_clients:
            notif_clients.remove(ws)

async def broadcast_notification(data: Dict[str, Any]):
    for ws in list(notif_clients):
        try:
            await ws.send_json({"type": "notification", "data": data})
        except Exception:
            try:
                await ws.close()
            except Exception:
                pass
            if ws in notif_clients:
                notif_clients.remove(ws)

# background alert checker
async def alert_runner():
    await asyncio.sleep(2)
    while True:
        try:
            alerts = await db.alerts.find({"enabled": True}).to_list(5000)
            if not alerts or not poly_client:
                await asyncio.sleep(3)
                continue
            symbols = sorted(list({a.get('symbol') for a in alerts if a.get('symbol')}))
            if not symbols:
                await asyncio.sleep(3)
                continue
            quotes = poly_client.get_quotes_snapshot(symbols)
            qmap = {q['symbol']: q for q in quotes}
            for a in alerts:
                sym = a['symbol']
                q = qmap.get(sym) or {}
                last = q.get('last')
                chg = q.get('changePct')
                triggered = False
                if a['type'] == 'price_above' and last is not None and last >= a['value']:
                    triggered = True
                if a['type'] == 'price_below' and last is not None and last <= a['value']:
                    triggered = True
                if a['type'] == 'pct_change_ge' and chg is not None and chg >= a['value']:
                    triggered = True
                if triggered:
                    # disable alert and store notification
                    await db.alerts.update_one({"id": a['id']}, {"$set": {"enabled": False, "triggeredAt": datetime.utcnow()}})
                    note = a.get('note')
                    msg = f"{sym} triggered {a['type']} at {last} (%chg {round(chg,2) if chg is not None else 'N/A'})"
                    if note:
                        msg += f" — {note}"
                    notif = Notification(symbol=sym, message=msg)
                    await db.notifications.insert_one(notif.dict())
                    await broadcast_notification({"id": notif.id, "symbol": sym, "message": msg, "createdAt": notif.createdAt.isoformat()})
        except Exception as e:
            logging.warning("alert runner error: %s", e)
        await asyncio.sleep(3)

# ---------------- Watchlists (v2 with sections) ----------------
class Section(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    color: Optional[str] = None  # hex or token
    symbols: List[str] = Field(default_factory=list)

class Watchlist(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    color: Optional[str] = None
    symbols: List[str] = Field(default_factory=list)  # union for backward-compat
    sections: List[Section] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class WatchlistCreate(BaseModel):
    name: str
    color: Optional[str] = None
    symbols: Optional[List[str]] = None
    sections: Optional[List[Section]] = None

class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    sections: Optional[List[Section]] = None

@api_router.get('/watchlists')
async def get_watchlists():
    docs = await db.watchlists.find().sort('createdAt', 1).to_list(1000)
    out = []
    for d in docs:
        d.pop('_id', None)
        # rebuild union symbols for compatibility
        sections = d.get('sections') or []
        if sections:
            sym_set = []
            for sec in sections:
                for s in sec.get('symbols', []) or []:
                    sym_set.append(s)
            d['symbols'] = sym_set
        out.append(d)
    return out

@api_router.post('/watchlists')
async def create_watchlist(body: WatchlistCreate):
    wl = Watchlist(name=body.name, color=body.color)
    if body.sections:
        # Trust provided sections
        wl.sections = body.sections
    elif body.symbols:
        # Create default section if only symbols provided
        wl.sections = [Section(name='Main', color=body.color, symbols=[s.upper() for s in body.symbols])]
    # union symbols
    wl.symbols = [s for sec in wl.sections for s in (sec.symbols or [])]
    await db.watchlists.insert_one(wl.dict())
    return wl

@api_router.put('/watchlists/{id}')
async def update_watchlist(id: str, body: WatchlistUpdate):
    doc = await db.watchlists.find_one({"id": id})
    if not doc:
        raise HTTPException(404, 'Not found')
    upd: Dict[str, Any] = {}
    if body.name is not None:
        upd['name'] = body.name
    if body.color is not None:
        upd['color'] = body.color
    if body.sections is not None:
        # ensure symbols uppercased
        sections = []
        for sec in body.sections:
            symbols = [s.upper() for s in (sec.symbols or [])]
            sections.append({"id": sec.id or str(uuid.uuid4()), "name": sec.name, "color": sec.color, "symbols": symbols})
        upd['sections'] = sections
        # rebuild union
        upd['symbols'] = [s for sec in sections for s in (sec.get('symbols') or [])]
    upd['updatedAt'] = datetime.utcnow()
    await db.watchlists.update_one({"id": id}, {"$set": upd})
    new_doc = await db.watchlists.find_one({"id": id})
    new_doc.pop('_id', None)
    return new_doc

@api_router.delete('/watchlists/{id}')
async def delete_watchlist(id: str):
    await db.watchlists.delete_one({"id": id})
    return {"ok": True}

# ---------------- Screener metadata/run (same as before) ----------------
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
    page: Optional[Dict[str, Any]] = None

@api_router.post("/screeners/run")
async def run_screener_endpoint(body: ScreenerBody):
    if not poly_client:
        return {"rows": [], "nextCursor": None}
    syms = [s.strip().upper() for s in body.symbols if s.strip()]
    rows = run_screener(poly_client, finn_client, syms, body.filters or [], body.sort)
    limit = int((body.page or {}).get('limit') or 100)
    cursor = int((body.page or {}).get('cursor') or 0)
    page_rows = rows[cursor: cursor + limit]
    next_cursor = cursor + limit if (cursor + limit) < len(rows) else None
    return {"rows": page_rows, "nextCursor": next_cursor}

# ---------------- Market data ----------------
@api_router.get("/marketdata/quotes")
async def get_quotes(symbols: str):
    if not poly_client:
        return {"quotes": []}
    syms = [s.strip().upper() for s in symbols.split(',') if s.strip()]
    data = poly_client.get_quotes_snapshot(syms)
    return {"quotes": data}

@api_router.get("/")
async def root():
    return {"message": "Hello World"}

# ---------------- WebSocket quotes ----------------
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

@app.on_event("startup")
async def startup_tasks():
    asyncio.create_task(alert_runner())

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()