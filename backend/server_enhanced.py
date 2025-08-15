from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone, date
import asyncio
import aiohttp
import json
import pandas as pd
import numpy as np
import pytz
import requests
import bcrypt
import jwt
from xml.etree import ElementTree as ET
from hashlib import sha256
import base64
from cryptography.fernet import Fernet
from urllib.parse import quote, urlparse

# Import deepvue screener functionality
try:
    from polygon_client import PolygonClient
    from finnhub_client import FinnhubClient  
    from screener_engine import run_screener
    SCREENER_AVAILABLE = True
except ImportError:
    SCREENER_AVAILABLE = False

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")

JWT_SECRET = os.environ.get('JWT_SECRET', 'etf-intelligence-secret-key')
JWT_ALGORITHM = "HS256"
security = HTTPBearer()
SA_TZ = pytz.timezone('Africa/Johannesburg')
NY_TZ = pytz.timezone('America/New_York')

CACHE: Dict[str, Dict[str, Any]] = {}

def cache_get(key: str):
    item = CACHE.get(key)
    if not item:
        return None
    if datetime.now(timezone.utc) > item["expires_at"]:
        CACHE.pop(key, None)
        return None
    return item["value"]

def cache_set(key: str, value: Any, ttl_seconds: int):
    CACHE[key] = {"value": value, "expires_at": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)}

FERNET_KEY = base64.urlsafe_b64encode(sha256(JWT_SECRET.encode()).digest())
fernet = Fernet(FERNET_KEY)

# =====================
# Auth helpers + models
# =====================
class LoginRequest(BaseModel):
    email: str
    password: str

class PasswordReset(BaseModel):
    email: str

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=12))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


class PolygonKeyInput(BaseModel):
    api_key: str

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = await db.users.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_polygon_api_key() -> Optional[str]:
    doc = await db.app_settings.find_one({"key": "polygon_api_key"})
    if doc and doc.get("encrypted_value"):
        try:
            return fernet.decrypt(doc["encrypted_value"]).decode()
        except Exception:
            pass
    return os.environ.get("POLYGON_API_KEY")

async def get_finnhub_api_key() -> Optional[str]:
    doc = await db.app_settings.find_one({"key": "finnhub_api_key"})
    if doc and doc.get("encrypted_value"):
        try:
            return fernet.decrypt(doc["encrypted_value"]).decode()
        except Exception:
            pass
    return os.environ.get("FINNHUB_API_KEY")

