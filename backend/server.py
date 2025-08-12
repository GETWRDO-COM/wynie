from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header, status, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
import uuid
from datetime import datetime, date
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Service configuration (do not hardcode URLs or ports; env-managed)
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Feature flag
FEATURE_HUNT_TRADE_JOURNAL_ENABLED = os.environ.get('FEATURE_HUNT_TRADE_JOURNAL_ENABLED', 'true').lower() == 'true'
INTERNAL_JOB_TOKEN = os.environ.get('INTERNAL_JOB_TOKEN', None)
SAST_TZ = pytz.timezone('Africa/Johannesburg')

# Scheduler (global)
scheduler: Optional[BackgroundScheduler] = None

# Main app and /api router
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class Account(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    external_account_id: str
    name: str
    currency: str = 'USD'
    ingest_window_local: str = '22:30'  # HH:MM in SAST
    timezone: str = 'Africa/Johannesburg'
    portfolio_list: str = 'BOTH'  # PF1 | PF2 | BOTH
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    ingest_window_local: Optional[str] = None
    currency: Optional[str] = None
    enabled: Optional[bool] = None
    portfolio_list: Optional[str] = None

class IngestJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str
    idempotency_key: str
    as_of_date: Optional[str] = None  # YYYY-MM-DD
    artifact_hash: Optional[str] = None  # sha256 of batch
    status: str = 'pending'  # pending|running|completed|failed
    error_message: Optional[str] = None
    files_processed: int = 0
    files_failed: int = 0
    total_bytes: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestAudit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str
    external_account_id: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    as_of_date: Optional[str] = None
    artifact_hash: Optional[str] = None
    headers_fingerprint: Dict[str, Any] = Field(default_factory=dict)
    remote_files: List[Dict[str, Any]] = Field(default_factory=list)
    note: Optional[str] = None

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Helpers
async def ensure_indexes_and_seed():
    # Unique indexes for idempotency and keys
    await db.accounts.create_index('external_account_id', unique=True)
    await db.accounts.create_index('enabled')
    await db.ingest_jobs.create_index('idempotency_key', unique=True)
    await db.ingest_jobs.create_index('account_id')
    await db.ingest_jobs.create_index(
        [('account_id', 1), ('as_of_date', 1), ('artifact_hash', 1)],
        unique=True,
        partialFilterExpression={"artifact_hash": {"$exists": True}}
    )
    # Domain collection indexes (compound uniques for idempotency)
    await db.orders.create_index([('account_id', 1), ('external_order_id', 1)], unique=True)
    await db.executions.create_index([('account_id', 1), ('external_execution_id', 1)], unique=True)
    await db.positions_eod.create_index([('account_id', 1), ('as_of', 1), ('instrument_id', 1)], unique=True)
    await db.balances_eod.create_index([('account_id', 1), ('as_of', 1)], unique=True)
    await db.cash_events.create_index([('account_id', 1), ('posted_at', 1), ('amount', 1), ('description', 1)], unique=True)
    await db.tags.create_index('name', unique=True)
    await db.execution_tags.create_index([('execution_id', 1), ('tag_id', 1)], unique=True)
    await db.trades_net.create_index([('account_id', 1), ('exit_time', -1)])

    # Seed two accounts if not present
    existing = await db.accounts.count_documents({})
    if existing == 0:
        seed_accounts = [
            Account(external_account_id='9863032', name='Portfolio 1', currency='USD', ingest_window_local='22:30'),
            Account(external_account_id='9063957', name='Portfolio 2', currency='USD', ingest_window_local='22:30'),
        ]
        for acc in seed_accounts:
            doc = acc.model_dump()
            doc['_id'] = doc['id']  # UUID string _id
            await db.accounts.insert_one(doc)

async def get_account_by_external(external_account_id: str) -> Optional[Account]:
    doc = await db.accounts.find_one({'external_account_id': external_account_id})
    if not doc:
        return None
    doc['id'] = doc['_id']
    return Account(**{k: v for k, v in doc.items() if k != '_id'})

async def verify_feature_enabled():
    if not FEATURE_HUNT_TRADE_JOURNAL_ENABLED:
        raise HTTPException(status_code=403, detail='HUNT Trade Journal is disabled by feature flag')

async def verify_internal_token(authorization: Optional[str]):
    if not INTERNAL_JOB_TOKEN:
        raise HTTPException(status_code=401, detail='Internal job token not configured')
    if not authorization:
        raise HTTPException(status_code=401, detail='Missing Authorization header')
    try:
        scheme, token = authorization.split(' ')
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid Authorization header')
    if scheme.lower() != 'bearer' or token != INTERNAL_JOB_TOKEN:
        raise HTTPException(status_code=401, detail='Unauthorized')

# Basic routes
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.model_dump())
    doc = status_obj.model_dump()
    doc['_id'] = doc['id']
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**{**sc, 'id': sc.get('_id', sc.get('id'))}) for sc in status_checks]

# Admin: Accounts
@api_router.get('/admin/accounts', response_model=List[Account])
async def list_accounts():
    await verify_feature_enabled()
    docs = await db.accounts.find().to_list(100)
    items: List[Account] = []
    for d in docs:
        d['id'] = d.get('_id', d.get('id'))
        items.append(Account(**{k: v for k, v in d.items() if k != '_id'}))
    return items

@api_router.patch('/admin/accounts/{external_account_id}', response_model=Account)
async def update_account(external_account_id: str, payload: AccountUpdate):
    await verify_feature_enabled()
    acc = await get_account_by_external(external_account_id)
    if not acc:
        raise HTTPException(status_code=404, detail='Account not found')
    update: Dict[str, Any] = {}
    for field in ['name', 'ingest_window_local', 'currency', 'enabled', 'portfolio_list']:
        val = getattr(payload, field)
        if val is not None:
            update[field] = val
    if not update:
        return acc
    update['updated_at'] = datetime.utcnow()
    await db.accounts.update_one({'external_account_id': external_account_id}, {'$set': update})
    acc_dict = acc.model_dump()
    acc_dict.update(update)
    return Account(**acc_dict)

# Ingest endpoint with idempotency and audit
class IngestResponse(BaseModel):
    job: IngestJob
    note: str

