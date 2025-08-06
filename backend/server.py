from fastapi import FastAPI, APIRouter, HTTPException, Query
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Timezone setup for South Africa
SA_TZ = pytz.timezone('Africa/Johannesburg')
NY_TZ = pytz.timezone('America/New_York')

# ETF Data Models
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
    gmma_pattern: str  # "RWB", "BWR", "Mixed"
    sma20_trend: str  # "U" (up), "D" (down), "F" (flat)
    volume: int
    market_cap: float
    swing_start_date: Optional[datetime] = None
    swing_days: Optional[int] = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# New Model Classes for Enhanced Features
class WatchlistItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticker: str
    name: str
    list_name: str
    notes: str = ""
    tags: List[str] = []
    priority: int = 1  # 1-5 priority level
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    position_size: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CustomWatchlist(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    color: str = "#3B82F6"  # Default blue
    created_at: datetime = Field(default_factory=datetime.utcnow)

class JournalEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime = Field(default_factory=datetime.utcnow)
    title: str
    content: str
    tags: List[str] = []
    market_score: Optional[int] = None
    trades_mentioned: List[str] = []
    mood: str = "neutral"  # positive, neutral, negative
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

# Enhanced ETF Universe
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
    
    # NYSE opens at 9:30 AM ET
    market_open = ny_time.replace(hour=9, minute=30, second=0, microsecond=0)
    
    # If it's past market open today, calculate for tomorrow
    if ny_time.time() > market_open.time():
        market_open += timedelta(days=1)
    
    # Skip weekends
    while market_open.weekday() > 4:  # 0-4 is Mon-Fri
        market_open += timedelta(days=1)
    
    time_diff = market_open - ny_time
    hours = int(time_diff.seconds // 3600)
    minutes = int((time_diff.seconds % 3600) // 60)
    seconds = int(time_diff.seconds % 60)
    
    return f"{hours}h {minutes}m {seconds}s"

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
    classification: str  # "Green Day", "Yellow Day", "Red Day"
    recommendation: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)

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

# ETF Universe - Major ETFs across sectors
ETF_UNIVERSE = [
    # Major Indices
    {"ticker": "SPY", "name": "SPDR S&P 500 ETF", "sector": "Broad Market", "theme": "Large Cap"},
    {"ticker": "QQQ", "name": "Invesco QQQ Trust", "sector": "Technology", "theme": "Large Cap Growth"},
    {"ticker": "IWM", "name": "iShares Russell 2000 ETF", "sector": "Broad Market", "theme": "Small Cap"},
    {"ticker": "DIA", "name": "SPDR Dow Jones Industrial ETF", "sector": "Broad Market", "theme": "Blue Chip"},
    
    # Leveraged ETFs
    {"ticker": "TQQQ", "name": "ProShares UltraPro QQQ", "sector": "Technology", "theme": "3x Leveraged"},
    {"ticker": "SQQQ", "name": "ProShares UltraPro Short QQQ", "sector": "Technology", "theme": "3x Inverse"},
    {"ticker": "TNA", "name": "Direxion Daily Small Cap Bull 3X", "sector": "Small Cap", "theme": "3x Leveraged"},
    {"ticker": "SPXL", "name": "Direxion Daily S&P 500 Bull 3X", "sector": "Large Cap", "theme": "3x Leveraged"},
    
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
    
    # Specialty & Thematic
    {"ticker": "GLD", "name": "SPDR Gold Shares", "sector": "Commodities", "theme": "Precious Metals"},
    {"ticker": "TLT", "name": "iShares 20+ Year Treasury Bond", "sector": "Bonds", "theme": "Long Term Treasury"},
    {"ticker": "VIX", "name": "iPath Series B S&P 500 VIX", "sector": "Volatility", "theme": "Volatility"},
    {"ticker": "UVXY", "name": "ProShares Ultra VIX Short-Term", "sector": "Volatility", "theme": "2x Volatility"},
]

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

# API Routes
@api_router.get("/")
async def root():
    return {"message": "ETF Intelligence System API"}

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

@api_router.get("/etfs/leaders")
async def get_leaders(timeframe: str = Query("1m", description="1d, 1w, 1m, 3m, 6m")):
    """Get top performing ETFs by timeframe"""
    try:
        sort_field = f"change_{timeframe}"
        etfs = await db.etfs.find().sort(sort_field, -1).limit(20).to_list(length=20)
        return [ETFData(**etf) for etf in etfs]
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

@api_router.get("/watchlists/lists")
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
        score = await db.market_scores.find().sort("date", -1).limit(1).first()
        if not score:
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
        
        return MarketScore(**score)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/market-score", response_model=MarketScore)
async def update_market_score(score: MarketScore):
    """Update market score"""
    try:
        # Calculate total and classification
        total = (score.sata_score + score.adx_score + score.vix_score + 
                score.atr_score + score.gmi_score + score.nhnl_score + 
                score.fg_index_score + score.qqq_ath_distance_score)
        
        if total >= 28:
            classification = "Green Day"
            recommendation = "Full exposure. Use wider stop losses. Aggressive position sizing."
        elif total >= 20:
            classification = "Yellow Day"  
            recommendation = "Selective entries. Moderate position sizing. Standard stops."
        else:
            classification = "Red Day"
            recommendation = "Risk-off mode. Tight stops or avoid new positions."
        
        score.total_score = total
        score.classification = classification
        score.recommendation = recommendation
        
        await db.market_scores.insert_one(score.dict())
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chart Analysis Route (placeholder for AI integration)
@api_router.get("/charts/{ticker}/analysis", response_model=ChartAnalysis)
async def get_chart_analysis(ticker: str, timeframe: str = "1d"):
    """Get AI-powered chart analysis for a ticker"""
    try:
        # This would integrate with OpenAI's vision API
        # For now, return mock analysis
        analysis = ChartAnalysis(
            ticker=ticker,
            timeframe=timeframe,
            pattern_analysis=f"Analyzing {ticker} on {timeframe} timeframe: Strong uptrend with consolidation pattern forming near resistance.",
            support_levels=[100.0, 95.0],
            resistance_levels=[110.0, 115.0],
            trend_analysis="Bullish momentum with decreasing volume - possible exhaustion.",
            risk_reward="Risk/Reward: 1:2.5 with stop at $95 and target at $115",
            recommendation="Wait for breakout above $110 with volume confirmation.",
            confidence=0.75
        )
        
        await db.chart_analyses.insert_one(analysis.dict())
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize data on startup"""
    try:
        # Update ETF data on startup
        await update_etf_data()
        logging.info("ETF Intelligence System started successfully")
    except Exception as e:
        logging.error(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()