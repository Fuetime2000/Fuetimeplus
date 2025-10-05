#!/usr/bin/env python3
"""
Manual Migration Creation Script
This script creates the initial migration file for the existing database.
"""
import os
from datetime import datetime

# Generate a timestamp-based revision ID
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
revision_id = f"{timestamp}_initial"

migration_content = f'''"""initial migration

Revision ID: {revision_id}
Revises: 
Create Date: {datetime.now().isoformat()}

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '{revision_id}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create all tables that currently exist in the database
    pass

def downgrade():
    # Drop all tables
    pass
'''

# Write the migration file
migration_file = f"migrations/versions/{revision_id}_initial.py"
with open(migration_file, 'w') as f:
    f.write(migration_content)

print(f"Created migration file: {migration_file}")
print(f"Revision ID: {revision_id}")
print()
print("Now you can run:")
print("flask db stamp head")
print("flask db upgrade")
