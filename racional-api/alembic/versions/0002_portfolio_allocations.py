"""add portfolio_allocations table

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolio_allocations",
        sa.Column("id",           sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("portfolio_id", sa.Integer, sa.ForeignKey("portfolios.id"), nullable=False),
        sa.Column("ticker",       sa.String(20),   nullable=False),
        sa.Column("target_pct",   sa.Numeric(6, 4), nullable=False),
        sa.Column("created_at",   sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at",   sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_allocation_portfolio_ticker",
        "portfolio_allocations",
        ["portfolio_id", "ticker"]
    )


def downgrade() -> None:
    op.drop_table("portfolio_allocations")
