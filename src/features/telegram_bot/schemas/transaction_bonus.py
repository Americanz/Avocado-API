"""create transaction_bonus table

Revision ID: create_transaction_bonus
Revises: previous_revision_id
Create Date: 2025-09-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'create_transaction_bonus'
down_revision = 'previous_revision_id'  # замініть на актуальний
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create transaction_bonus table
    op.create_table('transaction_bonus',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        # Links
        sa.Column('client_id', sa.BigInteger(), nullable=False, comment='Client ID from Poster'),
        sa.Column('transaction_id', sa.BigInteger(), nullable=True, comment='Related Poster transaction ID'),

        # Operation details
        sa.Column('operation_type', sa.String(length=20), nullable=False, comment='Operation type: EARN, SPEND, ADJUST, EXPIRE'),

        # Amounts
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False, comment='Bonus amount (+/- value)'),
        sa.Column('balance_before', sa.Numeric(precision=10, scale=2), nullable=False, comment='Client bonus balance before operation'),
        sa.Column('balance_after', sa.Numeric(precision=10, scale=2), nullable=False, comment='Client bonus balance after operation'),

        # Details
        sa.Column('description', sa.Text(), nullable=True, comment='Operation description'),
        sa.Column('bonus_percent', sa.Numeric(precision=5, scale=2), nullable=True, comment='Bonus percentage applied'),
        sa.Column('transaction_sum', sa.Numeric(precision=10, scale=2), nullable=True, comment='Transaction sum for bonus calculation'),

        # System
        sa.Column('processed_at', sa.DateTime(), nullable=False, comment='When operation was processed'),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.client_id'], ),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.transaction_id'], ),
    )

    # Create indexes
    op.create_index('ix_transaction_bonus_client_id', 'transaction_bonus', ['client_id'], unique=False)
    op.create_index('ix_transaction_bonus_transaction_id', 'transaction_bonus', ['transaction_id'], unique=False)
    op.create_index('ix_transaction_bonus_operation_type', 'transaction_bonus', ['operation_type'], unique=False)
    op.create_index('ix_transaction_bonus_created_at', 'transaction_bonus', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_transaction_bonus_created_at', table_name='transaction_bonus')
    op.drop_index('ix_transaction_bonus_operation_type', table_name='transaction_bonus')
    op.drop_index('ix_transaction_bonus_transaction_id', table_name='transaction_bonus')
    op.drop_index('ix_transaction_bonus_client_id', table_name='transaction_bonus')

    # Drop table
    op.drop_table('transaction_bonus')
