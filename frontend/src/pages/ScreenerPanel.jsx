import React, { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Button } from "../components/ui/button"
import { getScreenerFilters, runScreener } from "../services/api"
import QueryBuilder from "../components/QueryBuilder"
import PresetsBar from "../components/PresetsBar"

export default function ScreenerPanel({ onResults }){
  const [registry, setRegistry] = useState(null)
  const [symbolsText, setSymbolsText] = useState("AAPL MSFT TSLA NVDA AMZN GOOGL META AMD NFLX AVGO")
  const [query, setQuery] = useState({ filters: [{ field: 'last', op: '>=', value: 5 }] })
  const [sortKey, setSortKey] = useState("last")
  const [running, setRunning] = useState(false)

  useEffect(()=>{ (async()=>{ try { const r = await getScreenerFilters(); setRegistry(r) } catch {} })() }, [])

  const applyPreset = (id)=>{
    if (id==='newHighs') setQuery({ filters: [{ field: 'pct_to_hi52', op: '<=', value: 2 }] })
    if (id==='redList') setQuery({ filters: [{ field: 'changePct', op: '<=', value: -2 }] })
    if (id==='leaders') setQuery({ filters: [{ field: 'RS', op: '>=', value: 90 }] })
    if (id==='vcp') setQuery({ filters: [{ field: 'bb_bw', op: '<=', value: 0.1 }] })
    if (id==='breakouts') setQuery({ filters: [{ field: 'pct_to_hi52', op: '<=', value: 1 }] })
    if (id==='pullbacks') setQuery({ filters: [{ field: 'sma50', op: '>=', value: 0 }] })
    if (id==='earnings') setQuery({ filters: [{ field: 'marketCap', op: '>=', value: 1000000000 }] })
  }

  const run = async () => {
    setRunning(true)
    try {
      const symbols = symbolsText.split(/[ ,\n\t]+/).map(s=> s.trim().toUpperCase()).filter(Boolean)
      const payload = { symbols, filters: query.filters, sort: { key: sortKey, dir: 'desc' }, page: { limit: 200 } }
      const data = await runScreener(payload)
      onResults && onResults(data.rows || [])
    } catch (e) {
      onResults && onResults([])
    } finally {
      setRunning(false)
    }
  }

  return (
    <Card>
      <CardHeader className="py-2"><CardTitle className="text-base">Screener</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-sm">Universe (space/comma separated)</label>
          <Input value={symbolsText} onChange={(e)=> setSymbolsText(e.target.value)} />
        </div>
        <PresetsBar onApply={applyPreset} />
        <QueryBuilder registry={registry} query={query} setQuery={setQuery} />
        <div className="flex items-center gap-3">
          <label className="text-sm">Sort By</label>
          <select className="border rounded px-2 py-1" value={sortKey} onChange={(e)=> setSortKey(e.target.value)}>
            <option value="last">Last</option>
            <option value="changePct">% Chg</option>
            <option value="volume">Volume</option>
            <option value="RS">RS</option>
          </select>
          <Button onClick={run} disabled={running}>{running? 'Running...':'Run Screener'}</Button>
        </div>
      </CardContent>
    </Card>
  )
}