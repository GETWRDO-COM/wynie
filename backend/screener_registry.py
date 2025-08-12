from __future__ import annotations
from typing import List, Dict

# Expanded registry for screener fields
REGISTRY: List[Dict] = [
  # General
  {"id": "symbol", "label": "Symbol", "category": "General", "type": "string", "source": "provider"},

  # Price & Volume
  {"id": "last", "label": "Last", "category": "Price & Volume", "type": "number", "source": "provider"},
  {"id": "changePct", "label": "% Change", "category": "Price & Volume", "type": "number", "source": "computed"},
  {"id": "volume", "label": "Volume", "category": "Price & Volume", "type": "number", "source": "provider"},
  {"id": "avgVol20d", "label": "Avg Vol (20d)", "category": "Price & Volume", "type": "number", "source": "computed"},
  {"id": "runRate20d", "label": "Run Rate (20d)", "category": "Price & Volume", "type": "number", "source": "computed"},
  {"id": "relVol", "label": "Relative Volume", "category": "Price & Volume", "type": "number", "source": "computed"},
  {"id": "pct_to_hi52", "label": "% to 52w High", "category": "Price & Volume", "type": "number", "source": "computed"},
  {"id": "pct_above_lo52", "label": "% above 52w Low", "category": "Price & Volume", "type": "number", "source": "computed"},
  {"id": "adr20", "label": "ADR(20)", "category": "Price & Volume", "type": "number", "source": "computed"},

  # Technicals
  {"id": "sma20", "label": "SMA 20", "category": "Technicals", "type": "number", "source": "computed"},
  {"id": "sma50", "label": "SMA 50", "category": "Technicals", "type": "number", "source": "computed"},
  {"id": "sma200", "label": "SMA 200", "category": "Technicals", "type": "number", "source": "computed"},
  {"id": "ema8", "label": "EMA 8", "category": "Technicals", "type": "number", "source": "computed"},
  {"id": "ema21", "label": "EMA 21", "category": "Technicals", "type": "number", "source": "computed"},
  {"id": "ema50", "label": "EMA 50", "category": "Technicals", "type": "number", "source": "computed"},
  {"id": "rsi14", "label": "RSI 14", "category": "Technicals", "type": "number", "source": "computed"},
  {"id": "atr14", "label": "ATR 14", "category": "Technicals", "type": "number", "source": "computed"},
  {"id": "bb_bw", "label": "Bollinger BW", "category": "Technicals", "type": "number", "source": "computed"},
  {"id": "stoch_k", "label": "Stoch %K", "category": "Technicals", "type": "number", "source": "computed"},

  # Signals
  {"id": "sma50_above_sma200", "label": "SMA50 > SMA200", "category": "Signals", "type": "boolean", "source": "computed"},
  {"id": "ema8_above_ema21", "label": "EMA8 > EMA21", "category": "Signals", "type": "boolean", "source": "computed"},

  # Proprietary
  {"id": "RS", "label": "RS", "category": "Proprietary Ratings", "type": "number", "source": "computed"},
  {"id": "AS", "label": "AS", "category": "Proprietary Ratings", "type": "number", "source": "computed"},

  # Fundamentals (Finnhub)
  {"id": "marketCap", "label": "Market Cap", "category": "Fundamentals", "type": "number", "source": "finnhub"},
  {"id": "sharesOutstanding", "label": "Shares Out", "category": "Fundamentals", "type": "number", "source": "finnhub"},
  {"id": "float", "label": "Float", "category": "Fundamentals", "type": "number", "source": "finnhub"},
  {"id": "peTTM", "label": "P/E (ttm)", "category": "Fundamentals", "type": "number", "source": "finnhub"},
  {"id": "psTTM", "label": "P/S (ttm)", "category": "Fundamentals", "type": "number", "source": "finnhub"},
  {"id": "pb", "label": "P/B", "category": "Fundamentals", "type": "number", "source": "finnhub"},
  {"id": "roe", "label": "ROE", "category": "Fundamentals", "type": "number", "source": "finnhub"},
  {"id": "roa", "label": "ROA", "category": "Fundamentals", "type": "number", "source": "finnhub"},
  {"id": "grossMarginTTM", "label": "Gross Margin TTM", "category": "Fundamentals", "type": "number", "source": "finnhub"},
  {"id": "operatingMarginTTM", "label": "Operating Margin TTM", "category": "Fundamentals", "type": "number", "source": "finnhub"},
  {"id": "netMarginTTM", "label": "Net Margin TTM", "category": "Fundamentals", "type": "number", "source": "finnhub"},
]