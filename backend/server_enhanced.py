from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, status
# ... (rest of file above unchanged)
# --- Earnings (basic via Polygon financials as proxy) ---
@api_router.get("/earnings")
async def earnings(tickers: Optional[str] = Query(None)):
    api_key = await get_polygon_api_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="Polygon API key not configured")
    base = "https://api.polygon.io"
    out = []
    try:
        if not tickers:
            return {"items": out, "last_updated": datetime.utcnow().isoformat()}
        tlist = [t.strip().upper() for t in tickers.split(',') if t.strip()]
        async with aiohttp.ClientSession() as session:
            async def fetch_one(t):
                # Using financials as rough proxy for most recent earnings filing
                url = f"{base}/v3/reference/financials?ticker={quote(t)}&limit=1&timeframe=quarterly&sort=filing_date&order=desc&apiKey={api_key}"
                try:
                    async with session.get(url, timeout=20) as resp:
                        js = await resp.json()
                    results = js.get('results') or []
                    if results:
                        r = results[0]
                        out.append({
                            "ticker": t,
                            "filing_date": r.get('filing_date'),
                            "period": r.get('period_of_report_date'),
                            "source": "polygon",
                            "link": f"https://polygon.io/stock/{t}/financials"
                        })
                except Exception:
                    pass
            await asyncio.gather(*[fetch_one(t) for t in tlist])
        return {"items": out, "last_updated": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(api_router)