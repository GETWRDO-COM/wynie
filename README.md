# Wynie - ETF Intelligence Engine

A comprehensive web-based platform for ETF analysis, market intelligence, and trading insights.

## Features

- **Market Dashboard**: Real-time market data with South African and US time zones
- **ETF Analysis**: Advanced screening with technical indicators
- **Trading Journal**: Track trades, positions, and performance 
- **News Integration**: Multi-source news aggregation
- **Market Sentiment**: CNN Fear & Greed Index integration
- **Advanced Screener**: Filter stocks by technical, fundamental, and computed metrics

## Quick Start

### Backend Setup

1. **Environment Configuration**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your API keys and database settings
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Backend**
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8001 --reload
   ```

### Frontend Setup  

1. **Environment Configuration**
   ```bash
   cd frontend
   cp .env.example .env
   # Update REACT_APP_BACKEND_URL if needed
   ```

2. **Install Dependencies**
   ```bash
   yarn install
   ```

3. **Run Frontend**
   ```bash
   yarn start
   ```

### Required Environment Variables

#### Backend (.env)
- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `POLYGON_API_KEY`: Polygon.io API key for market data
- `FINNHUB_API_KEY`: Finnhub API key for fundamentals
- `JWT_SECRET`: Secret key for JWT tokens

#### Frontend (.env)
- `REACT_APP_BACKEND_URL`: Backend API URL (default: http://localhost:8001)

## Architecture

### Backend
- **FastAPI**: Modern Python web framework
- **MongoDB**: Document database via Motor (async)
- **Authentication**: JWT-based with bcrypt password hashing
- **Market Data**: Polygon.io and Finnhub integration
- **AI Features**: OpenAI GPT integration for analysis

### Frontend  
- **React**: Modern UI framework
- **Tailwind CSS**: Utility-first styling
- **Chart.js**: Interactive charts and visualizations
- **Axios**: HTTP client for API communication

## New Features

### Advanced Screener
- Filter stocks by 20+ technical indicators
- Fundamental analysis metrics
- Custom filter combinations with AND/OR logic
- Real-time market data integration

### Trading Journal
- Track individual trades and positions
- Performance analytics and risk metrics
- Daily P&L aggregation
- Trade reconstruction from executions

### Enhanced Market Data
- Multi-timeframe chart data
- Real-time quotes and market aggregates
- Earnings calendar integration
- Market sentiment indicators

## Development

### Project Structure
```
wynie/
├── backend/
│   ├── server.py              # Main FastAPI entry point
│   ├── server_enhanced.py     # Core API implementation  
│   ├── indicators.py          # Technical indicators
│   ├── screener_engine.py     # Stock screening engine
│   ├── polygon_client.py      # Polygon.io API client
│   ├── finnhub_client.py      # Finnhub API client
│   ├── etl_schemas.py         # Trading data schemas
│   └── utils_etl.py           # ETL utilities
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   └── App.js            # Main application
│   └── public/
└── docs/
```

### Testing
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests  
cd frontend
yarn test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is proprietary software.
