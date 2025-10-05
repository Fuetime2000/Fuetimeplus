#!/usr/bin/env python3
"""
Direct database stamp script
This script directly stamps the database with the current migration head.
"""
import os
import sys
import sqlite3
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

db_path = 'instance/fuetime.db'

def stamp_database():
    """Stamp the database with the current migration head"""

    if not os.path.exists(db_path):
        print(f"Database file not found at: {db_path}")
        return False

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create alembic_version table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL
            )
        """)

        # Clear any existing version
        cursor.execute("DELETE FROM alembic_version;")

        # Get the latest migration file revision ID
        versions_dir = 'migrations/versions'
        if os.path.exists(versions_dir):
            files = [f for f in os.listdir(versions_dir) if f.endswith('.py') and not f.startswith('__')]
            if files:
                # Extract revision ID from the most recent migration file
                latest_file = max(files, key=lambda f: f.split('_')[0])
                revision_id = latest_file.split('_')[0]
                print(f"Using revision ID: {revision_id}")

                # Insert the revision ID
                cursor.execute("INSERT INTO alembic_version (version_num) VALUES (?);", (revision_id,))
                print(f"Stamped database with revision: {revision_id}")
            else:
                print("No migration files found in versions directory")
                return False
        else:
            print("Migrations versions directory not found")
            return False

        conn.commit()
        conn.close()

        print("Database successfully stamped!")
        return True

    except Exception as e:
        print(f"Error stamping database: {e}")
        return False

if __name__ == "__main__":
    success = stamp_database()
    if success:
        print("\nNext step: Run 'flask db upgrade' to complete the migration process.")
    else:
        print("\nFailed to stamp database.")
