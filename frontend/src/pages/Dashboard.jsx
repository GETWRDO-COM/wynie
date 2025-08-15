import React, { useEffect, useMemo, useState } from "react"
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import DataTable from "../components/DataTable"
import ColumnSettings from "../components/ColumnSettings"
import ScreenerPanel from "./ScreenerPanel"
import { getBars, getQuotes, computeRatings, getColumnSchema, getColumnPresets, saveColumnPreset, getFundamentals } from "../services/api"
import { Settings2, Pencil, Eraser, BellPlus } from "lucide-react"
import useQuotesWS from "../hooks/useQuotesWS"
import { LS } from "../mock/mock"
import TVToolbar from "../components/TVToolbar"
import MiniListPanel from "../components/MiniListPanel"
import NotificationsBell from "../components/NotificationsBell"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select"
import axios from "axios"
import WatchlistsPanel from "../components/WatchlistsPanel"
import { Avatar, AvatarImage, AvatarFallback } from "../components/ui/avatar"

const BASE = (process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL || "")

function useLocalState(key, initial) {
  const [v, setV] = useState(()=> LS.get(key, initial))
  useEffect(()=> { LS.set(key, v) }, [key, v])
  return [v, setV]
}

function CandleChart({ symbol, companyName, drawings, setDrawings, tool, setTool }) {
  const [bars, setBars] = useState([])
  useEffect(()=>{
    let cancelled = false
    ;(async()=>{
      try {
        const to = new Date().toISOString().slice(0,10)
        const from = new Date(new Date().setFullYear(new Date().getFullYear()-1)).toISOString().slice(0,10)
        const d = await getBars(symbol, '1D', from, to)
        if (!cancelled) setBars(d.bars||[])
      } catch { setBars([]) }
    })()
    return ()=>{ cancelled = true }
  }, [symbol])

  const W = 820, H = 420, PAD = 40
  const highs = bars.map(c=> c.h), lows = bars.map(c=> c.l)
  const maxP = highs.length? Math.max(...highs) : 100
  const minP = lows.length? Math.min(...lows) : 0
  const x = (i) => PAD + (i * (W - PAD*2)) / Math.max(1,(bars.length - 1))
  const y = (p) => H - PAD - ((p - minP) / Math.max(1,(maxP - minP))) * (H - PAD*2)

  const [temp, setTemp] = useState(null)

  function onDown(e){ if (tool!=='line') return; const rect = e.currentTarget.getBoundingClientRect(); const p = { x: e.clientX - rect.left, y: e.clientY - rect.top }; setTemp({ start: p, end: p }) }
  function onMove(e){ if(!temp) return; const r=e.currentTarget.getBoundingClientRect(); const p={x:e.clientX-r.left,y:e.clientY-r.top}; setTemp(prev=> ({...prev, end:p})) }
  function onUp(){ if(!temp) return; setDrawings(prev => ({...prev, [symbol]: [...(prev[symbol]||[]), temp]})); setTemp(null) }
  function clear(){ setDrawings(prev => ({...prev, [symbol]: []})) }

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between py-2">
        <CardTitle className="text-base flex items-center gap-2">
          <Avatar className="w-5 h-5 bg-white ring-1 ring-black/10 dark:ring-white/10 rounded-full overflow-hidden">
            <AvatarImage className="object-contain p-0.5" src={`${BASE}/api/marketdata/logo_image?symbol=${symbol}`} alt={symbol} />
            <AvatarFallback className="text-[10px] text-black bg-white">{symbol?.slice(0,2)}</AvatarFallback>
          </Avatar>
          {symbol} {companyName ? `— ${companyName}` : ''} • Chart
        </CardTitle>
        <div className="flex items-center gap-2">
          <Button size="sm" variant={tool==='line'? 'default':'secondary'} onClick={()=> setTool('line')}><Pencil className="w-4 h-4 mr-1"/>Line</Button>
          <Button size="sm" variant="secondary" onClick={clear}><Eraser className="w-4 h-4 mr-1"/>Clear</Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex">
          <TVToolbar tool={tool} setTool={setTool} />
          <svg width={W} height={H} onMouseDown={onDown} onMouseMove={onMove} onMouseUp={onUp} className="bg-background border rounded ml-2">
            <line x1={PAD} y1={PAD} x2={PAD} y2={H-PAD} stroke="#444" />
            <line x1={PAD} y1={H-PAD} x2={W-PAD} y2={H-PAD} stroke="#444" />
            {bars.map((c, i)=>{
              const cx = x(i)
              const top = y(Math.max(c.o,c.c))
              const bottom = y(Math.min(c.o,c.c))
              const color = c.c >= c.o ? "#10b981" : "#ef4444"
              return (
                <g key={i}>
                  <line x1={cx} x2={cx} y1={y(c.h)} y2={y(c.l)} stroke={color} />
                  <rect x={cx-3} width={6} y={top} height={Math.max(2, bottom-top)} fill={color} />
                </g>
              )
            })}
            {(drawings[symbol]||[]).map((d, idx)=> (
              <line key={idx} x1={d.start.x} y1={d.start.y} x2={d.end.x} y2={d.end.y} stroke="#60a5fa" strokeWidth="2" />
            ))}
            {temp && <line x1={temp.start.x} y1={temp.start.y} x2={temp.end.x} y2={temp.end.y} stroke="#38bdf8" strokeDasharray="4 4" />}
          </svg>
        </div>
      </CardContent>
    </Card>
  )
}

