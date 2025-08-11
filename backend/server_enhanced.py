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
from datetime import datetime, timedelta, timezone
import asyncio
import aiohttp
import json
import yfinance as yf
import pandas as pd
import numpy as np
from collections import defaultdict
import pytz
import requests
import bcrypt
import jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
from xml.etree import ElementTree as ET
from hashlib import sha256
import base64
from cryptography.fernet import Fernet
from urllib.parse import quote

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
JWT_SECRET = os.environ.get('JWT_SECRET', 'etf-intelligence-secret-key')
JWT_ALGORITHM = "HS256"

# Security
security = HTTPBearer()

# Timezone setup for South Africa
SA_TZ = pytz.timezone('Africa/Johannesburg')
NY_TZ = pytz.timezone('America/New_York')

# In-memory caches
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
    CACHE[key] = {
        "value": value,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    }

# --- Encryption helpers for settings ---
FERNET_KEY = base64.urlsafe_b64encode(sha256(JWT_SECRET.encode()).digest())
fernet = Fernet(FERNET_KEY)

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
    # DB first
    doc = await db.app_settings.find_one({"key": "polygon_api_key"})
    if doc and doc.get("encrypted_value"):
        try:
            return fernet.decrypt(doc["encrypted_value"]).decode()
        except Exception:
            pass
    # Fallback to env
    return os.environ.get("POLYGON_API_KEY")

@api_router.post("/integrations/polygon/key")
async def set_polygon_key(data: PolygonKeyInput, user: dict = Depends(get_current_user)):
    try:
        enc = fernet.encrypt(data.api_key.encode())
        await db.app_settings.update_one(
            {"key": "polygon_api_key"},
            {"$set": {"key": "polygon_api_key", "encrypted_value": enc, "updated_at": datetime.utcnow()}},
            upsert=True
        )
        # Do not return the key back
        return {"message": "Polygon API key saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/integrations/polygon/status")
async def polygon_status(user: dict = Depends(get_current_user)):
    key = await get_polygon_api_key()
    return {"configured": bool(key)}

# --- News Proxy ---
NEWS_FEEDS = {
    "All": 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',
    "USA": 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',
    "World": 'https://news.google.com/rss/search?q=world%20news&hl=en-US&gl=US&ceid=US:en',
    "South Africa": 'https://news.google.com/rss?hl=en-ZA&gl=ZA&ceid=ZA:en',
    "Stock Market": 'https://news.google.com/rss/search?q=stock%20market&hl=en-US&gl=US&ceid=US:en',
    "Finance News": 'https://news.google.com/rss/search?q=finance&hl=en-US&gl=US&ceid=US:en',
}

@api_router.get("/news")
async def news_proxy(category: str = Query("All")):
    cache_key = f"news:{category}"
    cached = cache_get(cache_key)
    if cached:
        return {"category": category, "items": cached, "cached": True}
    url = NEWS_FEEDS.get(category, NEWS_FEEDS["All"])
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as resp:
                text = await resp.text()
        root = ET.fromstring(text)
        items = []
        for it in root.findall('.//item'):
            title_el = it.find('title')
            link_el = it.find('link')
            title = title_el.text if title_el is not None else ''
            link = link_el.text if link_el is not None else '#'
            if title:
                items.append({"title": title, "link": link})
        items = items[:50]
        cache_set(cache_key, items, ttl_seconds=300)  # 5 min
        return {"category": category, "items": items, "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News fetch failed: {e}")

# --- CNN Fear & Greed ---
CNN_JSON_URLS = [
    "https://production-files-cnn.com/markets/fearandgreed/graphdata.json",
    "https://production-files-cnn.com/markets/fearandgreed/greedandfear.json",
]
CNN_PAGE_URLS = [
    "https://edition.cnn.com/markets/fear-and-greed",
    "https://money.cnn.com/data/fear-and-greed/",
]

