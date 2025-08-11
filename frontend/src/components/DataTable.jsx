import React, { useMemo } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table"
import { Input } from "../components/ui/input"
import { Button } from "../components/ui/button"
import { ArrowUpDown, Pin, Settings } from "lucide-react"

// Column registry with categories. Easy to extend.
export const COLUMN_REGISTRY = [
  { id: "symbol", label: "Symbol", category: "General", width: 90 },
  { id: "description", label: "Description", category: "General", width: 180 },
  { id: "sector", label: "Sector", category: "Sector & Industry", width: 140 },
  { id: "industry", label: "Industry", category: "Sector & Industry", width: 160 },
  { id: "marketCap", label: "Mkt Cap", category: "General", formatter: (v) => Intl.NumberFormat().format(v) },
  { id: "last", label: "Last", category: "Price & Volume" },
  { id: "changePct", label: "% Chg", category: "Price & Volume", formatter: (v)=> `${v.toFixed(2)}%` },
  { id: "volume", label: "Vol", category: "Price & Volume", formatter: (v)=> Intl.NumberFormat().format(v) },
  { id: "avgVol20d", label: "AvgVol20d", category: "Price & Volume", formatter: (v)=> Intl.NumberFormat().format(v) },
  { id: "runRate20d", label: "RunRate20d", category: "Price & Volume" },
  { id: "relVol", label: "RelVol", category: "Price & Volume" },
  { id: "high52w", label: "52w High", category: "Price & Volume" },
  { id: "low52w", label: "52w Low", category: "Price & Volume" },
  { id: "gapPct", label: "Gap %", category: "Price & Volume" },
  { id: "nextEarnings", label: "Next Earnings", category: "Earnings", formatter: (v)=> new Date(v).toLocaleDateString() },
  { id: "latestEarnings", label: "Latest Earnings", category: "Earnings", formatter: (v)=> new Date(v).toLocaleDateString() },
  { id: "sma20", label: "SMA20", category: "Technicals" },
  { id: "sma50", label: "SMA50", category: "Technicals" },
  { id: "sma200", label: "SMA200", category: "Technicals" },
  { id: "rsi14", label: "RSI(14)", category: "Technicals" },
  { id: "atr", label: "ATR", category: "Technicals" },
  { id: "prePct", label: "Pre %", category: "Pre/Post Market" },
  { id: "postPct", label: "Post %", category: "Pre/Post Market" },
  { id: "RS", label: "RS", category: "Proprietary Ratings" },
  { id: "AS", label: "AS", category: "Proprietary Ratings" },
  { id: "notes", label: "Notes", category: "General", editable: true },
]

export default function DataTable({ rows, visibleColumns, onColumnsClick, sort, setSort, onRowClick, onEdit }) {
  const cols = useMemo(() => COLUMN_REGISTRY.filter(c => visibleColumns.includes(c.id)), [visibleColumns])

  const sortedRows = useMemo(() => {
    if (!sort || !sort.key) return rows
    const arr = [...rows]
    arr.sort((a,b)=>{
      const av = a[sort.key]; const bv = b[sort.key]
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      return sort.dir === 'asc' ? (av > bv ? 1 : av < bv ? -1 : 0) : (av < bv ? 1 : av > bv ? -1 : 0)
    })
    return arr
  }, [rows, sort])

  return (
    <div className="w-full overflow-auto border rounded-md">
      <div className="flex items-center justify-between px-3 py-2 border-b bg-card sticky top-0 z-10">
        <div className="text-sm text-muted-foreground">Rows: {rows.length}</div>
        <Button variant="secondary" size="sm" onClick={onColumnsClick}><Settings className="w-4 h-4 mr-2"/>Columns</Button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            {cols.map(col => (
              <TableHead key={col.id} style={{minWidth: col.width || 110}}>
                <button className="flex items-center gap-1" onClick={()=> setSort(sort && sort.key===col.id ? { key: col.id, dir: sort.dir==='asc'?'desc':'asc'} : { key: col.id, dir: 'asc'})}>
                  {col.label}
                  <ArrowUpDown className="w-3 h-3"/>
                </button>
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedRows.map((r)=> (
            <TableRow key={r.symbol} className="cursor-pointer hover:bg-muted/30" onClick={()=> onRowClick && onRowClick(r)}>
              {cols.map(col => (
                <TableCell key={col.id}>
                  {col.editable ? (
                    <Input value={r[col.id] || ''} onClick={(e)=> e.stopPropagation()} onChange={(e)=> onEdit && onEdit(r.symbol, col.id, e.target.value)} />
                  ) : (
                    col.formatter ? col.formatter(r[col.id]) : (r[col.id] ?? '-')
                  )}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}