import React, { useEffect, useMemo, useState } from "react"
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import { Separator } from "../components/ui/separator"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../components/ui/tooltip"
import DataTable, { COLUMN_REGISTRY } from "../components/DataTable"
import ColumnSettings from "../components/ColumnSettings"
import { getMockUniverse, getCandles, computeRS, computeAS, LS, SYMBOLS } from "../mock/mock"
import { Settings2, ListPlus, List, Pencil, Eraser, LineChart, Cog } from "lucide-react"

function useLocalState(key, initial) {
  const [v, setV] = useState(()=> LS.get(key, initial))
  useEffect(()=> { LS.set(key, v) }, [key, v])
  return [v, setV]
}

// Simple SVG candle chart with line drawing overlay (mock). When TradingView is added, this becomes a wrapper.
function CandleChart({ symbol, drawings, setDrawings }) {
  const candles = useMemo(()=> getCandles(symbol, 180), [symbol])
  // Dimensions
  const W = 820, H = 420, PAD = 40
  const highs = candles.map(c=> c.high), lows = candles.map(c=> c.low)
  const maxP = Math.max(...highs), minP = Math.min(...lows)
  const x = (i) => PAD + (i * (W - PAD*2)) / (candles.length - 1)
  const y = (p) => H - PAD - ((p - minP) / (maxP - minP)) * (H - PAD*2)

  const [tool, setTool] = useLocalState("tool", "line")
  const [temp, setTemp] = useState(null)

  function onDown(e){
    const rect = e.currentTarget.getBoundingClientRect()
    const p = { x: e.clientX - rect.left, y: e.clientY - rect.top }
    setTemp({ start: p, end: p })
  }
  function onMove(e){ if(!temp) return; const r=e.currentTarget.getBoundingClientRect(); const p={x:e.clientX-r.left,y:e.clientY-r.top}; setTemp(prev=> ({...prev, end:p})) }
  function onUp(){ if(!temp) return; setDrawings(prev => ({...prev, [symbol]: [...(prev[symbol]||[]), temp]})); setTemp(null) }
  function clear(){ setDrawings(prev => ({...prev, [symbol]: []})) }

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between py-2">
        <CardTitle className="text-base">{symbol} • Mock Chart (TV ready)</CardTitle>
        <div className="flex items-center gap-2">
          <Button size="sm" variant={tool==='line'? 'default':'secondary'} onClick={()=> setTool('line')}><Pencil className="w-4 h-4 mr-1"/>Line</Button>
          <Button size="sm" variant="secondary" onClick={clear}><Eraser className="w-4 h-4 mr-1"/>Clear</Button>
        </div>
      </CardHeader>
      <CardContent>
        <svg width={W} height={H} onMouseDown={onDown} onMouseMove={onMove} onMouseUp={onUp} className="bg-background border rounded">
          {/* Axes */}
          <line x1={PAD} y1={PAD} x2={PAD} y2={H-PAD} stroke="#444" />
          <line x1={PAD} y1={H-PAD} x2={W-PAD} y2={H-PAD} stroke="#444" />
          {/* Candles */}
          {candles.map((c, i)=>{
            const cx = x(i)
            const yO = y(c.open), yC = y(c.close)
            const top = y(Math.max(c.open,c.close))
            const bottom = y(Math.min(c.open,c.close))
            const color = c.close >= c.open ? "#10b981" : "#ef4444" // emerald/red
            return (
              <g key={i}>
                <line x1={cx} x2={cx} y1={y(c.high)} y2={y(c.low)} stroke={color} />
                <rect x={cx-3} width={6} y={top} height={Math.max(2, bottom-top)} fill={color} />
              </g>
            )
          })}
          {/* Existing drawings */}
          {(drawings[symbol]||[]).map((d, idx)=> (
            <line key={idx} x1={d.start.x} y1={d.start.y} x2={d.end.x} y2={d.end.y} stroke="#60a5fa" strokeWidth="2" />
          ))}
          {/* Temp */}
          {temp && <line x1={temp.start.x} y1={temp.start.y} x2={temp.end.x} y2={temp.end.y} stroke="#38bdf8" strokeDasharray="4 4" />}
        </svg>
      </CardContent>
    </Card>
  )
}

