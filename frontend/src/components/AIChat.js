import React, { useState, useEffect } from 'react';
import { FaRobot, FaSpinner } from 'react-icons/fa';

// Simple AI Chat panel extracted into its own component
// Requires an axios instance via props.api
const AIChat = ({ api, user }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('latest');
  const [availableModels, setAvailableModels] = useState({});
  const [currentSession, setCurrentSession] = useState(null);
  const [ticker, setTicker] = useState('');
  const [includeChart, setIncludeChart] = useState(false);

  useEffect(() => {
    fetchAvailableModels();
    createNewSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchAvailableModels = async () => {
    try {
      const response = await api.get('/api/ai/models');
      setAvailableModels(response.data.models || {});
      setSelectedModel(response.data.recommended || 'latest');
    } catch (err) {
      console.error('Failed to fetch AI models:', err);
    }
  };

  const createNewSession = async () => {
    try {
      const sessionData = { title: 'New Trading Chat', model: selectedModel };
      const response = await api.post('/api/ai/sessions', sessionData);
      setCurrentSession(response.data.id);
      setMessages([]);
    } catch (err) {
      console.error('Failed to create chat session:', err);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
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
    } catch (err) {
      const errorMessage = { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.', timestamp: new Date().toISOString() };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-6 h-[600px] flex flex-col animate-fade-in">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-white flex items-center">
          <FaRobot className="mr-2 text-blue-400" />
          AI Trading Assistant
        </h2>
        <div className="flex gap-2">
          <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)} className="form-select text-sm">
            {Object.entries(availableModels).map(([key, model]) => (
              <option key={key} value={key}>{key === 'latest' ? `🚀 Latest (${model})` : `${key}`}</option>
            ))}
          </select>
          <button onClick={createNewSession} className="btn btn-secondary">New Chat</button>
        </div>
      </div>
      <div className="mb-4 p-3 bg-white/5 rounded-lg">
        <div className="flex items-center gap-4">
          <label className="flex items-center text-sm text-gray-300">
            <input type="checkbox" checked={includeChart} onChange={(e) => setIncludeChart(e.target.checked)} className="mr-2" />
            Include Chart Analysis
          </label>
          {includeChart && (
            <input type="text" placeholder="Enter ticker (e.g., AAPL, SPY)" value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} className="px-3 py-1 bg-gray-700 border border-white/10 rounded text-white text-sm" />
          )}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto mb-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-gray-400 text-center py-8">
            <FaRobot className="text-4xl mx-auto mb-4 opacity-50" />
            <p>Welcome to your AI Trading Assistant!</p>
            <p className="text-sm mt-2">Ask me about market analysis, trading strategies, or specific stocks.</p>
          </div>
        )}
        {messages.map((message, index) => (
          <div key={index} className={`p-3 rounded-lg ${message.role === 'user' ? 'bg-blue-600/90 ml-12 text-white glow-ring' : 'bg-white/5 mr-12 text-gray-100'}`}>
            <div className="text-sm opacity-75 mb-1">{message.role === 'user' ? 'You' : `AI (${selectedModel})`}</div>
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>
        ))}
        {loading && (
          <div className="bg-white/5 mr-12 p-3 rounded-lg">
            <div className="flex items-center text-gray-300">
              <FaSpinner className="animate-spin mr-2" />
              AI is thinking...
            </div>
          </div>
        )}
      </div>
      <form onSubmit={sendMessage} className="flex gap-2">
        <input type="text" value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} placeholder={includeChart && ticker ? `Ask about ${ticker} chart...` : 'Ask me about trading, markets, or analysis...'} className="flex-1 form-input" disabled={loading} />
        <button type="submit" disabled={loading || !inputMessage.trim()} className="btn btn-primary disabled:opacity-50">Send</button>
      </form>
    </div>
  );
};

export default AIChat;