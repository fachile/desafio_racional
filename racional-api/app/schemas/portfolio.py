from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator
from app.models.models import OrderType, OrderStatus


class AllocationItem(BaseModel):
    ticker:     str     = Field(..., min_length=1, max_length=20)
    target_pct: Decimal = Field(..., gt=0, le=1, decimal_places=4)


class AllocationResponse(BaseModel):
    id:           int
    portfolio_id: int
    ticker:       str
    target_pct:   Decimal

    model_config = {"from_attributes": True}


class PortfolioCreate(BaseModel):
    name:        str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)
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
    cash_balance: int
    allocations:  list[AllocationResponse] = []
    created_at:   datetime
    updated_at:   datetime

    model_config = {"from_attributes": True}


class FundRequest(BaseModel):
    amount: int = Field(..., gt=0)


class WithdrawRequest(BaseModel):
    amount: int = Field(..., gt=0)


class HoldingValuation(BaseModel):
    ticker:        str
    quantity:      Decimal
    avg_buy_price: int
    current_price: int
    market_value:  int
    gain_loss:     int
    target_pct:    Decimal | None = None


class PortfolioTotal(BaseModel):
    portfolio_id:   int
    cash_balance:   int
    holdings_value: int
    total_value:    int
    holdings:       list[HoldingValuation]


class OrderResponse(BaseModel):
    id:                 int
    portfolio_id:       int
    ticker:             str
    type:               OrderType
    quantity:           Decimal
    price_at_execution: int
    status:             OrderStatus
    created_at:         datetime

    model_config = {"from_attributes": True}


class MovementItem(BaseModel):
    id:          int
    event_type:  str
    description: str
    amount:      int
    created_at:  datetime