export default function Dashboard() {
  const [rows, setRows] = useState([])
  const [selected, setSelected] = useLocalState("selectedSymbol", "AAPL")
  const [visibleColumns, setVisibleColumns] = useLocalState("visibleColumns", ["symbol","last","changePct","volume","avgVol20d","runRate20d","sma20","sma50","sma200","rsi14","marketCap","peTTM","RS","AS"]) 
  const [miniColumns, setMiniColumns] = useLocalState("miniColumns", ["symbol","last","changePct","volume","RS","AS"]) 
  const [sort, setSort] = useState({ key: "RS", dir: "desc" })
  const [miniSort, setMiniSort] = useState({ key: "changePct", dir: "desc" })
  const [rsWindow, setRsWindow] = useLocalState("rsWindow", 63)
  const [asShort, setAsShort] = useLocalState("asShort", 21)
  const [asLong, setAsLong] = useLocalState("asLong", 63)
  const [watchSymbols, setWatchSymbols] = useLocalState("watchlist_default", ["AAPL","MSFT","NVDA","AMZN","GOOGL"]) 
  const [query, setQuery] = useState("")
  const [openCol, setOpenCol] = useState(false)
  const [presets, setPresets] = useState({})
  const [drawings, setDrawings] = useLocalState("drawings", {})
  const [logos, setLogos] = useLocalState("logos", {})
  const [names, setNames] = useLocalState("companyNames", {})
  const [columnDefs, setColumnDefs] = useState([])
  const [tool, setTool] = useLocalState("tool", "line")
  const [density, setDensity] = useLocalState("rowDensity", "compact")

  const quotesMap = useQuotesWS(watchSymbols)

  useEffect(()=>{ (async()=>{
    try{ const s = await getColumnSchema(); const cols = s.categories.flatMap(g=> g.columns); setColumnDefs(cols) } catch {}
    try{ const p = await getColumnPresets(); setPresets(p) } catch {}
  })() }, [])

  useEffect(()=>{
    (async()=>{
      try{
        const csv = watchSymbols.join(',')
        const q = await getQuotes(csv)
        const fmap = await getFundamentals(csv).catch(()=>({data:{}}))
        const f = fmap.data || {}
        const map = {}
        const nextNames = {...names}
        q.quotes.forEach(it => { map[it.symbol] = it })
        const data = watchSymbols.map(sym => ({
          symbol: sym,
          description: `${sym} Inc.`,
          last: map[sym]?.last ?? null,
          changePct: map[sym]?.changePct ?? null,
          volume: map[sym]?.volume ?? null,
          avgVol20d: null,
          runRate20d: null,
          rsi14: null,
          sma20: null, sma50: null, sma200: null,
          marketCap: f[sym]?.marketCap ?? null,
          peTTM: f[sym]?.peTTM ?? null,
        }))
        Object.keys(f).forEach(s => { if (f[s]?.companyName) nextNames[s] = f[s].companyName })
        setNames(nextNames)
        setRows(data)
      } catch(e){ console.error(e) }
    })()
  }, [watchSymbols])

  useEffect(()=>{
    if (!quotesMap || Object.keys(quotesMap).length===0) return
    setRows(prev => prev.map(r => {
      const q = quotesMap[r.symbol]
      if (!q) return r
      return { ...r, last: q.last ?? r.last, changePct: q.changePct ?? r.changePct, volume: q.volume ?? r.volume }
    }))
  }, [quotesMap])

  useEffect(()=>{
    (async()=>{
      try{ const r = await computeRatings({ symbols: watchSymbols, rsWindowDays: rsWindow, asShortDays: asShort, asLongDays: asLong })
        setRows(prev => prev.map(row => ({...row, RS: r.RS?.[row.symbol] ?? row.RS, AS: r.AS?.[row.symbol] ?? row.AS })))
      }catch(e){ console.warn('ratings compute failed', e) }
    })()
  }, [rsWindow, asShort, asLong, watchSymbols])

  // Build proxied logo URLs to avoid CORS
  useEffect(()=>{
    (async()=>{
      const next = {...logos}
      for (const s of watchSymbols) {
        next[s] = `${BASE}/api/marketdata/logo_image?symbol=${s}`
      }
      setLogos(next)
    })()
  }, [watchSymbols])

  const filteredRows = useMemo(()=> {
    return query ? rows.filter(r => r.symbol.toLowerCase().includes(query.toLowerCase())) : rows
  }, [rows, query])

  const onAddSymbol = (sym)=>{
    const s = sym.toUpperCase().trim()
    if (!s) return
    if (!watchSymbols.includes(s)) setWatchSymbols([...watchSymbols, s])
  }

  const savePreset = async (name)=>{ if(!name) return; try { await saveColumnPreset(name, visibleColumns); setPresets(prev=> ({...prev, [name]: visibleColumns})) } catch { setPresets(prev=> ({...prev, [name]: visibleColumns})) } }
  const loadPreset = (name)=>{ if(!name) return; const cols = presets[name]; if (cols) setVisibleColumns(cols) }
  const resetRecommended = ()=> setVisibleColumns(["symbol","last","changePct","volume","avgVol20d","runRate20d","sma20","sma50","sma200","rsi14","marketCap","peTTM","RS","AS"])

  const onEdit = (symbol, key, value)=>{ setRows(prev => prev.map(r => r.symbol===symbol ? ({...r, [key]: value}) : r)) }

  async function createAlert(type){
    try {
      const value = prompt(type==='pct_change_ge' ? 'Enter % change threshold (e.g. 5 for +5%)' : 'Enter price level')
      if (!value) return
      await axios.post(`${BASE}/api/alerts`, { symbol: selected, type, value: parseFloat(value) })
      alert('Alert created')
    } catch (e) { alert('Failed to create alert') }
  }

  return (
    <div className="h-screen w-full flex flex-col">
      <header className="h-12 border-b px-4 flex items-center justify-between bg-card">
        <div className="font-semibold">Market Workstation</div>
        <div className="flex items-center gap-3 text-sm">
          <NotificationsBell />
          <div className="flex items-center gap-2">
            <label>RS</label>
            <Select value={String(rsWindow)} onValueChange={(v)=> setRsWindow(parseInt(v))}>
              <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="21">1M</SelectItem>
                <SelectItem value="63">3M</SelectItem>
                <SelectItem value="126">6M</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <label>AS</label>
            <Select value={String(asShort)} onValueChange={(v)=> setAsShort(parseInt(v))}>
              <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10d</SelectItem>
                <SelectItem value="21">21d</SelectItem>
                <SelectItem value="30">30d</SelectItem>
              </SelectContent>
            </Select>
            <Select value={String(asLong)} onValueChange={(v)=> setAsLong(parseInt(v))}>
              <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="42">42d</SelectItem>
                <SelectItem value="63">63d</SelectItem>
                <SelectItem value="90">90d</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Select value={density} onValueChange={setDensity}>
            <SelectTrigger className="w-32"><SelectValue placeholder="Density" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="compact">Compact</SelectItem>
              <SelectItem value="cozy">Cozy</SelectItem>
              <SelectItem value="comfortable">Comfortable</SelectItem>
            </SelectContent>
          </Select>
          <Button size="sm" variant="secondary" onClick={()=> setOpenCol(true)}><Settings2 className="w-4 h-4 mr-1"/>Columns</Button>
        </div>
      </header>

      <PanelGroup direction="vertical" className="flex-1">
        <Panel defaultSize={58} minSize={40}>
          <div className="h-full grid grid-cols-12 gap-3 p-3">
            <div className="col-span-8 h-full">
              <div className="flex items-center gap-2 mb-2">
                <Button size="sm" variant="secondary" onClick={()=> createAlert('price_above')}><BellPlus className="w-4 h-4 mr-1"/>Price Above</Button>
                <Button size="sm" variant="secondary" onClick={()=> createAlert('price_below')}><BellPlus className="w-4 h-4 mr-1"/>Price Below</Button>
                <Button size="sm" variant="secondary" onClick={()=> createAlert('pct_change_ge')}><BellPlus className="w-4 h-4 mr-1"/>% Change ≥</Button>
              </div>
              <CandleChart symbol={selected} companyName={names[selected]} drawings={drawings} setDrawings={setDrawings} tool={tool} setTool={setTool} />
            </div>
            <div className="col-span-4 h-full space-y-3 overflow-auto pr-1">
              <ScreenerPanel onResults={(rows)=> setRows(rows)} />
              <WatchlistsPanel onUseSymbols={(syms)=> setWatchSymbols(syms)} />
              <MiniListPanel title="Live List" rows={filteredRows} columnDefs={columnDefs} visibleColumns={miniColumns} onColumnsClick={()=> setOpenCol(true)} sort={miniSort} setSort={setMiniSort} onRowClick={(r)=> setSelected(r.symbol)} onEdit={onEdit} logos={logos} />
            </div>
          </div>
        </Panel>
        <PanelResizeHandle className="h-1 bg-border" />
        <Panel defaultSize={42} minSize={30}>
          <div className="h-full p-3">
            <DataTable rows={filteredRows} columnDefs={columnDefs} visibleColumns={visibleColumns} onColumnsClick={()=> setOpenCol(true)} sort={sort} setSort={setSort} onRowClick={(r)=> setSelected(r.symbol)} onEdit={onEdit} logos={logos} density={density} summaryLabel="matched" />
          </div>
        </Panel>
      </PanelGroup>

      <ColumnSettings open={openCol} onOpenChange={setOpenCol} columnDefs={columnDefs} visibleColumns={visibleColumns} setVisibleColumns={setVisibleColumns} presets={presets} savePreset={savePreset} loadPreset={loadPreset} resetRecommended={resetRecommended} />
    </div>
  )
}