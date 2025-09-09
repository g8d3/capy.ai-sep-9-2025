from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_user_email', 'user', ['email'], unique=True)

    op.create_table(
        'asset',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('exchange_symbol', sa.String(length=50), nullable=False),
        sa.Column('cg_id', sa.String(length=100), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('base', sa.String(length=50), nullable=True),
        sa.Column('quote', sa.String(length=50), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    )
    op.create_index('ix_asset_exchange_symbol', 'asset', ['exchange_symbol'], unique=False)

    op.create_table(
        'price',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('asset_id', sa.Integer(), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('ts', sa.BigInteger(), nullable=False),
        sa.Column('o', sa.Numeric(20, 10), nullable=False),
        sa.Column('h', sa.Numeric(20, 10), nullable=False),
        sa.Column('l', sa.Numeric(20, 10), nullable=False),
        sa.Column('c', sa.Numeric(20, 10), nullable=False),
        sa.Column('v', sa.Numeric(28, 10), nullable=False),
    )
    op.create_index('ix_price_asset_time_ts', 'price', ['asset_id', 'timeframe', 'ts'], unique=False)
    op.create_unique_constraint('uq_price_asset_time_ts', 'price', ['asset_id', 'timeframe', 'ts'])

    op.create_table(
        'strategy',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('params', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'backtest',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('strategy_id', sa.Integer(), sa.ForeignKey('strategy.id', ondelete='SET NULL'), nullable=True),
        sa.Column('params', sa.JSON(), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('start', sa.Integer(), nullable=False),
        sa.Column('end', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('queued', 'running', 'completed', 'failed', name='backteststatus'), nullable=False, server_default='queued'),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0'),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'backtest_asset',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('backtest_id', sa.Integer(), sa.ForeignKey('backtest.id', ondelete='CASCADE'), nullable=False),
        sa.Column('asset_id', sa.Integer(), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=False),
    )


def downgrade():
    op.drop_table('backtest_asset')
    op.drop_table('backtest')
    op.drop_table('strategy')
    op.drop_constraint('uq_price_asset_time_ts', 'price', type_='unique')
    op.drop_index('ix_price_asset_time_ts', table_name='price')
    op.drop_table('price')
    op.drop_index('ix_asset_exchange_symbol', table_name='asset')
    op.drop_table('asset')
    op.drop_index('ix_user_email', table_name='user')
    op.drop_table('user')
