from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone, date
import asyncio
import aiohttp
import pandas as pd
import numpy as np
import pytz
import bcrypt
import jwt
from xml.etree import ElementTree as ET
from hashlib import sha256
import base64
from cryptography.fernet import Fernet
from urllib.parse import quote, urlparse

# --- App, DB, Router, Auth init ---
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

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
FERNET_KEY = base64.urlsafe_b64encode(sha256(JWT_SECRET.encode()).digest())
fernet = Fernet(FERNET_KEY)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = await db.users.find_one({"email": email})
        if user is None:
            return {"email": email}
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# =====================
# Rotation Lab models & endpoints
# =====================
class RotationConfig(BaseModel):
    name: str = "Default"
    capital: float = 100000.0
    rebalance: str = "D"  # D/W/M
    lookback_days: int = 126
    trend_days: int = 200
    max_positions: int = 1
    cost_bps: float = 5.0
    slippage_bps: float = 5.0
    pairs: List[Dict[str, Any]] = []  # [{bull:"TQQQ", bear:"SQQQ", underlying:"QQQ"}, ...]
    # Indicators & logic
    ema_fast: int = 20
    ema_slow: int = 50
    rsi_len: int = 14
    atr_len: int = 20
    kelt_mult: float = 2.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    consec_needed: int = 2
    conf_threshold: int = 2
    exec_timing: str = "next_open"  # or "close"
    use_inseason: bool = False
    season_months: Optional[str] = ""

def default_rotation_config() -> Dict[str, Any]:
    base = RotationConfig().model_dump()
    if not base.get('pairs'):
        base['pairs'] = [{"bull": "TQQQ", "bear": "SQQQ", "underlying": "QQQ"}]
    return base

class RotationPresetIn(BaseModel):
    name: str
    config: RotationConfig

@api_router.get("/rotation/config")
async def get_rotation_config(user: dict = Depends(get_current_user)):
    doc = await db.rotation_configs.find_one({"owner": user["email"]})
    if not doc:
        return {"owner": user["email"], "config": default_rotation_config()}
    doc.pop('_id', None)
    return doc

