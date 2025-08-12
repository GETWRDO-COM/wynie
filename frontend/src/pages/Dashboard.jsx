import React, { useEffect, useMemo, useState } from "react"
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import { Separator } from "../components/ui/separator"
import DataTable from "../components/DataTable"
import ColumnSettings from "../components/ColumnSettings"
import ScreenerPanel from "./ScreenerPanel"
import { getBars, getLogo, getQuotes, computeRatings, getColumnSchema, getColumnPresets, saveColumnPreset } from "../services/api"
import { Settings2, ListPlus, List, Pencil, Eraser, LineChart } from "lucide-react"
import useQuotesWS from "../hooks/useQuotesWS"
import { LS } from "../mock/mock"

function useLocalState(key, initial) {
  const [v, setV] = useState(()=> LS.get(key, initial))
  useEffect(()=> { LS.set(key, v) }, [key, v])
  return [v, setV]
}

function CandleChart({ symbol, drawings, setDrawings }) {
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

  const [tool, setTool] = useLocalState("tool", "line")
  const [temp, setTemp] = useState(null)

  function onDown(e){ const rect = e.currentTarget.getBoundingClientRect(); const p = { x: e.clientX - rect.left, y: e.clientY - rect.top }; setTemp({ start: p, end: p }) }
  function onMove(e){ if(!temp) return; const r=e.currentTarget.getBoundingClientRect(); const p={x:e.clientX-r.left,y:e.clientY-r.top}; setTemp(prev=> ({...prev, end:p})) }
  function onUp(){ if(!temp) return; setDrawings(prev => ({...prev, [symbol]: [...(prev[symbol]||[]), temp]})); setTemp(null) }
  function clear(){ setDrawings(prev => ({...prev, [symbol]: []})) }

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between py-2">
        <CardTitle className="text-base">{symbol} • Chart</CardTitle>
        <div className="flex items-center gap-2">
          <Button size="sm" variant={tool==='line'? 'default':'secondary'} onClick={()=> LS.set('tool', setTool('line'))}><Pencil className="w-4 h-4 mr-1"/>Line</Button>
          <Button size="sm" variant="secondary" onClick={clear}><Eraser className="w-4 h-4 mr-1"/>Clear</Button>
        </div>
      </CardHeader>
      <CardContent>
        <svg width={W} height={H} onMouseDown={onDown} onMouseMove={onMove} onMouseUp={onUp} className="bg-background border rounded">
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
      </CardContent>
    </Card>
  )
}

