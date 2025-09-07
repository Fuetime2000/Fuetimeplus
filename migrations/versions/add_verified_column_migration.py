"""Add verified column to user table

Revision ID: add_verified_column
Revises: 2643d37fd26d
Create Date: 2025-09-07 11:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_verified_column'
down_revision = '2643d37fd26d'
branch_labels = None
depends_on = None

def upgrade():
    # Add the verified column with a default value of False
    op.add_column('user', sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    
    # If you want to update existing rows to have a default value
    # op.execute("UPDATE user SET verified = 0 WHERE verified IS NULL")
    
    # Make the column non-nullable after updating all rows
    # op.alter_column('user', 'verified', nullable=False)

def downgrade():
    # Remove the verified column if rolling back
    op.drop_column('user', 'verified')
