from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.models import Currency, MovementType


class WalletResponse(BaseModel):
    id:           int
    user_id:      int
    cash_balance: Decimal
    currency:     Currency
    created_at:   datetime

    model_config = {"from_attributes": True}


class DepositRequest(BaseModel):
    amount:          Decimal = Field(..., gt=0, decimal_places=4)
    currency:        Currency
    date:            date
    note:            str | None = Field(None, max_length=500)
    idempotency_key: str | None = Field(None, max_length=255)


class WithdrawalRequest(BaseModel):
    amount:   Decimal = Field(..., gt=0, decimal_places=4)
    currency: Currency
    date:     date
    note:     str | None = Field(None, max_length=500)


class CashMovementResponse(BaseModel):
    id:              int
    wallet_id:       int
    type:            MovementType
    amount:          Decimal
    currency:        Currency
    date:            date
    note:            str | None
    idempotency_key: str | None
    created_at:      datetime

    model_config = {"from_attributes": True}
