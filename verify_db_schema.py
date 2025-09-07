import os
import sqlite3
from sqlalchemy import create_engine, text
from config import Config

def verify_user_table():
    # Create SQLAlchemy engine
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as conn:
        # Check if user table exists
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        )
        if not result.fetchone():
            print("Error: 'user' table does not exist in the database.")
            return False
        
        # Get table info
        result = conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name='user'")
        )
        table_definition = result.scalar()
        print("\nUser Table Definition:")
        print("-" * 50)
        print(table_definition)
        print("-" * 50)
        
        # Check for verified column
        result = conn.execute(
            text("SELECT name FROM pragma_table_info('user') WHERE name='verified'")
        )
        if result.fetchone():
            print("\n✓ 'verified' column exists in user table")
            return True
        else:
            print("\n✗ 'verified' column is MISSING from user table")
            return False

if __name__ == "__main__":
    print("Verifying database schema...")
    verify_user_table()
