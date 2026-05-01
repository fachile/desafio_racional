"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

movement_type_col = sa.Enum("deposit", "withdrawal", name="movementtype", create_type=False)
order_type_col    = sa.Enum("buy", "sell",            name="ordertype",    create_type=False)
order_status_col  = sa.Enum("executed", "cancelled",  name="orderstatus",  create_type=False)
currency_col      = sa.Enum("USD", "CLP", "EUR",      name="currency",     create_type=False)


def create_enum_if_not_exists(name: str, values: list[str]) -> None:
    values_str = ", ".join(f"'{v}'" for v in values)
    op.execute(f"""
        DO $$ BEGIN
            CREATE TYPE {name} AS ENUM ({values_str});
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)


def upgrade() -> None:
    create_enum_if_not_exists("movementtype", ["deposit", "withdrawal"])
    create_enum_if_not_exists("ordertype",    ["buy", "sell"])
    create_enum_if_not_exists("orderstatus",  ["executed", "cancelled"])
    create_enum_if_not_exists("currency",     ["USD", "CLP", "EUR"])

    # users
    op.create_table(
        "users",
        sa.Column("id",         sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email",      sa.String(255), nullable=False),
        sa.Column("full_name",  sa.String(255), nullable=False),
        sa.Column("phone",      sa.String(50),  nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # wallets
    op.create_table(
        "wallets",
        sa.Column("id",           sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id",      sa.Integer, sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("cash_balance", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("currency",     sa.TEXT(), nullable=False),  # Will be cast to currency enum via constraint
        sa.Column("created_at",   sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("updated_at",   sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # portfolios
    op.create_table(
        "portfolios",
        sa.Column("id",           sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id",      sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name",         sa.String(255), nullable=False),
        sa.Column("description",  sa.String(500), nullable=True),
        sa.Column("cash_balance", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("currency",     sa.TEXT(), nullable=False),  # Will be cast to currency enum via constraint
        sa.Column("created_at",   sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("updated_at",   sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    # Add CHECK constraint to enforce valid currency values
    op.execute("ALTER TABLE portfolios ADD CONSTRAINT portfolios_currency_check CHECK (currency IN ('USD', 'CLP', 'EUR'))")

    # cash_movements
    op.create_table(
        "cash_movements",
        sa.Column("id",              sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("wallet_id",       sa.Integer, sa.ForeignKey("wallets.id"), nullable=False),
        sa.Column("type",            sa.TEXT(), nullable=False),  # Will be cast to movementtype enum via constraint
        sa.Column("amount",          sa.Numeric(18, 4), nullable=False),
        sa.Column("currency",        sa.TEXT(), nullable=False),  # Will be cast to currency enum via constraint
        sa.Column("date",            sa.Date, nullable=False),
        sa.Column("note",            sa.String(500), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("created_at",      sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_cash_movements_idempotency_key", "cash_movements", ["idempotency_key"], unique=True)
    # Add CHECK constraints
    op.execute("ALTER TABLE cash_movements ADD CONSTRAINT cash_movements_type_check CHECK (type IN ('deposit', 'withdrawal'))")
    op.execute("ALTER TABLE cash_movements ADD CONSTRAINT cash_movements_currency_check CHECK (currency IN ('USD', 'CLP', 'EUR'))")

    # portfolio_transfers
    op.create_table(
        "portfolio_transfers",
        sa.Column("id",           sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("wallet_id",    sa.Integer, sa.ForeignKey("wallets.id"), nullable=False),
        sa.Column("portfolio_id", sa.Integer, sa.ForeignKey("portfolios.id"), nullable=False),
        sa.Column("amount",       sa.Numeric(18, 4), nullable=False),
        sa.Column("currency",     sa.TEXT(), nullable=False),  # Will be cast to currency enum via constraint
        sa.Column("created_at",   sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Add CHECK constraint
    op.execute("ALTER TABLE portfolio_transfers ADD CONSTRAINT portfolio_transfers_currency_check CHECK (currency IN ('USD', 'CLP', 'EUR'))")

    # holdings
    op.create_table(
        "holdings",
        sa.Column("id",            sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("portfolio_id",  sa.Integer, sa.ForeignKey("portfolios.id"), nullable=False),
        sa.Column("ticker",        sa.String(20),     nullable=False),
        sa.Column("quantity",      sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("avg_buy_price", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("updated_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_holding_portfolio_ticker", "holdings", ["portfolio_id", "ticker"])

    # orders
    op.create_table(
        "orders",
        sa.Column("id",                 sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("portfolio_id",       sa.Integer, sa.ForeignKey("portfolios.id"), nullable=False),
        sa.Column("ticker",             sa.String(20),     nullable=False),
        sa.Column("type",               sa.TEXT(),    nullable=False),  # Will be cast to ordertype enum via constraint
        sa.Column("quantity",           sa.Numeric(18, 6), nullable=False),
        sa.Column("price_at_execution", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency",           sa.TEXT(),      nullable=False),  # Will be cast to currency enum via constraint
        sa.Column("date",               sa.Date,           nullable=False),
        sa.Column("status",             sa.TEXT(),  nullable=False),  # Will be cast to orderstatus enum via constraint
        sa.Column("created_at",         sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Add CHECK constraints
    op.execute("ALTER TABLE orders ADD CONSTRAINT orders_type_check CHECK (type IN ('buy', 'sell'))")
    op.execute("ALTER TABLE orders ADD CONSTRAINT orders_currency_check CHECK (currency IN ('USD', 'CLP', 'EUR'))")
    op.execute("ALTER TABLE orders ADD CONSTRAINT orders_status_check CHECK (status IN ('executed', 'cancelled'))")


def downgrade() -> None:
    op.drop_table("orders")
    op.drop_table("holdings")
    op.drop_table("portfolio_transfers")
    op.drop_table("cash_movements")
    op.drop_table("portfolios")
    op.drop_table("wallets")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS ordertype")
    op.execute("DROP TYPE IF EXISTS movementtype")
    op.execute("DROP TYPE IF EXISTS currency")
