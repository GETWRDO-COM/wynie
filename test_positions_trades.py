#!/usr/bin/env python3
"""
Targeted Positions & Trades API testing as per review request
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f'{BACKEND_URL}/api'

print('🧪 Running targeted Positions & Trades API tests as per review request...')
print(f'📡 Testing against: {API_BASE}')
print('=' * 80)

session = requests.Session()

# 1. Login with beetge@mwebbiz.co.za and any password (auto-creates user)
print('1. Testing login with beetge@mwebbiz.co.za...')
login_data = {'email': 'beetge@mwebbiz.co.za', 'password': 'test123'}
login_response = session.post(f'{API_BASE}/auth/login', json=login_data)
if login_response.status_code == 200:
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print('✅ Login successful, got bearer token')
else:
    print(f'❌ Login failed: {login_response.status_code}')
    exit(1)

# 2. GET /api/positions (auth required) returns [] or existing items with computed fields
print('\n2. Testing GET /api/positions...')
positions_response = session.get(f'{API_BASE}/positions', headers=headers)
if positions_response.status_code == 200:
    positions = positions_response.json()
    print(f'✅ GET positions successful, returned {len(positions)} positions')
    if positions:
        pos = positions[0]
        computed_fields = ['initial_stop', 'trailing_stop', 'r_multiple', 'breached_initial_stop', 'breached_trailing_stop', 'status']
        missing = [f for f in computed_fields if f not in pos]
        if missing:
            print(f'❌ Missing computed fields: {missing}')
        else:
            print('✅ All computed fields present')
else:
    print(f'❌ GET positions failed: {positions_response.status_code}')

# 3. POST /api/positions (admin required) creates position for AAPL, LONG, entry_price=100, shares=10
print('\n3. Testing POST /api/positions for AAPL...')
position_data = {
    'symbol': 'AAPL',
    'side': 'LONG', 
    'entry_price': 100.0,
    'shares': 10,
    'strategy_tag': 'Review Test Position'
}
create_response = session.post(f'{API_BASE}/positions', json=position_data, headers=headers)
if create_response.status_code == 200:
    result = create_response.json()
    position = result['position']
    entry_trade = result['entry_trade']
    position_id = position['id']
    
    print(f'✅ Position created: {position["symbol"]} {position["side"]} @ ${position["entry_price"]}')
    print(f'   Initial stop: ${position["initial_stop"]} (should be <= entry for LONG)')
    print(f'   Trailing stop: ${position["trailing_stop"]}')
    print(f'   Entry trade created: {entry_trade["side"]} {entry_trade["shares"]} shares')
    
    # Verify initial stop <= entry for LONG
    if position['initial_stop'] <= position['entry_price']:
        print('✅ Initial stop correctly calculated for LONG position')
    else:
        print(f'❌ Initial stop {position["initial_stop"]} > entry price {position["entry_price"]}')
else:
    print(f'❌ POST position failed: {create_response.status_code}: {create_response.text}')
    exit(1)

# 4. PATCH /api/positions/{id} (admin required) set status=CLOSED, exit_price=110
print('\n4. Testing PATCH /api/positions/{id} to close position...')
patch_data = {'status': 'CLOSED', 'exit_price': 110.0}
patch_response = session.patch(f'{API_BASE}/positions/{position_id}', json=patch_data, headers=headers)
if patch_response.status_code == 200:
    updated_pos = patch_response.json()
    pnl = updated_pos.get('pnl', 0)
    r_exit = updated_pos.get('r_exit')
    
    print(f'✅ Position closed at ${updated_pos["exit_price"]}')
    print(f'   PnL: ${pnl} (should be > 0)')
    print(f'   R-multiple at exit: {r_exit}')
    
    if pnl > 0:
        print('✅ PnL is positive as expected')
    else:
        print(f'❌ PnL should be positive, got {pnl}')
        
    if r_exit is not None:
        print('✅ R-exit calculated')
    else:
        print('❌ R-exit not calculated')
else:
    print(f'❌ PATCH position failed: {patch_response.status_code}: {patch_response.text}')

# 5. GET /api/trades returns at least the 2 trades (entry+exit) with correct order
print('\n5. Testing GET /api/trades...')
trades_response = session.get(f'{API_BASE}/trades')
if trades_response.status_code == 200:
    trades = trades_response.json()
    print(f'✅ GET trades successful, returned {len(trades)} trades')
    
    if len(trades) >= 2:
        print('✅ At least 2 trades present (entry + exit)')
        
        # Check order (most recent first)
        if len(trades) >= 2:
            first_ts = datetime.fromisoformat(trades[0]['ts'].replace('Z', '+00:00'))
            second_ts = datetime.fromisoformat(trades[1]['ts'].replace('Z', '+00:00'))
            if first_ts >= second_ts:
                print('✅ Trades in correct order (most recent first)')
            else:
                print('❌ Trades not in correct order')
        
        # Find our position trades
        position_trades = [t for t in trades if t.get('position_id') == position_id]
        if len(position_trades) >= 2:
            print(f'✅ Found {len(position_trades)} trades for our position')
            buy_trade = next((t for t in position_trades if t['side'] == 'BUY'), None)
            sell_trade = next((t for t in position_trades if t['side'] == 'SELL'), None)
            if buy_trade and sell_trade:
                print('✅ Both entry (BUY) and exit (SELL) trades created')
            else:
                print('❌ Missing BUY or SELL trade')
        else:
            print(f'❌ Expected 2 trades for position, got {len(position_trades)}')
    else:
        print(f'❌ Expected at least 2 trades, got {len(trades)}')
else:
    print(f'❌ GET trades failed: {trades_response.status_code}')

# 6. POST /api/trades (admin required) creates a standalone trade
print('\n6. Testing POST /api/trades for standalone trade...')
trade_data = {
    'symbol': 'MSFT',
    'side': 'BUY',
    'price': 300.0,
    'shares': 5,
    'notes': 'Standalone test trade'
}
trade_response = session.post(f'{API_BASE}/trades', json=trade_data, headers=headers)
if trade_response.status_code == 200:
    trade = trade_response.json()
    print(f'✅ Standalone trade created: {trade["side"]} {trade["shares"]} {trade["symbol"]} @ ${trade["price"]}')
    print(f'   Trade ID: {trade["id"]}')
else:
    print(f'❌ POST trade failed: {trade_response.status_code}: {trade_response.text}')

print('\n' + '=' * 80)
print('🏆 Positions & Trades API testing completed!')