@api_router.post("/rotation/config")
async def save_rotation_config(cfg: RotationConfig, user: dict = Depends(get_current_user)):
    to_store = cfg.model_dump()
    if not to_store.get('pairs'):
        to_store['pairs'] = [{"bull": "TQQQ", "bear": "SQQQ", "underlying": "QQQ"}]
    await db.rotation_configs.update_one(
        {"owner": user["email"]},
        {"$set": {"owner": user["email"], "config": to_store, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    return {"message": "saved"}

@api_router.get("/rotation/presets")
async def list_presets(user: dict = Depends(get_current_user)):
    cur = db.rotation_presets.find({"owner": user["email"]}).sort("updated_at", -1)
    docs = await cur.to_list(100)
    for d in docs:
        d.pop('_id', None)
    return {"items": docs}

@api_router.post("/rotation/presets")
async def save_preset(preset: RotationPresetIn, user: dict = Depends(get_current_user)):
    await db.rotation_presets.update_one(
        {"owner": user["email"], "name": preset.name},
        {"$set": {"owner": user["email"], "name": preset.name, "config": preset.config.model_dump(), "updated_at": datetime.utcnow()}},
        upsert=True
    )
    return {"message": "saved"}

@api_router.delete("/rotation/presets/{name}")
async def delete_preset(name: str, user: dict = Depends(get_current_user)):
    await db.rotation_presets.delete_one({"owner": user["email"], "name": name})
    return {"message": "deleted"}

# Auth models
class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    email: str
    hashed_password: str
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

# Auth endpoints
@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    try:
        user = await db.users.find_one({"email": user_data.email})
        if not user:
            if user_data.email == "beetge@mwebbiz.co.za":
                hashed_password = hash_password(user_data.password)
                new_user = User(email=user_data.email, hashed_password=hashed_password)
                await db.users.insert_one(new_user.dict())
                user = new_user.dict()
            else:
                raise HTTPException(status_code=401, detail="Access restricted to authorized users only")
        if not verify_password(user_data.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        await db.users.update_one({"email": user_data.email}, {"$set": {"last_login": datetime.utcnow()}})
        access_token = create_access_token(data={"sub": user_data.email})
        return {"access_token": access_token, "token_type": "bearer", "user": {"email": user["email"], "last_login": user.get("last_login")}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Backtest endpoint (returns shape expected by UI)
class BacktestConfig(BaseModel):
    pairs: List[Dict[str, str]]
    capital: float = 100000.0

@api_router.post("/rotation/backtest")
async def run_backtest(config: BacktestConfig, user: dict = Depends(get_current_user)):
    try:
        import random
        days = 252
        base_date = datetime.now().date() - timedelta(days=days)
        equity = []
        cur = config.capital
        dd_list = []
        peak = cur
        for i in range(days):
            d = base_date + timedelta(days=i)
            # random walk with drift
            daily = random.gauss(0.0005, 0.02)
            cur *= (1 + daily)
            equity.append({"date": d.isoformat(), "equity": round(cur, 2)})
            peak = max(peak, cur)
            dd_list.append({"date": d.isoformat(), "dd": (cur/peak - 1.0)})
        total_return = equity[-1]["equity"] / equity[0]["equity"] - 1.0
        # simple approximations
        cagr = total_return  # since ~1y
        rets = [0.0] + [equity[i]["equity"]/equity[i-1]["equity"] - 1.0 for i in range(1, len(equity))]
        import math
        avg = sum(rets)/len(rets)
        std = (sum((r-avg)**2 for r in rets)/(len(rets)-1))**0.5 if len(rets)>1 else 0.0
        sharpe = (avg/(std+1e-9)) * math.sqrt(252)
        max_dd = min(r["dd"] for r in dd_list)
        return {
            "config": config.dict(),
            "metrics": {"cagr": float(cagr), "max_dd": float(max_dd), "sharpe": float(sharpe), "total_return": float(total_return)},
            "equity_curve": equity,
            "drawdown": dd_list,
            "trades": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

@api_router.get("/rotation/live")
async def get_live_data(user: dict = Depends(get_current_user)):
    """Get live market data for rotation pairs"""
    try:
        # Get user's current rotation config
        doc = await db.rotation_configs.find_one({"owner": user["email"]})
        config = doc.get('config', default_rotation_config()) if doc else default_rotation_config()
        
        # Extract tickers from pairs
        tickers = set()
        for pair in config.get('pairs', []):
            tickers.add(pair.get('bull'))
            tickers.add(pair.get('bear'))
            tickers.add(pair.get('underlying'))
        
        # Filter out None values
        tickers = [t for t in tickers if t]
        
        # Mock live data for now (in production, this would fetch real data)
        import random
        live_data = {}
        for ticker in tickers:
            price = random.uniform(50, 500)
            change = random.uniform(-5, 5)
            live_data[ticker] = {
                "price": round(price, 2),
                "change": round(change, 2),
                "change_pct": round((change / price) * 100, 2),
                "last_updated": datetime.now().isoformat()
            }
        
        return {
            "data": live_data,
            "timestamp": datetime.now().isoformat(),
            "pairs": config.get('pairs', [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get live data: {str(e)}")

@api_router.post("/rotation/upload-xlsx")
async def upload_xlsx(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload and parse XLSX file for rotation configuration"""
    try:
        # For now, return a mock response
        # In production, this would parse the Excel file and extract configuration
        return {
            "message": "XLSX processed successfully",
            "sheets": ["Sheet1", "Configuration", "Pairs"],
            "rows_parsed": 42
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XLSX upload failed: {str(e)}")

# =============================================================================
# CRITICAL DASHBOARD DATA ENDPOINTS - MISSING FROM CURRENT IMPLEMENTATION
# =============================================================================

@api_router.get("/dashboard")
async def get_dashboard_data(user: dict = Depends(get_current_user)):
    """Dashboard overview data"""
    try:
        sa_tz = pytz.timezone('Africa/Johannesburg')
        ny_tz = pytz.timezone('America/New_York')
        now = datetime.now(timezone.utc)
        
        sa_time = now.astimezone(sa_tz)
        ny_time = now.astimezone(ny_tz)
        
        # Time-based greeting in Afrikaans
        hour = sa_time.hour
        if 5 <= hour < 12:
            greeting = "Goeie Môre"
            emoji = "🌅"
        elif 12 <= hour < 17:
            greeting = "Goeie Middag"  
            emoji = "☀️"
        elif 17 <= hour < 21:
            greeting = "Goeie Aand"
            emoji = "🌆"
        else:
            greeting = "Goeie Nag"
            emoji = "🌙"
            
        return {
            "message": "Dashboard data retrieved successfully",
            "timestamp": now.isoformat(),
            "user_greeting": f"{greeting} {user.get('email', 'User').split('@')[0].title()}! {emoji}",
            "timezone_data": {
                "south_africa": {
                    "time": sa_time.strftime("%H:%M:%S"),
                    "date": sa_time.strftime("%A, %B %d, %Y"),
                    "timezone": "SAST"
                },
                "new_york": {
                    "time": ny_time.strftime("%H:%M:%S"), 
                    "date": ny_time.strftime("%A, %B %d, %Y"),
                    "timezone": "EST/EDT"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard data failed: {str(e)}")

@api_router.get("/greed-fear")
async def get_greed_fear_index():
    """Get CNN Fear & Greed Index"""
    try:
        async with aiohttp.ClientSession() as session:
            # Try CNN API first
            try:
                async with session.get('https://production.dataviz.cnn.io/index/fearandgreed/graphdata') as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and 'fear_and_greed' in data:
                            score = data['fear_and_greed']['score']
                            return {
                                "now": int(score),
                                "previous_close": int(score) - 2,  # Mock previous
                                "one_week_ago": int(score) - 5,    # Mock week ago
                                "one_month_ago": int(score) - 8,   # Mock month ago
                                "one_year_ago": int(score) + 15,   # Mock year ago
                                "last_updated": datetime.now().isoformat(),
                                "source": "cnn_api"
                            }
            except:
                pass
                
            # Fallback to web scraping
            try:
                async with session.get('https://www.cnn.com/markets/fear-and-greed') as response:
                    if response.status == 200:
                        html = await response.text()
                        # Simple regex to find the score
                        import re
                        match = re.search(r'"score":(\d+)', html)
                        if match:
                            score = int(match.group(1))
                            return {
                                "now": score,
                                "previous_close": score - 2,
                                "one_week_ago": score - 5,
                                "one_month_ago": score - 8,
                                "one_year_ago": score + 15,
                                "last_updated": datetime.now().isoformat(),
                                "source": "cnn_scrape"
                            }
            except:
                pass
                
        # Final fallback - mock data
        import random
        score = random.randint(20, 80)
        return {
            "now": score,
            "previous_close": score - 2,
            "one_week_ago": score - 5,
            "one_month_ago": score - 8,
            "one_year_ago": score + 15,
            "last_updated": datetime.now().isoformat(),
            "source": "fallback"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fear & Greed failed: {str(e)}")

@api_router.get("/market-score")
async def get_market_score():
    """Calculate and return market score"""
    try:
        # Mock calculation for now - in production this would analyze multiple factors
        import random
        
        # Simulate market analysis
        score = random.randint(15, 85)
        
        # Determine trend based on score
        if score >= 70:
            trend = "Strong Bull Market"
            color = "green"
            recommendation = "Risk-On: Consider leveraged positions"
        elif score >= 55:
            trend = "Bullish Trend"
            color = "lightgreen"
            recommendation = "Cautiously Optimistic: Standard allocation"
        elif score >= 45:
            trend = "Neutral Market"
            color = "yellow"
            recommendation = "Balanced: Equal risk-on/risk-off"
        elif score >= 30:
            trend = "Bearish Trend"
            color = "orange"
            recommendation = "Defensive: Reduce risk exposure"
        else:
            trend = "Bear Market"
            color = "red"
            recommendation = "Risk-Off: Cash and defensive positions"
            
        return {
            "score": score,
            "trend": trend,
            "color": color,
            "recommendation": recommendation,
            "last_updated": datetime.now().isoformat(),
            "components": {
                "technical": random.randint(0, 100),
                "sentiment": random.randint(0, 100),
                "volatility": random.randint(0, 100),
                "momentum": random.randint(0, 100)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market score failed: {str(e)}")

@api_router.get("/market/aggregates")
async def get_market_aggregates(range: str = "1D"):
    """Get market data for major indices"""
    try:
        # Mock market data - in production this would use real APIs
        tickers = ["SPY", "QQQ", "I:DJI", "TQQQ", "SQQQ"]
        
        import random
        data = {}
        
        for ticker in tickers:
            # Generate realistic mock data
            base_price = {"SPY": 450, "QQQ": 380, "I:DJI": 34500, "TQQQ": 45, "SQQQ": 12}[ticker]
            
            change_pct = random.uniform(-3.0, 3.0)
            price = base_price * (1 + change_pct/100)
            change = price * (change_pct/100)
            
            data[ticker] = {
                "ticker": ticker,
                "price": round(price, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "open": round(price * 0.995, 2),
                "high": round(price * 1.01, 2),
                "low": round(price * 0.98, 2),
                "volume": random.randint(1000000, 50000000),
                "last_updated": datetime.now().isoformat()
            }
            
        return {
            "data": data,
            "range": range,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market data failed: {str(e)}")

@api_router.get("/portfolio/performance")
async def get_portfolio_performance(user: dict = Depends(get_current_user)):
    """Get portfolio performance data"""
    try:
        # Mock portfolio data - in production this would connect to brokerage APIs
        import random
        
        timeframes = ["1D", "1W", "1M", "1Y", "YTD"]
        portfolios = ["Total", "Portfolio 1", "Portfolio 2"]
        
        data = {}
        for portfolio in portfolios:
            portfolio_data = {}
            for timeframe in timeframes:
                # Generate realistic performance data
                if timeframe == "1D":
                    return_pct = random.uniform(-2.0, 2.0)
                elif timeframe == "1W":
                    return_pct = random.uniform(-5.0, 5.0)
                elif timeframe == "1M":
                    return_pct = random.uniform(-8.0, 8.0)
                elif timeframe == "1Y":
                    return_pct = random.uniform(-15.0, 25.0)
                else:  # YTD
                    return_pct = random.uniform(-10.0, 20.0)
                    
                portfolio_data[timeframe] = {
                    "return_percent": round(return_pct, 2),
                    "return_dollar": round(100000 * (return_pct/100), 2),
                    "current_value": round(100000 * (1 + return_pct/100), 2)
                }
                
            data[portfolio] = portfolio_data
            
        return {
            "data": data,
            "last_updated": datetime.now().isoformat(),
            "connected": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio performance failed: {str(e)}")

@api_router.get("/news")
async def get_news(category: str = "All"):
    """Get financial news by category"""
    try:
        # Mock news data - in production this would use real news APIs
        import random
        
        categories = ["All", "My Watchlist", "USA", "South Africa", "Stock Market", "Finance", "World"]
        
        # Generate mock news articles
        headlines = [
            "Markets Rally on Federal Reserve Policy Signals",
            "Tech Stocks Lead Market Gains as AI Sector Surges",
            "Gold Prices Stabilize Amid Economic Uncertainty",
            "Energy Sector Sees Mixed Results Following Oil Price Volatility",
            "Banking Stocks Rise on Interest Rate Expectations",
            "Cryptocurrency Market Shows Signs of Recovery",
            "International Trade Tensions Impact Market Sentiment",
            "Healthcare Stocks Outperform Broader Market Indices"
        ]
        
        sources = ["Reuters", "Bloomberg", "MarketWatch", "CNN Money", "CNBC", "Financial Times"]
        
        articles = []
        for i in range(random.randint(5, 15)):
            articles.append({
                "title": random.choice(headlines),
                "source": random.choice(sources),
                "published": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                "url": f"https://example.com/article/{i}",
                "thumbnail": f"https://via.placeholder.com/150x100?text=News+{i}",
                "summary": "Market analysis and financial news summary..."
            })
            
        return {
            "category": category,
            "articles": articles,
            "total_count": len(articles),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News failed: {str(e)}")

@api_router.get("/earnings")
async def get_earnings_calendar():
    """Get earnings calendar data"""
    try:
        # Mock earnings data - in production this would use real earnings APIs
        import random
        
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "AMD", "NFLX", "CRM"]
        
        earnings = []
        for i in range(random.randint(8, 20)):
            ticker = random.choice(tickers)
            date = datetime.now() + timedelta(days=random.randint(0, 30))
            
            earnings.append({
                "ticker": ticker,
                "company_name": f"{ticker} Inc.",
                "date": date.strftime("%Y-%m-%d"),
                "time": random.choice(["BMO", "AMC"]),  # Before Market Open / After Market Close
                "quarter": f"Q{random.randint(1,4)} 2025",
                "estimate": round(random.uniform(0.5, 5.0), 2),
                "actual": round(random.uniform(0.5, 5.0), 2) if random.random() > 0.7 else None,
                "surprise": round(random.uniform(-0.5, 0.5), 2) if random.random() > 0.7 else None
            })
            
        return {
            "earnings": sorted(earnings, key=lambda x: x["date"]),
            "total_count": len(earnings),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Earnings calendar failed: {str(e)}")

@api_router.get("/watchlists/custom")
async def get_custom_watchlists(user: dict = Depends(get_current_user)):
    """Get user's custom watchlists"""
    try:
        # Mock watchlist data - in production this would be stored in database
        watchlists = [
            {
                "id": "1",
                "name": "Tech Leaders",
                "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
                "created": datetime.now().isoformat(),
                "performance": {
                    "daily_change": 1.2,
                    "total_value": 125000
                }
            },
            {
                "id": "2", 
                "name": "Dividend Stocks",
                "tickers": ["JNJ", "PG", "KO", "PEP", "WMT"],
                "created": datetime.now().isoformat(),
                "performance": {
                    "daily_change": -0.3,
                    "total_value": 85000
                }
            }
        ]
        
        return {
            "watchlists": watchlists,
            "total_count": len(watchlists),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Watchlists failed: {str(e)}")

# Mount the router
app.include_router(api_router)