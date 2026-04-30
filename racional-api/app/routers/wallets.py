from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.wallet import DepositRequest, WithdrawalRequest, CashMovementResponse, WalletResponse
from app.services import wallet_service

router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.get("/by-user/{user_id}", response_model=WalletResponse)
def get_wallet_by_user(user_id: UUID, db: Session = Depends(get_db)):
    from app.models.models import Wallet
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet

@router.post("/{wallet_id}/deposit", response_model=CashMovementResponse, status_code=201)
def deposit(wallet_id: UUID, data: DepositRequest, db: Session = Depends(get_db)):
    return wallet_service.deposit(db, wallet_id, data)


@router.post("/{wallet_id}/withdrawal", response_model=CashMovementResponse, status_code=201)
def withdrawal(wallet_id: UUID, data: WithdrawalRequest, db: Session = Depends(get_db)):
    return wallet_service.withdrawal(db, wallet_id, data)
