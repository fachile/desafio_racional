from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import Wallet, CashMovement, MovementType
from app.schemas.wallet import DepositRequest, WithdrawalRequest


def _get_wallet(db: Session, wallet_id: int) -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return wallet


def deposit(db: Session, wallet_id: int, data: DepositRequest) -> CashMovement:
    wallet = _get_wallet(db, wallet_id)

    movement = CashMovement(
        wallet_id=wallet_id,
        type=MovementType.deposit,
        amount=data.amount,
        note=data.note,
    )
    wallet.cash_balance += data.amount
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


def withdrawal(db: Session, wallet_id: int, data: WithdrawalRequest) -> CashMovement:
    wallet = _get_wallet(db, wallet_id)

    if wallet.cash_balance < data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient funds. Available: ${wallet.cash_balance:,} CLP"
        )

    movement = CashMovement(
        wallet_id=wallet_id,
        type=MovementType.withdrawal,
        amount=data.amount,
        note=data.note,
    )
    wallet.cash_balance -= data.amount
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement
