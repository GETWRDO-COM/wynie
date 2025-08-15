from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, date

class BaseRow(BaseModel):
    raw: Dict[str, Any] = Field(default_factory=dict)
    raw_hash: Optional[str] = None

    class Config:
        extra = 'allow'

class OrdersRow(BaseRow):
    external_order_id: str
    submitted_at: Optional[datetime] = None
    side: Optional[str] = None
    type: Optional[str] = None
    time_in_force: Optional[str] = None
    symbol: Optional[str] = None
    instrument_id: Optional[str] = None
    asset_class: Optional[str] = None
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    qty: Optional[float] = None
    status: Optional[str] = None
    currency: Optional[str] = None
    placed_by: Optional[str] = None

class ExecutionsRow(BaseRow):
    external_execution_id: str
    filled_at: datetime
    side: str
    symbol: Optional[str] = None
    instrument_id: Optional[str] = None
    asset_class: Optional[str] = None
    qty: float
    price: float
    gross_amount: Optional[float] = None
    commission: Optional[float] = 0.0
    fees: Optional[float] = 0.0
    net_amount: Optional[float] = None
    currency: Optional[str] = None
    venue: Optional[str] = None

class PositionsEODRow(BaseRow):
    as_of: date
    symbol: Optional[str] = None
    instrument_id: str
    asset_class: Optional[str] = None
    currency: Optional[str] = None
    qty: Optional[float] = 0.0
    avg_price: Optional[float] = None
    market_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    cost_basis: Optional[float] = None
    trade_date_open: Optional[date] = None
    last_update: Optional[datetime] = None

class BalancesEODRow(BaseRow):
    as_of: date
    currency: Optional[str] = None
    cash_available: Optional[float] = None
    cash_balance: Optional[float] = None
    net_equity: Optional[float] = None
    margin_usable: Optional[float] = None
    margin_used: Optional[float] = None
    buying_power: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl_day: Optional[float] = 0.0
    accrued_fees_interest: Optional[float] = None

class CashEventRow(BaseRow):
    posted_at: datetime
    value_date: date
    type: str
    description: Optional[str] = None
    amount: float
    currency: Optional[str] = None
    balance_after: Optional[float] = None