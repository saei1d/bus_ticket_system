"""Add performance indexes for bookings and seats

Revision ID: a1b2c3d4e5f6
Revises: 5e4bd2ba16f6
Create Date: 2025-11-20 11:45:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "5e4bd2ba16f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_bookings_created_confirmed",
        "bookings",
        ["created_at"],
        unique=False,
        postgresql_where=sa.text("status = 'confirmed'"),
    )
    op.create_index(
        "ix_bookings_seat_id",
        "bookings",
        ["seat_id"],
        unique=False,
    )
    op.create_index(
        "ix_seats_trip_available",
        "seats",
        ["trip_id"],
        unique=False,
        postgresql_where=sa.text("is_reserved = false"),
    )


def downgrade() -> None:
    op.drop_index("ix_seats_trip_available", table_name="seats")
    op.drop_index("ix_bookings_seat_id", table_name="bookings")
    op.drop_index("ix_bookings_created_confirmed", table_name="bookings")

