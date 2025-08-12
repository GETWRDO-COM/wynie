import React, { useState, useEffect, useMemo } from 'react';
import { FaTable, FaDownload, FaCog, FaEye, FaEyeSlash, FaSort, FaSortUp, FaSortDown, FaFilter, FaCalculator, FaSave } from 'react-icons/fa';

const SpreadsheetTab = ({ api, etfs, sectors, selectedSector, setSelectedSector, exportLoading, setExportLoading }) => {
  const [spreadsheetData, setSpreadsheetData] = useState([]);
  const [formulas, setFormulas] = useState({});
  const [showFormulas, setShowFormulas] = useState(false);
  const [formulaConfig, setFormulaConfig] = useState({});
  const [editingFormulas, setEditingFormulas] = useState(false);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [loading, setLoading] = useState(false);

  useEffect(() => { fetchSpreadsheetData(); fetchFormulaConfig(); }, [selectedSector]);

  const fetchSpreadsheetData = async () => { setLoading(true); try { const params = selectedSector ? `?sector=${encodeURIComponent(selectedSector)}` : ''; const response = await api.get(`/api/spreadsheet/etfs${params}`); setSpreadsheetData(response.data.data); setFormulas(response.data.formulas); } catch (err) { console.error('Failed to fetch spreadsheet data:', err); } finally { setLoading(false); } };
  const fetchFormulaConfig = async () => { try { const response = await api.get('/api/formulas/config'); setFormulaConfig(response.data); } catch (err) { console.error('Failed to fetch formula config:', err); } };

  const updateFormulaConfig = async () => { setLoading(true); try { await api.post('/api/formulas/config', formulaConfig); await fetchSpreadsheetData(); setEditingFormulas(false); alert('Formula configuration updated successfully!'); } catch (err) { console.error('Failed to update formula config:', err); alert('Failed to update formula configuration.'); } finally { setLoading(false); } };

  const exportToCSV = async () => { setExportLoading(true); try { const response = await api.get('/api/export/etfs'); const csvData = response.data.data; const headers = Object.keys(csvData[0]).join(','); const rows = csvData.map(row => Object.values(row).join(',')).join('\n'); const csvContent = headers + '\n' + rows; const blob = new Blob([csvContent], { type: 'text/csv' }); const url = window.URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `etf-spreadsheet-${new Date().toISOString().split('T')[0]}.csv`; a.click(); window.URL.revokeObjectURL(url); alert('Spreadsheet data exported successfully!'); } catch (err) { alert('Failed to export data. Please try again.'); } finally { setExportLoading(false); } };

  const exportToGoogleSheets = () => { let googleSheetsData = `=IMPORTDATA("${window.location.origin}/api/export/etfs")\n\n`; googleSheetsData += "// HUNT BY WRDO - Spreadsheet View\n"; googleSheetsData += "// Copy the formula above into cell A1 in Google Sheets\n"; googleSheetsData += "// This will import live data from the platform\n\n"; const blob = new Blob([googleSheetsData], { type: 'text/plain' }); const url = window.URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'wrdo-google-sheets-formula.txt'; a.click(); window.URL.revokeObjectURL(url); alert('Google Sheets import formula downloaded! Copy the formula from the file into cell A1 in Google Sheets.'); };

  const getCellColor = (value, type) => {
    switch (type) {
      case 'change':
        if (value > 5) return 'bg-green-900 text-green-300';
        if (value > 0) return 'bg-green-800 text-green-400';
        if (value < -5) return 'bg-red-900 text-red-300';
        if (value < 0) return 'bg-red-800 text-red-400';
        return 'bg-white/5 text-gray-300';
      case 'sata':
        if (value >= 8) return 'bg-green-900 text-green-300 font-bold';
        if (value >= 6) return 'bg-yellow-800 text-yellow-300 font-bold';
        return 'bg-red-900 text-red-300 font-bold';
      case 'rs':
        if (value.includes('Y')) return 'bg-green-900 text-green-300 font-bold';
        if (value.includes('N')) return 'bg-red-900 text-red-300 font-bold';
        return 'bg-yellow-800 text-yellow-300 font-bold';
      case 'color':
        if (value === 'Green') return 'bg-green-900 text-green-300 font-bold';
        if (value === 'Red') return 'bg-red-900 text-red-300 font-bold';
        return 'bg-yellow-800 text-yellow-300 font-bold';
      default:
        return 'bg-white/5 text-gray-300';
    }
  };

  const handleSort = (key) => { let direction = 'asc'; if (sortConfig.key === key && sortConfig.direction === 'asc') { direction = 'desc'; } setSortConfig({ key, direction }); };
  const getSortIcon = (columnName) => { if (sortConfig.key !== columnName) return <FaSort className="text-gray-500" />; return sortConfig.direction === 'asc' ? <FaSortUp className="text-blue-400" /> : <FaSortDown className="text-blue-400" />; };

  const processedData = useMemo(() => { let data = [...spreadsheetData]; if (sortConfig.key) { data.sort((a, b) => { const aVal = a[sortConfig.key] || 0; const bVal = b[sortConfig.key] || 0; const aNum = typeof aVal === 'string' ? parseFloat(aVal.replace(/[^\d.-]/g, '')) || 0 : aVal; const bNum = typeof bVal === 'string' ? parseFloat(bVal.replace(/[^\d.-]/g, '')) || 0 : bVal; if (aNum < bNum) return sortConfig.direction === 'asc' ? -1 : 1; if (aNum > bNum) return sortConfig.direction === 'asc' ? 1 : -1; return 0; }); } return data; }, [spreadsheetData, sortConfig]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-card p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
          <h2 className="text-2xl md:text-3xl font-bold text-white flex items-center"><FaTable className="mr-3 text-green-400" /> HUNT BY WRDO — Spreadsheet</h2>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => setShowFormulas(!showFormulas)} className="btn btn-secondary text-sm flex items-center gap-2">{showFormulas ? <FaEyeSlash /> : <FaEye />}{showFormulas ? 'Hide' : 'Show'} Formulas</button>
            <button onClick={() => setEditingFormulas(!editingFormulas)} className="btn btn-outline text-sm flex items-center gap-2"><FaCog />{editingFormulas ? 'Cancel' : 'Edit'} Config</button>
            <button onClick={exportToCSV} disabled={exportLoading} className="btn btn-success disabled:opacity-50 text-sm flex items-center gap-2"><FaDownload />{exportLoading ? 'Exporting...' : 'Export CSV'}</button>
            <button onClick={exportToGoogleSheets} className="btn btn-primary text-sm flex items-center gap-2"><FaTable />Google Sheets</button>
          </div>
        </div>

        <div className="mb-4">
          <select value={selectedSector} onChange={(e) => setSelectedSector(e.target.value)} className="form-select"><option value="">All Sectors 📊</option>{sectors.map((sector) => (<option key={sector} value={sector}>{sector}</option>))}</select>
        </div>

        {editingFormulas && (
          <div className="bg-white/5 rounded-lg p-4 mb-4">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center"><FaCalculator className="mr-2" />Formula Configuration</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-green-400 font-semibold mb-2">Relative Strength Thresholds</h4>
                <div className="space-y-2">
                  <div><label className="block text-sm text-gray-300">Strong Threshold (Y flag):</label><input type="number" step="0.01" value={formulaConfig.relative_strength?.strong_threshold || 0.10} onChange={(e) => setFormulaConfig({ ...formulaConfig, relative_strength: { ...formulaConfig.relative_strength, strong_threshold: parseFloat(e.target.value) } })} className="form-input w-full" /></div>
                  <div><label className="block text-sm text-gray-300">Moderate Threshold (M flag):</label><input type="number" step="0.01" value={formulaConfig.relative_strength?.moderate_threshold || 0.02} onChange={(e) => setFormulaConfig({ ...formulaConfig, relative_strength: { ...formulaConfig.relative_strength, moderate_threshold: parseFloat(e.target.value) } })} className="form-input w-full" /></div>
                </div>
              </div>
              <div>
                <h4 className="text-blue-400 font-semibold mb-2">SATA Weights</h4>
                <div className="space-y-2">
                  <div><label className="block text-sm text-gray-300">Performance Weight:</label><input type="number" step="0.01" value={formulaConfig.sata_weights?.performance || 0.40} onChange={(e) => setFormulaConfig({ ...formulaConfig, sata_weights: { ...formulaConfig.sata_weights, performance: parseFloat(e.target.value) } })} className="form-input w-full" /></div>
                  <div><label className="block text-sm text-gray-300">Relative Strength Weight:</label><input type="number" step="0.01" value={formulaConfig.sata_weights?.relative_strength || 0.30} onChange={(e) => setFormulaConfig({ ...formulaConfig, sata_weights: { ...formulaConfig.sata_weights, relative_strength: parseFloat(e.target.value) } })} className="form-input w-full" /></div>
                </div>
              </div>
            </div>
            <div className="flex gap-2 mt-4"><button onClick={updateFormulaConfig} disabled={loading} className="btn btn-success disabled:opacity-50"><FaSave />{loading ? 'Saving...' : 'Save Configuration'}</button><button onClick={() => { fetchFormulaConfig(); setEditingFormulas(false); }} className="btn btn-secondary">Cancel</button></div>
          </div>
        )}

        {showFormulas && !editingFormulas && (
          <div className="bg-white/5 rounded-lg p-4 mb-4">
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center"><FaCalculator className="mr-2" />Active Formulas & Logic</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm font-mono text-gray-300">
              {Object.entries(formulas).map(([key, formula]) => (
                <div key={key} className="bg-white/5 p-3 rounded"><div className="text-blue-300 font-semibold capitalize mb-1">{key.replace('_', ' ')}:</div><div className="text-gray-200 text-xs">{formula}</div></div>
              ))}
            </div>
          </div>
        )}

        <div className="text-gray-400 text-sm">Showing {processedData.length} ETFs • Google Sheets Compatible Format</div>
      </div>

      {/* Spreadsheet Grid */}
      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center"><div className="text-gray-400">Loading spreadsheet data...</div></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-white/5 sticky top-0">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold text-gray-200 cursor-pointer border-r border-white/10" onClick={() => handleSort('Ticker')}><div className="flex items-center gap-1">A {getSortIcon('Ticker')}</div></th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-200 border-r border-white/10">B</th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-200 border-r border-white/10">C</th>
                  <th className="px-3 py-2 text-right font-semibold text-gray-200 cursor-pointer border-r border-white/10" onClick={() => handleSort('Price')}><div className="flex items-center justify-end gap-1">D {getSortIcon('Price')}</div></th>
                  <th className="px-3 py-2 text-center font-semibold text-gray-200 border-r border-white/10">E</th>
                  <th className="px-3 py-2 text-center font-semibold text-gray-200 cursor-pointer border-r border-white/10" onClick={() => handleSort('SATA')}><div className="flex items-center justify-center gap-1">F {getSortIcon('SATA')}</div></th>
                  <th className="px-3 py-2 text-center font-semibold text-gray-200 border-r border-white/10">G</th>
                  <th className="px-3 py-2 text-center font-semibold text-gray-200 border-r border-white/10">H</th>
                  <th className="px-3 py-2 text-center font-semibold text-gray-200 border-r border-white/10">I</th>
                  <th className="px-3 py-2 text-center font-semibold text-gray-200 border-r border-white/10">J</th>
                  <th className="px-3 py-2 text-center font-semibold text-gray-200 border-r border-white/10">K</th>
                  <th className="px-3 py-2 text-center font-semibold text-gray-200 border-r border-white/10">L</th>
                  <th className="px-3 py-2 text-center font-semibold text-gray-200 border-r border-white/10">M</th>
                  <th className="px-3 py-2 text-center font-semibold text-gray-200 border-r border-white/10">N</th>
                  <th className="px-3 py-2 text-center font-semibold text-gray-200">O</th>
                </tr>
                <tr className="bg-white/10">
                  <th className="px-3 py-2 text-left text-xs text-gray-200 border-r border-white/10">Ticker</th>
                  <th className="px-3 py-2 text-left text-xs text-gray-200 border-r border-white/10">Name</th>
                  <th className="px-3 py-2 text-left text-xs text-gray-200 border-r border-white/10">Sector</th>
                  <th className="px-3 py-2 text-right text-xs text-gray-200 border-r border-white/10">Price</th>
                  <th className="px-3 py-2 text-center text-xs text-gray-200 border-r border-white/10">Swing Days</th>
                  <th className="px-3 py-2 text-center text-xs text-gray-200 border-r border-white/10">SATA</th>
                  <th className="px-3 py-2 text-center text-xs text-gray-200 border-r border-white/10">20SMA</th>
                  <th className="px-3 py-2 text-center text-xs text-gray-200 border-r border-white/10">GMMA</th>
                  <th className="px-3 py-2 text-center text-xs text-gray-200 border-r border-white/10">ATR%</th>
                  <th className="px-3 py-2 text-center text-xs text-gray-200 border-r border-white/10">1D%</th>
                  <th className="px-3 py-2 text-center text-xs text-gray-200 border-r border-white/10">1W%</th>
                  <th className="px-3 py-2 text-center text-xs text-gray-200 border-r border-white/10">1M%</th>
                  <th className="px-3 py-2 text-center text-xs text-gray-200 border-r border-white/10">RS 1M</th>
                  <th className="px-3 py-2 text-center text-xs text-gray-200 border-r border-white/10">RS 3M</th>
                  <th className="px-3 py-2 text-center text-xs text-gray-200">Color</th>
                </tr>
              </thead>
              <tbody>
                {processedData.map((row, rowIndex) => (
                  <tr key={rowIndex} className="border-b border-white/10 hover:bg-white/5">
                    <td className="px-3 py-2 font-bold text-white border-r border-white/10">{row.Ticker}</td>
                    <td className="px-3 py-2 border-r border-white/10"><div className="text-white text-xs">{typeof row.Name === 'string' && row.Name.length > 20 ? row.Name.substring(0, 20) + '...' : row.Name}</div></td>
                    <td className="px-3 py-2 border-r border-white/10"><span className="px-2 py-1 rounded text-xs text-white" style={{ background: 'linear-gradient(135deg, var(--brand-start), var(--brand-end))' }}>{row.Sector}</span></td>
                    <td className="px-3 py-2 text-right border-r border-white/10"><div className="font-mono text-white">${typeof row.Price === 'number' ? row.Price.toFixed(2) : row.Price}</div></td>
                    <td className="px-3 py-2 text-center border-r border-white/10"><div className="font-mono text-yellow-400">{row.Swing_Days}</div></td>
                    <td className={`px-3 py-2 text-center border-r border-white/10 font-mono ${getCellColor(row.SATA, 'sata')}`}>{row.SATA}</td>
                    <td className="px-3 py-2 text-center border-r border-white/10"><span className={`px-2 py-1 rounded text-xs font-bold ${row['20SMA'] === 'U' ? 'bg-green-600 text-white' : row['20SMA'] === 'D' ? 'bg-red-600 text-white' : 'bg-gray-600 text-white'}`}>{row['20SMA']}</span></td>
                    <td className="px-3 py-2 text-center border-r border-white/10"><span className={`font-mono text-sm ${row.GMMA === 'RWB' ? 'text-green-400 font-bold' : row.GMMA === 'BWR' ? 'text-red-400 font-bold' : 'text-gray-400'}`}>{row.GMMA}</span></td>
                    <td className="px-3 py-2 text-center border-r border-white/10"><div className="font-mono text-sm">{row.ATR_Percent}</div></td>
                    <td className={`px-3 py-2 text-center border-r border-white/10 font-mono ${getCellColor(parseFloat(row.Change_1D?.replace(/[^\d.-]/g, '')), 'change')}`}>{row.Change_1D}</td>
                    <td className={`px-3 py-2 text-center border-r border-white/10 font-mono ${getCellColor(parseFloat(row.Change_1W?.replace(/[^\d.-]/g, '')), 'change')}`}>{row.Change_1W}</td>
                    <td className={`px-3 py-2 text-center border-r border-white/10 font-mono ${getCellColor(parseFloat(row.Change_1M?.replace(/[^\d.-]/g, '')), 'change')}`}>{row.Change_1M}</td>
                    <td className={`px-3 py-2 text-center border-r border-white/10 font-bold ${getCellColor(row.RS_1M, 'rs')}`}>{row.RS_1M?.includes('Y') ? 'Y' : row.RS_1M?.includes('N') ? 'N' : 'M'}</td>
                    <td className={`px-3 py-2 text-center border-r border-white/10 font-bold ${getCellColor(row.RS_3M, 'rs')}`}>{row.RS_3M?.includes('Y') ? 'Y' : row.RS_3M?.includes('N') ? 'N' : 'M'}</td>
                    <td className={`px-3 py-2 text-center font-bold ${getCellColor(row.Color_Rule, 'color')}`}>{row.Color_Rule?.includes('Green') ? 'G' : row.Color_Rule?.includes('Red') ? 'R' : 'Y'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Spreadsheet Instructions */}
      <div className="glass-card p-6">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center"><FaTable className="mr-2 text-green-400" />Google Sheets Integration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-lg font-semibold text-white mb-2">How to Import to Google Sheets:</h4>
            <ol className="list-decimal list-inside space-y-2 text-gray-300 text-sm">
              <li>Click "Google Sheets" button above to download the import formula</li>
              <li>Open Google Sheets and create a new spreadsheet</li>
              <li>Copy the formula from the downloaded file</li>
              <li>Paste it into cell A1 of your Google Sheet</li>
              <li>Press Enter to import live data</li>
              <li>Data will auto-refresh periodically</li>
            </ol>
          </div>
          <div>
            <h4 className="text-lg font-semibold text-white mb-2">Spreadsheet Features:</h4>
            <ul className="list-disc list-inside space-y-2 text-gray-300 text-sm">
              <li>📊 Real-time ETF data with live formulas</li>
              <li>🎨 Color-coded cells based on performance</li>
              <li>🔢 Excel/Google Sheets compatible formulas</li>
              <li>📈 Sortable columns (click headers)</li>
              <li>⚙️ Configurable calculation parameters</li>
              <li>📋 CSV export for offline analysis</li>
              <li>🔄 Auto-updating data</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpreadsheetTab;