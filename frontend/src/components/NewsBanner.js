import React, { useState, useEffect } from 'react';

const NewsBanner = () => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [scrollSpeed, setScrollSpeed] = useState(80); // seconds for full scroll
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  const categories = ['All', 'USA', 'South Africa', 'World', 'Stock Market', 'Finance'];

  const loadNews = async (category = 'All') => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/news?category=${encodeURIComponent(category)}`, {
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
    loadNews(selectedCategory);
  }, [selectedCategory]);

  if (loading || news.length === 0) {
    return (
      <div 
        className="fixed bottom-0 left-0 right-0 z-50 bg-black/95 backdrop-blur-xl border-t border-white/10 h-16"
        style={{ zIndex: 2000 }}
      >
        <div className="flex items-center h-full px-4">
          <div className="text-amber-400 text-sm font-semibold mr-4">📺 Breaking News:</div>
          <div className="text-white text-sm">
            {loading ? 'Loading latest headlines...' : 'No headlines available'}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="fixed bottom-0 left-0 right-0 z-50 bg-black/95 backdrop-blur-xl border-t border-white/10 h-16"
      style={{ zIndex: 2000 }}
    >
      {/* News Controls and Ticker */}
      <div className="flex items-center h-full">
        {/* News Category Dropdown */}
        <div className="flex items-center gap-2 px-4 bg-black/80 border-r border-white/10">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="text-sm bg-white/10 text-white border border-white/20 rounded px-3 py-1.5 font-medium"
          >
            {categories.map(cat => (
              <option key={cat} value={cat} className="bg-black text-white">{cat}</option>
            ))}
          </select>
        </div>
        
        {/* Speed Controls */}
        <div className="flex items-center gap-1 px-3 bg-black/80 border-r border-white/10">
          <button
            onClick={() => setScrollSpeed(Math.min(scrollSpeed + 20, 160))}
            className="text-sm bg-white/10 text-white border border-white/20 rounded px-2 py-1 hover:bg-white/20 transition-colors"
            title="Slow down"
          >
            🐌
          </button>
          <button
            onClick={() => setScrollSpeed(Math.max(scrollSpeed - 20, 40))}
            className="text-sm bg-white/10 text-white border border-white/20 rounded px-2 py-1 hover:bg-white/20 transition-colors"
            title="Speed up"
          >
            🚀
          </button>
        </div>

        {/* News Ticker */}
        <div className="flex-1 overflow-hidden relative">
          <div 
            className="flex items-center whitespace-nowrap text-white text-sm animate-marquee"
            style={{
              animation: `marquee ${scrollSpeed}s linear infinite`
            }}
          >
            {news.map((article, index) => (
              <React.Fragment key={index}>
                <div className="flex items-center gap-2 mx-3">
                  <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent font-semibold text-xs px-2 py-1 border border-cyan-400/30 rounded whitespace-nowrap">
                    {selectedCategory === 'All' ? getArticleCategory(article) : selectedCategory}
                  </span>
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-cyan-400 transition-colors cursor-pointer"
                  >
                    {article.title}
                  </a>
                  <span className="text-gray-400 text-xs whitespace-nowrap">
                    - {article.source}
                  </span>
                </div>
                {index < news.length - 1 && (
                  <div className="mx-2 text-amber-400">•</div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
      
      <style jsx>{`
        @keyframes marquee {
          0% { transform: translateX(100%); }
          100% { transform: translateX(-100%); }
        }
        .animate-marquee {
          animation: marquee ${scrollSpeed}s linear infinite;
        }
      `}</style>
    </div>
  );
};

// Helper function to categorize articles
const getArticleCategory = (article) => {
  const title = article.title.toLowerCase();
  const source = article.source.toLowerCase();
  
  if (source.includes('bloomberg') || source.includes('reuters') || title.includes('stock') || title.includes('market')) {
    return 'MARKET';
  }
  if (title.includes('usa') || title.includes('america') || source.includes('cnn') || source.includes('fox')) {
    return 'USA';
  }
  if (title.includes('south africa') || source.includes('news24')) {
    return 'SA';
  }
  return 'WORLD';
};

export default NewsBanner;