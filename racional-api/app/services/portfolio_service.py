from decimal import Decimal, ROUND_DOWN
from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import (
    Portfolio, Wallet, Holding, Order, OrderType, OrderStatus,
    PortfolioTransfer, PortfolioAllocation
)
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, FundRequest, WithdrawRequest,
    AllocationItem, PortfolioTotal, HoldingValuation, MovementItem
)
from app.core.mock_prices import get_price


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_portfolio(db: Session, portfolio_id: int) -> Portfolio:
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return portfolio


def _get_holding(db: Session, portfolio_id: int, ticker: str) -> Holding | None:
    return db.query(Holding).filter(
        Holding.portfolio_id == portfolio_id,
        Holding.ticker == ticker
    ).first()


def _portfolio_total_value(db: Session, portfolio: Portfolio) -> Decimal:
    """Cash + market value of all holdings."""
    holdings = db.query(Holding).filter(
        Holding.portfolio_id == portfolio.id,
        Holding.quantity > 0
    ).all()
    total = portfolio.cash_balance
    for h in holdings:
        try:
            total += h.quantity * get_price(h.ticker)
        except ValueError:
            total += h.quantity * h.avg_buy_price
    return total


def _execute_buy(db: Session, portfolio: Portfolio, ticker: str, amount: Decimal, order_date: date) -> Order | None:
    """Buy as many shares as possible with `amount` of cash. Returns Order or None if amount too small."""
    price = get_price(ticker)
    quantity = (amount / price).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
    if quantity <= 0:
        return None

    cost = quantity * price
    portfolio.cash_balance -= cost

    holding = _get_holding(db, portfolio.id, ticker)
    if holding:
        total_qty = holding.quantity + quantity
        holding.avg_buy_price = (
            (holding.quantity * holding.avg_buy_price + quantity * price) / total_qty
        )
        holding.quantity = total_qty
    else:
        holding = Holding(
            portfolio_id=portfolio.id,
            ticker=ticker,
            quantity=quantity,
            avg_buy_price=price,
        )
        db.add(holding)

    order = Order(
        portfolio_id=portfolio.id,
        ticker=ticker,
        type=OrderType.buy,
        quantity=quantity,
        price_at_execution=price,
        currency=portfolio.currency,
        date=order_date,
        status=OrderStatus.executed,
    )
    db.add(order)
    return order


def _execute_sell(db: Session, portfolio: Portfolio, ticker: str, amount: Decimal, order_date: date) -> Order | None:
    """Sell shares worth `amount`. Returns Order or None if no holding."""
    price = get_price(ticker)
    holding = _get_holding(db, portfolio.id, ticker)
    if not holding or holding.quantity <= 0:
        return None

    quantity = (amount / price).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
    quantity = min(quantity, holding.quantity)  # can't sell more than we have
    if quantity <= 0:
        return None

    proceeds = quantity * price
    holding.quantity -= quantity
    portfolio.cash_balance += proceeds

    order = Order(
        portfolio_id=portfolio.id,
        ticker=ticker,
        type=OrderType.sell,
        quantity=quantity,
        price_at_execution=price,
        currency=portfolio.currency,
        date=order_date,
        status=OrderStatus.executed,
    )
    db.add(order)
    return order


def _sell_all(db: Session, portfolio: Portfolio, ticker: str, order_date: date) -> Order | None:
    """Sell entire position of a ticker."""
    holding = _get_holding(db, portfolio.id, ticker)
    if not holding or holding.quantity <= 0:
        return None

    price = get_price(ticker)
    proceeds = holding.quantity * price
    portfolio.cash_balance += proceeds

    order = Order(
        portfolio_id=portfolio.id,
        ticker=ticker,
        type=OrderType.sell,
        quantity=holding.quantity,
        price_at_execution=price,
        currency=portfolio.currency,
        date=order_date,
        status=OrderStatus.executed,
    )
    holding.quantity = Decimal("0")
    db.add(order)
    return order


def _invest_cash(db: Session, portfolio: Portfolio, order_date: date) -> list[Order]:
    """
    Invest available cash according to target allocations.
    Only invests cash that exceeds the non-allocated portion.
    """
    allocations = portfolio.allocations
    if not allocations:
        return []

    total_allocated_pct = sum(a.target_pct for a in allocations)
    # Cash that should remain uninvested (the non-allocated portion)
    total_value = _portfolio_total_value(db, portfolio)
    target_cash = total_value * (Decimal("1") - total_allocated_pct)
    investable_cash = portfolio.cash_balance - target_cash

    if investable_cash <= 0:
        return []

    orders = []
    for alloc in allocations:
        amount = (investable_cash * alloc.target_pct / total_allocated_pct).quantize(
            Decimal("0.0001"), rounding=ROUND_DOWN
        )
        if amount > 0:
            order = _execute_buy(db, portfolio, alloc.ticker.upper(), amount, order_date)
            if order:
                orders.append(order)
    return orders


def _rebalance(db: Session, portfolio: Portfolio, new_allocations: list[AllocationItem], order_date: date) -> list[Order]:
    """
    Rebalance portfolio to match new target allocations.
    Sells tickers removed from allocation, then buys/sells to hit targets.
    """
    orders = []
    new_tickers = {a.ticker.upper() for a in new_allocations}

    # Sell any tickers no longer in the allocation
    for holding in portfolio.holdings:
        if holding.quantity > 0 and holding.ticker not in new_tickers:
            order = _sell_all(db, portfolio, holding.ticker, order_date)
            if order:
                orders.append(order)

    db.flush()  # reflect cash changes before computing total

    total_value = _portfolio_total_value(db, portfolio)

    for alloc in new_allocations:
        ticker = alloc.ticker.upper()
        price = get_price(ticker)
        target_value  = total_value * alloc.target_pct
        holding       = _get_holding(db, portfolio.id, ticker)
        current_value = (holding.quantity * price) if holding and holding.quantity > 0 else Decimal("0")
        diff          = target_value - current_value

        if diff > Decimal("0.01"):  # need to buy
            order = _execute_buy(db, portfolio, ticker, diff, order_date)
            if order:
                orders.append(order)
        elif diff < Decimal("-0.01"):  # need to sell
            order = _execute_sell(db, portfolio, ticker, abs(diff), order_date)
            if order:
                orders.append(order)

    return orders


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
    db.flush()

    for alloc in data.allocations:
        db.add(PortfolioAllocation(
            portfolio_id=portfolio.id,
            ticker=alloc.ticker.upper(),
            target_pct=alloc.target_pct,
        ))

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


def get_user_portfolios(db: Session, user_id: int) -> list[Portfolio]:
    return db.query(Portfolio).filter(Portfolio.user_id == user_id).all()


# ---------------------------------------------------------------------------
# Update allocations → rebalance
# ---------------------------------------------------------------------------

def update_allocations(db: Session, portfolio_id: int, allocations: list[AllocationItem]) -> Portfolio:
    portfolio = _get_portfolio(db, portfolio_id)

    # Validate tickers exist in mock
    for alloc in allocations:
        try:
            get_price(alloc.ticker)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    today = date.today()

    # Replace all allocations
    db.query(PortfolioAllocation).filter(
        PortfolioAllocation.portfolio_id == portfolio_id
    ).delete()
    db.flush()

    for alloc in allocations:
        db.add(PortfolioAllocation(
            portfolio_id=portfolio_id,
            ticker=alloc.ticker.upper(),
            target_pct=alloc.target_pct,
        ))
    db.flush()

    # Refresh relationships before rebalancing
    db.refresh(portfolio)

    # Rebalance immediately
    _rebalance(db, portfolio, allocations, today)

    db.commit()
    db.refresh(portfolio)
    return portfolio


# ---------------------------------------------------------------------------
# Fund: wallet → portfolio → auto invest
# ---------------------------------------------------------------------------

def fund_portfolio(db: Session, portfolio_id: int, data: FundRequest) -> Portfolio:
    portfolio = _get_portfolio(db, portfolio_id)
    wallet = db.query(Wallet).filter(Wallet.user_id == portfolio.user_id).first()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    if wallet.currency != portfolio.currency:
        raise HTTPException(status_code=422, detail=f"Currency mismatch: wallet={wallet.currency}, portfolio={portfolio.currency}")
    if wallet.cash_balance < data.amount:
        raise HTTPException(status_code=400, detail=f"Insufficient wallet funds. Available: {wallet.cash_balance}")

    wallet.cash_balance    -= data.amount
    portfolio.cash_balance += data.amount

    db.add(PortfolioTransfer(
        wallet_id=wallet.id,
        portfolio_id=portfolio_id,
        amount=data.amount,
        currency=portfolio.currency,
    ))
    db.flush()

    # Auto-invest according to allocations
    _invest_cash(db, portfolio, date.today())

    db.commit()
    db.refresh(portfolio)
    return portfolio


# ---------------------------------------------------------------------------
# Withdraw: sell proportionally → portfolio → wallet
# ---------------------------------------------------------------------------

def withdraw_from_portfolio(db: Session, portfolio_id: int, data: WithdrawRequest) -> Portfolio:
    portfolio = _get_portfolio(db, portfolio_id)
    wallet    = db.query(Wallet).filter(Wallet.user_id == portfolio.user_id).first()

    total_value = _portfolio_total_value(db, portfolio)
    if data.amount > total_value:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient portfolio value. Total: {total_value}, requested: {data.amount}"
        )

    today = date.today()

    # Sell proportionally based on current market value of each holding
    holdings = [h for h in portfolio.holdings if h.quantity > 0]
    holdings_value = sum(h.quantity * get_price(h.ticker) for h in holdings)

    if holdings_value > 0:
        # How much of the withdrawal comes from holdings vs cash
        cash_portion     = min(portfolio.cash_balance, data.amount)
        holdings_portion = data.amount - cash_portion

        if holdings_portion > 0:
            for holding in holdings:
                current_value  = holding.quantity * get_price(holding.ticker)
                sell_amount    = (holdings_portion * current_value / holdings_value).quantize(
                    Decimal("0.0001"), rounding=ROUND_DOWN
                )
                if sell_amount > 0:
                    _execute_sell(db, portfolio, holding.ticker, sell_amount, today)

    # Move cash from portfolio to wallet
    portfolio.cash_balance -= data.amount
    wallet.cash_balance    += data.amount

    db.add(PortfolioTransfer(
        wallet_id=wallet.id,
        portfolio_id=portfolio_id,
        amount=-data.amount,  # negative = outflow
        currency=portfolio.currency,
    ))

    db.commit()
    db.refresh(portfolio)
    return portfolio


# ---------------------------------------------------------------------------
# Total valuation
# ---------------------------------------------------------------------------

def get_portfolio_total(db: Session, portfolio_id: int) -> PortfolioTotal:
    portfolio   = _get_portfolio(db, portfolio_id)
    holdings    = db.query(Holding).filter(Holding.portfolio_id == portfolio_id, Holding.quantity > 0).all()
    alloc_map   = {a.ticker: a.target_pct for a in portfolio.allocations}

    valuations     = []
    holdings_value = Decimal("0")

    for h in holdings:
        try:
            current_price = get_price(h.ticker)
        except ValueError:
            current_price = h.avg_buy_price

        market_value    = h.quantity * current_price
        gain_loss       = (current_price - h.avg_buy_price) * h.quantity
        holdings_value += market_value

        valuations.append(HoldingValuation(
            ticker=h.ticker,
            quantity=h.quantity,
            avg_buy_price=h.avg_buy_price,
            current_price=current_price,
            market_value=market_value,
            gain_loss=gain_loss,
            target_pct=alloc_map.get(h.ticker),
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
# Movements feed
# ---------------------------------------------------------------------------

def get_movements(db: Session, portfolio_id: int, limit: int = 50) -> list[MovementItem]:
    _get_portfolio(db, portfolio_id)

    orders    = db.query(Order).filter(Order.portfolio_id == portfolio_id).all()
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
        is_inflow  = t.amount > 0
        items.append(MovementItem(
            id=t.id,
            event_type="fund_in" if is_inflow else "fund_out",
            description=f"{'Transfer in' if is_inflow else 'Transfer out'}: {abs(t.amount)} {t.currency}",
            amount=abs(t.amount),
            currency=t.currency,
            date=t.created_at.date(),
            created_at=t.created_at,
        ))

    items.sort(key=lambda x: x.created_at, reverse=True)
    return items[:limit]
