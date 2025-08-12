import React, { useMemo } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table"
import { Input } from "./ui/input"
import { Button } from "./ui/button"
import { Checkbox } from "./ui/checkbox"
import { ArrowUpDown, Settings } from "lucide-react"
import { Avatar, AvatarImage, AvatarFallback } from "./ui/avatar"

function SymbolCell({row, logoUrl, selectable, selected, onToggle}){
  return (
    <div className="flex items-center gap-2">
      {selectable && <Checkbox checked={!!selected} onCheckedChange={onToggle} />}
      <Avatar className="w-5 h-5">
        <AvatarImage src={logoUrl || ''} alt={row.symbol} />
        <AvatarFallback className="text-[10px]">{row.symbol?.slice(0,2)}</AvatarFallback>
      </Avatar>
      <span className="font-medium">{row.symbol}</span>
    </div>
  )
}

function formatValue(col, v){
  if (v == null) return '-'
  if (col.type === 'number' && typeof v === 'number'){
    if (col.id.toLowerCase().includes('pct')) return `${v.toFixed(2)}%`
    if (['volume','avgVol20d'].includes(col.id)) return Intl.NumberFormat().format(v)
    return typeof v === 'number' ? +(+v).toFixed(2) : v
  }
  return v
}

export default function DataTable({ rows, columnDefs, visibleColumns, onColumnsClick, sort, setSort, onRowClick, onEdit, logos, selectable=false, selectedMap={}, onSelectChange }) {
  const colMap = useMemo(()=>{
    const map = {}
    ;(columnDefs||[]).forEach(c => map[c.id] = c)
    return map
  }, [columnDefs])

  const cols = useMemo(() => (visibleColumns||[]).map(id => colMap[id]).filter(Boolean), [visibleColumns, colMap])

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
    <div className="w-full overflow-auto border rounded-md text-xs">
      <div className="flex items-center justify-between px-3 py-2 border-b bg-card sticky top-0 z-10">
        <div className="text-xs text-muted-foreground">Rows: {rows.length}</div>
        <Button variant="secondary" size="sm" onClick={onColumnsClick}><Settings className="w-4 h-4 mr-2"/>Columns</Button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            {cols.map(col => (
              <TableHead key={col.id} style={{minWidth: col.width || 110}} className="py-1">
                <button className="flex items-center gap-1" onClick={()=> setSort(sort && sort.key===col.id ? { key: col.id, dir: sort.dir==='asc'?'desc':'asc'} : { key: col.id, dir: 'asc'})}>
                  {col.label || ''}
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
                <TableCell key={col.id} className="py-1">
                  {col.id === 'logo' ? (
                    <Avatar className="w-5 h-5">
                      <AvatarImage src={logos?.[r.symbol] || ''} alt={r.symbol} />
                      <AvatarFallback className="text-[10px]">{r.symbol?.slice(0,2)}</AvatarFallback>
                    </Avatar>
                  ) : col.id === 'symbol' ? (
                    <SymbolCell row={r} logoUrl={logos?.[r.symbol]} selectable={selectable} selected={selectedMap[r.symbol]} onToggle={(val)=> onSelectChange && onSelectChange(r.symbol, !!val)} />
                  ) : col.editable ? (
                    <Input value={r[col.id] || ''} onClick={(e)=> e.stopPropagation()} onChange={(e)=> onEdit && onEdit(r.symbol, col.id, e.target.value)} />
                  ) : (
                    formatValue(col, r[col.id])
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