@api_router.post('/ingest/eod/{external_account_id}', response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def trigger_eod_ingest(
    external_account_id: str,
    authorization: Optional[str] = Header(None),
    x_idempotency_key: Optional[str] = Header(default=None, alias='X-Idempotency-Key'),
    date_param: Optional[str] = Query(default=None, alias='date'),  # YYYY-MM-DD
    force: bool = Query(default=False)
):
    await verify_feature_enabled()
    await verify_internal_token(authorization)
    acc = await get_account_by_external(external_account_id)
    if not acc or not acc.enabled:
        raise HTTPException(status_code=404, detail='Account not found or disabled')

    as_of_date = date_param
    idem = x_idempotency_key or f"{external_account_id}_{as_of_date or ''}_{uuid.uuid4().hex[:8]}"

    # Optional artifact hash will come from ETL once files are read; placeholder None now
    artifact_hash = None

    # Idempotency check: if not force, try to find existing by (idempotency_key) or (account_id, as_of_date, artifact_hash)
    if not force:
        existing = await db.ingest_jobs.find_one({'idempotency_key': idem})
        if existing:
            existing['id'] = existing.get('_id', existing.get('id'))
            await _audit_ingest_attempt(acc, as_of_date, artifact_hash, note='idempotent-existing')
            return IngestResponse(job=IngestJob(**{k: v for k, v in existing.items() if k != '_id'}), note='Job already exists for this idempotency key')

    job = IngestJob(account_id=acc.id, idempotency_key=idem, as_of_date=as_of_date, artifact_hash=artifact_hash, status='pending', metadata={'trigger': 'manual'})
    doc = job.model_dump()
    doc['_id'] = doc['id']
    try:
        await db.ingest_jobs.insert_one(doc)
    except Exception:
        existing = await db.ingest_jobs.find_one({'idempotency_key': idem})
        if existing:
            existing['id'] = existing.get('_id', existing.get('id'))
            await _audit_ingest_attempt(acc, as_of_date, artifact_hash, note='idempotent-existing-2')
            return IngestResponse(job=IngestJob(**{k: v for k, v in existing.items() if k != '_id'}), note='Job already exists')
        raise

    await _audit_ingest_attempt(acc, as_of_date, artifact_hash, note='queued')
    return IngestResponse(job=job, note='Ingestion queued (stub). Configure SFTP/S3 to enable processing.')

async def _audit_ingest_attempt(acc: Account, as_of_date: Optional[str], artifact_hash: Optional[str], note: Optional[str]):
    audit = IngestAudit(account_id=acc.id, external_account_id=acc.external_account_id, as_of_date=as_of_date, artifact_hash=artifact_hash, headers_fingerprint={'v': 1}, note=note)
    doc = audit.model_dump(); doc['_id'] = doc['id']
    await db.ingest_audit.insert_one(doc)

# Journal endpoints (v1 scaffolds with pagination)
class JournalDailyPoint(BaseModel):
    date: date
    r: float
    pnl: float
    wins: int = 0
    losses: int = 0
    tagsHistogram: Dict[str, int] = Field(default_factory=dict)

class JournalDailyResponse(BaseModel):
    days: List[JournalDailyPoint]
    summary: Dict[str, float]

@api_router.get('/journal/daily', response_model=JournalDailyResponse)
async def journal_daily(accountId: str, frm: Optional[str] = None, to: Optional[str] = None):
    await verify_feature_enabled()
    q: Dict[str, Any] = {'account_id': accountId}
    if frm or to:
        q['as_of'] = {}
        if frm:
            q['as_of']['$gte'] = frm
        if to:
            q['as_of']['$lte'] = to
    rows = await db.balances_eod.find(q).sort('as_of', 1).to_list(3650)
    days: List[JournalDailyPoint] = []
    for r in rows:
        as_of_val = r['as_of']
        d = datetime.strptime(as_of_val, '%Y-%m-%d').date() if isinstance(as_of_val, str) else as_of_val
        pnl = float(r.get('realized_pnl_day', 0) or 0)
        days.append(JournalDailyPoint(date=d, r=0.0, pnl=pnl))
    total_pnl = sum(p.pnl for p in days)
    summary = {'total_pnl': total_pnl, 'avg_r': 0.0, 'expectancy': 0.0, 'win_rate': 0.0}
    return JournalDailyResponse(days=days, summary=summary)

# Trades with pagination
class TradeItem(BaseModel):
    id: str
    account_id: str
    symbol: str
    r_multiple: float
    net_pnl: float
    fees_total: float
    entered_at: Optional[datetime] = None
    exited_at: Optional[datetime] = None

class TradesListResponse(BaseModel):
    items: List[TradeItem]
    total: int
    nextCursor: Optional[str] = None

@api_router.get('/journal/trades', response_model=TradesListResponse)
async def list_trades(
    accountId: str,
    frm: Optional[str] = None,
    to: Optional[str] = None,
    tag: Optional[str] = None,
    strategy: Optional[str] = None,
    symbol: Optional[str] = None,
    sort: str = 'exit_time_desc',
    limit: int = 100,
    cursor: Optional[str] = None
):
    await verify_feature_enabled()
    q: Dict[str, Any] = {'account_id': accountId}
    if frm or to:
        q['exit_time'] = {}
        if frm: q['exit_time']['$gte'] = frm
        if to: q['exit_time']['$lte'] = to
    if symbol:
        q['symbol'] = symbol
    sort_spec = ('exit_time', -1) if sort.endswith('desc') else ('exit_time', 1)
    docs = await db.trades_net.find(q).sort([sort_spec]).limit(limit).to_list(limit)
    items: List[TradeItem] = []
    for d in docs:
        items.append(TradeItem(
            id=d.get('_id') or d.get('id') or str(uuid.uuid4()),
            account_id=d['account_id'],
            symbol=d.get('symbol', ''),
            r_multiple=float(d.get('r_multiple', 0) or 0),
            net_pnl=float(d.get('net_pnl', 0) or 0),
            fees_total=float(d.get('fees_total', 0) or 0),
            entered_at=d.get('entry_time'),
            exited_at=d.get('exit_time')
        ))
    next_cursor = None
    total = len(items)
    return TradesListResponse(items=items, total=total, nextCursor=next_cursor)

# Changes (diff)
class ChangesResponse(BaseModel):
    openedPositions: List[Dict[str, Any]] = Field(default_factory=list)
    closedPositions: List[Dict[str, Any]] = Field(default_factory=list)
    dividends: List[Dict[str, Any]] = Field(default_factory=list)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)

@api_router.get('/changes', response_model=ChangesResponse)
async def changes(accountId: str, date_param: str = Query(alias='date')):
    await verify_feature_enabled()
    return ChangesResponse()

# Calendar
class CalendarPoint(BaseModel):
    date: date
    pnl: float
    mistakes: int = 0

class CalendarResponse(BaseModel):
    points: List[CalendarPoint]

@api_router.get('/calendar', response_model=CalendarResponse)
async def calendar_heatmap(accountId: str, month: str):
    await verify_feature_enabled()
    year = int(month.split('-')[0]); mon = int(month.split('-')[1])
    rows = await db.balances_eod.find({'account_id': accountId, 'as_of': {'$regex': f'^{year}-{mon:02d}-'}}).to_list(100)
    pts: List[CalendarPoint] = []
    for r in rows:
        pts.append(CalendarPoint(date=datetime.strptime(r['as_of'], '%Y-%m-%d').date() if isinstance(r['as_of'], str) else r['as_of'], pnl=float(r.get('realized_pnl_day', 0) or 0), mistakes=0))
    return CalendarResponse(points=pts)