export default function Dashboard() {
  const [universe, setUniverse] = useState([])
  const [rows, setRows] = useState([])
  const [selected, setSelected] = useLocalState("selectedSymbol", "AAPL")
  const [visibleColumns, setVisibleColumns] = useLocalState("visibleColumns", [
    "symbol","last","changePct","volume","avgVol20d","runRate20d","sma20","sma50","sma200","rsi14","RS","AS","notes"
  ])
  const [sort, setSort] = useState({ key: "RS", dir: "desc" })
  const [rsWindow, setRsWindow] = useLocalState("rsWindow", 63) // ~3M
  const [asShort, setAsShort] = useLocalState("asShort", 21)
  const [asLong, setAsLong] = useLocalState("asLong", 63)
  const [watchlist, setWatchlist] = useLocalState("watchlist_default", ["AAPL","MSFT","NVDA","AMZN","GOOGL"]) 
  const [query, setQuery] = useState("")
  const [openCol, setOpenCol] = useState(false)
  const [presets, setPresets] = useLocalState("column_presets", {})
  const [drawings, setDrawings] = useLocalState("drawings", {})

  useEffect(()=>{
    const uni = getMockUniverse()
    // compute RS/AS
    const RS = computeRS(uni, rsWindow)
    const AS = computeAS(uni, asShort, asLong)
    const withRatings = uni.map((r, i)=> ({...r, RS: RS[i], AS: AS[i]}))
    setUniverse(withRatings)
  }, [rsWindow, asShort, asLong])

  useEffect(()=>{
    const wl = new Set(watchlist)
    const base = universe.filter(r => wl.has(r.symbol))
    const filtered = query ? base.filter(r => r.symbol.toLowerCase().includes(query.toLowerCase()) || (r.description||"").toLowerCase().includes(query.toLowerCase())) : base
    setRows(filtered)
  }, [universe, watchlist, query])

  const onAddSymbol = (sym)=>{
    const s = sym.toUpperCase().trim()
    if (!s) return
    if (!watchlist.includes(s)) setWatchlist([...watchlist, s])
  }

  const savePreset = (name)=>{ if(!name) return; setPresets(prev => ({...prev, [name]: visibleColumns})) }
  const loadPreset = (name)=>{ if(!name) return; const cols = presets[name]; if (cols) setVisibleColumns(cols) }
  const resetRecommended = ()=> setVisibleColumns(["symbol","last","changePct","volume","avgVol20d","runRate20d","sma20","sma50","sma200","rsi14","RS","AS","notes"])

  const onEdit = (symbol, key, value)=>{
    setUniverse(prev => prev.map(r => r.symbol===symbol ? ({...r, [key]: value}) : r))
  }

  return (
    <div className="h-screen w-full flex flex-col">
      <header className="h-12 border-b px-4 flex items-center justify-between bg-card">
        <div className="font-semibold">Deepvue Workstation (Mock)</div>
        <div className="flex items-center gap-3 text-sm">
          <div className="flex items-center gap-2">
            <label>RS window</label>
            <select className="border rounded px-2 py-1" value={rsWindow} onChange={(e)=> LS.set('rsWindow', setRsWindow(parseInt(e.target.value)))}>
              <option value={21}>1M</option>
              <option value={63}>3M</option>
              <option value={126}>6M</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label>AS short</label>
            <select className="border rounded px-2 py-1" value={asShort} onChange={(e)=> LS.set('asShort', setAsShort(parseInt(e.target.value)))}>
              <option value={10}>10d</option>
              <option value={21}>21d</option>
              <option value={30}>30d</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label>AS long</label>
            <select className="border rounded px-2 py-1" value={asLong} onChange={(e)=> LS.set('asLong', setAsLong(parseInt(e.target.value)))}>
              <option value={42}>42d</option>
              <option value={63}>63d</option>
              <option value={90}>90d</option>
            </select>
          </div>
          <Button size="sm" variant="secondary" onClick={()=> setOpenCol(true)}><Settings2 className="w-4 h-4 mr-1"/>Columns</Button>
        </div>
      </header>

      <PanelGroup direction="horizontal" className="flex-1">
        <Panel defaultSize={28} minSize={18}>
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
                  {watchlist.map(sym => (
                    <div key={sym} className={`px-2 py-1 rounded cursor-pointer hover:bg-muted/50 ${selected===sym? 'bg-muted/70':''}`} onClick={()=> setSelected(sym)}>
                      {sym}
                    </div>
                  ))}
                </div>
                <Separator className="my-2"/>
                <Input placeholder="Search in list" value={query} onChange={(e)=> setQuery(e.target.value)} />
                <div className="mt-2">
                  <DataTable rows={rows} visibleColumns={visibleColumns} onColumnsClick={()=> setOpenCol(true)} sort={sort} setSort={setSort} onRowClick={(r)=> setSelected(r.symbol)} onEdit={onEdit} />
                </div>
              </TabsContent>
              <TabsContent value="screener">
                <Screener universe={universe} setRows={setRows} setSelected={setSelected} />
              </TabsContent>
            </Tabs>
          </div>
        </Panel>
        <PanelResizeHandle className="w-1 bg-border" />
        <Panel defaultSize={72} minSize={35}>
          <div className="h-full p-3">
            <CandleChart symbol={selected} drawings={drawings} setDrawings={setDrawings} />
          </div>
        </Panel>
      </PanelGroup>

      <ColumnSettings open={openCol} onOpenChange={setOpenCol} visibleColumns={visibleColumns} setVisibleColumns={setVisibleColumns} presets={presets} savePreset={savePreset} loadPreset={loadPreset} resetRecommended={resetRecommended} />
    </div>
  )
}

