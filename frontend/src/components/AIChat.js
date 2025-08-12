import React, { useState, useEffect, useRef } from 'react';
import { FaRobot, FaSpinner } from 'react-icons/fa';

// AI Chat panel (WRDO)
const AIChat = ({ api, user }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('latest');
  const [currentSession, setCurrentSession] = useState(null);
  const [ticker, setTicker] = useState('');
  const [includeChart, setIncludeChart] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    fetchModels();
    createNewSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchModels = async () => {
    try {
      const response = await api.get('/api/ai/models');
      // Only expose two options in UI, but keep latest auto
      setSelectedModel(response.data.recommended || 'latest');
    } catch (err) {
      console.error('Failed to fetch AI models:', err);
    }
  };

  const createNewSession = async () => {
    try {
      const sessionData = { title: 'New WRDO Chat', model: selectedModel };
      const response = await api.post('/api/ai/sessions', sessionData);
      setCurrentSession(response.data.id);
      setMessages([]);
      setTimeout(() => inputRef.current?.focus(), 50);
    } catch (err) {
      console.error('Failed to create chat session:', err);
    }
  };

  const submit = async () => {
    if (!inputMessage.trim() || !currentSession) return;
    const userMessage = { role: 'user', content: inputMessage, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    try {
      const response = await api.post('/api/ai/chat', {
        session_id: currentSession,
        message: inputMessage,
        model: selectedModel,
        ticker: includeChart ? ticker : null,
        include_chart_data: includeChart && ticker
      });
      const aiMessage = { role: 'assistant', content: response.data.response, timestamp: new Date().toISOString() };
      setMessages(prev => [...prev, aiMessage]);
      setInputMessage('');
      setTimeout(() => inputRef.current?.focus(), 50);
    } catch (err) {
      const errorMessage = { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.', timestamp: new Date().toISOString() };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if ((e.key === 'Enter') && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      submit();
    }
  };

  const primaryModels = [
    { key: 'latest', label: 'Auto' },
    { key: 'gpt-5', label: 'GPT‑5' },
    { key: 'gpt-5-think', label: 'GPT‑5 Think' },
  ];

  return (
    <div className="glass-card p-4 h-full flex flex-col animate-fade-in">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-xl font-bold text-white flex items-center">
          <FaRobot className="mr-2 text-blue-400" />
          WRDO
        </h2>
        <div className="flex items-center gap-2">
          <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)} className="form-select text-sm">
            {primaryModels.map(m => (
              <option key={m.key} value={m.key}>{m.label}</option>
            ))}
          </select>
          <button onClick={createNewSession} className="btn btn-secondary">New Chat</button>
        </div>
      </div>

      <div className="mb-3 p-3 bg-white/5 rounded-lg">
        <div className="flex items-center gap-4">
          <label className="flex items-center text-sm text-gray-300">
            <input type="checkbox" checked={includeChart} onChange={(e) => setIncludeChart(e.target.checked)} className="mr-2" />
            Include Chart Analysis
          </label>
          {includeChart && (
            <input type="text" placeholder="Ticker (e.g., AAPL, SPY)" value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} className="px-3 py-1 bg-gray-700 border border-white/10 rounded text-white text-sm" />
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto mb-3 space-y-3">
        {messages.length === 0 && (
          <div className="text-gray-400 text-center py-8">
            <FaRobot className="text-3xl mx-auto mb-3 opacity-50" />
            <p>Welcome to WRDO. Ask about markets, strategies, or a specific stock.</p>
          </div>
        )}
        {messages.map((message, index) => (
          <div key={index} className={`p-3 rounded-lg ${message.role === 'user' ? 'bg-blue-600/90 ml-12 text-white glow-ring' : 'bg-white/5 mr-12 text-gray-100'}`}>
            <div className="text-xs opacity-75 mb-1">{message.role === 'user' ? 'You' : `WRDO (${selectedModel})`}</div>
            <div className="whitespace-pre-wrap text-sm">{message.content}</div>
          </div>
        ))}
        {loading && (
          <div className="bg-white/5 mr-12 p-3 rounded-lg">
            <div className="flex items-center text-gray-300 text-sm">
              <FaSpinner className="animate-spin mr-2" />
              WRDO is thinking...
            </div>
          </div>
        )}
      </div>

      <form onSubmit={(e)=>{e.preventDefault(); submit();}} className="flex gap-2">
        <input id="wrdo-chat-input" ref={inputRef} type="text" value={inputMessage} onKeyDown={onKeyDown} onChange={(e) => setInputMessage(e.target.value)} placeholder={includeChart && ticker ? `Ask about ${ticker} chart…` : 'Type to chat with WRDO…'} className="flex-1 form-input" disabled={loading} />
        <button type="submit" disabled={loading || !inputMessage.trim()} className="btn btn-primary disabled:opacity-50">Send</button>
      </form>
    </div>
  );
};

export default AIChat;