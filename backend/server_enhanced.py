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

# ... existing imports and setup above unchanged ...
# (omitted here for brevity in this snippet)

# =====================
# Rotation Lab: models
# =====================
class RotationConfig(BaseModel):
    name: str = "Default"
    capital: float = 100000.0
    rebalance: str = "W"  # D/W/M
    lookback_days: int = 126
    trend_days: int = 200
    max_positions: int = 2
    cost_bps: float = 5.0
    slippage_bps: float = 5.0
    pairs: List[Dict[str, Any]] = []  # [{bull:"TQQQ", bear:"SQQQ"}, ...]

# =====================
# Rotation Lab: endpoints
# =====================
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
        # Read all sheets
        xls = pd.ExcelFile(content)
        sheets = {}
        for name in xls.sheet_names:
            df = xls.parse(name)
            # limit to first 200 rows/30 cols to keep payload light
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
    # Minimal placeholder: echo config and empty signals to wire UI
    doc = await db.rotation_configs.find_one({"owner": user["email"]})
    config = (doc or {}).get("config") or RotationConfig().model_dump()
    return {"config": config, "as_of": datetime.utcnow().isoformat(), "signals": [], "trades": []}

@api_router.post("/rotation/backtest")
async def rotation_backtest(cfg: RotationConfig, user: dict = Depends(get_current_user)):
    # Minimal placeholder backtest result with shape for UI
    return {
        "config": cfg.model_dump(),
        "metrics": {"cagr": 0.0, "max_dd": 0.0, "sharpe": 0.0},
        "equity_curve": [],
        "drawdown": [],
        "trades": []
    }

# ... rest of existing routes remain unchanged ...