function Screener({ universe, setRows, setSelected }){
  const [minPrice, setMinPrice] = useState(5)
  const [minVol, setMinVol] = useState(500000)
  const [minRSI, setMinRSI] = useState(30)
  const [maxRSI, setMaxRSI] = useState(80)

  useEffect(()=>{ run() }, [universe])

  const run = ()=>{
    const res = universe.filter(r => r.last &gt;= minPrice &amp;&amp; r.volume &gt;= minVol &amp;&amp; r.rsi14 &gt;= minRSI &amp;&amp; r.rsi14 &lt;= maxRSI)
    setRows(res)
  }

  return (
    <Card>
      <CardHeader className="py-2"><CardTitle className="text-base">Quick Screener</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm">Min Price
            <Input type="number" value={minPrice} onChange={(e)=> setMinPrice(parseFloat(e.target.value||0))} />
          </label>
          <label className="text-sm">Min Volume
            <Input type="number" value={minVol} onChange={(e)=> setMinVol(parseInt(e.target.value||0))} />
          </label>
          <label className="text-sm">Min RSI
            <Input type="number" value={minRSI} onChange={(e)=> setMinRSI(parseFloat(e.target.value||0))} />
          </label>
          <label className="text-sm">Max RSI
            <Input type="number" value={maxRSI} onChange={(e)=> setMaxRSI(parseFloat(e.target.value||0))} />
          </label>
        </div>
        <div className="flex gap-2">
          <Button onClick={run}>Run</Button>
          <Button variant="secondary" onClick={()=> { setMinPrice(5); setMinVol(500000); setMinRSI(30); setMaxRSI(80); setTimeout(run, 0) }}>Reset</Button>
        </div>
      </CardContent>
    </Card>
  )
}