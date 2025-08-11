import React, { useEffect, useMemo, useState } from 'react';

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
      const parsed = parseRSS(text).slice(0, 40);
      setItems(parsed);
    } catch (e) {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeed(category);
    const id = setInterval(() => fetchFeed(category), 180000);
    return () => clearInterval(id);
  }, [category]);

  const parts = useMemo(() => {
    const arr = loading ? ['Loading news…'] : items.length ? items.map((it) => it.title) : ['No headlines available'];
    return arr;
  }, [items, loading]);

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40">
      <div className="mx-auto max-w-7xl">
        <div className="backdrop-blur bg-black/50 border border-white/10 rounded-xl flex items-center gap-3 px-3 py-1.5 mb-3">
          <div className="flex items-center gap-2 min-w-[190px] text-xs text-white/85">
            Breaking News
            <select value={category} onChange={(e) => setCategory(e.target.value)} className="form-select text-xs py-0.5 px-2">
              {Object.keys(FEEDS).map((k) => (
                <option key={k} value={k}>{k}</option>
              ))}
            </select>
          </div>
          <div className="relative flex-1 overflow-hidden h-6">
            <div className="absolute inset-0 pointer-events-none bg-gradient-to-r from-black/50 via-transparent to-black/50" />
            <div className="absolute whitespace-nowrap will-change-transform animate-[ticker_60s_linear_infinite] text-xs text-white/90">
              {parts.map((t, i) => (
                <span key={i} className="inline-flex items-center">
                  {i > 0 && <span className="mx-3 text-white/40">|</span>}
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
      <style>{`@keyframes ticker { 0% { transform: translateX(100%);} 100% { transform: translateX(-100%);} }`}</style>
    </div>
  );
};

export default NewsTicker;