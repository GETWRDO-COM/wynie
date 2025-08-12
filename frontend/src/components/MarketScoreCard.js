import React, { useMemo } from 'react';

function rel(ts){ if(!ts) return ''; const d=new Date(ts).getTime(); const diff=Math.round((d-Date.now())/60000); const rtf=new Intl.RelativeTimeFormat('en',{numeric:'auto'}); if(Math.abs(diff)<60) return rtf.format(diff,'minute'); const dh=Math.round(diff/60); if(Math.abs(dh)<24) return rtf.format(dh,'hour'); const dd=Math.round(dh/24); return rtf.format(dd,'day'); }

const MarketScoreCard = ({ marketScore }) => {
  const updatedDate = marketScore?.last_updated || marketScore?.date;
  const updatedRel = useMemo(() => updatedDate ? rel(updatedDate) : null, [updatedDate]);
  const scoreVal = marketScore?.score ?? marketScore?.total_score ?? '--';
  const trendVal = marketScore?.trend ?? marketScore?.classification ?? 'N/A';
  const rec = marketScore?.recommendation;

  return (
    <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-xl p-5 h-full">
      <div className="text-sm text-gray-300 mb-1">Market Score</div>
      <div className="text-4xl font-extrabold text-white mb-2">{scoreVal}</div>
      <div className="text-xs text-gray-400 mb-3">{trendVal}</div>
      {rec && <div className="text-xs text-gray-300 bg-white/5 border border-white/10 rounded-lg p-2">{rec}</div>}
      <div className="text-xs text-gray-500 mt-3">{updatedRel ? `Updated ${updatedRel}` : ''}</div>
    </div>
  );
};

export default MarketScoreCard;