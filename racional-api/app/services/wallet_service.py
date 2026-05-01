from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
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

    # Validate currency matches wallet
    if data.currency != wallet.currency:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Currency mismatch: wallet is {wallet.currency}, deposit is {data.currency}"
        )

    # Idempotency check: if key already exists, return the existing movement
    if data.idempotency_key:
        existing = db.query(CashMovement).filter(
            CashMovement.idempotency_key == data.idempotency_key
        ).first()
        if existing:
            return existing

    movement = CashMovement(
        wallet_id=wallet_id,
        type=MovementType.deposit,
        amount=data.amount,
        currency=data.currency,
        date=data.date,
        note=data.note,
        idempotency_key=data.idempotency_key,
    )
    wallet.cash_balance += data.amount

    db.add(movement)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Race condition: another request with same key was committed first
        existing = db.query(CashMovement).filter(
            CashMovement.idempotency_key == data.idempotency_key
        ).first()
        if existing:
            return existing
        raise

    db.refresh(movement)
    return movement


def withdrawal(db: Session, wallet_id: int, data: WithdrawalRequest) -> CashMovement:
    wallet = _get_wallet(db, wallet_id)

    if data.currency != wallet.currency:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Currency mismatch: wallet is {wallet.currency}, withdrawal is {data.currency}"
        )

    if wallet.cash_balance < data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient funds. Available: {wallet.cash_balance} {wallet.currency}"
        )

    movement = CashMovement(
        wallet_id=wallet_id,
        type=MovementType.withdrawal,
        amount=data.amount,
        currency=data.currency,
        date=data.date,
        note=data.note,
    )
    wallet.cash_balance -= data.amount

    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement
