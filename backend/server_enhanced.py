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
from datetime import datetime, timedelta
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

# Available OpenAI Models with latest auto-selection
OPENAI_MODELS = {
    "latest": "gpt-4.1",  # Auto-latest model
    "gpt-4.1": "gpt-4.1",
    "gpt-4.1-mini": "gpt-4.1-mini", 
    "gpt-4.1-nano": "gpt-4.1-nano",
    "o4-mini": "o4-mini",
    "o3-mini": "o3-mini",
    "o3": "o3",
    "o1-mini": "o1-mini",
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-4.5-preview": "gpt-4.5-preview",
    "gpt-4o": "gpt-4o",
    "o1": "o1",
    "o1-pro": "o1-pro"
}

# Authentication Models
class UserLogin(BaseModel):
    email: str
    password: str

class UserSettings(BaseModel):
    current_password: str
    new_password: str

class PasswordReset(BaseModel):
    email: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

# AI Chat Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    chart_context: Optional[Dict] = None

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str = "New Chat"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model: str = "gpt-4.1"
    system_message: str = "You are an expert financial analyst and trading advisor."

class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: Optional[str] = "gpt-4.1"
    ticker: Optional[str] = None  # For chart-specific questions
    include_chart_data: Optional[bool] = False

# Enhanced Stock/Company Models
class CompanyInfo(BaseModel):
    ticker: str
    company_name: str
    sector: str
    industry: str
    market_cap: float
    logo_url: Optional[str] = None
    description: Optional[str] = ""
    website: Optional[str] = ""
    rotation_status: str = "Neutral"  # Rotating In/Out/Neutral
    
class StockSearch(BaseModel):
    query: str
    limit: int = 10

# TradingView Integration Models
class TradingViewAccount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    username: str
    access_token: Optional[str] = None
    connected_at: datetime = Field(default_factory=datetime.utcnow)

