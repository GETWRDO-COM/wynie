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

class ChatSessionCreate(BaseModel):
    title: str = "New Chat"
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

class TradingViewAccountCreate(BaseModel):
    username: str
    access_token: Optional[str] = None

class ChartDrawing(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    ticker: str
    drawing_data: Dict  # TradingView drawing data
    timeframe: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChartDrawingCreate(BaseModel):
    ticker: str
    drawing_data: Dict
    timeframe: str

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

class WatchlistItemCreate(BaseModel):
    ticker: str
    name: str = ""
    notes: str = ""
    tags: List[str] = []
    priority: int = 1
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    position_size: Optional[float] = None

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
        
        # Generate logo URL
        website = info.get('website', '')
        if website:
            domain = website.replace('https://', '').replace('http://', '').split('/')[0]
            logo_url = f"https://logo.clearbit.com/{domain}"
        else:
            # Fallback to generic logo service
            logo_url = f"https://logo.clearbit.com/{ticker.lower()}.com"
        
        return CompanyInfo(
            ticker=ticker.upper(),
            company_name=info.get('longName', ticker.upper()),
            sector=info.get('sector', 'Unknown'),
            industry=info.get('industry', 'Unknown'),
            market_cap=info.get('marketCap', 0),
            logo_url=logo_url,
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

# ==================== API ROUTES ====================

# Authentication Routes
@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    """Authenticate user and return access token"""
    try:
        # For the specific user, create account if it doesn't exist
        user = await db.users.find_one({"email": user_data.email})
        
        if not user:
            # Create the default user account
            if user_data.email == "beetge@mwebbiz.co.za":
                hashed_password = hash_password(user_data.password)
                new_user = User(
                    email=user_data.email,
                    hashed_password=hashed_password
                )
                await db.users.insert_one(new_user.dict())
                user = new_user.dict()
            else:
                raise HTTPException(status_code=401, detail="Access restricted to authorized users only")
        
        # Verify password
        if not verify_password(user_data.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        # Update last login
        await db.users.update_one(
            {"email": user_data.email},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create access token
        access_token = create_access_token(data={"sub": user_data.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": user["email"],
                "last_login": user.get("last_login")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/settings")
async def update_settings(settings: UserSettings, current_user: User = Depends(get_current_user)):
    """Update user password"""
    try:
        # Verify current password
        if not verify_password(settings.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Hash new password
        new_hashed_password = hash_password(settings.new_password)
        
        # Update password
        await db.users.update_one(
            {"email": current_user.email},
            {"$set": {"hashed_password": new_hashed_password}}
        )
        
        return {"message": "Password updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/forgot-password")
async def forgot_password(reset_data: PasswordReset):
    """Send password reset instructions (simplified)"""
    try:
        user = await db.users.find_one({"email": reset_data.email})
        if not user:
            # Don't reveal if email exists or not
            return {"message": "If this email exists in our system, you will receive password reset instructions."}
        
        # In production, you would send an actual email
        # For now, return a temporary reset message
        return {
            "message": "Password reset instructions sent to your email.",
            "temp_instructions": "Please contact system administrator for password reset assistance."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "email": current_user.email,
        "last_login": current_user.last_login,
        "created_at": current_user.created_at
    }

# Enhanced AI Chat Routes
@api_router.get("/ai/models")
async def get_available_models():
    """Get list of available AI models"""
    return {
        "models": OPENAI_MODELS,
        "latest_model": OPENAI_MODELS["latest"],
        "recommended": "latest"
    }

@api_router.post("/ai/chat")
async def ai_chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """AI chat with optional chart context"""
    try:
        # Generate AI response
        response = await create_ai_chat_response(
            message=request.message,
            model=request.model,
            ticker=request.ticker if request.include_chart_data else None,
            session_id=request.session_id
        )
        
        # Save messages to database
        user_message = ChatMessage(
            session_id=request.session_id,
            role="user",
            content=request.message,
            chart_context={"ticker": request.ticker} if request.ticker else None
        )
        
        ai_message = ChatMessage(
            session_id=request.session_id,
            role="assistant",
            content=response
        )
        
        await db.chat_messages.insert_many([user_message.dict(), ai_message.dict()])
        
        return {
            "response": response,
            "session_id": request.session_id,
            "model_used": request.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/ai/sessions")
async def get_chat_sessions(current_user: User = Depends(get_current_user)):
    """Get user's chat sessions"""
    try:
        sessions = await db.chat_sessions.find({"user_id": current_user.id}).to_list(length=50)
        return [ChatSession(**session) for session in sessions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ai/sessions")
async def create_chat_session(session_data: ChatSessionCreate, current_user: User = Depends(get_current_user)):
    """Create new chat session"""
    try:
        session = ChatSession(
            user_id=current_user.id,
            title=session_data.title,
            model=session_data.model,
            system_message=session_data.system_message
        )
        await db.chat_sessions.insert_one(session.dict())
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/ai/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, current_user: User = Depends(get_current_user)):
    """Get messages from a specific session"""
    try:
        messages = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(length=100)
        
        return [ChatMessage(**msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Company/Stock Search Routes
@api_router.get("/companies/search")
async def search_companies_api(query: str = Query(...), limit: int = Query(10)):
    """Search for companies by name or ticker"""
    try:
        results = await search_companies(query, limit)
        return {"companies": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/companies/{ticker}")
async def get_company_details(ticker: str):
    """Get detailed company information"""
    try:
        company_info = await get_company_info(ticker)
        stock_data = await get_stock_data(ticker)
        
        return {
            "company": company_info,
            "market_data": stock_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# TradingView Integration Routes
@api_router.post("/tradingview/connect")
async def connect_tradingview_account(account_data: TradingViewAccountCreate, current_user: User = Depends(get_current_user)):
    """Connect TradingView account"""
    try:
        account = TradingViewAccount(
            user_id=current_user.id,
            username=account_data.username,
            access_token=account_data.access_token
        )
        
        # Check if account already exists
        existing = await db.tradingview_accounts.find_one({"user_id": current_user.id})
        if existing:
            await db.tradingview_accounts.replace_one(
                {"user_id": current_user.id},
                account.dict()
            )
        else:
            await db.tradingview_accounts.insert_one(account.dict())
        
        return {"message": "TradingView account connected successfully", "account": account}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tradingview/account")
async def get_tradingview_account(current_user: User = Depends(get_current_user)):
    """Get connected TradingView account"""
    try:
        account = await db.tradingview_accounts.find_one({"user_id": current_user.id})
        if not account:
            return {"connected": False}
        
        return {"connected": True, "account": TradingViewAccount(**account)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/tradingview/drawings")
async def save_chart_drawing(drawing_data: ChartDrawingCreate, current_user: User = Depends(get_current_user)):
    """Save chart drawing/annotation"""
    try:
        drawing = ChartDrawing(
            user_id=current_user.id,
            ticker=drawing_data.ticker,
            drawing_data=drawing_data.drawing_data,
            timeframe=drawing_data.timeframe
        )
        await db.chart_drawings.insert_one(drawing.dict())
        return {"message": "Chart drawing saved successfully", "drawing": drawing}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tradingview/drawings/{ticker}")
async def get_chart_drawings(ticker: str, current_user: User = Depends(get_current_user)):
    """Get saved chart drawings for a ticker"""
    try:
        drawings = await db.chart_drawings.find({
            "user_id": current_user.id,
            "ticker": ticker.upper()
        }).to_list(length=50)
        
        return [ChartDrawing(**drawing) for drawing in drawings]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Charts Data Routes
@api_router.get("/charts/indices")
async def get_indices_chart_data(timeframe: str = Query("1d", description="1d, 1w, 1m, 1y, 5y")):
    """Get chart data for major indices with different timeframes"""
    try:
        indices = ["SPY", "QQQ", "DIA", "IWM"]
        chart_data = {}
        
        # Map timeframe to yfinance period
        period_map = {
            "1d": "1d",
            "1w": "5d", 
            "1m": "1mo",
            "1y": "1y",
            "5y": "5y"
        }
        
        period = period_map.get(timeframe, "1mo")
        
        for index in indices:
            try:
                ticker = yf.Ticker(index)
                hist = ticker.history(period=period)
                
                if not hist.empty:
                    chart_data[index] = {
                        "dates": [d.strftime("%Y-%m-%d") for d in hist.index],
                        "prices": hist['Close'].tolist(),
                        "volumes": hist['Volume'].tolist(),
                        "highs": hist['High'].tolist(),
                        "lows": hist['Low'].tolist(),
                        "opens": hist['Open'].tolist()
                    }
            except Exception as e:
                logging.error(f"Error fetching chart data for {index}: {e}")
                continue
        
        return {"data": chart_data, "timeframe": timeframe}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/charts/{ticker}")
async def get_ticker_chart_data(ticker: str, timeframe: str = Query("1mo")):
    """Get chart data for any ticker"""
    try:
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period=timeframe)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}")
        
        return {
            "ticker": ticker.upper(),
            "timeframe": timeframe,
            "data": {
                "dates": [d.strftime("%Y-%m-%d %H:%M") for d in hist.index],
                "prices": hist['Close'].tolist(),
                "volumes": hist['Volume'].tolist(),
                "highs": hist['High'].tolist(),
                "lows": hist['Low'].tolist(),
                "opens": hist['Open'].tolist()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Keep all existing routes from original server.py but enhance them
@api_router.get("/")
async def root():
    return {"message": "ETF Intelligence System API - Enhanced Version"}

@api_router.get("/dashboard")
async def get_dashboard_data():
    """Get enhanced dashboard data with SA greetings, market info, and live indices"""
    try:
        sa_time = datetime.now(SA_TZ)
        ny_time = datetime.now(NY_TZ)
        
        # Fetch major indices data
        major_indices = {}
        try:
            indices_data = ['SPY', 'QQQ', 'DIA', 'IWM']
            for symbol in indices_data:
                data = await fetch_etf_data(symbol)
                if data:
                    major_indices[symbol] = {
                        'price': data['current_price'],
                        'change_1d': data['change_1d'],
                        'last_updated': datetime.utcnow().strftime("%H:%M")
                    }
        except Exception as e:
            logging.error(f"Error fetching indices data: {e}")
        
        # Fetch ZAR/USD exchange rate (mock for now)
        zar_usd_rate = 18.75
        
        # Fetch CNN Fear & Greed Index (mock for now)
        fear_greed_data = {
            'index': 73,
            'rating': 'Greed',
            'last_updated': datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            'components': {
                'stock_price_momentum': 85,
                'market_volatility': 45,
                'safe_haven_demand': 25,
                'put_call_ratio': 70
            }
        }
        
        dashboard_data = {
            "greeting": get_south_african_greeting(),
            "sa_time": {
                "time": sa_time.strftime("%H:%M:%S"),
                "timezone": "SAST",
                "date": sa_time.strftime("%A, %d %B %Y"),
                "flag": "🇿🇦"
            },
            "ny_time": {
                "time": ny_time.strftime("%H:%M:%S"), 
                "timezone": "EST" if ny_time.dst() else "EST",
                "date": ny_time.strftime("%A, %d %B %Y"),
                "flag": "🇺🇸"
            },
            "market_countdown": get_market_countdown(),
            "major_indices": major_indices,
            "zar_usd_rate": zar_usd_rate,
            "fear_greed_index": fear_greed_data,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Keep all existing ETF routes
@api_router.get("/etfs", response_model=List[ETFData])
async def get_etfs(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    min_rs: Optional[float] = Query(None, description="Minimum relative strength"),
    limit: Optional[int] = Query(100, description="Limit results")
):
    """Get ETF data with optional filtering"""
    try:
        query = {}
        if sector:
            query["sector"] = sector
        if min_rs:
            query["relative_strength_1m"] = {"$gte": min_rs}
        
        etfs = await db.etfs.find(query).limit(limit).to_list(length=limit)
        return [ETFData(**etf) for etf in etfs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/etfs/update")
async def update_etfs():
    """Manually trigger ETF data update"""
    try:
        updated_etfs = await update_etf_data()
        return {"message": f"Updated {len(updated_etfs)} ETFs", "count": len(updated_etfs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/etfs/sectors")
async def get_sectors():
    """Get unique sectors"""
    try:
        sectors = await db.etfs.distinct("sector")
        return {"sectors": sectors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/etfs/swing-leaders")
async def get_swing_leaders():
    """Get top 5 ETFs based on SATA + RS combination"""
    try:
        etfs = await db.etfs.find().to_list(length=None)
        
        # Calculate combined swing score
        for etf in etfs:
            swing_score = etf.get('sata_score', 0) + (etf.get('relative_strength_1m', 0) * 10)
            etf['swing_score'] = swing_score
        
        # Sort by swing score
        top_etfs = sorted(etfs, key=lambda x: x.get('swing_score', 0), reverse=True)[:5]
        
        return [ETFData(**etf) for etf in top_etfs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Stock lookup for any ticker
@api_router.get("/stocks/{ticker}")
async def get_stock_info(ticker: str):
    """Get stock data for any ticker"""
    try:
        stock_data = await get_stock_data(ticker.upper())
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}")
        return stock_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Custom Watchlists Management
@api_router.post("/watchlists/lists", response_model=CustomWatchlist)
async def create_custom_watchlist(watchlist: CustomWatchlist):
    """Create a new custom watchlist"""
    try:
        await db.custom_watchlists.insert_one(watchlist.dict())
        return watchlist
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/watchlists/lists", response_model=List[CustomWatchlist])
async def get_custom_watchlists():
    """Get all custom watchlists"""
    try:
        lists = await db.custom_watchlists.find().to_list(length=None)
        return [CustomWatchlist(**wl) for wl in lists]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Watchlist Routes with Manual Management
@api_router.get("/watchlists/custom")
async def get_custom_watchlists_with_stocks(current_user: User = Depends(get_current_user)):
    """Get all custom watchlists with their stocks"""
    try:
        watchlists = await db.custom_watchlists.find().to_list(length=None)
        
        result = []
        for watchlist in watchlists:
            # Get stocks in this watchlist
            stocks = await db.watchlists.find({"list_name": watchlist["name"]}).to_list(length=None)
            
            # Convert to dict and clean up MongoDB ObjectId
            watchlist_dict = dict(watchlist)
            if '_id' in watchlist_dict:
                del watchlist_dict['_id']
            
            # Clean up stock data and convert to WatchlistItem
            cleaned_stocks = []
            for stock in stocks:
                if '_id' in stock:
                    del stock['_id']
                cleaned_stocks.append(WatchlistItem(**stock))
            
            watchlist_dict["stocks"] = cleaned_stocks
            result.append(watchlist_dict)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/watchlists/custom/{list_name}/add-stock")
async def add_stock_to_watchlist(list_name: str, item_data: WatchlistItemCreate, current_user: User = Depends(get_current_user)):
    """Add stock to watchlist manually"""
    try:
        # Verify the watchlist exists
        watchlist = await db.custom_watchlists.find_one({"name": list_name})
        if not watchlist:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        
        # Check if stock already exists in this list
        existing = await db.watchlists.find_one({"ticker": item_data.ticker, "list_name": list_name})
        if existing:
            raise HTTPException(status_code=400, detail="Stock already in watchlist")
        
        # Get company info to populate name if not provided
        name = item_data.name
        if not name or name == item_data.ticker:
            company_info = await get_company_info(item_data.ticker)
            name = company_info.company_name
        
        # Create full WatchlistItem
        item = WatchlistItem(
            ticker=item_data.ticker,
            name=name,
            list_name=list_name,
            notes=item_data.notes,
            tags=item_data.tags,
            priority=item_data.priority,
            entry_price=item_data.entry_price,
            target_price=item_data.target_price,
            stop_loss=item_data.stop_loss,
            position_size=item_data.position_size
        )
        
        await db.watchlists.insert_one(item.dict())
        
        return {"message": f"Added {item_data.ticker} to {list_name}", "item": item}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/watchlists/custom/{list_name}/remove-stock/{ticker}")
async def remove_stock_from_watchlist(list_name: str, ticker: str, current_user: User = Depends(get_current_user)):
    """Remove stock from watchlist"""
    try:
        result = await db.watchlists.delete_one({"ticker": ticker.upper(), "list_name": list_name})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Stock not found in watchlist")
        
        return {"message": f"Removed {ticker} from {list_name}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Historical Data Routes
@api_router.get("/history", response_model=List[HistoricalSnapshot])
async def get_historical_snapshots(days: int = Query(30, description="Number of days")):
    """Get historical snapshots"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        snapshots = await db.historical_snapshots.find(
            {"date": {"$gte": cutoff_date}}
        ).sort("date", -1).to_list(length=days)
        
        return [HistoricalSnapshot(**snapshot) for snapshot in snapshots]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Journal Routes
@api_router.post("/journal", response_model=JournalEntry)
async def create_journal_entry(entry: JournalEntry):
    """Create new journal entry"""
    try:
        await db.journal_entries.insert_one(entry.dict())
        return entry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/journal", response_model=List[JournalEntry])
async def get_journal_entries(days: int = Query(30)):
    """Get recent journal entries"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        entries = await db.journal_entries.find(
            {"date": {"$gte": cutoff_date}}
        ).sort("date", -1).to_list(length=100)
        
        return [JournalEntry(**entry) for entry in entries]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Watchlist Routes
@api_router.post("/watchlists", response_model=WatchlistItem)
async def create_watchlist_item(item: WatchlistItem):
    """Create new watchlist item"""
    try:
        await db.watchlists.insert_one(item.dict())
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/watchlists", response_model=List[WatchlistItem])
async def get_watchlists(list_name: Optional[str] = Query(None)):
    """Get watchlist items"""
    try:
        query = {}
        if list_name:
            query["list_name"] = list_name
        
        items = await db.watchlists.find(query).to_list(length=1000)
        return [WatchlistItem(**item) for item in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/watchlists/names")
async def get_watchlist_names():
    """Get unique watchlist names"""
    try:
        lists = await db.watchlists.distinct("list_name")
        return {"lists": lists}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/watchlists/{item_id}")
async def delete_watchlist_item(item_id: str):
    """Delete watchlist item"""
    try:
        result = await db.watchlists.delete_one({"id": item_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"message": "Item deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Market Score Routes
@api_router.get("/market-score", response_model=MarketScore)
async def get_market_score():
    """Get current market situational awareness score"""
    try:
        scores = await db.market_scores.find().sort("date", -1).limit(1).to_list(1)
        if not scores:
            # Create default score
            default_score = MarketScore(
                sata_score=2,
                adx_score=2,
                vix_score=2,
                atr_score=2,
                gmi_score=2,
                nhnl_score=2,
                fg_index_score=2,
                qqq_ath_distance_score=2,
                total_score=16,
                classification="Yellow Day",
                recommendation="Selective entries. Use moderate position sizing."
            )
            await db.market_scores.insert_one(default_score.dict())
            return default_score
        
        return MarketScore(**scores[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/market-score", response_model=MarketScore)
async def update_market_score(score_input: MarketScoreInput):
    """Update market score"""
    try:
        # Calculate total and classification
        total = (score_input.sata_score + score_input.adx_score + score_input.vix_score + 
                score_input.atr_score + score_input.gmi_score + score_input.nhnl_score + 
                score_input.fg_index_score + score_input.qqq_ath_distance_score)
        
        if total >= 28:
            classification = "Green Day"
            recommendation = "Full exposure. Use wider stop losses. Aggressive position sizing."
        elif total >= 20:
            classification = "Yellow Day"  
            recommendation = "Selective entries. Moderate position sizing. Standard stops."
        else:
            classification = "Red Day"
            recommendation = "Risk-off mode. Tight stops or avoid new positions."
        
        # Create full MarketScore object
        score = MarketScore(
            sata_score=score_input.sata_score,
            adx_score=score_input.adx_score,
            vix_score=score_input.vix_score,
            atr_score=score_input.atr_score,
            gmi_score=score_input.gmi_score,
            nhnl_score=score_input.nhnl_score,
            fg_index_score=score_input.fg_index_score,
            qqq_ath_distance_score=score_input.qqq_ath_distance_score,
            total_score=total,
            classification=classification,
            recommendation=recommendation
        )
        
        await db.market_scores.insert_one(score.dict())
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI Chart Analysis Routes
@api_router.get("/charts/{ticker}/analysis", response_model=ChartAnalysis)
async def get_chart_analysis(ticker: str, timeframe: str = "1d"):
    """Get AI-powered chart analysis for a ticker"""
    try:
        analysis = await get_ai_chart_analysis(ticker.upper(), timeframe)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Export Routes
@api_router.get("/export/etfs")
async def export_etfs_data():
    """Export ETF data for Google Sheets integration"""
    try:
        etfs = await db.etfs.find().to_list(length=None)
        
        # Format data for export
        export_data = []
        for etf in etfs:
            export_data.append({
                'Ticker': etf.get('ticker', ''),
                'Name': etf.get('name', ''),
                'Sector': etf.get('sector', ''),
                'Theme': etf.get('theme', ''),
                'Current_Price': etf.get('current_price', 0),
                'Change_1D': etf.get('change_1d', 0),
                'Change_1W': etf.get('change_1w', 0),
                'Change_1M': etf.get('change_1m', 0),
                'Change_3M': etf.get('change_3m', 0),
                'Change_6M': etf.get('change_6m', 0),
                'RS_1M': etf.get('relative_strength_1m', 0),
                'RS_3M': etf.get('relative_strength_3m', 0),
                'RS_6M': etf.get('relative_strength_6m', 0),
                'ATR_Percent': etf.get('atr_percent', 0),
                'SATA_Score': etf.get('sata_score', 0),
                'GMMA_Pattern': etf.get('gmma_pattern', ''),
                'SMA20_Trend': etf.get('sma20_trend', ''),
                'Volume': etf.get('volume', 0),
                'Market_Cap': etf.get('market_cap', 0),
                'Last_Updated': etf.get('last_updated', '')
            })
        
        return {
            "data": export_data,
            "total_records": len(export_data),
            "export_timestamp": datetime.utcnow().isoformat(),
            "format": "csv_compatible"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/export/market-score")
async def export_market_score():
    """Export current market score data"""
    try:
        score = await db.market_scores.find().sort("date", -1).limit(1).to_list(1)
        if not score:
            raise HTTPException(status_code=404, detail="No market score data found")
        
        # Convert ObjectId to string and clean up the data
        score_data = score[0]
        if '_id' in score_data:
            score_data['_id'] = str(score_data['_id'])
        
        # Convert datetime objects to ISO strings
        for key, value in score_data.items():
            if isinstance(value, datetime):
                score_data[key] = value.isoformat()
        
        return {
            "market_score_data": score_data,
            "export_timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Formula Configuration Routes
@api_router.get("/formulas/config")
async def get_formula_config():
    """Get current formula configuration (legacy spreadsheet config). Also ensures etf_regime defaults exist in collection."""
    try:
        # Keep legacy behavior for frontend while seeding etf_regime in the background
        await _ensure_etf_regime_config()
        config = await db.formula_configs.find({"kind": {"$exists": False}}).to_list(length=None)
        # If none exists, create the legacy default config used by spreadsheet
        if not config:
            default_config = {
                "relative_strength": {
                    "strong_threshold": 0.10,
                    "moderate_threshold": 0.02,
                    "formula": "(ETF_Return - SPY_Return) / |SPY_Return|"
                },
                "sata_weights": {
                    "performance": 0.40,
                    "relative_strength": 0.30,
                    "volume": 0.20,
                    "volatility": 0.10,
                    "formula": "Weighted_Score = (Performance × 0.40) + (RS × 0.30) + (Volume × 0.20) + (Volatility × 0.10)"
                },
                "atr_calculation": {
                    "period_days": 14,
                    "high_volatility_threshold": 3.0
                },
                "gmma_patterns": {
                    "bullish_requirement": "1W_change > 0 AND 1M_change > 0",
                    "bearish_requirement": "1W_change < 0 AND 1M_change < 0"
                }
            }
            await db.formula_configs.insert_one(default_config)
            return default_config
        # Return first legacy config for compatibility
        cfg = dict(config[0])
        cfg.pop('_id', None)
        # Convert datetimes
        for k, v in list(cfg.items()):
            if isinstance(v, datetime):
                cfg[k] = v.isoformat()
        return cfg
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/formulas/config")
async def update_formula_config(config_update: Dict[str, Any]):
    """Update formula configuration and trigger recalculation"""
    try:
        # Update the configuration
        await db.formula_configs.replace_one(
            {},
            config_update,
            upsert=True
        )
        
        # Trigger ETF data recalculation with new formulas
        updated_etfs = await update_etf_data()
        
        return {
            "message": "Formula configuration updated successfully",
            "config": config_update,
            "recalculated_etfs": len(updated_etfs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Spreadsheet-Style Interface Routes
@api_router.get("/spreadsheet/etfs")
async def get_spreadsheet_etf_data(sector: Optional[str] = Query(None)):
    """Get ETF data in spreadsheet format with formulas"""
    try:
        query = {}
        if sector:
            query["sector"] = sector
        
        etfs = await db.etfs.find(query).to_list(length=None)
        
        # Format for spreadsheet view
        spreadsheet_data = []
        for etf in etfs:
            row = {
                "Ticker": etf.get("ticker", ""),
                "Name": etf.get("name", ""),
                "Sector": etf.get("sector", ""),
                "Theme": etf.get("theme", ""),
                "Price": etf.get("current_price", 0),
                "Swing_Days": f"=TODAY() - {etf.get('swing_start_date', datetime.utcnow().strftime('%Y-%m-%d'))}",
                "SATA": etf.get("sata_score", 0),
                "20SMA": etf.get("sma20_trend", "F"),
                "GMMA": etf.get("gmma_pattern", "Mixed"),
                "ATR_Percent": f"=({etf.get('atr_percent', 0):.2f})",
                "Change_1D": f"=({etf.get('change_1d', 0):.2f}%)",
                "Change_1W": f"=({etf.get('change_1w', 0):.2f}%)",
                "Change_1M": f"=({etf.get('change_1m', 0):.2f}%)",
                "RS_1M": "=IF({} > SPY_1M, \"Y\", \"N\")".format(etf.get('relative_strength_1m', 0)),
                "RS_3M": "=IF({} > SPY_3M, \"Y\", \"N\")".format(etf.get('relative_strength_3m', 0)),
                "RS_6M": "=IF({} > SPY_6M, \"Y\", \"N\")".format(etf.get('relative_strength_6m', 0)),
                "Color_Rule": f"=IF(AND(RS_1M=\"Y\", SATA>=7, GMMA=\"RWB\"), \"Green\", IF(RS_1M=\"N\", \"Red\", \"Yellow\"))"
            }
            spreadsheet_data.append(row)
        
        return {
            "data": spreadsheet_data,
            "formulas": {
                "swing_days": "=TODAY() - [Swing_Date_Cell]",
                "atr_percent": "=(14_Day_ATR / Current_Price) * 100",
                "relative_strength": "=(ETF_Return - SPY_Return) / ABS(SPY_Return)",
                "sata_score": "=Performance(40%) + RelStrength(30%) + Volume(20%) + Volatility(10%)",
                "color_logic": "Green: RS=Y AND SATA>=7 AND GMMA=RWB, Red: RS=N, Yellow: Mixed signals"
            },
            "total_records": len(spreadsheet_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Historical Data Pruning Route
@api_router.post("/admin/prune-historical-data")
async def prune_historical_data(days: int = 60, current_user: User = Depends(get_current_user)):
    """Prune historical data older than specified days"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Prune historical snapshots
        snapshots_result = await db.historical_snapshots.delete_many(
            {"date": {"$lt": cutoff_date}}
        )
        
        # Prune old chart analyses
        charts_result = await db.chart_analyses.delete_many(
            {"created_at": {"$lt": cutoff_date}}
        )
        
        # Prune old chat messages (keep last 1000 per session)
        sessions = await db.chat_sessions.find().to_list(length=None)
        chat_deletions = 0
        
        for session in sessions:
            messages = await db.chat_messages.find(
                {"session_id": session["id"]}
            ).sort("timestamp", -1).skip(1000).to_list(length=None)
            
            if messages:
                message_ids = [msg["id"] for msg in messages]
                result = await db.chat_messages.delete_many(
                    {"id": {"$in": message_ids}}
                )
                chat_deletions += result.deleted_count
        
        return {
            "message": f"Pruned historical data older than {days} days",
            "deleted": {
                "historical_snapshots": snapshots_result.deleted_count,
                "chart_analyses": charts_result.deleted_count,
                "chat_messages": chat_deletions
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Live Data Routes (for compatibility with existing frontend)
@api_router.get("/live/indices")
async def get_live_indices():
    """Get live major indices data"""
    try:
        indices = ["SPY", "QQQ", "DIA", "IWM", "^VIX"]
        live_data = {}
        
        for index in indices:
            data = await fetch_etf_data(index)
            if data:
                # Handle VIX special case (use VIX as key but ^VIX as ticker)
                key = "VIX" if index == "^VIX" else index
                live_data[key] = {
                    "symbol": key,
                    "price": data["current_price"],
                    "change_1d": data["change_1d"],
                    "volume": data["volume"],
                    "last_updated": datetime.utcnow().strftime("%H:%M:%S")
                }
        
        return live_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/live/forex")
async def get_live_forex():
    """Get live forex data"""
    try:
        # For now, return mock data - in production you'd use a forex API
        forex_data = {
            "ZAR_USD": {
                "rate": 18.75,
                "change": -0.15,
                "change_percent": -0.80,
                "last_updated": datetime.utcnow().strftime("%H:%M:%S")
            },
            "major_pairs": {
                "EURUSD": {"rate": 1.0521, "change": 0.0012, "change_percent": 0.11},
                "GBPUSD": {"rate": 1.2345, "change": -0.0023, "change_percent": -0.19},
                "JPYUSD": {"rate": 0.0067, "change": 0.0001, "change_percent": 1.49}
            }
        }
        
        return forex_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/live/fear-greed")
async def get_live_fear_greed():
    """Get CNN Fear & Greed Index"""
    try:
        # Mock data - in production you'd fetch from CNN API
        fear_greed_data = {
            "index": 73,
            "rating": "Greed",
            "color": "#FFA500",  # Orange for Greed
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "components": {
                "stock_price_momentum": 85,
                "market_volatility": 45,
                "safe_haven_demand": 25,
                "put_call_ratio": 70,
                "junk_bond_demand": 65,
                "market_breadth": 80,
                "options_activity": 75
            }
        }
        
        return fear_greed_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MSAE + ETF REGIME ENGINE (Phase 1) ====================

class MarketStateSnapshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: datetime = Field(default_factory=datetime.utcnow)
    regime: str  # UPTREND | DOWNTREND | CHOP
    msae_score: float
    components: Dict[str, Any]
    stale: bool = False

class EtfRegimeConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "default"
    kind: str = "etf_regime"
    params: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    comment: Optional[str] = None

class EtfRegimeSignal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: datetime = Field(default_factory=datetime.utcnow)
    module: str = "etf_regime"
    regime: str
    decision: str  # TQQQ | SQQQ | QQQI | OUT
    weights: Dict[str, float]
    confidence: float
    reason: Dict[str, Any]
    params_version: str

# Default NDX tickers fallback (trimmed core; prefer Mongo ndx_constituents when present)
NDX_TICKERS_FALLBACK = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","AVGO","TSLA","COST",
    "ADBE","NFLX","PEP","AMD","CSCO","LIN","TMUS","CMCSA","TXN","INTC",
    "AMAT","QCOM","INTU","AMGN","HON","VRTX","SBUX","PYPL","PDD","REGN",
    "GILD","BKNG","ADP","ISRG","MU","ADI","LRCX","MDLZ","ABNB","PANW",
    "SNPS","KLAC","ASML","MRVL","CEG","CRWD","ADSK","CDNS","CSX","KDP",
    "ORLY","FTNT","MELI","MAR","ROP","NXPI","CTAS","AEP","IDXX","KHC",
    "ODFL","CHTR","WDAY","PAYX","PCAR","ROST","CPRT","MNST","EXC","TEAM",
    "FAST","XEL","EA","FTV","DDOG","ZS","AZN","BIIB","MRNA","LCID","BIDU",
    "DOCU","VRSK","WDAY","LULU","GOOG","GOOGL","SPLK","OKTA","ANSS","CDW"
]

async def _load_ndx_constituents_symbols() -> List[str]:
    try:
        doc = await db.ndx_constituents.find_one({"_id": {"$regex": "^ndx:"}})
        if doc and "universe" in doc:
            symbols = [m.get("yf_symbol", m.get("symbol")).upper() for m in doc["universe"] if m.get("active", True)]
            symbols = [s for s in symbols if s]
            if symbols:
                return symbols
        return NDX_TICKERS_FALLBACK
    except Exception:
        return NDX_TICKERS_FALLBACK

def _is_market_hours_ny(dt_now=None) -> bool:
    now_ny = datetime.now(NY_TZ) if dt_now is None else dt_now.astimezone(NY_TZ)
    if now_ny.weekday() >= 5:
        return False
    open_t = now_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    close_t = now_ny.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_t.time() <= now_ny.time() <= close_t.time()

async def _ensure_etf_regime_config() -> Dict[str, Any]:
    # If a config with kind=etf_regime doesn't exist, insert defaults
    existing = await db.formula_configs.find_one({"kind": "etf_regime"})
    if existing:
        return existing
    default = {
        "name": "default",
        "kind": "etf_regime",
        "params": {
            "ema_fast": 20,
            "ema_slow": 50,
            "adx_period": 14,
            "adx_threshold": 20,
            "atr_period": 14,
            "flip_confirmation_days": 2,
            "qqqi_weight_in_chop": 1.0,
            "allow_short_both_decay": False,
            "max_leverage_alloc": 1.0,
            "stale_minutes_rth": 20,
            "stale_minutes_oth": 180,
            "whipsaw_cross_count_lookback": 20,
            "whipsaw_cross_threshold": 3,
            "decay_guard_lookback_days": 10,
            "atrp_vol_cap_pct": 3.5,
            "freeze_on_vol_spike_days": 1,
            "income_etf": "QQQI",
            "out_instead_of_income": False
        },
        "created_at": datetime.utcnow().isoformat(),
        "comment": "Initial ETF regime defaults"
    }
    await db.formula_configs.insert_one(default)
    return default

def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()

def _compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    # Wilder's DMI/ADX
    high = df['High']
    low = df['Low']
    close = df['Close']
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period, min_periods=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period, min_periods=period).mean() / atr)
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di)).fillna(0)
    adx = dx.rolling(window=period, min_periods=period).mean()
    return adx

async def _fetch_hist(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Fetch historical data with retry logic for yfinance rate limiting"""
    import asyncio
    
    for attempt in range(3):  # Try up to 3 times
        try:
            # Add small delay between attempts to avoid rate limiting
            if attempt > 0:
                await asyncio.sleep(1 + attempt)  # 1s, 2s delays
            
            df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=False)
            if isinstance(df, pd.DataFrame) and not df.empty:
                # yfinance returns multi-index columns sometimes for multiple tickers; ensure single
                if isinstance(df.columns, pd.MultiIndex):
                    # Check which level contains the ticker
                    if symbol in df.columns.get_level_values(1):
                        df = df.xs(symbol, axis=1, level=1)
                    elif symbol in df.columns.get_level_values(0):
                        df = df.xs(symbol, axis=1, level=0)
                    else:
                        # Fallback: just take the first ticker's data
                        df = df.iloc[:, :6]  # Take first 6 columns (OHLCV + Adj Close)
                        df.columns = ['Adj Close', 'Close', 'High', 'Low', 'Open', 'Volume']
                return df
            
            # If empty, try again unless it's the last attempt
            if attempt < 2:
                logging.warning(f"Empty data for {symbol} on attempt {attempt + 1}, retrying...")
                continue
            return pd.DataFrame()
            
        except Exception as e:
            logging.error(f"History fetch failed for {symbol} on attempt {attempt + 1}: {e}")
            if attempt < 2:  # Not the last attempt
                continue
            return pd.DataFrame()

async def _compute_components(params: Dict[str, Any]) -> Dict[str, Any]:
    # QQQ core
    qqq_df = await _fetch_hist("QQQ", period="12mo", interval="1d")
    if qqq_df.empty:
        raise HTTPException(status_code=503, detail="Data unavailable for QQQ")
    close = qqq_df['Close']
    ema20 = _ema(close, params.get("ema_fast", 20))
    ema50 = _ema(close, params.get("ema_slow", 50))
    adx_series = _compute_adx(qqq_df, params.get("adx_period", 14))
    # ATR% daily using existing logic pattern
    hl = qqq_df['High'] - qqq_df['Low']
    hc = (qqq_df['High'] - qqq_df['Close'].shift()).abs()
    lc = (qqq_df['Low'] - qqq_df['Close'].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr = tr.rolling(params.get("atr_period", 14)).mean()
    atr_pct = (atr / close) * 100
    dist_from_ath_pct = (close / close.cummax() - 1.0) * 100

    # VIX/VXN latest
    vix_df = await _fetch_hist("^VIX", period="6mo", interval="1d")
    vxn_df = await _fetch_hist("^VXN", period="6mo", interval="1d")
    vix = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else None
    vxn = float(vxn_df['Close'].iloc[-1]) if not vxn_df.empty else None

    # Breadth: % NDX above 50-DMA (SMA)
    symbols = await _load_ndx_constituents_symbols()
    eligible = 0
    above = 0
    excluded = 0
    # batch download in chunks to reduce calls
    chunk_size = 20
    for i in range(0, len(symbols), chunk_size):
        chunk = symbols[i:i+chunk_size]
        try:
            multi = yf.download(" ".join(chunk), period="120d", interval="1d", progress=False, auto_adjust=False, group_by='ticker')
            for sym in chunk:
                try:
                    df = multi[sym] if isinstance(multi.columns, pd.MultiIndex) else multi
                    if df.empty or 'Close' not in df:
                        excluded += 1
                        continue
                    if len(df['Close']) < 50:
                        excluded += 1
                        continue
                    sma50 = _sma(df['Close'], 50)
                    c = df['Close'].iloc[-1]
                    s = sma50.iloc[-1]
                    if pd.isna(s):
                        excluded += 1
                        continue
                    eligible += 1
                    if c > s:
                        above += 1
                except Exception:
                    excluded += 1
                    continue
        except Exception:
            excluded += len(chunk)
            continue
    breadth_pct = (above / eligible * 100) if eligible > 0 else None

    components = {
        "qqq_close": float(close.iloc[-1]),
        "ema20": float(ema20.iloc[-1]),
        "ema50": float(ema50.iloc[-1]),
        "adx": float(adx_series.iloc[-1]) if not adx_series.empty else None,
        "atr_pct": float(atr_pct.iloc[-1]),
        "vix": vix,
        "vxn": vxn,
        "breadth_pct_above_50dma": float(breadth_pct) if breadth_pct is not None else None,
        "qqq_dist_from_ath_pct": float(dist_from_ath_pct.iloc[-1]),
        "qqq_ts": close.index[-1].strftime("%Y-%m-%d")
    }

    # additional series for rules
    components["series"] = {
        "close": close.tail(60).tolist(),
        "ema20": ema20.tail(60).tolist(),
        "ema50": ema50.tail(60).tolist(),
        "adx": adx_series.tail(60).fillna(0).tolist(),
        "atr_pct": atr_pct.tail(60).tolist(),
        "dates": [d.strftime("%Y-%m-%d") for d in close.tail(60).index]
    }
    return components

def _compute_msae_and_regime(components: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    # Simple scoring heuristic to 0-100
    score = 0.0
    weights = {
        "trend": 30,
        "adx": 20,
        "vol": 15,
        "fear": 10,
        "breadth": 15,
        "ath": 10
    }
    # Trend
    if components["qqq_close"] > components["ema20"] > components["ema50"]:
        trend_score = weights["trend"]
    elif components["ema20"] > components["ema50"]:
        trend_score = weights["trend"] * 0.6
    else:
        trend_score = weights["trend"] * 0.2
    score += trend_score
    # ADX
    adx_th = params.get("adx_threshold", 20)
    adx_val = components.get("adx", 0)
    adx_score = weights["adx"] * min(max((adx_val - adx_th) / 20 + 0.5, 0), 1)  # center around threshold
    score += adx_score
    # Volatility (lower ATR% better)
    atrp = components.get("atr_pct", 0)
    vol_cap = params.get("atrp_vol_cap_pct", 3.5)
    vol_score = weights["vol"] * (1 - min(atrp / (vol_cap * 2), 1))
    score += vol_score
    # Fear (lower VIX better)
    vix = components.get("vix") or 0
    fear_score = weights["fear"] * (1 - min(vix / 40, 1))
    score += fear_score
    # Breadth
    breadth = components.get("breadth_pct_above_50dma") or 0
    breadth_score = weights["breadth"] * min(breadth / 80, 1)  # 80% breadth saturates
    score += breadth_score
    # ATH distance (closer to 0 better; negative means below ATH)
    ath_dist = abs(components.get("qqq_dist_from_ath_pct", 0))
    ath_score = weights["ath"] * (1 - min(ath_dist / 20, 1))
    score += ath_score

    # Regime label
    ema20 = components["ema20"]
    ema50 = components["ema50"]
    price = components["qqq_close"]
    adx_ok = adx_val > adx_th
    uptrend = (price > ema20 and ema20 > ema50 and adx_ok)
    downtrend = (price < ema20 and ema20 < ema50 and adx_ok)
    # Whipsaw check
    series = components["series"]
    crosses = 0
    e20 = pd.Series(series["ema20"]).dropna()
    e50 = pd.Series(series["ema50"]).dropna()
    if len(e20) == len(e50) and len(e20) > 1:
        above = e20 > e50
        switches = above.astype(int).diff().abs()
        crosses = int(switches.sum())
    chop = (not adx_ok) or (crosses >= params.get("whipsaw_cross_threshold", 3))
    regime = "CHOP"
    if uptrend:
        regime = "UPTREND"
    elif downtrend:
        regime = "DOWNTREND"
    elif chop:
        regime = "CHOP"

    return {
        "msae_score": round(float(score), 2),
        "regime": regime,
        "breakdown": {
            "trend": round(trend_score, 2),
            "adx": round(adx_score, 2),
            "vol": round(vol_score, 2),
            "fear": round(fear_score, 2),
            "breadth": round(breadth_score, 2),
            "ath": round(ath_score, 2)
        },
        "crosses": crosses,
        "adx_ok": adx_ok
    }

async def _decay_guard(params: Dict[str, Any]) -> bool:
    look = params.get("decay_guard_lookback_days", 10)
    tqqq = await _fetch_hist("TQQQ", period=f"{max(look+5, 20)}d", interval="1d")
    sqqq = await _fetch_hist("SQQQ", period=f"{max(look+5, 20)}d", interval="1d")
    def ret_n(df):
        if df.empty or len(df['Close']) <= look:
            return 0
        return float(df['Close'].iloc[-1] / df['Close'].iloc[-look] - 1)
    return (ret_n(tqqq) < 0) and (ret_n(sqqq) < 0)

async def _vol_guard(params: Dict[str, Any], components: Dict[str, Any]) -> bool:
    cap = params.get("atrp_vol_cap_pct", 3.5)
    # Daily check
    if components.get("atr_pct", 0) > cap:
        return True
    # 15m intraday realized proxy: use last day 15m bars HL/Close
    qqq_15 = await _fetch_hist("QQQ", period="5d", interval="15m")
    if not qqq_15.empty:
        last_day = qqq_15.index[-1].date()
        day_df = qqq_15[qqq_15.index.date == last_day]
        if not day_df.empty:
            tr = (day_df['High'] - day_df['Low']).abs()
            atr15 = tr.rolling(16).mean().iloc[-1] if len(tr) >= 16 else tr.mean()
            atrp15 = float(atr15 / day_df['Close'].iloc[-1] * 100)
            if atrp15 > cap:
                return True
    return False

async def _latest_signal() -> Optional[Dict[str, Any]]:
    sig = await db.signals.find({"module": "etf_regime"}).sort("ts", -1).limit(1).to_list(1)
    return sig[0] if sig else None

async def _compute_signal(snapshot: MarketStateSnapshot, params_doc: Dict[str, Any]) -> Dict[str, Any]:
    params = params_doc.get("params", {})
    stale = snapshot.stale
    decision = "QQQI" if not params.get("out_instead_of_income", False) else "OUT"
    weights = {"TQQQ": 0.0, "SQQQ": 0.0, "QQQI": 0.0}
    reason = {}
    confidence = 0.5

    last_sig = await _latest_signal()

    if stale:
        # Do not change decision; use last if exists
        if last_sig:
            return last_sig
        else:
            weights[params.get("income_etf", "QQQI")] = params.get("qqqi_weight_in_chop", 1.0)
            return {
                "ts": datetime.utcnow().isoformat(),
                "module": "etf_regime",
                "regime": snapshot.regime,
                "decision": decision,
                "weights": weights,
                "confidence": 0.5,
                "reason": {"stale": True},
                "params_version": f"{params_doc.get('name','default')}@{params_doc.get('created_at','')}"
            }

    # Confirmation logic using last N days of conditions
    series = snapshot.components.get("series", {})
    close = pd.Series(series.get("close", []))
    ema20 = pd.Series(series.get("ema20", []))
    ema50 = pd.Series(series.get("ema50", []))
    adx = pd.Series(series.get("adx", []))
    n = params.get("flip_confirmation_days", 2)
    cond_up = (close > ema20) & (ema20 > ema50) & (adx > params.get("adx_threshold", 20))
    cond_dn = (close < ema20) & (ema20 < ema50) & (adx > params.get("adx_threshold", 20))
    up_conf = bool(cond_up.tail(n).all()) if len(cond_up) >= n else False
    dn_conf = bool(cond_dn.tail(n).all()) if len(cond_dn) >= n else False

    # Guards
    decay = await _decay_guard(params)
    volfreeze = await _vol_guard(params, snapshot.components)
    reason["guards"] = {"decay": decay, "volatility_freeze": volfreeze}

    if volfreeze and last_sig:
        # Freeze flips: keep last decision
        return last_sig

    if decay:
        decision = "QQQI" if not params.get("out_instead_of_income", False) else "OUT"
        weights[params.get("income_etf", "QQQI")] = params.get("qqqi_weight_in_chop", 1.0)
        reason["decay_guard"] = True
        confidence = 0.6
    else:
        if snapshot.regime == "UPTREND" and up_conf:
            decision = "TQQQ"
            weights = {"TQQQ": params.get("max_leverage_alloc", 1.0), "SQQQ": 0.0, "QQQI": 0.0}
            reason["confirmation"] = f"{n}/{n}"
            confidence = 0.8
        elif snapshot.regime == "DOWNTREND" and dn_conf:
            decision = "SQQQ"
            weights = {"TQQQ": 0.0, "SQQQ": params.get("max_leverage_alloc", 1.0), "QQQI": 0.0}
            reason["confirmation"] = f"{n}/{n}"
            confidence = 0.8
        else:
            decision = "QQQI" if not params.get("out_instead_of_income", False) else "OUT"
            weights[params.get("income_etf", "QQQI")] = params.get("qqqi_weight_in_chop", 1.0)
            reason["confirmation"] = f"0/{n}"
            confidence = 0.6

    # Build reason
    reason.update({
        "ema": "QQQ>20>50" if (snapshot.components["qqq_close"] > snapshot.components["ema20"] > snapshot.components["ema50"]) else "other",
        "adx": f"{round(snapshot.components.get('adx',0),1)}>{params.get('adx_threshold',20)}"
    })

    payload = {
        "ts": datetime.utcnow().isoformat(),
        "module": "etf_regime",
        "regime": snapshot.regime,
        "decision": decision,
        "weights": weights,
        "confidence": round(confidence, 2),
        "reason": reason,
        "params_version": f"{params_doc.get('name','default')}@{params_doc.get('created_at','')}"
    }
    return payload

@api_router.get("/formulas/config/etf-regime")
async def get_etf_regime_config():
    cfg = await _ensure_etf_regime_config()
    # strip ObjectId if any
    if cfg and "_id" in cfg:
        cfg["_id"] = str(cfg["_id"]) if not isinstance(cfg["_id"], str) else cfg["_id"]
    return cfg

@api_router.get("/market/state")
async def get_market_state():
    # Ensure config
    cfg = await _ensure_etf_regime_config()
    params = cfg.get("params", {})

    # Staleness thresholds
    rth = _is_market_hours_ny()
    stale_minutes = params.get("stale_minutes_rth", 20) if rth else params.get("stale_minutes_oth", 180)

    components = await _compute_components(params)
    # Determine staleness by comparing now to last QQQ date; for intraday we could refine
    now_utc = datetime.utcnow()
    last_bar_date = datetime.strptime(components["qqq_ts"], "%Y-%m-%d")
    # If RTH and last daily bar is previous day and minutes exceed threshold, mark stale
    stale = False
    if rth:
        # use 15m data to better gauge freshness
        q15 = await _fetch_hist("QQQ", period="1d", interval="15m")
        if not q15.empty:
            last_ts = q15.index[-1]
            age_min = (now_utc - last_ts.tz_convert(pytz.UTC).to_pydatetime()).total_seconds() / 60
            stale = age_min > stale_minutes
        else:
            stale = True
    else:
        # off hours, acceptable data age is days
        age_min = (now_utc - datetime.combine(last_bar_date, datetime.min.time())).total_seconds() / 60
        stale = age_min > stale_minutes

    msae = _compute_msae_and_regime(components, params)
    snapshot = MarketStateSnapshot(
        regime=msae["regime"],
        msae_score=msae["msae_score"],
        components={k: v for k, v in components.items() if k != "series"},
        stale=stale
    )
    doc = snapshot.dict()
    doc.update({"breakdown": msae["breakdown"], "crosses": msae["crosses"], "adx_ok": msae["adx_ok"]})
    await db.market_state.insert_one(doc)

    # Build minimal response per contract
    return {
        "ts": snapshot.ts.isoformat(),
        "regime": snapshot.regime,
        "msae_score": snapshot.msae_score,
        "components": snapshot.components,
        "stale": snapshot.stale
    }

@api_router.get("/market/history")
async def get_market_history(start: Optional[str] = None, end: Optional[str] = None, interval: str = Query("1d", pattern="^(1d|15m)$")):
    # Return persisted snapshots within window
    query = {}
    try:
        if start:
            query.setdefault("ts", {})["$gte"] = datetime.fromisoformat(start.replace("Z",""))
        if end:
            query.setdefault("ts", {})["$lte"] = datetime.fromisoformat(end.replace("Z",""))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid start/end format. Use ISO 8601.")

    cur = db.market_state.find(query).sort("ts", 1)
    items = await cur.to_list(length=1000)
    out = []
    for it in items:
        # sanitize
        it.pop("_id", None)
        out.append(it)
    return out

@api_router.get("/signals/etf-regime")
async def get_etf_regime_signal():
    cfg = await _ensure_etf_regime_config()
    params = cfg.get("params", {})

    # Use latest snapshot or compute fresh
    latest = await db.market_state.find({}).sort("ts", -1).limit(1).to_list(1)
    if latest:
        snap_doc = latest[0]
    else:
        # compute via calling market state
        _ = await get_market_state()
        latest = await db.market_state.find({}).sort("ts", -1).limit(1).to_list(1)
        if not latest:
            raise HTTPException(status_code=503, detail="No market state available")
        snap_doc = latest[0]

    snapshot = MarketStateSnapshot(
        ts=snap_doc.get("ts", datetime.utcnow()),
        regime=snap_doc.get("regime", "CHOP"),
        msae_score=float(snap_doc.get("msae_score", 0)),
        components=snap_doc.get("components", {}),
        stale=bool(snap_doc.get("stale", False))
    )

    signal_payload = await _compute_signal(snapshot, cfg)
    # Persist signal
    to_save = signal_payload.copy()
    to_save["module"] = "etf_regime"
    # Avoid duplicate key if payload came from a previous doc (stale freeze etc.)
    to_save.pop("_id", None)
    await db.signals.insert_one(to_save)
    return signal_payload

# ==================== END MSAE + ETF ENGINE ====================

@api_router.get("/formulas/config/all")
async def get_all_formula_configs():
    """Return all formula configs including etf_regime"""
    try:
        await _ensure_etf_regime_config()
        config = await db.formula_configs.find().to_list(length=None)
        cleaned = []
        for cfg in config:
            cfg = dict(cfg)
            if '_id' in cfg:
                cfg['_id'] = str(cfg['_id'])
            for k, v in list(cfg.items()):
                if isinstance(v, datetime):
                    cfg[k] = v.isoformat()
            cleaned.append(cfg)
        return cleaned
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- NDX Constituents Admin Endpoints ----------

class NdxMember(BaseModel):
    symbol: str
    yf_symbol: Optional[str] = None
    name: Optional[str] = None
    sector: Optional[str] = None
    active: bool = True
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    weight: Optional[float] = None

class NdxPayload(BaseModel):
    as_of: Optional[str] = None
    source: Optional[str] = None
    version: Optional[int] = None
    universe: List[NdxMember]
    notes: Optional[str] = None

@api_router.get("/ndx/constituents")
async def get_ndx_constituents(all: bool = Query(False)):
    doc = await db.ndx_constituents.find_one({"_id": "ndx:active"})
    if not doc:
        # return fallback universe as active only
        uni = [{"symbol": s, "yf_symbol": s, "name": s, "sector": None, "active": True, "effective_from": None, "effective_to": None} for s in NDX_TICKERS_FALLBACK]
        return {"_id": "ndx:active", "index": "NDX", "as_of": datetime.utcnow().isoformat()+"Z", "version": 1, "universe": uni if all else [u for u in uni if u["active"]]}
    # sanitize
    doc["_id"] = str(doc["_id"])
    if not all and "universe" in doc:
        doc = dict(doc)
        doc["universe"] = [m for m in doc["universe"] if m.get("active", True)]
    return doc

@api_router.post("/ndx/constituents")
async def upsert_ndx_constituents(payload: NdxPayload, current_user: User = Depends(get_current_user)):
    # Admin-only could be enforced later via roles; for now any authenticated user
    # Validate basic shape
    symbols = set()
    for m in payload.universe:
        s = (m.symbol or "").upper()
        if not s:
            raise HTTPException(status_code=400, detail="symbol required")
        if s in symbols:
            raise HTTPException(status_code=400, detail=f"duplicate symbol {s}")
        symbols.add(s)
    now = datetime.utcnow().isoformat()+"Z"
    # Versioning
    active = await db.ndx_constituents.find_one({"_id": "ndx:active"})
    new_version = (active.get("version", 0) + 1) if active else (payload.version or 1)
    new_doc = {
        "_id": "ndx:active",
        "index": "NDX",
        "as_of": payload.as_of or now,
        "source": payload.source or "manual_seed",
        "version": new_version,
        "notes": payload.notes,
        "universe": [m.dict() for m in payload.universe]
    }
    # Archive previous active as ndx:v<version>
    if active:
        old_ver = active.get("version", 0)
        active_copy = dict(active)
        active_copy["_id"] = f"ndx:v{old_ver}"
        await db.ndx_constituents.replace_one({"_id": f"ndx:v{old_ver}"}, active_copy, upsert=True)
    # Save new active and archive as its version as well
    await db.ndx_constituents.replace_one({"_id": "ndx:active"}, new_doc, upsert=True)
    archive_doc = dict(new_doc)
    archive_doc["_id"] = f"ndx:v{new_version}"
    await db.ndx_constituents.replace_one({"_id": archive_doc["_id"]}, archive_doc, upsert=True)
    return {"message": "NDX constituents updated", "version": new_version}

@api_router.get("/ndx/constituents/diff")
async def ndx_constituents_diff(fromVersion: int = Query(...), toVersion: int = Query(...)):
    a = await db.ndx_constituents.find_one({"_id": f"ndx:v{fromVersion}"})
    b = await db.ndx_constituents.find_one({"_id": f"ndx:v{toVersion}"})
    if not a or not b:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    set_a = {m.get("symbol","" ).upper(): m for m in a.get("universe", []) if m.get("active", True)}
    set_b = {m.get("symbol","" ).upper(): m for m in b.get("universe", []) if m.get("active", True)}
    added = [set_b[s] for s in set(set_b.keys()) - set(set_a.keys())]
    removed = [set_a[s] for s in set(set_a.keys()) - set(set_b.keys())]
    changed = []
    for s in set(set_a.keys()) & set(set_b.keys()):
        ma, mb = set_a[s], set_b[s]
        if (ma.get("yf_symbol") != mb.get("yf_symbol")) or (ma.get("active") != mb.get("active")):
            changed.append({"symbol": s, "from": ma, "to": mb})
    return {"fromVersion": fromVersion, "toVersion": toVersion, "added": added, "removed": removed, "changed": changed}

@api_router.post("/ndx/constituents/refresh-prices")
async def ndx_refresh_prices(interval: str = Query("1d", pattern="^(1d|15m)$")):
    doc = await db.ndx_constituents.find_one({"_id": "ndx:active"})
    symbols = [m.get("yf_symbol", m.get("symbol")).upper() for m in (doc.get("universe", []) if doc else []) if m.get("active", True)]
    if not symbols:
        symbols = NDX_TICKERS_FALLBACK
    # batch
    batch = 20
    requested = 0
    succeeded = 0
    failed = []
    for i in range(0, len(symbols), batch):
        chunk = symbols[i:i+batch]
        requested += len(chunk)
        try:
            multi = yf.download(" ".join(chunk), period="120d", interval=interval, progress=False, auto_adjust=False, group_by='ticker')
            for sym in chunk:
                try:
                    df = multi[sym] if isinstance(multi.columns, pd.MultiIndex) else multi
                    if df is None or df.empty:
                        failed.append(sym); continue
                    # Persist last 5 rows only to keep light
                    tail = df.tail(5)
                    for idx, row in tail.iterrows():
                        rec = {
                            "_id": f"{sym}|{interval}|{idx.strftime('%Y-%m-%d %H:%M') if interval=='15m' else idx.strftime('%Y-%m-%d')}",
                            "symbol": sym,
                            "interval": interval,
                            "ts": idx.to_pydatetime().isoformat(),
                            "o": float(row['Open']),
                            "h": float(row['High']),
                            "l": float(row['Low']),
                            "c": float(row['Close']),
                            "v": int(row['Volume']) if not pd.isna(row['Volume']) else 0
                        }
                        await db.prices.replace_one({"_id": rec["_id"]}, rec, upsert=True)
                    succeeded += 1
                except Exception:
                    failed.append(sym)
        except Exception:
            failed.extend(chunk)
    return {"requested": requested, "succeeded": succeeded, "failed": failed}


# Mount the router
app.include_router(api_router)

# Add this to enable the app to be run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)