@api_router.get("/greed-fear")
async def greed_fear():
    cache_key = "greed_fear"
    cached = cache_get(cache_key)
    if cached:
        return {"source": cached.get("source", "cache"), **cached}
    # Try known JSON endpoints first
    try:
        async with aiohttp.ClientSession() as session:
            for u in CNN_JSON_URLS:
                try:
                    async with session.get(u, timeout=20) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            # Normalize
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
                            cache_set(cache_key, result, ttl_seconds=21600)  # 6h
                            return result
                except Exception:
                    continue
    except Exception:
        pass
    # Fallback: scrape page for the current value only
    try:
        async with aiohttp.ClientSession() as session:
            for u in CNN_PAGE_URLS:
                try:
                    async with session.get(u, timeout=20) as resp:
                        html = await resp.text()
                        # naive scrape: look for "Fear & Greed Now" value like data-score or \"value\":
                        import re
                        m = re.search(r"(Fear\s*&\s*Greed|Greed\s*&\s*Fear).*?(\d{1,3})", html, re.IGNORECASE | re.DOTALL)
                        score = int(m.group(2)) if m else None
                        if score is not None:
                            result = {"now": score, "last_updated": datetime.utcnow().isoformat(), "source": "cnn-scrape"}
                            cache_set(cache_key, result, ttl_seconds=21600)
                            return result
                except Exception:
                    continue
        raise HTTPException(status_code=502, detail="Unable to fetch CNN Fear & Greed Index")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Polygon Aggregates ---
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
    # Only for ETFs/stocks; indices may not support
    url = f"{base}/v1/open-close/{quote(ticker, safe=':')}/{date_str}?adjusted=true&apiKey={api_key}"
    async with session.get(url, timeout=30) as resp:
        if resp.status != 200:
            return None
        try:
            data = await resp.json()
        except Exception:
            return None
        return {
            "close": data.get("close"),
            "preMarket": data.get("preMarket"),
            "afterHours": data.get("afterHours"),
        }

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
        # Fetch aggregates concurrently
        async def fetch_one(t: str):
            agg_url = f"{base}/v2/aggs/ticker/{quote(t, safe=':')}/range/{cfg['multiplier']}/{cfg['timespan']}/{start_dt.date()}/{end_dt.date()}?adjusted=true&sort=asc&apiKey={api_key}"
            async with session.get(agg_url, timeout=40) as resp:
                data = await resp.json()
            results = data.get("results") or []
            series = [{"t": r.get("t"), "o": r.get("o"), "h": r.get("h"), "l": r.get("l"), "c": r.get("c"), "v": r.get("v")} for r in results]
            last_close = series[-1]["c"] if series else None
            # prev close and pre/post
            prev_close = await fetch_polygon_prev_close(session, base, t, api_key)
            pre_val = None
            post_val = None
            if not t.startswith("I:"):
                # Try open/close for today (US ET date)
                et_now = datetime.now(NY_TZ)
                date_str = et_now.strftime("%Y-%m-%d")
                oc = await fetch_polygon_open_close(session, base, t, date_str, api_key)
                if oc:
                    pre_val = oc.get("preMarket")
                    post_val = oc.get("afterHours")
            change_pct = None
            if last_close and prev_close:
                try:
                    change_pct = (last_close - prev_close) / prev_close * 100
                except Exception:
                    change_pct = None
            out[t] = {
                "series": series,
                "close": last_close,
                "prev_close": prev_close,
                "pre_market": pre_val,
                "post_market": post_val,
                "change_pct": change_pct,
            }
        await asyncio.gather(*[fetch_one(t) for t in tlist])
    return {"range": range, "last_updated": datetime.utcnow().isoformat(), "data": out}

# --- Existing routes below (truncated for brevity in this file) ---
# NOTE: Keep your previously implemented routes (dashboard, etfs, watchlists, etc.) intact here.

# Register router
app.include_router(api_router)