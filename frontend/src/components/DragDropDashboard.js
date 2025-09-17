import React, { useState, useRef } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import HeroBanner from './HeroBanner';
import GreedFearCard from './GreedFearCard';
import MarketScoreCard from './MarketScoreCard';
import MyPerformance from './MyPerformance';
import MarketCharts from './MarketCharts';
import WatchlistsSection from './WatchlistsSection';
import EnhancedNewsSection from './EnhancedNewsSection';
import EarningsCalendar from './EarningsCalendar';

const DragDropDashboard = ({ user, api, marketScore }) => {
  const [cards, setCards] = useState([
    { id: 'hero', type: 'hero', size: 'full', title: 'Main Dashboard' },
    { id: 'greed-fear', type: 'greed-fear', size: 'half', title: 'Fear & Greed Index' },
    { id: 'market-score', type: 'market-score', size: 'half', title: 'Market Score' },
    { id: 'performance', type: 'performance', size: 'full', title: 'My Performance' },
    { id: 'charts', type: 'charts', size: 'full', title: 'Market Charts' },
    { id: 'watchlists', type: 'watchlists', size: 'half', title: 'Watchlists' },
    { id: 'news', type: 'news', size: 'half', title: 'Enhanced News' },
    { id: 'earnings', type: 'earnings', size: 'full', title: 'Earnings Calendar' }
  ]);

  const [editMode, setEditMode] = useState(false);

  const onDragEnd = (result) => {
    if (!result.destination) return;

    const newCards = Array.from(cards);
    const [reorderedCard] = newCards.splice(result.source.index, 1);
    newCards.splice(result.destination.index, 0, reorderedCard);

    setCards(newCards);
  };

  const changeCardSize = (cardId, newSize) => {
    setCards(cards.map(card => 
      card.id === cardId ? { ...card, size: newSize } : card
    ));
  };

  const removeCard = (cardId) => {
    setCards(cards.filter(card => card.id !== cardId));
  };

  const addCard = (type) => {
    const newCard = {
      id: `${type}-${Date.now()}`,
      type,
      size: 'half',
      title: type.charAt(0).toUpperCase() + type.slice(1)
    };
    setCards([...cards, newCard]);
  };

  const renderCard = (card) => {
    const baseClasses = {
      full: 'col-span-1 lg:col-span-2',
      half: 'col-span-1',
      quarter: 'col-span-1 lg:col-span-1'
    };

    const cardContent = () => {
      switch (card.type) {
        case 'hero':
          return <HeroBanner user={user} />;
        case 'greed-fear':
          return <GreedFearCard />;
        case 'market-score':
          return <MarketScoreCard marketScore={marketScore} />;
        case 'performance':
          return <MyPerformance api={api} />;
        case 'charts':
          return <MarketCharts />;
        case 'watchlists':
          return <WatchlistsSection />;
        case 'news':
          return <EnhancedNewsSection />;
        case 'earnings':
          return <EarningsCalendar />;
        default:
          return <div className="glass-panel p-4">Unknown card type</div>;
      }
    };

    return (
      <div className={`${baseClasses[card.size]} relative group`}>
        {editMode && (
          <div className="absolute top-2 right-2 z-10 flex gap-1">
            <select
              value={card.size}
              onChange={(e) => changeCardSize(card.id, e.target.value)}
              className="text-xs bg-black/80 text-white border border-white/20 rounded px-1 py-0.5"
            >
              <option value="quarter">1/4</option>
              <option value="half">1/2</option>
              <option value="full">Full</option>
            </select>
            <button
              onClick={() => removeCard(card.id)}
              className="text-xs bg-red-500/80 text-white border border-red-400/40 rounded px-1 py-0.5 hover:bg-red-600/80"
            >
              ✕
            </button>
          </div>
        )}
        {cardContent()}
      </div>
    );
  };

  if (!editMode) {
    return (
      <>
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <button
            onClick={() => setEditMode(true)}
            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all"
          >
            🎨 Customize
          </button>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 auto-rows-max">
          {cards.map((card) => (
            <div key={card.id}>
              {renderCard(card)}
            </div>
          ))}
        </div>
      </>
    );
  }

  return (
    <>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white">Dashboard - Edit Mode</h1>
        <div className="flex gap-2">
          <select
            onChange={(e) => e.target.value && addCard(e.target.value)}
            className="bg-black/80 text-white border border-white/20 rounded px-3 py-2"
            defaultValue=""
          >
            <option value="">+ Add Card</option>
            <option value="greed-fear">Fear & Greed</option>
            <option value="market-score">Market Score</option>
            <option value="charts">Charts</option>
            <option value="watchlists">Watchlists</option>
            <option value="news">News</option>
            <option value="earnings">Earnings</option>
          </select>
          <button
            onClick={() => setEditMode(false)}
            className="px-4 py-2 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-lg hover:from-green-600 hover:to-blue-600 transition-all"
          >
            ✓ Done
          </button>
        </div>
      </div>

      <DragDropContext onDragEnd={onDragEnd}>
        <Droppable droppableId="dashboard">
          {(provided) => (
            <div
              {...provided.droppableProps}
              ref={provided.innerRef}
              className="grid grid-cols-1 lg:grid-cols-2 gap-6 auto-rows-max"
            >
              {cards.map((card, index) => (
                <Draggable key={card.id} draggableId={card.id} index={index}>
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      {...provided.dragHandleProps}
                      className={`${snapshot.isDragging ? 'opacity-80 scale-105' : ''} transition-all`}
                    >
                      {renderCard(card)}
                    </div>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </DragDropContext>
    </>
  );
};

export default DragDropDashboard;