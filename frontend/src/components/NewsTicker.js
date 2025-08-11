import React, { useEffect, useMemo, useRef, useState } from 'react';

const FEEDS = {
  All: 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',
  USA: 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',
  World: 'https://news.google.com/rss/search?q=world%20news&hl=en-US&gl=US&ceid=US:en',
  'South Africa': 'https://news.google.com/rss?hl=en-ZA&gl=ZA&ceid=ZA:en',
  'Stock Market': 'https://news.google.com/rss/search?q=stock%20market&hl=en-US&gl=US&ceid=US:en',
  'Finance News': 'https://news.google.com/rss/search?q=finance&hl=en-US&gl=US&ceid=US:en',
};

function parseRSS(xmlText) {
  try {
    const items = [];
    const doc = new window.DOMParser().parseFromString(xmlText, 'text/xml');
    const nodes = doc.querySelectorAll('item');
    nodes.forEach((n) => {
      const title = n.querySelector('title')?.textContent || '';
      const link = n.querySelector('link')?.textContent || '#';
      if (title) items.push({ title, link });
    });
    return items;
  } catch {
    return [];
  }
}

const NewsTicker = () => {
  const [category, setCategory] = useState('All');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchFeed = async (cat) => {
    const url = FEEDS[cat] || FEEDS.All;
    const proxied = `https://api.allorigins.win/raw?url=${encodeURIComponent(url)}`;
    setLoading(true);
    try {
      const resp = await fetch(proxied);
      const text = await resp.text();
      const parsed = parseRSS(text).slice(0, 30);
      setItems(parsed);
    } catch (e) {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeed(category);
    const id = setInterval(() => fetchFeed(category), 180000); // refresh 3 min
    return () => clearInterval(id);
  }, [category]);

  const content = useMemo(() => {
    if (loading) return 'Loading news…';
    if (!items.length) return 'No headlines available right now';
    return items.map((it) => `• ${it.title}`).join('    ');
  }, [items, loading]);

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40">
      <div className="mx-auto max-w-7xl">
        <div className="glass-panel flex items-center gap-3 px-3 py-2 mb-3" style={{ backdropFilter: 'saturate(160%) blur(10px)' }}>
          <div className="flex items-center gap-2 min-w-[180px]">
            <span className="text-xs text-white/80">Breaking News</span>
            <select value={category} onChange={(e) => setCategory(e.target.value)} className="form-select text-xs py-1 px-2">
              {Object.keys(FEEDS).map((k) => (
                <option key={k} value={k}>{k}</option>
              ))}
            </select>
          </div>
          <div className="relative flex-1 overflow-hidden h-6">
            <div className="absolute whitespace-nowrap will-change-transform animate-[ticker_30s_linear_infinite] text-xs text-white/90">
              {content}
            </div>
          </div>
        </div>
      </div>
      <style>{`
        @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
      `}</style>
    </div>
  );
};

export default NewsTicker;