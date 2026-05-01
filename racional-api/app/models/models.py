import enum
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    String, Numeric, Enum, ForeignKey, DateTime, Date,
    UniqueConstraint, func, Integer
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---------------------------------------------------------------------------
# Python Enums
# ---------------------------------------------------------------------------

class MovementType(str, enum.Enum):
    deposit    = "deposit"
    withdrawal = "withdrawal"


class OrderType(str, enum.Enum):
    buy  = "buy"
    sell = "sell"


class OrderStatus(str, enum.Enum):
    executed  = "executed"
    cancelled = "cancelled"


class Currency(str, enum.Enum):
    USD = "USD"
    CLP = "CLP"
    EUR = "EUR"


# ---------------------------------------------------------------------------
# SQLAlchemy Enum column types — create_type=False because the PG types
# are created by Alembic migrations, not by SQLAlchemy's metadata.
# ---------------------------------------------------------------------------

movement_type_enum = Enum(MovementType, name="movementtype", create_type=False)
order_type_enum    = Enum(OrderType,    name="ordertype",    create_type=False)
order_status_enum  = Enum(OrderStatus,  name="orderstatus",  create_type=False)
currency_enum      = Enum(Currency,     name="currency",     create_type=False)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id:         Mapped[int]       = mapped_column(Integer, primary_key=True, autoincrement=True)
    email:      Mapped[str]       = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name:  Mapped[str]       = mapped_column(String(255), nullable=False)
    phone:      Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    wallet:     Mapped["Wallet"]          = relationship("Wallet", back_populates="user", uselist=False)
    portfolios: Mapped[list["Portfolio"]] = relationship("Portfolio", back_populates="user")


class Wallet(Base):
    __tablename__ = "wallets"

    id:           Mapped[int]       = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:      Mapped[int]       = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    cash_balance: Mapped[Decimal]   = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    currency:     Mapped[Currency]  = mapped_column(currency_enum, nullable=False, default=Currency.USD)
    created_at:   Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:   Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user:                Mapped["User"]                  = relationship("User", back_populates="wallet")
    cash_movements:      Mapped[list["CashMovement"]]    = relationship("CashMovement", back_populates="wallet")
    portfolio_transfers: Mapped[list["PortfolioTransfer"]] = relationship("PortfolioTransfer", back_populates="wallet")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id:           Mapped[int]        = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:      Mapped[int]        = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name:         Mapped[str]        = mapped_column(String(255), nullable=False)
    description:  Mapped[str | None] = mapped_column(String(500))
    cash_balance: Mapped[Decimal]    = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    currency:     Mapped[Currency]   = mapped_column(currency_enum, nullable=False, default=Currency.USD)
    created_at:   Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:   Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user:                Mapped["User"]                  = relationship("User", back_populates="portfolios")
    holdings:            Mapped[list["Holding"]]         = relationship("Holding", back_populates="portfolio")
    orders:              Mapped[list["Order"]]           = relationship("Order", back_populates="portfolio")
    portfolio_transfers: Mapped[list["PortfolioTransfer"]] = relationship("PortfolioTransfer", back_populates="portfolio")


class CashMovement(Base):
    __tablename__ = "cash_movements"

    id:              Mapped[int]          = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallet_id:       Mapped[int]          = mapped_column(Integer, ForeignKey("wallets.id"), nullable=False)
    type:            Mapped[MovementType] = mapped_column(movement_type_enum, nullable=False)
    amount:          Mapped[Decimal]      = mapped_column(Numeric(18, 4), nullable=False)
    currency:        Mapped[Currency]     = mapped_column(currency_enum, nullable=False)
    date:            Mapped[date]         = mapped_column(Date, nullable=False)
    note:            Mapped[str | None]   = mapped_column(String(500))
    idempotency_key: Mapped[str | None]   = mapped_column(String(255), unique=True, index=True)
    created_at:      Mapped[datetime]     = mapped_column(DateTime(timezone=True), server_default=func.now())

    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="cash_movements")


class PortfolioTransfer(Base):
    __tablename__ = "portfolio_transfers"

    id:           Mapped[int]       = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallet_id:    Mapped[int]       = mapped_column(Integer, ForeignKey("wallets.id"), nullable=False)
    portfolio_id: Mapped[int]       = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False)
    amount:       Mapped[Decimal]   = mapped_column(Numeric(18, 4), nullable=False)
    currency:     Mapped[Currency]  = mapped_column(currency_enum, nullable=False)
    created_at:   Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

    wallet:    Mapped["Wallet"]    = relationship("Wallet", back_populates="portfolio_transfers")
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="portfolio_transfers")


class Holding(Base):
    __tablename__ = "holdings"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "ticker", name="uq_holding_portfolio_ticker"),
    )

    id:            Mapped[int]       = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id:  Mapped[int]       = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False)
    ticker:        Mapped[str]       = mapped_column(String(20), nullable=False)
    quantity:      Mapped[Decimal]   = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    avg_buy_price: Mapped[Decimal]   = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    updated_at:    Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="holdings")


class Order(Base):
    __tablename__ = "orders"

    id:                  Mapped[int]         = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id:        Mapped[int]         = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False)
    ticker:              Mapped[str]         = mapped_column(String(20), nullable=False)
    type:                Mapped[OrderType]   = mapped_column(order_type_enum, nullable=False)
    quantity:            Mapped[Decimal]     = mapped_column(Numeric(18, 6), nullable=False)
    price_at_execution:  Mapped[Decimal]     = mapped_column(Numeric(18, 4), nullable=False)
    currency:            Mapped[Currency]    = mapped_column(currency_enum, nullable=False)
    date:                Mapped[date]        = mapped_column(Date, nullable=False)
    status:              Mapped[OrderStatus] = mapped_column(order_status_enum, nullable=False, default=OrderStatus.executed)
    created_at:          Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="orders")
