from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    FundRequest, OrderCreate, OrderResponse,
    PortfolioTotal, MovementItem
)
from app.services import portfolio_service

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


@router.post("", response_model=PortfolioResponse, status_code=201)
def create_portfolio(user_id: UUID, data: PortfolioCreate, db: Session = Depends(get_db)):
    """Create a new portfolio for a user. Pass user_id as query param."""
    return portfolio_service.create_portfolio(db, user_id, data)


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(portfolio_id: UUID, data: PortfolioUpdate, db: Session = Depends(get_db)):
    return portfolio_service.update_portfolio(db, portfolio_id, data)


@router.post("/{portfolio_id}/fund", response_model=PortfolioResponse)
def fund_portfolio(portfolio_id: UUID, data: FundRequest, db: Session = Depends(get_db)):
    """Transfer cash from the user's wallet into this portfolio."""
    return portfolio_service.fund_portfolio(db, portfolio_id, data)


@router.get("/{portfolio_id}/total", response_model=PortfolioTotal)
def get_total(portfolio_id: UUID, db: Session = Depends(get_db)):
    """Return portfolio total value: cash + holdings at mock prices."""
    return portfolio_service.get_portfolio_total(db, portfolio_id)


@router.get("/{portfolio_id}/movements", response_model=list[MovementItem])
def get_movements(
    portfolio_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Return the latest N movements (orders + fund transfers) for a portfolio."""
    return portfolio_service.get_movements(db, portfolio_id, limit)


@router.post("/{portfolio_id}/orders", response_model=OrderResponse, status_code=201)
def create_order(portfolio_id: UUID, data: OrderCreate, db: Session = Depends(get_db)):
    """Place a buy or sell order. Executed immediately at mock price."""
    return portfolio_service.create_order(db, portfolio_id, data)
