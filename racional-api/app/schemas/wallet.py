from datetime import datetime
from pydantic import BaseModel, Field
from app.models.models import MovementType


class WalletResponse(BaseModel):
    id:           int
    user_id:      int
    cash_balance: int
    created_at:   datetime

    model_config = {"from_attributes": True}


class DepositRequest(BaseModel):
    amount: int = Field(..., gt=0)
    note:   str | None = Field(None, max_length=500)


class WithdrawalRequest(BaseModel):
    amount: int = Field(..., gt=0)
    note:   str | None = Field(None, max_length=500)


class CashMovementResponse(BaseModel):
    id:         int
    wallet_id:  int
    type:       MovementType
    amount:     int
    note:       str | None
    created_at: datetime

    model_config = {"from_attributes": True}
