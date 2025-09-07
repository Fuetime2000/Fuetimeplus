"""Add verified column to user table

Revision ID: add_verified_column
Revises: 
Create Date: 2025-09-07 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_verified_column'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add the verified column with a default value of False
    op.add_column('user', sa.Column('verified', sa.Boolean(), nullable=False, server_default='0'))
    
    # If you want to update existing records to have verified=True
    # op.execute("UPDATE user SET verified = 1")

def downgrade():
    # Remove the verified column if rolling back
    op.drop_column('user', 'verified')
