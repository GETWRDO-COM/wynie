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

  const color = scoreVal==null? 'from-gray-600 to-gray-800' : (scoreVal<=33? 'from-red-600 to-red-800' : (scoreVal<=66? 'from-yellow-600 to-yellow-800' : 'from-green-600 to-green-800'));
  return (
    <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-xl p-6 h-full relative overflow-hidden">
      <div className={`absolute -inset-1 opacity-30 blur-2xl bg-gradient-to-br ${color}`} />
      <div className="relative">
        <div className="text-sm text-gray-300 mb-1">Market Score</div>
        <div className="flex items-end gap-3 mb-2">
          <div className="text-5xl font-extrabold text-white drop-shadow-[0_0_20px_rgba(255,255,255,0.25)]">{scoreVal != null ? scoreVal : (loading ? '…' : '--')}</div>
          <div className="text-xs text-white/90 bg-white/10 border border-white/20 rounded px-2 py-0.5">{trendVal}</div>
        </div>
        {rec && <div className="text-xs text-white/90 bg-white/10 border border-white/20 rounded-lg p-2">{rec}</div>}
        <div className="text-xs text-gray-300 mt-3">{updatedRel ? `Updated ${updatedRel}` : ''}</div>
      </div>
    </div>
  );
};

export default MarketScoreCard;