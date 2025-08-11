import React, { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Button } from "../components/ui/button"
import { computeRatings } from "../services/api"
import { getLogo, getQuotes, getBars } from "../services/api"
import { saveColumnPreset } from "../services/api"
import { getColumnSchema } from "../services/api"
import { post } from "../services/api" // not exported; but we did not export post. We'll avoid and use direct call through service.
import axios from "axios"

const BASE = (process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL || "")

export default function ScreenerPanel({ onResults }){
  const [symbolsText, setSymbolsText] = useState("AAPL,MSFT,TSLA,NVDA,AMZN,GOOGL")
  const [minPrice, setMinPrice] = useState(5)
  const [minVol, setMinVol] = useState(500000)
  const [minRSI, setMinRSI] = useState(30)
  const [sortKey, setSortKey] = useState("last")
  const [running, setRunning] = useState(false)

  const run = async () => {
    setRunning(true)
    try {
      const symbols = symbolsText.split(/[,\s]+/).map(s=> s.trim().toUpperCase()).filter(Boolean)
      const payload = {
        symbols,
        filters: [
          { field: 'last', op: '>=', value: Number(minPrice||0) },
          { field: 'volume', op: '>=', value: Number(minVol||0) },
          { field: 'rsi14', op: '>=', value: Number(minRSI||0) },
        ],
        sort: { key: sortKey, dir: 'desc' }
      }
      const { data } = await axios.post(`${BASE}/api/screeners/run`, payload)
      onResults && onResults(data.rows || [])
    } catch (e) {
      onResults && onResults([])
    } finally {
      setRunning(false)
    }
  }

  const applyPresetNewHighs = () => {
    setMinRSI(70); setMinPrice(5); setMinVol(300000)
  }
  const applyPresetRedList = () => {
    setMinRSI(20); setMinPrice(5); setMinVol(100000)
  }

  return (
    <Card>
      <CardHeader className="py-2"><CardTitle className="text-base">Screener</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div>
          <label className="text-sm">Universe (comma or space separated)</label>
          <Input value={symbolsText} onChange={(e)=> setSymbolsText(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <label className="text-sm">Min Price
            <Input type="number" value={minPrice} onChange={(e)=> setMinPrice(e.target.value)} />
          </label>
          <label className="text-sm">Min Volume
            <Input type="number" value={minVol} onChange={(e)=> setMinVol(e.target.value)} />
          </label>
          <label className="text-sm">Min RSI
            <Input type="number" value={minRSI} onChange={(e)=> setMinRSI(e.target.value)} />
          </label>
          <label className="text-sm">Sort By
            <select className="border rounded px-2 py-1 w-full" value={sortKey} onChange={(e)=> setSortKey(e.target.value)}>
              <option value="last">Last</option>
              <option value="changePct">% Chg</option>
              <option value="volume">Volume</option>
            </select>
          </label>
        </div>
        <div className="flex gap-2">
          <Button onClick={run} disabled={running}>{running? 'Running...':'Run Screener'}</Button>
          <Button variant="secondary" onClick={applyPresetNewHighs}>Preset: New Highs</Button>
          <Button variant="secondary" onClick={applyPresetRedList}>Preset: Red List</Button>
        </div>
      </CardContent>
    </Card>
  )
}