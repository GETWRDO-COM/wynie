import React, { useState, useEffect } from 'react';

const NewsBanner = () => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  const loadNews = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/news?category=All`, {
        headers: (() => { 
          const token = localStorage.getItem('authToken'); 
          return token ? { Authorization: `Bearer ${token}` } : {}; 
        })()
      });
      
      if (response.ok) {
        const data = await response.json();
        setNews(data.articles || []);
      }
    } catch (error) {
      console.error('Failed to load news:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNews();
    // Refresh news every 10 minutes
    const interval = setInterval(loadNews, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading || news.length === 0) {
    return (
      <div 
        className="fixed bottom-0 left-0 right-0 z-50 bg-black/90 backdrop-blur-xl border-t border-white/10 h-12 flex items-center"
        style={{ zIndex: 2000 }}
      >
        <div className="flex items-center text-amber-400 text-sm font-semibold px-4">
          📺 Breaking News: {loading ? 'Loading...' : 'No headlines available'}
        </div>
      </div>
    );
  }

  const newsText = news.map(article => article.title).join(' • ');

  return (
    <div 
      className="fixed bottom-0 left-0 right-0 z-50 bg-black/90 backdrop-blur-xl border-t border-white/10 h-12 overflow-hidden"
      style={{ zIndex: 2000 }}
    >
      <div className="flex items-center h-full">
        <div className="flex items-center text-amber-400 text-sm font-semibold px-4 whitespace-nowrap">
          📺 Breaking News:
        </div>
        <div className="flex-1 overflow-hidden">
          <div 
            className="animate-marquee text-white text-sm whitespace-nowrap"
            style={{
              animation: 'marquee 120s linear infinite'
            }}
          >
            {newsText}
          </div>
        </div>
      </div>
      
      <style jsx>{`
        @keyframes marquee {
          0% { transform: translateX(100%); }
          100% { transform: translateX(-100%); }
        }
        .animate-marquee {
          animation: marquee 120s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default NewsBanner;