"""Add verified column to user table

Revision ID: add_verified_column
Revises: 868c3cef9b0f
Create Date: 2023-09-07 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_verified_column'
down_revision = '868c3cef9b0f'
branch_labels = None
depends_on = None


def upgrade():
    # Add verified column to user table
    op.add_column('user', sa.Column('verified', sa.Boolean(), server_default='0', nullable=False))


def downgrade():
    # Remove verified column from user table
    op.drop_column('user', 'verified')