export default function Dashboard() {
  const [rows, setRows] = useState([])
  const [selected, setSelected] = useLocalState("selectedSymbol", "AAPL")
  const [visibleColumns, setVisibleColumns] = useLocalState("visibleColumns", ["logo","symbol","last","changePct","volume","avgVol20d","runRate20d","sma20","sma50","sma200","rsi14","RS","AS"]) 
  const [sort, setSort] = useState({ key: "RS", dir: "desc" })
  const [rsWindow, setRsWindow] = useLocalState("rsWindow", 63)
  const [asShort, setAsShort] = useLocalState("asShort", 21)
  const [asLong, setAsLong] = useLocalState("asLong", 63)
  const [watchSymbols, setWatchSymbols] = useLocalState("watchlist_default", ["AAPL","MSFT","NVDA","AMZN","GOOGL"]) 
  const [query, setQuery] = useState("")
  const [openCol, setOpenCol] = useState(false)
  const [presets, setPresets] = useState({})
  const [drawings, setDrawings] = useLocalState("drawings", {})
  const [logos, setLogos] = useLocalState("logos", {})
  const [columnDefs, setColumnDefs] = useState([])

  // live quotes via WS
  const quotesMap = useQuotesWS(watchSymbols)

  // Load column schema & presets
  useEffect(()=>{ (async()=>{
    try{ const s = await getColumnSchema(); const cols = s.categories.flatMap(g=> g.columns); setColumnDefs(cols) } catch {}
    try{ const p = await getColumnPresets(); setPresets(p) } catch {}
  })() }, [])

  // Load initial quotes for table
  useEffect(()=>{
    (async()=>{
      try{
        const csv = watchSymbols.join(',')
        const q = await getQuotes(csv)
        const map = {}
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
        }))
        setRows(data)
      } catch(e){ console.error(e) }
    })()
  }, [watchSymbols])

  // Apply live quotes onto rows
  useEffect(()=>{
    if (!quotesMap || Object.keys(quotesMap).length===0) return
    setRows(prev => prev.map(r => {
      const q = quotesMap[r.symbol]
      if (!q) return r
      return { ...r, last: q.last ?? r.last, changePct: q.changePct ?? r.changePct, volume: q.volume ?? r.volume }
    }))
  }, [quotesMap])

  // Fetch RS/AS when windows or symbols change
  useEffect(()=>{
    (async()=>{
      try{ const r = await computeRatings({ symbols: watchSymbols, rsWindowDays: rsWindow, asShortDays: asShort, asLongDays: asLong })
        setRows(prev => prev.map(row => ({...row, RS: r.RS?.[row.symbol] ?? row.RS, AS: r.AS?.[row.symbol] ?? row.AS })))
      }catch(e){ console.warn('ratings compute failed', e) }
    })()
  }, [rsWindow, asShort, asLong, watchSymbols])

  // Lazy fetch logos
  useEffect(()=>{
    (async()=>{
      const next = {...logos}
      for (const s of watchSymbols) {
        if (!next[s]) {
          try { const r = await getLogo(s); next[s] = r.logoUrl || null } catch {}
        }
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
  const resetRecommended = ()=> setVisibleColumns(["logo","symbol","last","changePct","volume","avgVol20d","runRate20d","sma20","sma50","sma200","rsi14","RS","AS"])

  const onEdit = (symbol, key, value)=>{ setRows(prev => prev.map(r => r.symbol===symbol ? ({...r, [key]: value}) : r)) }

  return (
    <div className="h-screen w-full flex flex-col">
      <header className="h-12 border-b px-4 flex items-center justify-between bg-card">
        <div className="font-semibold">Deepvue Workstation (Live • Polygon + Finnhub)</div>
        <div className="flex items-center gap-3 text-sm">
          <div className="flex items-center gap-2">
            <label>RS window</label>
            <select className="border rounded px-2 py-1" value={rsWindow} onChange={(e)=> setRsWindow(parseInt(e.target.value))}>
              <option value={21}>1M</option>
              <option value={63}>3M</option>
              <option value={126}>6M</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label>AS short</label>
            <select className="border rounded px-2 py-1" value={asShort} onChange={(e)=> setAsShort(parseInt(e.target.value))}>
              <option value={10}>10d</option>
              <option value={21}>21d</option>
              <option value={30}>30d</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label>AS long</label>
            <select className="border rounded px-2 py-1" value={asLong} onChange={(e)=> setAsLong(parseInt(e.target.value))}>
              <option value={42}>42d</option>
              <option value={63}>63d</option>
              <option value={90}>90d</option>
            </select>
          </div>
          <Button size="sm" variant="secondary" onClick={()=> setOpenCol(true)}><Settings2 className="w-4 h-4 mr-1"/>Columns</Button>
        </div>
      </header>

      <PanelGroup direction="horizontal" className="flex-1">
        <Panel defaultSize={30} minSize={18}>
          <div className="h-full flex flex-col">
            <Tabs defaultValue="watchlists" className="px-3 pt-3">
              <TabsList>
                <TabsTrigger value="watchlists"><List className="w-4 h-4 mr-1"/>Watchlists</TabsTrigger>
                <TabsTrigger value="screener"><LineChart className="w-4 h-4 mr-1"/>Screener</TabsTrigger>
              </TabsList>
              <TabsContent value="watchlists">
                <div className="flex items-center gap-2 py-2">
                  <Input placeholder="Add symbol" id="addSym" onKeyDown={(e)=> e.key==='Enter' && onAddSymbol(e.currentTarget.value)} />
                  <Button onClick={()=> onAddSymbol(document.getElementById('addSym').value)}><ListPlus className="w-4 h-4 mr-1"/>Add</Button>
                </div>
                <div className="space-y-1 max-h-[30vh] overflow-auto pr-1">
                  {watchSymbols.map(sym => (
                    <div key={sym} className={`px-2 py-1 rounded cursor-pointer hover:bg-muted/50 ${selected===sym? 'bg-muted/70':''}`} onClick={()=> setSelected(sym)}>
                      {sym}
                    </div>
                  ))}
                </div>
                <Separator className="my-2"/>
                <Input placeholder="Search in list" value={query} onChange={(e)=> setQuery(e.target.value)} />
                <div className="mt-2">
                  <DataTable rows={filteredRows} columnDefs={columnDefs} visibleColumns={visibleColumns} onColumnsClick={()=> setOpenCol(true)} sort={sort} setSort={setSort} onRowClick={(r)=> setSelected(r.symbol)} onEdit={onEdit} logos={logos} />
                </div>
              </TabsContent>
              <TabsContent value="screener">
                <ScreenerPanel onResults={(rows)=> setRows(rows)} />
              </TabsContent>
            </Tabs>
          </div>
        </Panel>
        <PanelResizeHandle className="w-1 bg-border" />
        <Panel defaultSize={70} minSize={35}>
          <div className="h-full p-3">
            <CandleChart symbol={selected} drawings={drawings} setDrawings={setDrawings} />
          </div>
        </Panel>
      </PanelGroup>

      <ColumnSettings open={openCol} onOpenChange={setOpenCol} columnDefs={columnDefs} visibleColumns={visibleColumns} setVisibleColumns={setVisibleColumns} presets={presets} savePreset={savePreset} loadPreset={loadPreset} resetRecommended={resetRecommended} />
    </div>
  )
}