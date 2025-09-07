import os
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import Config

def check_and_fix_verified_column():
    # Create SQLAlchemy engine
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri)
    
    # Check if verified column exists
    with engine.connect() as conn:
        # SQLite specific query to check column existence
        result = conn.execute(
            text("SELECT name FROM pragma_table_info('user') WHERE name='verified'")
        )
        column_exists = bool(result.fetchone())
        
        if not column_exists:
            print("Adding 'verified' column to user table...")
            try:
                # Add the column
                conn.execute(
                    text("ALTER TABLE user ADD COLUMN verified BOOLEAN DEFAULT 0")
                )
                conn.commit()
                print("Successfully added 'verified' column to user table.")
            except Exception as e:
                print(f"Error adding column: {e}")
                conn.rollback()
        else:
            print("'verified' column already exists in user table.")

if __name__ == "__main__":
    check_and_fix_verified_column()
