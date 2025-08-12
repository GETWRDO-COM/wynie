import React, { useEffect, useMemo, useState } from 'react';

function rel(ts){ if(!ts) return ''; const d=new Date(ts).getTime(); const diff=Math.round((d-Date.now())/60000); const rtf=new Intl.RelativeTimeFormat('en',{numeric:'auto'}); if(Math.abs(diff)<60) return rtf.format(diff,'minute'); const dh=Math.round(diff/60); if(Math.abs(dh)<24) return rtf.format(dh,'hour'); const dd=Math.round(dh/24); return rtf.format(dd,'day'); }

const MarketScoreCard = ({ marketScore }) => {
  const [localScore, setLocalScore] = useState(null);
  const [loading, setLoading] = useState(false);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  const effective = marketScore || localScore;
  const updatedDate = effective?.last_updated || effective?.date;
  const updatedRel = useMemo(() => updatedDate ? rel(updatedDate) : null, [updatedDate]);
  const scoreVal = effective?.score ?? effective?.total_score ?? null;
  const trendVal = effective?.trend ?? effective?.classification ?? 'N/A';
  const rec = effective?.recommendation;

  useEffect(() => {
    if (!marketScore && !localScore && !loading) {
      (async () => {
        try {
          setLoading(true);
          const resp = await fetch(`${BACKEND_URL}/api/market-score`, {
            headers: (() => { const t = localStorage.getItem('authToken'); return t ? { Authorization: `Bearer ${t}` } : {}; })()
          });
          const js = await resp.json();
          setLocalScore(js);
        } catch (e) {
          // no-op; leave localScore null
        } finally { setLoading(false); }
      })();
    }
  }, [marketScore, localScore, loading, BACKEND_URL]);

  return (
    <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-xl p-5 h-full">
      <div className="text-sm text-gray-300 mb-1">Market Score</div>
      <div className="text-4xl font-extrabold text-white mb-2">{scoreVal != null ? scoreVal : (loading ? '…' : '--')}</div>
      <div className="text-xs text-gray-400 mb-3">{trendVal}</div>
      {rec && <div className="text-xs text-gray-300 bg-white/5 border border-white/10 rounded-lg p-2">{rec}</div>}
      <div className="text-xs text-gray-500 mt-3">{updatedRel ? `Updated ${updatedRel}` : ''}</div>
    </div>
  );
};

export default MarketScoreCard;