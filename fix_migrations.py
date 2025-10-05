#!/usr/bin/env python3
"""
Migration Fix Script
This script will fix the Flask-Migrate issue by resetting the migration state.
"""
import os
import sys
import shutil
from flask import Flask
from flask_migrate import Migrate
from extensions import db

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create Flask app context
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/fuetime.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)

def fix_migrations():
    """Fix the migration state by resetting alembic_version table"""
    with app.app_context():
        # Check if alembic_version table exists
        from sqlalchemy import text
        try:
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version';"))
            if result.fetchone():
                print("Found alembic_version table")

                # Get current version
                result = db.session.execute(text("SELECT version_num FROM alembic_version;"))
                current_version = result.fetchone()
                print(f"Current migration version: {current_version[0] if current_version else 'None'}")

                # Clear the alembic_version table
                db.session.execute(text("DELETE FROM alembic_version;"))
                db.session.commit()
                print("Cleared alembic_version table")

            # Stamp the database with the initial migration state
            from flask_migrate import stamp
            try:
                stamp()
                print("Stamped database with current migration state")
            except Exception as e:
                print(f"Error stamping database: {e}")

                # Try to stamp with head
                try:
                    from alembic.command import stamp as alembic_stamp
                    from alembic.config import Config

                    alembic_cfg = Config("migrations/alembic.ini")
                    alembic_stamp(alembic_cfg, "head")
                    print("Stamped database with head migration")
                except Exception as e2:
                    print(f"Error stamping with head: {e2}")

        except Exception as e:
            print(f"Error accessing database: {e}")

if __name__ == "__main__":
    fix_migrations()
