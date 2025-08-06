# Authentication Routes
@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    """Authenticate user and return access token"""
    try:
        # For the specific user, create account if it doesn't exist
        user = await db.users.find_one({"email": user_data.email})
        
        if not user:
            # Create the default user account
            if user_data.email == "beetge@mwebbiz.co.za":
                hashed_password = hash_password(user_data.password)
                new_user = User(
                    email=user_data.email,
                    hashed_password=hashed_password
                )
                await db.users.insert_one(new_user.dict())
                user = new_user.dict()
            else:
                raise HTTPException(status_code=401, detail="Access restricted to authorized users only")
        
        # Verify password
        if not verify_password(user_data.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        # Update last login
        await db.users.update_one(
            {"email": user_data.email},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create access token
        access_token = create_access_token(data={"sub": user_data.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": user["email"],
                "last_login": user.get("last_login")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/settings")
async def update_settings(settings: UserSettings, current_user: User = Depends(get_current_user)):
    """Update user password"""
    try:
        # Verify current password
        if not verify_password(settings.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Hash new password
        new_hashed_password = hash_password(settings.new_password)
        
        # Update password
        await db.users.update_one(
            {"email": current_user.email},
            {"$set": {"hashed_password": new_hashed_password}}
        )
        
        return {"message": "Password updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/forgot-password")
async def forgot_password(reset_data: PasswordReset):
    """Send password reset instructions (simplified)"""
    try:
        user = await db.users.find_one({"email": reset_data.email})
        if not user:
            # Don't reveal if email exists or not
            return {"message": "If this email exists in our system, you will receive password reset instructions."}
        
        # In production, you would send an actual email
        # For now, return a temporary reset message
        return {
            "message": "Password reset instructions sent to your email.",
            "temp_instructions": "Please contact system administrator for password reset assistance."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "email": current_user.email,
        "last_login": current_user.last_login,
        "created_at": current_user.created_at
    }

# Enhanced AI Chat Routes
@api_router.get("/ai/models")
async def get_available_models():
    """Get list of available AI models"""
    return {
        "models": OPENAI_MODELS,
        "latest_model": OPENAI_MODELS["latest"],
        "recommended": "latest"
    }

@api_router.post("/ai/chat")
async def ai_chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """AI chat with optional chart context"""
    try:
        # Generate AI response
        response = await create_ai_chat_response(
            message=request.message,
            model=request.model,
            ticker=request.ticker if request.include_chart_data else None,
            session_id=request.session_id
        )
        
        # Save messages to database
        user_message = ChatMessage(
            session_id=request.session_id,
            role="user",
            content=request.message,
            chart_context={"ticker": request.ticker} if request.ticker else None
        )
        
        ai_message = ChatMessage(
            session_id=request.session_id,
            role="assistant",
            content=response
        )
        
        await db.chat_messages.insert_many([user_message.dict(), ai_message.dict()])
        
        return {
            "response": response,
            "session_id": request.session_id,
            "model_used": request.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/ai/sessions")
async def get_chat_sessions(current_user: User = Depends(get_current_user)):
    """Get user's chat sessions"""
    try:
        sessions = await db.chat_sessions.find({"user_id": current_user.id}).to_list(length=50)
        return [ChatSession(**session) for session in sessions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ai/sessions")
async def create_chat_session(session: ChatSession, current_user: User = Depends(get_current_user)):
    """Create new chat session"""
    try:
        session.user_id = current_user.id
        await db.chat_sessions.insert_one(session.dict())
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/ai/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, current_user: User = Depends(get_current_user)):
    """Get messages from a specific session"""
    try:
        messages = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(length=100)
        
        return [ChatMessage(**msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Company/Stock Search Routes
@api_router.get("/companies/search")
async def search_companies_api(query: str = Query(...), limit: int = Query(10)):
    """Search for companies by name or ticker"""
    try:
        results = await search_companies(query, limit)
        return {"companies": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/companies/{ticker}")
async def get_company_details(ticker: str):
    """Get detailed company information"""
    try:
        company_info = await get_company_info(ticker)
        stock_data = await get_stock_data(ticker)
        
        return {
            "company": company_info,
            "market_data": stock_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# TradingView Integration Routes
@api_router.post("/tradingview/connect")
async def connect_tradingview_account(account: TradingViewAccount, current_user: User = Depends(get_current_user)):
    """Connect TradingView account"""
    try:
        account.user_id = current_user.id
        
        # Check if account already exists
        existing = await db.tradingview_accounts.find_one({"user_id": current_user.id})
        if existing:
            await db.tradingview_accounts.replace_one(
                {"user_id": current_user.id},
                account.dict()
            )
        else:
            await db.tradingview_accounts.insert_one(account.dict())
        
        return {"message": "TradingView account connected successfully", "account": account}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tradingview/account")
async def get_tradingview_account(current_user: User = Depends(get_current_user)):
    """Get connected TradingView account"""
    try:
        account = await db.tradingview_accounts.find_one({"user_id": current_user.id})
        if not account:
            return {"connected": False}
        
        return {"connected": True, "account": TradingViewAccount(**account)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/tradingview/drawings")
async def save_chart_drawing(drawing: ChartDrawing, current_user: User = Depends(get_current_user)):
    """Save chart drawing/annotation"""
    try:
        drawing.user_id = current_user.id
        await db.chart_drawings.insert_one(drawing.dict())
        return {"message": "Chart drawing saved successfully", "drawing": drawing}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tradingview/drawings/{ticker}")
async def get_chart_drawings(ticker: str, current_user: User = Depends(get_current_user)):
    """Get saved chart drawings for a ticker"""
    try:
        drawings = await db.chart_drawings.find({
            "user_id": current_user.id,
            "ticker": ticker.upper()
        }).to_list(length=50)
        
        return [ChartDrawing(**drawing) for drawing in drawings]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Charts Data Routes
@api_router.get("/charts/indices")
async def get_indices_chart_data(timeframe: str = Query("1d", description="1d, 1w, 1m, 1y, 5y")):
    """Get chart data for major indices with different timeframes"""
    try:
        indices = ["SPY", "QQQ", "DIA", "IWM"]
        chart_data = {}
        
        # Map timeframe to yfinance period
        period_map = {
            "1d": "1d",
            "1w": "5d", 
            "1m": "1mo",
            "1y": "1y",
            "5y": "5y"
        }
        
        period = period_map.get(timeframe, "1mo")
        
        for index in indices:
            try:
                ticker = yf.Ticker(index)
                hist = ticker.history(period=period)
                
                if not hist.empty:
                    chart_data[index] = {
                        "dates": [d.strftime("%Y-%m-%d") for d in hist.index],
                        "prices": hist['Close'].tolist(),
                        "volumes": hist['Volume'].tolist(),
                        "highs": hist['High'].tolist(),
                        "lows": hist['Low'].tolist(),
                        "opens": hist['Open'].tolist()
                    }
            except Exception as e:
                logging.error(f"Error fetching chart data for {index}: {e}")
                continue
        
        return {"data": chart_data, "timeframe": timeframe}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/charts/{ticker}")
async def get_ticker_chart_data(ticker: str, timeframe: str = Query("1mo")):
    """Get chart data for any ticker"""
    try:
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period=timeframe)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}")
        
        return {
            "ticker": ticker.upper(),
            "timeframe": timeframe,
            "data": {
                "dates": [d.strftime("%Y-%m-%d %H:%M") for d in hist.index],
                "prices": hist['Close'].tolist(),
                "volumes": hist['Volume'].tolist(),
                "highs": hist['High'].tolist(),
                "lows": hist['Low'].tolist(),
                "opens": hist['Open'].tolist()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Watchlist Routes with Manual Management
@api_router.get("/watchlists/custom")
async def get_custom_watchlists_with_stocks(current_user: User = Depends(get_current_user)):
    """Get all custom watchlists with their stocks"""
    try:
        watchlists = await db.custom_watchlists.find().to_list(length=None)
        
        for watchlist in watchlists:
            # Get stocks in this watchlist
            stocks = await db.watchlists.find({"list_name": watchlist["name"]}).to_list(length=None)
            watchlist["stocks"] = [WatchlistItem(**stock) for stock in stocks]
        
        return [CustomWatchlist(**wl) for wl in watchlists]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/watchlists/custom/{list_name}/add-stock")
async def add_stock_to_watchlist(list_name: str, item: WatchlistItem, current_user: User = Depends(get_current_user)):
    """Add stock to watchlist manually"""
    try:
        # Verify the watchlist exists
        watchlist = await db.custom_watchlists.find_one({"name": list_name})
        if not watchlist:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        
        # Check if stock already exists in this list
        existing = await db.watchlists.find_one({"ticker": item.ticker, "list_name": list_name})
        if existing:
            raise HTTPException(status_code=400, detail="Stock already in watchlist")
        
        # Get company info to populate name if not provided
        if not item.name or item.name == item.ticker:
            company_info = await get_company_info(item.ticker)
            item.name = company_info.company_name
        
        item.list_name = list_name
        await db.watchlists.insert_one(item.dict())
        
        return {"message": f"Added {item.ticker} to {list_name}", "item": item}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/watchlists/custom/{list_name}/remove-stock/{ticker}")
async def remove_stock_from_watchlist(list_name: str, ticker: str, current_user: User = Depends(get_current_user)):
    """Remove stock from watchlist"""
    try:
        result = await db.watchlists.delete_one({"ticker": ticker.upper(), "list_name": list_name})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Stock not found in watchlist")
        
        return {"message": f"Removed {ticker} from {list_name}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Spreadsheet-Style Interface Routes
@api_router.get("/spreadsheet/etfs")
async def get_spreadsheet_etf_data(sector: Optional[str] = Query(None)):
    """Get ETF data in spreadsheet format with formulas"""
    try:
        query = {}
        if sector:
            query["sector"] = sector
        
        etfs = await db.etfs.find(query).to_list(length=None)
        
        # Format for spreadsheet view
        spreadsheet_data = []
        for etf in etfs:
            row = {
                "Ticker": etf.get("ticker", ""),
                "Name": etf.get("name", ""),
                "Sector": etf.get("sector", ""),
                "Theme": etf.get("theme", ""),
                "Price": etf.get("current_price", 0),
                "Swing_Days": f"=TODAY() - {etf.get('swing_start_date', datetime.utcnow().strftime('%Y-%m-%d'))}",
                "SATA": etf.get("sata_score", 0),
                "20SMA": etf.get("sma20_trend", "F"),
                "GMMA": etf.get("gmma_pattern", "Mixed"),
                "ATR_Percent": f"=({etf.get('atr_percent', 0):.2f})",
                "Change_1D": f"=({etf.get('change_1d', 0):.2f}%)",
                "Change_1W": f"=({etf.get('change_1w', 0):.2f}%)",
                "Change_1M": f"=({etf.get('change_1m', 0):.2f}%)",
                "RS_1M": "=IF({} > SPY_1M, \"Y\", \"N\")".format(etf.get('relative_strength_1m', 0)),
                "RS_3M": "=IF({} > SPY_3M, \"Y\", \"N\")".format(etf.get('relative_strength_3m', 0)),
                "RS_6M": "=IF({} > SPY_6M, \"Y\", \"N\")".format(etf.get('relative_strength_6m', 0)),
                "Color_Rule": f"=IF(AND(RS_1M=\"Y\", SATA>=7, GMMA=\"RWB\"), \"Green\", IF(RS_1M=\"N\", \"Red\", \"Yellow\"))"
            }
            spreadsheet_data.append(row)
        
        return {
            "data": spreadsheet_data,
            "formulas": {
                "swing_days": "=TODAY() - [Swing_Date_Cell]",
                "atr_percent": "=(14_Day_ATR / Current_Price) * 100",
                "relative_strength": "=(ETF_Return - SPY_Return) / ABS(SPY_Return)",
                "sata_score": "=Performance(40%) + RelStrength(30%) + Volume(20%) + Volatility(10%)",
                "color_logic": "Green: RS=Y AND SATA>=7 AND GMMA=RWB, Red: RS=N, Yellow: Mixed signals"
            },
            "total_records": len(spreadsheet_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Historical Data Pruning Route
@api_router.post("/admin/prune-historical-data")
async def prune_historical_data(days: int = 60, current_user: User = Depends(get_current_user)):
    """Prune historical data older than specified days"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Prune historical snapshots
        snapshots_result = await db.historical_snapshots.delete_many(
            {"date": {"$lt": cutoff_date}}
        )
        
        # Prune old chart analyses
        charts_result = await db.chart_analyses.delete_many(
            {"created_at": {"$lt": cutoff_date}}
        )
        
        # Prune old chat messages (keep last 1000 per session)
        sessions = await db.chat_sessions.find().to_list(length=None)
        chat_deletions = 0
        
        for session in sessions:
            messages = await db.chat_messages.find(
                {"session_id": session["id"]}
            ).sort("timestamp", -1).skip(1000).to_list(length=None)
            
            if messages:
                message_ids = [msg["id"] for msg in messages]
                result = await db.chat_messages.delete_many(
                    {"id": {"$in": message_ids}}
                )
                chat_deletions += result.deleted_count
        
        return {
            "message": f"Pruned historical data older than {days} days",
            "deleted": {
                "historical_snapshots": snapshots_result.deleted_count,
                "chart_analyses": charts_result.deleted_count,
                "chat_messages": chat_deletions
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Keep all existing routes from original server.py
@api_router.get("/")
async def root():
    return {"message": "ETF Intelligence System API - Enhanced Version"}

@api_router.get("/dashboard")
async def get_dashboard_data():
    """Get enhanced dashboard data with SA greetings, market info, and live indices"""
    try:
        sa_time = datetime.now(SA_TZ)
        ny_time = datetime.now(NY_TZ)
        
        # Fetch major indices data
        major_indices = {}
        try:
            indices_data = ['SPY', 'QQQ', 'DIA', 'IWM']
            for symbol in indices_data:
                data = await fetch_etf_data(symbol)
                if data:
                    major_indices[symbol] = {
                        'price': data['current_price'],
                        'change_1d': data['change_1d'],
                        'last_updated': datetime.utcnow().strftime("%H:%M")
                    }
        except Exception as e:
            logging.error(f"Error fetching indices data: {e}")
        
        # Fetch ZAR/USD exchange rate (mock for now)
        zar_usd_rate = 18.75
        
        # Fetch CNN Fear & Greed Index (mock for now)
        fear_greed_data = {
            'index': 73,
            'rating': 'Greed',
            'last_updated': datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            'components': {
                'stock_price_momentum': 85,
                'market_volatility': 45,
                'safe_haven_demand': 25,
                'put_call_ratio': 70
            }
        }
        
        dashboard_data = {
            "greeting": get_south_african_greeting(),
            "sa_time": {
                "time": sa_time.strftime("%H:%M:%S"),
                "timezone": "SAST",
                "date": sa_time.strftime("%A, %d %B %Y"),
                "flag": "🇿🇦"
            },
            "ny_time": {
                "time": ny_time.strftime("%H:%M:%S"), 
                "timezone": "EST" if ny_time.dst() else "EST",
                "date": ny_time.strftime("%A, %d %B %Y"),
                "flag": "🇺🇸"
            },
            "market_countdown": get_market_countdown(),
            "major_indices": major_indices,
            "zar_usd_rate": zar_usd_rate,
            "fear_greed_index": fear_greed_data,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include all other existing routes from the original server.py
# (ETFs, market score, watchlists, journal, etc.)

# Keep the existing routes exactly as they are
@api_router.get("/etfs", response_model=List[ETFData])
async def get_etfs(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    min_rs: Optional[float] = Query(None, description="Minimum relative strength"),
    limit: Optional[int] = Query(100, description="Limit results")
):
    """Get ETF data with optional filtering"""
    try:
        query = {}
        if sector:
            query["sector"] = sector
        if min_rs:
            query["relative_strength_1m"] = {"$gte": min_rs}
        
        etfs = await db.etfs.find(query).limit(limit).to_list(length=limit)
        return [ETFData(**etf) for etf in etfs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/etfs/update")
async def update_etfs():
    """Manually trigger ETF data update"""
    try:
        updated_etfs = await update_etf_data()
        return {"message": f"Updated {len(updated_etfs)} ETFs", "count": len(updated_etfs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/etfs/sectors")
async def get_sectors():
    """Get unique sectors"""
    try:
        sectors = await db.etfs.distinct("sector")
        return {"sectors": sectors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/etfs/swing-leaders")
async def get_swing_leaders():
    """Get top 5 ETFs based on SATA + RS combination"""
    try:
        etfs = await db.etfs.find().to_list(length=None)
        
        # Calculate combined swing score
        for etf in etfs:
            swing_score = etf.get('sata_score', 0) + (etf.get('relative_strength_1m', 0) * 10)
            etf['swing_score'] = swing_score
        
        # Sort by swing score
        top_etfs = sorted(etfs, key=lambda x: x.get('swing_score', 0), reverse=True)[:5]
        
        return [ETFData(**etf) for etf in top_etfs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Stock lookup for any ticker
@api_router.get("/stocks/{ticker}")
async def get_stock_info(ticker: str):
    """Get stock data for any ticker"""
    try:
        stock_data = await get_stock_data(ticker.upper())
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}")
        return stock_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Custom Watchlists Management (keeping existing routes)
@api_router.post("/watchlists/lists", response_model=CustomWatchlist)
async def create_custom_watchlist(watchlist: CustomWatchlist):
    """Create a new custom watchlist"""
    try:
        await db.custom_watchlists.insert_one(watchlist.dict())
        return watchlist
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/watchlists/lists", response_model=List[CustomWatchlist])
async def get_custom_watchlists():
    """Get all custom watchlists"""
    try:
        lists = await db.custom_watchlists.find().to_list(length=None)
        return [CustomWatchlist(**wl) for wl in lists]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Continue with all existing routes...