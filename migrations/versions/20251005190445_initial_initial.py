"""initial migration

Revision ID: 20251005190445_initial
Revises: 
Create Date: 2025-10-05T19:04:45.099158

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251005190445_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create all tables that currently exist in the database
    pass

def downgrade():
    # Drop all tables
    pass
