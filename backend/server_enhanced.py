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
            # Restrict auto-create to the known user
            if email != "beetge@mwebbiz.co.za":
                raise HTTPException(status_code=401, detail="Access restricted to authorized users only")
            # create user with provided password
            hashed = hash_password(password)
            now = datetime.utcnow()
            await db.users.insert_one({
                "email": email,
                "hashed_password": hashed,
                "created_at": now,
                "last_login": now,
            })
            user = await db.users.find_one({"email": email})
        # verify
        if not verify_password(password, user.get("hashed_password", "")):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        # update last_login
        await db.users.update_one({"email": email}, {"$set": {"last_login": datetime.utcnow()}})
        # token
        token = create_access_token({"sub": email})
        return {"access_token": token, "token_type": "bearer", "user": {"email": user.get("email"), "last_login": user.get("last_login")}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/forgot-password")
async def forgot_password(req: PasswordReset):
    try:
        # Do not reveal if user exists
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

# Finnhub earnings calendar
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

# Normalize market score shape
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
        # Remove MongoDB ObjectId to avoid serialization issues
        if '_id' in doc:
            del doc['_id']
        score = doc.get('score') or doc.get('total_score')
        trend = doc.get('trend') or doc.get('classification')
        last_updated = doc.get('last_updated') or doc.get('date') or datetime.utcnow().isoformat()
        recommendation = doc.get('recommendation')
        normalized = {"score": score, "trend": trend, "last_updated": last_updated, "recommendation": recommendation}
        # Add other fields from doc if they exist
        for key, value in doc.items():
            if key not in normalized and key != '_id':
                normalized[key] = value
        return normalized
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(api_router)