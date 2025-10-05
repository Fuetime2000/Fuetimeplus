#!/usr/bin/env python3
"""
Direct Migration Fix Script
This script directly fixes the database migration issue.
"""
import sqlite3
import os

# Database path
db_path = 'instance/fuetime.db'

def fix_migration_issue():
    """Fix the migration issue by clearing alembic_version table"""

    if not os.path.exists(db_path):
        print(f"Database file not found at: {db_path}")
        return False

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check current tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Current tables in database:")
        for table in tables:
            print(f"  {table[0]}")

        # Check if alembic_version table exists and what version it has
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='alembic_version';")
        alembic_table = cursor.fetchone()

        if alembic_table:
            print(f"\nAlembic version table exists: {alembic_table[0]}")

            # Get current version
            cursor.execute("SELECT version_num FROM alembic_version;")
            version = cursor.fetchone()
            print(f"Current alembic version: {version[0] if version else 'None'}")

            # Clear the alembic_version table
            cursor.execute("DELETE FROM alembic_version;")
            print("Cleared alembic_version table")

        # Create or update alembic_version table with null (no migrations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL
            )
        """)

        # Insert a null version to indicate no migrations applied
        cursor.execute("DELETE FROM alembic_version;")
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES (NULL);")
        print("Set alembic_version to NULL (no migrations)")

        conn.commit()
        conn.close()

        print("\nMigration issue fixed! The database is now in a clean state.")
        print("You can now run 'flask db upgrade' to apply any pending migrations.")
        return True

    except Exception as e:
        print(f"Error fixing migration: {e}")
        return False

if __name__ == "__main__":
    success = fix_migration_issue()
    if success:
        print("\nNext steps:")
        print("1. Run: flask db upgrade")
        print("2. If that fails, run: flask db stamp head")
        print("3. Then run: flask db upgrade again")
    else:
        print("\nFailed to fix migration issue. You may need to recreate the database.")
