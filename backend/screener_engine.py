from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime
from polygon_client import PolygonClient
from finnhub_client import FinnhubClient
from indicators import compute_all_daily

class Cache:
  def __init__(self):
    self.bars: Dict[str, tuple[float, Any]] = {}
    self.metrics: Dict[str, tuple[float, Any]] = {}
    self.fund: Dict[str, tuple[float, Any]] = {}
  def get(self, store: Dict, key: str):
    item = store.get(key)
    if not item: return None
    exp, val = item
    if exp < datetime.utcnow().timestamp():
      store.pop(key, None); return None
    return val
  def set(self, store: Dict, key: str, val: Any, ttl: float):
    store[key] = (datetime.utcnow().timestamp() + ttl, val)

CACHE = Cache()

COMPUTED_FIELDS = {
  "sma20":("daily", lambda m:m.get("sma20")),
  "sma50":("daily", lambda m:m.get("sma50")),
  "sma200":("daily", lambda m:m.get("sma200")),
  "ema8":("daily", lambda m:m.get("ema8")),
  "ema21":("daily", lambda m:m.get("ema21")),
  "ema50":("daily", lambda m:m.get("ema50")),
  "rsi14":("daily", lambda m:m.get("rsi14")),
  "atr14":("daily", lambda m:m.get("atr14")),
  "bb_bw":("daily", lambda m:m.get("bb_bw")),
  "macd_line":("daily", lambda m:m.get("macd_line")),
  "macd_signal":("daily", lambda m:m.get("macd_signal")),
  "macd_hist":("daily", lambda m:m.get("macd_hist")),
  "stoch_k":("daily", lambda m:m.get("stoch_k")),
  "stoch_d":("daily", lambda m:m.get("stoch_d")),
  "avgVol20d":("daily", lambda m:m.get("avgVol20d")),
  "runRate20d":("daily", lambda m:m.get("runRate20d")),
  "relVol":("daily", lambda m:m.get("relVol")),
  "pct_to_hi52":("daily", lambda m:m.get("pct_to_hi52")),
  "pct_above_lo52":("daily", lambda m:m.get("pct_above_lo52")),
  "hi52":("daily", lambda m:m.get("hi52")),
  "lo52":("daily", lambda m:m.get("lo52")),
  "adr20": ("daily", lambda m:m.get("adr20")),
  "gapPct": ("daily", lambda m:m.get("gapPct")),
}

FUND_FIELDS = {
  "marketCap": ("profile", "marketCapitalization"),
  "sharesOutstanding": ("metrics", "sharesoutstanding"),
  "float": ("metrics", "floatShares"),
  "peTTM": ("metrics", "peBasicExclExtraTTM"),
  "psTTM": ("metrics", "psTTM"),
  "pb": ("metrics", "pbAnnual"),
  "roe": ("metrics", "roeTTM"),
  "roa": ("metrics", "roaTTM"),
  "grossMarginTTM": ("metrics", "grossMarginTTM"),
  "operatingMarginTTM": ("metrics", "operatingMarginTTM"),
  "netMarginTTM": ("metrics", "netMarginTTM"),
}

def fetch_daily_bars(poly: PolygonClient, symbol: str) -> List[Dict[str, Any]]:
  key = f"{symbol}:D"
  cached = CACHE.get(CACHE.bars, key)
  if cached is not None: return cached
  to = datetime.utcnow().date().isoformat(); fr = (datetime.utcnow().date().replace(year=datetime.utcnow().year - 1)).isoformat()
  bars = poly.get_bars(symbol, 1, "day", fr, to)
  CACHE.set(CACHE.bars, key, bars, 300)
  return bars

def compute_metrics_daily(poly: PolygonClient, symbol: str) -> Dict[str, Any]:
  key = f"{symbol}:metricsD"
  cached = CACHE.get(CACHE.metrics, key)
  if cached is not None: return cached
  bars = fetch_daily_bars(poly, symbol)
  metrics = compute_all_daily(bars)
  CACHE.set(CACHE.metrics, key, metrics, 120)
  return metrics

