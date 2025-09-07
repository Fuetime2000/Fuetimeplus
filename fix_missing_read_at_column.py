import os
import sqlite3
from sqlalchemy import create_engine, text
from config import Config

def check_and_fix_read_at_column():
    # Create SQLAlchemy engine
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    engine = create_engine(db_uri)
    
    with engine.connect() as conn:
        # Check if read_at column exists in messages table
        result = conn.execute(
            text("SELECT name FROM pragma_table_info('messages') WHERE name='read_at'")
        )
        column_exists = bool(result.fetchone())
        
        if not column_exists:
            print("Adding 'read_at' column to messages table...")
            try:
                # Add the column
                conn.execute(
                    text("ALTER TABLE messages ADD COLUMN read_at DATETIME")
                )
                conn.commit()
                print("Successfully added 'read_at' column to messages table.")
                return True
            except Exception as e:
                print(f"Error adding column: {e}")
                conn.rollback()
                return False
        else:
            print("'read_at' column already exists in messages table.")
            return True

if __name__ == "__main__":
    if check_and_fix_read_at_column():
        print("Database check and fix completed successfully.")
    else:
        print("There was an error checking/fixing the database.")
        exit(1)