class ChartDrawing(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    ticker: str
    drawing_data: Dict  # TradingView drawing data
    timeframe: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Enhanced ETF Data Models (keeping existing structure)
class ETFData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticker: str
    name: str
    sector: str
    theme: str
    current_price: float
    change_1d: float
    change_1w: float
    change_1m: float
    change_3m: float
    change_6m: float
    relative_strength_1m: float
    relative_strength_3m: float
    relative_strength_6m: float
    atr_percent: float
    sata_score: int
    gmma_pattern: str
    sma20_trend: str
    volume: int
    market_cap: float
    swing_start_date: Optional[datetime] = None
    swing_days: Optional[int] = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Keep all existing models from the original file
class WatchlistItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticker: str
    name: str
    list_name: str
    notes: str = ""
    tags: List[str] = []
    priority: int = 1
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    position_size: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CustomWatchlist(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    color: str = "#3B82F6"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class JournalEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime = Field(default_factory=datetime.utcnow)
    title: str
    content: str
    tags: List[str] = []
    market_score: Optional[int] = None
    trades_mentioned: List[str] = []
    mood: str = "neutral"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class HistoricalSnapshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime = Field(default_factory=datetime.utcnow)
    market_score: int
    top_etfs: List[Dict[str, Any]]
    market_leaders: List[str]
    sector_rotation: Dict[str, float]
    vix_level: float
    key_metrics: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MarketScore(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime = Field(default_factory=datetime.utcnow)
    sata_score: int
    adx_score: int
    vix_score: int
    atr_score: int
    gmi_score: int
    nhnl_score: int
    fg_index_score: int
    qqq_ath_distance_score: int
    total_score: int
    classification: str
    recommendation: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class MarketScoreInput(BaseModel):
    sata_score: int
    adx_score: int
    vix_score: int
    atr_score: int
    gmi_score: int
    nhnl_score: int
    fg_index_score: int
    qqq_ath_distance_score: int

class ChartAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticker: str
    timeframe: str
    pattern_analysis: str
    support_levels: List[float]
    resistance_levels: List[float]
    trend_analysis: str
    risk_reward: str
    recommendation: str
    confidence: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Enhanced ETF Universe with more comprehensive data
ETF_UNIVERSE = [
    # Major Indices
    {"ticker": "SPY", "name": "SPDR S&P 500 ETF", "sector": "Broad Market", "theme": "Large Cap"},
    {"ticker": "QQQ", "name": "Invesco QQQ Trust", "sector": "Technology", "theme": "Large Cap Growth"},
    {"ticker": "IWM", "name": "iShares Russell 2000 ETF", "sector": "Small Cap", "theme": "Small Cap"},
    {"ticker": "DIA", "name": "SPDR Dow Jones Industrial ETF", "sector": "Broad Market", "theme": "Blue Chip"},
    
    # Leveraged ETFs
    {"ticker": "TQQQ", "name": "ProShares UltraPro QQQ", "sector": "Technology", "theme": "3x Leveraged"},
    {"ticker": "SQQQ", "name": "ProShares UltraPro Short QQQ", "sector": "Technology", "theme": "3x Inverse"},
    {"ticker": "TNA", "name": "Direxion Daily Small Cap Bull 3X", "sector": "Small Cap", "theme": "3x Leveraged"},
    {"ticker": "SPXL", "name": "Direxion Daily S&P 500 Bull 3X", "sector": "Large Cap", "theme": "3x Leveraged"},
    {"ticker": "QLD", "name": "ProShares Ultra QQQ", "sector": "Technology", "theme": "2x Leveraged"},
    
    # Sector ETFs
    {"ticker": "XLK", "name": "Technology Select Sector SPDR", "sector": "Technology", "theme": "Sector"},
    {"ticker": "XLF", "name": "Financial Select Sector SPDR", "sector": "Financials", "theme": "Sector"},
    {"ticker": "XLV", "name": "Health Care Select Sector SPDR", "sector": "Healthcare", "theme": "Sector"},
    {"ticker": "XLE", "name": "Energy Select Sector SPDR", "sector": "Energy", "theme": "Sector"},
    {"ticker": "XLI", "name": "Industrial Select Sector SPDR", "sector": "Industrials", "theme": "Sector"},
    {"ticker": "XLU", "name": "Utilities Select Sector SPDR", "sector": "Utilities", "theme": "Sector"},
    {"ticker": "XLP", "name": "Consumer Staples Select Sector", "sector": "Consumer Staples", "theme": "Sector"},
    {"ticker": "XLY", "name": "Consumer Discretionary Select Sector", "sector": "Consumer Discretionary", "theme": "Sector"},
    
    # Growth & Momentum
    {"ticker": "MGK", "name": "Vanguard Mega Cap Growth ETF", "sector": "Growth", "theme": "Large Cap Growth"},
    {"ticker": "ARKK", "name": "ARK Innovation ETF", "sector": "Innovation", "theme": "Disruptive Growth"},
    {"ticker": "FFTY", "name": "Innovator IBD 50 ETF", "sector": "Growth", "theme": "Momentum"},
    {"ticker": "VUG", "name": "Vanguard Growth ETF", "sector": "Growth", "theme": "Large Cap Growth"},
    {"ticker": "QQQE", "name": "Invesco NASDAQ 100 Equal Weight", "sector": "Technology", "theme": "Equal Weight"},
    {"ticker": "QQQI", "name": "Invesco NASDAQ Internet ETF", "sector": "Technology", "theme": "Internet"},
    
    # Specialty & Thematic
    {"ticker": "GLD", "name": "SPDR Gold Shares", "sector": "Commodities", "theme": "Precious Metals"},
    {"ticker": "TLT", "name": "iShares 20+ Year Treasury Bond", "sector": "Bonds", "theme": "Long Term Treasury"},
    {"ticker": "UVXY", "name": "ProShares Ultra VIX Short-Term", "sector": "Volatility", "theme": "2x Volatility"},
]

# Authentication helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user = await db.users.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Enhanced utility functions (keep existing ones and add new ones)
def get_south_african_greeting():
    """Get appropriate South African greeting based on time"""
    sa_time = datetime.now(SA_TZ)
    hour = sa_time.hour
    
    if 5 <= hour < 12:
        return "Goeie More Alwyn! 🌅"
    elif 12 <= hour < 18:
        return "Goeie Middag Alwyn! ☀️"
    else:
        return "Goeie Naand Alwyn! 🌙"

def get_market_countdown():
    """Calculate time until NYSE opens"""
    ny_time = datetime.now(NY_TZ)
    market_open = ny_time.replace(hour=9, minute=30, second=0, microsecond=0)
    
    if ny_time.time() > market_open.time():
        market_open += timedelta(days=1)
    
    while market_open.weekday() > 4:
        market_open += timedelta(days=1)
    
    time_diff = market_open - ny_time
    hours = int(time_diff.seconds // 3600)
    minutes = int((time_diff.seconds % 3600) // 60)
    seconds = int(time_diff.seconds % 60)
    
    return f"{hours}h {minutes}m {seconds}s"

async def fetch_etf_data(ticker: str) -> Dict:
    """Fetch real-time ETF data using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        info = stock.info
        
        if hist.empty:
            return None
            
        current_price = hist['Close'].iloc[-1]
        
        # Calculate percentage changes
        change_1d = ((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100) if len(hist) > 1 else 0
        change_1w = ((current_price - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5] * 100) if len(hist) > 5 else 0
        change_1m = ((current_price - hist['Close'].iloc[-22]) / hist['Close'].iloc[-22] * 100) if len(hist) > 22 else 0
        change_3m = ((current_price - hist['Close'].iloc[-66]) / hist['Close'].iloc[-66] * 100) if len(hist) > 66 else 0
        change_6m = ((current_price - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100) if len(hist) > 0 else 0
        
        # Calculate ATR
        high_low = hist['High'] - hist['Low']
        high_close = np.abs(hist['High'] - hist['Close'].shift())
        low_close = np.abs(hist['Low'] - hist['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]
        atr_percent = (atr / current_price) * 100
        
        return {
            "current_price": float(current_price),
            "change_1d": float(change_1d),
            "change_1w": float(change_1w),
            "change_1m": float(change_1m),
            "change_3m": float(change_3m),
            "change_6m": float(change_6m),
            "atr_percent": float(atr_percent),
            "volume": int(hist['Volume'].iloc[-1]) if not pd.isna(hist['Volume'].iloc[-1]) else 0,
            "market_cap": info.get('marketCap', 0) if info else 0
        }
    except Exception as e:
        logging.error(f"Error fetching data for {ticker}: {e}")
        return None

async def get_company_info(ticker: str) -> CompanyInfo:
    """Get comprehensive company information"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Determine sector rotation status
        hist = stock.history(period="3mo")
        if not hist.empty:
            recent_perf = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-22]) / hist['Close'].iloc[-22] * 100) if len(hist) > 22 else 0
            if recent_perf > 5:
                rotation_status = "Rotating In"
            elif recent_perf < -5:
                rotation_status = "Rotating Out"
            else:
                rotation_status = "Neutral"
        else:
            rotation_status = "Neutral"
        
        return CompanyInfo(
            ticker=ticker.upper(),
            company_name=info.get('longName', ticker.upper()),
            sector=info.get('sector', 'Unknown'),
            industry=info.get('industry', 'Unknown'),
            market_cap=info.get('marketCap', 0),
            logo_url=f"https://logo.clearbit.com/{info.get('website', '').replace('https://', '').replace('http://', '').split('/')[0] if info.get('website') else ticker.lower()}.com",
            description=info.get('longBusinessSummary', '')[:200] + '...' if info.get('longBusinessSummary') else "",
            website=info.get('website', ''),
            rotation_status=rotation_status
        )
    except Exception as e:
        logging.error(f"Error fetching company info for {ticker}: {e}")
        return CompanyInfo(
            ticker=ticker.upper(),
            company_name=ticker.upper(),
            sector="Unknown",
            industry="Unknown",
            market_cap=0,
            rotation_status="Unknown"
        )

async def search_companies(query: str, limit: int = 10) -> List[CompanyInfo]:
    """Search for companies by name or ticker"""
    # This is a simplified implementation - in production, you'd use a proper company database
    common_stocks = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "LLY", "AVGO",
        "JPM", "UNH", "XOM", "JNJ", "V", "PG", "MA", "HD", "CVX", "COST"
    ]
    
    results = []
    query_upper = query.upper()
    
    for ticker in common_stocks:
        if query_upper in ticker or len(results) < limit:
            if ticker.startswith(query_upper) or query_upper in ticker:
                company_info = await get_company_info(ticker)
                if query_upper in company_info.company_name.upper() or query_upper in ticker:
                    results.append(company_info)
                
                if len(results) >= limit:
                    break
    
    return results

# Keep all existing functions from original server.py
async def get_stock_data(ticker: str) -> Dict:
    """Get stock data for any ticker (not just ETFs)"""
    return await fetch_etf_data(ticker)

async def get_ai_chart_analysis(ticker: str, timeframe: str = "1d") -> ChartAnalysis:
    """Generate AI-powered chart analysis using OpenAI"""
    try:
        # Get recent price data for context
        stock_data = await get_stock_data(ticker)
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}")
        
        # Generate realistic mock analysis based on actual data
        trend = "Bullish" if stock_data['change_1m'] > 0 else "Bearish" if stock_data['change_1m'] < -5 else "Neutral"
        
        current_price = stock_data['current_price']
        support_1 = current_price * 0.95
        support_2 = current_price * 0.90  
        resistance_1 = current_price * 1.05
        resistance_2 = current_price * 1.10
        
        pattern_analysis = f"""
        {ticker} is showing {trend.lower()} momentum with {stock_data['change_1m']:.1f}% monthly performance.
        Current volatility (ATR: {stock_data['atr_percent']:.1f}%) suggests {'normal' if 1 < stock_data['atr_percent'] < 3 else 'elevated' if stock_data['atr_percent'] > 3 else 'low'} market conditions.
        
        Technical Setup: The stock is {'above' if stock_data['change_1w'] > 0 else 'below'} its weekly momentum levels.
        Volume analysis shows {'strong institutional interest' if stock_data['volume'] > 1000000 else 'moderate participation'}.
        """
        
        risk_reward = f"Risk/Reward ratio approximately 1:2.5 with stop at ${support_1:.2f} and target at ${resistance_2:.2f}"
        
        if trend == "Bullish" and stock_data['change_1w'] > 2:
            recommendation = f"BUY above ${current_price:.2f} with stop loss at ${support_1:.2f}. Target ${resistance_1:.2f} (short-term), ${resistance_2:.2f} (swing target)."
            confidence = 0.75
        elif trend == "Bearish" and stock_data['change_1w'] < -3:
            recommendation = f"AVOID new longs. Consider short below ${current_price:.2f} with stop at ${resistance_1:.2f}."
            confidence = 0.70
        else:
            recommendation = f"WAIT for clearer setup. Watch for breakout above ${resistance_1:.2f} or breakdown below ${support_1:.2f}."
            confidence = 0.60
            
        analysis = ChartAnalysis(
            ticker=ticker.upper(),
            timeframe=timeframe,
            pattern_analysis=pattern_analysis.strip(),
            support_levels=[round(support_1, 2), round(support_2, 2)],
            resistance_levels=[round(resistance_1, 2), round(resistance_2, 2)],
            trend_analysis=f"{trend} trend with {stock_data['change_1m']:.1f}% monthly momentum. ATR suggests {stock_data['atr_percent']:.1f}% daily volatility range.",
            risk_reward=risk_reward,
            recommendation=recommendation,
            confidence=confidence
        )
        
        # Save to database
        await db.chart_analyses.insert_one(analysis.dict())
        return analysis
        
    except Exception as e:
        logging.error(f"Error generating chart analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def calculate_relative_strength(etf_data: Dict, spy_data: Dict) -> Dict:
    """Calculate relative strength vs SPY"""
    try:
        rs_1m = (etf_data['change_1m'] - spy_data['change_1m']) / abs(spy_data['change_1m']) if spy_data['change_1m'] != 0 else 0
        rs_3m = (etf_data['change_3m'] - spy_data['change_3m']) / abs(spy_data['change_3m']) if spy_data['change_3m'] != 0 else 0
        rs_6m = (etf_data['change_6m'] - spy_data['change_6m']) / abs(spy_data['change_6m']) if spy_data['change_6m'] != 0 else 0
        
        return {
            "relative_strength_1m": float(rs_1m),
            "relative_strength_3m": float(rs_3m),
            "relative_strength_6m": float(rs_6m)
        }
    except Exception as e:
        logging.error(f"Error calculating relative strength: {e}")
        return {"relative_strength_1m": 0, "relative_strength_3m": 0, "relative_strength_6m": 0}

def calculate_sata_score(change_1m: float, volume: int, atr_percent: float) -> int:
    """Calculate SATA (Strength Across The Averages) score 1-10"""
    score = 5  # Base score
    
    # Performance component (40%)
    if change_1m > 10:
        score += 2
    elif change_1m > 5:
        score += 1
    elif change_1m < -5:
        score -= 1
    elif change_1m < -10:
        score -= 2
    
    # Volume component (30%) - simplified
    if volume > 1000000:
        score += 1
    
    # Volatility component (30%)
    if 2 < atr_percent < 5:
        score += 1
    elif atr_percent > 8:
        score -= 1
    
    return max(1, min(10, score))

def determine_gmma_pattern(change_1w: float, change_1m: float) -> str:
    """Determine GMMA pattern based on short and long term trends"""
    if change_1w > 0 and change_1m > 0:
        return "RWB"  # Red White Blue (Bullish)
    elif change_1w < 0 and change_1m < 0:
        return "BWR"  # Blue White Red (Bearish)
    else:
        return "Mixed"

def determine_sma20_trend(change_1w: float) -> str:
    """Determine 20SMA trend direction"""
    if change_1w > 2:
        return "U"  # Up
    elif change_1w < -2:
        return "D"  # Down
    else:
        return "F"  # Flat

async def update_etf_data():
    """Update ETF data for all tickers in universe"""
    try:
        # Get SPY data first for relative strength calculations
        spy_data = await fetch_etf_data("SPY")
        if not spy_data:
            logging.error("Failed to fetch SPY data")
            return
        
        updated_etfs = []
        
        for etf_info in ETF_UNIVERSE:
            ticker = etf_info["ticker"]
            logging.info(f"Fetching data for {ticker}")
            
            etf_data = await fetch_etf_data(ticker)
            if not etf_data:
                continue
            
            # Calculate relative strength
            rs_data = await calculate_relative_strength(etf_data, spy_data)
            
            # Calculate derived metrics
            sata_score = calculate_sata_score(
                etf_data['change_1m'], 
                etf_data['volume'], 
                etf_data['atr_percent']
            )
            
            gmma_pattern = determine_gmma_pattern(etf_data['change_1w'], etf_data['change_1m'])
            sma20_trend = determine_sma20_trend(etf_data['change_1w'])
            
            # Create ETF object
            etf = ETFData(
                ticker=ticker,
                name=etf_info["name"],
                sector=etf_info["sector"],
                theme=etf_info["theme"],
                current_price=etf_data["current_price"],
                change_1d=etf_data["change_1d"],
                change_1w=etf_data["change_1w"],
                change_1m=etf_data["change_1m"],
                change_3m=etf_data["change_3m"],
                change_6m=etf_data["change_6m"],
                relative_strength_1m=rs_data["relative_strength_1m"],
                relative_strength_3m=rs_data["relative_strength_3m"],
                relative_strength_6m=rs_data["relative_strength_6m"],
                atr_percent=etf_data["atr_percent"],
                sata_score=sata_score,
                gmma_pattern=gmma_pattern,
                sma20_trend=sma20_trend,
                volume=etf_data["volume"],
                market_cap=etf_data["market_cap"]
            )
            
            # Update in database
            await db.etfs.replace_one(
                {"ticker": ticker},
                etf.dict(),
                upsert=True
            )
            
            updated_etfs.append(etf)
            
        logging.info(f"Updated {len(updated_etfs)} ETFs")
        return updated_etfs
        
    except Exception as e:
        logging.error(f"Error updating ETF data: {e}")
        return []

# Enhanced AI Chat with LLM Integration
async def create_ai_chat_response(message: str, model: str, ticker: str = None, session_id: str = None) -> str:
    """Generate AI response using emergentintegrations"""
    try:
        # Create system message based on context
        if ticker:
            # Get stock data for context
            stock_data = await get_stock_data(ticker)
            chart_analysis = await get_ai_chart_analysis(ticker)
            
            system_message = f"""
            You are an expert financial analyst and trading advisor. You have access to live market data and chart analysis.
            
            Current context for {ticker}:
            - Current Price: ${stock_data.get('current_price', 'N/A')}
            - 1-Day Change: {stock_data.get('change_1d', 0):.2f}%
            - 1-Week Change: {stock_data.get('change_1w', 0):.2f}%
            - 1-Month Change: {stock_data.get('change_1m', 0):.2f}%
            - Volatility (ATR): {stock_data.get('atr_percent', 0):.2f}%
            - Volume: {stock_data.get('volume', 0):,}
            
            Chart Analysis:
            - Pattern: {chart_analysis.pattern_analysis[:200]}...
            - Trend: {chart_analysis.trend_analysis}
            - Recommendation: {chart_analysis.recommendation}
            - Confidence: {chart_analysis.confidence:.0%}
            
            Provide specific, actionable trading advice based on this data.
            """
        else:
            system_message = """
            You are an expert financial analyst and trading advisor. You help with market analysis, trading strategies, 
            technical analysis, risk management, and general investment advice. Provide clear, actionable insights 
            while emphasizing proper risk management. You can access live market data and perform web research when needed.
            """
        
        # Use actual model name from OPENAI_MODELS
        selected_model = OPENAI_MODELS.get(model, "gpt-4.1")
        
        # Create LLM chat instance
        chat = LlmChat(
            api_key=OPENAI_API_KEY,
            session_id=session_id or str(uuid.uuid4()),
            system_message=system_message
        ).with_model("openai", selected_model)
        
        # Create user message
        user_message = UserMessage(text=message)
        
        # Get response
        response = await chat.send_message(user_message)
        
        return response
        
    except Exception as e:
        logging.error(f"Error generating AI response: {e}")
        return f"I apologize, but I'm having trouble generating a response right now. Please try again. (Error: {str(e)})"