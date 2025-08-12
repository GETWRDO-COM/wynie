from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import csv
import asyncio
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase

from .etl_schemas import OrdersRow, ExecutionsRow, PositionsEODRow, BalancesEODRow, CashEventRow
from .utils_etl import hash_row, sha256_text, artifact_hash_from_files, parse_date_str


async def process_eod_batch(db: AsyncIOMotorDatabase, account_doc: Dict, as_of_date: str, base_dir: Optional[str] = None) -> Dict:
    """
    Process EOD CSVs for the given account and date.
    - Reads files from base_dir/tests/seed_eod/{external_account_id}/{YYYY-MM-DD}/ by default if base_dir not provided.
    - Upserts into domain collections with idempotency via unique keys.
    - Rebuilds trades_net and precomputed collections for the given day.
    Returns summary with artifact_hash and file_audit.
    """
    account_id = account_doc['_id']
    external_account_id = account_doc['external_account_id']
    day = parse_date_str(as_of_date)

    folder = Path(base_dir or '/app/tests/seed_eod') / external_account_id / day
    patterns = [
        ('balances', f'balances_{external_account_id}_{day.replace("-", "")}.csv'),
        ('positions', f'positions_{external_account_id}_{day.replace("-", "")}.csv'),
        ('orders', f'orders_{external_account_id}_{day.replace("-", "")}.csv'),
        ('executions', f'executions_{external_account_id}_{day.replace("-", "")}.csv'),
        ('cash', f'cash_{external_account_id}_{day.replace("-", "")}.csv'),
    ]

    file_audit: List[Dict] = []

    # Parse helpers
    async def _read_csv(file_path: Path) -> List[Dict]:
        rows: List[Dict] = []
        with file_path.open('r', newline='') as f:
            reader = csv.DictReader(f)
            for raw in reader:
                # normalize keys
                norm = { (k or '').strip(): (v or '').strip() for k, v in raw.items() }
                rows.append(norm)
        return rows

    # PROCESS EACH FILE
    present_files: List[str] = []
    file_hashes: List[str] = []

    for kind, fname in patterns:
        path = folder / fname
        if not path.exists():
            file_audit.append({'name': fname, 'bytes': 0, 'row_count': 0, 'file_hash': None, 'warnings': [f'missing {kind} file']})
            continue
        present_files.append(fname)
        rows = await _read_csv(path)
        fh = sha256_text((path.read_text()))
        file_hashes.append(fh)
        row_count = 0
        warnings: List[str] = []

        if kind == 'orders':
            for r in rows:
                try:
                    model = OrdersRow(**r, raw=r)
                    doc = model.model_dump()
                    doc['raw_hash'] = hash_row(r)
                    key = {'account_id': account_id, 'external_order_id': model.external_order_id}
                    await db.orders.update_one(key, {'$set': {**doc, 'account_id': account_id}}, upsert=True)
                    row_count += 1
                except Exception as e:
                    warnings.append(f'orders row error: {e}')
        elif kind == 'executions':
            for r in rows:
                try:
                    model = ExecutionsRow(**r, raw=r)
                    doc = model.model_dump()
                    doc['raw_hash'] = hash_row(r)
                    key = {'account_id': account_id, 'external_execution_id': model.external_execution_id}
                    await db.executions.update_one(key, {'$set': {**doc, 'account_id': account_id}}, upsert=True)
                    row_count += 1
                except Exception as e:
                    warnings.append(f'executions row error: {e}')
        elif kind == 'positions':
            for r in rows:
                try:
                    model = PositionsEODRow(**r, raw=r)
                    doc = model.model_dump()
                    doc['raw_hash'] = hash_row(r)
                    key = {'account_id': account_id, 'as_of': str(model.as_of), 'instrument_id': model.instrument_id}
                    await db.positions_eod.update_one(key, {'$set': {**doc, 'account_id': account_id}}, upsert=True)
                    row_count += 1
                except Exception as e:
                    warnings.append(f'positions row error: {e}')
        elif kind == 'balances':
            for r in rows:
                try:
                    model = BalancesEODRow(**r, raw=r)
                    doc = model.model_dump()
                    doc['raw_hash'] = hash_row(r)
                    key = {'account_id': account_id, 'as_of': str(model.as_of)}
                    await db.balances_eod.update_one(key, {'$set': {**doc, 'account_id': account_id}}, upsert=True)
                    row_count += 1
                except Exception as e:
                    warnings.append(f'balances row error: {e}')
        elif kind == 'cash':
            for r in rows:
                try:
                    model = CashEventRow(**r, raw=r)
                    doc = model.model_dump()
                    doc['raw_hash'] = hash_row(r)
                    key = {'account_id': account_id, 'posted_at': model.posted_at, 'amount': model.amount, 'description': model.description}
                    await db.cash_events.update_one(key, {'$set': {**doc, 'account_id': account_id}}, upsert=True)
                    row_count += 1
                except Exception as e:
                    warnings.append(f'cash row error: {e}')

        file_audit.append({'name': fname, 'bytes': path.stat().st_size, 'row_count': row_count, 'file_hash': fh, 'warnings': warnings})

    # Compute artifact hash
    artifact_hash = artifact_hash_from_files(file_hashes) if file_hashes else None

    # Build trades_net and precomputes for the day
    await _rebuild_trades_for_day(db, account_id, day)
    await _rebuild_precomputes_for_day(db, account_id, day)

    return {'artifact_hash': artifact_hash, 'file_audit': file_audit}


