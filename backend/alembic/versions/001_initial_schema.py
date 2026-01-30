"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('venue', sa.String(255), nullable=False),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('stubhub_event_id', sa.String(100), nullable=True),
        sa.Column('seatgeek_event_id', sa.String(100), nullable=True),
        sa.Column('vividseats_event_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Inventory table
    op.create_table(
        'inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('section', sa.String(50), nullable=False),
        sa.Column('row', sa.String(10), nullable=True),
        sa.Column('seat_numbers', sa.String(100), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('cost_per_ticket', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_cost', sa.Numeric(10, 2), nullable=False),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('target_sell_min', sa.Numeric(10, 2), nullable=True),
        sa.Column('target_sell_max', sa.Numeric(10, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Listing snapshots table
    op.create_table(
        'listing_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('section', sa.String(50), nullable=True),
        sa.Column('row', sa.String(10), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('price_per_ticket', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('listing_url', sa.Text(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_listings_event_fetched', 'listing_snapshots', ['event_id', 'fetched_at'])
    op.create_index('idx_listings_section', 'listing_snapshots', ['section'])
    op.create_index('idx_listings_platform', 'listing_snapshots', ['platform'])

    # Price history table
    op.create_table(
        'price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('section', sa.String(50), nullable=True),
        sa.Column('recorded_date', sa.Date(), nullable=False),
        sa.Column('recorded_hour', sa.Integer(), nullable=True),
        sa.Column('min_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('max_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('avg_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('median_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('listing_count', sa.Integer(), nullable=True),
        sa.Column('platform_breakdown', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', 'section', 'recorded_date', 'recorded_hour', name='uq_price_history_lookup')
    )
    op.create_index('idx_price_history_lookup', 'price_history', ['event_id', 'section', 'recorded_date'])


def downgrade() -> None:
    op.drop_table('price_history')
    op.drop_table('listing_snapshots')
    op.drop_table('inventory')
    op.drop_table('events')
