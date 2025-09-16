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

# ... existing config/upload/live/backtest endpoints below ...