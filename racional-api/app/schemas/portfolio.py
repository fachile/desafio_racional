from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator
from app.models.models import Currency, OrderType, OrderStatus


# --- Allocation ---

class AllocationItem(BaseModel):
    ticker:     str     = Field(..., min_length=1, max_length=20)
    target_pct: Decimal = Field(..., gt=0, le=1, decimal_places=4)


class AllocationResponse(BaseModel):
    id:           int
    portfolio_id: int
    ticker:       str
    target_pct:   Decimal

    model_config = {"from_attributes": True}


# --- Portfolio ---

class PortfolioCreate(BaseModel):
    name:        str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)
    currency:    Currency = Currency.USD
    allocations: list[AllocationItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_allocations(self):
        if self.allocations:
            tickers = [a.ticker.upper() for a in self.allocations]
            if len(tickers) != len(set(tickers)):
                raise ValueError("Duplicate tickers in allocations")
            total = sum(a.target_pct for a in self.allocations)
            if total > Decimal("1.0"):
                raise ValueError(f"Allocations sum to {total}, must be <= 1.0")
        return self


class PortfolioUpdate(BaseModel):
    name:        str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)


class PortfolioResponse(BaseModel):
    id:           int
    user_id:      int
    name:         str
    description:  str | None
    cash_balance: Decimal
    currency:     Currency
    allocations:  list[AllocationResponse] = []
    created_at:   datetime
    updated_at:   datetime

    model_config = {"from_attributes": True}


# --- Fund / Withdraw ---

class FundRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=4)


class WithdrawRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=4)


# --- Total ---

class HoldingValuation(BaseModel):
    ticker:        str
    quantity:      Decimal
    avg_buy_price: Decimal
    current_price: Decimal
    market_value:  Decimal
    gain_loss:     Decimal
    target_pct:    Decimal | None = None


class PortfolioTotal(BaseModel):
    portfolio_id:   int
    currency:       Currency
    cash_balance:   Decimal
    holdings_value: Decimal
    total_value:    Decimal
    holdings:       list[HoldingValuation]


# --- Orders ---

class OrderResponse(BaseModel):
    id:                 int
    portfolio_id:       int
    ticker:             str
    type:               OrderType
    quantity:           Decimal
    price_at_execution: Decimal
    currency:           Currency
    date:               date
    status:             OrderStatus
    created_at:         datetime

    model_config = {"from_attributes": True}


# --- Movements ---

class MovementItem(BaseModel):
    id:          int
    event_type:  str
    description: str
    amount:      Decimal
    currency:    Currency
    date:        date
    created_at:  datetime