# =====================
# Auth routes (fix login 404)
# =====================
@api_router.post("/auth/login")
async def login(data: LoginRequest):
    try:
        email = data.email.strip().lower()
        password = data.password
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")

        user = await db.users.find_one({"email": email})
        if not user:
            if email != "beetge@mwebbiz.co.za":
                raise HTTPException(status_code=401, detail="Access restricted to authorized users only")
            hashed = hash_password(password)
            now = datetime.utcnow()
            await db.users.insert_one({
                "email": email,
                "hashed_password": hashed,
                "created_at": now,
                "last_login": now,
            })
            user = await db.users.find_one({"email": email})
        if not verify_password(password, user.get("hashed_password", "")):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        await db.users.update_one({"email": email}, {"$set": {"last_login": datetime.utcnow()}})
        token = create_access_token({"sub": email})
        return {"access_token": token, "token_type": "bearer", "user": {"email": user.get("email"), "last_login": user.get("last_login")}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/forgot-password")
async def forgot_password(req: PasswordReset):
    try:
        return {"message": "If this email exists in our system, you will receive password reset instructions.", "temp_instructions": "Please contact system administrator for password reset assistance."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return {"email": user.get("email"), "last_login": user.get("last_login")}


@api_router.post("/integrations/polygon/key")
async def set_polygon_key(data: PolygonKeyInput, user: dict = Depends(get_current_user)):
    try:
        enc = fernet.encrypt(data.api_key.encode())
        await db.app_settings.update_one(
            {"key": "polygon_api_key"},
            {"$set": {"key": "polygon_api_key", "encrypted_value": enc, "updated_at": datetime.utcnow()}},
            upsert=True
        )
        return {"message": "Polygon API key saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/integrations/polygon/status")
async def polygon_status(user: dict = Depends(get_current_user)):
    key = await get_polygon_api_key()
    return {"configured": bool(key)}

# =====================
# Legacy/expected endpoints for UI compatibility
# =====================
@api_router.get("/dashboard")
async def dashboard_summary(user: dict = Depends(get_current_user)):
    # Minimal placeholder to satisfy UI; extend as needed
    return {"message": "ok", "time": datetime.utcnow().isoformat()}

@api_router.get("/etfs")
async def list_etfs(limit: int = Query(200)):
    # Try to read from DB if available, else return empty list
    try:
        docs = await db.etfs.find().limit(limit).to_list(length=limit)
        # Strip ObjectIds and return a small subset to keep payload light
        def clean(d):
            d.pop('_id', None)
            return d
        return [clean(d) for d in docs]
    except Exception:
        return []

@api_router.get("/etfs/sectors")
async def etf_sectors():
    try:
        sectors = await db.etfs.distinct('sector')
        sectors = [s for s in sectors if s]
        return {"sectors": sectors}
    except Exception:
        return {"sectors": []}

@api_router.get("/etfs/swing-leaders")
async def swing_leaders():
    # Placeholder minimal list; UI handles empty gracefully
    try:
        docs = await db.swing_leaders.find().sort("change_1m", -1).limit(10).to_list(10)
        for d in docs:
            d.pop('_id', None)
        return docs
    except Exception:
        return []

@api_router.get("/watchlists/custom")
async def custom_watchlists(user: dict = Depends(get_current_user)):
    try:
        lists = await db.watchlists.find({"owner": user.get("email")}).to_list(50)
        for w in lists:
            w.pop('_id', None)
        return lists
    except Exception:
        return []

@api_router.get("/charts/indices")
async def charts_indices(timeframe: str = Query("1m")):
    # Bridge to market/aggregates for compatibility
    # Map timeframe to our ranges
    tf_map = {"1d":"1D","1w":"1W","1m":"1M","ytd":"YTD","1y":"1Y"}
    rng = tf_map.get(timeframe.lower(), "1M")
    try:
        # Reuse the market_aggregates logic via HTTP call to self is overkill; instead return empty
        # The current UI no longer depends on this data for charts; keep shape compatible
        return {"data": {}}
    except Exception:
        return {"data": {}}

# =====================
# News + Data endpoints
# =====================
NEWS_FEEDS = {
    "All": 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',
    "USA": 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',
    "World": 'https://news.google.com/rss/search?q=world%20news&hl=en-US&gl=US&ceid=US:en',
    "South Africa": 'https://news.google.com/rss?hl=en-ZA&gl=ZA&ceid=ZA:en',
    "Stock Market": 'https://news.google.com/rss/search?q=stock%20market&hl=en-US&gl=US&ceid=US:en',
    "Finance News": 'https://news.google.com/rss/search?q=finance&hl=en-US&gl=US&ceid=US:en',
}

@api_router.get("/news")
async def news_proxy(category: str = Query("All"), q: Optional[str] = Query(None)):
    if q:
        cache_key = f"newsq:{q}"
        cached = cache_get(cache_key)
        if cached:
            return {"category": f"search:{q}", "items": cached, "cached": True}
        url = f"https://news.google.com/rss/search?q={quote(q)}&hl=en-US&gl=US&ceid=US:en"
    else:
        cache_key = f"news:{category}"
        cached = cache_get(cache_key)
        if cached:
            return {"category": category, "items": cached, "cached": True}
        url = NEWS_FEEDS.get(category, NEWS_FEEDS["All"])
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
            "Accept": "text/xml,application/xml,application/rss+xml,application/xhtml+xml,application/html;q=0.9,text/plain;q=0.8,*/*;q=0.5",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=25) as resp:
                text = await resp.text()
        root = ET.fromstring(text)
        ns = { 'media': 'http://search.yahoo.com/mrss/' }
        items = []
        for it in root.findall('.//item'):
            title_el = it.find('title')
            link_el = it.find('link')
            pub_el = it.find('pubDate')
            title = title_el.text if title_el is not None else ''
            link = link_el.text if link_el is not None else '#'
            published = pub_el.text if pub_el is not None else None
            thumb = None
            mthumb = it.find('media:thumbnail', ns)
            if mthumb is not None and mthumb.attrib.get('url'):
                thumb = mthumb.attrib.get('url')
            else:
                mcont = it.find('media:content', ns)
                if mcont is not None and mcont.attrib.get('url'):
                    thumb = mcont.attrib.get('url')
            if not thumb:
                encl = it.find('enclosure')
                if encl is not None and encl.attrib.get('url'):
                    thumb = encl.attrib.get('url')
            source = None
            try:
                source = urlparse(link).hostname
            except Exception:
                source = None
            if title:
                items.append({"title": title, "link": link, "thumb": thumb, "published": published, "source": source})
        items = items[:100]
        cache_set(cache_key, items, ttl_seconds=300)
        return {"category": category, "items": items, "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News fetch failed: {e}")

CNN_JSON_URLS = [
    "https://production-files-cnn.com/markets/fearandgreed/graphdata.json",
    "https://production-files-cnn.com/markets/fearandgreed/greedandfear.json",
]

@api_router.get("/greed-fear")
async def greed_fear():
    cache_key = "greed_fear"
    cached = cache_get(cache_key)
    if cached:
        return {"source": cached.get("source", "cache"), **cached}
    try:
        async with aiohttp.ClientSession() as session:
            for u in CNN_JSON_URLS:
                try:
                    async with session.get(u, timeout=20) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            result = {
                                "now": data.get("fear_and_greed", {}).get("score") or data.get("now"),
                                "previous_close": data.get("previous_close"),
                                "one_week_ago": data.get("one_week_ago"),
                                "one_month_ago": data.get("one_month_ago"),
                                "one_year_ago": data.get("one_year_ago"),
                                "timeseries": data.get("timeseries") or data.get("data"),
                                "last_updated": datetime.utcnow().isoformat(),
                                "source": "cnn-json"
                            }
                            cache_set(cache_key, result, ttl_seconds=21600)
                            return result
                except Exception:
                    continue
    except Exception:
        pass
    raise HTTPException(status_code=502, detail="Unable to fetch CNN Fear & Greed Index")

TIME_RANGE_CONFIG = {
    "1D": {"multiplier": 5, "timespan": "minute", "days_back": 1},
    "1W": {"multiplier": 30, "timespan": "minute", "days_back": 7},
    "1M": {"multiplier": 1, "timespan": "day", "days_back": 31},
    "YTD": {"multiplier": 1, "timespan": "day", "from_start_of_year": True},
    "1Y": {"multiplier": 1, "timespan": "day", "days_back": 365},
    "5Y": {"multiplier": 1, "timespan": "week", "days_back": 365*5},
}

async def fetch_polygon_prev_close(session: aiohttp.ClientSession, base: str, ticker: str, api_key: str):
    url = f"{base}/v2/aggs/ticker/{quote(ticker, safe=':')}/prev?adjusted=true&apiKey={api_key}"
    async with session.get(url, timeout=30) as resp:
        if resp.status != 200:
            return None
        data = await resp.json()
        results = data.get("results") or []
        if results:
            return results[0].get("c")
        return None

async def fetch_polygon_open_close(session: aiohttp.ClientSession, base: str, ticker: str, date_str: str, api_key: str):
    url = f"{base}/v1/open-close/{quote(ticker, safe=':')}/{date_str}?adjusted=true&apiKey={api_key}"
    async with session.get(url, timeout=30) as resp:
        if resp.status != 200:
            return None
        try:
            data = await resp.json()
        except Exception:
            return None
        return {"open": data.get("open"), "close": data.get("close"), "preMarket": data.get("preMarket"), "afterHours": data.get("afterHours")}

@api_router.get("/market/aggregates")
async def market_aggregates(
    tickers: str = Query("SPY,QQQ,I:DJI,TQQQ,SQQQ"),
    range: str = Query("1M", regex="^(1D|1W|1M|YTD|1Y|5Y)$")
):
    api_key = await get_polygon_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="Polygon API key not configured")
    cfg = TIME_RANGE_CONFIG[range]
    end_dt = datetime.now(timezone.utc)
    if cfg.get("from_start_of_year"):
        start_dt = datetime(end_dt.year, 1, 1, tzinfo=timezone.utc)
    else:
        start_dt = end_dt - timedelta(days=cfg.get("days_back", 30))
    base = "https://api.polygon.io"
    out: Dict[str, Any] = {}
    tlist = [t.strip() for t in tickers.split(',') if t.strip()]
    async with aiohttp.ClientSession() as session:
        async def fetch_one(t: str):
            agg_url = f"{base}/v2/aggs/ticker/{quote(t, safe=':')}/range/{cfg['multiplier']}/{cfg['timespan']}/{start_dt.date()}/{end_dt.date()}?adjusted=true&sort=asc&apiKey={api_key}"
            async with session.get(agg_url, timeout=40) as resp:
                data = await resp.json()
            results = data.get("results") or []
            series = [{"t": r.get("t"), "o": r.get("o"), "h": r.get("h"), "l": r.get("l"), "c": r.get("c"), "v": r.get("v")} for r in results]
            last_close = series[-1]["c"] if series else None
            prev_close = await fetch_polygon_prev_close(session, base, t, api_key)
            pre_val = None
            post_val = None
            open_val = None
            if not t.startswith("I:"):
                et_now = datetime.now(NY_TZ)
                date_str = et_now.strftime("%Y-%m-%d")
                oc = await fetch_polygon_open_close(session, base, t, date_str, api_key)
                if oc:
                    pre_val = oc.get("preMarket")
                    post_val = oc.get("afterHours")
                    open_val = oc.get("open")
            change_pct = None
            if last_close and prev_close:
                try:
                    change_pct = (last_close - prev_close) / prev_close * 100
                except Exception:
                    change_pct = None
            out[t] = {"series": series, "close": last_close, "prev_close": prev_close, "open": open_val, "pre_market": pre_val, "post_market": post_val, "change_pct": change_pct}
        await asyncio.gather(*[fetch_one(t) for t in tlist])
    return {"range": range, "last_updated": datetime.utcnow().isoformat(), "data": out}

