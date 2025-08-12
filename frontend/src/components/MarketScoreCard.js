import React, { useMemo } from 'react';

const MarketScoreCard = ({ marketScore }) => {
  const updatedDate = marketScore?.last_updated || marketScore?.date;
  const updatedFmt = useMemo(() => updatedDate ? new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(updatedDate)) : null, [updatedDate]);
  const scoreVal = marketScore?.score ?? marketScore?.total_score ?? '--';
  const trendVal = marketScore?.trend ?? marketScore?.classification ?? 'N/A';
  const rec = marketScore?.recommendation;

  return (
    <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-xl p-5 h-full">
      <div className="text-sm text-gray-300 mb-1">Market Score</div>
      <div className="text-4xl font-extrabold text-white mb-2">{scoreVal}</div>
      <div className="text-xs text-gray-400 mb-3">{trendVal}</div>
      {rec && <div className="text-xs text-gray-300 bg-white/5 border border-white/10 rounded-lg p-2">{rec}</div>}
      <div className="text-xs text-gray-500 mt-3">{updatedFmt ? `Updated ${updatedFmt}` : ''}</div>
    </div>
  );
};

export default MarketScoreCard;