# Risk overview
class RiskOverview(BaseModel):
    equity_curve: List[Dict[str, Any]]
    drawdown_curve: List[Dict[str, Any]]
    max_drawdown: float

@api_router.get('/risk/overview', response_model=RiskOverview)
async def risk_overview(accountId: str, frm: Optional[str] = None, to: Optional[str] = None):
    await verify_feature_enabled()
    q: Dict[str, Any] = {'account_id': accountId}
    if frm or to:
        q['as_of'] = {}
        if frm: q['as_of']['$gte'] = frm
        if to: q['as_of']['$lte'] = to
    rows = await db.balances_eod.find(q).sort('as_of', 1).to_list(3650)
    equity = []
    max_dd = 0.0
    peak = None
    dd_curve = []
    for r in rows:
        d = datetime.strptime(r['as_of'], '%Y-%m-%d').date() if isinstance(r['as_of'], str) else r['as_of']
        eq = float(r.get('net_equity', 0) or 0)
        equity.append({'date': d.isoformat(), 'value': eq})
        if peak is None or eq > peak:
            peak = eq
        dd = 0.0 if not peak else (eq - peak) / peak
        max_dd = min(max_dd, dd)
        dd_curve.append({'date': d.isoformat(), 'value': dd})
    return RiskOverview(equity_curve=equity, drawdown_curve=dd_curve, max_drawdown=max_dd)

# Journal entry upsert
class JournalEntryUpsert(BaseModel):
    date: date
    text: str
    attachments: Optional[List[Dict[str, Any]]] = None
    accountId: Optional[str] = None

class JournalEntry(BaseModel):
    id: str
    date: date
    text: str
    attachments: Optional[List[Dict[str, Any]]] = None
    accountId: Optional[str] = None

@api_router.post('/journal/entry/upsert', response_model=JournalEntry)
async def upsert_journal_entry(body: JournalEntryUpsert):
    await verify_feature_enabled()
    key = {'account_id': body.accountId or None, 'date': body.date.isoformat()}
    doc = {'account_id': body.accountId or None, 'date': body.date.isoformat(), 'text': body.text, 'attachments': body.attachments or [], 'updated_at': datetime.utcnow()}
    existing = await db.journal_entries.find_one(key)
    if existing:
        await db.journal_entries.update_one(key, {'$set': doc})
        _id = existing.get('_id') or existing.get('id') or str(uuid.uuid4())
    else:
        _id = str(uuid.uuid4())
        await db.journal_entries.insert_one({**doc, '_id': _id, 'id': _id, 'created_at': datetime.utcnow()})
    return JournalEntry(id=_id, date=body.date, text=body.text, attachments=body.attachments or [], accountId=body.accountId)

# Tag apply
class TagApplyRequest(BaseModel):
    executionId: str
    tagName: str

@api_router.post('/journal/tags/apply')
async def apply_tag(req: TagApplyRequest):
    await verify_feature_enabled()
    tag = await db.tags.find_one({'name': req.tagName})
    if not tag:
        tag_id = str(uuid.uuid4())
        await db.tags.insert_one({'_id': tag_id, 'id': tag_id, 'name': req.tagName})
        tag = {'_id': tag_id, 'id': tag_id, 'name': req.tagName}
    key = {'execution_id': req.executionId, 'tag_id': tag['id']}
    existing = await db.execution_tags.find_one(key)
    if not existing:
        await db.execution_tags.insert_one({**key, '_id': str(uuid.uuid4())})
    return {'ok': True}

# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Scheduler helpers
def _parse_hhmm(val: str) -> Tuple[int, int]:
    try:
        hh, mm = val.split(':')
        return int(hh), int(mm)
    except Exception:
        return (22, 30)

async def _schedule_all_accounts():
    docs = await db.accounts.find({'enabled': True}).to_list(100)
    for d in docs:
        acc_id = d.get('_id')
        hh, mm = _parse_hhmm(d.get('ingest_window_local', '22:30'))
        job_id = f"eod_{acc_id}"
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass
        trigger = CronTrigger(hour=hh, minute=mm, timezone=SAST_TZ)
        # NOTE: we will wire this to real ETL later; keep a stub
        scheduler.add_job(lambda: None, trigger=trigger, id=job_id, name=f"EOD Ingest {d['name']}")

@app.on_event("startup")
async def on_startup():
    await ensure_indexes_and_seed()
    global scheduler
    if scheduler is None:
        scheduler = BackgroundScheduler(timezone=SAST_TZ)
        scheduler.start()
    # schedule in background
    import asyncio
    asyncio.create_task(_schedule_all_accounts())

@app.on_event("shutdown")
async def shutdown_db_client():
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
    client.close()