@api_router.get("/earnings")
async def earnings(tickers: Optional[str] = Query(None), days_ahead: int = Query(30)):
    api_key = os.environ.get('FINNHUB_API_KEY')
    if not api_key:
        raise HTTPException(status_code=400, detail="Finnhub API key not configured")
    base = "https://finnhub.io/api/v1/calendar/earnings"
    today = date.today()
    to = today + timedelta(days=days_ahead)
    out = []
    try:
        async with aiohttp.ClientSession() as session:
            if tickers:
                syms = [s.strip().upper() for s in tickers.split(',') if s.strip()][:20]
                for s in syms:
                    url = f"{base}?symbol={quote(s)}&from={today}&to={to}&token={api_key}"
                    try:
                        async with session.get(url, timeout=20) as resp:
                            js = await resp.json()
                        for r in (js.get('earningsCalendar') or []):
                            out.append({
                                "ticker": r.get('symbol') or s,
                                "date": r.get('date'),
                                "time": r.get('hour') or r.get('time'),
                                "period": r.get('quarter'),
                                "estimate": r.get('epsEstimate'),
                                "actual": r.get('epsActual'),
                                "surprise": r.get('epsSurprise'),
                                "link": f"https://finnhub.io/stock/{s}"
                            })
                    except Exception:
                        continue
            else:
                url = f"{base}?from={today}&to={to}&token={api_key}"
                async with session.get(url, timeout=20) as resp:
                    js = await resp.json()
                for r in (js.get('earningsCalendar') or []):
                    out.append({
                        "ticker": r.get('symbol'),
                        "date": r.get('date'),
                        "time": r.get('hour') or r.get('time'),
                        "period": r.get('quarter'),
                        "estimate": r.get('epsEstimate'),
                        "actual": r.get('epsActual'),
                        "surprise": r.get('epsSurprise'),
                        "link": f"https://finnhub.io/stock/{r.get('symbol')}"
                    })
        return {"items": out[:50], "last_updated": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/market-score")
async def get_market_score_normalized():
    try:
        scores = await db.market_scores.find().sort("date", -1).limit(1).to_list(1)
        if not scores:
            now = datetime.utcnow().isoformat()
            default = {"score": 16, "trend": "Yellow Day", "recommendation": "Selective entries. Use moderate position sizing.", "last_updated": now, "total_score": 16, "classification": "Yellow Day", "date": now}
            await db.market_scores.insert_one(default)
            return default
        doc = scores[0]
        score = doc.get('score') or doc.get('total_score')
        trend = doc.get('trend') or doc.get('classification')
        last_updated = doc.get('last_updated') or doc.get('date') or datetime.utcnow().isoformat()
        recommendation = doc.get('recommendation')
        normalized = {**doc, "score": score, "trend": trend, "last_updated": last_updated, "recommendation": recommendation}
        normalized.pop('_id', None)
        return normalized
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================
# Screener endpoints (from deepvue branch)
# =====================
class ScreenerRequest(BaseModel):
    symbols: List[str]
    filters: List[Dict[str, Any]] = []
    sort: Optional[Dict[str, str]] = None

@api_router.post("/screener/run")
async def run_stock_screener(request: ScreenerRequest, user: dict = Depends(get_current_user)):
    """Run stock screener with filters and sorting"""
    if not SCREENER_AVAILABLE:
        raise HTTPException(status_code=501, detail="Screener functionality not available")
    
    try:
        polygon_key = await get_polygon_api_key()
        if not polygon_key:
            raise HTTPException(status_code=400, detail="Polygon API key not configured")
        
        finnhub_key = await get_finnhub_api_key()
        
        poly_client = PolygonClient(polygon_key)
        finn_client = FinnhubClient(finnhub_key) if finnhub_key else None
        
        results = run_screener(
            poly_client, 
            finn_client, 
            request.symbols, 
            request.filters, 
            request.sort
        )
        
        return {
            "results": results,
            "total": len(results),
            "filters_applied": request.filters,
            "sort_applied": request.sort
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/screener/symbols/search")
async def search_symbols(q: str, limit: int = 25, user: dict = Depends(get_current_user)):
    """Search for stock symbols using Polygon API"""
    if not SCREENER_AVAILABLE:
        raise HTTPException(status_code=501, detail="Symbol search not available")
    
    try:
        polygon_key = await get_polygon_api_key()
        if not polygon_key:
            raise HTTPException(status_code=400, detail="Polygon API key not configured")
        
        poly_client = PolygonClient(polygon_key)
        results = poly_client.search_symbols(q, limit)
        
        return {"symbols": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/screener/fields")
async def get_screener_fields():
    """Get available fields for screening"""
    basic_fields = ["symbol", "last", "changePct", "volume", "liquidity"]
    technical_fields = [
        "sma20", "sma50", "sma200", "ema8", "ema21", "ema50",
        "rsi14", "atr14", "bb_bw", "macd_line", "macd_signal", 
        "macd_hist", "stoch_k", "stoch_d", "avgVol20d", "runRate20d",
        "relVol", "pct_to_hi52", "pct_above_lo52", "adr20", "gapPct"
    ]
    fundamental_fields = [
        "marketCap", "sharesOutstanding", "float", "peTTM", "psTTM", 
        "pb", "roe", "roa", "grossMarginTTM", "operatingMarginTTM", "netMarginTTM"
    ]
    computed_fields = [
        "sma50_above_sma200", "ema8_above_ema21", "macd_cross_up", "macd_cross_down"
    ]
    
    return {
        "basic": basic_fields,
        "technical": technical_fields,
        "fundamental": fundamental_fields,
        "computed": computed_fields,
        "operators": [">", ">=", "<", "<=", "==", "!=", "between", "in"]
    }

# =====================  
# Trading Journal endpoints (from trading-journal branch)
# =====================
class JournalEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    tags: List[str] = []
    date: datetime = Field(default_factory=datetime.utcnow)
    trades_mentioned: List[str] = []
    mood: str = "neutral"
    market_score: Optional[int] = None

class TradeEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    side: str  # "long" or "short"
    status: str = "open"  # "open", "closed"
    notes: str = ""
    tags: List[str] = []

@api_router.post("/journal/entries")
async def create_journal_entry(entry: JournalEntry, user: dict = Depends(get_current_user)):
    """Create a new journal entry"""
    try:
        entry_doc = entry.model_dump()
        entry_doc["user_id"] = user.get("email")
        entry_doc["created_at"] = datetime.utcnow()
        result = await db.journal_entries.insert_one(entry_doc)
        entry_doc["_id"] = str(result.inserted_id)
        return entry_doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/journal/entries")
async def get_journal_entries(limit: int = 50, skip: int = 0, user: dict = Depends(get_current_user)):
    """Get journal entries for the user"""
    try:
        cursor = db.journal_entries.find({"user_id": user.get("email")}).sort("date", -1).skip(skip).limit(limit)
        entries = await cursor.to_list(length=limit)
        for entry in entries:
            entry["_id"] = str(entry["_id"])
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/journal/trades")
async def create_trade_entry(trade: TradeEntry, user: dict = Depends(get_current_user)):
    """Create a new trade entry"""
    try:
        trade_doc = trade.model_dump()
        trade_doc["user_id"] = user.get("email")
        trade_doc["created_at"] = datetime.utcnow()
        result = await db.trade_entries.insert_one(trade_doc)
        trade_doc["_id"] = str(result.inserted_id)
        return trade_doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/journal/trades")
async def get_trade_entries(
    limit: int = 50, 
    skip: int = 0, 
    status: Optional[str] = None, 
    user: dict = Depends(get_current_user)
):
    """Get trade entries for the user"""
    try:
        query = {"user_id": user.get("email")}
        if status:
            query["status"] = status
        cursor = db.trade_entries.find(query).sort("entry_time", -1).skip(skip).limit(limit)
        trades = await cursor.to_list(length=limit)
        for trade in trades:
            trade["_id"] = str(trade["_id"])
        return {"trades": trades}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/journal/trades/{trade_id}")
async def update_trade_entry(trade_id: str, trade: TradeEntry, user: dict = Depends(get_current_user)):
    """Update an existing trade entry"""
    try:
        trade_doc = trade.model_dump()
        trade_doc["user_id"] = user.get("email")
        trade_doc["updated_at"] = datetime.utcnow()
        result = await db.trade_entries.update_one(
            {"id": trade_id, "user_id": user.get("email")}, 
            {"$set": trade_doc}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Trade not found")
        return {"message": "Trade updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(api_router)