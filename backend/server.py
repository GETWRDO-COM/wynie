<file>
<absolute_file_name>/app/backend/server.py</absolute_file_name>
<content_insert>
<![CDATA[
AFTER_LINE:1035

@api_router.get("/earnings")
async def earnings(tickers: str | None = Query(None), days_ahead: int = Query(30)):
    """Finnhub earnings calendar. If tickers provided, fetch per symbol within next N days; otherwise today's calendar.
    Returns items: [{ticker, date, time, period, estimate, actual, surprise, link}]"""
    api_key = os.environ.get('FINNHUB_API_KEY')
    if not api_key:
        raise HTTPException(status_code=400, detail="Finnhub API key not configured")
    try:
        base = "https://finnhub.io/api/v1/calendar/earnings"
        today = datetime.utcnow().date()
        to = today + timedelta(days=days_ahead)
        out = []
        async with aiohttp.ClientSession() as session:
            if tickers:
                syms = [s.strip().upper() for s in tickers.split(',') if s.strip()][:20]
                for s in syms:
                    url = f"{base}?symbol={quote(s)}&from={today}&to={to}&token={api_key}"
                    try:
                        async with session.get(url, timeout=20) as resp:
                            js = await resp.json()
                        for r in js.get('earningsCalendar', []):
                            out.append({
                                "ticker": r.get('symbol') or s,
                                "date": r.get('date'),
                                "time": r.get('hour') or r.get('time'),
                                "period": r.get('quarter'),
                                "estimate": r.get('epsEstimate'),
                                "actual": r.get('epsActual'),
                                "surprise": r.get('epsSurprise'),
                                "link": f"https://finnhub.io/stock/{s}"
                            })
                    except Exception:
                        continue
            else:
                url = f"{base}?from={today}&to={to}&token={api_key}"
                async with session.get(url, timeout=20) as resp:
                    js = await resp.json()
                for r in js.get('earningsCalendar', []):
                    out.append({
                        "ticker": r.get('symbol'),
                        "date": r.get('date'),
                        "time": r.get('hour') or r.get('time'),
                        "period": r.get('quarter'),
                        "estimate": r.get('epsEstimate'),
                        "actual": r.get('epsActual'),
                        "surprise": r.get('epsSurprise'),
                        "link": f"https://finnhub.io/stock/{r.get('symbol')}"
                    })
        return {"items": out[:50], "last_updated": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Normalize market score output shape
@api_router.get("/market-score")
async def get_market_score_normalized():
    try:
        scores = await db.market_scores.find().sort("date", -1).limit(1).to_list(1)
        if not scores:
            # Default
            now = datetime.utcnow().isoformat()
            default = {
                "score": 16,
                "trend": "Yellow Day",
                "recommendation": "Selective entries. Use moderate position sizing.",
                "last_updated": now,
                # keep original fields for compatibility
                "total_score": 16,
                "classification": "Yellow Day",
                "date": now
            }
            await db.market_scores.insert_one(default)
            return default
        doc = scores[0]
        score = doc.get('score') or doc.get('total_score')
        trend = doc.get('trend') or doc.get('classification')
        last_updated = doc.get('last_updated') or doc.get('date') or datetime.utcnow().isoformat()
        recommendation = doc.get('recommendation')
        normalized = { **doc, "score": score, "trend": trend, "last_updated": last_updated, "recommendation": recommendation }
        return normalized
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
]]>
</content_insert>
</file>