import React from 'react';

const Dashboard = ({ 
  marketScore, 
  swingLeaders, 
  leaders, 
  getScoreColor, 
  getRSBadge, 
  getChangeColor, 
  analyzeChart 
}) => {
  return (
    <div className="space-y-8">
      {/* Market Score Card */}
      {marketScore && (
        <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
          <h2 className="text-2xl font-bold mb-4">🎯 Market Situational Awareness Engine (MSAE)</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className={`text-4xl font-bold p-4 rounded-lg ${getScoreColor(marketScore.total_score)}`}>
                {marketScore.total_score}/40
              </div>
              <p className="text-lg font-semibold mt-2">{marketScore.classification}</p>
            </div>
            <div className="md:col-span-2">
              <h3 className="text-lg font-semibold mb-2">Current Recommendation:</h3>
              <p className="text-gray-300 mb-4">{marketScore.recommendation}</p>
              <div className="grid grid-cols-4 gap-2 text-sm">
                <div className="bg-gray-700 p-2 rounded">SATA: {marketScore.sata_score}/5</div>
                <div className="bg-gray-700 p-2 rounded">ADX: {marketScore.adx_score}/5</div>
                <div className="bg-gray-700 p-2 rounded">VIX: {marketScore.vix_score}/5</div>
                <div className="bg-gray-700 p-2 rounded">ATR: {marketScore.atr_score}/5</div>
                <div className="bg-gray-700 p-2 rounded">GMI: {marketScore.gmi_score}/5</div>
                <div className="bg-gray-700 p-2 rounded">NH-NL: {marketScore.nhnl_score}/5</div>
                <div className="bg-gray-700 p-2 rounded">F&G: {marketScore.fg_index_score}/5</div>
                <div className="bg-gray-700 p-2 rounded">QQQ ATH: {marketScore.qqq_ath_distance_score}/5</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top 5 Swing Leaders */}
      <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
        <h2 className="text-2xl font-bold mb-4">🚀 Top 5 Swing Leaders (SATA + RS Combined)</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {swingLeaders.map((etf, index) => (
            <div key={etf.ticker} className="bg-gray-700 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold mb-2">#{index + 1}</div>
              <div className="text-lg font-semibold text-blue-300">{etf.ticker}</div>
              <div className="text-sm text-gray-400 mb-2">{etf.name?.slice(0, 20)}...</div>
              <div className="text-sm">
                <div>SATA: <span className="font-semibold">{etf.sata_score}/10</span></div>
                <div className="mt-1">{getRSBadge(etf.relative_strength_1m)}</div>
                <div className={`mt-1 font-semibold ${getChangeColor(etf.change_1m)}`}>
                  {etf.change_1m > 0 ? '+' : ''}{etf.change_1m?.toFixed(2)}% (1M)
                </div>
              </div>
              <button
                onClick={() => analyzeChart(etf.ticker)}
                className="mt-2 bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-xs"
              >
                📈 Analyze
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Risk-On/Off Summary */}
      <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
        <h2 className="text-2xl font-bold mb-4">⚖️ Risk-On vs Risk-Off Signals</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold text-green-400 mb-3">🟢 Risk-On Signals</h3>
            <div className="space-y-2">
              {leaders.filter(etf => 
                ['TQQQ', 'FFTY', 'MGK', 'QQQ', 'SPXL'].includes(etf.ticker) && etf.change_1d > 0
              ).map(etf => (
                <div key={etf.ticker} className="flex justify-between bg-green-900 bg-opacity-30 p-2 rounded">
                  <span className="font-semibold">{etf.ticker}</span>
                  <span className="text-green-400">+{etf.change_1d.toFixed(2)}%</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-red-400 mb-3">🔴 Risk-Off Signals</h3>
            <div className="space-y-2">
              {leaders.filter(etf => 
                ['SQQQ', 'VIX', 'TLT', 'GLD'].includes(etf.ticker) && etf.change_1d > 0
              ).map(etf => (
                <div key={etf.ticker} className="flex justify-between bg-red-900 bg-opacity-30 p-2 rounded">
                  <span className="font-semibold">{etf.ticker}</span>
                  <span className="text-red-400">+{etf.change_1d.toFixed(2)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;