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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

# FastAPI app and router
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api_router = APIRouter(prefix="/api")

# Auth basics
JWT_SECRET = os.environ.get('JWT_SECRET', 'etf-intelligence-secret-key')
JWT_ALGORITHM = "HS256"
security = HTTPBearer()

from cryptography.fernet import Fernet
from hashlib import sha256
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
            # allow pass-through for now but indicate anonymous
            return {"email": email}
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

class RotationConfig(BaseModel):
    name: str = "Default"
    capital: float = 100000.0
    rebalance: str = "D"  # D/W/M (not used in v1 logic, placeholder)
    lookback_days: int = 126
    trend_days: int = 200
    max_positions: int = 1
    cost_bps: float = 5.0
    slippage_bps: float = 5.0
    pairs: List[Dict[str, Any]] = []  # [{bull:"TQQQ", bear:"SQQQ", underlying:"QQQ"}, ...]
    # Sheet-like knobs
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

@api_router.get("/rotation/config")
async def get_rotation_config(user: dict = Depends(get_current_user)):
    doc = await db.rotation_configs.find_one({"owner": user["email"]})
    if not doc:
        return {"owner": user["email"], "config": RotationConfig().model_dump()}
    doc.pop("_id", None)
    return doc

@api_router.post("/rotation/config")
async def save_rotation_config(cfg: RotationConfig, user: dict = Depends(get_current_user)):
    await db.rotation_configs.update_one(
        {"owner": user["email"]},
        {"$set": {"owner": user["email"], "config": cfg.model_dump(), "updated_at": datetime.utcnow()}},
        upsert=True
    )
    return {"message": "saved"}

@api_router.post("/rotation/upload-xlsx")
async def upload_rotation_xlsx(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    try:
        content = await file.read()
        xls = pd.ExcelFile(content)
        sheets = {}
        for name in xls.sheet_names:
            df = xls.parse(name)
            sheets[name] = df.iloc[:200, :30].fillna("").to_dict(orient="records")
        await db.rotation_uploads.update_one(
            {"owner": user["email"]},
            {"$set": {"owner": user["email"], "filename": file.filename, "sheets": sheets, "uploaded_at": datetime.utcnow()}},
            upsert=True
        )
        return {"message": "parsed", "sheets": list(sheets.keys())}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload parse failed: {e}")

@api_router.get("/rotation/live")
async def rotation_live(user: dict = Depends(get_current_user)):
    doc = await db.rotation_configs.find_one({"owner": user["email"]})
    config = (doc or {}).get("config") or RotationConfig().model_dump()
    return {"config": config, "as_of": datetime.utcnow().isoformat(), "signals": [], "trades": []}

@api_router.post("/rotation/backtest")
async def rotation_backtest(cfg: RotationConfig, user: dict = Depends(get_current_user)):
    import yfinance as yf

    # Pull knobs from cfg
    short_len = cfg.ema_fast or 20
    long_len = cfg.ema_slow or 50
    trend_len = cfg.trend_days or 200
    rsi_len = cfg.rsi_len or 14
    atr_len = cfg.atr_len or 20
    kelt_mult = cfg.kelt_mult or 2.0
    macd_fast, macd_slow, macd_sig = cfg.macd_fast or 12, cfg.macd_slow or 26, cfg.macd_signal or 9
    consec_needed = cfg.consec_needed or 2
    conf_threshold = cfg.conf_threshold or 2

    pairs = cfg.pairs or [{"bull": "TQQQ", "bear": "SQQQ", "underlying": "QQQ"}]
    p0 = pairs[0]
    bull = p0.get("bull", "TQQQ")
    bear = p0.get("bear", "SQQQ")
    underlying = p0.get("underlying", "QQQ")

    end = datetime.now().date()
    start = end - timedelta(days=max(900, trend_len*3))

    def dl(t):
        df = yf.download(t, start=start, end=end, progress=False, auto_adjust=True)
        if df is None or df.empty:
            raise HTTPException(status_code=500, detail=f"No data for {t}")
        df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
        return df[["open","high","low","close","volume"]]

    u = dl(underlying)
    b = dl(bull)
    s = dl(bear)

    def EMA(x, n): return x.ewm(span=n, adjust=False).mean()
    def SMA(x, n): return x.rolling(n).mean()
    def RSI(x, n=14):
        delta = x.diff()
        gain = (delta.where(delta > 0, 0.0)).rolling(n).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(n).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
    def ATR(df, n=14):
        high, low, close = df['high'], df['low'], df['close']
        prev_close = close.shift(1)
        tr = pd.concat([
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs()
        ], axis=1).max(axis=1)
        return tr.rolling(n).mean()
    def MACD(x, fast=12, slow=26, sig=9):
        ema_fast = EMA(x, fast)
        ema_slow = EMA(x, slow)
        macd = ema_fast - ema_slow
        signal = EMA(macd, sig)
        hist = macd - signal
        return macd, signal, hist

    sig = pd.DataFrame(index=u.index)
    sig['close'] = u['close']
    sig['ema20'] = EMA(sig['close'], short_len)
    sig['ema50'] = EMA(sig['close'], long_len)
    sig['sma200'] = SMA(sig['close'], trend_len)
    sig['rsi14'] = RSI(sig['close'], rsi_len)
    sig['atr20'] = ATR(u, atr_len)
    sig['kc_mid'] = sig['ema20']
    sig['kc_upper'] = sig['kc_mid'] + kelt_mult*sig['atr20']
    sig['kc_lower'] = sig['kc_mid'] - kelt_mult*sig['atr20']
    sig['macd'], sig['macd_sig'], sig['macd_hist'] = MACD(sig['close'], macd_fast, macd_slow, macd_sig)

    sig['dual_up'] = (sig['ema20'] > sig['ema50']).astype(int)
    sig['dual_dn'] = (sig['ema20'] < sig['ema50']).astype(int)
    sig['dual_consec'] = sig['dual_up'] * (sig['dual_up'].groupby((sig['dual_up'] != sig['dual_up'].shift()).cumsum()).cumcount()+1)
    sig['dual_consec_ok'] = (sig['dual_consec'] >= consec_needed).astype(int)

    sig['trend_bull'] = (sig['close'] > sig['sma200']).astype(int)
    sig['trend_bear'] = (sig['close'] < sig['sma200']).astype(int)
    sig['kelt_bull'] = (sig['close'] > sig['kc_upper']).astype(int)
    sig['kelt_bear'] = (sig['close'] < sig['kc_lower']).astype(int)
    sig['macd_bull'] = (sig['macd'] > sig['macd_sig']).astype(int)
    sig['macd_bear'] = (sig['macd'] < sig['macd_sig']).astype(int)
    sig['rsi_bull'] = (sig['rsi14'] > 50).astype(int)
    sig['rsi_bear'] = (sig['rsi14'] < 50).astype(int)

    sig['conf_bull'] = sig[['dual_up','trend_bull','kelt_bull','macd_bull','rsi_bull']].sum(axis=1)
    sig['conf_bear'] = sig[['dual_dn','trend_bear','kelt_bear','macd_bear','rsi_bear']].sum(axis=1)

    pos = []  # 1 bull, -1 bear, 0 cash
    last = 0
    for i, row in sig.iterrows():
        bull_ok = (row['conf_bull'] >= conf_threshold) and (row['dual_consec_ok'] == 1)
        bear_ok = (row['conf_bear'] >= conf_threshold)
        if bull_ok and not bear_ok:
            cur = 1
        elif bear_ok and not bull_ok:
            cur = -1
        elif bull_ok and bear_ok:
            cur = 1 if row['conf_bull'] >= row['conf_bear'] else -1
        else:
            cur = 0
        pos.append(cur)
        last = cur
    sig['pos_signal'] = pos

    # Execution prices
    if cfg.exec_timing == 'close':
        exec_prices = pd.DataFrame(index=sig.index)
        exec_prices['bull_px'] = b['close']
        exec_prices['bear_px'] = s['close']
    else:
        exec_prices = pd.DataFrame(index=sig.index)
        exec_prices['bull_px'] = b['open']
        exec_prices['bear_px'] = s['open']
        exec_prices = exec_prices.shift(-1)  # next day open

    capital = cfg.capital
    cost = cfg.cost_bps/10000.0
    slip = cfg.slippage_bps/10000.0

    holding = 0  # 1 bull, -1 bear, 0 cash
    equity = []
    cash = capital
    shares_bull = 0.0
    shares_bear = 0.0
    trades = []

    for dt, row in sig.iterrows():
        px_b = exec_prices.at[dt, 'bull_px'] if dt in exec_prices.index else np.nan
        px_s = exec_prices.at[dt, 'bear_px'] if dt in exec_prices.index else np.nan
        target = row['pos_signal']
        # change position
        if target != holding:
            # sell existing
            if holding == 1 and shares_bull>0 and pd.notna(px_b):
                proceeds = shares_bull * px_b * (1 - cost - slip)
                cash += proceeds
                trades.append({"date": str(dt.date()), "action": "SELL", "ticker": bull, "shares": float(shares_bull), "price": float(px_b)})
                shares_bull = 0.0
            if holding == -1 and shares_bear>0 and pd.notna(px_s):
                proceeds = shares_bear * px_s * (1 - cost - slip)
                cash += proceeds
                trades.append({"date": str(dt.date()), "action": "SELL", "ticker": bear, "shares": float(shares_bear), "price": float(px_s)})
                shares_bear = 0.0
            holding = 0
            # buy new
            if target == 1 and pd.notna(px_b) and cash > 0:
                alloc = cash
                shares_bull = alloc / (px_b * (1 + cost + slip))
                cash -= shares_bull * px_b * (1 + cost + slip)
                trades.append({"date": str(dt.date()), "action": "BUY", "ticker": bull, "shares": float(shares_bull), "price": float(px_b)})
                holding = 1
            elif target == -1 and pd.notna(px_s) and cash > 0:
                alloc = cash
                shares_bear = alloc / (px_s * (1 + cost + slip))
                cash -= shares_bear * px_s * (1 + cost + slip)
                trades.append({"date": str(dt.date()), "action": "BUY", "ticker": bear, "shares": float(shares_bear), "price": float(px_s)})
                holding = -1
        # mark to market
        cur_equity = cash
        if holding == 1 and pd.notna(px_b):
            cur_equity += shares_bull * px_b
        if holding == -1 and pd.notna(px_s):
            cur_equity += shares_bear * px_s
        equity.append({"date": str(dt.date()), "equity": float(cur_equity)})

    if not equity:
        raise HTTPException(status_code=500, detail="No equity curve computed")

    eq = pd.Series([e['equity'] for e in equity], index=[pd.to_datetime(e['date']) for e in equity])
    ret = eq.pct_change().fillna(0.0)
    total_return = eq.iloc[-1]/eq.iloc[0] - 1
    yrs = max(1e-9, (eq.index[-1] - eq.index[0]).days/365.25)
    cagr = (1+total_return)**(1/yrs) - 1 if yrs>0 else total_return
    dd = (eq/eq.cummax()-1)
    max_dd = dd.min()
    sharpe = (ret.mean()/ (ret.std()+1e-9)) * np.sqrt(252)

    return {
        "config": cfg.model_dump(),
        "metrics": {"cagr": float(cagr), "max_dd": float(max_dd), "sharpe": float(sharpe), "total_return": float(total_return)},
        "equity_curve": equity,
        "drawdown": [{"date": str(d.date()), "dd": float(v)} for d,v in dd.items()],
        "trades": trades
    }