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

class RotationPresetIn(BaseModel):
    name: str
    config: RotationConfig

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

# Backtest endpoint
class BacktestConfig(BaseModel):
    pairs: List[Dict[str, str]]  # [{"bull": "TQQQ", "bear": "SQQQ", "underlying": "QQQ"}]
    capital: float = 100000.0
    lookback_days: int = 126
    rebalance: str = "D"

@api_router.post("/rotation/backtest")
async def run_backtest(config: BacktestConfig, user: dict = Depends(get_current_user)):
    """Run rotation backtest with given configuration"""
    try:
        # Mock backtest results for testing
        # In production, this would run actual backtest logic
        
        # Generate mock equity curve data
        import random
        dates = []
        equity_values = []
        base_date = datetime.now() - timedelta(days=252)  # 1 year back
        
        current_value = config.capital
        for i in range(252):  # Daily data for 1 year
            dates.append((base_date + timedelta(days=i)).strftime("%Y-%m-%d"))
            # Mock random walk with slight upward bias
            daily_return = random.gauss(0.0005, 0.02)  # 0.05% daily return, 2% volatility
            current_value *= (1 + daily_return)
            equity_values.append(round(current_value, 2))
        
        # Calculate metrics
        total_return = (equity_values[-1] - config.capital) / config.capital * 100
        max_equity = max(equity_values)
        max_drawdown = min([(eq - max_equity) / max_equity * 100 for eq in equity_values])
        
        # Mock additional metrics
        metrics = {
            "total_return_pct": round(total_return, 2),
            "annualized_return_pct": round(total_return, 2),  # Simplified for 1 year
            "max_drawdown_pct": round(abs(max_drawdown), 2),
            "sharpe_ratio": round(random.uniform(0.5, 2.0), 2),
            "win_rate_pct": round(random.uniform(45, 65), 1),
            "profit_factor": round(random.uniform(1.1, 2.5), 2),
            "total_trades": random.randint(50, 150),
            "avg_trade_pct": round(random.uniform(-0.5, 1.5), 2),
            "volatility_pct": round(random.uniform(15, 25), 2)
        }
        
        equity_curve = {
            "dates": dates,
            "equity": equity_values
        }
        
        return {
            "status": "completed",
            "config": config.dict(),
            "metrics": metrics,
            "equity_curve": equity_curve,
            "pairs_tested": len(config.pairs),
            "backtest_period": f"{dates[0]} to {dates[-1]}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

# Mount the router
app.include_router(api_router)