import React from "react"
import DataTable from "./DataTable"

export default function MiniListPanel({ title="List", rows, columnDefs, visibleColumns, onColumnsClick, sort, setSort, onRowClick, onEdit, logos }){
  return (
    <div className="h-full flex flex-col border rounded-md overflow-hidden">
      <div className="px-3 py-2 border-b text-sm font-medium bg-card/80">{title}</div>
      <div className="flex-1 overflow-auto text-xs">
        <DataTable rows={rows} columnDefs={columnDefs} visibleColumns={visibleColumns} onColumnsClick={onColumnsClick} sort={sort} setSort={setSort} onRowClick={onRowClick} onEdit={onEdit} logos={logos} />
      </div>
    </div>
  )
}