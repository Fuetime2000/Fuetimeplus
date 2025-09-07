"""Remove read_at column from messages table

Revision ID: b2a5c1d9f1a6
Revises: 2643d37fd26d
Create Date: 2025-09-07 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2a5c1d9f1a6'
down_revision = '2643d37fd26d'
branch_labels = None
depends_on = None

def upgrade():
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table('messages', schema=None) as batch_op:
        try:
            batch_op.drop_column('read_at')
        except Exception:
            # Column may not exist on some environments; ignore if absent
            pass


def downgrade():
    # Recreate the column on downgrade
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('read_at', sa.DateTime(), nullable=True))
