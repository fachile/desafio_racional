from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    FundRequest, WithdrawRequest, AllocationItem,
    PortfolioTotal, MovementItem
)
from app.services import portfolio_service

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


@router.post("", response_model=PortfolioResponse, status_code=201)
def create_portfolio(user_id: int, data: PortfolioCreate, db: Session = Depends(get_db)):
    return portfolio_service.create_portfolio(db, user_id, data)


@router.get("/by-user/{user_id}", response_model=list[PortfolioResponse])
def get_user_portfolios(user_id: int, db: Session = Depends(get_db)):
    return portfolio_service.get_user_portfolios(db, user_id)


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(portfolio_id: int, data: PortfolioUpdate, db: Session = Depends(get_db)):
    return portfolio_service.update_portfolio(db, portfolio_id, data)


@router.put("/{portfolio_id}/allocations", response_model=PortfolioResponse)
def update_allocations(portfolio_id: int, allocations: list[AllocationItem], db: Session = Depends(get_db)):
    """Replace portfolio allocations and rebalance immediately."""
    return portfolio_service.update_allocations(db, portfolio_id, allocations)


@router.post("/{portfolio_id}/fund", response_model=PortfolioResponse)
def fund_portfolio(portfolio_id: int, data: FundRequest, db: Session = Depends(get_db)):
    """Transfer cash from wallet into portfolio and auto-invest per allocations."""
    return portfolio_service.fund_portfolio(db, portfolio_id, data)


@router.post("/{portfolio_id}/withdraw", response_model=PortfolioResponse)
def withdraw_from_portfolio(portfolio_id: int, data: WithdrawRequest, db: Session = Depends(get_db)):
    """Sell holdings proportionally and transfer cash back to wallet."""
    return portfolio_service.withdraw_from_portfolio(db, portfolio_id, data)


@router.get("/{portfolio_id}/total", response_model=PortfolioTotal)
def get_total(portfolio_id: int, db: Session = Depends(get_db)):
    return portfolio_service.get_portfolio_total(db, portfolio_id)


@router.get("/{portfolio_id}/movements", response_model=list[MovementItem])
def get_movements(
    portfolio_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    return portfolio_service.get_movements(db, portfolio_id, limit)