def get_fundamentals(fin: FinnhubClient, symbol: str) -> Dict[str, Any]:
  key = f"{symbol}:funds"
  cached = CACHE.get(CACHE.fund, key)
  if cached is not None: return cached
  prof = fin.company_profile(symbol) if fin else {}
  met = fin.metrics(symbol) if fin else {}
  data = {"profile": prof, "metrics": met}
  CACHE.set(CACHE.fund, key, data, 1800)
  return data

# Helpers

def eval_condition(value, op: str, target):
  if value is None: return False
  if op in (">", "gt"): return value > target
  if op in (">=", "gte"): return value >= target
  if op in ("<", "lt"): return value < target
  if op in ("<=", "lte"): return value <= target
  if op in ("==", "eq"): return value == target
  if op in ("!=", "ne"): return value != target
  if op == "between" and isinstance(target, list) and len(target) == 2: return target[0] <= value <= target[1]
  if op == "in" and isinstance(target, list): return value in target
  return False


def get_field_value(symbol: str, row: Dict[str, Any], field: str, poly: PolygonClient, fin: FinnhubClient | None):
  if field in row: return row.get(field)
  if field == "liquidity":
    last = row.get("last"); vol = row.get("volume")
    try:
      return (last or 0) * (vol or 0)
    except Exception:
      return None
  if field in COMPUTED_FIELDS:
    _, fn = COMPUTED_FIELDS[field]
    return fn(compute_metrics_daily(poly, symbol))
  if field in FUND_FIELDS and fin:
    data = get_fundamentals(fin, symbol)
    src, key = FUND_FIELDS[field]
    return data.get(src, {}).get(key)
  if field == "sma50_above_sma200":
    m = compute_metrics_daily(poly, symbol); a = m.get("sma50"); b = m.get("sma200"); return (a is not None and b is not None and a > b)
  if field == "ema8_above_ema21":
    m = compute_metrics_daily(poly, symbol); a = m.get("ema8"); b = m.get("ema21"); return (a is not None and b is not None and a > b)
  if field == "macd_cross_up":
    m = compute_metrics_daily(poly, symbol); a = m.get("macd_line"); b = m.get("macd_signal"); return (a is not None and b is not None and a > b)
  if field == "macd_cross_down":
    m = compute_metrics_daily(poly, symbol); a = m.get("macd_line"); b = m.get("macd_signal"); return (a is not None and b is not None and a < b)
  return None


def eval_filters(symbol: str, row: Dict[str, Any], flt: Dict[str, Any], poly: PolygonClient, fin: FinnhubClient | None) -> bool:
  if "field" in flt:
    v = get_field_value(symbol, row, flt["field"], poly, fin)
    op = flt.get("op")
    val = flt.get("value")
    # cast string inputs to numbers when possible
    try:
      if isinstance(val, str) and val.strip() != "":
        if "." in val or "e" in val.lower():
          val = float(val)
        else:
          val = int(val)
    except Exception:
      pass
    return eval_condition(v, op, val)
  logic = (flt.get("logic") or "AND").upper()
  subs = flt.get("filters") or []
  if not subs: return True
  if logic == "AND": return all(eval_filters(symbol, row, s, poly, fin) for s in subs)
  else: return any(eval_filters(symbol, row, s, poly, fin) for s in subs)


def run_screener(poly: PolygonClient, fin: FinnhubClient | None, symbols: List[str], filters: List[Dict[str, Any]] | Dict[str, Any], sort: Dict[str, str] | None) -> List[Dict[str, Any]]:
  quotes = poly.get_quotes_snapshot(symbols)
  rows = {q["symbol"]: {"symbol": q["symbol"], "last": q.get("last"), "changePct": q.get("changePct"), "volume": q.get("volume")} for q in quotes}
  root = {"logic": "AND", "filters": filters} if isinstance(filters, list) else (filters or {"logic": "AND", "filters": []})
  out: List[Dict[str, Any]] = []
  for s in symbols:
    r = rows.get(s) or {"symbol": s}
    if eval_filters(s, r, root, poly, fin):
      out.append(r)
  if sort and sort.get("key"):
    k = sort["key"]; d = sort.get("dir", "desc")
    out.sort(key=lambda x: (x.get(k) is None, x.get(k)), reverse=(d == "desc"))
  return out