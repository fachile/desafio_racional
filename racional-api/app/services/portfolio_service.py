from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import Portfolio, Wallet, Holding, Order, OrderType, PortfolioTransfer
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, FundRequest,
    OrderCreate, PortfolioTotal, HoldingValuation, MovementItem
)
from app.core.mock_prices import get_price


def _get_portfolio(db: Session, portfolio_id: int) -> Portfolio:
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return portfolio


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_portfolio(db: Session, user_id: int, data: PortfolioCreate) -> Portfolio:
    portfolio = Portfolio(
        user_id=user_id,
        name=data.name,
        description=data.description,
        currency=data.currency,
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


def update_portfolio(db: Session, portfolio_id: int, data: PortfolioUpdate) -> Portfolio:
    portfolio = _get_portfolio(db, portfolio_id)

    if data.name is not None:
        portfolio.name = data.name
    if data.description is not None:
        portfolio.description = data.description

    db.commit()
    db.refresh(portfolio)
    return portfolio


# ---------------------------------------------------------------------------
# Fund transfer: wallet → portfolio
# ---------------------------------------------------------------------------

def fund_portfolio(db: Session, portfolio_id: int, data: FundRequest) -> Portfolio:
    portfolio = _get_portfolio(db, portfolio_id)
    wallet = db.query(Wallet).filter(Wallet.user_id == portfolio.user_id).first()

    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found for this user")

    if wallet.currency != portfolio.currency:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Currency mismatch: wallet is {wallet.currency}, portfolio is {portfolio.currency}"
        )

    if wallet.cash_balance < data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient wallet funds. Available: {wallet.cash_balance} {wallet.currency}"
        )

    wallet.cash_balance    -= data.amount
    portfolio.cash_balance += data.amount

    transfer = PortfolioTransfer(
        wallet_id=wallet.id,
        portfolio_id=portfolio_id,
        amount=data.amount,
        currency=portfolio.currency,
    )
    db.add(transfer)
    db.commit()
    db.refresh(portfolio)
    return portfolio


# ---------------------------------------------------------------------------
# Orders: buy / sell
# ---------------------------------------------------------------------------

def create_order(db: Session, portfolio_id: int, data: OrderCreate) -> Order:
    portfolio = _get_portfolio(db, portfolio_id)

    try:
        price = get_price(data.ticker)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    total_cost = price * data.quantity

    if data.type == OrderType.buy:
        _execute_buy(db, portfolio, data, price, total_cost)
    else:
        _execute_sell(db, portfolio, data, price, total_cost)

    order = Order(
        portfolio_id=portfolio_id,
        ticker=data.ticker.upper(),
        type=data.type,
        quantity=data.quantity,
        price_at_execution=price,
        currency=portfolio.currency,
        date=data.date,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def _execute_buy(db: Session, portfolio: Portfolio, data: OrderCreate, price: Decimal, total_cost: Decimal):
    if portfolio.cash_balance < total_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient portfolio cash. Need {total_cost}, have {portfolio.cash_balance}"
        )

    portfolio.cash_balance -= total_cost

    # Update or create holding with weighted average price
    holding = db.query(Holding).filter(
        Holding.portfolio_id == portfolio.id,
        Holding.ticker == data.ticker.upper()
    ).first()

    if holding:
        total_qty   = holding.quantity + data.quantity
        holding.avg_buy_price = (
            (holding.quantity * holding.avg_buy_price + data.quantity * price) / total_qty
        )
        holding.quantity = total_qty
    else:
        holding = Holding(
            portfolio_id=portfolio.id,
            ticker=data.ticker.upper(),
            quantity=data.quantity,
            avg_buy_price=price,
        )
        db.add(holding)


def _execute_sell(db: Session, portfolio: Portfolio, data: OrderCreate, price: Decimal, total_proceeds: Decimal):
    holding = db.query(Holding).filter(
        Holding.portfolio_id == portfolio.id,
        Holding.ticker == data.ticker.upper()
    ).first()

    if not holding or holding.quantity < data.quantity:
        available = holding.quantity if holding else Decimal("0")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient shares. Have {available} {data.ticker.upper()}, trying to sell {data.quantity}"
        )

    holding.quantity       -= data.quantity
    portfolio.cash_balance += total_proceeds
    # avg_buy_price stays unchanged on sell (standard behavior)


# ---------------------------------------------------------------------------
# Portfolio total valuation
# ---------------------------------------------------------------------------

def get_portfolio_total(db: Session, portfolio_id: int) -> PortfolioTotal:
    portfolio = _get_portfolio(db, portfolio_id)
    holdings  = db.query(Holding).filter(
        Holding.portfolio_id == portfolio_id,
        Holding.quantity > 0
    ).all()

    valuations: list[HoldingValuation] = []
    holdings_value = Decimal("0")

    for h in holdings:
        try:
            current_price = get_price(h.ticker)
        except ValueError:
            current_price = h.avg_buy_price  # fallback to cost if ticker disappeared from mock

        market_value = h.quantity * current_price
        gain_loss    = (current_price - h.avg_buy_price) * h.quantity
        holdings_value += market_value

        valuations.append(HoldingValuation(
            ticker=h.ticker,
            quantity=h.quantity,
            avg_buy_price=h.avg_buy_price,
            current_price=current_price,
            market_value=market_value,
            gain_loss=gain_loss,
        ))

    return PortfolioTotal(
        portfolio_id=portfolio_id,
        currency=portfolio.currency,
        cash_balance=portfolio.cash_balance,
        holdings_value=holdings_value,
        total_value=portfolio.cash_balance + holdings_value,
        holdings=valuations,
    )


# ---------------------------------------------------------------------------
# Movements feed (unified: orders + transfers)
# ---------------------------------------------------------------------------

def get_movements(db: Session, portfolio_id: int, limit: int = 50) -> list[MovementItem]:
    _get_portfolio(db, portfolio_id)

    orders = db.query(Order).filter(Order.portfolio_id == portfolio_id).all()
    transfers = db.query(PortfolioTransfer).filter(PortfolioTransfer.portfolio_id == portfolio_id).all()

    items: list[MovementItem] = []

    for o in orders:
        items.append(MovementItem(
            id=o.id,
            event_type=o.type.value,
            description=f"{o.type.value.capitalize()} {o.quantity} {o.ticker} @ {o.price_at_execution}",
            amount=o.quantity * o.price_at_execution,
            currency=o.currency,
            date=o.date,
            created_at=o.created_at,
        ))

    for t in transfers:
        items.append(MovementItem(
            id=t.id,
            event_type="fund_in",
            description=f"Transfer from wallet: {t.amount} {t.currency}",
            amount=t.amount,
            currency=t.currency,
            date=t.created_at.date(),
            created_at=t.created_at,
        ))

    # Sort by created_at descending, return latest N
    items.sort(key=lambda x: x.created_at, reverse=True)
    return items[:limit]
