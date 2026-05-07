from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class TradeCreate(BaseModel):
    asset: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., min_length=1, max_length=20)
    market: str = Field(..., min_length=1, max_length=50)
    direction: str = Field(..., pattern="^(LONG|SHORT)$")
    price_open: float = Field(..., gt=0)
    quantity: float = Field(..., gt=0)
    cost: float = Field(..., gt=0)
    signal_source: str | None = None
    notes: str | None = None


class TradeClose(BaseModel):
    price_close: float = Field(..., gt=0)
    date_close: str | None = None


class TradeResponse(BaseModel):
    id: str
    date_open: str
    asset: str
    symbol: str
    market: str
    direction: str
    price_open: float
    quantity: float
    cost: float
    status: str
    date_close: str | None
    price_close: float | None
    pnl: float | None
    pnl_pct: float | None
    signal_source: str | None
    notes: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PortfolioSummary(BaseModel):
    initial_capital: float
    cash: float
    invested: float
    portfolio_value: float
    total_pnl: float
    total_pnl_pct: float
    open_positions: int
    closed_trades: int
    win_rate: float


class PriceResponse(BaseModel):
    symbol: str
    price: float
    currency: str = "USD"
    timestamp: str
    source: str