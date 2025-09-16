import React, { useState, useEffect } from 'react';

const EnhancedNewsSection = () => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [expanded, setExpanded] = useState(false);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  const categories = [
    'All', 
    'My Watchlist', 
    'USA', 
    'South Africa', 
    'Stock Market', 
    'Finance', 
    'World'
  ];

  const loadNews = async (category = 'All') => {
    try {
      setLoading(true);
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

  const handleCategoryChange = (category) => {
    setSelectedCategory(category);
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInHours = Math.floor((now - time) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours === 1) return '1 hour ago';
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays === 1) return '1 day ago';
    return `${diffInDays} days ago`;
  };

  const displayedNews = expanded ? news : news.slice(0, 6);

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="text-white/90 font-semibold">Enhanced News</div>
        <button 
          onClick={() => loadNews(selectedCategory)}
          className="btn btn-outline text-xs py-1"
          disabled={loading}
        >
          {loading ? 'Loading...' : 'Reload'}
        </button>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 mb-4">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => handleCategoryChange(category)}
            className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${
              selectedCategory === category
                ? 'text-white bg-white/10 border border-white/10'
                : 'text-gray-300 hover:text-white hover:bg-white/5 border border-transparent'
            }`}
          >
            {category}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-gray-400 text-sm text-center py-8">
          Loading news articles...
        </div>
      ) : news.length === 0 ? (
        <div className="text-gray-400 text-sm text-center py-8">
          <div className="mb-2">📰</div>
          <div>No news articles available for "{selectedCategory}"</div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {displayedNews.map((article, index) => (
              <div 
                key={index}
                className="rounded-xl border border-white/10 bg-black/30 p-4 hover:bg-black/40 transition-colors group"
              >
                {article.thumbnail && (
                  <div className="w-full h-32 mb-3 rounded-lg overflow-hidden bg-gray-800">
                    <img 
                      src={article.thumbnail} 
                      alt={article.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  </div>
                )}
                
                <div className="flex items-start justify-between mb-2">
                  <div className="text-xs text-cyan-400 font-semibold">
                    {article.source}
                  </div>
                  <div className="text-xs text-gray-400">
                    {formatTimeAgo(article.published)}
                  </div>
                </div>
                
                <h3 className="text-white/90 font-semibold text-sm mb-2 line-clamp-3 leading-snug">
                  {article.title}
                </h3>
                
                {article.summary && (
                  <p className="text-gray-300 text-xs mb-3 line-clamp-2">
                    {article.summary}
                  </p>
                )}
                
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
                >
                  Read more →
                </a>
              </div>
            ))}
          </div>

          {news.length > 6 && (
            <div className="text-center mt-6">
              <button
                onClick={() => setExpanded(!expanded)}
                className="btn btn-outline text-sm"
              >
                {expanded ? 'Show Less' : `Show All ${news.length} Articles`}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default EnhancedNewsSection;