async def _rebuild_trades_for_day(db: AsyncIOMotorDatabase, account_id: str, day: str):
    # Simple FIFO round-trip builder across all executions up to "day" (inclusive)
    # Load executions sorted by filled_at
    execs = await db.executions.find({'account_id': account_id, 'filled_at': {'$lte': datetime.fromisoformat(day + 'T23:59:59')}}).sort('filled_at', 1).to_list(100000)
    lots: Dict[str, List[Dict]] = {}  # instrument_id -> open lots

    trades: List[Dict] = []

    def push_lot(instr: str, lot: Dict):
        lots.setdefault(instr, []).append(lot)

    def pop_fifo(instr: str) -> Optional[Dict]:
        arr = lots.get(instr, [])
        return arr.pop(0) if arr else None

    for ex in execs:
        instr = ex.get('instrument_id') or ex.get('symbol')
        side = (ex.get('side') or '').upper()
        qty = float(ex.get('qty') or 0)
        price = float(ex.get('price') or 0)
        fees = float(ex.get('fees') or 0) + float(ex.get('commission') or 0)
        ts = ex.get('filled_at')
        if side == 'BUY':
            push_lot(instr, {'qty': qty, 'price': price, 'time': ts, 'fees': fees})
        elif side == 'SELL':
            remain = qty
            while remain > 1e-9:
                open_lot = pop_fifo(instr)
                if not open_lot:
                    # short sell or unmatched; treat as opening short (not fully handled)
                    push_lot(instr, {'qty': -remain, 'price': price, 'time': ts, 'fees': fees})
                    remain = 0
                    break
                use = min(remain, open_lot['qty'])
                # trade for the used quantity
                entry_price = open_lot['price']
                exit_price = price
                entry_time = open_lot['time']
                exit_time = ts
                entry_fees = open_lot.get('fees', 0)
                exit_fees = fees * (use / qty) if qty else 0
                gross = (exit_price - entry_price) * use
                net = gross - (entry_fees + exit_fees)
                trade_id = str(uuid.uuid4())
                trade_doc = {
                    '_id': trade_id,
                    'id': trade_id,
                    'account_id': account_id,
                    'instrument_id': instr,
                    'symbol': ex.get('symbol'),
                    'entry_time': entry_time,
                    'exit_time': exit_time,
                    'entry_qty': use,
                    'exit_qty': use,
                    'avg_entry_price': entry_price,
                    'avg_exit_price': exit_price,
                    'gross_pnl': gross,
                    'fees_total': entry_fees + exit_fees,
                    'net_pnl': net,
                    'r_multiple': 0.0,
                }
                trades.append(trade_doc)
                open_lot['qty'] -= use
                remain -= use
                if open_lot['qty'] > 1e-9:
                    # put back remaining lot
                    lots.setdefault(instr, []).insert(0, open_lot)

    # Remove and reinsert trades for this day
    await db.trades_net.delete_many({'account_id': account_id, 'exit_time': {'$gte': datetime.fromisoformat(day + 'T00:00:00'), '$lte': datetime.fromisoformat(day + 'T23:59:59')}})
    if trades:
        await db.trades_net.insert_many(trades)


async def _rebuild_precomputes_for_day(db: AsyncIOMotorDatabase, account_id: str, day: str):
    # risk_equity_daily
    bal = await db.balances_eod.find_one({'account_id': account_id, 'as_of': day})
    if bal:
        eq = float(bal.get('net_equity') or 0)
        # recompute drawdown peak using history
        hist = await db.risk_equity_daily.find({'account_id': account_id}).sort('date', 1).to_list(10000)
        peak = max([h.get('equity', 0) for h in hist] + [eq]) if hist else eq
        dd = 0.0 if peak == 0 else (eq - peak) / peak
        await db.risk_equity_daily.update_one({'account_id': account_id, 'date': day}, {'$set': {'equity': eq, 'dd': dd}}, upsert=True)

    # trades_net_daily + journal_daily_agg
    start = datetime.fromisoformat(day + 'T00:00:00'); end = datetime.fromisoformat(day + 'T23:59:59')
    trades = await db.trades_net.find({'account_id': account_id, 'exit_time': {'$gte': start, '$lte': end}}).to_list(10000)
    await db.trades_net_daily.update_one({'account_id': account_id, 'date': day}, {'$set': {'trades': trades}}, upsert=True)

    pnl_sum = sum(float(t.get('net_pnl') or 0) for t in trades)
    r_vals = [float(t.get('r_multiple') or 0) for t in trades]
    wins = sum(1 for t in trades if float(t.get('net_pnl') or 0) > 0)
    losses = sum(1 for t in trades if float(t.get('net_pnl') or 0) < 0)
    avg_r = (sum(r_vals) / len(r_vals)) if r_vals else 0.0
    win_rate = (wins / len(trades)) if trades else 0.0
    await db.journal_daily_agg.update_one({'account_id': account_id, 'date': day}, {'$set': {'pnl': pnl_sum, 'r': avg_r, 'wins': wins, 'losses': losses, 'tagsHistogram': {}}}, upsert=True)

    # position_flags_daily placeholder
    await db.position_flags_daily.update_one({'account_id': account_id, 'as_of': day}, {'$setOnInsert': {'flags': []}}, upsert=True)