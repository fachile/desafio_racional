"""simplify schema - int cash, no currency, no date, no idempotency_key

Revision ID: 0003
Revises: 0002
Create Date: 2024-01-03 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # wallets: cash_balance Numeric → BigInteger, drop currency
    op.alter_column("wallets", "cash_balance", type_=sa.BigInteger(), server_default="0")
    op.drop_column("wallets", "currency")

    # portfolios: cash_balance Numeric → BigInteger, drop currency
    op.alter_column("portfolios", "cash_balance", type_=sa.BigInteger(), server_default="0")
    op.drop_column("portfolios", "currency")

    # cash_movements: amount Numeric → BigInteger, drop currency, date, idempotency_key
    op.alter_column("cash_movements", "amount", type_=sa.BigInteger())
    op.drop_index("ix_cash_movements_idempotency_key", table_name="cash_movements")
    op.drop_column("cash_movements", "currency")
    op.drop_column("cash_movements", "date")
    op.drop_column("cash_movements", "idempotency_key")

    # portfolio_transfers: amount Numeric → BigInteger, drop currency
    op.alter_column("portfolio_transfers", "amount", type_=sa.BigInteger())
    op.drop_column("portfolio_transfers", "currency")

    # holdings: avg_buy_price Numeric → BigInteger
    op.alter_column("holdings", "avg_buy_price", type_=sa.BigInteger(), server_default="0")

    # orders: price_at_execution Numeric → BigInteger, drop currency, date
    op.alter_column("orders", "price_at_execution", type_=sa.BigInteger())
    op.drop_column("orders", "currency")
    op.drop_column("orders", "date")

    # Drop currency enum type
    op.execute("DROP TYPE IF EXISTS currency")


def downgrade() -> None:
    pass  # intentionally left blank — downgrade not supported for this migration
