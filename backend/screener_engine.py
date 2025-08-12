from __future__ import annotations
from typing import List, Dict, Any, Callable
from datetime import datetime, timedelta
from polygon_client import PolygonClient
from indicators import compute_all_daily

# Simple TTL cache for bars and computed metrics
class Cache:
    def __init__(self):
        self.bars: Dict[str, tuple[float, Any]] = {}
        self.metrics: Dict[str, tuple[float, Any]] = {}

    def get(self, store: Dict, key: str, ttl: float):
        item = store.get(key)
        if not item:
            return None
        exp, val = item
        if exp < datetime.utcnow().timestamp():
            store.pop(key, None)
            return None
        return val

    def set(self, store: Dict, key: str, val: Any, ttl: float):
        store[key] = (datetime.utcnow().timestamp() + ttl, val)

CACHE = Cache()

# Registry of computed fields mapping
COMPUTED_FIELDS = {
    # computed from daily bars
    "sma20": ("daily", lambda m: m.get("sma20")),
    "sma50": ("daily", lambda m: m.get("sma50")),
    "sma200": ("daily", lambda m: m.get("sma200")),
    "ema8": ("daily", lambda m: m.get("ema8")),
    "ema21": ("daily", lambda m: m.get("ema21")),
    "ema50": ("daily", lambda m: m.get("ema50")),
    "rsi14": ("daily", lambda m: m.get("rsi14")),
    "atr14": ("daily", lambda m: m.get("atr14")),
    "bb_bw": ("daily", lambda m: m.get("bb_bw")),
    "stoch_k": ("daily", lambda m: m.get("stoch_k")),
    "avgVol20d": ("daily", lambda m: m.get("avgVol20d")),
    "runRate20d": ("daily", lambda m: m.get("runRate20d")),
    "relVol": ("daily", lambda m: m.get("relVol")),
    "pct_to_hi52": ("daily", lambda m: m.get("pct_to_hi52")),
    "pct_above_lo52": ("daily", lambda m: m.get("pct_above_lo52")),
}


def fetch_daily_bars(poly: PolygonClient, symbol: str) -> List[Dict[str, Any]]:
    cached = CACHE.get(CACHE.bars, f"{symbol}:D", 0)
    if cached is not None:
        return cached
    to = datetime.utcnow().date().isoformat()
    fr = (datetime.utcnow().date().replace(year=datetime.utcnow().year - 1)).isoformat()
    bars = poly.get_bars(symbol, 1, "day", fr, to)
    CACHE.set(CACHE.bars, f"{symbol}:D", bars, 300)  # 5min
    return bars


def compute_metrics_daily(poly: PolygonClient, symbol: str) -> Dict[str, Any]:
    cached = CACHE.get(CACHE.metrics, f"{symbol}:D", 0)
    if cached is not None:
        return cached
    bars = fetch_daily_bars(poly, symbol)
    metrics = compute_all_daily(bars)
    CACHE.set(CACHE.metrics, f"{symbol}:D", metrics, 120)  # 2min cache
    return metrics


# Screener evaluator with AND/OR grouping

def eval_condition(value, op: str, target):
    if value is None:
        return False
    if op in (">", "gt"):
        return value > target
    if op in (">=", "gte"):
        return value >= target
    if op in ("<", "lt"):
        return value < target
    if op in ("<=", "lte"):
        return value <= target
    if op == "between" and isinstance(target, list) and len(target) == 2:
        return target[0] <= value <= target[1]
    if op == "in" and isinstance(target, list):
        return value in target
    return False


def get_field_value(symbol: str, row: Dict[str, Any], field: str, poly: PolygonClient):
    # quote fields come from row; computed fields from metrics
    if field in row:
        return row.get(field)
    if field in COMPUTED_FIELDS:
        layer, fn = COMPUTED_FIELDS[field]
        metrics = compute_metrics_daily(poly, symbol)
        return fn(metrics)
    # derived booleans
    if field == "sma50_above_sma200":
        m = compute_metrics_daily(poly, symbol)
        a = m.get("sma50")
        b = m.get("sma200")
        return (a is not None and b is not None and a > b)
    if field == "ema8_above_ema21":
        m = compute_metrics_daily(poly, symbol)
        a = m.get("ema8"); b = m.get("ema21")
        return (a is not None and b is not None and a > b)
    return None


def eval_filters(symbol: str, row: Dict[str, Any], flt: Dict[str, Any], poly: PolygonClient) -> bool:
    # leaf
    if "field" in flt:
        v = get_field_value(symbol, row, flt["field"], poly)
        return eval_condition(v, flt.get("op"), flt.get("value"))
    # group
    logic = (flt.get("logic") or "AND").upper()
    subs = flt.get("filters") or []
    if not subs:
        return True
    if logic == "AND":
        return all(eval_filters(symbol, row, s, poly) for s in subs)
    else:
        return any(eval_filters(symbol, row, s, poly) for s in subs)


def run_screener(poly: PolygonClient, symbols: List[str], filters: List[Dict[str, Any]] | Dict[str, Any], sort: Dict[str, str] | None) -> List[Dict[str, Any]]:
    # get quotes snapshot first
    quotes = poly.get_quotes_snapshot(symbols)
    rows = {q["symbol"]: {
        "symbol": q["symbol"],
        "last": q.get("last"),
        "changePct": q.get("changePct"),
        "volume": q.get("volume"),
    } for q in quotes}

    # build filter root as group if list provided
    root = {"logic": "AND", "filters": filters} if isinstance(filters, list) else (filters or {"logic": "AND", "filters": []})

    out: List[Dict[str, Any]] = []
    for s in symbols:
        r = rows.get(s) or {"symbol": s}
        if eval_filters(s, r, root, poly):
            out.append(r)

    if sort and sort.get("key"):
        k = sort["key"]; d = sort.get("dir", "desc")
        out.sort(key=lambda x: (x.get(k) is None, x.get(k)), reverse=(d == "desc"))
    return out