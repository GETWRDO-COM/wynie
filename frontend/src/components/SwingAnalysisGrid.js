import React, { useState, useEffect, useMemo } from 'react';
import { FaChartLine, FaPlus, FaSort, FaSortUp, FaSortDown, FaEye, FaEyeSlash, FaDownload, FaFilter } from 'react-icons/fa';

const SwingAnalysisGrid = ({ 
  etfs, 
  sectors, 
  selectedSector, 
  setSelectedSector, 
  analyzeChart, 
  addToWatchlist, 
  showFormulas, 
  setShowFormulas, 
  exportToGoogleSheets, 
  exportLoading,
  updateETFData,
  loading 
}) => {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [filterConfig, setFilterConfig] = useState({
    minSATA: 0,
    maxATR: 100,
    hasRS: false,
    minChange: -100,
    maxChange: 100
  });

  // Utility functions
  const getChangeColor = (change) => {
    if (change > 0) return 'text-green-400';
    if (change < 0) return 'text-red-400';
    return 'text-gray-400';
  };

  const getRSBadge = (rs) => {
    if (rs > 0.1) return <span className="bg-green-600 text-white px-2 py-1 rounded-full text-xs font-bold">Y</span>;
    if (rs > 0.02) return <span className="bg-yellow-600 text-white px-2 py-1 rounded-full text-xs font-bold">M</span>;
    return <span className="bg-red-600 text-white px-2 py-1 rounded-full text-xs font-bold">N</span>;
  };

  const getSwingDaysColor = (days) => {
    if (days <= 5) return 'text-green-400';
    if (days <= 15) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getSATAColor = (score) => {
    if (score >= 8) return 'text-green-400 font-bold';
    if (score >= 6) return 'text-yellow-400 font-bold';
    return 'text-red-400 font-bold';
  };

  const getGMMAColor = (pattern) => {
    if (pattern === 'RWB') return 'text-green-400 font-bold';
    if (pattern === 'BWR') return 'text-red-400 font-bold';
    return 'text-gray-400';
  };

  const getRowColor = (etf) => {
    const hasStrong1MRS = etf.relative_strength_1m > 0.1;
    const hasGoodSATA = etf.sata_score >= 7;
    const hasBullishGMMA = etf.gmma_pattern === 'RWB';
    
    if (hasStrong1MRS && hasGoodSATA && hasBullishGMMA) {
      return 'bg-green-900 bg-opacity-30 border-l-4 border-green-500';
    } else if (etf.relative_strength_1m < -0.1 || etf.sata_score <= 3) {
      return 'bg-red-900 bg-opacity-30 border-l-4 border-red-500';
    }
    return 'bg-gray-800 bg-opacity-50 border-l-4 border-yellow-500';
  };

  // Calculate swing days
  const calculateSwingDays = (swingDate) => {
    if (!swingDate) return 0;
    const today = new Date();
    const swing = new Date(swingDate);
    return Math.floor((today - swing) / (1000 * 60 * 60 * 24));
  };

  // Sorting function
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const getSortIcon = (columnName) => {
    if (sortConfig.key !== columnName) return <FaSort className="text-gray-500" />;
    return sortConfig.direction === 'asc' ? <FaSortUp className="text-blue-400" /> : <FaSortDown className="text-blue-400" />;
  };

  // Filtered and sorted data
  const processedEtfs = useMemo(() => {
    let filtered = selectedSector ? etfs.filter(etf => etf.sector === selectedSector) : etfs;
    
    // Apply advanced filters
    filtered = filtered.filter(etf => 
      etf.sata_score >= filterConfig.minSATA &&
      etf.atr_percent <= filterConfig.maxATR &&
      etf.change_1m >= filterConfig.minChange &&
      etf.change_1m <= filterConfig.maxChange &&
      (!filterConfig.hasRS || etf.relative_strength_1m > 0.02)
    );

    // Sort data
    if (sortConfig.key) {
      filtered.sort((a, b) => {
        const aVal = a[sortConfig.key] || 0;
        const bVal = b[sortConfig.key] || 0;
        
        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  }, [etfs, selectedSector, sortConfig, filterConfig]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-3xl font-bold text-white flex items-center">
            📊 Capitalization & Swing Analysis Grid
          </h2>
          <div className="flex gap-2">
            <button 
              onClick={() => setShowFormulas(!showFormulas)}
              className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2"
            >
              {showFormulas ? <FaEyeSlash /> : <FaEye />}
              {showFormulas ? 'Hide' : 'Show'} Formulas
            </button>
            <button 
              onClick={exportToGoogleSheets}
              disabled={exportLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2"
            >
              <FaDownload />
              {exportLoading ? 'Exporting...' : 'Export CSV'}
            </button>
            <button 
              onClick={updateETFData}
              disabled={loading}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 px-4 py-2 rounded-lg text-sm font-medium"
            >
              {loading ? 'Updating...' : '🔄 Update Data'}
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-4">
          <select
            value={selectedSector}
            onChange={(e) => setSelectedSector(e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
          >
            <option value="">All Sectors 📊</option>
            {sectors.map((sector) => (
              <option key={sector} value={sector}>
                {sector}
              </option>
            ))}
          </select>
          
          <input
            type="range"
            min="0"
            max="10"
            value={filterConfig.minSATA}
            onChange={(e) => setFilterConfig({...filterConfig, minSATA: parseInt(e.target.value)})}
            className="bg-gray-700 rounded-lg"
            title={`Min SATA: ${filterConfig.minSATA}`}
          />
          <div className="text-sm text-gray-400">SATA ≥ {filterConfig.minSATA}</div>
          
          <input
            type="range"
            min="0"
            max="10"
            step="0.5"
            value={filterConfig.maxATR}
            onChange={(e) => setFilterConfig({...filterConfig, maxATR: parseFloat(e.target.value)})}
            className="bg-gray-700 rounded-lg"
          />
          <div className="text-sm text-gray-400">ATR ≤ {filterConfig.maxATR}%</div>
          
          <label className="flex items-center text-sm text-gray-300">
            <input
              type="checkbox"
              checked={filterConfig.hasRS}
              onChange={(e) => setFilterConfig({...filterConfig, hasRS: e.target.checked})}
              className="mr-2"
            />
            Has RS
          </label>
        </div>

        {/* Formula Display */}
        {showFormulas && (
          <div className="bg-gray-900 rounded-lg p-4 mb-4">
            <h3 className="text-lg font-semibold text-blue-400 mb-3">📐 Calculation Formulas</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm font-mono">
              <div>
                <div className="text-green-400 font-semibold">Swing Days:</div>
                <div className="text-gray-300">=TODAY() - [Swing_Start_Date]</div>
              </div>
              <div>
                <div className="text-blue-400 font-semibold">SATA Score (1-10):</div>
                <div className="text-gray-300">Performance(40%) + RelStr(30%) + Vol(20%) + ATR(10%)</div>
              </div>
              <div>
                <div className="text-yellow-400 font-semibold">ATR Percent:</div>
                <div className="text-gray-300">=(14_Day_ATR / Current_Price) * 100</div>
              </div>
              <div>
                <div className="text-purple-400 font-semibold">Relative Strength:</div>
                <div className="text-gray-300">=(ETF_Return - SPY_Return) / |SPY_Return|</div>
              </div>
              <div>
                <div className="text-red-400 font-semibold">GMMA Pattern:</div>
                <div className="text-gray-300">RWB: Weekly&gt;0 & Monthly&gt;0, BWR: Both&lt;0</div>
              </div>
              <div>
                <div className="text-cyan-400 font-semibold">Color Logic:</div>
                <div className="text-gray-300">Green: RS&gt;10% & SATA≥7 & GMMA=RWB</div>
              </div>
            </div>
          </div>
        )}

        <div className="text-gray-400 text-sm">
          Showing {processedEtfs.length} of {etfs.length} ETFs • Updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Data Grid */}
      <div className="bg-gray-800 rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300 cursor-pointer" onClick={() => handleSort('ticker')}>
                  <div className="flex items-center gap-2">
                    Ticker {getSortIcon('ticker')}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300">Name</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-300 cursor-pointer" onClick={() => handleSort('sector')}>
                  <div className="flex items-center gap-2">
                    Sector {getSortIcon('sector')}
                  </div>
                </th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-300 cursor-pointer" onClick={() => handleSort('current_price')}>
                  <div className="flex items-center justify-end gap-2">
                    Price {getSortIcon('current_price')}
                  </div>
                </th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-300">Swing Days</th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-300 cursor-pointer" onClick={() => handleSort('sata_score')}>
                  <div className="flex items-center justify-center gap-2">
                    SATA {getSortIcon('sata_score')}
                  </div>
                </th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-300">20SMA</th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-300">GMMA</th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-300 cursor-pointer" onClick={() => handleSort('atr_percent')}>
                  <div className="flex items-center justify-center gap-2">
                    ATR% {getSortIcon('atr_percent')}
                  </div>
                </th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-300 cursor-pointer" onClick={() => handleSort('change_1d')}>
                  <div className="flex items-center justify-center gap-2">
                    1D% {getSortIcon('change_1d')}
                  </div>
                </th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-300 cursor-pointer" onClick={() => handleSort('change_1w')}>
                  <div className="flex items-center justify-center gap-2">
                    1W% {getSortIcon('change_1w')}
                  </div>
                </th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-300 cursor-pointer" onClick={() => handleSort('change_1m')}>
                  <div className="flex items-center justify-center gap-2">
                    1M% {getSortIcon('change_1m')}
                  </div>
                </th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-300">RS Flags</th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-300">Actions</th>
              </tr>
            </thead>
            <tbody>
              {processedEtfs.map((etf) => {
                const swingDays = calculateSwingDays(etf.swing_start_date);
                
                return (
                  <tr key={etf.ticker} className={`border-b border-gray-700 hover:bg-gray-700 transition-colors ${getRowColor(etf)}`}>
                    <td className="px-4 py-4">
                      <div className="font-bold text-blue-300 text-lg">{etf.ticker}</div>
                      <div className="text-xs text-gray-400">{etf.theme}</div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="text-white text-sm font-medium">
                        {etf.name?.length > 25 ? etf.name.substring(0, 25) + '...' : etf.name}
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className="px-2 py-1 bg-gray-700 rounded-full text-xs font-medium text-gray-300">
                        {etf.sector}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-right">
                      <div className="font-semibold text-white">
                        ${etf.current_price?.toFixed(2)}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <div className={`font-bold text-lg ${getSwingDaysColor(swingDays)}`}>
                        {swingDays}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <div className={`font-bold text-xl ${getSATAColor(etf.sata_score)}`}>
                        {etf.sata_score}/10
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                        etf.sma20_trend === 'U' ? 'bg-green-600 text-white' :
                        etf.sma20_trend === 'D' ? 'bg-red-600 text-white' :
                        'bg-gray-600 text-white'
                      }`}>
                        {etf.sma20_trend || 'F'}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <span className={`font-bold text-sm ${getGMMAColor(etf.gmma_pattern)}`}>
                        {etf.gmma_pattern || 'Mixed'}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <div className={`font-semibold ${
                        etf.atr_percent > 5 ? 'text-red-400' :
                        etf.atr_percent > 2 ? 'text-yellow-400' :
                        'text-green-400'
                      }`}>
                        {etf.atr_percent?.toFixed(2)}%
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <div className={`font-semibold ${getChangeColor(etf.change_1d)}`}>
                        {etf.change_1d > 0 ? '+' : ''}{etf.change_1d?.toFixed(2)}%
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <div className={`font-semibold ${getChangeColor(etf.change_1w)}`}>
                        {etf.change_1w > 0 ? '+' : ''}{etf.change_1w?.toFixed(2)}%
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <div className={`font-semibold ${getChangeColor(etf.change_1m)}`}>
                        {etf.change_1m > 0 ? '+' : ''}{etf.change_1m?.toFixed(2)}%
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <div className="flex justify-center gap-1">
                        <div className="flex flex-col gap-1 text-xs">
                          <div>1M: {getRSBadge(etf.relative_strength_1m)}</div>
                          <div>3M: {getRSBadge(etf.relative_strength_3m)}</div>
                          <div>6M: {getRSBadge(etf.relative_strength_6m)}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <div className="flex flex-col gap-2">
                        <button
                          onClick={() => analyzeChart(etf.ticker)}
                          className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded-lg text-xs font-medium flex items-center gap-1"
                        >
                          <FaChartLine />
                          Analyze
                        </button>
                        <button
                          onClick={() => addToWatchlist(etf.ticker, etf.name, 'Swing Analysis')}
                          className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded-lg text-xs font-medium flex items-center gap-1"
                        >
                          <FaPlus />
                          Watch
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {processedEtfs.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <FaFilter className="text-4xl mx-auto mb-4 opacity-50" />
          <p className="text-lg">No ETFs match your current filters</p>
          <p className="text-sm mt-2">Try adjusting the sector filter or clearing some criteria</p>
        </div>
      )}
    </div>
  );
};

export default SwingAnalysisGrid;