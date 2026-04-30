from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.models import Currency, OrderType, OrderStatus


# --- Portfolio ---

class PortfolioCreate(BaseModel):
    name:        str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)
    currency:    Currency = Currency.USD


class PortfolioUpdate(BaseModel):
    name:        str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)


class PortfolioResponse(BaseModel):
    id:           UUID
    user_id:      UUID
    name:         str
    description:  str | None
    cash_balance: Decimal
    currency:     Currency
    created_at:   datetime
    updated_at:   datetime

    model_config = {"from_attributes": True}


# --- Fund Transfer ---

class FundRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=4)


# --- Total ---

class HoldingValuation(BaseModel):
    ticker:        str
    quantity:      Decimal
    avg_buy_price: Decimal
    current_price: Decimal
    market_value:  Decimal
    gain_loss:     Decimal


class PortfolioTotal(BaseModel):
    portfolio_id:   UUID
    currency:       Currency
    cash_balance:   Decimal
    holdings_value: Decimal
    total_value:    Decimal
    holdings:       list[HoldingValuation]


# --- Orders ---

class OrderCreate(BaseModel):
    ticker:   str = Field(..., min_length=1, max_length=20)
    type:     OrderType
    quantity: Decimal = Field(..., gt=0, decimal_places=6)
    date:     date


class OrderResponse(BaseModel):
    id:                 UUID
    portfolio_id:       UUID
    ticker:             str
    type:               OrderType
    quantity:           Decimal
    price_at_execution: Decimal
    currency:           Currency
    date:               date
    status:             OrderStatus
    created_at:         datetime

    model_config = {"from_attributes": True}


# --- Movements (unified feed) ---

class MovementItem(BaseModel):
    id:          UUID
    event_type:  str          # "deposit" | "withdrawal" | "buy" | "sell" | "fund_in" | "fund_out"
    description: str
    amount:      Decimal
    currency:    Currency
    date:        date
    created_at:  datetime
